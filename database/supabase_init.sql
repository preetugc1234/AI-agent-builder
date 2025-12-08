-- ============================================
-- NodeRush - Supabase PostgreSQL Database Setup
-- Architecture: ARCHITECTURE.md
-- Budget: $0 (Free Tier - 500 MB storage limit)
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    cognito_id VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free' NOT NULL,
    subscription_status VARCHAR(50) DEFAULT 'active' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);

-- ============================================
-- 2. AGENTS TABLE (3-Agent LangGraph Workflow)
-- ============================================
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    vibe_prompt TEXT NOT NULL,

    -- 3-Agent LangGraph Outputs
    architecture TEXT,                -- Agent 1 (Architect) output
    generated_code TEXT,              -- Agent 2 (Coder) output
    review_notes TEXT,                -- Agent 3 (Reviewer) output
    final_code TEXT,                  -- Final reviewed code
    file_structure JSONB DEFAULT '[]'::jsonb,  -- File list

    -- Deployment
    docker_image_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'draft' NOT NULL,  -- draft, generating, ready, deployed, error
    integrations JSONB DEFAULT '[]'::jsonb,
    flow_data JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for agents
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at DESC);

-- ============================================
-- 3. USER INTEGRATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS user_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,  -- gmail, slack, github, etc.
    auth_type VARCHAR(50) NOT NULL,      -- oauth, api_key
    encrypted_data TEXT NOT NULL,        -- Encrypted credentials
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for user_integrations
CREATE INDEX IF NOT EXISTS idx_user_integrations_user_id ON user_integrations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_integrations_service ON user_integrations(service_name);

-- ============================================
-- 4. DEPLOYMENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    platform VARCHAR(50) DEFAULT 'render' NOT NULL,  -- render, vercel, cloudflare
    task_arn VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,  -- pending, building, running, stopped, error
    logs_url VARCHAR(500),
    deployment_url VARCHAR(500),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for deployments
CREATE INDEX IF NOT EXISTS idx_deployments_agent_id ON deployments(agent_id);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);

-- ============================================
-- 5. SUBSCRIPTION PLANS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    price_monthly DECIMAL(10, 2),
    price_yearly DECIMAL(10, 2),
    max_agents INTEGER NOT NULL,
    max_deployments INTEGER NOT NULL,
    max_executions_per_day INTEGER NOT NULL,
    max_ai_tokens_per_day INTEGER NOT NULL,
    max_storage_mb INTEGER NOT NULL,
    features JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Insert Free Tier Plan (from ARCHITECTURE.md)
INSERT INTO subscription_plans (name, price_monthly, price_yearly, max_agents, max_deployments, max_executions_per_day, max_ai_tokens_per_day, max_storage_mb, features)
VALUES (
    'free',
    0.00,
    0.00,
    10,           -- Max 10 agents
    5,            -- Max 5 deployments
    50,           -- Max 50 executions per day
    50000,        -- Max 50k AI tokens per day
    100,          -- Max 100 MB storage in R2
    '{
        "concurrent_websockets": 3,
        "rate_limits": {
            "agents_create_per_hour": 5,
            "agents_create_per_day": 20,
            "executions_per_hour": 10
        },
        "support": "community"
    }'::jsonb
) ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 6. EXECUTION LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    execution_type VARCHAR(50) NOT NULL,  -- test, production
    status VARCHAR(50) NOT NULL,          -- running, completed, failed
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    duration_seconds INTEGER,
    tokens_used JSONB DEFAULT '{}'::jsonb,  -- {agent1: 1500, agent2: 2000, agent3: 1800}
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ
);

-- Indexes for execution_logs
CREATE INDEX IF NOT EXISTS idx_execution_logs_agent_id ON execution_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_status ON execution_logs(status);
CREATE INDEX IF NOT EXISTS idx_execution_logs_created_at ON execution_logs(created_at DESC);

-- ============================================
-- 7. SECURITY LOGS TABLE (Audit Trail)
-- ============================================
CREATE TABLE IF NOT EXISTS security_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,  -- failed_login, rate_limit_exceeded, suspicious_activity
    ip_address INET,
    user_agent TEXT,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for security_logs
CREATE INDEX IF NOT EXISTS idx_security_logs_event_type ON security_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_security_logs_ip_address ON security_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_logs_created_at ON security_logs(created_at DESC);

-- ============================================
-- 8. TOKEN USAGE TRACKING TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS token_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    agent_name VARCHAR(50) NOT NULL,  -- agent1_architect, agent2_coder, agent3_reviewer
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    model VARCHAR(100) NOT NULL,  -- nvidia/nemotron-nano-12b-v2-vl:free
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for token_usage
CREATE INDEX IF NOT EXISTS idx_token_usage_user_id ON token_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_created_at ON token_usage(created_at DESC);

-- ============================================
-- 9. RATE LIMIT TRACKING TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    ip_address INET,
    resource VARCHAR(100) NOT NULL,  -- agents:create, agents:execute, api:general
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for rate_limits
CREATE INDEX IF NOT EXISTS idx_rate_limits_user_id ON rate_limits(user_id);
CREATE INDEX IF NOT EXISTS idx_rate_limits_ip_address ON rate_limits(ip_address);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window_end ON rate_limits(window_end);

-- ============================================
-- 10. ROW LEVEL SECURITY (RLS)
-- Enable RLS for data isolation
-- ============================================

-- Enable RLS on all user-owned tables
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE deployments ENABLE ROW LEVEL SECURITY;
ALTER TABLE execution_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE token_usage ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS agents_user_isolation ON agents;
DROP POLICY IF EXISTS user_integrations_isolation ON user_integrations;
DROP POLICY IF EXISTS deployments_user_isolation ON deployments;
DROP POLICY IF EXISTS execution_logs_user_isolation ON execution_logs;
DROP POLICY IF EXISTS token_usage_user_isolation ON token_usage;

-- RLS Policies for agents (users can only see their own agents)
CREATE POLICY agents_user_isolation ON agents
    FOR ALL
    USING (user_id = auth.uid());

-- RLS Policies for user_integrations
CREATE POLICY user_integrations_isolation ON user_integrations
    FOR ALL
    USING (user_id = auth.uid());

-- RLS Policies for deployments (through agents)
CREATE POLICY deployments_user_isolation ON deployments
    FOR ALL
    USING (
        agent_id IN (
            SELECT id FROM agents WHERE user_id = auth.uid()
        )
    );

-- RLS Policies for execution_logs (through agents)
CREATE POLICY execution_logs_user_isolation ON execution_logs
    FOR ALL
    USING (
        agent_id IN (
            SELECT id FROM agents WHERE user_id = auth.uid()
        )
    );

-- RLS Policies for token_usage
CREATE POLICY token_usage_user_isolation ON token_usage
    FOR ALL
    USING (user_id = auth.uid());

-- ============================================
-- 11. UPDATED_AT TRIGGER FUNCTION
-- Automatically update updated_at timestamp
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
DROP TRIGGER IF EXISTS update_deployments_updated_at ON deployments;

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deployments_updated_at
    BEFORE UPDATE ON deployments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 12. HELPER FUNCTIONS
-- ============================================

-- Function to check user quota (free tier limits)
CREATE OR REPLACE FUNCTION check_user_agent_quota(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    agent_count INTEGER;
    max_agents INTEGER;
BEGIN
    -- Get user's subscription tier max agents
    SELECT sp.max_agents INTO max_agents
    FROM users u
    JOIN subscription_plans sp ON u.subscription_tier = sp.name
    WHERE u.id = p_user_id;

    -- Count user's current agents
    SELECT COUNT(*) INTO agent_count
    FROM agents
    WHERE user_id = p_user_id;

    -- Return true if under quota
    RETURN agent_count < max_agents;
END;
$$ LANGUAGE plpgsql;

-- Function to get daily token usage
CREATE OR REPLACE FUNCTION get_daily_token_usage(p_user_id UUID)
RETURNS INTEGER AS $$
DECLARE
    total_tokens INTEGER;
BEGIN
    SELECT COALESCE(SUM(total_tokens), 0) INTO total_tokens
    FROM token_usage
    WHERE user_id = p_user_id
    AND created_at >= CURRENT_DATE
    AND created_at < CURRENT_DATE + INTERVAL '1 day';

    RETURN total_tokens;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 13. CLEANUP OLD DATA (Auto-delete for free tier)
-- ============================================

-- Function to cleanup old execution logs (30 days retention)
CREATE OR REPLACE FUNCTION cleanup_old_execution_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM execution_logs
    WHERE created_at < NOW() - INTERVAL '30 days';

    DELETE FROM security_logs
    WHERE created_at < NOW() - INTERVAL '90 days';

    DELETE FROM rate_limits
    WHERE window_end < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 14. VIEWS FOR ANALYTICS
-- ============================================

-- View: User stats
CREATE OR REPLACE VIEW user_stats AS
SELECT
    u.id,
    u.email,
    u.subscription_tier,
    COUNT(DISTINCT a.id) as total_agents,
    COUNT(DISTINCT d.id) as total_deployments,
    COUNT(DISTINCT el.id) as total_executions,
    COALESCE(SUM(tu.total_tokens), 0) as total_tokens_used,
    u.created_at
FROM users u
LEFT JOIN agents a ON u.id = a.user_id
LEFT JOIN deployments d ON a.id = d.agent_id
LEFT JOIN execution_logs el ON a.id = el.agent_id
LEFT JOIN token_usage tu ON u.id = tu.user_id
GROUP BY u.id, u.email, u.subscription_tier, u.created_at;

-- View: Daily token usage per user
CREATE OR REPLACE VIEW daily_token_usage AS
SELECT
    user_id,
    DATE(created_at) as usage_date,
    SUM(total_tokens) as total_tokens,
    COUNT(*) as request_count
FROM token_usage
GROUP BY user_id, DATE(created_at)
ORDER BY usage_date DESC;

-- ============================================
-- SETUP COMPLETE!
-- ============================================

-- Verify setup
SELECT 'Database setup complete!' as status;
SELECT COUNT(*) as table_count FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- Show free tier plan
SELECT * FROM subscription_plans WHERE name = 'free';
