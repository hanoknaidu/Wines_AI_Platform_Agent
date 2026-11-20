-- =============================================================================
-- Wines AI Platform Agent: E-commerce Customer Database (phase 2, part A)
-- Engine: SQLite >= 3.38 (STRICT tables, JSON1). Designed to port to PostgreSQL.
--
-- Conventions (see database/README.md for the full rationale)
--   * Surrogate keys: <table_singular>_id INTEGER PRIMARY KEY  (PG: BIGINT IDENTITY)
--   * Public, non-enumerable business keys for anything shown to customers or
--     the AI agent: customer_number, order_number, rma_number, ticket_number ...
--   * Money: INTEGER cents, column suffix _cents, currency_code 'USD'.
--   * Rates: discounts in basis points (_bps, 1000 = 10%); tax in parts per
--     million (_ppm, 66250 = 6.625%) because tax rates have 3 decimals.
--   * Timestamps: TEXT ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ' (PG: TIMESTAMPTZ).
--     Dates: TEXT 'YYYY-MM-DD' (PG: DATE). Booleans: INTEGER 0/1 (PG: BOOLEAN).
--   * Enumerations: TEXT + CHECK (... IN (...)). Values match _KB/00_system.
--   * JSON: TEXT + CHECK (json_valid(...)) (PG: JSONB).
--   * Ledgers (inventory, payments, loyalty, store credit, gift cards, audit,
--     status history, tracking events) are append-only; triggers enforce it.
--   * Every foreign-key column is indexed (SQLite and PG do not do it for you).
--   * PRAGMA foreign_keys = ON must be set on EVERY connection.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 1. ORGANIZATION: licensed stores, hours, warehouses, staff
-- -----------------------------------------------------------------------------

-- A store is a licensed seller of record (A-01). Prices, assortment and tax
-- follow the store. Orders are always fulfilled by a store in the delivery state.
CREATE TABLE stores (
    store_id          INTEGER PRIMARY KEY,
    store_code        TEXT    NOT NULL UNIQUE,                 -- 'NJ-HOB'
    name              TEXT    NOT NULL,
    legal_name        TEXT    NOT NULL,
    state_code        TEXT    NOT NULL CHECK (state_code IN ('NJ','NY')),
    license_type      TEXT    NOT NULL,                        -- 'NJ Plenary Retail Distribution'
    license_number    TEXT    NOT NULL UNIQUE,
    address_line1     TEXT    NOT NULL,
    address_line2     TEXT,
    city              TEXT    NOT NULL,
    postal_code       TEXT    NOT NULL CHECK (length(postal_code) = 5),
    phone_e164        TEXT    NOT NULL CHECK (phone_e164 LIKE '+1%'),
    email             TEXT    NOT NULL,
    timezone          TEXT    NOT NULL DEFAULT 'America/New_York',
    is_active         INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (store_id, state_code)          -- target for composite FKs (state consistency)
) STRICT;

CREATE TABLE store_hours (
    store_id     INTEGER NOT NULL REFERENCES stores(store_id),
    day_of_week  INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),   -- 0 = Sunday
    opens_at     TEXT    NOT NULL CHECK (opens_at  GLOB '[0-2][0-9]:[0-5][0-9]'),
    closes_at    TEXT    NOT NULL CHECK (closes_at GLOB '[0-2][0-9]:[0-5][0-9]'),
    PRIMARY KEY (store_id, day_of_week),
    CHECK (closes_at > opens_at)
) STRICT;

-- Holidays and one-off changes (A-82). is_closed = 1 means no hours that day.
CREATE TABLE store_hours_exceptions (
    store_id     INTEGER NOT NULL REFERENCES stores(store_id),
    exception_date TEXT  NOT NULL,
    is_closed    INTEGER NOT NULL DEFAULT 0 CHECK (is_closed IN (0,1)),
    opens_at     TEXT,
    closes_at    TEXT,
    note         TEXT,
    PRIMARY KEY (store_id, exception_date),
    CHECK ((is_closed = 1 AND opens_at IS NULL AND closes_at IS NULL)
        OR (is_closed = 0 AND opens_at IS NOT NULL AND closes_at > opens_at))
) STRICT;

-- Physical inventory locations. A warehouse belongs to exactly one store and
-- must be in the same state (composite FK), so stock can never cross state lines.
CREATE TABLE warehouses (
    warehouse_id      INTEGER PRIMARY KEY,
    store_id          INTEGER NOT NULL,
    state_code        TEXT    NOT NULL,
    warehouse_code    TEXT    NOT NULL UNIQUE,
    name              TEXT    NOT NULL,
    warehouse_type    TEXT    NOT NULL CHECK (warehouse_type IN ('store_floor','fulfillment_center','temperature_controlled_cellar')),
    is_pickup_point   INTEGER NOT NULL DEFAULT 0 CHECK (is_pickup_point IN (0,1)),
    ships_by_carrier  INTEGER NOT NULL DEFAULT 0 CHECK (ships_by_carrier IN (0,1)),
    runs_local_delivery INTEGER NOT NULL DEFAULT 0 CHECK (runs_local_delivery IN (0,1)),
    address_line1     TEXT    NOT NULL,
    city              TEXT    NOT NULL,
    postal_code       TEXT    NOT NULL CHECK (length(postal_code) = 5),
    is_active         INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (store_id, state_code) REFERENCES stores(store_id, state_code),
    UNIQUE (warehouse_id, store_id)        -- target for shipment/order consistency
) STRICT;
CREATE INDEX ix_warehouses_store ON warehouses(store_id, state_code);

CREATE TABLE staff_users (
    staff_id       INTEGER PRIMARY KEY,
    employee_code  TEXT    NOT NULL UNIQUE,
    full_name      TEXT    NOT NULL,
    email          TEXT    NOT NULL,
    role           TEXT    NOT NULL CHECK (role IN ('support_agent','support_lead','fulfillment','finance','compliance','pricing','catalog','events','admin')),
    store_id       INTEGER REFERENCES stores(store_id),
    is_active      INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
) STRICT;
CREATE UNIQUE INDEX ux_staff_email ON staff_users(lower(email));
CREATE INDEX ix_staff_store ON staff_users(store_id);

-- -----------------------------------------------------------------------------
-- 2. CUSTOMER MANAGEMENT
-- -----------------------------------------------------------------------------

-- Account required to order (A-75). 21+ enforced at creation (A-04): the CHECK
-- uses created_at, not 'now', so it is deterministic and portable.
-- Customers are never hard-deleted: privacy deletion anonymizes PII (A-73).
CREATE TABLE customers (
    customer_id       INTEGER PRIMARY KEY,
    customer_number   TEXT    NOT NULL UNIQUE,                  -- 'C-100001' (public)
    first_name        TEXT    NOT NULL,
    last_name         TEXT    NOT NULL,
    email             TEXT    NOT NULL,
    phone_e164        TEXT    CHECK (phone_e164 IS NULL OR phone_e164 LIKE '+%'),
    date_of_birth     TEXT    NOT NULL,
    status            TEXT    NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active','locked','suspended','closed','anonymized')),
    status_reason     TEXT,
    home_store_id     INTEGER REFERENCES stores(store_id),
    marketing_source  TEXT,
    last_login_at     TEXT,
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    CHECK (date_of_birth <= date(created_at, '-21 years')),
    CHECK (status = 'active' OR status_reason IS NOT NULL)
) STRICT;
CREATE UNIQUE INDEX ux_customers_email ON customers(lower(email));
CREATE INDEX ix_customers_phone ON customers(phone_e164);
CREATE INDEX ix_customers_name ON customers(last_name, first_name);
CREATE INDEX ix_customers_home_store ON customers(home_store_id);

-- Third-party ID verification attempts (A-05). Latest row = current status;
-- see view v_customer_age_verification. ID images are never stored (A-74).
CREATE TABLE age_verifications (
    age_verification_id INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    status          TEXT    NOT NULL CHECK (status IN ('pending','verified','failed','manual_review')),
    method          TEXT    NOT NULL CHECK (method IN ('document_scan','database_check','manual_review','in_person')),
    provider        TEXT    NOT NULL,
    provider_reference TEXT,
    failure_reason  TEXT,
    started_at      TEXT    NOT NULL,
    completed_at    TEXT,
    CHECK (status IN ('pending','manual_review') OR completed_at IS NOT NULL),
    CHECK (status <> 'failed' OR failure_reason IS NOT NULL)
) STRICT;
CREATE INDEX ix_age_verifications_customer ON age_verifications(customer_id, started_at);

-- Saved addresses (max 10 per customer, A-75). Billing addresses may be in any
-- US state; delivery is restricted to NJ/NY at the order level (A-02).
CREATE TABLE customer_addresses (
    address_id        INTEGER PRIMARY KEY,
    customer_id       INTEGER NOT NULL REFERENCES customers(customer_id),
    label             TEXT,
    recipient_name    TEXT    NOT NULL,
    line1             TEXT    NOT NULL,
    line2             TEXT,
    city              TEXT    NOT NULL,
    state_code        TEXT    NOT NULL CHECK (length(state_code) = 2 AND state_code = upper(state_code)),
    postal_code       TEXT    NOT NULL CHECK (length(postal_code) = 5),
    country_code      TEXT    NOT NULL DEFAULT 'US' CHECK (country_code = 'US'),
    phone_e164        TEXT,
    address_type      TEXT    NOT NULL DEFAULT 'residential'
                      CHECK (address_type IN ('residential','business','hotel','po_box','school','dormitory')),
    delivery_instructions TEXT,
    is_default_shipping INTEGER NOT NULL DEFAULT 0 CHECK (is_default_shipping IN (0,1)),
    is_default_billing  INTEGER NOT NULL DEFAULT 0 CHECK (is_default_billing IN (0,1)),
    validated_at      TEXT,
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    deleted_at        TEXT,
    -- A-20: PO boxes, schools and dorms can be saved (e.g. billing) but never shipped to.
    is_restricted_destination INTEGER GENERATED ALWAYS AS
        (CASE WHEN address_type IN ('po_box','school','dormitory') THEN 1 ELSE 0 END) VIRTUAL
) STRICT;
CREATE INDEX ix_customer_addresses_customer ON customer_addresses(customer_id);
CREATE UNIQUE INDEX ux_customer_addresses_default_ship ON customer_addresses(customer_id)
    WHERE is_default_shipping = 1 AND deleted_at IS NULL;
CREATE UNIQUE INDEX ux_customer_addresses_default_bill ON customer_addresses(customer_id)
    WHERE is_default_billing = 1 AND deleted_at IS NULL;

-- Tokenized payment methods only. Never PAN, CVV or full expiry history (A-74).
CREATE TABLE customer_payment_methods (
    payment_method_id INTEGER PRIMARY KEY,
    customer_id       INTEGER NOT NULL REFERENCES customers(customer_id),
    method_type       TEXT    NOT NULL CHECK (method_type IN ('card','apple_pay','google_pay')),
    processor         TEXT    NOT NULL,
    processor_token   TEXT    NOT NULL UNIQUE,              -- opaque vault token
    card_brand        TEXT    NOT NULL CHECK (card_brand IN ('visa','mastercard','amex','discover')),
    card_last4        TEXT    NOT NULL CHECK (length(card_last4) = 4 AND card_last4 GLOB '[0-9][0-9][0-9][0-9]'),
    exp_month         INTEGER NOT NULL CHECK (exp_month BETWEEN 1 AND 12),
    exp_year          INTEGER NOT NULL CHECK (exp_year BETWEEN 2000 AND 2100),
    billing_address_id INTEGER REFERENCES customer_addresses(address_id),
    is_default        INTEGER NOT NULL DEFAULT 0 CHECK (is_default IN (0,1)),
    status            TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active','expired','removed')),
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    removed_at        TEXT,
    CHECK ((status = 'removed') = (removed_at IS NOT NULL))
) STRICT;
CREATE INDEX ix_payment_methods_customer ON customer_payment_methods(customer_id);
CREATE INDEX ix_payment_methods_billing_address ON customer_payment_methods(billing_address_id);
CREATE UNIQUE INDEX ux_payment_methods_default ON customer_payment_methods(customer_id)
    WHERE is_default = 1 AND status = 'active';

-- Consent per channel and purpose (A-76: CAN-SPAM, TCPA express consent for SMS).
CREATE TABLE communication_preferences (
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    channel         TEXT    NOT NULL CHECK (channel IN ('email','sms','push')),
    purpose         TEXT    NOT NULL CHECK (purpose IN ('marketing','transactional','loyalty')),
    is_opted_in     INTEGER NOT NULL CHECK (is_opted_in IN (0,1)),
    consent_source  TEXT    NOT NULL CHECK (consent_source IN ('signup_form','checkout','account_settings','sms_keyword','support_request','default')),
    consent_text_version TEXT,
    updated_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    PRIMARY KEY (customer_id, channel, purpose),
    CHECK (NOT (channel = 'sms' AND purpose = 'marketing' AND is_opted_in = 1 AND consent_text_version IS NULL))
) STRICT;

-- Stated taste preferences used for recommendations (_KB/01 six-axis framework).
CREATE TABLE customer_taste_profiles (
    customer_id       INTEGER PRIMARY KEY REFERENCES customers(customer_id),
    preferred_sweetness TEXT CHECK (preferred_sweetness IN ('dry','off_dry','medium_sweet','sweet')),
    preferred_body      TEXT CHECK (preferred_body IN ('light','medium','full')),
    preferred_acidity   TEXT CHECK (preferred_acidity IN ('soft','fresh','crisp')),
    preferred_tannin    TEXT CHECK (preferred_tannin IN ('smooth','moderate','grippy')),
    preferred_oak       TEXT CHECK (preferred_oak IN ('none','subtle','pronounced')),
    preferred_fruit_profile TEXT CHECK (preferred_fruit_profile IN ('fruit_forward','balanced','earthy_savory')),
    typical_budget_min_cents INTEGER CHECK (typical_budget_min_cents >= 0),
    typical_budget_max_cents INTEGER CHECK (typical_budget_max_cents >= 0),
    notes             TEXT,
    updated_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    CHECK (typical_budget_max_cents IS NULL OR typical_budget_min_cents IS NULL
           OR typical_budget_max_cents >= typical_budget_min_cents)
) STRICT;

-- -----------------------------------------------------------------------------
-- 3. PRODUCT CATALOG (wine-aware)
--    product  = the wine/spirit independent of vintage and size
--    variant  = the sellable SKU: product x vintage x bottle size x pack
-- -----------------------------------------------------------------------------

-- Hierarchical geography: country > region > subregion > appellation.
CREATE TABLE regions (
    region_id          INTEGER PRIMARY KEY,
    parent_region_id   INTEGER REFERENCES regions(region_id),
    name               TEXT    NOT NULL,
    region_level       TEXT    NOT NULL CHECK (region_level IN ('country','region','subregion','appellation')),
    country_code       TEXT    NOT NULL CHECK (length(country_code) = 2),
    appellation_system TEXT    CHECK (appellation_system IN ('AOC','AOP','DOCG','DOC','IGT','DO','DOCa','DOP','AVA','GI','WO','VDP','PDO','PGI','none')),
    CHECK ((region_level = 'country') = (parent_region_id IS NULL)),
    UNIQUE (parent_region_id, name)
) STRICT;
CREATE INDEX ix_regions_parent ON regions(parent_region_id);

CREATE TABLE brands (
    brand_id        INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL UNIQUE,
    brand_type      TEXT    NOT NULL CHECK (brand_type IN ('estate_winery','negociant','cooperative','champagne_house','distillery','brewery','non_alcoholic_producer','private_label')),
    home_region_id  INTEGER REFERENCES regions(region_id),
    founded_year    INTEGER CHECK (founded_year BETWEEN 1500 AND 2100),
    description     TEXT,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
) STRICT;
CREATE INDEX ix_brands_region ON brands(home_region_id);

CREATE TABLE grape_varieties (
    grape_id   INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL UNIQUE,
    skin_color TEXT    NOT NULL CHECK (skin_color IN ('red','white','pink')),
    synonyms   TEXT                                     -- e.g. 'Shiraz' for Syrah
) STRICT;

-- Storefront "shop by style" tags (_KB/01 taste-profile-framework section 3).
CREATE TABLE wine_styles (
    style_code   TEXT PRIMARY KEY CHECK (style_code GLOB '[a-z]*'),
    display_name TEXT NOT NULL UNIQUE,
    description  TEXT NOT NULL
) STRICT;

-- Navigation tree for the whole liquor store (wine, spirits, beer, NA, accessories).
CREATE TABLE categories (
    category_id        INTEGER PRIMARY KEY,
    parent_category_id INTEGER REFERENCES categories(category_id),
    slug               TEXT    NOT NULL UNIQUE CHECK (slug GLOB '[a-z0-9]*' AND slug NOT GLOB '*[^a-z0-9-]*'),
    name               TEXT    NOT NULL,
    sort_order         INTEGER NOT NULL DEFAULT 0,
    is_active          INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
) STRICT;
CREATE INDEX ix_categories_parent ON categories(parent_category_id);

CREATE TABLE products (
    product_id     INTEGER PRIMARY KEY,
    product_code   TEXT    NOT NULL UNIQUE,                     -- 'P-0001'
    name           TEXT    NOT NULL,
    brand_id       INTEGER NOT NULL REFERENCES brands(brand_id),
    product_type   TEXT    NOT NULL CHECK (product_type IN ('wine','spirit','beer','cider','sake','non_alcoholic_wine')),
    wine_color     TEXT    CHECK (wine_color IN ('red','white','rose','orange')),
    wine_type      TEXT    CHECK (wine_type IN ('still','sparkling','fortified','dessert')),
    style_code     TEXT    REFERENCES wine_styles(style_code),
    region_id      INTEGER REFERENCES regions(region_id),
    -- Six taste axes (_KB/01). Wine-only; NULL for spirits/accessories.
    sweetness      TEXT    CHECK (sweetness IN ('dry','off_dry','medium_sweet','sweet')),
    body           TEXT    CHECK (body IN ('light','medium','full')),
    acidity        TEXT    CHECK (acidity IN ('soft','fresh','crisp')),
    tannin         TEXT    CHECK (tannin IN ('smooth','moderate','grippy')),
    oak            TEXT    CHECK (oak IN ('none','subtle','pronounced')),
    fruit_profile  TEXT    CHECK (fruit_profile IN ('fruit_forward','balanced','earthy_savory')),
    sparkling_sweetness TEXT CHECK (sparkling_sweetness IN ('brut_nature','extra_brut','brut','extra_dry','dry','demi_sec','doux')),
    closure_type   TEXT    CHECK (closure_type IN ('natural_cork','technical_cork','synthetic_cork','screw_cap','glass_stopper','crown_cap','none')),
    description    TEXT,
    tasting_notes  TEXT,
    food_pairings  TEXT,
    allergen_notes TEXT,                                         -- fining agents, sulfites
    status         TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('draft','active','discontinued','archived')),
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    CHECK (product_type IN ('wine','non_alcoholic_wine') OR (wine_color IS NULL AND wine_type IS NULL AND style_code IS NULL)),
    CHECK (product_type NOT IN ('wine','non_alcoholic_wine') OR wine_type IS NOT NULL),
    CHECK (sparkling_sweetness IS NULL OR wine_type = 'sparkling'),
    CHECK (tannin IS NULL OR wine_color IN ('red','orange','rose'))
) STRICT;
CREATE INDEX ix_products_brand ON products(brand_id);
CREATE INDEX ix_products_region ON products(region_id);
CREATE INDEX ix_products_style ON products(style_code);
CREATE INDEX ix_products_search ON products(product_type, wine_color, sweetness, body);

CREATE TABLE product_categories (
    product_id  INTEGER NOT NULL REFERENCES products(product_id),
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    is_primary  INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0,1)),
    PRIMARY KEY (product_id, category_id)
) STRICT;
CREATE INDEX ix_product_categories_category ON product_categories(category_id);
CREATE UNIQUE INDEX ux_product_primary_category ON product_categories(product_id) WHERE is_primary = 1;

-- Blend composition. percentage NULL = undisclosed share.
CREATE TABLE product_grapes (
    product_id  INTEGER NOT NULL REFERENCES products(product_id),
    grape_id    INTEGER NOT NULL REFERENCES grape_varieties(grape_id),
    percentage  INTEGER CHECK (percentage BETWEEN 1 AND 100),
    PRIMARY KEY (product_id, grape_id)
) STRICT;
CREATE INDEX ix_product_grapes_grape ON product_grapes(grape_id);

-- Sellable SKU. vintage_year NULL = non-vintage (NV).
CREATE TABLE product_variants (
    variant_id        INTEGER PRIMARY KEY,
    product_id        INTEGER NOT NULL REFERENCES products(product_id),
    sku               TEXT    NOT NULL UNIQUE,
    gtin              TEXT    UNIQUE CHECK (gtin IS NULL OR length(gtin) IN (8,12,13,14)),
    vintage_year      INTEGER CHECK (vintage_year BETWEEN 1900 AND 2100),
    size_ml           INTEGER NOT NULL CHECK (size_ml > 0),
    pack_quantity     INTEGER NOT NULL DEFAULT 1 CHECK (pack_quantity BETWEEN 1 AND 24),
    container_type    TEXT    NOT NULL DEFAULT 'bottle' CHECK (container_type IN ('bottle','can','bag_in_box','tetra_pak','keg')),
    abv_percent       REAL    NOT NULL CHECK (abv_percent >= 0 AND abv_percent <= 75),
    is_vintage_specific INTEGER NOT NULL DEFAULT 0 CHECK (is_vintage_specific IN (0,1)),  -- A-23
    is_collectible    INTEGER NOT NULL DEFAULT 0 CHECK (is_collectible IN (0,1)),         -- A-33 library/as-is
    is_final_sale     INTEGER NOT NULL DEFAULT 0 CHECK (is_final_sale IN (0,1)),
    case_discount_eligible INTEGER NOT NULL DEFAULT 1 CHECK (case_discount_eligible IN (0,1)), -- A-50
    weight_grams      INTEGER CHECK (weight_grams > 0),
    status            TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active','coming_soon','discontinued','archived')),
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    -- 750 ml equivalents x 1000 for mixed-case math (A-50): 187 ml = 250, 1.5 L = 2000.
    bottle_equiv_milli INTEGER GENERATED ALWAYS AS ((size_ml * pack_quantity * 1000) / 750) VIRTUAL
) STRICT;
CREATE INDEX ix_variants_product ON product_variants(product_id);
CREATE UNIQUE INDEX ux_variants_identity ON product_variants(product_id, COALESCE(vintage_year, 0), size_ml, pack_quantity, container_type);

-- Organic/biodynamic/sustainable/vegan/kosher tags with evidence (_KB/06 ORG-R1).
-- Per variant because certification can change between vintages.
CREATE TABLE variant_certifications (
    variant_id         INTEGER NOT NULL REFERENCES product_variants(variant_id),
    certification_type TEXT    NOT NULL CHECK (certification_type IN (
        'usda_organic','made_with_organic_grapes','eu_organic','demeter','biodyvin',
        'ccsw','sip','lodi_rules','napa_green','live','swnz','hve','b_corp','roc',
        'vegan','practicing_organic','no_added_sulfites','low_intervention',
        'vin_methode_nature','kosher','kosher_for_passover','mevushal')),
    evidence_level     TEXT    NOT NULL CHECK (evidence_level IN ('certified','declared')),
    certifier          TEXT,
    evidence_ref       TEXT    NOT NULL,                      -- document id, never a free claim
    verified_at        TEXT    NOT NULL,
    expires_at         TEXT,
    status             TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active','expired','revoked')),
    PRIMARY KEY (variant_id, certification_type),
    CHECK (evidence_level = 'declared' OR certifier IS NOT NULL)
) STRICT;

-- Nutrition per serving (_KB/05). Source must be stated; no health claims.
CREATE TABLE variant_nutrition (
    variant_id   INTEGER PRIMARY KEY REFERENCES product_variants(variant_id),
    serving_ml   INTEGER NOT NULL CHECK (serving_ml > 0),
    calories     INTEGER NOT NULL CHECK (calories >= 0),
    carbs_g      REAL    CHECK (carbs_g >= 0),
    sugar_g      REAL    CHECK (sugar_g >= 0),
    residual_sugar_g_per_l REAL CHECK (residual_sugar_g_per_l >= 0),
    source       TEXT    NOT NULL CHECK (source IN ('label','producer_tech_sheet','lab_analysis','ttb_statement')),
    verified_at  TEXT    NOT NULL
) STRICT;

CREATE TABLE product_accolades (
    accolade_id  INTEGER PRIMARY KEY,
    variant_id   INTEGER NOT NULL REFERENCES product_variants(variant_id),
    source       TEXT    NOT NULL,
    score        INTEGER CHECK (score BETWEEN 50 AND 100),
    award        TEXT,
    awarded_year INTEGER NOT NULL CHECK (awarded_year BETWEEN 1900 AND 2100),
    CHECK (score IS NOT NULL OR award IS NOT NULL),
    UNIQUE (variant_id, source, awarded_year)
) STRICT;

-- -----------------------------------------------------------------------------
-- 4. PRICING: per-store listings, effective-dated prices, costs, tax, fees,
--    promotions and price matching (A-03, A-40..A-55)
-- -----------------------------------------------------------------------------

-- What a store sells online and on what terms. A variant can be listed in NJ
-- and not in NY (assortment differs, A-03; NA wine NJ-only, A-06).
CREATE TABLE product_listings (
    store_id          INTEGER NOT NULL REFERENCES stores(store_id),
    variant_id        INTEGER NOT NULL REFERENCES product_variants(variant_id),
    listing_status    TEXT    NOT NULL DEFAULT 'active' CHECK (listing_status IN (
                        'active','pre_arrival','coming_soon','special_order','in_store_only',
                        'temporarily_unavailable','discontinued')),
    is_sellable       INTEGER NOT NULL DEFAULT 1 CHECK (is_sellable IN (0,1)),
    not_sellable_reason TEXT,
    backorder_allowed INTEGER NOT NULL DEFAULT 0 CHECK (backorder_allowed IN (0,1)),
    allocation_limit  INTEGER CHECK (allocation_limit > 0),          -- per customer
    max_per_order     INTEGER NOT NULL DEFAULT 36 CHECK (max_per_order > 0),  -- A-26
    next_arrival_estimate TEXT,
    online_only       INTEGER NOT NULL DEFAULT 0 CHECK (online_only IN (0,1)),
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    PRIMARY KEY (store_id, variant_id),
    CHECK (is_sellable = 1 OR not_sellable_reason IS NOT NULL)
) STRICT;
CREATE INDEX ix_listings_variant ON product_listings(variant_id);

-- Effective-dated price history. A sale price is a separate row with an end
-- date; the current price is the row whose window contains "now"
-- (view v_current_prices). Overlaps are blocked by trigger.
CREATE TABLE product_prices (
    price_id          INTEGER PRIMARY KEY,
    store_id          INTEGER NOT NULL,
    variant_id        INTEGER NOT NULL,
    price_type        TEXT    NOT NULL CHECK (price_type IN ('regular','sale')),
    amount_cents      INTEGER NOT NULL CHECK (amount_cents > 0),
    compare_at_cents  INTEGER CHECK (compare_at_cents > 0),
    compare_at_verified INTEGER NOT NULL DEFAULT 0 CHECK (compare_at_verified IN (0,1)),
    starts_at         TEXT    NOT NULL,
    ends_at           TEXT,
    change_reason     TEXT    NOT NULL,
    created_by_staff_id INTEGER REFERENCES staff_users(staff_id),
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (store_id, variant_id) REFERENCES product_listings(store_id, variant_id),
    CHECK (ends_at IS NULL OR ends_at > starts_at),
    CHECK (price_type = 'regular' OR ends_at IS NOT NULL),              -- sales always end
    CHECK (compare_at_cents IS NULL OR compare_at_cents > amount_cents)
) STRICT;
CREATE INDEX ix_prices_lookup ON product_prices(store_id, variant_id, price_type, starts_at);
CREATE INDEX ix_prices_variant ON product_prices(variant_id);
CREATE INDEX ix_prices_staff ON product_prices(created_by_staff_id);

-- Landed unit cost. Internal only (never exposed to the agent); used to enforce
-- the NJ below-cost floor (A-54).
CREATE TABLE product_costs (
    cost_id         INTEGER PRIMARY KEY,
    store_id        INTEGER NOT NULL,
    variant_id      INTEGER NOT NULL,
    unit_cost_cents INTEGER NOT NULL CHECK (unit_cost_cents > 0),
    effective_from  TEXT    NOT NULL,
    effective_to    TEXT,
    source          TEXT    NOT NULL CHECK (source IN ('distributor_invoice','price_posting','manual')),
    FOREIGN KEY (store_id, variant_id) REFERENCES product_listings(store_id, variant_id),
    CHECK (effective_to IS NULL OR effective_to > effective_from),
    UNIQUE (store_id, variant_id, effective_from)
) STRICT;
CREATE INDEX ix_costs_variant ON product_costs(variant_id);

-- Sales-tax rates (illustrative values; the tax engine is authoritative).
-- postal_code NULL = statewide/county default for the jurisdiction.
CREATE TABLE tax_rates (
    tax_rate_id       INTEGER PRIMARY KEY,
    state_code        TEXT    NOT NULL CHECK (state_code IN ('NJ','NY')),
    jurisdiction_name TEXT    NOT NULL,
    postal_code       TEXT    CHECK (postal_code IS NULL OR length(postal_code) = 5),
    rate_ppm          INTEGER NOT NULL CHECK (rate_ppm BETWEEN 0 AND 200000),
    applies_to_shipping INTEGER NOT NULL DEFAULT 1 CHECK (applies_to_shipping IN (0,1)),
    effective_from    TEXT    NOT NULL,
    effective_to      TEXT,
    CHECK (effective_to IS NULL OR effective_to > effective_from)
) STRICT;
CREATE UNIQUE INDEX ux_tax_rates ON tax_rates(state_code, COALESCE(postal_code, '*'), jurisdiction_name, effective_from);

-- Delivery and shipping fee schedule (A-10..A-16).
CREATE TABLE fulfillment_rates (
    rate_id           INTEGER PRIMARY KEY,
    store_id          INTEGER NOT NULL REFERENCES stores(store_id),
    fulfillment_type  TEXT    NOT NULL CHECK (fulfillment_type IN ('local_delivery','pickup','shipping')),
    zone              INTEGER CHECK (zone BETWEEN 1 AND 9),
    min_distance_miles REAL,
    max_distance_miles REAL,
    min_bottles       INTEGER CHECK (min_bottles >= 1),
    max_bottles       INTEGER,
    fee_cents         INTEGER NOT NULL CHECK (fee_cents >= 0),
    extra_fee_per_6_bottles_cents INTEGER NOT NULL DEFAULT 0 CHECK (extra_fee_per_6_bottles_cents >= 0),
    order_minimum_cents INTEGER NOT NULL DEFAULT 0 CHECK (order_minimum_cents >= 0),
    free_threshold_cents INTEGER CHECK (free_threshold_cents > 0),
    effective_from    TEXT    NOT NULL,
    effective_to      TEXT,
    CHECK (fulfillment_type <> 'local_delivery' OR zone IS NOT NULL),
    CHECK (max_bottles IS NULL OR max_bottles >= min_bottles)
) STRICT;
CREATE INDEX ix_fulfillment_rates_store ON fulfillment_rates(store_id, fulfillment_type);

-- Promotions: automatic (code NULL) or code-based. One code per order (A-51).
CREATE TABLE promotions (
    promotion_id      INTEGER PRIMARY KEY,
    code              TEXT,
    name              TEXT    NOT NULL,
    promo_type        TEXT    NOT NULL CHECK (promo_type IN ('percent_off','amount_off','free_delivery','mixed_case','first_order','loyalty_reward')),
    percent_off_bps   INTEGER CHECK (percent_off_bps BETWEEN 1 AND 10000),
    amount_off_cents  INTEGER CHECK (amount_off_cents > 0),
    min_subtotal_cents INTEGER NOT NULL DEFAULT 0 CHECK (min_subtotal_cents >= 0),
    store_id          INTEGER REFERENCES stores(store_id),              -- NULL = all stores
    channel           TEXT    NOT NULL DEFAULT 'all' CHECK (channel IN ('all','online_only','in_store_only')),
    is_stackable      INTEGER NOT NULL DEFAULT 0 CHECK (is_stackable IN (0,1)),
    max_redemptions   INTEGER CHECK (max_redemptions > 0),
    max_per_customer  INTEGER CHECK (max_per_customer > 0),
    starts_at         TEXT    NOT NULL,
    ends_at           TEXT,
    status            TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('draft','active','paused','expired','cancelled')),
    terms             TEXT    NOT NULL,
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    CHECK (ends_at IS NULL OR ends_at > starts_at),
    CHECK (promo_type <> 'percent_off' OR percent_off_bps IS NOT NULL),
    CHECK (promo_type NOT IN ('amount_off','first_order','loyalty_reward') OR amount_off_cents IS NOT NULL),
    CHECK (NOT (percent_off_bps IS NOT NULL AND amount_off_cents IS NOT NULL))
) STRICT;
CREATE UNIQUE INDEX ux_promotions_code ON promotions(upper(code)) WHERE code IS NOT NULL;
CREATE INDEX ix_promotions_store ON promotions(store_id);
CREATE INDEX ix_promotions_active ON promotions(status, starts_at, ends_at);

-- Volume tiers, e.g. mixed case 6+ = 10%, 12+ = 15% (A-50).
CREATE TABLE promotion_tiers (
    promotion_id      INTEGER NOT NULL REFERENCES promotions(promotion_id),
    min_bottle_equivalents INTEGER NOT NULL CHECK (min_bottle_equivalents > 0),
    percent_off_bps   INTEGER NOT NULL CHECK (percent_off_bps BETWEEN 1 AND 10000),
    PRIMARY KEY (promotion_id, min_bottle_equivalents)
) STRICT;

-- Inclusions/exclusions. Exactly one target column is set (FK-safe polymorphism).
CREATE TABLE promotion_targets (
    promotion_target_id INTEGER PRIMARY KEY,
    promotion_id      INTEGER NOT NULL REFERENCES promotions(promotion_id),
    is_exclusion      INTEGER NOT NULL DEFAULT 0 CHECK (is_exclusion IN (0,1)),
    category_id       INTEGER REFERENCES categories(category_id),
    brand_id          INTEGER REFERENCES brands(brand_id),
    product_id        INTEGER REFERENCES products(product_id),
    variant_id        INTEGER REFERENCES product_variants(variant_id),
    CHECK ((category_id IS NOT NULL) + (brand_id IS NOT NULL) + (product_id IS NOT NULL) + (variant_id IS NOT NULL) = 1)
) STRICT;
CREATE INDEX ix_promotion_targets_promotion ON promotion_targets(promotion_id);
CREATE INDEX ix_promotion_targets_category ON promotion_targets(category_id);
CREATE INDEX ix_promotion_targets_brand ON promotion_targets(brand_id);
CREATE INDEX ix_promotion_targets_product ON promotion_targets(product_id);
CREATE INDEX ix_promotion_targets_variant ON promotion_targets(variant_id);

-- -----------------------------------------------------------------------------
-- 5. INVENTORY
--    inventory_levels      = current balance per warehouse x variant (fast reads)
--    inventory_movements   = append-only ledger that explains every change
--    inventory_reservations (section 7) = stock promised to open order lines
-- -----------------------------------------------------------------------------

CREATE TABLE inventory_levels (
    warehouse_id   INTEGER NOT NULL REFERENCES warehouses(warehouse_id),
    variant_id     INTEGER NOT NULL REFERENCES product_variants(variant_id),
    qty_on_hand    INTEGER NOT NULL DEFAULT 0 CHECK (qty_on_hand >= 0),
    qty_reserved   INTEGER NOT NULL DEFAULT 0 CHECK (qty_reserved >= 0),
    safety_stock   INTEGER NOT NULL DEFAULT 0 CHECK (safety_stock >= 0),
    reorder_point  INTEGER NOT NULL DEFAULT 0 CHECK (reorder_point >= 0),
    bin_location   TEXT,
    last_counted_at TEXT,
    updated_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    PRIMARY KEY (warehouse_id, variant_id),
    CHECK (qty_reserved <= qty_on_hand)
) STRICT;
CREATE INDEX ix_inventory_variant ON inventory_levels(variant_id);

CREATE TABLE inventory_movements (
    movement_id     INTEGER PRIMARY KEY,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouses(warehouse_id),
    variant_id      INTEGER NOT NULL REFERENCES product_variants(variant_id),
    movement_type   TEXT    NOT NULL CHECK (movement_type IN (
                      'receipt','sale_shipment','return_restock','damage_writeoff',
                      'cycle_count_adjustment','transfer_in','transfer_out','vendor_return','initial_load')),
    quantity_delta  INTEGER NOT NULL CHECK (quantity_delta <> 0),
    reference_type  TEXT    CHECK (reference_type IN ('shipment','return','purchase_receipt','count','transfer')),
    reference_id    INTEGER,
    note            TEXT,
    created_by_staff_id INTEGER REFERENCES staff_users(staff_id),
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    CHECK ((reference_type IS NULL) = (reference_id IS NULL)),
    CHECK (movement_type NOT IN ('receipt','return_restock','transfer_in','initial_load') OR quantity_delta > 0),
    CHECK (movement_type NOT IN ('sale_shipment','damage_writeoff','transfer_out','vendor_return') OR quantity_delta < 0)
) STRICT;
CREATE INDEX ix_movements_item ON inventory_movements(warehouse_id, variant_id, created_at);
CREATE INDEX ix_movements_variant ON inventory_movements(variant_id);
CREATE INDEX ix_movements_reference ON inventory_movements(reference_type, reference_id);
CREATE INDEX ix_movements_staff ON inventory_movements(created_by_staff_id);

-- Back-in-stock alerts and allocation waitlists (subscribe_back_in_stock).
CREATE TABLE back_in_stock_subscriptions (
    subscription_id INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    store_id        INTEGER NOT NULL,
    variant_id      INTEGER NOT NULL,
    channel         TEXT    NOT NULL CHECK (channel IN ('email','sms','push')),
    is_waitlist     INTEGER NOT NULL DEFAULT 0 CHECK (is_waitlist IN (0,1)),
    status          TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active','notified','cancelled','expired')),
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    notified_at     TEXT,
    FOREIGN KEY (store_id, variant_id) REFERENCES product_listings(store_id, variant_id)
) STRICT;
CREATE INDEX ix_bis_customer ON back_in_stock_subscriptions(customer_id);
CREATE INDEX ix_bis_listing ON back_in_stock_subscriptions(store_id, variant_id, status);
CREATE UNIQUE INDEX ux_bis_active ON back_in_stock_subscriptions(customer_id, store_id, variant_id) WHERE status = 'active';

-- -----------------------------------------------------------------------------
-- 6. ORDERS
--    orders.status          = fulfillment lifecycle (_KB/11 order-status-lifecycle)
--    orders.payment_status  = financial summary (refunded / partially_refunded live
--                             here, not in the lifecycle, as Shopify/Medusa do)
--    order_items            = immutable snapshot of what was bought and the price
-- -----------------------------------------------------------------------------

CREATE TABLE orders (
    order_id          INTEGER PRIMARY KEY,
    order_number      TEXT    NOT NULL UNIQUE,                  -- 'WA-100482' (public)
    customer_id       INTEGER NOT NULL REFERENCES customers(customer_id),
    store_id          INTEGER NOT NULL REFERENCES stores(store_id),   -- seller of record
    channel           TEXT    NOT NULL DEFAULT 'web' CHECK (channel IN ('web','mobile_app','chat_agent','phone','in_store_kiosk')),
    status            TEXT    NOT NULL DEFAULT 'placed' CHECK (status IN (
                        'placed','age_verification_pending','confirmed','picking','substitution_pending',
                        'ready_for_pickup','out_for_delivery','label_created','in_transit','partially_fulfilled',
                        'delivery_exception','delivered','picked_up','delivery_failed','redelivery_scheduled',
                        'returned_to_store','returned_to_sender','on_hold','cancelled','completed')),
    hold_reason       TEXT    CHECK (hold_reason IN ('weather','fraud_review','bulk_review','address_verification','age_verification','payment_issue')),
    payment_status    TEXT    NOT NULL DEFAULT 'pending' CHECK (payment_status IN (
                        'pending','authorized','partially_paid','paid','partially_refunded','refunded','voided','failed')),
    fulfillment_type  TEXT    NOT NULL CHECK (fulfillment_type IN ('local_delivery','pickup','shipping')),
    pickup_warehouse_id INTEGER,
    alternate_pickup_name TEXT,                                     -- A-29b
    delivery_zone     INTEGER CHECK (delivery_zone BETWEEN 1 AND 9),
    delivery_window_start TEXT,
    delivery_window_end   TEXT,
    substitution_preference TEXT NOT NULL DEFAULT 'contact_me'
                      CHECK (substitution_preference IN ('contact_me','substitute_similar','do_not_substitute')), -- A-24
    is_gift           INTEGER NOT NULL DEFAULT 0 CHECK (is_gift IN (0,1)),
    gift_message      TEXT,
    customer_note     TEXT,
    currency_code     TEXT    NOT NULL DEFAULT 'USD' CHECK (currency_code = 'USD'),
    -- Totals snapshot (authoritative at placement; later changes go through refunds)
    items_subtotal_cents  INTEGER NOT NULL DEFAULT 0 CHECK (items_subtotal_cents >= 0),
    discount_total_cents  INTEGER NOT NULL DEFAULT 0 CHECK (discount_total_cents >= 0),
    shipping_fee_cents    INTEGER NOT NULL DEFAULT 0 CHECK (shipping_fee_cents >= 0),
    tip_cents             INTEGER NOT NULL DEFAULT 0 CHECK (tip_cents >= 0),
    tax_total_cents       INTEGER NOT NULL DEFAULT 0 CHECK (tax_total_cents >= 0),
    grand_total_cents     INTEGER NOT NULL DEFAULT 0 CHECK (grand_total_cents >= 0),
    tax_rate_ppm          INTEGER NOT NULL CHECK (tax_rate_ppm BETWEEN 0 AND 200000),
    tax_jurisdiction      TEXT    NOT NULL,
    replacement_for_order_id INTEGER REFERENCES orders(order_id),   -- replacement orders
    placed_at         TEXT    NOT NULL,
    cancelled_at      TEXT,
    cancel_reason     TEXT    CHECK (cancel_reason IN ('customer_request','out_of_stock','pricing_error','fraud','age_verification_failed','pickup_not_collected','failed_delivery','store_decision')),
    completed_at      TEXT,
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    FOREIGN KEY (pickup_warehouse_id, store_id) REFERENCES warehouses(warehouse_id, store_id),
    UNIQUE (order_id, store_id),
    UNIQUE (order_id, customer_id),
    CHECK (grand_total_cents = items_subtotal_cents - discount_total_cents + shipping_fee_cents + tip_cents + tax_total_cents),
    CHECK (discount_total_cents <= items_subtotal_cents),
    CHECK ((fulfillment_type = 'pickup') = (pickup_warehouse_id IS NOT NULL)),
    CHECK (fulfillment_type = 'local_delivery' OR tip_cents = 0),          -- A-27
    CHECK (fulfillment_type <> 'local_delivery' OR delivery_zone IS NOT NULL),
    CHECK (alternate_pickup_name IS NULL OR fulfillment_type = 'pickup'),
    CHECK (delivery_window_end IS NULL OR delivery_window_end > delivery_window_start),
    CHECK ((status = 'on_hold') = (hold_reason IS NOT NULL)),
    CHECK ((status = 'cancelled') = (cancelled_at IS NOT NULL AND cancel_reason IS NOT NULL)),
    CHECK (status <> 'completed' OR completed_at IS NOT NULL),
    CHECK (gift_message IS NULL OR is_gift = 1)
) STRICT;
CREATE INDEX ix_orders_customer ON orders(customer_id, placed_at DESC);
CREATE INDEX ix_orders_store_status ON orders(store_id, status);
CREATE INDEX ix_orders_status ON orders(status, placed_at);
CREATE INDEX ix_orders_pickup_wh ON orders(pickup_warehouse_id, store_id);
CREATE INDEX ix_orders_replacement ON orders(replacement_for_order_id);

-- Address snapshot at order time (the saved address can change later).
CREATE TABLE order_addresses (
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    address_role    TEXT    NOT NULL CHECK (address_role IN ('shipping','billing')),
    source_address_id INTEGER REFERENCES customer_addresses(address_id),
    recipient_name  TEXT    NOT NULL,
    line1           TEXT    NOT NULL,
    line2           TEXT,
    city            TEXT    NOT NULL,
    state_code      TEXT    NOT NULL CHECK (length(state_code) = 2),
    postal_code     TEXT    NOT NULL CHECK (length(postal_code) = 5),
    country_code    TEXT    NOT NULL DEFAULT 'US' CHECK (country_code = 'US'),
    phone_e164      TEXT,
    address_type    TEXT    NOT NULL DEFAULT 'residential' CHECK (address_type IN ('residential','business','hotel','po_box','school','dormitory')),
    delivery_instructions TEXT,
    PRIMARY KEY (order_id, address_role),
    CHECK (address_role <> 'shipping' OR state_code IN ('NJ','NY')),                          -- A-02
    CHECK (address_role <> 'shipping' OR address_type NOT IN ('po_box','school','dormitory'))  -- A-20
) STRICT;
CREATE INDEX ix_order_addresses_source ON order_addresses(source_address_id);

CREATE TABLE order_items (
    order_item_id     INTEGER PRIMARY KEY,
    order_id          INTEGER NOT NULL REFERENCES orders(order_id),
    line_number       INTEGER NOT NULL CHECK (line_number > 0),
    variant_id        INTEGER NOT NULL REFERENCES product_variants(variant_id),
    price_id          INTEGER REFERENCES product_prices(price_id),     -- which price row was used
    -- Snapshot (immutable; trigger trg_order_items_snapshot_immutable)
    sku               TEXT    NOT NULL,
    product_name      TEXT    NOT NULL,
    brand_name        TEXT    NOT NULL,
    vintage_year      INTEGER,
    size_ml           INTEGER NOT NULL CHECK (size_ml > 0),
    pack_quantity     INTEGER NOT NULL DEFAULT 1 CHECK (pack_quantity > 0),
    is_final_sale     INTEGER NOT NULL DEFAULT 0 CHECK (is_final_sale IN (0,1)),
    is_vintage_specific INTEGER NOT NULL DEFAULT 0 CHECK (is_vintage_specific IN (0,1)),
    unit_regular_price_cents INTEGER NOT NULL CHECK (unit_regular_price_cents > 0),
    unit_price_cents  INTEGER NOT NULL CHECK (unit_price_cents > 0),
    quantity          INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 999),
    line_subtotal_cents INTEGER NOT NULL,
    discount_cents    INTEGER NOT NULL DEFAULT 0 CHECK (discount_cents >= 0),
    tax_cents         INTEGER NOT NULL DEFAULT 0 CHECK (tax_cents >= 0),
    line_total_cents  INTEGER NOT NULL,
    -- Mutable operational field
    quantity_cancelled INTEGER NOT NULL DEFAULT 0 CHECK (quantity_cancelled >= 0),
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (order_id, line_number),
    UNIQUE (order_id, order_item_id),                     -- target for composite FKs
    CHECK (unit_price_cents <= unit_regular_price_cents),
    CHECK (line_subtotal_cents = unit_price_cents * quantity),
    CHECK (discount_cents <= line_subtotal_cents),
    CHECK (line_total_cents = line_subtotal_cents - discount_cents + tax_cents),
    CHECK (quantity_cancelled <= quantity)
) STRICT;
CREATE INDEX ix_order_items_variant ON order_items(variant_id);
CREATE INDEX ix_order_items_price ON order_items(price_id);

-- Vintage / similar-wine substitution proposals (A-22..A-24, respond_to_substitution).
CREATE TABLE order_item_substitutions (
    substitution_id   INTEGER PRIMARY KEY,
    order_id          INTEGER NOT NULL,
    order_item_id     INTEGER NOT NULL,
    proposed_variant_id INTEGER NOT NULL REFERENCES product_variants(variant_id),
    proposed_unit_price_cents INTEGER NOT NULL CHECK (proposed_unit_price_cents > 0),
    substitution_type TEXT    NOT NULL CHECK (substitution_type IN ('adjacent_vintage','similar_wine')),
    requires_consent  INTEGER NOT NULL CHECK (requires_consent IN (0,1)),
    status            TEXT    NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed','approved','declined','expired','auto_applied')),
    decided_by_type   TEXT    CHECK (decided_by_type IN ('customer','ai_agent','staff','system')),
    proposed_at       TEXT    NOT NULL,
    expires_at        TEXT    NOT NULL,
    decided_at        TEXT,
    FOREIGN KEY (order_id, order_item_id) REFERENCES order_items(order_id, order_item_id),
    CHECK (expires_at > proposed_at),
    CHECK ((status = 'proposed') = (decided_at IS NULL)),
    CHECK (status <> 'auto_applied' OR requires_consent = 0)
) STRICT;
CREATE INDEX ix_substitutions_item ON order_item_substitutions(order_id, order_item_id);
CREATE INDEX ix_substitutions_variant ON order_item_substitutions(proposed_variant_id);

-- Discounts applied to the order and how each is spread over lines, so a
-- partial refund returns the line "net of allocated discounts" (_KB/12 refunds).
CREATE TABLE order_discounts (
    order_discount_id INTEGER PRIMARY KEY,
    order_id          INTEGER NOT NULL REFERENCES orders(order_id),
    promotion_id      INTEGER REFERENCES promotions(promotion_id),
    discount_type     TEXT    NOT NULL CHECK (discount_type IN ('promo_code','mixed_case','first_order','loyalty_reward','price_match','price_correction','free_delivery')),
    code_used         TEXT,
    description       TEXT    NOT NULL,
    amount_cents      INTEGER NOT NULL CHECK (amount_cents >= 0),
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE (order_discount_id, order_id)
) STRICT;
CREATE INDEX ix_order_discounts_order ON order_discounts(order_id);
CREATE INDEX ix_order_discounts_promotion ON order_discounts(promotion_id);
-- At most one promo code per order (A-51).
CREATE UNIQUE INDEX ux_order_one_promo_code ON order_discounts(order_id) WHERE discount_type = 'promo_code';

CREATE TABLE order_discount_allocations (
    order_discount_id INTEGER NOT NULL,
    order_id          INTEGER NOT NULL,
    order_item_id     INTEGER NOT NULL,
    amount_cents      INTEGER NOT NULL CHECK (amount_cents > 0),
    PRIMARY KEY (order_discount_id, order_item_id),
    FOREIGN KEY (order_discount_id, order_id) REFERENCES order_discounts(order_discount_id, order_id),
    FOREIGN KEY (order_id, order_item_id) REFERENCES order_items(order_id, order_item_id)
) STRICT;
CREATE INDEX ix_discount_alloc_item ON order_discount_allocations(order_id, order_item_id);
CREATE INDEX ix_discount_alloc_discount ON order_discount_allocations(order_discount_id, order_id);

-- Append-only status timeline (get_order "timeline").
CREATE TABLE order_status_history (
    history_id     INTEGER PRIMARY KEY,
    order_id       INTEGER NOT NULL REFERENCES orders(order_id),
    from_status    TEXT,
    to_status      TEXT    NOT NULL,
    actor_type     TEXT    NOT NULL CHECK (actor_type IN ('customer','ai_agent','staff','system','carrier')),
    actor_ref      TEXT,
    note           TEXT,
    changed_at     TEXT    NOT NULL
) STRICT;
CREATE INDEX ix_order_status_history_order ON order_status_history(order_id, changed_at);

-- Stock promised to an order line at a specific warehouse.
CREATE TABLE inventory_reservations (
    reservation_id  INTEGER PRIMARY KEY,
    order_id        INTEGER NOT NULL,
    order_item_id   INTEGER NOT NULL,
    warehouse_id    INTEGER NOT NULL REFERENCES warehouses(warehouse_id),
    variant_id      INTEGER NOT NULL REFERENCES product_variants(variant_id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    status          TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active','consumed','released','expired')),
    expires_at      TEXT,
    created_at      TEXT    NOT NULL,
    closed_at       TEXT,
    FOREIGN KEY (order_id, order_item_id) REFERENCES order_items(order_id, order_item_id),
    CHECK ((status = 'active') = (closed_at IS NULL))
) STRICT;
CREATE INDEX ix_reservations_item ON inventory_reservations(order_id, order_item_id);
CREATE INDEX ix_reservations_stock ON inventory_reservations(warehouse_id, variant_id, status);
CREATE INDEX ix_reservations_variant ON inventory_reservations(variant_id);

-- Carts (get_cart / add_to_cart). Prices are not stored: carts reprice live.
CREATE TABLE carts (
    cart_id          INTEGER PRIMARY KEY,
    cart_token       TEXT    NOT NULL UNIQUE,
    customer_id      INTEGER NOT NULL REFERENCES customers(customer_id),
    store_id         INTEGER NOT NULL REFERENCES stores(store_id),
    status           TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active','converted','abandoned','merged')),
    fulfillment_type TEXT    CHECK (fulfillment_type IN ('local_delivery','pickup','shipping')),
    promo_code       TEXT,
    converted_order_id INTEGER UNIQUE REFERENCES orders(order_id),
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    expires_at       TEXT,
    CHECK ((status = 'converted') = (converted_order_id IS NOT NULL))
) STRICT;
CREATE INDEX ix_carts_customer ON carts(customer_id, status);
CREATE INDEX ix_carts_store ON carts(store_id);
CREATE UNIQUE INDEX ux_carts_one_active ON carts(customer_id) WHERE status = 'active';

CREATE TABLE cart_items (
    cart_id     INTEGER NOT NULL REFERENCES carts(cart_id) ON DELETE CASCADE,
    variant_id  INTEGER NOT NULL REFERENCES product_variants(variant_id),
    quantity    INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 999),
    added_at    TEXT    NOT NULL,
    PRIMARY KEY (cart_id, variant_id)
) STRICT;
CREATE INDEX ix_cart_items_variant ON cart_items(variant_id);

-- Human-reviewed price matching (A-43).
CREATE TABLE price_match_requests (
    price_match_id     INTEGER PRIMARY KEY,
    request_number     TEXT    NOT NULL UNIQUE,
    customer_id        INTEGER NOT NULL REFERENCES customers(customer_id),
    store_id           INTEGER NOT NULL,
    variant_id         INTEGER NOT NULL,
    order_id           INTEGER REFERENCES orders(order_id),
    competitor_name    TEXT    NOT NULL,
    competitor_state   TEXT    NOT NULL CHECK (competitor_state IN ('NJ','NY')),
    competitor_url_or_proof TEXT NOT NULL,
    competitor_price_cents INTEGER NOT NULL CHECK (competitor_price_cents > 0),
    our_price_cents    INTEGER NOT NULL CHECK (our_price_cents > 0),
    quantity           INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 12),
    status             TEXT    NOT NULL DEFAULT 'pending_review' CHECK (status IN ('pending_review','approved','rejected','expired','withdrawn')),
    decision_reason    TEXT,
    reviewed_by_staff_id INTEGER REFERENCES staff_users(staff_id),
    created_at         TEXT    NOT NULL,
    decided_at         TEXT,
    FOREIGN KEY (store_id, variant_id) REFERENCES product_listings(store_id, variant_id),
    CHECK (status IN ('pending_review','withdrawn') OR (decided_at IS NOT NULL AND reviewed_by_staff_id IS NOT NULL))
) STRICT;
CREATE INDEX ix_price_match_customer ON price_match_requests(customer_id);
CREATE INDEX ix_price_match_listing ON price_match_requests(store_id, variant_id);
CREATE INDEX ix_price_match_order ON price_match_requests(order_id);
CREATE INDEX ix_price_match_staff ON price_match_requests(reviewed_by_staff_id);

-- -----------------------------------------------------------------------------
-- 7. PAYMENTS
--    payments             = one row per tender on an order (split payment = 2+ rows),
--                           like a PaymentIntent / Medusa Payment
--    payment_transactions = append-only processor operations (section 9, after
--                           refunds): authorization, capture(s), void, refund(s),
--                           chargeback. Card authorized at order, captured at
--                           fulfillment (A-29), so partial shipments = partial captures.
-- -----------------------------------------------------------------------------

-- Gift cards never expire and have no fees (A-56). Only a hash of the code is stored.
CREATE TABLE gift_cards (
    gift_card_id        INTEGER PRIMARY KEY,
    code_hash           TEXT    NOT NULL UNIQUE,
    code_last4          TEXT    NOT NULL CHECK (length(code_last4) = 4),
    card_format         TEXT    NOT NULL CHECK (card_format IN ('digital','physical')),
    initial_value_cents INTEGER NOT NULL CHECK (initial_value_cents BETWEEN 500 AND 50000),
    status              TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('pending_activation','active','frozen','depleted','void')),
    purchaser_customer_id INTEGER REFERENCES customers(customer_id),
    purchase_order_id   INTEGER REFERENCES orders(order_id),
    recipient_email     TEXT,
    issued_at           TEXT    NOT NULL
) STRICT;
CREATE INDEX ix_gift_cards_purchaser ON gift_cards(purchaser_customer_id);
CREATE INDEX ix_gift_cards_order ON gift_cards(purchase_order_id);

-- Lets payments prove the saved card belongs to the paying customer.
CREATE UNIQUE INDEX ux_payment_methods_owner ON customer_payment_methods(payment_method_id, customer_id);

CREATE TABLE payments (
    payment_id          INTEGER PRIMARY KEY,
    order_id            INTEGER NOT NULL,
    customer_id         INTEGER NOT NULL,
    tender_type         TEXT    NOT NULL CHECK (tender_type IN ('card','apple_pay','google_pay','gift_card','store_credit')),
    payment_method_id   INTEGER,
    gift_card_id        INTEGER REFERENCES gift_cards(gift_card_id),
    processor           TEXT    NOT NULL CHECK (processor IN ('card_gateway','internal_ledger')),
    processor_payment_ref TEXT  UNIQUE,
    amount_cents        INTEGER NOT NULL CHECK (amount_cents > 0),     -- amount assigned to this tender
    status              TEXT    NOT NULL DEFAULT 'pending' CHECK (status IN (
                          'pending','requires_action','authorized','partially_captured','captured',
                          'partially_refunded','refunded','voided','failed')),
    refund_priority     INTEGER NOT NULL DEFAULT 1 CHECK (refund_priority > 0),  -- card refunded last (_KB/12)
    created_at          TEXT    NOT NULL,
    updated_at          TEXT    NOT NULL,
    FOREIGN KEY (order_id, customer_id) REFERENCES orders(order_id, customer_id),
    FOREIGN KEY (payment_method_id, customer_id) REFERENCES customer_payment_methods(payment_method_id, customer_id),
    UNIQUE (payment_id, order_id),
    CHECK ((tender_type IN ('card','apple_pay','google_pay')) = (payment_method_id IS NOT NULL)),
    CHECK ((tender_type = 'gift_card') = (gift_card_id IS NOT NULL)),
    CHECK ((tender_type IN ('gift_card','store_credit')) = (processor = 'internal_ledger'))
) STRICT;
CREATE INDEX ix_payments_order ON payments(order_id, customer_id);
CREATE INDEX ix_payments_method ON payments(payment_method_id, customer_id);
CREATE INDEX ix_payments_gift_card ON payments(gift_card_id);
CREATE INDEX ix_payments_status ON payments(status);

-- -----------------------------------------------------------------------------
-- 8. FULFILLMENT: shipments (carrier, local delivery and pickup handoffs),
--    shipment lines (partial shipments) and tracking events
-- -----------------------------------------------------------------------------

CREATE TABLE shipments (
    shipment_id        INTEGER PRIMARY KEY,
    shipment_number    TEXT    NOT NULL UNIQUE,                  -- 'SH-200001'
    order_id           INTEGER NOT NULL,
    store_id           INTEGER NOT NULL,
    warehouse_id       INTEGER NOT NULL,
    method             TEXT    NOT NULL CHECK (method IN ('local_delivery','carrier','pickup')),
    carrier            TEXT    CHECK (carrier IN ('UPS','FedEx','store_driver','courier_partner')),
    service_level      TEXT,
    tracking_number    TEXT    UNIQUE,
    tracking_url       TEXT,
    status             TEXT    NOT NULL DEFAULT 'pending' CHECK (status IN (
                         'pending','picking','packed','label_created','ready_for_pickup','out_for_delivery',
                         'in_transit','delivery_exception','delivered','picked_up','delivery_failed',
                         'returned_to_store','returned_to_sender','cancelled')),
    requires_adult_signature INTEGER NOT NULL DEFAULT 1 CHECK (requires_adult_signature IN (0,1)),
    weather_hold       INTEGER NOT NULL DEFAULT 0 CHECK (weather_hold IN (0,1)),        -- A-19
    attempt_count      INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 3), -- A-17/A-18
    delivery_window_start TEXT,
    delivery_window_end   TEXT,
    estimated_delivery_at TEXT,
    shipping_cost_cents INTEGER CHECK (shipping_cost_cents >= 0),  -- our cost, not the customer fee
    shipped_at         TEXT,
    delivered_at       TEXT,
    -- Handoff age check (A-05 point 3). Never stores the ID image or number.
    handed_to_name     TEXT,
    id_check_method    TEXT    CHECK (id_check_method IN ('id_scan','visual_id_check','carrier_adult_signature')),
    id_verified        INTEGER NOT NULL DEFAULT 0 CHECK (id_verified IN (0,1)),
    created_at         TEXT    NOT NULL,
    updated_at         TEXT    NOT NULL,
    FOREIGN KEY (order_id, store_id) REFERENCES orders(order_id, store_id),
    FOREIGN KEY (warehouse_id, store_id) REFERENCES warehouses(warehouse_id, store_id),
    UNIQUE (shipment_id, order_id),
    CHECK ((method = 'carrier') = (carrier IN ('UPS','FedEx'))),
    CHECK (method <> 'local_delivery' OR carrier IN ('store_driver','courier_partner')),
    CHECK (method <> 'pickup' OR carrier IS NULL),
    CHECK (tracking_number IS NULL OR method = 'carrier'),
    -- No handoff without a 21+ ID check (compliance guardrail).
    CHECK (status NOT IN ('delivered','picked_up')
           OR (delivered_at IS NOT NULL AND id_verified = 1 AND handed_to_name IS NOT NULL AND id_check_method IS NOT NULL)),
    CHECK (delivery_window_end IS NULL OR delivery_window_end > delivery_window_start)
) STRICT;
CREATE INDEX ix_shipments_order ON shipments(order_id, store_id);
CREATE INDEX ix_shipments_warehouse ON shipments(warehouse_id, store_id);
CREATE INDEX ix_shipments_status ON shipments(status);

CREATE TABLE shipment_items (
    shipment_id    INTEGER NOT NULL,
    order_id       INTEGER NOT NULL,
    order_item_id  INTEGER NOT NULL,
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (shipment_id, order_item_id),
    FOREIGN KEY (shipment_id, order_id) REFERENCES shipments(shipment_id, order_id),
    FOREIGN KEY (order_id, order_item_id) REFERENCES order_items(order_id, order_item_id)
) STRICT;
CREATE INDEX ix_shipment_items_item ON shipment_items(order_id, order_item_id);
CREATE INDEX ix_shipment_items_shipment ON shipment_items(shipment_id, order_id);

CREATE TABLE shipment_tracking_events (
    tracking_event_id INTEGER PRIMARY KEY,
    shipment_id       INTEGER NOT NULL REFERENCES shipments(shipment_id),
    event_code        TEXT    NOT NULL CHECK (event_code IN (
                        'label_created','carrier_pickup','in_transit','arrived_at_facility','weather_hold',
                        'out_for_delivery','driver_assigned','delivery_attempted','delivery_exception',
                        'address_issue','delivered','ready_for_pickup','picked_up',
                        'returned_to_store','returned_to_sender')),
    description       TEXT    NOT NULL,
    location_city     TEXT,
    location_state    TEXT,
    source            TEXT    NOT NULL CHECK (source IN ('carrier_webhook','driver_app','store_staff','system')),
    carrier_event_ref TEXT    UNIQUE,                     -- dedupe webhook retries
    raw_payload       TEXT    CHECK (raw_payload IS NULL OR json_valid(raw_payload)),
    occurred_at       TEXT    NOT NULL,
    received_at       TEXT    NOT NULL,
    CHECK (received_at >= occurred_at)
) STRICT;
CREATE INDEX ix_tracking_shipment ON shipment_tracking_events(shipment_id, occurred_at);

-- -----------------------------------------------------------------------------
-- 9. RETURNS, REFUNDS AND MONEY LEDGERS
-- -----------------------------------------------------------------------------

-- A return (RMA) covers claims (damage, defect, wrong/missing) and change-of-mind.
CREATE TABLE returns (
    return_id          INTEGER PRIMARY KEY,
    rma_number         TEXT    NOT NULL UNIQUE,                  -- 'RMA-300001'
    order_id           INTEGER NOT NULL,
    customer_id        INTEGER NOT NULL,
    status             TEXT    NOT NULL DEFAULT 'requested' CHECK (status IN (
                         'requested','needs_review','approved','rejected','awaiting_items',
                         'received','inspected','completed','cancelled')),
    eligibility        TEXT    NOT NULL CHECK (eligibility IN ('auto_approved','needs_review','ineligible')),
    ineligible_reason  TEXT,
    remedy             TEXT    CHECK (remedy IN ('refund_original_payment','store_credit','replacement','redelivery')),
    return_method      TEXT    NOT NULL CHECK (return_method IN ('not_required','courier_pickup','in_store_dropoff','carrier_label')),
    initiated_via      TEXT    NOT NULL CHECK (initiated_via IN ('chat_agent','web','phone','in_store','email')),
    customer_notes     TEXT,
    decided_by_type    TEXT    CHECK (decided_by_type IN ('ai_agent','staff','system')),
    decided_by_staff_id INTEGER REFERENCES staff_users(staff_id),
    replacement_order_id INTEGER REFERENCES orders(order_id),
    requested_at       TEXT    NOT NULL,
    decided_at         TEXT,
    received_at        TEXT,
    closed_at          TEXT,
    FOREIGN KEY (order_id, customer_id) REFERENCES orders(order_id, customer_id),
    UNIQUE (return_id, order_id),
    CHECK ((eligibility = 'ineligible') = (ineligible_reason IS NOT NULL)),
    CHECK (eligibility <> 'ineligible' OR status IN ('rejected','cancelled')),
    CHECK (status IN ('requested','needs_review','cancelled') OR decided_at IS NOT NULL),
    CHECK (decided_by_type <> 'staff' OR decided_by_staff_id IS NOT NULL),
    CHECK (replacement_order_id IS NULL OR remedy = 'replacement')
) STRICT;
CREATE INDEX ix_returns_order ON returns(order_id, customer_id);
CREATE INDEX ix_returns_customer ON returns(customer_id, requested_at);
CREATE INDEX ix_returns_status ON returns(status);
CREATE INDEX ix_returns_staff ON returns(decided_by_staff_id);
CREATE INDEX ix_returns_replacement ON returns(replacement_order_id);

CREATE TABLE return_items (
    return_item_id   INTEGER PRIMARY KEY,
    return_id        INTEGER NOT NULL,
    order_id         INTEGER NOT NULL,
    order_item_id    INTEGER NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    reason_code      TEXT    NOT NULL CHECK (reason_code IN (
                       'damaged_in_transit','broken_on_arrival','corked_or_flawed','leaking',
                       'wrong_item','missing_item','change_of_mind','late_delivery')),
    item_condition   TEXT    CHECK (item_condition IN ('unopened','opened','broken','defective','not_received')),
    disposition      TEXT    NOT NULL DEFAULT 'pending' CHECK (disposition IN ('pending','restock','destroy','return_to_vendor','customer_keeps')),
    restocking_fee_bps INTEGER NOT NULL DEFAULT 0 CHECK (restocking_fee_bps BETWEEN 0 AND 10000),
    inspection_notes TEXT,
    FOREIGN KEY (return_id, order_id) REFERENCES returns(return_id, order_id),
    FOREIGN KEY (order_id, order_item_id) REFERENCES order_items(order_id, order_item_id),
    UNIQUE (return_id, order_item_id),
    UNIQUE (return_item_id, return_id),
    CHECK (reason_code = 'change_of_mind' OR restocking_fee_bps = 0),       -- A-34
    CHECK (disposition <> 'restock' OR item_condition = 'unopened')
) STRICT;
CREATE INDEX ix_return_items_item ON return_items(order_id, order_item_id);
CREATE INDEX ix_return_items_return ON return_items(return_id, order_id);

-- Photo evidence (request_evidence_upload). Only an object-store reference.
CREATE TABLE return_evidence (
    evidence_id      INTEGER PRIMARY KEY,
    return_id        INTEGER NOT NULL REFERENCES returns(return_id),
    return_item_id   INTEGER,
    evidence_type    TEXT    NOT NULL CHECK (evidence_type IN ('photo','video','carrier_report','receipt')),
    storage_ref      TEXT    NOT NULL UNIQUE,
    uploaded_at      TEXT    NOT NULL,
    FOREIGN KEY (return_item_id, return_id) REFERENCES return_items(return_item_id, return_id)
) STRICT;
CREATE INDEX ix_return_evidence_return ON return_evidence(return_id);
CREATE INDEX ix_return_evidence_item ON return_evidence(return_item_id, return_id);

-- A refund is the business decision; money moves through payment_transactions,
-- store_credit_transactions and gift_card_transactions that point back to it.
CREATE TABLE refunds (
    refund_id             INTEGER PRIMARY KEY,
    refund_number         TEXT    NOT NULL UNIQUE,               -- 'RF-400001'
    order_id              INTEGER NOT NULL REFERENCES orders(order_id),
    return_id             INTEGER,
    reason_code           TEXT    NOT NULL CHECK (reason_code IN (
                            'damaged_in_transit','broken_on_arrival','corked_or_flawed','leaking','wrong_item',
                            'missing_item','change_of_mind','late_delivery','order_cancelled','item_out_of_stock',
                            'price_adjustment','price_match','failed_delivery','duplicate_charge')),
    method                TEXT    NOT NULL CHECK (method IN ('original_payment','store_credit')),
    status                TEXT    NOT NULL DEFAULT 'pending_approval' CHECK (status IN (
                            'pending_approval','approved','processing','succeeded','failed','rejected','cancelled')),
    items_amount_cents    INTEGER NOT NULL DEFAULT 0 CHECK (items_amount_cents >= 0),
    tax_amount_cents      INTEGER NOT NULL DEFAULT 0 CHECK (tax_amount_cents >= 0),       -- tax on products only
    shipping_amount_cents INTEGER NOT NULL DEFAULT 0 CHECK (shipping_amount_cents >= 0),  -- fee + tax on the fee
    tip_amount_cents      INTEGER NOT NULL DEFAULT 0 CHECK (tip_amount_cents >= 0),
    restocking_fee_cents  INTEGER NOT NULL DEFAULT 0 CHECK (restocking_fee_cents >= 0),
    amount_cents          INTEGER NOT NULL CHECK (amount_cents > 0),
    requires_human_approval INTEGER NOT NULL DEFAULT 0 CHECK (requires_human_approval IN (0,1)),
    approved_by_staff_id  INTEGER REFERENCES staff_users(staff_id),
    initiated_by_type     TEXT    NOT NULL CHECK (initiated_by_type IN ('customer','ai_agent','staff','system')),
    initiated_by_ref      TEXT,
    idempotency_key       TEXT    NOT NULL UNIQUE,
    note                  TEXT,
    created_at            TEXT    NOT NULL,
    approved_at           TEXT,
    completed_at          TEXT,
    FOREIGN KEY (return_id, order_id) REFERENCES returns(return_id, order_id),
    UNIQUE (refund_id, order_id),
    CHECK (amount_cents = items_amount_cents + tax_amount_cents + shipping_amount_cents + tip_amount_cents - restocking_fee_cents),
    CHECK (restocking_fee_cents = 0 OR (reason_code = 'change_of_mind' AND method = 'original_payment')),  -- A-34
    -- A-60/A-62: the AI agent may not complete a refund over $150 on its own.
    CHECK (initiated_by_type <> 'ai_agent' OR amount_cents <= 15000 OR requires_human_approval = 1),
    CHECK (requires_human_approval = 0 OR status IN ('pending_approval','rejected','cancelled') OR approved_by_staff_id IS NOT NULL),
    CHECK (status <> 'succeeded' OR completed_at IS NOT NULL)
) STRICT;
CREATE INDEX ix_refunds_order ON refunds(order_id);
CREATE INDEX ix_refunds_return ON refunds(return_id, order_id);
CREATE INDEX ix_refunds_status ON refunds(status);
CREATE INDEX ix_refunds_staff ON refunds(approved_by_staff_id);

-- Which units/lines a refund covers (partial refunds). quantity 0 = price-only
-- adjustment on a line (price correction, price match).
CREATE TABLE refund_items (
    refund_id      INTEGER NOT NULL,
    order_id       INTEGER NOT NULL,
    order_item_id  INTEGER NOT NULL,
    quantity       INTEGER NOT NULL CHECK (quantity >= 0),
    amount_cents   INTEGER NOT NULL CHECK (amount_cents > 0),   -- items + tax for this line
    PRIMARY KEY (refund_id, order_item_id),
    FOREIGN KEY (refund_id, order_id) REFERENCES refunds(refund_id, order_id),
    FOREIGN KEY (order_id, order_item_id) REFERENCES order_items(order_id, order_item_id)
) STRICT;
CREATE INDEX ix_refund_items_item ON refund_items(order_id, order_item_id);
CREATE INDEX ix_refund_items_refund ON refund_items(refund_id, order_id);

CREATE TABLE payment_transactions (
    transaction_id        INTEGER PRIMARY KEY,
    payment_id            INTEGER NOT NULL,
    order_id              INTEGER NOT NULL,
    transaction_type      TEXT    NOT NULL CHECK (transaction_type IN (
                            'authorization','capture','void','refund','chargeback','chargeback_reversal')),
    status                TEXT    NOT NULL CHECK (status IN ('pending','succeeded','failed')),
    amount_cents          INTEGER NOT NULL CHECK (amount_cents > 0),
    parent_transaction_id INTEGER REFERENCES payment_transactions(transaction_id),
    refund_id             INTEGER,
    shipment_id           INTEGER REFERENCES shipments(shipment_id),    -- capture triggered by fulfillment
    processor_reference   TEXT    UNIQUE,
    failure_code          TEXT,
    failure_message       TEXT,
    idempotency_key       TEXT    NOT NULL UNIQUE,
    created_at            TEXT    NOT NULL,
    processed_at          TEXT,
    FOREIGN KEY (payment_id, order_id) REFERENCES payments(payment_id, order_id),
    FOREIGN KEY (refund_id, order_id) REFERENCES refunds(refund_id, order_id),
    CHECK ((transaction_type = 'refund') = (refund_id IS NOT NULL)),
    CHECK (transaction_type NOT IN ('capture','void','refund') OR parent_transaction_id IS NOT NULL),
    CHECK ((status = 'failed') = (failure_code IS NOT NULL)),
    CHECK (status = 'pending' OR processed_at IS NOT NULL)
) STRICT;
CREATE INDEX ix_ptx_payment ON payment_transactions(payment_id, transaction_type, status);
CREATE INDEX ix_ptx_payment_order ON payment_transactions(payment_id, order_id);
CREATE INDEX ix_ptx_order ON payment_transactions(order_id);
CREATE INDEX ix_ptx_parent ON payment_transactions(parent_transaction_id);
CREATE INDEX ix_ptx_refund ON payment_transactions(refund_id, order_id);
CREATE INDEX ix_ptx_shipment ON payment_transactions(shipment_id);

-- Store credit: instant, never expires, no cash value (A-36, RF-R6).
-- Positive = credit issued; negative = spent. Balance = SUM(amount_cents).
CREATE TABLE store_credit_transactions (
    store_credit_txn_id INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    entry_type      TEXT    NOT NULL CHECK (entry_type IN ('issue_refund','issue_goodwill','redeem','reversal','adjustment')),
    amount_cents    INTEGER NOT NULL CHECK (amount_cents <> 0),
    order_id        INTEGER REFERENCES orders(order_id),
    refund_id       INTEGER REFERENCES refunds(refund_id),
    payment_id      INTEGER REFERENCES payments(payment_id),
    reason          TEXT    NOT NULL,
    issued_by_type  TEXT    NOT NULL CHECK (issued_by_type IN ('ai_agent','staff','system')),
    issued_by_ref   TEXT,
    created_at      TEXT    NOT NULL,
    CHECK (entry_type NOT IN ('issue_refund','issue_goodwill') OR amount_cents > 0),
    CHECK (entry_type <> 'redeem' OR (amount_cents < 0 AND payment_id IS NOT NULL)),
    CHECK (entry_type <> 'issue_refund' OR refund_id IS NOT NULL),
    CHECK (entry_type <> 'issue_goodwill' OR issued_by_type <> 'ai_agent' OR amount_cents <= 1500)  -- A-61
) STRICT;
CREATE INDEX ix_sct_customer ON store_credit_transactions(customer_id, created_at);
CREATE INDEX ix_sct_order ON store_credit_transactions(order_id);
CREATE INDEX ix_sct_refund ON store_credit_transactions(refund_id);
CREATE INDEX ix_sct_payment ON store_credit_transactions(payment_id);

CREATE TABLE gift_card_transactions (
    gift_card_txn_id INTEGER PRIMARY KEY,
    gift_card_id    INTEGER NOT NULL REFERENCES gift_cards(gift_card_id),
    entry_type      TEXT    NOT NULL CHECK (entry_type IN ('activation','redemption','refund','adjustment')),
    amount_cents    INTEGER NOT NULL CHECK (amount_cents <> 0),
    payment_id      INTEGER REFERENCES payments(payment_id),
    refund_id       INTEGER REFERENCES refunds(refund_id),
    created_at      TEXT    NOT NULL,
    CHECK (entry_type NOT IN ('activation','refund') OR amount_cents > 0),
    CHECK (entry_type <> 'redemption' OR (amount_cents < 0 AND payment_id IS NOT NULL)),
    CHECK (entry_type <> 'refund' OR refund_id IS NOT NULL)
) STRICT;
CREATE INDEX ix_gct_card ON gift_card_transactions(gift_card_id, created_at);
CREATE INDEX ix_gct_payment ON gift_card_transactions(payment_id);
CREATE INDEX ix_gct_refund ON gift_card_transactions(refund_id);

-- -----------------------------------------------------------------------------
-- 10. LOYALTY ("Rewards", A-53)
-- -----------------------------------------------------------------------------

CREATE TABLE loyalty_accounts (
    customer_id     INTEGER PRIMARY KEY REFERENCES customers(customer_id),
    tier            TEXT    NOT NULL DEFAULT 'member' CHECK (tier IN ('member','insider')),
    status          TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active','suspended','closed')),
    enrolled_at     TEXT    NOT NULL,
    tier_updated_at TEXT    NOT NULL
) STRICT;

-- 250 points = $10 reward; rewards expire after 90 days.
CREATE TABLE loyalty_rewards (
    reward_id       INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES loyalty_accounts(customer_id),
    value_cents     INTEGER NOT NULL CHECK (value_cents > 0),
    points_cost     INTEGER NOT NULL CHECK (points_cost > 0),
    status          TEXT    NOT NULL DEFAULT 'available' CHECK (status IN ('available','redeemed','expired','void')),
    issued_at       TEXT    NOT NULL,
    expires_at      TEXT    NOT NULL,
    redeemed_order_id INTEGER REFERENCES orders(order_id),
    redeemed_at     TEXT,
    CHECK (expires_at > issued_at),
    CHECK ((status = 'redeemed') = (redeemed_order_id IS NOT NULL AND redeemed_at IS NOT NULL))
) STRICT;
CREATE INDEX ix_rewards_customer ON loyalty_rewards(customer_id, status);
CREATE INDEX ix_rewards_order ON loyalty_rewards(redeemed_order_id);

-- Points ledger. Balance = SUM(points); cannot go negative (trigger).
CREATE TABLE loyalty_point_transactions (
    loyalty_txn_id  INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES loyalty_accounts(customer_id),
    entry_type      TEXT    NOT NULL CHECK (entry_type IN ('earn','convert_to_reward','adjustment','expire','reversal')),
    points          INTEGER NOT NULL CHECK (points <> 0),
    order_id        INTEGER REFERENCES orders(order_id),
    reward_id       INTEGER REFERENCES loyalty_rewards(reward_id),
    reason          TEXT    NOT NULL,
    created_by_type TEXT    NOT NULL CHECK (created_by_type IN ('ai_agent','staff','system')),
    created_at      TEXT    NOT NULL,
    CHECK (entry_type <> 'earn' OR (points > 0 AND order_id IS NOT NULL)),
    CHECK (entry_type <> 'convert_to_reward' OR (points < 0 AND reward_id IS NOT NULL)),
    CHECK (entry_type <> 'expire' OR points < 0)
) STRICT;
CREATE INDEX ix_loyalty_txn_customer ON loyalty_point_transactions(customer_id, created_at);
CREATE INDEX ix_loyalty_txn_order ON loyalty_point_transactions(order_id);
CREATE INDEX ix_loyalty_txn_reward ON loyalty_point_transactions(reward_id);

-- -----------------------------------------------------------------------------
-- 11. CUSTOMER SUPPORT
-- -----------------------------------------------------------------------------

CREATE TABLE support_tickets (
    ticket_id        INTEGER PRIMARY KEY,
    ticket_number    TEXT    NOT NULL UNIQUE,                     -- 'TKT-500001'
    customer_id      INTEGER REFERENCES customers(customer_id),   -- NULL = unauthenticated contact
    order_id         INTEGER REFERENCES orders(order_id),
    return_id        INTEGER REFERENCES returns(return_id),
    conversation_id  TEXT,                                        -- chat session that created it
    channel          TEXT    NOT NULL CHECK (channel IN ('chat_agent','email','phone','web_form','sms','in_store')),
    category         TEXT    NOT NULL CHECK (category IN (
                       'order_status','delivery_issue','pickup_issue','damaged_item','flawed_wine','wrong_or_missing_item',
                       'return_request','refund_status','pricing_dispute','price_match','promo_code','loyalty',
                       'account_access','age_verification','privacy_request','payment_issue','product_question',
                       'product_request','bulk_or_event_order','complaint','compliance','fraud','general')),
    priority         TEXT    NOT NULL CHECK (priority IN ('P1','P2','P3')),
    reason_code      TEXT    CHECK (reason_code IN (                                -- _KB/00 escalation matrix
                       'handoff_compliance_incident','underage_risk','legal_matter','safety_crisis','fraud_signal',
                       'account_takeover','refund_over_limit','claim_review','policy_exception_request','price_match',
                       'pricing_dispute','fulfillment_delay','bulk_order','account_recovery','privacy_request',
                       'id_verification_failure','pre_arrival_issue','product_request','conduct_complaint','kb_gap',
                       'customer_requested_human','tool_failure','refund_trace')),
    status           TEXT    NOT NULL DEFAULT 'new' CHECK (status IN ('new','open','pending_customer','pending_internal','escalated','resolved','closed')),
    subject          TEXT    NOT NULL,
    summary          TEXT    NOT NULL,
    customer_sentiment TEXT  CHECK (customer_sentiment IN ('positive','neutral','frustrated','angry')),
    assigned_team    TEXT    CHECK (assigned_team IN ('support','fulfillment','finance','compliance','pricing','events','privacy','catalog')),
    assigned_staff_id INTEGER REFERENCES staff_users(staff_id),
    sla_due_at       TEXT    NOT NULL,
    first_response_at TEXT,
    resolved_at      TEXT,
    closed_at        TEXT,
    csat_score       INTEGER CHECK (csat_score BETWEEN 1 AND 5),
    created_by_type  TEXT    NOT NULL CHECK (created_by_type IN ('customer','ai_agent','staff','system')),
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    CHECK (sla_due_at > created_at),
    CHECK (status NOT IN ('resolved','closed') OR resolved_at IS NOT NULL),
    CHECK (status <> 'closed' OR closed_at IS NOT NULL),
    CHECK (priority <> 'P1' OR reason_code IS NOT NULL)
) STRICT;
CREATE INDEX ix_tickets_customer ON support_tickets(customer_id, created_at);
CREATE INDEX ix_tickets_order ON support_tickets(order_id);
CREATE INDEX ix_tickets_return ON support_tickets(return_id);
CREATE INDEX ix_tickets_queue ON support_tickets(status, priority, sla_due_at);
CREATE INDEX ix_tickets_staff ON support_tickets(assigned_staff_id);
CREATE INDEX ix_tickets_conversation ON support_tickets(conversation_id);

-- Append-only conversation on a ticket. Internal notes are never shown to customers.
CREATE TABLE ticket_messages (
    message_id       INTEGER PRIMARY KEY,
    ticket_id        INTEGER NOT NULL REFERENCES support_tickets(ticket_id),
    author_type      TEXT    NOT NULL CHECK (author_type IN ('customer','ai_agent','staff','system')),
    author_customer_id INTEGER REFERENCES customers(customer_id),
    author_staff_id  INTEGER REFERENCES staff_users(staff_id),
    visibility       TEXT    NOT NULL DEFAULT 'public' CHECK (visibility IN ('public','internal')),
    body             TEXT    NOT NULL CHECK (length(body) > 0),
    attachment_refs  TEXT    CHECK (attachment_refs IS NULL OR json_valid(attachment_refs)),
    created_at       TEXT    NOT NULL,
    CHECK ((author_type = 'customer') = (author_customer_id IS NOT NULL)),
    CHECK ((author_type = 'staff') = (author_staff_id IS NOT NULL)),
    CHECK (author_type <> 'customer' OR visibility = 'public')
) STRICT;
CREATE INDEX ix_ticket_messages_ticket ON ticket_messages(ticket_id, created_at);
CREATE INDEX ix_ticket_messages_customer ON ticket_messages(author_customer_id);
CREATE INDEX ix_ticket_messages_staff ON ticket_messages(author_staff_id);

-- -----------------------------------------------------------------------------
-- 12. AUDIT LOG (append-only; written by the API layer in the same transaction
--     as the change it describes). No secrets, card data or ID images, ever.
-- -----------------------------------------------------------------------------

CREATE TABLE audit_logs (
    audit_id        INTEGER PRIMARY KEY,
    occurred_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    actor_type      TEXT    NOT NULL CHECK (actor_type IN ('customer','ai_agent','staff','system','carrier','payment_processor')),
    actor_ref       TEXT    NOT NULL,                     -- customer_number, employee_code, service name
    action          TEXT    NOT NULL CHECK (action GLOB '[a-z]*.[a-z]*'),   -- 'order.cancel'
    entity_type     TEXT    NOT NULL,
    entity_id       TEXT    NOT NULL,
    customer_id     INTEGER REFERENCES customers(customer_id),        -- for per-customer access reviews
    outcome         TEXT    NOT NULL CHECK (outcome IN ('success','denied','failed','requires_approval')),
    reason          TEXT,
    conversation_id TEXT,
    request_id      TEXT,
    idempotency_key TEXT,
    before_state    TEXT    CHECK (before_state IS NULL OR json_valid(before_state)),
    after_state     TEXT    CHECK (after_state  IS NULL OR json_valid(after_state)),
    ip_address      TEXT
) STRICT;
CREATE INDEX ix_audit_entity ON audit_logs(entity_type, entity_id, occurred_at);
CREATE INDEX ix_audit_customer ON audit_logs(customer_id, occurred_at);
CREATE INDEX ix_audit_actor ON audit_logs(actor_type, actor_ref, occurred_at);
CREATE INDEX ix_audit_action ON audit_logs(action, occurred_at);

-- =============================================================================
-- 13. INTEGRITY TRIGGERS
--     Rules that CHECK/FK cannot express (cross-row sums, immutability).
--     PostgreSQL: re-implement as PL/pgSQL trigger functions (see README).
-- =============================================================================

-- 13.1 Append-only ledgers and histories ---------------------------------------
CREATE TRIGGER trg_audit_logs_no_update BEFORE UPDATE ON audit_logs
BEGIN SELECT RAISE(ABORT, 'audit_logs is append-only'); END;
CREATE TRIGGER trg_audit_logs_no_delete BEFORE DELETE ON audit_logs
BEGIN SELECT RAISE(ABORT, 'audit_logs is append-only'); END;

CREATE TRIGGER trg_inventory_movements_no_update BEFORE UPDATE ON inventory_movements
BEGIN SELECT RAISE(ABORT, 'inventory_movements is append-only; post a correcting movement'); END;
CREATE TRIGGER trg_inventory_movements_no_delete BEFORE DELETE ON inventory_movements
BEGIN SELECT RAISE(ABORT, 'inventory_movements is append-only; post a correcting movement'); END;

CREATE TRIGGER trg_order_status_history_no_update BEFORE UPDATE ON order_status_history
BEGIN SELECT RAISE(ABORT, 'order_status_history is append-only'); END;
CREATE TRIGGER trg_order_status_history_no_delete BEFORE DELETE ON order_status_history
BEGIN SELECT RAISE(ABORT, 'order_status_history is append-only'); END;

CREATE TRIGGER trg_tracking_events_no_update BEFORE UPDATE ON shipment_tracking_events
BEGIN SELECT RAISE(ABORT, 'shipment_tracking_events is append-only'); END;
CREATE TRIGGER trg_tracking_events_no_delete BEFORE DELETE ON shipment_tracking_events
BEGIN SELECT RAISE(ABORT, 'shipment_tracking_events is append-only'); END;

CREATE TRIGGER trg_ticket_messages_no_update BEFORE UPDATE ON ticket_messages
BEGIN SELECT RAISE(ABORT, 'ticket_messages is append-only; add a new message'); END;
CREATE TRIGGER trg_ticket_messages_no_delete BEFORE DELETE ON ticket_messages
BEGIN SELECT RAISE(ABORT, 'ticket_messages is append-only; add a new message'); END;

CREATE TRIGGER trg_store_credit_no_update BEFORE UPDATE ON store_credit_transactions
BEGIN SELECT RAISE(ABORT, 'store_credit_transactions is append-only; post a reversal'); END;
CREATE TRIGGER trg_store_credit_no_delete BEFORE DELETE ON store_credit_transactions
BEGIN SELECT RAISE(ABORT, 'store_credit_transactions is append-only; post a reversal'); END;

CREATE TRIGGER trg_gift_card_txn_no_update BEFORE UPDATE ON gift_card_transactions
BEGIN SELECT RAISE(ABORT, 'gift_card_transactions is append-only'); END;
CREATE TRIGGER trg_gift_card_txn_no_delete BEFORE DELETE ON gift_card_transactions
BEGIN SELECT RAISE(ABORT, 'gift_card_transactions is append-only'); END;

CREATE TRIGGER trg_loyalty_txn_no_update BEFORE UPDATE ON loyalty_point_transactions
BEGIN SELECT RAISE(ABORT, 'loyalty_point_transactions is append-only'); END;
CREATE TRIGGER trg_loyalty_txn_no_delete BEFORE DELETE ON loyalty_point_transactions
BEGIN SELECT RAISE(ABORT, 'loyalty_point_transactions is append-only'); END;

-- Payment transactions: only a pending row may change, and only its outcome.
CREATE TRIGGER trg_ptx_no_delete BEFORE DELETE ON payment_transactions
BEGIN SELECT RAISE(ABORT, 'payment_transactions is append-only'); END;
CREATE TRIGGER trg_ptx_only_pending_changes BEFORE UPDATE ON payment_transactions
WHEN OLD.status <> 'pending'
  OR NEW.payment_id <> OLD.payment_id OR NEW.order_id <> OLD.order_id
  OR NEW.transaction_type <> OLD.transaction_type OR NEW.amount_cents <> OLD.amount_cents
  OR NEW.refund_id IS NOT OLD.refund_id OR NEW.parent_transaction_id IS NOT OLD.parent_transaction_id
BEGIN SELECT RAISE(ABORT, 'only the outcome of a pending payment transaction can be updated'); END;

-- 13.2 Order-item snapshot is immutable ----------------------------------------
CREATE TRIGGER trg_order_items_snapshot_immutable BEFORE UPDATE OF
    order_id, line_number, variant_id, price_id, sku, product_name, brand_name, vintage_year, size_ml,
    pack_quantity, is_final_sale, is_vintage_specific, unit_regular_price_cents, unit_price_cents,
    quantity, line_subtotal_cents, discount_cents, tax_cents, line_total_cents ON order_items
BEGIN SELECT RAISE(ABORT, 'order_items snapshot is immutable; use cancellations, refunds or substitutions'); END;
CREATE TRIGGER trg_order_items_no_delete BEFORE DELETE ON order_items
BEGIN SELECT RAISE(ABORT, 'order_items cannot be deleted; cancel the quantity instead'); END;

-- 13.3 Quantity invariants (partial shipments / partial returns / partial refunds)
-- Shipped (non-cancelled shipments) <= ordered - cancelled.
CREATE TRIGGER trg_shipment_items_qty_cap BEFORE INSERT ON shipment_items
WHEN NEW.quantity + COALESCE((
        SELECT SUM(si.quantity) FROM shipment_items si
        JOIN shipments s ON s.shipment_id = si.shipment_id
        WHERE si.order_item_id = NEW.order_item_id AND s.status <> 'cancelled'), 0)
   > (SELECT quantity - quantity_cancelled FROM order_items WHERE order_item_id = NEW.order_item_id)
BEGIN SELECT RAISE(ABORT, 'shipment quantity exceeds ordered minus cancelled quantity'); END;

CREATE TRIGGER trg_order_items_cancel_cap BEFORE UPDATE OF quantity_cancelled ON order_items
WHEN NEW.quantity - NEW.quantity_cancelled < COALESCE((
        SELECT SUM(si.quantity) FROM shipment_items si
        JOIN shipments s ON s.shipment_id = si.shipment_id
        WHERE si.order_item_id = NEW.order_item_id AND s.status <> 'cancelled'), 0)
BEGIN SELECT RAISE(ABORT, 'cannot cancel units already assigned to a shipment'); END;

-- Returned (open or completed returns) <= shipped.
CREATE TRIGGER trg_return_items_qty_cap BEFORE INSERT ON return_items
WHEN NEW.quantity + COALESCE((
        SELECT SUM(ri.quantity) FROM return_items ri
        JOIN returns r ON r.return_id = ri.return_id
        WHERE ri.order_item_id = NEW.order_item_id AND r.status NOT IN ('rejected','cancelled')), 0)
   > COALESCE((
        SELECT SUM(si.quantity) FROM shipment_items si
        JOIN shipments s ON s.shipment_id = si.shipment_id
        WHERE si.order_item_id = NEW.order_item_id AND s.status <> 'cancelled'), 0)
BEGIN SELECT RAISE(ABORT, 'return quantity exceeds shipped quantity'); END;

-- Refunded units <= ordered units and refunded money <= line total.
CREATE TRIGGER trg_refund_items_cap BEFORE INSERT ON refund_items
WHEN NEW.quantity + COALESCE((
        SELECT SUM(fi.quantity) FROM refund_items fi JOIN refunds f ON f.refund_id = fi.refund_id
        WHERE fi.order_item_id = NEW.order_item_id AND f.status NOT IN ('failed','rejected','cancelled')), 0)
     > (SELECT quantity FROM order_items WHERE order_item_id = NEW.order_item_id)
  OR NEW.amount_cents + COALESCE((
        SELECT SUM(fi.amount_cents) FROM refund_items fi JOIN refunds f ON f.refund_id = fi.refund_id
        WHERE fi.order_item_id = NEW.order_item_id AND f.status NOT IN ('failed','rejected','cancelled')), 0)
     > (SELECT line_total_cents FROM order_items WHERE order_item_id = NEW.order_item_id)
BEGIN SELECT RAISE(ABORT, 'refund exceeds the order line (quantity or amount)'); END;

-- Total refunds on an order <= what the customer was charged.
CREATE TRIGGER trg_refunds_order_cap BEFORE INSERT ON refunds
WHEN NEW.amount_cents + COALESCE((
        SELECT SUM(amount_cents) FROM refunds
        WHERE order_id = NEW.order_id AND status NOT IN ('failed','rejected','cancelled')), 0)
   > (SELECT grand_total_cents FROM orders WHERE order_id = NEW.order_id)
BEGIN SELECT RAISE(ABORT, 'refunds would exceed the order total'); END;

-- 13.4 Payment money invariants -------------------------------------------------
-- captured + voided <= authorized;  refunded <= captured;  parents must match.
CREATE TRIGGER trg_ptx_parent_matches BEFORE INSERT ON payment_transactions
WHEN NEW.parent_transaction_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM payment_transactions p
        WHERE p.transaction_id = NEW.parent_transaction_id
          AND p.payment_id = NEW.payment_id AND p.status = 'succeeded'
          AND p.transaction_type = CASE NEW.transaction_type
                WHEN 'capture' THEN 'authorization' WHEN 'void' THEN 'authorization'
                WHEN 'refund' THEN 'capture' ELSE p.transaction_type END)
BEGIN SELECT RAISE(ABORT, 'parent transaction must be a succeeded authorization (capture/void) or capture (refund) on the same payment'); END;

CREATE TRIGGER trg_ptx_capture_cap_ins BEFORE INSERT ON payment_transactions
WHEN NEW.status = 'succeeded' AND NEW.transaction_type IN ('capture','void')
 AND NEW.amount_cents + COALESCE((SELECT SUM(amount_cents) FROM payment_transactions
        WHERE payment_id = NEW.payment_id AND status = 'succeeded' AND transaction_type IN ('capture','void')), 0)
   > COALESCE((SELECT SUM(amount_cents) FROM payment_transactions
        WHERE payment_id = NEW.payment_id AND status = 'succeeded' AND transaction_type = 'authorization'), 0)
BEGIN SELECT RAISE(ABORT, 'capture/void exceeds the authorized amount'); END;

CREATE TRIGGER trg_ptx_capture_cap_upd BEFORE UPDATE OF status ON payment_transactions
WHEN NEW.status = 'succeeded' AND NEW.transaction_type IN ('capture','void')
 AND NEW.amount_cents + COALESCE((SELECT SUM(amount_cents) FROM payment_transactions
        WHERE payment_id = NEW.payment_id AND status = 'succeeded' AND transaction_type IN ('capture','void')
          AND transaction_id <> NEW.transaction_id), 0)
   > COALESCE((SELECT SUM(amount_cents) FROM payment_transactions
        WHERE payment_id = NEW.payment_id AND status = 'succeeded' AND transaction_type = 'authorization'), 0)
BEGIN SELECT RAISE(ABORT, 'capture/void exceeds the authorized amount'); END;

CREATE TRIGGER trg_ptx_refund_cap_ins BEFORE INSERT ON payment_transactions
WHEN NEW.transaction_type = 'refund' AND NEW.status IN ('pending','succeeded')
 AND NEW.amount_cents + COALESCE((SELECT SUM(amount_cents) FROM payment_transactions
        WHERE payment_id = NEW.payment_id AND status IN ('pending','succeeded') AND transaction_type = 'refund'), 0)
   > COALESCE((SELECT SUM(amount_cents) FROM payment_transactions
        WHERE payment_id = NEW.payment_id AND status = 'succeeded' AND transaction_type = 'capture'), 0)
BEGIN SELECT RAISE(ABORT, 'refund exceeds the captured amount on this payment'); END;

-- 13.5 Ledger balances never go negative ----------------------------------------
CREATE TRIGGER trg_store_credit_balance BEFORE INSERT ON store_credit_transactions
WHEN NEW.amount_cents < 0 AND NEW.amount_cents + COALESCE((
        SELECT SUM(amount_cents) FROM store_credit_transactions WHERE customer_id = NEW.customer_id), 0) < 0
BEGIN SELECT RAISE(ABORT, 'insufficient store credit'); END;

CREATE TRIGGER trg_gift_card_balance BEFORE INSERT ON gift_card_transactions
WHEN NEW.amount_cents < 0 AND NEW.amount_cents + COALESCE((
        SELECT SUM(amount_cents) FROM gift_card_transactions WHERE gift_card_id = NEW.gift_card_id), 0) < 0
BEGIN SELECT RAISE(ABORT, 'insufficient gift card balance'); END;

CREATE TRIGGER trg_loyalty_balance BEFORE INSERT ON loyalty_point_transactions
WHEN NEW.points < 0 AND NEW.points + COALESCE((
        SELECT SUM(points) FROM loyalty_point_transactions WHERE customer_id = NEW.customer_id), 0) < 0
BEGIN SELECT RAISE(ABORT, 'insufficient loyalty points'); END;

-- 13.6 Compliance and catalog rules ---------------------------------------------
-- A-01: the shipping address must be in the fulfilling store's state.
CREATE TRIGGER trg_order_address_state_ins BEFORE INSERT ON order_addresses
WHEN NEW.address_role = 'shipping' AND NEW.state_code <> (
        SELECT s.state_code FROM orders o JOIN stores s ON s.store_id = o.store_id WHERE o.order_id = NEW.order_id)
BEGIN SELECT RAISE(ABORT, 'shipping address state must match the fulfilling store state (A-01)'); END;
CREATE TRIGGER trg_order_address_state_upd BEFORE UPDATE OF state_code, address_role ON order_addresses
WHEN NEW.address_role = 'shipping' AND NEW.state_code <> (
        SELECT s.state_code FROM orders o JOIN stores s ON s.store_id = o.store_id WHERE o.order_id = NEW.order_id)
BEGIN SELECT RAISE(ABORT, 'shipping address state must match the fulfilling store state (A-01)'); END;

-- A-75: at most 10 saved (non-deleted) addresses per customer.
CREATE TRIGGER trg_customer_addresses_max BEFORE INSERT ON customer_addresses
WHEN (SELECT COUNT(*) FROM customer_addresses WHERE customer_id = NEW.customer_id AND deleted_at IS NULL) >= 10
BEGIN SELECT RAISE(ABORT, 'a customer can save at most 10 addresses (A-75)'); END;

-- No overlapping price windows for the same store, variant and price type.
CREATE TRIGGER trg_product_prices_no_overlap BEFORE INSERT ON product_prices
WHEN EXISTS (
    SELECT 1 FROM product_prices p
    WHERE p.store_id = NEW.store_id AND p.variant_id = NEW.variant_id AND p.price_type = NEW.price_type
      AND p.starts_at < COALESCE(NEW.ends_at, '9999-12-31T00:00:00Z')
      AND NEW.starts_at < COALESCE(p.ends_at, '9999-12-31T00:00:00Z'))
BEGIN SELECT RAISE(ABORT, 'overlapping price window for this store, variant and price type'); END;

-- =============================================================================
-- 14. READ VIEWS (what the phase-2 API will mostly read from)
--     Views that depend on "now" use SQLite strftime('now'); PG: now().
-- =============================================================================

-- 'France > Bordeaux > Pauillac'
CREATE VIEW v_region_paths AS
WITH RECURSIVE walk(region_id, ancestor_id, path, depth) AS (
    SELECT region_id, parent_region_id, name, 0 FROM regions
    UNION ALL
    SELECT w.region_id, r.parent_region_id, r.name || ' > ' || w.path, w.depth + 1
    FROM walk w JOIN regions r ON r.region_id = w.ancestor_id
)
SELECT region_id, path AS region_path FROM walk WHERE ancestor_id IS NULL;

CREATE VIEW v_product_catalog AS
SELECT v.variant_id, v.sku, p.product_id, p.product_code, p.name AS product_name, b.name AS brand_name,
       p.product_type, p.wine_color, p.wine_type, p.style_code, rp.region_path,
       v.vintage_year, v.size_ml, v.pack_quantity, v.abv_percent,
       p.sweetness, p.body, p.acidity, p.tannin, p.oak, p.fruit_profile, p.closure_type,
       v.is_vintage_specific, v.is_collectible, v.is_final_sale, v.case_discount_eligible,
       (SELECT group_concat(g.name, ', ') FROM product_grapes pg JOIN grape_varieties g ON g.grape_id = pg.grape_id
         WHERE pg.product_id = p.product_id) AS grapes,
       (SELECT group_concat(vc.certification_type, ',') FROM variant_certifications vc
         WHERE vc.variant_id = v.variant_id AND vc.status = 'active') AS certifications,
       v.status AS variant_status
FROM product_variants v
JOIN products p ON p.product_id = v.product_id
JOIN brands b   ON b.brand_id = p.brand_id
LEFT JOIN v_region_paths rp ON rp.region_id = p.region_id;

-- Current regular and sale price per store x variant.
CREATE VIEW v_current_prices AS
SELECT l.store_id, l.variant_id,
       r.amount_cents AS regular_price_cents,
       s.amount_cents AS sale_price_cents,
       s.ends_at      AS sale_ends_at,
       COALESCE(s.amount_cents, r.amount_cents) AS effective_price_cents,
       COALESCE(s.compare_at_cents, r.compare_at_cents) AS compare_at_cents,
       COALESCE(s.compare_at_verified, r.compare_at_verified, 0) AS compare_at_verified
FROM product_listings l
LEFT JOIN product_prices r ON r.store_id = l.store_id AND r.variant_id = l.variant_id AND r.price_type = 'regular'
      AND r.starts_at <= strftime('%Y-%m-%dT%H:%M:%SZ','now')
      AND (r.ends_at IS NULL OR r.ends_at > strftime('%Y-%m-%dT%H:%M:%SZ','now'))
LEFT JOIN product_prices s ON s.store_id = l.store_id AND s.variant_id = l.variant_id AND s.price_type = 'sale'
      AND s.starts_at <= strftime('%Y-%m-%dT%H:%M:%SZ','now')
      AND s.ends_at > strftime('%Y-%m-%dT%H:%M:%SZ','now');

-- check_inventory: store-level availability mapped to the KB stock_status
-- vocabulary (_KB/09 inventory-status-definitions). Exact counts stay internal;
-- the agent only ever sees stock_status and qty_bucket.
CREATE VIEW v_inventory_availability AS
WITH stock AS (
    SELECT w.store_id, il.variant_id,
           SUM(il.qty_on_hand) AS qty_on_hand,
           SUM(il.qty_reserved) AS qty_reserved,
           SUM(MAX(il.qty_on_hand - il.qty_reserved - il.safety_stock, 0)) AS qty_available
    FROM inventory_levels il JOIN warehouses w ON w.warehouse_id = il.warehouse_id
    WHERE w.is_active = 1
    GROUP BY w.store_id, il.variant_id
)
SELECT l.store_id, st.state_code, l.variant_id,
       COALESCE(s.qty_on_hand, 0)   AS qty_on_hand,
       COALESCE(s.qty_reserved, 0)  AS qty_reserved,
       COALESCE(s.qty_available, 0) AS qty_available,
       CASE WHEN COALESCE(s.qty_available,0) >= 12 THEN '12+'
            WHEN COALESCE(s.qty_available,0) >= 6  THEN '6-11'
            WHEN COALESCE(s.qty_available,0) >= 1  THEN '1-5' END AS qty_bucket,
       CASE
         WHEN l.is_sellable = 0                       THEN 'not_sellable_in_jurisdiction'
         WHEN l.listing_status <> 'active'            THEN l.listing_status
         WHEN COALESCE(s.qty_available,0) > 0 AND l.allocation_limit IS NOT NULL THEN 'allocated'
         WHEN COALESCE(s.qty_available,0) >= 6       THEN 'in_stock'
         WHEN COALESCE(s.qty_available,0) >= 1       THEN 'low_stock'
         WHEN l.allocation_limit IS NOT NULL          THEN 'waitlist'
         WHEN l.backorder_allowed = 1                 THEN 'backorder'
         ELSE 'out_of_stock' END AS stock_status,
       l.is_sellable AS sellable_in_jurisdiction,
       l.allocation_limit, l.max_per_order, l.next_arrival_estimate
FROM product_listings l
JOIN stores st ON st.store_id = l.store_id
LEFT JOIN stock s ON s.store_id = l.store_id AND s.variant_id = l.variant_id;

CREATE VIEW v_customer_age_verification AS
SELECT c.customer_id,
       COALESCE(av.status, 'not_started') AS age_verification_status,
       av.completed_at AS last_completed_at
FROM customers c
LEFT JOIN (
    SELECT customer_id, status, completed_at,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY started_at DESC, age_verification_id DESC) AS rn
    FROM age_verifications
) av ON av.customer_id = c.customer_id AND av.rn = 1;

-- Per-line quantities across the whole lifecycle.
CREATE VIEW v_order_item_fulfillment AS
SELECT oi.order_id, oi.order_item_id, oi.line_number, oi.sku, oi.product_name, oi.vintage_year,
       oi.quantity AS qty_ordered, oi.quantity_cancelled AS qty_cancelled,
       COALESCE((SELECT SUM(si.quantity) FROM shipment_items si JOIN shipments s ON s.shipment_id = si.shipment_id
                 WHERE si.order_item_id = oi.order_item_id AND s.status <> 'cancelled'), 0) AS qty_shipped,
       COALESCE((SELECT SUM(si.quantity) FROM shipment_items si JOIN shipments s ON s.shipment_id = si.shipment_id
                 WHERE si.order_item_id = oi.order_item_id AND s.status IN ('delivered','picked_up')), 0) AS qty_delivered,
       COALESCE((SELECT SUM(ri.quantity) FROM return_items ri JOIN returns r ON r.return_id = ri.return_id
                 WHERE ri.order_item_id = oi.order_item_id AND r.status NOT IN ('rejected','cancelled')), 0) AS qty_returned,
       COALESCE((SELECT SUM(fi.quantity) FROM refund_items fi JOIN refunds f ON f.refund_id = fi.refund_id
                 WHERE fi.order_item_id = oi.order_item_id AND f.status = 'succeeded'), 0) AS qty_refunded,
       COALESCE((SELECT SUM(fi.amount_cents) FROM refund_items fi JOIN refunds f ON f.refund_id = fi.refund_id
                 WHERE fi.order_item_id = oi.order_item_id AND f.status = 'succeeded'), 0) AS amount_refunded_cents,
       oi.line_total_cents
FROM order_items oi;

CREATE VIEW v_payment_balances AS
SELECT p.payment_id, p.order_id, p.tender_type, p.amount_cents, p.status,
       COALESCE(SUM(CASE WHEN t.transaction_type = 'authorization' AND t.status = 'succeeded' THEN t.amount_cents END), 0) AS authorized_cents,
       COALESCE(SUM(CASE WHEN t.transaction_type = 'capture'       AND t.status = 'succeeded' THEN t.amount_cents END), 0) AS captured_cents,
       COALESCE(SUM(CASE WHEN t.transaction_type = 'void'          AND t.status = 'succeeded' THEN t.amount_cents END), 0) AS voided_cents,
       COALESCE(SUM(CASE WHEN t.transaction_type = 'refund'        AND t.status = 'succeeded' THEN t.amount_cents END), 0) AS refunded_cents,
       COALESCE(SUM(CASE WHEN t.transaction_type = 'chargeback'    AND t.status = 'succeeded' THEN t.amount_cents END), 0) AS chargeback_cents
FROM payments p
LEFT JOIN payment_transactions t ON t.payment_id = p.payment_id
GROUP BY p.payment_id;

CREATE VIEW v_order_financials AS
SELECT o.order_id, o.order_number, o.grand_total_cents, o.payment_status,
       COALESCE(SUM(pb.authorized_cents), 0) AS authorized_cents,
       COALESCE(SUM(pb.captured_cents), 0)   AS captured_cents,
       COALESCE(SUM(pb.refunded_cents), 0)   AS refunded_to_payments_cents,
       COALESCE((SELECT SUM(sct.amount_cents) FROM store_credit_transactions sct
                 JOIN refunds f ON f.refund_id = sct.refund_id
                 WHERE f.order_id = o.order_id AND sct.entry_type = 'issue_refund'), 0) AS refunded_to_store_credit_cents,
       COALESCE(SUM(pb.captured_cents), 0) - COALESCE(SUM(pb.refunded_cents), 0) AS net_collected_cents
FROM orders o
LEFT JOIN v_payment_balances pb ON pb.order_id = o.order_id
GROUP BY o.order_id;

CREATE VIEW v_customer_balances AS
SELECT c.customer_id, c.customer_number,
       COALESCE((SELECT SUM(points) FROM loyalty_point_transactions WHERE customer_id = c.customer_id), 0) AS loyalty_points,
       (SELECT tier FROM loyalty_accounts WHERE customer_id = c.customer_id) AS loyalty_tier,
       (SELECT COUNT(*) FROM loyalty_rewards WHERE customer_id = c.customer_id AND status = 'available') AS available_rewards,
       COALESCE((SELECT SUM(amount_cents) FROM store_credit_transactions WHERE customer_id = c.customer_id), 0) AS store_credit_cents
FROM customers c;
