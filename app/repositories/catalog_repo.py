from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.models import (
    Brand,
    GrapeVariety,
    InventoryLevel,
    Product,
    ProductGrape,
    ProductListing,
    ProductPrice,
    ProductVariant,
    Region,
    Store,
    VariantCertification,
    Warehouse,
)
from app.repositories.base import Repository


@dataclass
class ProductFilters:
    q: str | None = None
    product_type: str | None = None
    color: str | None = None
    wine_type: str | None = None
    sweetness: str | None = None
    body: str | None = None
    country: str | None = None
    region: str | None = None
    grape: str | None = None
    brand: str | None = None
    certification: str | None = None
    is_non_alcoholic: bool | None = None
    store_id: int | None = None
    variant_ids: list[int] | None = field(default=None)
    region_ids: list[int] | None = field(default=None)  # resolved from country/region by the service


@dataclass
class StockRow:
    store_id: int
    variant_id: int
    qty_on_hand: int
    qty_available: int


class CatalogRepository(Repository):
    async def region_map(self) -> dict[int, Region]:
        return {r.region_id: r for r in (await self.session.execute(select(Region))).scalars()}

    async def search_variants(
        self, f: ProductFilters, offset: int, limit: int, sort: str
    ) -> tuple[list[ProductVariant], int]:
        conds = [ProductVariant.status.in_(("active", "coming_soon")), Product.status == "active"]
        if f.q:
            like = f"%{f.q.lower()}%"
            conds.append(
                or_(
                    func.lower(Product.name).like(like),
                    func.lower(Brand.name).like(like),
                    func.lower(ProductVariant.sku).like(like),
                    func.lower(func.coalesce(Product.description, "")).like(like),
                    func.lower(func.coalesce(Product.tasting_notes, "")).like(like),
                )
            )
        for col, val in (
            (Product.product_type, f.product_type),
            (Product.wine_color, f.color),
            (Product.wine_type, f.wine_type),
            (Product.sweetness, f.sweetness),
            (Product.body, f.body),
        ):
            if val:
                conds.append(col == val)
        if f.is_non_alcoholic is not None:
            conds.append(
                (Product.product_type == "non_alcoholic_wine")
                if f.is_non_alcoholic
                else (Product.product_type != "non_alcoholic_wine")
            )
        if f.brand:
            conds.append(func.lower(Brand.name).like(f"%{f.brand.lower()}%"))
        if f.grape:
            conds.append(
                Product.product_id.in_(
                    select(ProductGrape.product_id)
                    .join(GrapeVariety, GrapeVariety.grape_id == ProductGrape.grape_id)
                    .where(
                        or_(
                            func.lower(GrapeVariety.name).like(f"%{f.grape.lower()}%"),
                            func.lower(func.coalesce(GrapeVariety.synonyms, "")).like(f"%{f.grape.lower()}%"),
                        )
                    )
                )
            )
        if f.certification:
            conds.append(
                ProductVariant.variant_id.in_(
                    select(VariantCertification.variant_id).where(
                        VariantCertification.certification_type == f.certification,
                        VariantCertification.status == "active",
                    )
                )
            )
        if f.region_ids is not None:
            conds.append(Product.region_id.in_(f.region_ids or [-1]))
        if f.store_id is not None:
            conds.append(
                ProductVariant.variant_id.in_(
                    select(ProductListing.variant_id).where(ProductListing.store_id == f.store_id)
                )
            )
        if f.variant_ids is not None:
            conds.append(ProductVariant.variant_id.in_(f.variant_ids or [-1]))

        base = (
            select(ProductVariant)
            .join(Product, Product.product_id == ProductVariant.product_id)
            .join(Brand, Brand.brand_id == Product.brand_id)
            .where(and_(*conds))
        )
        total = (await self.session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        order_col = {
            "name": Product.name,
            "vintage": ProductVariant.vintage_year,
            "brand": Brand.name,
            "sku": ProductVariant.sku,
        }.get(sort.lstrip("-"), Product.name)
        stmt = (
            base.options(*self._variant_options())
            .order_by(order_col.desc() if sort.startswith("-") else order_col.asc(), ProductVariant.variant_id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars()), int(total)

    @staticmethod
    def _variant_options():
        return (
            selectinload(ProductVariant.product).selectinload(Product.brand),
            selectinload(ProductVariant.product).selectinload(Product.grapes).selectinload(ProductGrape.grape),
            selectinload(ProductVariant.certifications),
            selectinload(ProductVariant.nutrition),
            selectinload(ProductVariant.accolades),
            selectinload(ProductVariant.listings),
        )

    async def get_variant_by_sku(self, sku: str) -> ProductVariant | None:
        stmt = select(ProductVariant).where(ProductVariant.sku == sku).options(*self._variant_options())
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def current_prices(
        self, variant_ids: list[int], now: datetime
    ) -> dict[tuple[int, int], dict[str, ProductPrice]]:
        """{(store_id, variant_id): {"regular": row, "sale": row}} effective at `now`."""
        if not variant_ids:
            return {}
        stmt = select(ProductPrice).where(
            ProductPrice.variant_id.in_(variant_ids),
            ProductPrice.starts_at <= now,
            or_(ProductPrice.ends_at.is_(None), ProductPrice.ends_at > now),
        )
        out: dict[tuple[int, int], dict[str, ProductPrice]] = {}
        for p in (await self.session.execute(stmt)).scalars():
            out.setdefault((p.store_id, p.variant_id), {})[p.price_type] = p
        return out

    async def stock(self, variant_ids: list[int]) -> dict[tuple[int, int], StockRow]:
        """Store-level stock across active warehouses (exact counts stay internal)."""
        if not variant_ids:
            return {}
        free = InventoryLevel.qty_on_hand - InventoryLevel.qty_reserved - InventoryLevel.safety_stock
        # per-row floor at 0 (SQLite's 2-arg max() == PostgreSQL's greatest())
        available = func.sum(func.max(free, 0) if self.dialect == "sqlite" else func.greatest(free, 0))
        stmt = (
            select(Warehouse.store_id, InventoryLevel.variant_id, func.sum(InventoryLevel.qty_on_hand), available)
            .join(Warehouse, Warehouse.warehouse_id == InventoryLevel.warehouse_id)
            .where(Warehouse.is_active.is_(True), InventoryLevel.variant_id.in_(variant_ids))
            .group_by(Warehouse.store_id, InventoryLevel.variant_id)
        )
        rows = (await self.session.execute(stmt)).all()
        return {(r[0], r[1]): StockRow(r[0], r[1], int(r[2] or 0), int(r[3] or 0)) for r in rows}

    async def stores(self) -> dict[int, Store]:
        return {s.store_id: s for s in (await self.session.execute(select(Store))).scalars()}
