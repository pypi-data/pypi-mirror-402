-- Analytics Events Table Schema for Supabase
-- Run this SQL in your Supabase SQL Editor
-- Table name: raw_analytics

CREATE TABLE IF NOT EXISTS raw_analytics (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  event_name TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_raw_analytics_user_id ON raw_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_raw_analytics_event_name ON raw_analytics(event_name);
CREATE INDEX IF NOT EXISTS idx_raw_analytics_created_at ON raw_analytics(created_at);

-- Optional: Create a composite index for common queries
CREATE INDEX IF NOT EXISTS idx_raw_analytics_user_event ON raw_analytics(user_id, event_name);

-- Optional: Row Level Security (RLS) policies
-- Since you're using anon key, you may want to enable RLS for security
-- Uncomment the following if you want to use RLS:

-- Enable RLS
-- ALTER TABLE raw_analytics ENABLE ROW LEVEL SECURITY;

-- Policy for inserts (allows anyone with anon key to insert)
-- This is needed if RLS is enabled and you want to use anon key
-- CREATE POLICY "Allow anon inserts" ON raw_analytics
-- FOR INSERT
-- TO anon
-- WITH CHECK (true);

-- Policy for service role (bypasses RLS)
-- Service role key automatically bypasses RLS, so no policy needed

-- Session tracking support
ALTER TABLE raw_analytics ADD COLUMN IF NOT EXISTS session_id TEXT;
CREATE INDEX IF NOT EXISTS idx_raw_analytics_session_id ON raw_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_raw_analytics_session_created ON raw_analytics(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_raw_analytics_user_session ON raw_analytics(user_id, session_id);

-- MCP name tracking support
ALTER TABLE raw_analytics ADD COLUMN IF NOT EXISTS mcp_name TEXT;
CREATE INDEX IF NOT EXISTS idx_raw_analytics_mcp_name ON raw_analytics(mcp_name);

-- Optional: Add comments for documentation
COMMENT ON TABLE raw_analytics IS 'Stores analytics events tracked by the Analytics SDK';
COMMENT ON COLUMN raw_analytics.user_id IS 'Unique identifier for the user';
COMMENT ON COLUMN raw_analytics.event_name IS 'Name of the event (e.g., tool_used, page_view)';
COMMENT ON COLUMN raw_analytics.metadata IS 'Additional event data as JSON';
COMMENT ON COLUMN raw_analytics.created_at IS 'Timestamp when the event was created';
COMMENT ON COLUMN raw_analytics.session_id IS 'Session ID for grouping events into chains';
COMMENT ON COLUMN raw_analytics.mcp_name IS 'MCP server name (e.g., "drea", "benchmark-mcp")';

