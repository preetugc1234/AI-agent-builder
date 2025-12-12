-- ============================================================================
-- Database Schema Setup for Application-Level RLS
-- ============================================================================
--
-- NodeRush implements APPLICATION-LEVEL row-level security (not database RLS).
-- This migration ensures the database schema supports the RLS patterns used
-- in the FastAPI application layer.
--
-- Security Model:
-- - All queries filter by user_id in application code (SQLAlchemy)
-- - Foreign key constraints with CASCADE delete ensure data cleanup
-- - Indexes on user_id columns optimize query performance
-- - Application code enforces ownership checks before mutations
--
-- Tables with user_id ownership:
-- 1. users - User profiles (id is the primary user identifier)
-- 2. agents - AI agents (user_id foreign key)
-- 3. user_integrations - OAuth/API key integrations (user_id foreign key)
-- 4. token_usage - AI token consumption tracking (user_id foreign key)
-- 5. security_logs - Security audit logs (user_id foreign key)
-- 6. rate_limits - Rate limit tracking (user_id foreign key)
--
-- Tables with indirect ownership (via agents):
-- 7. deployments - Agent deployments (agent_id -> agents.user_id)
-- 8. execution_logs - Agent execution history (agent_id -> agents.user_id)
--
-- ============================================================================

-- ============================================================================
-- Performance Indexes for Application-Level RLS
-- ============================================================================
-- These indexes speed up the WHERE user_id = ? queries in the application

-- Agents table - already has index from index=True in SQLAlchemy
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);

-- User integrations table
CREATE INDEX IF NOT EXISTS idx_user_integrations_user_id ON user_integrations(user_id);

-- Token usage table
CREATE INDEX IF NOT EXISTS idx_token_usage_user_id ON token_usage(user_id);

-- Security logs table
CREATE INDEX IF NOT EXISTS idx_security_logs_user_id ON security_logs(user_id);

-- Rate limits table (if exists)
CREATE INDEX IF NOT EXISTS idx_rate_limits_user_id ON rate_limits(user_id);

-- Composite indexes for indirect ownership queries
-- These speed up JOIN queries for deployments and execution logs
CREATE INDEX IF NOT EXISTS idx_deployments_agent_id ON deployments(agent_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_agent_id ON execution_logs(agent_id);

-- Index on email for faster login lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================================
-- Verify Foreign Key Constraints
-- ============================================================================
-- Ensure CASCADE delete is properly configured
-- (This should already be set via SQLAlchemy models, but we verify here)

-- Verify agents.user_id has CASCADE delete
-- Query to check:
-- SELECT conname, conrelid::regclass, confrelid::regclass, confdeltype
-- FROM pg_constraint
-- WHERE contype = 'f' AND conrelid = 'agents'::regclass;

-- Expected: confdeltype = 'c' (CASCADE)

-- ============================================================================
-- Add Comments for Documentation
-- ============================================================================

COMMENT ON TABLE users IS
'User profiles table. Application-level RLS: users can only access their own profile (id = current_user.id)';

COMMENT ON TABLE agents IS
'AI agents table. Application-level RLS: users can only access agents where user_id = current_user.id';

COMMENT ON TABLE user_integrations IS
'User OAuth/API integrations. Application-level RLS: filter by user_id = current_user.id';

COMMENT ON TABLE deployments IS
'Agent deployments. Application-level RLS: access via JOIN with agents table to verify ownership';

COMMENT ON TABLE execution_logs IS
'Agent execution history. Application-level RLS: access via JOIN with agents table to verify ownership';

COMMENT ON TABLE token_usage IS
'AI token usage tracking. Application-level RLS: filter by user_id = current_user.id';

COMMENT ON TABLE security_logs IS
'Security audit logs. Application-level RLS: users can view their own logs (user_id = current_user.id)';

COMMENT ON COLUMN agents.user_id IS
'Foreign key to users.id. CASCADE delete ensures agent cleanup when user is deleted. Application code MUST filter by this column.';

COMMENT ON COLUMN user_integrations.user_id IS
'Foreign key to users.id. CASCADE delete ensures integration cleanup when user is deleted. Application code MUST filter by this column.';

COMMENT ON COLUMN deployments.agent_id IS
'Foreign key to agents.id. CASCADE delete ensures deployment cleanup when agent is deleted. Application code MUST JOIN with agents to verify ownership.';

COMMENT ON COLUMN execution_logs.agent_id IS
'Foreign key to agents.id. CASCADE delete ensures log cleanup when agent is deleted. Application code MUST JOIN with agents to verify ownership.';

-- ============================================================================
-- Application-Level RLS Pattern Verification
-- ============================================================================

-- Use these queries to verify RLS implementation in application code:

-- 1. Verify all SELECT queries filter by user_id:
--    SELECT * FROM agents WHERE user_id = current_user.id;

-- 2. Verify all INSERT queries set user_id from token:
--    INSERT INTO agents (user_id, ...) VALUES (current_user.id, ...);

-- 3. Verify all UPDATE/DELETE queries check ownership first:
--    UPDATE agents SET ... WHERE id = ? AND user_id = current_user.id;

-- 4. Verify indirect ownership uses JOIN:
--    SELECT d.* FROM deployments d
--    JOIN agents a ON d.agent_id = a.id
--    WHERE d.id = ? AND a.user_id = current_user.id;

-- ============================================================================
-- Database Statistics
-- ============================================================================

-- Analyze tables to update statistics for query planner
ANALYZE users;
ANALYZE agents;
ANALYZE user_integrations;
ANALYZE deployments;
ANALYZE execution_logs;
ANALYZE token_usage;
ANALYZE security_logs;

-- ============================================================================
-- Rollback Instructions
-- ============================================================================

-- To remove indexes (for testing only):
-- DROP INDEX IF EXISTS idx_agents_user_id;
-- DROP INDEX IF EXISTS idx_user_integrations_user_id;
-- DROP INDEX IF EXISTS idx_token_usage_user_id;
-- DROP INDEX IF EXISTS idx_security_logs_user_id;
-- DROP INDEX IF EXISTS idx_rate_limits_user_id;
-- DROP INDEX IF EXISTS idx_deployments_agent_id;
-- DROP INDEX IF EXISTS idx_execution_logs_agent_id;
-- DROP INDEX IF EXISTS idx_users_email;

-- ============================================================================
-- Migration Complete
-- ============================================================================

-- This migration prepares the database for application-level RLS.
-- All security enforcement happens in the FastAPI application layer.
-- See backend/ROW_LEVEL_SECURITY.md for implementation details.
