"""ServiceContext bundles what every service needs (DB session, clock,
settings, caller identity) and provides ownership checks + audit logging."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.config import Settings
from app.core.errors import NotFoundError
from app.core.masking import redact_mapping
from app.core.request_context import get_request_id
from app.core.security import Principal
from app.models import AuditLog, Customer, Order
from app.repositories.customer_repo import CustomerRepository
from app.repositories.misc_repo import AuditRepository
from app.repositories.order_repo import OrderRepository


@dataclass
class ServiceContext:
    session: AsyncSession
    clock: Clock
    settings: Settings
    principal: Principal
    client_ip: str | None = None

    @property
    def now(self):
        return self.clock.now()

    @property
    def actor_ref(self) -> str:
        if self.principal.role == "agent":
            return f"ai-agent:{self.principal.run_id or 'unknown'}"
        return self.principal.subject

    # --- ownership ---------------------------------------------------------
    async def owned_customer(self, customer_number: str) -> Customer:
        """404 (not 403) for someone else's customer record: no enumeration."""
        if not self.principal.can_access_customer(customer_number):
            raise NotFoundError("Customer not found", code="CUSTOMER_NOT_FOUND")
        customer = await CustomerRepository(self.session).get_by_number(customer_number)
        if customer is None or customer.status == "anonymized":
            raise NotFoundError("Customer not found", code="CUSTOMER_NOT_FOUND")
        return customer

    async def owned_order(self, order_number: str, *, for_update: bool = False) -> Order:
        order = await OrderRepository(self.session).get_full(order_number, for_update=for_update)
        if order is None or not self.principal.can_access_customer(order.customer.customer_number):
            raise NotFoundError("Order not found", code="ORDER_NOT_FOUND")
        return order

    # --- audit ---------------------------------------------------------------
    def audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        *,
        customer_id: int | None,
        outcome: str = "success",
        reason: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> None:
        AuditRepository(self.session).append(
            AuditLog(
                occurred_at=self.now,
                actor_type=self.principal.actor_type,
                actor_ref=self.actor_ref,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                customer_id=customer_id,
                outcome=outcome,
                reason=reason,
                conversation_id=self.principal.session_id,
                request_id=get_request_id(),
                idempotency_key=idempotency_key,
                before_state=redact_mapping(before) if before else None,
                after_state=redact_mapping(after) if after else None,
                ip_address=self.client_ip,
            )
        )
