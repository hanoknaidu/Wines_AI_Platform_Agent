"""Order, refund, return and cancellation tool APIs."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Query, Request
from fastapi.responses import JSONResponse

from app.api.deps import get_container, get_ctx
from app.container import Container
from app.schemas.common import ERROR_RESPONSES, OrderNumber, RmaNumber
from app.schemas.order import (
    CancellationEligibility,
    CancelOrderRequest,
    CancelOrderResult,
    Invoice,
    OrderDetail,
    OrderLine,
    OrderPayment,
    OrderStatusOut,
    OrderTracking,
    StatusHistoryEntry,
)
from app.schemas.refund import (
    ClaimReason,
    EligibilityResult,
    EvidenceUploadLink,
    RefundOut,
    RefundRequest,
    RefundResult,
    ReturnCreated,
    ReturnOut,
    ReturnRequestIn,
)
from app.services.cancellation_service import CancellationService
from app.services.context import ServiceContext
from app.services.idempotency import run_idempotent, validate_key
from app.services.order_service import OrderService
from app.services.refund_service import RefundService, ReturnService

router = APIRouter(tags=["Tool APIs: Orders, Refunds & Returns"], responses=ERROR_RESPONSES)
OrderId = Annotated[OrderNumber, Path(description="Public order number, e.g. WA-100101")]
IdemKey = Annotated[str | None, Header(alias="Idempotency-Key", description="Required for POST; 8-128 chars")]


def _replay_response(status_code: int, body: dict, replayed: bool) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=body,
                        headers={"Idempotent-Replayed": "true" if replayed else "false"})


# --- B. Orders ------------------------------------------------------------------
@router.get("/orders/{order_id}", response_model=OrderDetail, operation_id="get_order")
async def get_order(order_id: OrderId, ctx: ServiceContext = Depends(get_ctx)):
    return await OrderService(ctx).detail(order_id)


@router.get("/orders/{order_id}/status", response_model=OrderStatusOut, operation_id="get_order_status")
async def get_status(order_id: OrderId, ctx: ServiceContext = Depends(get_ctx)):
    return await OrderService(ctx).status(order_id)


@router.get("/orders/{order_id}/tracking", response_model=OrderTracking, operation_id="get_order_tracking")
async def get_tracking(order_id: OrderId, ctx: ServiceContext = Depends(get_ctx)):
    return await OrderService(ctx).tracking(order_id)


@router.get("/orders/{order_id}/items", response_model=list[OrderLine], operation_id="get_order_items")
async def get_items(order_id: OrderId, ctx: ServiceContext = Depends(get_ctx)):
    return await OrderService(ctx).items(order_id)


@router.get("/orders/{order_id}/payment", response_model=OrderPayment, operation_id="get_order_payment",
            summary="Payment information (audited sensitive read)")
async def get_payment(order_id: OrderId, ctx: ServiceContext = Depends(get_ctx)):
    return await OrderService(ctx).payment(order_id)


@router.get("/orders/{order_id}/history", response_model=list[StatusHistoryEntry], operation_id="get_order_history")
async def get_history(order_id: OrderId, ctx: ServiceContext = Depends(get_ctx)):
    return await OrderService(ctx).history(order_id)


@router.get("/orders/{order_id}/invoice", response_model=Invoice, operation_id="get_invoice",
            summary="Invoice / receipt (audited sensitive read)")
async def get_invoice(order_id: OrderId, ctx: ServiceContext = Depends(get_ctx)):
    return await OrderService(ctx).invoice(order_id)


# --- C. Refunds & returns ---------------------------------------------------------
@router.get("/orders/{order_id}/refund-eligibility", response_model=EligibilityResult,
            operation_id="check_refund_eligibility", summary="Policy decision only; never issues a refund")
async def refund_eligibility(
    order_id: OrderId,
    reason_code: Annotated[ClaimReason | None, Query(description="Omit to see every reason's window")] = None,
    ctx: ServiceContext = Depends(get_ctx),
    container: Container = Depends(get_container),
):
    return await RefundService(ctx, container.gateway).eligibility(order_id, reason_code)


@router.get("/orders/{order_id}/return-eligibility", response_model=EligibilityResult,
            operation_id="check_return_eligibility")
async def return_eligibility(
    order_id: OrderId,
    reason_code: Annotated[ClaimReason | None, Query()] = None,
    ctx: ServiceContext = Depends(get_ctx),
):
    return await ReturnService(ctx).eligibility(order_id, reason_code)


@router.get("/orders/{order_id}/refunds", response_model=list[RefundOut], operation_id="get_order_refunds")
async def list_refunds(order_id: OrderId, ctx: ServiceContext = Depends(get_ctx),
                       container: Container = Depends(get_container)):
    return await RefundService(ctx, container.gateway).list_refunds(order_id)


@router.get("/orders/{order_id}/returns", response_model=list[ReturnOut], operation_id="get_order_returns")
async def list_returns(order_id: OrderId, ctx: ServiceContext = Depends(get_ctx)):
    return await ReturnService(ctx).list_returns(order_id)


@router.post("/orders/{order_id}/refunds", response_model=RefundResult, status_code=201,
             operation_id="request_refund", responses={202: {"model": RefundResult,
                                                              "description": "Queued for human approval"}},
             summary="Initiate a refund (idempotent; requires explicit customer confirmation)")
async def create_refund(
    order_id: OrderId, body: RefundRequest, request: Request, idempotency_key: IdemKey = None,
    ctx: ServiceContext = Depends(get_ctx), container: Container = Depends(get_container),
):
    key = validate_key(idempotency_key)
    status, payload, replayed = await run_idempotent(
        ctx, key, "POST", request.url.path, body.model_dump(mode="json"),
        lambda: RefundService(ctx, container.gateway).request_refund(order_id, body, key),
    )
    return _replay_response(status, payload, replayed)


@router.post("/orders/{order_id}/returns", response_model=ReturnCreated, status_code=201,
             operation_id="create_return_request", summary="Create a return / claim (RMA)")
async def create_return(
    order_id: OrderId, body: ReturnRequestIn, request: Request, idempotency_key: IdemKey = None,
    ctx: ServiceContext = Depends(get_ctx),
):
    key = validate_key(idempotency_key)
    status, payload, replayed = await run_idempotent(
        ctx, key, "POST", request.url.path, body.model_dump(mode="json"),
        lambda: ReturnService(ctx).create_return(order_id, body, key),
    )
    return _replay_response(status, payload, replayed)


@router.get("/returns/{rma_number}", response_model=ReturnOut, operation_id="get_return_status")
async def get_return(rma_number: Annotated[RmaNumber, Path()], ctx: ServiceContext = Depends(get_ctx)):
    return await ReturnService(ctx).get_return(rma_number)


@router.post("/returns/{rma_number}/evidence-upload-link", response_model=EvidenceUploadLink,
             operation_id="request_evidence_upload", summary="Short-lived secure photo upload link")
async def evidence_link(rma_number: Annotated[RmaNumber, Path()], ctx: ServiceContext = Depends(get_ctx)):
    return await ReturnService(ctx).evidence_upload_link(rma_number)


# --- D. Cancellation ----------------------------------------------------------------
@router.get("/orders/{order_id}/cancellation-eligibility", response_model=CancellationEligibility,
            operation_id="check_cancellation_eligibility")
async def cancellation_eligibility(order_id: OrderId, ctx: ServiceContext = Depends(get_ctx),
                                   container: Container = Depends(get_container)):
    return await CancellationService(ctx, container.gateway).eligibility(order_id)


@router.post("/orders/{order_id}/cancellation", response_model=CancelOrderResult, operation_id="cancel_order",
             summary="Cancel an order (idempotent; requires explicit customer confirmation)")
async def cancel_order(
    order_id: OrderId, body: CancelOrderRequest, request: Request, idempotency_key: IdemKey = None,
    ctx: ServiceContext = Depends(get_ctx), container: Container = Depends(get_container),
):
    key = validate_key(idempotency_key)
    status, payload, replayed = await run_idempotent(
        ctx, key, "POST", request.url.path, body.model_dump(mode="json"),
        lambda: CancellationService(ctx, container.gateway).cancel(order_id, body, key),
    )
    return _replay_response(status, payload, replayed)
