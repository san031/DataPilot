-- schema.sql — DataPilot e-commerce database (mirrors the ER diagram)
--  CREATE TABLE statements for all 10 tables i.e, categories,products,warehouses,inventory,customers,orders,order_items,payments,returns.
-- Tables are listed in foreign-key order: a table only references tables above it.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- Products (B)
CREATE TABLE categories (
    category_id     INTEGER PRIMARY KEY,
    category_name   TEXT NOT NULL UNIQUE,
    category_type   TEXT NOT NULL
);

CREATE TABLE products (
    product_id      INTEGER PRIMARY KEY,
    category_id     INTEGER NOT NULL REFERENCES categories(category_id),
    product_name    TEXT NOT NULL,
    price           DECIMAL(10,2) NOT NULL CHECK (price > 0),
    cost_price      DECIMAL(10,2) NOT NULL CHECK (cost_price > 0)
);

-- ---------------------------------------------------------------- Inventory (V)
CREATE TABLE warehouses (
    warehouse_id    INTEGER PRIMARY KEY,
    warehouse_name  TEXT NOT NULL,
    city            TEXT NOT NULL
);

CREATE TABLE inventory (
    inventory_id    INTEGER PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    warehouse_id    INTEGER NOT NULL REFERENCES warehouses(warehouse_id),
    stock_quantity  INTEGER NOT NULL CHECK (stock_quantity >= 0),
    reorder_level   INTEGER NOT NULL CHECK (reorder_level >= 0),
    UNIQUE (product_id, warehouse_id)
);

-- ---------------------------------------------------------------- Customers (A)
CREATE TABLE customers (
    customer_id       INTEGER PRIMARY KEY,
    name              TEXT NOT NULL,
    email             TEXT NOT NULL UNIQUE,
    city              TEXT NOT NULL,
    registration_date DATE NOT NULL
);

-- ---------------------------------------------------------------- Orders & Payments (P)
CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date    DATE NOT NULL,
    order_status  TEXT NOT NULL
        CHECK (order_status IN ('pending','processing','shipped','delivered','cancelled'))
);

CREATE TABLE order_items (
    item_id     INTEGER PRIMARY KEY,
    order_id    INTEGER NOT NULL REFERENCES orders(order_id),
    product_id  INTEGER NOT NULL REFERENCES products(product_id),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  DECIMAL(10,2) NOT NULL CHECK (unit_price > 0)
);

CREATE TABLE payments (
    payment_id      INTEGER PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    payment_method  TEXT NOT NULL,
    payment_status  TEXT NOT NULL
        CHECK (payment_status IN ('completed','pending','failed','refunded')),
    amount          DECIMAL(10,2) NOT NULL CHECK (amount >= 0)
);

-- ---------------------------------------------------------------- Shipments & Returns (E)
CREATE TABLE shipments (
    shipment_id      INTEGER PRIMARY KEY,
    order_id         INTEGER NOT NULL REFERENCES orders(order_id),
    carrier          TEXT NOT NULL,
    shipping_status  TEXT NOT NULL CHECK (shipping_status IN ('in_transit','delivered')),
    delivery_date    DATE              -- NULL while in transit
);

CREATE TABLE returns (
    return_id      INTEGER PRIMARY KEY,
    order_id       INTEGER NOT NULL REFERENCES orders(order_id),
    product_id     INTEGER NOT NULL REFERENCES products(product_id),
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    return_reason  TEXT NOT NULL,
    return_date    DATE NOT NULL
);

-- ---------------------------------------------------------------- Indexes
-- On every foreign key, so the agent's JOINs stay fast
CREATE INDEX idx_products_category   ON products(category_id);
CREATE INDEX idx_inventory_product   ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_orders_customer     ON orders(customer_id);
CREATE INDEX idx_orders_date         ON orders(order_date);
CREATE INDEX idx_items_order         ON order_items(order_id);
CREATE INDEX idx_items_product       ON order_items(product_id);
CREATE INDEX idx_payments_order      ON payments(order_id);
CREATE INDEX idx_shipments_order     ON shipments(order_id);
CREATE INDEX idx_returns_order       ON returns(order_id);
CREATE INDEX idx_returns_product     ON returns(product_id);