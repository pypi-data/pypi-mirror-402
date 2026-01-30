-- Cite-Finance API Database Schema - Fixed for PostgreSQL
-- Production initialization script

-- Drop existing tables if they exist
DROP TABLE IF EXISTS webhook_events CASCADE;
DROP TABLE IF EXISTS subscription_history CASCADE;
DROP TABLE IF EXISTS usage_records CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS feature_flags CASCADE;

-- USERS TABLE
CREATE TABLE users (
    user_id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT false,
    password_hash VARCHAR(255),

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
    last_login TIMESTAMP
);

CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_stripe_customer ON users(stripe_customer_id);
CREATE INDEX idx_tier ON users(tier);
CREATE INDEX idx_status ON users(status);

-- API KEYS TABLE
CREATE TABLE api_keys (
    key_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Key data
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(100) DEFAULT 'Default Key',

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_test_mode BOOLEAN DEFAULT false,

    -- Usage tracking
    total_calls BIGINT DEFAULT 0,
    calls_this_month INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    -- Security
    allowed_ips TEXT[],
    allowed_domains TEXT[],

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_key_hash ON api_keys(key_hash);
CREATE INDEX idx_user_id ON api_keys(user_id);
CREATE INDEX idx_active ON api_keys(is_active);

-- USAGE RECORDS TABLE
CREATE TABLE usage_records (
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
    user_agent TEXT
);

CREATE INDEX idx_user_timestamp ON usage_records(user_id, timestamp);
CREATE INDEX idx_endpoint ON usage_records(endpoint);
CREATE INDEX idx_timestamp ON usage_records(timestamp);

-- SUBSCRIPTIONS TABLE
CREATE TABLE subscription_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Subscription details
    old_tier VARCHAR(20),
    new_tier VARCHAR(20) NOT NULL,

    -- Stripe event
    stripe_subscription_id VARCHAR(255),
    stripe_event_id VARCHAR(255),

    -- Reason
    change_reason VARCHAR(50),

    -- Metadata
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sub_user_id ON subscription_history(user_id);
CREATE INDEX idx_changed_at ON subscription_history(changed_at);

-- WEBHOOK EVENTS TABLE
CREATE TABLE webhook_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,

    -- Event data
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT false,
    processing_error TEXT,

    -- Metadata
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_event_id ON webhook_events(event_id);
CREATE INDEX idx_event_type ON webhook_events(event_type);
CREATE INDEX idx_received_at ON webhook_events(received_at);

-- FEATURE FLAGS TABLE
CREATE TABLE feature_flags (
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

-- FUNCTIONS & TRIGGERS

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
