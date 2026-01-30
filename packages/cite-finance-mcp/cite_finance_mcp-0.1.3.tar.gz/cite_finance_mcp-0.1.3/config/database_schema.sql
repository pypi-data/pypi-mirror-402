-- Cite-Finance API Database Schema
-- PostgreSQL schema for production use
-- Clean separation from Cite-Agent database

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT false,
    password_hash VARCHAR(255),  -- For dashboard login

    -- Company info
    company_name VARCHAR(255),
    website VARCHAR(255),

    -- Pricing tier
    tier VARCHAR(20) DEFAULT 'free' CHECK (tier IN ('free', 'starter', 'professional', 'enterprise')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled', 'trial')),

    -- Usage tracking
    api_calls_this_month INTEGER DEFAULT 0,
    api_calls_limit INTEGER DEFAULT 100,
    last_reset_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Billing (Stripe)
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255),
    billing_period_start TIMESTAMP,
    billing_period_end TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_api_call TIMESTAMP,
    last_login TIMESTAMP,

    -- Indexes
    INDEX idx_email (email),
    INDEX idx_stripe_customer (stripe_customer_id),
    INDEX idx_tier (tier),
    INDEX idx_status (status)
);

-- ============================================================================
-- API KEYS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    key_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Key data
    key_hash VARCHAR(255) UNIQUE NOT NULL,  -- SHA256 hash
    key_prefix VARCHAR(20) NOT NULL,  -- First chars for display (e.g., "fsk_Ab7d...")
    name VARCHAR(100) DEFAULT 'Default Key',

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_test_mode BOOLEAN DEFAULT false,

    -- Usage tracking
    total_calls BIGINT DEFAULT 0,
    calls_this_month INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    -- Security
    allowed_ips TEXT[],  -- IP whitelist
    allowed_domains TEXT[],  -- CORS whitelist

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    -- Indexes
    INDEX idx_key_hash (key_hash),
    INDEX idx_user_id (user_id),
    INDEX idx_active (is_active)
);

-- ============================================================================
-- USAGE RECORDS TABLE
-- For billing and analytics
-- ============================================================================
CREATE TABLE IF NOT EXISTS usage_records (
    record_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    key_id VARCHAR(64) NOT NULL REFERENCES api_keys(key_id) ON DELETE CASCADE,

    -- Request details
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,

    -- Cost calculation
    credits_used INTEGER DEFAULT 1,

    -- Performance
    response_time_ms INTEGER,

    -- Metadata
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,

    -- Indexes for analytics
    INDEX idx_user_timestamp (user_id, timestamp DESC),
    INDEX idx_endpoint (endpoint),
    INDEX idx_timestamp (timestamp DESC)
);

-- Partition by month for performance
-- CREATE TABLE usage_records_2025_01 PARTITION OF usage_records
--     FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- ============================================================================
-- SUBSCRIPTIONS TABLE
-- Track subscription changes for audit
-- ============================================================================
CREATE TABLE IF NOT EXISTS subscription_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Subscription details
    old_tier VARCHAR(20),
    new_tier VARCHAR(20) NOT NULL,

    -- Stripe event
    stripe_subscription_id VARCHAR(255),
    stripe_event_id VARCHAR(255),

    -- Reason
    change_reason VARCHAR(50),  -- 'upgrade', 'downgrade', 'cancelled', 'trial_ended'

    -- Metadata
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_changed_at (changed_at DESC)
);

-- ============================================================================
-- WEBHOOK EVENTS TABLE
-- Store Stripe webhook events for debugging
-- ============================================================================
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,  -- Stripe event ID
    event_type VARCHAR(100) NOT NULL,  -- 'customer.subscription.created', etc.

    -- Event data
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT false,
    processing_error TEXT,

    -- Metadata
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,

    INDEX idx_event_id (event_id),
    INDEX idx_event_type (event_type),
    INDEX idx_received_at (received_at DESC)
);

-- ============================================================================
-- FEATURE FLAGS TABLE
-- Control feature access per tier
-- ============================================================================
CREATE TABLE IF NOT EXISTS feature_flags (
    feature_name VARCHAR(100) PRIMARY KEY,
    description TEXT,

    -- Tier access
    free_tier BOOLEAN DEFAULT false,
    starter_tier BOOLEAN DEFAULT false,
    professional_tier BOOLEAN DEFAULT true,
    enterprise_tier BOOLEAN DEFAULT true,

    -- Global toggle
    enabled BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default features
INSERT INTO feature_flags (feature_name, description, free_tier, starter_tier, professional_tier, enterprise_tier) VALUES
    ('sec_edgar_data', 'Access SEC EDGAR filings', true, true, true, true),
    ('yahoo_finance_data', 'Access Yahoo Finance market data', false, true, true, true),
    ('alpha_vantage_data', 'Access Alpha Vantage real-time data', false, false, true, true),
    ('ai_synthesis', 'LLM-powered financial analysis', false, false, true, true),
    ('custom_metrics', 'Create custom calculation formulas', false, false, false, true),
    ('webhooks', 'Webhook notifications for events', false, false, true, true),
    ('priority_support', '24/7 priority support', false, false, false, true),
    ('sla_guarantee', '99.9% uptime SLA', false, false, false, true)
ON CONFLICT (feature_name) DO NOTHING;

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Reset monthly usage on first day of month
CREATE OR REPLACE FUNCTION reset_monthly_usage()
RETURNS void AS $$
BEGIN
    UPDATE users
    SET api_calls_this_month = 0,
        last_reset_at = CURRENT_TIMESTAMP
    WHERE DATE_TRUNC('month', last_reset_at) < DATE_TRUNC('month', CURRENT_TIMESTAMP);

    UPDATE api_keys
    SET calls_this_month = 0
    WHERE DATE_TRUNC('month', COALESCE(last_used_at, created_at)) < DATE_TRUNC('month', CURRENT_TIMESTAMP);
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly reset (run via cron or pg_cron)
-- SELECT cron.schedule('reset-monthly-usage', '0 0 1 * *', 'SELECT reset_monthly_usage()');

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_tier_status ON users(tier, status);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_active ON api_keys(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_usage_user_date ON usage_records(user_id, timestamp DESC);

-- ============================================================================
-- GRANTS (adjust for your user)
-- ============================================================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cite-finance_api;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cite-finance_api;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Create demo user for testing
INSERT INTO users (user_id, email, tier, status, api_calls_limit)
VALUES ('demo_user_123', 'demo@cite-finance.io', 'professional', 'active', 10000)
ON CONFLICT (user_id) DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts with billing and usage tracking';
COMMENT ON TABLE api_keys IS 'API keys for authentication and usage tracking';
COMMENT ON TABLE usage_records IS 'Detailed API usage logs for billing and analytics';
COMMENT ON TABLE subscription_history IS 'Audit log of subscription changes';
COMMENT ON TABLE webhook_events IS 'Stripe webhook events for debugging';
COMMENT ON TABLE feature_flags IS 'Feature access control per pricing tier';
