"""Store information and delivery/shipping estimates (A-01, A-02, A-10..A-16)."""
from __future__ import annotations

from datetime import timedelta

from app.core.errors import NotFoundError
from app.models import Store
from app.repositories.misc_repo import StoreRepository
from app.schemas.support import (
    DeliveryEstimate,
    FulfillmentOption,
    StoreExceptionOut,
    StoreHoursOut,
    StoreInfo,
)
from app.services.context import ServiceContext

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# Local-delivery zones by ZIP (stand-in for distance from the store; a real
# deployment geocodes the address). Everything else in-state ships by carrier.
DELIVERY_ZONES: dict[str, dict[str, int]] = {
    "NJ": {"07030": 1, "07302": 1, "07310": 1, "07306": 1, "07087": 1, "07094": 2, "07047": 2, "07042": 2,
           "07102": 2, "07601": 2},
    "NY": {"10011": 1, "10001": 1, "10010": 1, "10014": 1, "10003": 1, "11101": 1, "11105": 2, "11201": 2,
           "11215": 2, "10025": 2},
}


def state_for_zip(postal_code: str) -> str | None:
    """USPS ZIP prefixes: NJ 070-089, NY 100-149 (005/063 edge cases ignored)."""
    prefix = int(postal_code[:3])
    if 70 <= prefix <= 89:
        return "NJ"
    if 100 <= prefix <= 149:
        return "NY"
    return None


class StoreService:
    def __init__(self, ctx: ServiceContext) -> None:
        self.ctx = ctx
        self.repo = StoreRepository(ctx.session)

    def _info(self, s: Store) -> StoreInfo:
        today = self.ctx.now.date()
        horizon = today + timedelta(days=60)
        return StoreInfo(
            store_code=s.store_code, name=s.name, state_code=s.state_code,
            address=f"{s.address_line1}, {s.city}, {s.state_code} {s.postal_code}", phone=s.phone_e164,
            timezone=s.timezone,
            hours=[StoreHoursOut(day=DAYS[h.day_of_week], opens_at=h.opens_at, closes_at=h.closes_at) for h in s.hours],
            upcoming_exceptions=[
                StoreExceptionOut(date=e.exception_date.isoformat(), is_closed=e.is_closed, opens_at=e.opens_at,
                                  closes_at=e.closes_at, note=e.note)
                for e in s.exceptions if today <= e.exception_date <= horizon
            ],
        )

    async def list_stores(self) -> list[StoreInfo]:
        return [self._info(s) for s in await self.repo.list()]

    async def get_store(self, store_code: str) -> StoreInfo:
        s = await self.repo.get_by_code(store_code)
        if s is None:
            raise NotFoundError("Store not found", code="STORE_NOT_FOUND")
        return self._info(s)

    async def estimate(self, postal_code: str, bottles: int, subtotal_cents: int | None) -> DeliveryEstimate:
        state = state_for_zip(postal_code)
        refs = ["A-01", "A-02"]
        if state is None:
            return DeliveryEstimate(
                postal_code=postal_code, state_code=None, serviceable=False, fulfilling_store=None, options=[],
                reason="We can only deliver or ship to addresses in New Jersey and New York.", policy_refs=refs,
            )
        store = await self.repo.get_by_state(state)
        rates = await self.repo.fulfillment_rates(store.store_id, self.ctx.now.date())
        options: list[FulfillmentOption] = []
        subtotal = subtotal_cents

        def gap(threshold: int | None) -> int | None:
            if threshold is None or subtotal is None:
                return None
            return max(threshold - subtotal, 0)

        pickup = next((r for r in rates if r.fulfillment_type == "pickup"), None)
        if pickup:
            options.append(FulfillmentOption(
                type="pickup", eligible=True, fee=pickup.fee_cents, order_minimum=None, free_threshold=None,
                free_delivery_gap=None, estimate="Ready in about 2 hours during store hours; held 7 days",
                notes=["Bring a valid 21+ photo ID (A-05)."],
            ))
        zone = DELIVERY_ZONES.get(state, {}).get(postal_code)
        local = next((r for r in rates if r.fulfillment_type == "local_delivery" and r.zone == zone), None)
        if local:
            free = subtotal is not None and local.free_threshold_cents and subtotal >= local.free_threshold_cents
            below_min = subtotal is not None and subtotal < local.order_minimum_cents
            options.append(FulfillmentOption(
                type="local_delivery", eligible=not below_min, fee=0 if free else local.fee_cents,
                order_minimum=local.order_minimum_cents, free_threshold=local.free_threshold_cents,
                free_delivery_gap=gap(local.free_threshold_cents), zone=zone,
                estimate="Same day if ordered by 6 pm Mon-Sat / 3 pm Sun; 2-hour windows 11 am-9 pm",
                notes=["An adult 21+ must receive the order; no leave-at-door (A-20)."]
                + (["Below the $40 product minimum for delivery (A-11)."] if below_min else []),
            ))
            refs += ["A-10", "A-11", "A-12", "A-13"]
        ship = sorted((r for r in rates if r.fulfillment_type == "shipping"), key=lambda r: r.min_bottles or 0)
        if ship:
            band = next((r for r in ship if (r.max_bottles or 10**6) >= bottles), ship[-1])
            fee = band.fee_cents
            if bottles > (band.max_bottles or bottles):
                extra_blocks = -(-(bottles - band.max_bottles) // 6)
                fee += extra_blocks * band.extra_fee_per_6_bottles_cents
            free = subtotal is not None and band.free_threshold_cents and subtotal >= band.free_threshold_cents
            options.append(FulfillmentOption(
                type="shipping", eligible=True, fee=0 if free else fee, order_minimum=None,
                free_threshold=band.free_threshold_cents, free_delivery_gap=gap(band.free_threshold_cents),
                estimate="1-3 business days by adult-signature carrier",
                notes=["Weather holds may apply above 85°F or below 28°F (A-19).",
                       "No PO boxes, schools or dorms (A-20)."],
            ))
            refs += ["A-15", "A-19"]
        return DeliveryEstimate(
            postal_code=postal_code, state_code=state, serviceable=True, fulfilling_store=store.store_code,
            options=options, reason=None if zone else "Outside local-delivery zones: carrier shipping or pickup.",
            policy_refs=sorted(set(refs)),
        )
