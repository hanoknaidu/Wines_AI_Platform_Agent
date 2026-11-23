"""Catalog, price and availability. Exact stock counts and costs never leave
this service: only the KB stock_status vocabulary and qty buckets."""
from __future__ import annotations

from dataclasses import dataclass

from app.core.errors import NotFoundError
from app.models import ProductListing, ProductPrice, ProductVariant, Region, Store
from app.repositories.catalog_repo import CatalogRepository, ProductFilters, StockRow
from app.schemas.catalog import (
    Accolade,
    Availability,
    Certification,
    Nutrition,
    PriceOut,
    ProductDetail,
    ProductSummary,
    Taste,
)
from app.schemas.common import Page, PageParams
from app.services.context import ServiceContext


@dataclass
class SearchParams:
    filters: ProductFilters
    country: str | None = None
    region: str | None = None
    location: str | None = None
    price_min_cents: int | None = None
    price_max_cents: int | None = None
    in_stock_only: bool = False
    sort: str = "name"


def availability(listing: ProductListing, store: Store, stock: StockRow | None) -> Availability:
    """Same mapping as _DB view v_inventory_availability (KB stock_status)."""
    qty = stock.qty_available if stock else 0
    bucket = "12+" if qty >= 12 else "6-11" if qty >= 6 else "1-5" if qty >= 1 else None
    if not listing.is_sellable:
        status = "not_sellable_in_jurisdiction"
    elif listing.listing_status != "active":
        status = listing.listing_status
    elif qty > 0 and listing.allocation_limit is not None:
        status = "allocated"
    elif qty >= 6:
        status = "in_stock"
    elif qty >= 1:
        status = "low_stock"
    elif listing.allocation_limit is not None:
        status = "waitlist"
    elif listing.backorder_allowed:
        status = "backorder"
    else:
        status = "out_of_stock"
    return Availability(
        location=store.state_code, stock_status=status, qty_bucket=bucket if listing.is_sellable else None,
        sellable_in_jurisdiction=listing.is_sellable, allocation_limit=listing.allocation_limit,
        max_per_order=listing.max_per_order, next_arrival_estimate=listing.next_arrival_estimate,
    )


def price_out(prices: dict[str, ProductPrice], store: Store, variant: ProductVariant) -> PriceOut | None:
    regular, sale = prices.get("regular"), prices.get("sale")
    if regular is None:
        return None
    effective = sale or regular
    return PriceOut(
        location=store.state_code, unit_price=effective.amount_cents, regular_price=regular.amount_cents,
        sale_price=sale.amount_cents if sale else None, sale_ends_at=sale.ends_at if sale else None,
        compare_at_price=effective.compare_at_cents, compare_at_verified=effective.compare_at_verified,
        case_discount_eligible=variant.case_discount_eligible,
    )


def region_path(region_id: int | None, regions: dict[int, Region]) -> str | None:
    parts, seen = [], set()
    while region_id and region_id in regions and region_id not in seen:
        seen.add(region_id)
        parts.append(regions[region_id].name)
        region_id = regions[region_id].parent_region_id
    return " > ".join(reversed(parts)) or None


class CatalogService:
    def __init__(self, ctx: ServiceContext) -> None:
        self.ctx = ctx
        self.repo = CatalogRepository(ctx.session)

    def _region_ids(self, regions: dict[int, Region], country: str | None, name: str | None) -> list[int] | None:
        if not country and not name:
            return None
        roots = [
            r.region_id for r in regions.values()
            if (country and r.region_level == "country"
                and (r.name.lower() == country.lower() or r.country_code.lower() == country.lower()))
            or (name and name.lower() in r.name.lower())
        ]
        children: dict[int, list[int]] = {}
        for r in regions.values():
            if r.parent_region_id:
                children.setdefault(r.parent_region_id, []).append(r.region_id)
        out, stack = set(), list(roots)
        while stack:
            rid = stack.pop()
            if rid not in out:
                out.add(rid)
                stack.extend(children.get(rid, []))
        return sorted(out)

    async def _summaries(self, variants: list[ProductVariant], location: str | None) -> list[ProductSummary]:
        stores = await self.repo.stores()
        regions = await self.repo.region_map()
        ids = [v.variant_id for v in variants]
        prices = await self.repo.current_prices(ids, self.ctx.now)
        stock = await self.repo.stock(ids)
        store = next((s for s in stores.values() if s.state_code == location), None) if location else None
        out = []
        for v in variants:
            out.append(self._summary(v, store, stores, regions, prices, stock))
        return out

    def _summary(self, v, store, stores, regions, prices, stock) -> ProductSummary:
        p = v.product
        listing = next((pl for pl in v.listings if store and pl.store_id == store.store_id), None)
        return ProductSummary(
            sku=v.sku, name=p.name, brand=p.brand.name, product_type=p.product_type, color=p.wine_color,
            wine_type=p.wine_type, vintage=v.vintage_year, size_ml=v.size_ml,
            region_path=region_path(p.region_id, regions),
            grapes=[g.grape.name for g in sorted(p.grapes, key=lambda g: -(g.percentage or 0))],
            taste=Taste(sweetness=p.sweetness, body=p.body, acidity=p.acidity, tannin=p.tannin, oak=p.oak,
                        fruit_profile=p.fruit_profile),
            certifications=sorted(c.certification_type for c in v.certifications if c.status == "active"),
            price=price_out(prices.get((store.store_id, v.variant_id), {}), store, v) if store and listing else None,
            availability=availability(listing, store, stock.get((store.store_id, v.variant_id)))
            if store and listing else None,
        )

    async def search(self, params: SearchParams, page: PageParams) -> Page[ProductSummary]:
        f = params.filters
        regions = await self.repo.region_map()
        f.region_ids = self._region_ids(regions, params.country, params.region)
        store = None
        if params.location:
            stores = await self.repo.stores()
            store = next((s for s in stores.values() if s.state_code == params.location), None)
            f.store_id = store.store_id if store else -1
        price_filtered = params.price_min_cents is not None or params.price_max_cents is not None
        if not (price_filtered or params.in_stock_only):
            variants, total = await self.repo.search_variants(f, page.offset, page.page_size, params.sort)
            items = await self._summaries(variants, params.location)
            return Page(items=items, page=page.page, page_size=page.page_size, total=total,
                        has_more=page.offset + len(items) < total)
        # Price / stock are live per store: filter after pricing (catalog is small;
        # at scale this moves to a search index with denormalized price/stock).
        variants, _ = await self.repo.search_variants(f, 0, 1000, params.sort)
        summaries = await self._summaries(variants, params.location)

        def keep(s: ProductSummary) -> bool:
            if params.in_stock_only and not (s.availability and s.availability.stock_status
                                             in ("in_stock", "low_stock", "allocated")):
                return False
            if price_filtered:
                if s.price is None:
                    return False
                if params.price_min_cents is not None and s.price.unit_price < params.price_min_cents:
                    return False
                if params.price_max_cents is not None and s.price.unit_price > params.price_max_cents:
                    return False
            return True

        kept = [s for s in summaries if keep(s)]
        if params.sort.lstrip("-") == "price":
            kept.sort(key=lambda s: s.price.unit_price if s.price else 0, reverse=params.sort.startswith("-"))
        items = kept[page.offset : page.offset + page.page_size]
        return Page(items=items, page=page.page, page_size=page.page_size, total=len(kept),
                    has_more=page.offset + len(items) < len(kept))

    async def detail(self, sku: str) -> ProductDetail:
        v = await self.repo.get_variant_by_sku(sku)
        if v is None or v.status == "archived":
            raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")
        stores = await self.repo.stores()
        regions = await self.repo.region_map()
        prices = await self.repo.current_prices([v.variant_id], self.ctx.now)
        stock = await self.repo.stock([v.variant_id])
        base = self._summary(v, None, stores, regions, prices, stock)
        p = v.product
        price_list, avail_list = [], []
        for pl in sorted(v.listings, key=lambda x: x.store_id):
            store = stores[pl.store_id]
            if (pr := price_out(prices.get((store.store_id, v.variant_id), {}), store, v)) is not None:
                price_list.append(pr)
            avail_list.append(availability(pl, store, stock.get((store.store_id, v.variant_id))))
        n = v.nutrition
        return ProductDetail(
            **base.model_dump(),
            description=p.description, tasting_notes=p.tasting_notes, food_pairings=p.food_pairings,
            allergen_notes=p.allergen_notes, abv_percent=v.abv_percent, closure=p.closure_type,
            sparkling_sweetness=p.sparkling_sweetness, style=p.style_code, vintage_specific=v.is_vintage_specific,
            collectible=v.is_collectible, final_sale=v.is_final_sale,
            grape_blend=[{"grape": g.grape.name, "percentage": g.percentage} for g in p.grapes],
            nutrition=Nutrition(serving_ml=n.serving_ml, calories=n.calories, carbs_g=n.carbs_g, sugar_g=n.sugar_g,
                                source=n.source) if n else None,
            certification_details=[
                Certification(type=c.certification_type, evidence_level=c.evidence_level, certifier=c.certifier,
                              evidence_ref=c.evidence_ref, verified_at=c.verified_at)
                for c in v.certifications if c.status == "active"
            ],
            accolades=[Accolade(source=a.source, score=a.score, award=a.award, year=a.awarded_year)
                       for a in v.accolades],
            prices=price_list,
            availability_by_location=avail_list,
        )

    async def availability(self, sku: str, location: str) -> Availability:
        v = await self.repo.get_variant_by_sku(sku)
        if v is None:
            raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")
        stores = await self.repo.stores()
        store = next(s for s in stores.values() if s.state_code == location)
        listing = next((pl for pl in v.listings if pl.store_id == store.store_id), None)
        if listing is None:
            return Availability(location=location, stock_status="not_sellable_in_jurisdiction", qty_bucket=None,
                                sellable_in_jurisdiction=False, allocation_limit=None, max_per_order=0,
                                next_arrival_estimate=None)
        stock = await self.repo.stock([v.variant_id])
        return availability(listing, store, stock.get((store.store_id, v.variant_id)))
