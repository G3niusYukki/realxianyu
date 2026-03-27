-- 0013: Add foreign key constraint between virtual_goods_orders and virtual_goods_products
-- FK: virtual_goods_orders.xianyu_product_id -> virtual_goods_products.xianyu_product_id
-- ON DELETE SET NULL (orders.xianyu_product_id is nullable)
-- ON UPDATE CASCADE (if product xianyu_product_id changes, orders follow)
--
-- NOTE: SQLite does not support ALTER TABLE ADD CONSTRAINT, so this migration
-- rebuilds the table for existing deployments. New deployments should include
-- the FOREIGN KEY clause directly in the CREATE TABLE statement (see below).

-- For new deployments, include this in virtual_goods_orders CREATE TABLE:
--     FOREIGN KEY (xianyu_product_id) REFERENCES virtual_goods_products(xianyu_product_id) ON DELETE SET NULL ON UPDATE CASCADE

-- Step 1: Create new table with FK constraint
CREATE TABLE IF NOT EXISTS virtual_goods_orders_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    xianyu_order_id TEXT NOT NULL UNIQUE,
    xianyu_product_id TEXT,
    supply_order_no TEXT UNIQUE,
    session_id TEXT,
    order_status TEXT NOT NULL,
    fulfillment_status TEXT NOT NULL DEFAULT 'pending',
    callback_status TEXT NOT NULL DEFAULT 'none',
    manual_takeover INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK(order_status IN ('pending_payment','paid_waiting_delivery','delivered','delivery_failed','refund_pending','refunded','closed')),
    CHECK(fulfillment_status IN ('pending','delivering','fulfilled','failed','manual')),
    CHECK(callback_status IN ('none','received','processed','failed')),
    FOREIGN KEY (xianyu_product_id) REFERENCES virtual_goods_products(xianyu_product_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Step 2: Migrate data from old table to new table
INSERT INTO virtual_goods_orders_new
    (id, xianyu_order_id, xianyu_product_id, supply_order_no, session_id,
     order_status, fulfillment_status, callback_status, manual_takeover,
     last_error, created_at, updated_at)
SELECT
    id, xianyu_order_id, xianyu_product_id, supply_order_no, session_id,
    order_status, fulfillment_status, callback_status, manual_takeover,
    last_error, created_at, updated_at
FROM virtual_goods_orders;

-- Step 3: Drop the old table
DROP TABLE virtual_goods_orders;

-- Step 4: Rename new table to original name
ALTER TABLE virtual_goods_orders_new RENAME TO virtual_goods_orders;

-- Step 5: Restore indexes on the new table
CREATE INDEX IF NOT EXISTS idx_vg_orders_status_updated
ON virtual_goods_orders(order_status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_vg_orders_callback_status_updated
ON virtual_goods_orders(callback_status, updated_at DESC);
