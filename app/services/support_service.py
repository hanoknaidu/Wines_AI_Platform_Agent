from __future__ import annotations

from datetime import timedelta

from app.core.errors import NotFoundError
from app.models import Customer, ReturnRequest, SupportTicket, TicketMessage
from app.repositories.misc_repo import ReturnRepository, SupportRepository
from app.schemas.common import Page, PageParams
from app.schemas.support import TicketCreate, TicketDetail, TicketMessageOut, TicketSummary
from app.services.context import ServiceContext

SLA = {"P1": timedelta(hours=1), "P2": timedelta(hours=4), "P3": timedelta(days=1)}  # A-63
TEAM_BY_CATEGORY = {
    "fraud": "compliance", "compliance": "compliance", "privacy_request": "privacy", "age_verification": "compliance",
    "pricing_dispute": "pricing", "price_match": "pricing", "promo_code": "pricing",
    "bulk_or_event_order": "events", "product_request": "catalog", "product_question": "catalog",
    "refund_status": "finance", "payment_issue": "finance",
    "delivery_issue": "fulfillment", "pickup_issue": "fulfillment", "order_status": "fulfillment",
}
TEAM_BY_REASON = {"refund_over_limit": "finance", "claim_review": "support", "refund_trace": "finance"}


class SupportService:
    def __init__(self, ctx: ServiceContext) -> None:
        self.ctx = ctx
        self.repo = SupportRepository(ctx.session)

    async def create_ticket(self, data: TicketCreate, *, commit: bool = True) -> TicketDetail:
        ctx = self.ctx
        customer_number = data.customer_id or ctx.principal.customer_number
        customer = await ctx.owned_customer(customer_number) if customer_number else None
        order = await ctx.owned_order(data.order_id) if data.order_id else None
        if order and customer and order.customer_id != customer.customer_id:
            raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")
        rma = None
        if data.rma_number:
            rma = await ReturnRepository(ctx.session).get_by_rma(data.rma_number)
            if rma is None or (customer and rma.customer_id != customer.customer_id):
                raise NotFoundError("Return not found", code="RETURN_NOT_FOUND")
        now = ctx.now
        ticket = SupportTicket(
            customer_id=customer.customer_id if customer else None,
            order_id=order.order_id if order else None,
            return_id=rma.return_id if rma else None,
            conversation_id=data.conversation_id or ctx.principal.session_id,
            channel="chat_agent" if ctx.principal.role == "agent" else "web_form",
            category=data.category,
            priority=data.priority,
            reason_code=data.reason_code,
            status="new",
            subject=data.subject,
            summary=data.summary,
            customer_sentiment=data.customer_sentiment,
            assigned_team=TEAM_BY_REASON.get(data.reason_code or "") or TEAM_BY_CATEGORY.get(data.category, "support"),
            sla_due_at=now + SLA[data.priority],
            created_by_type=ctx.principal.actor_type,
            created_at=now,
            updated_at=now,
        )
        await self.repo.add_with_public_number(ticket, "ticket_number", "TKT", 500000, "ticket_id")
        author = ctx.principal.actor_type
        ctx.session.add(
            TicketMessage(
                ticket_id=ticket.ticket_id,
                author_type=author,
                author_customer_id=customer.customer_id if author == "customer" and customer else None,
                visibility="public",
                body=data.summary,
                created_at=now,
            )
        )
        ctx.audit(
            "ticket.create", "support_ticket", ticket.ticket_number,
            customer_id=ticket.customer_id,
            after={"category": ticket.category, "priority": ticket.priority, "reason_code": ticket.reason_code},
        )
        await ctx.session.flush()
        if commit:
            await ctx.session.commit()
        fresh = await self.repo.get_by_number(ticket.ticket_number)
        return await self._detail(fresh)

    async def get_ticket(self, ticket_number: str) -> TicketDetail:
        ticket = await self.repo.get_by_number(ticket_number)
        if ticket is None:
            raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")
        if not self.ctx.principal.is_staff:
            owner = await self.ctx.session.get(Customer, ticket.customer_id) if ticket.customer_id else None
            if owner is None or not self.ctx.principal.can_access_customer(owner.customer_number):
                raise NotFoundError("Ticket not found", code="TICKET_NOT_FOUND")
        return await self._detail(ticket)

    async def list_for_customer(self, customer_number: str, page: PageParams) -> Page[TicketSummary]:
        customer = await self.ctx.owned_customer(customer_number)
        tickets, total = await self.repo.list_for_customer(customer.customer_id, page.offset, page.page_size)
        numbers = await self.repo.order_numbers({t.order_id for t in tickets if t.order_id})
        items = [self._summary(t, numbers.get(t.order_id)) for t in tickets]
        return Page(items=items, page=page.page, page_size=page.page_size, total=total,
                    has_more=page.offset + len(items) < total)

    @staticmethod
    def _summary(t: SupportTicket, order_number: str | None) -> TicketSummary:
        return TicketSummary(
            ticket_number=t.ticket_number, category=t.category, priority=t.priority, status=t.status,
            subject=t.subject, order_id=order_number, sla_due_at=t.sla_due_at, created_at=t.created_at,
        )

    async def _detail(self, t: SupportTicket) -> TicketDetail:
        numbers = await self.repo.order_numbers({t.order_id} if t.order_id else set())
        rma_number = None
        if t.return_id:
            rma = await self.ctx.session.get(ReturnRequest, t.return_id)
            rma_number = rma.rma_number if rma else None
        base = self._summary(t, numbers.get(t.order_id))
        return TicketDetail(
            **base.model_dump(),
            reason_code=t.reason_code,
            assigned_team=t.assigned_team,
            summary=t.summary,
            rma_number=rma_number,
            resolved_at=t.resolved_at,
            # Internal notes are never returned (visibility = 'internal').
            messages=[
                TicketMessageOut(author_type=m.author_type, body=m.body, created_at=m.created_at)
                for m in t.messages
                if m.visibility == "public"
            ],
        )
