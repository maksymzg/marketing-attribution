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