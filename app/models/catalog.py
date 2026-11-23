"""Wine-aware catalog, per-store listings/prices, availability and fees.

product_costs (landed cost, NJ below-cost floor) is intentionally NOT mapped:
no API, and therefore no agent tool, can ever read it."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigId, UTCDateTime, in_


class Region(Base):
    __tablename__ = "regions"

    region_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    parent_region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.region_id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    region_level: Mapped[str] = mapped_column(String(20))
    country_code: Mapped[str] = mapped_column(String(2))
    appellation_system: Mapped[str | None] = mapped_column(String(10))


class Brand(Base):
    __tablename__ = "brands"

    brand_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    brand_type: Mapped[str] = mapped_column(String(40))
    home_region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.region_id"))
    founded_year: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class GrapeVariety(Base):
    __tablename__ = "grape_varieties"

    grape_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    skin_color: Mapped[str] = mapped_column(String(10))
    synonyms: Mapped[str | None] = mapped_column(String(200))


class WineStyle(Base):
    __tablename__ = "wine_styles"

    style_code: Mapped[str] = mapped_column(String(40), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str] = mapped_column(Text)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            in_("product_type", ("wine", "spirit", "beer", "cider", "sake", "non_alcoholic_wine")),
            name="product_type",
        ),
        Index("ix_products_search", "product_type", "wine_color", "sweetness", "body"),
    )

    product_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    product_code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.brand_id"), index=True)
    product_type: Mapped[str] = mapped_column(String(30))
    wine_color: Mapped[str | None] = mapped_column(String(10))
    wine_type: Mapped[str | None] = mapped_column(String(20))
    style_code: Mapped[str | None] = mapped_column(ForeignKey("wine_styles.style_code"))
    region_id: Mapped[int | None] = mapped_column(ForeignKey("regions.region_id"), index=True)
    sweetness: Mapped[str | None] = mapped_column(String(20))
    body: Mapped[str | None] = mapped_column(String(10))
    acidity: Mapped[str | None] = mapped_column(String(10))
    tannin: Mapped[str | None] = mapped_column(String(10))
    oak: Mapped[str | None] = mapped_column(String(12))
    fruit_profile: Mapped[str | None] = mapped_column(String(20))
    sparkling_sweetness: Mapped[str | None] = mapped_column(String(20))
    closure_type: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text)
    tasting_notes: Mapped[str | None] = mapped_column(Text)
    food_pairings: Mapped[str | None] = mapped_column(Text)
    allergen_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    brand: Mapped[Brand] = relationship(lazy="raise_on_sql")
    region: Mapped[Region | None] = relationship(lazy="raise_on_sql")
    grapes: Mapped[list[ProductGrape]] = relationship(lazy="raise_on_sql")


class ProductGrape(Base):
    __tablename__ = "product_grapes"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), primary_key=True)
    grape_id: Mapped[int] = mapped_column(ForeignKey("grape_varieties.grape_id"), primary_key=True, index=True)
    percentage: Mapped[int | None] = mapped_column(Integer)

    grape: Mapped[GrapeVariety] = relationship(lazy="raise_on_sql")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    variant_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), index=True)
    sku: Mapped[str] = mapped_column(String(40), unique=True)
    gtin: Mapped[str | None] = mapped_column(String(14), unique=True)
    vintage_year: Mapped[int | None] = mapped_column(Integer)
    size_ml: Mapped[int] = mapped_column(Integer)
    pack_quantity: Mapped[int] = mapped_column(Integer, default=1)
    container_type: Mapped[str] = mapped_column(String(20), default="bottle")
    abv_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    is_vintage_specific: Mapped[bool] = mapped_column(Boolean, default=False)
    is_collectible: Mapped[bool] = mapped_column(Boolean, default=False)
    is_final_sale: Mapped[bool] = mapped_column(Boolean, default=False)
    case_discount_eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    weight_grams: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)

    product: Mapped[Product] = relationship(lazy="raise_on_sql")
    certifications: Mapped[list[VariantCertification]] = relationship(lazy="raise_on_sql")
    nutrition: Mapped[VariantNutrition | None] = relationship(lazy="raise_on_sql")
    accolades: Mapped[list[ProductAccolade]] = relationship(lazy="raise_on_sql")
    listings: Mapped[list[ProductListing]] = relationship(lazy="raise_on_sql")


class VariantCertification(Base):
    __tablename__ = "variant_certifications"

    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.variant_id"), primary_key=True)
    certification_type: Mapped[str] = mapped_column(String(40), primary_key=True)
    evidence_level: Mapped[str] = mapped_column(String(20))
    certifier: Mapped[str | None] = mapped_column(String(120))
    evidence_ref: Mapped[str] = mapped_column(String(200))
    verified_at: Mapped[datetime] = mapped_column(UTCDateTime)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    status: Mapped[str] = mapped_column(String(20), default="active")


class VariantNutrition(Base):
    __tablename__ = "variant_nutrition"

    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.variant_id"), primary_key=True)
    serving_ml: Mapped[int] = mapped_column(Integer)
    calories: Mapped[int] = mapped_column(Integer)
    carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    residual_sugar_g_per_l: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    source: Mapped[str] = mapped_column(String(30))
    verified_at: Mapped[datetime] = mapped_column(UTCDateTime)


class ProductAccolade(Base):
    __tablename__ = "product_accolades"

    accolade_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.variant_id"), index=True)
    source: Mapped[str] = mapped_column(String(120))
    score: Mapped[int | None] = mapped_column(Integer)
    award: Mapped[str | None] = mapped_column(String(120))
    awarded_year: Mapped[int] = mapped_column(Integer)


class ProductListing(Base):
    __tablename__ = "product_listings"

    store_id: Mapped[int] = mapped_column(ForeignKey("stores.store_id"), primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.variant_id"), primary_key=True, index=True)
    listing_status: Mapped[str] = mapped_column(String(30), default="active")
    is_sellable: Mapped[bool] = mapped_column(Boolean, default=True)
    not_sellable_reason: Mapped[str | None] = mapped_column(Text)
    backorder_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    allocation_limit: Mapped[int | None] = mapped_column(Integer)
    max_per_order: Mapped[int] = mapped_column(Integer, default=36)
    next_arrival_estimate: Mapped[date | None] = mapped_column(Date)
    online_only: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)


class ProductPrice(Base):
    __tablename__ = "product_prices"
    __table_args__ = (
        ForeignKeyConstraint(
            ["store_id", "variant_id"], ["product_listings.store_id", "product_listings.variant_id"]
        ),
        CheckConstraint(in_("price_type", ("regular", "sale")), name="price_type"),
        CheckConstraint("amount_cents > 0", name="amount_positive"),
        Index("ix_prices_lookup", "store_id", "variant_id", "price_type", "starts_at"),
    )

    price_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    store_id: Mapped[int] = mapped_column(BigId)
    variant_id: Mapped[int] = mapped_column(BigId, index=True)
    price_type: Mapped[str] = mapped_column(String(10))
    amount_cents: Mapped[int] = mapped_column(Integer)
    compare_at_cents: Mapped[int | None] = mapped_column(Integer)
    compare_at_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime)
    ends_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    change_reason: Mapped[str] = mapped_column(Text)
    created_by_staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff_users.staff_id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)


class InventoryLevel(Base):
    """Exact counts stay internal; APIs expose only stock_status + qty_bucket."""

    __tablename__ = "inventory_levels"
    __table_args__ = (
        CheckConstraint("qty_on_hand >= 0", name="qty_on_hand"),
        CheckConstraint("qty_reserved >= 0 AND qty_reserved <= qty_on_hand", name="qty_reserved"),
    )

    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.warehouse_id"), primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("product_variants.variant_id"), primary_key=True, index=True)
    qty_on_hand: Mapped[int] = mapped_column(Integer, default=0)
    qty_reserved: Mapped[int] = mapped_column(Integer, default=0)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0)
    bin_location: Mapped[str | None] = mapped_column(String(40))
    last_counted_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)


class FulfillmentRate(Base):
    __tablename__ = "fulfillment_rates"
    __table_args__ = (Index("ix_fulfillment_rates_store", "store_id", "fulfillment_type"),)

    rate_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.store_id"))
    fulfillment_type: Mapped[str] = mapped_column(String(20))
    zone: Mapped[int | None] = mapped_column(Integer)
    min_distance_miles: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    max_distance_miles: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    min_bottles: Mapped[int | None] = mapped_column(Integer)
    max_bottles: Mapped[int | None] = mapped_column(Integer)
    fee_cents: Mapped[int] = mapped_column(Integer)
    extra_fee_per_6_bottles_cents: Mapped[int] = mapped_column(Integer, default=0)
    order_minimum_cents: Mapped[int] = mapped_column(Integer, default=0)
    free_threshold_cents: Mapped[int | None] = mapped_column(Integer)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class Promotion(Base):
    __tablename__ = "promotions"

    promotion_id: Mapped[int] = mapped_column(BigId, primary_key=True)
    code: Mapped[str | None] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120))
    promo_type: Mapped[str] = mapped_column(String(20))
    percent_off_bps: Mapped[int | None] = mapped_column(Integer)
    amount_off_cents: Mapped[int | None] = mapped_column(Integer)
    min_subtotal_cents: Mapped[int] = mapped_column(Integer, default=0)
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.store_id"))
    channel: Mapped[str] = mapped_column(String(20), default="all")
    is_stackable: Mapped[bool] = mapped_column(Boolean, default=False)
    max_redemptions: Mapped[int | None] = mapped_column(Integer)
    max_per_customer: Mapped[int | None] = mapped_column(Integer)
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime)
    ends_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    status: Mapped[str] = mapped_column(String(20), default="active")
    terms: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
