-- XianyuFlow v10 AI Service Database Schema
-- Phase 3: Context and User Profile

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- L3: User Profile Table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(64) UNIQUE NOT NULL,
    xianyu_user_id VARCHAR(64),

    -- Preferences (JSONB for flexibility)
    preferences JSONB DEFAULT '{}',

    -- Common addresses/routes
    common_routes JSONB DEFAULT '[]',
    preferred_couriers JSONB DEFAULT '[]',

    -- User behavior profile
    price_sensitivity VARCHAR(16) DEFAULT 'medium', -- low, medium, high
    communication_style VARCHAR(16) DEFAULT 'casual', -- formal, casual, concise
    response_speed_preference VARCHAR(16) DEFAULT 'normal', -- fast, normal, detailed

    -- Transaction history summary
    total_orders INT DEFAULT 0,
    total_spent_cents BIGINT DEFAULT 0,
    avg_order_value_cents INT DEFAULT 0,
    last_order_at TIMESTAMP,

    -- Credit/Risk score
    credit_score INT DEFAULT 100, -- 0-100
    risk_level VARCHAR(16) DEFAULT 'low', -- low, medium, high

    -- Metadata
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_xianyu_user_id ON user_profiles(xianyu_user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_active ON user_profiles(last_active_at);

-- L1/L2: Context Snapshots (for analytics/debugging)
CREATE TABLE IF NOT EXISTS context_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    request_id VARCHAR(128),

    -- State at snapshot time
    conversation_state VARCHAR(32),
    intent JSONB,
    extracted_slots JSONB,

    -- Full context (optional, for debugging)
    full_context JSONB,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_context_snapshots_user_session ON context_snapshots(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_context_snapshots_created ON context_snapshots(created_at);

-- Prompt Versions (for A/B testing)
CREATE TABLE IF NOT EXISTS prompt_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(64) NOT NULL, -- e.g., "quote_v1", "quote_v2"
    template_type VARCHAR(32) NOT NULL, -- "quote", "chat", "bargain"
    version VARCHAR(16) NOT NULL, -- semantic version

    -- Template content
    template_content TEXT NOT NULL,
    template_variables JSONB DEFAULT '[]',

    -- A/B testing
    is_active BOOLEAN DEFAULT false,
    traffic_percentage INT DEFAULT 0, -- 0-100

    -- Performance metrics
    total_calls INT DEFAULT 0,
    avg_response_time_ms INT,
    success_rate FLOAT,
    user_satisfaction_score FLOAT,

    -- Metadata
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(name, version)
);

CREATE INDEX IF NOT EXISTS idx_prompt_versions_type ON prompt_versions(template_type);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_active ON prompt_versions(is_active);

-- A/B Test Experiments
CREATE TABLE IF NOT EXISTS ab_experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(128) NOT NULL UNIQUE,
    description TEXT,

    -- Experiment config
    experiment_type VARCHAR(32) NOT NULL, -- "prompt", "model", "strategy"
    status VARCHAR(16) DEFAULT 'draft', -- draft, running, paused, completed

    -- Variants
    control_variant_id UUID NOT NULL,
    treatment_variant_id UUID NOT NULL,

    -- Traffic split
    traffic_percentage INT DEFAULT 50, -- percentage going to treatment

    -- Success metrics
    primary_metric VARCHAR(64) NOT NULL, -- e.g., "conversion_rate"
    secondary_metrics JSONB DEFAULT '[]',

    -- Results
    results JSONB,

    -- Timeline
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User experiment assignments
CREATE TABLE IF NOT EXISTS ab_user_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(64) NOT NULL,
    experiment_id UUID NOT NULL REFERENCES ab_experiments(id),
    variant VARCHAR(16) NOT NULL, -- "control" or "treatment"

    -- Events tracked for this user
    events_count INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, experiment_id)
);

CREATE INDEX IF NOT EXISTS idx_ab_assignments_user ON ab_user_assignments(user_id);
CREATE INDEX IF NOT EXISTS idx_ab_assignments_experiment ON ab_user_assignments(experiment_id);

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_prompt_versions_updated_at ON prompt_versions;
CREATE TRIGGER update_prompt_versions_updated_at
    BEFORE UPDATE ON prompt_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ab_experiments_updated_at ON ab_experiments;
CREATE TRIGGER update_ab_experiments_updated_at
    BEFORE UPDATE ON ab_experiments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default prompt versions
INSERT INTO prompt_versions (name, template_type, version, template_content, is_active, traffic_percentage)
VALUES (
    'quote_default',
    'quote',
    '1.0.0',
    '你是一个专业的物流报价助手。根据用户提供的信息给出准确的运费报价。

用户消息: {{message}}
提取信息: {{extracted_info}}
可用运力: {{couriers}}

请给出友好、专业的回复，包含：
1. 确认理解用户需求
2. 推荐最优运力及价格
3. 预计时效
4. 温馨提示',
    true,
    100
) ON CONFLICT (name, version) DO NOTHING;

INSERT INTO prompt_versions (name, template_type, version, template_content, is_active, traffic_percentage)
VALUES (
    'chat_default',
    'chat',
    '1.0.0',
    '你是闲鱼物流服务的智能客服助手。请友好、专业地回答用户问题。

对话历史:
{{history}}

用户消息: {{message}}

请给出恰当的回复：',
    true,
    100
) ON CONFLICT (name, version) DO NOTHING;
