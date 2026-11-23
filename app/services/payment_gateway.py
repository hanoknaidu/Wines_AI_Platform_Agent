"""Payment processor port. The simulated adapter is deterministic and has no
network calls; swap in a real processor client (Stripe, Adyen...) behind the
same interface. Card data never passes through here: only processor refs."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GatewayResult:
    status: str  # succeeded | pending | failed
    reference: str
    failure_code: str | None = None


class PaymentGateway(Protocol):
    async def refund(self, processor_payment_ref: str, amount_cents: int, idempotency_key: str) -> GatewayResult: ...

    async def void(self, processor_payment_ref: str, amount_cents: int, idempotency_key: str) -> GatewayResult: ...


class SimulatedPaymentGateway:
    @staticmethod
    def _ref(prefix: str, key: str) -> str:
        return f"{prefix}_sim_{hashlib.sha256(key.encode()).hexdigest()[:20]}"

    async def refund(self, processor_payment_ref: str, amount_cents: int, idempotency_key: str) -> GatewayResult:
        return GatewayResult("succeeded", self._ref("re", idempotency_key))

    async def void(self, processor_payment_ref: str, amount_cents: int, idempotency_key: str) -> GatewayResult:
        return GatewayResult("succeeded", self._ref("vd", idempotency_key))
