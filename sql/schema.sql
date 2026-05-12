-- SQL schema for the customers table
-- PLSygnet Marketing Attribution — Database Schema
-- Full documentation: docs/data_model.md
-- Execution order: customers → products → orders → order_items → marketing_spend → marketing_touchpoints
CREATE TABLE customers (
    id                   SERIAL          PRIMARY KEY,
    first_name           VARCHAR(50)     NOT NULL,
    last_name            VARCHAR(50)     NOT NULL,
    date_of_birth        DATE            NOT NULL CHECK (date_of_birth < CURRENT_DATE),
    gender               VARCHAR(10)     NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    city                 VARCHAR(100)    NOT NULL,
    acquisition_channel  VARCHAR(50)     NOT NULL CHECK (acquisition_channel IN (
                                            'google_ads',
                                            'meta_ads',
                                            'tiktok_ads',
                                            'influencer_ig',
                                            'email',
                                            'outdoor'
                                         )),
    acquired_at          DATE            NOT NULL,
    email                VARCHAR(255)    UNIQUE NOT NULL,
    created_at           TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_customers_acquisition_channel ON customers(acquisition_channel);
CREATE INDEX idx_customers_acquired_at ON customers(acquired_at);
CREATE INDEX idx_customers_city ON customers(city);
-- -------------------------------------------------------------------------
-- 2. products
-- -------------------------------------------------------------------------

CREATE TABLE products (
    id                  SERIAL          PRIMARY KEY,
    sku                 VARCHAR(20)     UNIQUE NOT NULL,
    name                VARCHAR(200)    NOT NULL,
    category            VARCHAR(50)     NOT NULL CHECK (category IN (
                                            'signet_rings',
                                            'bracelets',
                                            'necklaces',
                                            'rings',
                                            'watches',
                                            'earrings',
                                            'suit_accessories'
                                        )),
    selling_price_pln   NUMERIC(10, 2)  NOT NULL CHECK (selling_price_pln > 0),
    cost_price_pln      NUMERIC(10, 2)  NOT NULL CHECK (cost_price_pln > 0),
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_category ON products(category);

-- -------------------------------------------------------------------------
-- 3. orders
-- -------------------------------------------------------------------------

CREATE TABLE orders (
    id              SERIAL          PRIMARY KEY,
    customer_id     INT             NOT NULL REFERENCES customers(id),
    order_date      TIMESTAMP       NOT NULL,
    total_amount    NUMERIC(10, 2)  NOT NULL CHECK (total_amount >= 0),
    shipping_cost   NUMERIC(10, 2)  NOT NULL CHECK (shipping_cost >= 0),
    payment_method  VARCHAR(20)     NOT NULL CHECK (payment_method IN (
                                        'card',
                                        'blik',
                                        'transfer',
                                        'cod'
                                    )),
    status          VARCHAR(20)     NOT NULL CHECK (status IN (
                                        'pending',
                                        'paid',
                                        'shipped',
                                        'delivered',
                                        'returned'
                                    )),
    promo_code      VARCHAR(50),
    shipping_city   VARCHAR(100)    NOT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_orders_promo_code ON orders(promo_code) WHERE promo_code IS NOT NULL;

-- -------------------------------------------------------------------------
-- 4. order_items
-- -------------------------------------------------------------------------

CREATE TABLE order_items (
    order_id    INT             NOT NULL REFERENCES orders(id),
    product_id  INT             NOT NULL REFERENCES products(id),
    quantity    INT             NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10, 2)  NOT NULL CHECK (unit_price > 0),
    unit_cost   NUMERIC(10, 2)  NOT NULL CHECK (unit_cost > 0),
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW(),
    PRIMARY KEY (order_id, product_id)
);

CREATE INDEX idx_order_items_product_id ON order_items(product_id);


-- -------------------------------------------------------------------------
-- 5. marketing_spend
-- -------------------------------------------------------------------------

CREATE TABLE marketing_spend (
    id          SERIAL          PRIMARY KEY,
    date        DATE            NOT NULL,
    channel     VARCHAR(50)     NOT NULL CHECK (channel IN (
                                    'google_ads',
                                    'meta_ads',
                                    'tiktok_ads',
                                    'influencer_ig',
                                    'email',
                                    'outdoor'
                                )),
    campaign    VARCHAR(100)    NOT NULL,
    spend_pln   NUMERIC(10, 2)  NOT NULL CHECK (spend_pln >= 0),
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_marketing_spend_date ON marketing_spend(date);
CREATE INDEX idx_marketing_spend_channel ON marketing_spend(channel);
CREATE INDEX idx_marketing_spend_date_channel ON marketing_spend(date, channel);
-- -------------------------------------------------------------------------
-- 6. marketing_touchpoints
-- -------------------------------------------------------------------------

CREATE TABLE marketing_touchpoints (
    id              BIGSERIAL       PRIMARY KEY,
    customer_id     INT             NOT NULL REFERENCES customers(id),
    timestamp       TIMESTAMP       NOT NULL,
    channel         VARCHAR(50)     NOT NULL CHECK (channel IN (
                                        'google_ads',
                                        'meta_ads',
                                        'tiktok_ads',
                                        'influencer_ig',
                                        'email',
                                        'outdoor'
                                    )),
    campaign        VARCHAR(100)    NOT NULL,
    touchpoint_type VARCHAR(50)     NOT NULL CHECK (touchpoint_type IN (
                                        'impression',
                                        'click',
                                        'page_view',
                                        'email_open',
                                        'email_click',
                                        'promo_code_redemption'
                                    )),
    order_id        INT             REFERENCES orders(id),
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_touchpoints_customer_id ON marketing_touchpoints(customer_id);
CREATE INDEX idx_touchpoints_timestamp ON marketing_touchpoints(timestamp);
CREATE INDEX idx_touchpoints_channel ON marketing_touchpoints(channel);
CREATE INDEX idx_touchpoints_customer_timestamp ON marketing_touchpoints(customer_id, timestamp);
CREATE INDEX idx_touchpoints_order_id ON marketing_touchpoints(order_id) WHERE order_id IS NOT NULL;