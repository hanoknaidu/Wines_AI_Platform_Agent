from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from app.core.money import Money, MoneyOpt
from app.schemas.common import ApiModel, UtcDateTime

Location = Literal["NJ", "NY"]


class Taste(ApiModel):
    sweetness: str | None
    body: str | None
    acidity: str | None
    tannin: str | None
    oak: str | None
    fruit_profile: str | None


class Availability(ApiModel):
    location: str
    stock_status: str
    qty_bucket: str | None
    sellable_in_jurisdiction: bool
    allocation_limit: int | None
    max_per_order: int
    next_arrival_estimate: date | None


class PriceOut(ApiModel):
    location: str
    unit_price: Money
    regular_price: Money
    sale_price: MoneyOpt
    sale_ends_at: UtcDateTime | None
    compare_at_price: MoneyOpt
    compare_at_verified: bool
    case_discount_eligible: bool


class ProductSummary(ApiModel):
    sku: str
    name: str
    brand: str
    product_type: str
    color: str | None
    wine_type: str | None
    vintage: int | None
    size_ml: int
    region_path: str | None
    grapes: list[str]
    taste: Taste
    certifications: list[str]
    price: PriceOut | None
    availability: Availability | None


class Certification(ApiModel):
    type: str
    evidence_level: str
    certifier: str | None
    evidence_ref: str
    verified_at: UtcDateTime


class Nutrition(ApiModel):
    serving_ml: int
    calories: int
    carbs_g: Decimal | None
    sugar_g: Decimal | None
    source: str


class Accolade(ApiModel):
    source: str
    score: int | None
    award: str | None
    year: int


class ProductDetail(ProductSummary):
    description: str | None
    tasting_notes: str | None
    food_pairings: str | None
    allergen_notes: str | None
    abv_percent: Decimal
    closure: str | None
    sparkling_sweetness: str | None
    style: str | None
    vintage_specific: bool
    collectible: bool
    final_sale: bool
    grape_blend: list[dict]
    nutrition: Nutrition | None
    certification_details: list[Certification]
    accolades: list[Accolade]
    prices: list[PriceOut]
    availability_by_location: list[Availability]
