-- ============================================================================
-- Cross-Border E-Commerce Platform: China → India
-- PostgreSQL Schema
-- ============================================================================
-- Compliant with Indian e-commerce regulations:
--   - Country of Origin (CoO) marking
--   - HSN (HS) Chapter codes
--   - GST slabs (5%, 12%, 18%, 28%)
--   - BIS certification tracking
--   - MRP + 10% margin rule
--   - 6-digit PIN code serviceability
--
-- Landing Cost formula:
--   LandingCost_INR =
--     (Procurement_INR + Freight_INR + PortCharges_INR)        -- CIF base
--     + CIF_base * (BCD_Rate / 100)                            -- Basic Customs Duty
--     + (CIF_base + BCD) * (SWS_Rate / 100)                    -- Social Welfare Surcharge
--     + (CIF_base + BCD + SWS) * (IGST_Rate / 100)             -- Integrated GST
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CURRENCY & EXCHANGE RATE
-- ----------------------------------------------------------------------------
CREATE TABLE currencies (
    code       CHAR(3) PRIMARY KEY,              -- 'INR', 'USD', 'CNY'
    name       TEXT NOT NULL,
    symbol     VARCHAR(8),
    is_active  BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE exchange_rates (
    id            SERIAL PRIMARY KEY,
    from_currency CHAR(3) NOT NULL REFERENCES currencies(code),
    to_currency   CHAR(3) NOT NULL REFERENCES currencies(code),
    rate          NUMERIC(15,6) NOT NULL,                     -- 1 from = rate to
    effective_at  TIMESTAMPTZ DEFAULT now(),
    source        TEXT,                                        -- e.g. 'RBI', 'Manual'
    created_at    TIMESTAMPTZ DEFAULT now(),
    UNIQUE(from_currency, to_currency, effective_at)
);

CREATE INDEX idx_exchange_rates_cur_pair ON exchange_rates(from_currency, to_currency);
CREATE INDEX idx_exchange_rates_eff      ON exchange_rates(effective_at DESC);

-- ----------------------------------------------------------------------------
-- 2. USER / CUSTOMER MANAGEMENT
-- ----------------------------------------------------------------------------
CREATE TYPE user_type AS ENUM ('b2c_customer', 'b2b_customer', 'admin', 'ops');

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_type       user_type NOT NULL,
    email           TEXT UNIQUE,
    phone           TEXT,
    password_hash    TEXT,
    full_name       TEXT,
    company_name    TEXT,                                      -- B2B only
    gst_number      VARCHAR(15),                               -- B2B Indian customer
    billing_addr    JSONB,
    shipping_addr   JSONB,
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_users_email  ON users(email);
CREATE INDEX idx_users_phone  ON users(phone);
CREATE INDEX idx_users_gst    ON users(gst_number);
CREATE INDEX idx_users_type   ON users(user_type);

-- ----------------------------------------------------------------------------
-- 3. SUPPLIERS (CHINA)
-- ----------------------------------------------------------------------------
CREATE TABLE supplier_contacts (
    id           SERIAL PRIMARY KEY,
    supplier_id  UUID NOT NULL,
    name         TEXT NOT NULL,
    designation  TEXT,
    email        TEXT,
    phone        TEXT,
    wechat_id    TEXT,
    is_primary   BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE suppliers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    company_name    TEXT,
    country_code    CHAR(2) DEFAULT 'CN',
    address         JSONB,
    email           TEXT,
    phone           TEXT,
    wechat          TEXT,
    alibaba_id      TEXT,
    payment_terms   TEXT,                                       -- e.g. 'T/T 30% advance'
    lead_time_days  INTEGER,
    is_preferred    BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_suppliers_name    ON suppliers(name);
CREATE INDEX idx_suppliers_pref    ON suppliers(is_preferred);
CREATE INDEX idx_supplier_contacts ON supplier_contacts(supplier_id);

-- ----------------------------------------------------------------------------
-- 4. CATEGORIES & HSN CODES
-- ----------------------------------------------------------------------------
CREATE TABLE categories (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    parent_id   INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    hsn_chapter VARCHAR(2),                                -- e.g. '85' for Electrical
    created_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE(name)
);

CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_hsn    ON categories(hsn_chapter);

-- ----------------------------------------------------------------------------
-- 5. PRODUCTS (with Indian compliance fields)
-- ----------------------------------------------------------------------------
CREATE TYPE product_status AS ENUM (
    'draft', 'pending_approval', 'approved', 'rejected', 'discontinued'
);

CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku             TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    category_id     INTEGER REFERENCES categories(id),
    brand           TEXT,
    country_of_origin CHAR(2) NOT NULL DEFAULT 'CN',      -- mandatory CoO
    hsn_code        VARCHAR(8) NOT NULL,                    -- e.g. '8504.40.90'
    gst_slab        NUMERIC(5,2) NOT NULL,                 -- 5.00, 12.00, 18.00, 28.00
    mrp             NUMERIC(10,2) NOT NULL,                -- Maximum Retail Price (INR)
    bis_cert_required BOOLEAN DEFAULT FALSE,              -- BIS certification flag
    bis_cert_number TEXT,                                 -- BIS certificate number
    bis_cert_valid  DATE,                                 -- BIS certificate expiry
    is_bis_certified BOOLEAN DEFAULT FALSE,
    is_hazardous     BOOLEAN DEFAULT FALSE,
    dimensions_cm   JSONB,                                -- {length, width, height}
    weight_kg       NUMERIC(10,3),
    volume_cbm      NUMERIC(10,3),
    procurement_cost_cny NUMERIC(15,2),                   -- Last known FOB price (CNY)
    procurement_cost_usd NUMERIC(15,2),                   -- Last known FOB price (USD)
    status          product_status DEFAULT 'draft',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_products_sku        ON products(sku);
CREATE INDEX idx_products_category   ON products(category_id);
CREATE INDEX idx_products_coo        ON products(country_of_origin);
CREATE INDEX idx_products_hsn        ON products(hsn_code);
CREATE INDEX idx_products_status     ON products(status);
CREATE INDEX idx_products_bis        ON products(bis_cert_number);
CREATE INDEX idx_products_active     ON products(status) WHERE status = 'approved';

-- Product images (stored as URLs/S3 keys)
CREATE TABLE product_images (
    id         SERIAL PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    image_url  TEXT NOT NULL,
    alt_text   TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_product_images_pid ON product_images(product_id);

-- ----------------------------------------------------------------------------
-- 6. IMPORT SHIPMENTS (CHINA → INDIA TRACKING)
-- ----------------------------------------------------------------------------
CREATE TYPE shipment_status AS ENUM (
    'pending',           -- not yet shipped
    'booked',            -- cargo booked with freight forwarder
    'in_transit',        -- left Chinese port
    'at_destination',    -- arrived at Indian port
    'customs_hold',      -- stuck in customs
    'released',          -- cleared customs
    'delivered',         -- delivered to warehouse
    'cancelled'
);

CREATE TABLE import_shipments (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_number   TEXT UNIQUE NOT NULL,                -- e.g. 'SHP-2024-0001'
    supplier_id       UUID REFERENCES suppliers(id),
    invoice_number    TEXT,                                -- Supplier's Proforma/PI
    invoice_amount_cny NUMERIC(15,2),
    invoice_amount_usd NUMERIC(15,2),
    invoice_currency  CHAR(3) NOT NULL DEFAULT 'USD' CHECK (invoice_currency IN ('USD','CNY')),
    invoice_date      DATE,
    purchase_order_id UUID,                                -- FK to purchase_orders (if exists)
    freight_cost_inr  NUMERIC(12,2),                      -- Freight: China port → India port
    insurance_cost_inr NUMERIC(12,2),                      -- Marine cargo insurance
    port_charges_inr  NUMERIC(12,2),                      -- Terminal, handling, etc.
    bl_awb_number     TEXT,                               -- Bill of Lading / Airway Bill
    vessel_flight     TEXT,                               -- Vessel name / Flight number
    origin_port       TEXT,                               -- e.g. 'Shenzhen', 'Ningbo'
    destination_port  TEXT,                               -- e.g. 'Jawaharlal Nehru', 'Chennai'
    etd               DATE,                               -- Estimated Time of Departure
    eta               DATE,                               -- Estimated Time of Arrival
    ata               DATE,                               -- Actual Time of Arrival
    status            shipment_status DEFAULT 'pending',
    customs_declaration_number TEXT,
    created_at        TIMESTAMPTZ DEFAULT now(),
    updated_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_shipments_supplier  ON import_shipments(supplier_id);
CREATE INDEX idx_shipments_status    ON import_shipments(status);
CREATE INDEX idx_shipments_eta        ON import_shipments(eta);
CREATE INDEX idx_shipments_inv_num   ON import_shipments(invoice_number);
CREATE INDEX idx_shipments_bl        ON import_shipments(bl_awb_number);

CREATE TABLE import_shipment_items (
    id              SERIAL PRIMARY KEY,
    shipment_id     UUID NOT NULL REFERENCES import_shipments(id) ON DELETE CASCADE,
    product_id      UUID NOT NULL REFERENCES products(id),
    quantity        NUMERIC(12,3) NOT NULL,
    unit_price_cny  NUMERIC(10,2),
    unit_price_usd  NUMERIC(10,2),
    line_total_cny  NUMERIC(15,2),
    line_total_usd  NUMERIC(15,2),
    hsn_code        VARCHAR(8),
    country_of_origin CHAR(2),
    UNIQUE(shipment_id, product_id, hsn_code)
);

CREATE INDEX idx_shipment_items_sid ON import_shipment_items(shipment_id);
CREATE INDEX idx_shipment_items_pid ON import_shipment_items(product_id);

-- ----------------------------------------------------------------------------
-- 7. WAREHOUSES & INVENTORY
-- ----------------------------------------------------------------------------
CREATE TABLE warehouses (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    code         VARCHAR(10) UNIQUE,
    address      TEXT,
    city         TEXT,
    state        TEXT,
    pin_code     VARCHAR(6),
    country      CHAR(2) DEFAULT 'IN',
    latitude     NUMERIC(10,8),
    longitude    NUMERIC(11,8),
    capacity_cbm NUMERIC(12,2),
    is_active    BOOLEAN DEFAULT TRUE,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_warehouses_code ON warehouses(code);
CREATE INDEX idx_warehouses_pin  ON warehouses(pin_code);

CREATE TYPE inventory_status AS ENUM (
    'on_hand',          -- physically available in warehouse
    'in_transit',       -- arrived at Indian port, not yet in warehouse
    'at_port',          -- customs cleared, waiting for delivery to warehouse
    'on_hold'           -- held for quality check / customs
);

CREATE TABLE inventory (
    id              SERIAL PRIMARY KEY,
    product_id      UUID NOT NULL REFERENCES products(id),
    warehouse_id    INTEGER REFERENCES warehouses(id),
    status          inventory_status NOT NULL DEFAULT 'on_hand',
    quantity        NUMERIC(12,3) NOT NULL DEFAULT 0,
    reserved_qty    NUMERIC(12,3) DEFAULT 0,                          -- reserved for orders
    last_restocked  TIMESTAMPTZ,
    shipment_item_id INTEGER REFERENCES import_shipment_items(id),   -- link to source shipment
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_inventory_pid     ON inventory(product_id);
CREATE INDEX idx_inventory_wh      ON inventory(warehouse_id);
CREATE INDEX idx_inventory_status  ON inventory(status);
CREATE INDEX idx_inventory_pidwh   ON inventory(product_id, warehouse_id, status);

-- Stock movement journal (immutable audit trail)
CREATE TABLE inventory_movements (
    id              SERIAL PRIMARY KEY,
    product_id      UUID NOT NULL REFERENCES products(id),
    warehouse_id    INTEGER REFERENCES warehouses(id),
    shipment_item_id INTEGER REFERENCES import_shipment_items(id),
    from_status     inventory_status,
    to_status       inventory_status,
    quantity        NUMERIC(12,3) NOT NULL,
    reason          TEXT,               -- 'shipment_received', 'order_picked', etc.
    reference_id    TEXT,               -- order_id, shipment_number, etc.
    created_at      TIMESTAMPTZ DEFAULT now(),
    created_by      UUID REFERENCES users(id)
);

CREATE INDEX idx_inv_movements_pid   ON inventory_movements(product_id);
CREATE INDEX idx_inv_movements_date  ON inventory_movements(created_at);
CREATE INDEX idx_inv_movements_ref   ON inventory_movements(reference_id);

-- ----------------------------------------------------------------------------
-- 8. PIN CODE SERVICEABILITY
-- ----------------------------------------------------------------------------
CREATE TABLE pincode_serviceability (
    id            SERIAL PRIMARY KEY,
    pin_code       VARCHAR(6) NOT NULL,
    state          TEXT,
    district       TEXT,
    city           TEXT,
    postal_division TEXT,
    is_serviceable BOOLEAN DEFAULT TRUE,
    delivery_days  INTEGER,              -- estimated delivery days
    cod_available  BOOLEAN DEFAULT FALSE,
    min_order_value NUMERIC(10,2),
    max_order_value NUMERIC(10,2),
    shipping_charge NUMERIC(10,2),
    warehouse_id   INTEGER REFERENCES warehouses(id),
    updated_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE(pin_code)
);

CREATE INDEX idx_pincode_serviceable ON pincode_serviceability(is_serviceable);
CREATE INDEX idx_pincode_warehouse   ON pincode_serviceability(warehouse_id);

-- ----------------------------------------------------------------------------
-- 9. LANDING COST CALCULATION (stored per product-shipment)
-- ----------------------------------------------------------------------------
-- Formula:
--   CIF_base = Procurement_INR + Freight_INR + PortCharges_INR
--   BCD      = CIF_base * (bcd_rate / 100)
--   SWS      = (CIF_base + BCD) * (sws_rate / 100)
--   IGST     = (CIF_base + BCD + SWS) * (igst_rate / 100)
--   LandingCost_INR = CIF_base + BCD + SWS + IGST
-- ----------------------------------------------------------------------------

CREATE TABLE landing_costs (
    id                  SERIAL PRIMARY KEY,
    product_id          UUID NOT NULL REFERENCES products(id),
    shipment_id         UUID NOT NULL REFERENCES import_shipments(id),
    shipment_item_id    INTEGER REFERENCES import_shipment_items(id),

    -- Raw costs
    procurement_usd     NUMERIC(14,4),
    procurement_cny     NUMERIC(14,4),
    procurement_inr     NUMERIC(14,2),           -- converted to INR
    exchange_rate       NUMERIC(12,4),           -- rate used for conversion
    exchange_rate_date  DATE,

    freight_inr         NUMERIC(12,2),
    port_charges_inr    NUMERIC(12,2),

    -- Calculated components
    cif_base_inr        NUMERIC(14,2),           -- Procurement + Freight + Port
    bcd_rate            NUMERIC(5,3),            -- e.g. 10.0 (10%)
    bcd_amount_inr      NUMERIC(14,2),

    sws_rate            NUMERIC(5,3),            -- e.g. 10.0 (10% on BCD)
    sws_amount_inr      NUMERIC(14,2),

    igst_rate           NUMERIC(5,3),            -- e.g. 18.0 (18%)
    igst_amount_inr     NUMERIC(14,2),

    total_landing_cost_inr NUMERIC(14,2),        -- final landing cost

    calculated_at       TIMESTAMPTZ DEFAULT now(),
    calculated_by       UUID REFERENCES users(id),

    UNIQUE(product_id, shipment_id)
);

CREATE INDEX idx_landing_costs_product  ON landing_costs(product_id);
CREATE INDEX idx_landing_costs_shipment ON landing_costs(shipment_id);
CREATE INDEX idx_landing_costs_calc_date ON landing_costs(calculated_at);

-- ----------------------------------------------------------------------------
-- 10. CUSTOMER ORDERS (B2C / B2B)
-- ----------------------------------------------------------------------------
CREATE TYPE order_status AS ENUM (
    'pending', 'confirmed', 'processing', 'packed', 'shipped',
    'out_for_delivery', 'delivered', 'cancelled', 'returned', 'refunded'
);

CREATE TABLE orders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number    TEXT UNIQUE NOT NULL,           -- e.g. 'ORD-2024-0001234'
    user_id         UUID NOT NULL REFERENCES users(id),
    order_type      TEXT NOT NULL CHECK (order_type IN ('b2c', 'b2b')),
    status          order_status DEFAULT 'pending',
    currency        CHAR(3) NOT NULL DEFAULT 'INR',

    -- Pricing breakdown
    subtotal_inr    NUMERIC(14,2),                  -- sum of item prices
    shipping_inr    NUMERIC(10,2),
    discount_inr    NUMERIC(10,2) DEFAULT 0,
    tax_amount_inr  NUMERIC(10,2),
    round_off_inr   NUMERIC(10,2),
    total_inr       NUMERIC(14,2),                  -- final order total

    -- Address info (snapshot at order time)
    shipping_address JSONB,
    billing_address  JSONB,

    -- Delivery
    pin_code        VARCHAR(6),
    delivery_date   DATE,
    courier_name    TEXT,
    tracking_number TEXT,

    -- Payment
    payment_method  TEXT CHECK (payment_method IN ('cod', 'prepaid', 'rzp', 'card', 'upi', 'net_banking')),
    payment_status  TEXT CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded', 'partially_refunded')) DEFAULT 'pending',

    -- GST & compliance
    place_of_supply TEXT,                           -- e.g. 'Karnataka', or state code for B2B
    gst_state_code   VARCHAR(2),                   -- e.g. '29' for Karnataka (B2B)

    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_orders_user     ON orders(user_id);
CREATE INDEX idx_orders_status   ON orders(status);
CREATE INDEX idx_orders_date     ON orders(created_at);
CREATE INDEX idx_orders_pin      ON orders(pin_code);
CREATE INDEX idx_orders_payment  ON orders(payment_status);

CREATE TABLE order_items (
    id                    SERIAL PRIMARY KEY,
    order_id              UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id            UUID NOT NULL REFERENCES products(id),
    inventory_id          INTEGER REFERENCES inventory(id),
    quantity              INTEGER NOT NULL,
    unit_price_inr        NUMERIC(10,2),               -- selling price (MRP or discounted)
    landing_cost_inr      NUMERIC(10,2),               -- for margin tracking
    discount_per_item_inr NUMERIC(10,2) DEFAULT 0,
    line_total_inr        NUMERIC(14,2),               -- quantity * (unit_price - discount)
    hsn_code              VARCHAR(8) NOT NULL,
    gst_slab              NUMERIC(5,2) NOT NULL,      -- 5/12/18/28
    cgst_amount_inr       NUMERIC(10,2),               -- for B2B intra-state
    sgst_amount_inr       NUMERIC(10,2),               -- for B2B intra-state
    igst_amount_inr       NUMERIC(10,2),               -- for B2B inter-state / B2C
    taxable_amount_inr    NUMERIC(10,2)               -- subtotal before GST
);

CREATE INDEX idx_order_items_oid  ON order_items(order_id);
CREATE INDEX idx_order_items_pid  ON order_items(product_id);
CREATE INDEX idx_order_items_hsn  ON order_items(hsn_code);

-- ----------------------------------------------------------------------------
-- 11. TAX INVOICES (GST COMPLIANCE)
-- ----------------------------------------------------------------------------
CREATE TYPE invoice_type AS ENUM ('b2b', 'b2cl', 'b2cs', 'export');

CREATE TABLE tax_invoices (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number      TEXT UNIQUE NOT NULL,        -- GST invoice number
    invoice_type        invoice_type NOT NULL,
    order_id            UUID NOT NULL REFERENCES orders(id),
    user_id             UUID NOT NULL REFERENCES users(id),
    invoice_date        DATE NOT NULL,
    due_date            DATE,

    -- Customer details (snapshot)
    customer_name       TEXT,
    customer_gstin      VARCHAR(15),                -- B2B only
    customer_state_code VARCHAR(2),
    customer_address    TEXT,

    -- Line item aggregations
    taxable_amount      NUMERIC(14,2),
    cgst_total          NUMERIC(10,2) DEFAULT 0,
    sgst_total          NUMERIC(10,2) DEFAULT 0,
    igst_total          NUMERIC(10,2) DEFAULT 0,
    total_amount        NUMERIC(14,2),

    -- Compliance
    place_of_supply     TEXT,
    hsn_codes_summary   JSONB,                       -- aggregated HSN codes
    bis_cert_references JSONB,                       -- BIS certs referenced on invoice

    -- E-invoice / IRN
    irn                 TEXT,                       -- Invoice Reference Number (e-invoice)
    irn_date            DATE,
    qr_code             TEXT,                       -- QR code data (GST compliant)
    is_cancelled        BOOLEAN DEFAULT FALSE,
    cancelled_at        TIMESTAMPTZ,

    created_at          TIMESTAMPTZ DEFAULT now(),
    created_by          UUID REFERENCES users(id)
);

CREATE INDEX idx_tax_inv_number     ON tax_invoices(invoice_number);
CREATE INDEX idx_tax_inv_date       ON tax_invoices(invoice_date);
CREATE INDEX idx_tax_inv_gstin      ON tax_invoices(customer_gstin);
CREATE INDEX idx_tax_inv_type       ON tax_invoices(invoice_type);
CREATE INDEX idx_tax_inv_irn        ON tax_invoices(irn);
CREATE INDEX idx_tax_inv_order      ON tax_invoices(order_id);

-- ----------------------------------------------------------------------------
-- 12. PAYMENTS
-- ----------------------------------------------------------------------------
CREATE TYPE payment_provider AS ENUM ('razorpay', 'stripe', 'paypal', 'cod', 'bank_transfer', 'card');

CREATE TABLE payments (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id          UUID NOT NULL REFERENCES orders(id),
    user_id           UUID NOT NULL REFERENCES users(id),
    amount_inr        NUMERIC(14,2) NOT NULL,
    provider          payment_provider,
    provider_txn_id   TEXT,
    status            TEXT CHECK (status IN ('pending', 'success', 'failed', 'refunded', 'partially_refunded')),
    payment_method    TEXT,
    paid_at           TIMESTAMPTZ,
    refunded_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_payments_order  ON payments(order_id);
CREATE INDEX idx_payments_user   ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_provider ON payments(provider_txn_id);

-- ----------------------------------------------------------------------------
-- 13. AUDIT LOG
-- ----------------------------------------------------------------------------
CREATE TABLE audit_logs (
    id           SERIAL PRIMARY KEY,
    table_name   TEXT NOT NULL,
    record_id    TEXT,
    action       TEXT NOT NULL,                    -- INSERT, UPDATE, DELETE
    old_values   JSONB,
    new_values   JSONB,
    changed_by   UUID REFERENCES users(id),
    changed_at   TIMESTAMPTZ DEFAULT now(),
    ip_address   INET
);

CREATE INDEX idx_audit_table  ON audit_logs(table_name);
CREATE INDEX idx_audit_date   ON audit_logs(changed_at);
CREATE INDEX idx_audit_user   ON audit_logs(changed_by);
