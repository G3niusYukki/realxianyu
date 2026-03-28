-- XianyuFlow v10 Phase 4: PostgreSQL Performance Optimization
-- Database indexes and query optimizations

-- Order Service Indexes
-- ====================

-- Orders table indexes for common queries
CREATE INDEX IF NOT EXISTS idx_orders_xianyu_order_id
    ON orders(xianyu_order_id);

CREATE INDEX IF NOT EXISTS idx_orders_buyer_id
    ON orders(buyer_id);

CREATE INDEX IF NOT EXISTS idx_orders_status
    ON orders(status);

CREATE INDEX IF NOT EXISTS idx_orders_created_at
    ON orders(created_at DESC);

-- Composite index for status + created_at (common query pattern)
CREATE INDEX IF NOT EXISTS idx_orders_status_created
    ON orders(status, created_at DESC);

-- Partial index for active orders (excluding completed/cancelled)
CREATE INDEX IF NOT EXISTS idx_orders_active
    ON orders(status, created_at DESC)
    WHERE status NOT IN ('COMPLETED', 'CANCELLED', 'REFUNDED');

-- Virtual Goods Code indexes
CREATE INDEX IF NOT EXISTS idx_vg_codes_order_id
    ON virtual_goods_codes(order_id);

CREATE INDEX IF NOT EXISTS idx_vg_codes_used
    ON virtual_goods_codes(used, used_at)
    WHERE used = true;

-- AI Service Indexes
-- ==================

-- User Profiles indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_active
    ON user_profiles(last_active_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_profiles_credit_score
    ON user_profiles(credit_score DESC);

-- GIN index for JSONB queries on preferences
CREATE INDEX IF NOT EXISTS idx_user_profiles_preferences_gin
    ON user_profiles USING GIN (preferences);

-- Context Snapshots indexes
CREATE INDEX IF NOT EXISTS idx_context_snapshots_user_created
    ON context_snapshots(user_id, created_at DESC);

-- BRIN index for time-series data (efficient for large tables)
CREATE INDEX IF NOT EXISTS idx_context_snapshots_created_brin
    ON context_snapshots USING BRIN (created_at);

-- A/B Testing Indexes
-- ===================

CREATE INDEX IF NOT EXISTS idx_ab_experiments_status
    ON ab_experiments(status);

CREATE INDEX IF NOT EXISTS idx_ab_assignments_user_exp
    ON ab_user_assignments(user_id, experiment_id);

-- Performance Optimization: Partitioning for large tables
-- ========================================================

-- Partition context_snapshots by month for better query performance
-- Note: This requires creating a new partitioned table and migrating data

/*
-- Example of creating partitioned table (run manually for existing data)
CREATE TABLE context_snapshots_partitioned (
    LIKE context_snapshots INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE context_snapshots_y2024m01 PARTITION OF context_snapshots_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE context_snapshots_y2024m02 PARTITION OF context_snapshots_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- ... more partitions
*/

-- Query Optimization Views
-- ========================

-- Active orders view with commonly joined fields
CREATE OR REPLACE VIEW v_active_orders AS
SELECT
    o.id,
    o.xianyu_order_id,
    o.buyer_id,
    o.status,
    o.amount,
    o.created_at,
    o.updated_at,
    (SELECT COUNT(*) FROM virtual_goods_codes vgc WHERE vgc.order_id = o.id) as code_count,
    (SELECT COUNT(*) FROM virtual_goods_codes vgc WHERE vgc.order_id = o.id AND vgc.used = true) as used_code_count
FROM orders o
WHERE o.status NOT IN ('COMPLETED', 'CANCELLED', 'REFUNDED');

-- User activity summary view
CREATE OR REPLACE VIEW v_user_activity_summary AS
SELECT
    up.user_id,
    up.total_orders,
    up.total_spent_cents,
    up.avg_order_value_cents,
    up.last_active_at,
    up.credit_score,
    (SELECT COUNT(*) FROM context_snapshots cs WHERE cs.user_id = up.user_id AND cs.created_at > NOW() - INTERVAL '24 hours') as recent_interactions
FROM user_profiles up;

-- Performance Monitoring
-- ======================

-- Enable query statistics extension (if available)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Table to store query performance metrics
CREATE TABLE IF NOT EXISTS query_performance_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_hash VARCHAR(64),
    query_text TEXT,
    avg_execution_time_ms FLOAT,
    total_calls INT DEFAULT 0,
    captured_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_perf_hash
    ON query_performance_log(query_hash);

-- Analyze tables to update statistics
ANALYZE orders;
ANALYZE virtual_goods_codes;
ANALYZE user_profiles;
ANALYZE context_snapshots;
ANALYZE ab_experiments;
ANALYZE ab_user_assignments;

-- Vacuum to reclaim space and update visibility map
VACUUM ANALYZE;
