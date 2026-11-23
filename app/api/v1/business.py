"""Additional business tool APIs: catalog, delivery estimates, stores,
support tickets, plus the local-only dev token endpoint."""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Path, Query, Request
from fastapi.responses import JSONResponse
from pydantic import Field

from app.api.deps import get_container, get_ctx, get_db
from app.container import Container
from app.core.errors import BusinessRuleError, NotFoundError
from app.core.money import str_to_cents
from app.repositories.catalog_repo import ProductFilters
from app.repositories.customer_repo import CustomerRepository
from app.schemas.catalog import Availability, ProductDetail, ProductSummary
from app.schemas.common import ERROR_RESPONSES, ApiModel, Page, PageParams, Sku, StoreCode, TicketNumber
from app.schemas.support import DeliveryEstimate, StoreInfo, TicketCreate, TicketDetail
from app.services.catalog_service import CatalogService, SearchParams
from app.services.context import ServiceContext
from app.services.idempotency import run_idempotent, validate_key
from app.services.store_service import StoreService
from app.services.support_service import SupportService

catalog = APIRouter(prefix="/products", tags=["Tool APIs: Catalog & Wine Information"], responses=ERROR_RESPONSES)
shipping = APIRouter(prefix="/shipping", tags=["Tool APIs: Shipping & Delivery"], responses=ERROR_RESPONSES)
stores = APIRouter(prefix="/stores", tags=["Tool APIs: Stores"], responses=ERROR_RESPONSES)
support = APIRouter(prefix="/support", tags=["Tool APIs: Support Tickets"], responses=ERROR_RESPONSES)
auth = APIRouter(prefix="/auth", tags=["Auth (local/dev only)"])

Money = Annotated[str, Field(pattern=r"^\d{1,6}(\.\d{1,2})?$")]


@catalog.get("", response_model=Page[ProductSummary], operation_id="search_products",
             summary="Wine-aware catalog search with live price and availability per location")
async def search_products(
    q: Annotated[str | None, Query(max_length=100)] = None,
    product_type: Literal["wine", "spirit", "beer", "cider", "sake", "non_alcoholic_wine"] | None = None,
    color: Literal["red", "white", "rose", "orange"] | None = None,
    wine_type: Literal["still", "sparkling", "fortified", "dessert"] | None = None,
    sweetness: Literal["dry", "off_dry", "medium_sweet", "sweet"] | None = None,
    body: Literal["light", "medium", "full"] | None = None,
    country: Annotated[str | None, Query(max_length=60)] = None,
    region: Annotated[str | None, Query(max_length=60)] = None,
    grape: Annotated[str | None, Query(max_length=60)] = None,
    brand: Annotated[str | None, Query(max_length=80)] = None,
    certification: Annotated[str | None, Query(max_length=40)] = None,
    is_non_alcoholic: bool | None = None,
    location: Literal["NJ", "NY"] | None = None,
    price_min: Annotated[Money | None, Query()] = None,
    price_max: Annotated[Money | None, Query()] = None,
    in_stock_only: bool = False,
    sort: Literal["name", "-name", "price", "-price", "vintage", "-vintage", "brand"] = "name",
    page: Annotated[int, Query(ge=1, le=1000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
    ctx: ServiceContext = Depends(get_ctx),
):
    params = SearchParams(
        filters=ProductFilters(q=q, product_type=product_type, color=color, wine_type=wine_type, sweetness=sweetness,
                               body=body, grape=grape, brand=brand, certification=certification,
                               is_non_alcoholic=is_non_alcoholic),
        country=country, region=region, location=location,
        price_min_cents=str_to_cents(price_min) if price_min else None,
        price_max_cents=str_to_cents(price_max) if price_max else None,
        in_stock_only=in_stock_only, sort=sort,
    )
    needs_location = price_min or price_max or in_stock_only or sort.lstrip("-") == "price"
    if needs_location and not location:
        # Prices and stock differ per licensed store (A-03), so they need a location.
        raise BusinessRuleError("location (NJ or NY) is required to filter or sort by price or stock",
                                code="LOCATION_REQUIRED")
    return await CatalogService(ctx).search(params, PageParams(page=page, page_size=page_size))


@catalog.get("/{sku}", response_model=ProductDetail, operation_id="get_product_details",
             summary="Full wine information: taste, grapes, region, nutrition, certifications, prices per store")
async def product_detail(sku: Annotated[Sku, Path()], ctx: ServiceContext = Depends(get_ctx)):
    return await CatalogService(ctx).detail(sku)


@catalog.get("/{sku}/availability", response_model=Availability, operation_id="check_inventory")
async def product_availability(
    sku: Annotated[Sku, Path()], location: Literal["NJ", "NY"], ctx: ServiceContext = Depends(get_ctx)
):
    return await CatalogService(ctx).availability(sku, location)


@shipping.get("/estimate", response_model=DeliveryEstimate, operation_id="get_delivery_estimate",
              summary="Pickup / local delivery / shipping options, fees and timing for a ZIP")
async def delivery_estimate(
    postal_code: Annotated[str, Query(pattern=r"^\d{5}$")],
    bottles: Annotated[int, Query(ge=1, le=120)] = 1,
    subtotal: Annotated[Money | None, Query(description="Product subtotal after discounts")] = None,
    ctx: ServiceContext = Depends(get_ctx),
):
    return await StoreService(ctx).estimate(postal_code, bottles, str_to_cents(subtotal) if subtotal else None)


@stores.get("", response_model=list[StoreInfo], operation_id="list_stores")
async def list_stores(ctx: ServiceContext = Depends(get_ctx)):
    return await StoreService(ctx).list_stores()


@stores.get("/{store_code}", response_model=StoreInfo, operation_id="get_store_info")
async def get_store(store_code: Annotated[StoreCode, Path()], ctx: ServiceContext = Depends(get_ctx)):
    return await StoreService(ctx).get_store(store_code)


@support.post("/tickets", response_model=TicketDetail, status_code=201, operation_id="create_support_ticket",
              summary="Create a support ticket / escalation (idempotent)")
async def create_ticket(
    body: TicketCreate, request: Request,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ctx: ServiceContext = Depends(get_ctx),
):
    key = validate_key(idempotency_key)

    async def handler():
        return 201, await SupportService(ctx).create_ticket(body, commit=False)

    status, payload, replayed = await run_idempotent(ctx, key, "POST", request.url.path,
                                                     body.model_dump(mode="json"), handler)
    return JSONResponse(status_code=status, content=payload,
                        headers={"Idempotent-Replayed": "true" if replayed else "false"})


@support.get("/tickets/{ticket_number}", response_model=TicketDetail, operation_id="get_support_ticket")
async def get_ticket(ticket_number: Annotated[TicketNumber, Path()], ctx: ServiceContext = Depends(get_ctx)):
    return await SupportService(ctx).get_ticket(ticket_number)


class DevTokenRequest(ApiModel):
    role: Literal["customer", "staff"] = "customer"
    subject: str = Field(..., pattern=r"^(C|S)-\d{4,6}$", description="C-100001 (customer) or S-1001 (staff)")


class TokenResponse(ApiModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


@auth.post("/dev-token", response_model=TokenResponse, include_in_schema=True,
           summary="LOCAL/DEV ONLY: issue a token for a seed customer or staff member")
async def dev_token(body: DevTokenRequest, container: Container = Depends(get_container), db=Depends(get_db)):
    if not container.settings.enable_dev_auth:
        raise NotFoundError("Not found")
    if body.role == "customer":
        customer = await CustomerRepository(db).get_by_number(body.subject)
        if customer is None:
            raise NotFoundError("Customer not found", code="CUSTOMER_NOT_FOUND")
        token = container.tokens.issue_customer_token(body.subject)
    else:
        token = container.tokens.issue_staff_token(body.subject)
    return TokenResponse(access_token=token, expires_in=container.settings.access_token_ttl_s)
