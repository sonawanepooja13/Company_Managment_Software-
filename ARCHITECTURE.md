# Tech Stack & Architecture Recommendations

## Cross-Border E-Commerce Platform: China → India

---

## 1. Recommended Tech Stack

### Core Application
| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend (Storefront)** | Next.js 15 (App Router) + React 19 | SSR/SSG for SEO-critical product pages; great DX; built-in API routes for simple endpoints |
| **Frontend (Admin/Ops)** | Next.js (App Router) + Tailwind CSS + shadcn/ui | Modern component library; rapid dev for ops dashboard |
| **Backend API** | Next.js API Routes (Node.js 22) OR Go (Fiber/Gin) microservices | Node.js for shared code with frontend; Go for high-throughput order/inventory services |
| **Database** | PostgreSQL 17 | ACID compliance; JSONB for flexible address/attribute storage; GIS for pin-code mapping |
| **Cache** | Redis 7 | Session store; inventory cache; rate-limited exchange-rate cache; Celery-style job queues |
| **ORM** | Prisma ORM (schema.prisma) | Type-safe DB access; migration management; auto-generated TypeScript types |
| **File Storage** | AWS S3 / MinIO (self-hosted) | Product images; BIS certificates; POD scans; exported invoices |
| **Search** | MeiliSearch or Typesense | Fast product search; typo-tolerant; faceted filtering by HSN/category |
| **Task Queue** | BullMQ (Node) / Resque (Go) | Async: landing-cost recalculations, GST invoice generation, email/SMS dispatch |
| **Message Broker** | RabbitMQ or Apache Kafka (if high-scale) | Shipment status events; inventory sync between services |

### Infrastructure
| Component | Recommendation |
|-----------|----------------|
| **Hosting** | AWS / GCP / Azure (India regions: ap-south-1 / asia-south1 / centralindia) |
| **CDN** | CloudFront / Cloudflare (for static assets & images) |
| **Container Orchestration** | Kubernetes (EKS/GKE/AKS) or ECS/Fargate |
| **CI/CD** | GitHub Actions (build, test, deploy to staging/prod) |
| **Monitoring** | Prometheus + Grafana; Sentry for error tracking |
| **Logging** | Loki + Grafana or Datadog |

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CDN / CloudFront                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────────────┐                       │
│  │  Storefront  │    │  Admin / Ops Panel   │                       │
│  │  (Next.js)   │    │  (Next.js + Tailwind)│                       │
│  └──────────────┘    └──────────────────────┘                       │
│          │                      │                                    │
│          ▼                      ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │               API Gateway (NGINX / Traefik)                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │
│  │  Product &   │ │  Order &     │ │  Inventory   │ │  Finance &  │ │
│  │  Catalog     │ │  Checkout    │ │  & Logistics │ │  Tax        │ │
│  │  (Go)        │ │  (Node.js)   │ │  (Go)        │ │  (Go)      │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └─────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │   Redis      │ │  PostgreSQL  │ │   RabbitMQ   │                │
│  │  (Cache)     │ │   (Primary)  │ │  (Messaging) │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

### Service Boundaries

1. **Product Catalog Service** — CRUD for products, categories, suppliers.
   - Maintains compliance fields (CoO, HSN, GST slab, BIS cert).
   - Reads exchange rates for currency conversion display.

2. **Import / Logistics Service** — Manages `ImportShipment` lifecycle.
   - Tracks goods through: booked → in_transit → at_destination → customs_hold → released → delivered.
   - Triggers landing-cost recalculation on shipment status → released.
   - Integrates with shipping APIs (DHL, FedEx, Maersk, etc.) via webhook.

3. **Inventory Service** — Tracks stock levels across warehouses.
   - Two stock types: `on_hand` (in warehouse) and `in_transit` (in shipment).
   - Publishes `inventory.updated` events for the checkout service.
   - Pin-code → warehouse mapping for fulfillment.

4. **Order Service** — Handles order placement, checkout, payment.
   - Validates pin-code serviceability before order creation.
   - Reserves inventory (optimistic locking with Redis).
   - Emits `order.created` → triggers invoice generation.

5. **Finance / Tax Service** — Landing cost, GST invoices, e-invoicing.
   - Calls `calculate_landing_cost()` on shipment clearance.
   - Generates `tax_invoices` compliant with GST rules.
   - Pushes invoices to GSTN e-way bill / e-invoice APIs.

6. **Notification Service** — Email (SendGrid), SMS (Twilio/BulkSMS), WhatsApp (Meta API).

7. **Auth Service** — JWT-based; SSO; role-based access control (RBAC)
   - Roles: `customer`, `b2b_customer`, `ops_user`, `admin`

---

## 3. Key Compliance Features

### Indian E-Commerce Compliance
| Requirement | Implementation |
|------------|-----------------|
| **Country of Origin** | `country_of_origin` column on `products` table; displayed on PLP/PDP and invoice |
| **HSN Codes** | `hsn_code` on `products` and `order_items`; aggregated in `tax_invoices.hsn_codes_summary` |
| **GST Slabs** | `gst_slab` on `products` (5/12/18/28%); applied at checkout based on HSN chapter |
| **BIS Certification** | `bis_cert_required`, `bis_cert_number`, `bis_cert_valid` on `products`; validated before listing |
| **MRP + 10% Rule** | `mrp` stored on product; `unit_price_inr` on order_items cannot exceed MRP × 1.10 |
| **6-digit PIN Codes** | `pincode_serviceability` table; validated at checkout; maps to nearest warehouse |

### Landing Cost Compliance
- All import costs (procurement, freight, port charges, BCD, SWS, IGST) are
  stored in `landing_costs` table with full audit trail.
- Rate tables for BCD, SWS, and GST are maintained as configuration (editable
  by compliance team).
- Exchange rates are fetched daily from RBI API and cached in Redis.

---

## 4. Data Flow: Procurement → Sale

```
1. Supplier Invoice (CNY/USD) → import_shipments table
2. Shipment tracking updates → import_shipments.status
3. On status='released':
   → calculate_landing_cost() → landing_costs table
   → Update product.procurement_cost_cny/usd
4. Inventory arrives at warehouse:
   → inventory.status = 'on_hand'
   → inventory_movements journal updated
5. Customer places order:
   → orders table created
   → order_items reference products + inventory
   → Inventory reserved (reserved_qty incremented)
6. On order fulfillment:
   → Generate tax_invoices (B2B/B2CL/B2CS compliant)
   → Push to GSTN for e-invoice IRN (if B2B)
   → Publish delivery tracking via courier API
7. On delivery:
   → Inventory quantity decremented
   → Financial entries created in accounts
```

---

## 5. API Endpoints (suggested)

### Public Storefront
```
GET    /api/products              # List products (with filters)
GET    /api/products/:sku         # Product detail
GET    /api/categories            # Category tree
GET    /api/pincode/:code         # Check serviceability
GET    /api/exchange-rates        # Latest USD/CNY → INR rates
```

### Authenticated (Customer)
```
POST   /api/orders                # Place order (B2C or B2B)
GET    /api/orders/:number        # Order status
GET    /api/tracking/:awb         # Shipment tracking
```

### Ops / Admin
```
POST   /api/shipments             # Create import shipment
PUT    /api/shipments/:id/status  # Update shipment status
POST   /api/landing-costs         # Calculate / recalculate landing cost
POST   /api/inventory/receive     # Mark shipment as received
POST   /api/tax-invoices          # Generate GST invoice
GET    /api/reports/gst          # GST compliance report
GET    /api/reports/profit       # Margin analysis (selling price vs landing cost)
```

---

## 6. Scalability Considerations

### Read Scaling
- **Product Catalog**: Cache in Redis (1h TTL). Invalidate on product update.
- **Pin-code lookups**: Fully cached in Redis (rarely changes).
- **Exchange rates**: Cached in Redis (daily RBI fetch, manual override).

### Write Scaling
- **Orders**: Insert into PostgreSQL with connection pooling (pgBouncer).
- **Inventory reservations**: Use Redis atomic decrements with Lua scripts.
- **Landing cost**: Computed asynchronously in background jobs; stored in Postgres.

### Partitioning
- `orders` table: Partition by `created_at` (monthly).
- `inventory_movements` table: Partition by `created_at` (monthly).
- `audit_logs` table: Partition by `changed_at` (monthly), purged after 6 months.

### Caching Strategy
```
Redis keys:
- product:{sku}           → product JSON (TTL: 3600s)
- pincode:{code}          → serviceability JSON (TTL: 86400s)
- exchange_rate:USD:INR   → rate (TTL: 86400s)
- exchange_rate:CNY:INR   → rate (TTL: 86400s)
- inventory:{sku}:{warehouseId} → on_hand qty (TTL: 300s)
- bcd_rates               → rate table JSON (TTL: 604800s)
```

---

## 7. Deployment Checklist

| Task | Status |
|------|--------|
| PostgreSQL 17 provisioned | ☐ |
| Redis 7 provisioned | ☐ |
| S3-compatible bucket for file storage | ☐ |
| RabbitMQ / message broker | ☐ |
| RabbitMQ / message broker | ☐ |
| Payment gateway accounts (Razorpay / Stripe India) | ☐ |
| GSTN API credentials (for e-invoicing) | ☐ |
| Courier API credentials (Delhivery, Ecom Express, DTDC) | ☐ |
| RBI exchange rate API integration | ☐ |
| SSL certificate (ACM / Let's Encrypt) | ☐ |
| Domain + CDN (CloudFront) | ☐ |
| CI/CD pipeline configured | ☐ |
| Monitoring + alerting (Prometheus + Grafana + Sentry) | ☐ |
