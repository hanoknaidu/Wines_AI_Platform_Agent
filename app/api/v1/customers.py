"""Customer tool APIs. Routers only parse/validate HTTP input and shape the
response; all logic is in services."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import get_ctx
from app.repositories.order_repo import OrderFilters
from app.schemas.common import ERROR_RESPONSES, CustomerNumber, Page, PageParams
from app.schemas.customer import AccountSummary, Address, CustomerProfile
from app.schemas.order import OrderSummary
from app.schemas.support import TicketSummary
from app.services.context import ServiceContext
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.support_service import SupportService

router = APIRouter(prefix="/customers", tags=["Tool APIs: Customers"], responses=ERROR_RESPONSES)
CustomerId = Annotated[CustomerNumber, Path(description="Public customer number, e.g. C-100001")]


@router.get("/{customer_id}", response_model=CustomerProfile, operation_id="get_customer_profile",
            summary="Customer profile (contact data masked)")
async def get_customer(customer_id: CustomerId, ctx: ServiceContext = Depends(get_ctx)):
    return await CustomerService(ctx).profile(customer_id)


@router.get("/{customer_id}/orders", response_model=Page[OrderSummary], operation_id="list_customer_orders",
            summary="Customer's orders: filter by status/type/date, sort, paginate")
async def list_orders(
    customer_id: CustomerId,
    status: Annotated[list[str] | None, Query(description="Repeatable: ?status=delivered&status=completed")] = None,
    fulfillment_type: Literal["local_delivery", "pickup", "shipping"] | None = None,
    placed_from: datetime | None = None,
    placed_to: datetime | None = None,
    sort: Literal["placed_at", "-placed_at", "grand_total", "-grand_total", "status", "-status"] = "-placed_at",
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    ctx: ServiceContext = Depends(get_ctx),
):
    filters = OrderFilters(status=status, fulfillment_type=fulfillment_type, placed_from=placed_from,
                           placed_to=placed_to, sort=sort)
    return await OrderService(ctx).list_for_customer(customer_id, filters, PageParams(page=page, page_size=page_size))


@router.get("/{customer_id}/addresses", response_model=list[Address], operation_id="get_customer_addresses",
            summary="Saved addresses (street masked for agent tokens)")
async def list_addresses(customer_id: CustomerId, ctx: ServiceContext = Depends(get_ctx)):
    return await CustomerService(ctx).addresses(customer_id)


@router.get("/{customer_id}/account", response_model=AccountSummary, operation_id="get_account_summary",
            summary="Loyalty, store credit, saved cards (last 4 only), open orders/tickets")
async def account(customer_id: CustomerId, ctx: ServiceContext = Depends(get_ctx)):
    return await CustomerService(ctx).account(customer_id)


@router.get("/{customer_id}/tickets", response_model=Page[TicketSummary], operation_id="list_support_tickets",
            summary="Customer's support tickets")
async def list_tickets(
    customer_id: CustomerId,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    ctx: ServiceContext = Depends(get_ctx),
):
    return await SupportService(ctx).list_for_customer(customer_id, PageParams(page=page, page_size=page_size))
