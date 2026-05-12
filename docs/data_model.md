# Data Model — PLSygnet Marketing Attribution

This document describes the database schema for the marketing attribution analysis. It serves as the canonical reference for all 6 tables, their columns, constraints, and relationships.

> **Workflow:** This document is human-readable documentation. The executable SQL `CREATE TABLE` statements live in `sql/schema.sql` (created in Phase 1b).

## Tables overview

| Table | Purpose | Row granularity |
|---|---|---|
| `customers` | Customer master data | 1 row per customer |
| `products` | Product catalog | 1 row per SKU |
| `orders` | Order header | 1 row per order |
| `order_items` | Order line items | 1 row per product per order |
| `marketing_spend` | Marketing budget tracking | 1 row per channel per day |
| `marketing_touchpoints` | Customer interaction events | 1 row per touchpoint |

## Relationships (high-level)

```
customers (1) ──< (N) orders (1) ──< (N) order_items (N) >── (1) products
customers (1) ──< (N) marketing_touchpoints (N) >── (1) marketing_spend
```

---

## Table: `customers`

**Purpose:** Stores master data about PLSygnet customers — who they are, where they came from, when they were acquired.

**Analytical questions served:**

- **Q1.2** — promo code redemption (link promo code to customer)
- **Q2.2** — influencer engagement → conversion (link customer to influencer via acquisition_channel)
- **Q3.1** — LTV, AOV, gross profit per channel (segment customers by acquisition_channel)
- **Q3.2** — basket composition, repeat-purchase rate per channel
- **Q4.2** — demographic overlap with YouTube audience

**Columns:**

| Column | Type | Constraint | Why |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique customer identifier |
| `first_name` | `VARCHAR(50)` | `NOT NULL` | First name — for data realism |
| `last_name` | `VARCHAR(50)` | `NOT NULL` | Last name — for data realism |
| `date_of_birth` | `DATE` | `NOT NULL`, `CHECK (date_of_birth < CURRENT_DATE)` | Birth date (age calculated dynamically) |
| `gender` | `VARCHAR(10)` | `NOT NULL`, `CHECK (gender IN ('male', 'female', 'other'))` | Gender — target is men, but women buy as gifts |
| `city` | `VARCHAR(100)` | `NOT NULL` | City (for Q1.1 lift study: Warsaw vs other cities) |
| `acquisition_channel` | `VARCHAR(50)` | `NOT NULL`, `CHECK (acquisition_channel IN ('google_ads', 'meta_ads', 'tiktok_ads', 'influencer_ig', 'email', 'outdoor'))` | Channel through which customer was acquired — **key column** for entire analysis |
| `acquired_at` | `DATE` | `NOT NULL` | First contact / registration date |
| `email` | `VARCHAR(255)` | `UNIQUE`, `NOT NULL` | Customer email — unique per customer |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Audit log — when row was added to database |

**Sample row:**

```
id: 42
first_name: Jacek
last_name: Kot
date_of_birth: 1999-03-15
gender: male
city: Gdańsk
acquisition_channel: tiktok_ads
acquired_at: 2021-05-21
email: jacek.kot.42@example.com
created_at: 2021-05-21 14:32:11
```

**Design decisions:**

- **`date_of_birth` instead of `age`** — age changes over time, birth date doesn't. Age is computed dynamically: `EXTRACT(YEAR FROM AGE(date_of_birth))`.
- **`acquired_at` vs `created_at`** — `acquired_at` is a **business date** (when customer entered the funnel, may be historical), `created_at` is a **technical timestamp** (when row was inserted to DB, always `NOW()`).
- **`acquisition_channel` as VARCHAR with CHECK** — not a separate `channels` table, because the 6 values are fixed and won't change. CHECK constraint prevents typos like 'yotube'.
- **`email` UNIQUE** — enforces 1 customer = 1 email at database level.

---
## Table: `orders`

**Purpose:** Stores order headers — one row per order placed by a customer. Line items (specific products purchased) are stored separately in `order_items`.

**Analytical questions served:**

- **Q1.2** — promo code redemption (filtering by `promo_code`)
- **Q2.1** — influencer ROAS (join `customer_id` → channel attribution)
- **Q3.1** — AOV, gross profit per channel (revenue per order × channel join)
- **Q3.2** — repeat-purchase rate within 6 months (time-based aggregation per customer)
- **Q4.2** — demographic overlap (join with customers for YouTube target audience analysis)

**Columns:**

| Column | Type | Constraint | Why |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique order identifier |
| `customer_id` | `INT` | `NOT NULL REFERENCES customers(id)` | FK to the customer who placed the order |
| `order_date` | `TIMESTAMP` | `NOT NULL` | When the order was placed (date + time, used for time-series analyses) |
| `total_amount` | `NUMERIC(10, 2)` | `NOT NULL`, `CHECK (total_amount >= 0)` | Materialized total revenue of the order (sum of line items + shipping − discounts) |
| `shipping_cost` | `NUMERIC(10, 2)` | `NOT NULL`, `CHECK (shipping_cost >= 0)` | Operational cost — impacts net profitability calculations |
| `payment_method` | `VARCHAR(20)` | `NOT NULL`, `CHECK (payment_method IN ('card', 'blik', 'transfer', 'cod'))` | Tracks payment preference |
| `status` | `VARCHAR(20)` | `NOT NULL`, `CHECK (status IN ('pending', 'paid', 'shipped', 'delivered', 'returned'))` | Order lifecycle — filter out unpaid/returned from revenue |
| `promo_code` | `VARCHAR(50)` | `NULL` (nullable) | Captures attribution codes (e.g., `'WAW20'` for billboard); NULL if no code used |
| `shipping_city` | `VARCHAR(100)` | `NOT NULL` | Snapshotted delivery city — preserves historical accuracy if customer moves |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Audit log — when row was inserted into the database |

**Indexes (in addition to PK):**

| Index | Column(s) | Why |
|---|---|---|
| `idx_orders_customer_id` | `customer_id` | FK joins with `customers` — PostgreSQL does NOT index FKs automatically |
| `idx_orders_order_date` | `order_date` | Time-based filtering in nearly every analytical query |
| `idx_orders_promo_code` | `promo_code` WHERE `promo_code IS NOT NULL` | **Partial index** — speeds up Q1.2 promo redemption queries without indexing 90% of NULLs |

**Sample row:**

```
id: 1024
customer_id: 42
order_date: 2024-03-15 14:30:00
total_amount: 489.99
shipping_cost: 15.00
payment_method: blik
status: delivered
promo_code: WAW20
shipping_city: Warszawa
created_at: 2026-05-11 23:55:00
```

**Design decisions:**

- **Materialized `total_amount`** — stored as a column rather than computed from `order_items` on the fly. Trade-off: small data duplication risk in exchange for significantly faster analytical reads (ROAS, AOV calculations run dozens of times per dashboard refresh).
- **`shipping_city` snapshotted** — copied into `orders` rather than referencing `customers.city`. Preserves historical accuracy: if a customer moves from Gdańsk to Warszawa, past orders correctly report shipping to Gdańsk.
- **`status` as VARCHAR + CHECK** — not a separate `order_statuses` table. The 5 values are stable, no translations needed; separate table would force unnecessary JOINs in 90% of queries.
- **`promo_code` as VARCHAR (nullable)** — not a FK to a `promo_codes` table. Scope-appropriate: we don't manage discount rules (validity dates, percentage vs. nominal), only attribute orders to campaigns.
- **Partial index on `promo_code`** — `CREATE INDEX ... WHERE promo_code IS NOT NULL`. Most orders have no promo code; indexing only the meaningful subset.

---
## Table: `products`

**Purpose:** Product catalog — one row per SKU. Dimensional table (small, stable).

**Analytical questions served:**

- **Q3.1** — gross profit per channel (cost and price reference)
- **Q3.2** — basket composition (% of revenue by product category)

**Columns:**

| Column | Type | Constraint | Why |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique product identifier |
| `sku` | `VARCHAR(20)` | `UNIQUE NOT NULL` | Business-readable identifier (e.g., `'SIG-001'`) |
| `name` | `VARCHAR(200)` | `NOT NULL` | Product name (e.g., `'Sygnet srebrny klasyczny'`) |
| `category` | `VARCHAR(50)` | `NOT NULL`, `CHECK (category IN ('signet_rings', 'bracelets', 'necklaces', 'rings', 'watches', 'earrings', 'suit_accessories'))` | One of 7 categories |
| `selling_price_pln` | `NUMERIC(10, 2)` | `NOT NULL`, `CHECK (selling_price_pln > 0)` | Current catalog price (for reference; historical price snapshotted in `order_items.unit_price`) |
| `cost_price_pln` | `NUMERIC(10, 2)` | `NOT NULL`, `CHECK (cost_price_pln > 0)` | Current cost (for reference; historical cost snapshotted in `order_items.unit_cost`) |
| `is_active` | `BOOLEAN` | `NOT NULL DEFAULT TRUE` | TRUE = currently sold; FALSE = discontinued (kept for FK integrity with historical `order_items`) |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Audit log |

**Indexes (in addition to PK):**

| Index | Column(s) | Why |
|---|---|---|
| `idx_products_category` | `category` | Frequent grouping by category in Q3.2 basket composition |

**Sample row:**

```
id: 5
sku: SIG-001
name: Sygnet srebrny klasyczny męski
category: signet_rings
selling_price_pln: 289.00
cost_price_pln: 95.00
is_active: TRUE
created_at: 2024-01-15 10:30:00
```

**Design decisions:**

- **`sku` separate from `id`** — `id` is technical (DB internal), `sku` is business-readable for reports and conversations ("SIG-001 sold 12 times" vs "product 1234 sold 12 times").
- **`category` as VARCHAR + CHECK** — not a separate `categories` table. 7 values are fixed; separate table would force JOINs in every analysis without benefit.
- **`selling_price_pln` and `cost_price_pln` are catalog references only** — historical prices/costs are snapshotted in `order_items.unit_price` and `order_items.unit_cost`. Margin calculations use `order_items`, never `products`.
- **`is_active` flag instead of DELETE** — discontinued products stay in `products` to preserve FK integrity with historical `order_items`. Soft delete pattern.

---
## Table: `order_items`

**Purpose:** Order line items — one row per product per order. Splits the "what was purchased" from the order header (`orders`).

**Granularity:** 1 row = 1 product within 1 order.

**Analytical questions served:**

- **Q3.1** — gross profit per channel (margin = unit_price − unit_cost, summed per order, joined to channel via customers)
- **Q3.2** — basket composition (which products appear in which customers' baskets, % revenue per category)

**Columns:**

| Column | Type | Constraint | Why |
|---|---|---|---|
| `order_id` | `INT` | `NOT NULL REFERENCES orders(id)` | FK to parent order |
| `product_id` | `INT` | `NOT NULL REFERENCES products(id)` | FK to product |
| `quantity` | `INT` | `NOT NULL`, `CHECK (quantity > 0)` | How many units of this product in the order |
| `unit_price` | `NUMERIC(10, 2)` | `NOT NULL`, `CHECK (unit_price > 0)` | **Snapshotted** selling price at time of order — preserves historical accuracy if catalog price changes |
| `unit_cost` | `NUMERIC(10, 2)` | `NOT NULL`, `CHECK (unit_cost > 0)` | **Snapshotted** cost at time of order — used for gross profit calculations |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Audit log |

**Primary key:** `PRIMARY KEY (order_id, product_id)` — composite key. A given product appears at most once per order (with `quantity >= 1`).

**Indexes:**

| Index | Column(s) | Why |
|---|---|---|
| (PK auto-index) | `(order_id, product_id)` | PostgreSQL creates this automatically for the composite PK |
| `idx_order_items_product_id` | `product_id` | FK to products — needed for category-based queries (Q3.2 basket composition) |

**Sample rows (one order with 2 different products):**

```
order_id | product_id | quantity | unit_price | unit_cost | created_at
1024     | 5          | 1        | 289.00     | 95.00     | 2024-03-15 14:30:01
1024     | 12         | 2        | 145.00     | 52.00     | 2024-03-15 14:30:01
```

Order #1024 contains: 1× SKU 5 (sygnet) at PLN 289 each + 2× SKU 12 (bransoletka) at PLN 145 each. Total line value: 289 + (2 × 145) = PLN 579 (consistent with `orders.total_amount` minus shipping).

**Design decisions:**

- **Composite PK `(order_id, product_id)`** — natural key reflecting business rule: a product appears at most once per order (multiple units handled via `quantity`). No need for surrogate `id`.
- **Snapshotted `unit_price` and `unit_cost`** — same pattern as `orders.shipping_city`. Catalog prices in `products` can change over time; historical orders must preserve the price actually charged. Margin calculations always use these columns, never `products.selling_price_pln`.
- **No `discount_pln` or `discount_pct` column** — scope-appropriate. Analytical questions Q1–Q4 do not require discount-level analysis. Any discount logic is implicit in the snapshotted `unit_price` (i.e., `unit_price` is the actual price paid, post-discount).
- **Index on `product_id`** — PostgreSQL indexes the composite PK starting with `order_id`, which is efficient for `WHERE order_id = X` queries. But for `WHERE product_id = X` (Q3.2 — "which orders contain this product?"), we need a separate index on `product_id`.

---
## Table: `marketing_spend`

**Purpose:** Daily marketing expenditure per channel and campaign. Time-series table tracking how much PLSygnet spent, where, and on which campaign — across all 6 channels. Used as the denominator in every ROAS calculation.

**Granularity:** 1 row = 1 day × 1 channel × 1 campaign.

**Analytical questions served:**

- **Q1.2** — outdoor revenue attribution (revenue from promo code / outdoor spend)
- **Q2.1** — influencer ROAS (revenue per influencer / spend per influencer)
- **Q3.1** — channel-level ROAS calculations
- **Q4.1** — historical ROAS of paid video channels (TikTok, Meta video) as benchmark for YouTube

**Columns:**

| Column | Type | Constraint | Why |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique row identifier |
| `date` | `DATE` | `NOT NULL` | The day this spend is attributed to (daily granularity) |
| `channel` | `VARCHAR(50)` | `NOT NULL`, `CHECK (channel IN ('google_ads', 'meta_ads', 'tiktok_ads', 'influencer_ig', 'email', 'outdoor'))` | One of 6 marketing channels |
| `campaign` | `VARCHAR(100)` | `NOT NULL` | Campaign name within the channel (e.g., `'spring_sale_2024'`, `'macro_jan_kowal'`) |
| `spend_pln` | `NUMERIC(10, 2)` | `NOT NULL`, `CHECK (spend_pln >= 0)` | Amount spent on this campaign on this day (accrual basis) |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Audit log |

**Indexes (in addition to PK):**

| Index | Column(s) | Why |
|---|---|---|
| `idx_marketing_spend_date` | `date` | Frequent time-range filtering (e.g., "spend in Q1 2024") |
| `idx_marketing_spend_channel` | `channel` | Frequent channel-level aggregations (ROAS per channel) |
| `idx_marketing_spend_date_channel` | `(date, channel)` | Composite index for queries combining time range + channel (most common pattern) |

**Sample rows:**

```
id    | date       | channel       | campaign            | spend_pln | created_at
1001  | 2024-03-15 | google_ads    | spring_sale_2024    | 450.00    | 2026-05-12 ...
1002  | 2024-03-15 | meta_ads      | brand_awareness     | 320.00    | 2026-05-12 ...
1003  | 2024-03-15 | tiktok_ads    | gen_z_targeting     | 180.00    | 2026-05-12 ...
1004  | 2024-03-15 | influencer_ig | macro_jan_kowal     | 109.59    | 2026-05-12 ...
1005  | 2024-03-15 | outdoor       | warsaw_billboard    | 657.53    | 2026-05-12 ...
1006  | 2024-03-15 | email         | newsletter_q1       | 25.00     | 2026-05-12 ...
```

**Design decisions:**

- **Accrual basis for annual contracts** — outdoor (PLN 240,000 / 365 = PLN 657.53/day) and macro-influencer (PLN 40,000 / 365 = PLN 109.59/day) are spread evenly across the contract period. This is the **industry standard for marketing analytics**, not cash accounting. Reason: ROAS measures "value generated per złoty invested" — and billboard generated value for 365 days, not just on the payment day. Cash-basis accounting (lump-sum entry on payment day) is left to the finance/accounting team.
- **Campaign granularity, not just channel** — allows drill-down into "which Google Ads campaign performed best" (Q2.1, Q3.1). Adds complexity (~20-30k rows vs ~11k for channel-only) but pays off in analytical depth.
- **No `impressions`, `clicks`, or `conversions` columns** — these are **behavioral metrics** belonging to `marketing_touchpoints` table. Separation of concerns: `marketing_spend` answers "how much did we pay", `marketing_touchpoints` answers "what did customers do".
- **No FK to a `campaigns` table** — `campaign` is a VARCHAR. A separate `campaigns` table would be more normalized but adds complexity without analytical value. Out of scope.
- **Composite index `(date, channel)`** — anticipates the most common query pattern: `WHERE date BETWEEN ... AND channel = 'google_ads'`. PostgreSQL uses this composite efficiently for both columns when in this order.

---
## Table: `marketing_touchpoints`

**Purpose:** Captures every customer interaction with PLSygnet's marketing — clicks, impressions, page views, email opens, promo code redemptions. This is the **core attribution table**: it enables comparing different attribution models (first-touch, last-touch, linear) by reconstructing the full customer journey across all 6 channels.

**Granularity:** 1 row = 1 interaction by 1 customer with 1 channel at 1 moment in time.

**Analytical questions served:**

- **Q1.2** — promo code redemption (filter `touchpoint_type = 'promo_code_redemption'`, link to orders via `order_id`)
- **Q2.1** — influencer ROAS (engagement → conversion linked through customer journey)
- **Q2.2** — engagement rate per influencer (count of impressions vs. clicks vs. conversions)
- **Q3.1, Q3.2** — channel attribution (which channels touched the customer before purchase — input for first/last/linear attribution models)
- **Q4.1** — TikTok and Meta video benchmark (touchpoint volume and conversion rate per channel)

**Columns:**

| Column | Type | Constraint | Why |
|---|---|---|---|
| `id` | `BIGSERIAL` | `PRIMARY KEY` | Unique touchpoint identifier (BIGSERIAL because this table grows large — ~500k+ rows expected) |
| `customer_id` | `INT` | `NOT NULL REFERENCES customers(id)` | FK to customer (no anonymous touchpoints in this scope) |
| `timestamp` | `TIMESTAMP` | `NOT NULL` | Exact moment of interaction (date + time) — critical for customer journey ordering |
| `channel` | `VARCHAR(50)` | `NOT NULL`, `CHECK (channel IN ('google_ads', 'meta_ads', 'tiktok_ads', 'influencer_ig', 'email', 'outdoor'))` | One of 6 marketing channels |
| `campaign` | `VARCHAR(100)` | `NOT NULL` | Campaign within the channel (must match a value in `marketing_spend.campaign`) |
| `touchpoint_type` | `VARCHAR(50)` | `NOT NULL`, `CHECK (touchpoint_type IN ('impression', 'click', 'page_view', 'email_open', 'email_click', 'promo_code_redemption'))` | Type of interaction |
| `order_id` | `INT` | `NULL REFERENCES orders(id)` | Linked order if this touchpoint resulted in a purchase (e.g., promo_code_redemption); NULL otherwise |
| `created_at` | `TIMESTAMP` | `NOT NULL DEFAULT NOW()` | Audit log |

**Indexes (in addition to PK):**

| Index | Column(s) | Why |
|---|---|---|
| `idx_touchpoints_customer_id` | `customer_id` | Customer journey reconstruction (group by customer, order by timestamp) |
| `idx_touchpoints_timestamp` | `timestamp` | Time-based filtering and window functions |
| `idx_touchpoints_channel` | `channel` | Channel-level aggregations |
| `idx_touchpoints_customer_timestamp` | `(customer_id, timestamp)` | Composite — accelerates the most common attribution query pattern |
| `idx_touchpoints_order_id` | `order_id` WHERE `order_id IS NOT NULL` | Partial index — links touchpoints to converted orders |

**Sample rows (one customer journey):**

```
id      | customer_id | timestamp           | channel       | campaign            | touchpoint_type        | order_id
50001   | 42          | 2024-03-01 18:23:11 | meta_ads      | brand_awareness     | impression             | NULL
50002   | 42          | 2024-03-01 18:23:14 | meta_ads      | brand_awareness     | click                  | NULL
50003   | 42          | 2024-03-01 18:23:18 | meta_ads      | brand_awareness     | page_view              | NULL
50004   | 42          | 2024-03-05 09:12:00 | email         | newsletter_q1       | email_open             | NULL
50005   | 42          | 2024-03-05 09:12:35 | email         | newsletter_q1       | email_click            | NULL
50006   | 42          | 2024-03-08 14:28:51 | google_ads    | brand_search        | click                  | NULL
50007   | 42          | 2024-03-08 14:30:00 | google_ads    | brand_search        | page_view              | NULL
50008   | 42          | 2024-03-08 14:42:18 | outdoor       | warsaw_billboard    | promo_code_redemption  | 1024
```

Marek's journey: Meta brand awareness ad → 4 days later email → 3 days later Google search click → page view → conversion using billboard promo code (WAW20). **6 touchpoints, 4 channels involved before purchase.** This is the data that powers attribution model comparison.

**Design decisions:**

- **`BIGSERIAL` instead of `SERIAL` for `id`** — touchpoints table grows large (50-200× more rows than orders). `SERIAL` (INT) maxes at ~2.1 billion; `BIGSERIAL` (BIGINT) goes to ~9 quintillion. Future-proofing.
- **`customer_id` NOT NULL** — no anonymous touchpoints. Scope decision: tracking anonymous browsing (via session_id) adds complexity without analytical value for our 8 questions.
- **`order_id` nullable** — most touchpoints don't convert directly. Only `promo_code_redemption` and certain conversion-type touchpoints have an `order_id`. NULL is the default state.
- **No `first_touch` / `last_touch` flag columns** — these are **derived** via SQL window functions (`ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY timestamp)`), not stored. Storing them would violate the principle of separating raw data from analytical derivatives.
- **Composite index `(customer_id, timestamp)`** — the most common query is "give me all touchpoints for customer X, ordered by time" (customer journey reconstruction). This composite serves it efficiently.
- **Partial index on `order_id`** — most rows have `NULL`; indexing only non-NULL values speeds up conversion attribution queries without bloating the index.
- **`campaign` as VARCHAR, not FK to `marketing_spend.campaign`** — VARCHAR is simpler. Cross-table consistency relies on data generation logic ensuring the same campaign names appear in both tables.

---