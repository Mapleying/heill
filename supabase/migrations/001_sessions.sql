-- Heill sessions table
-- Run this in the Supabase SQL editor or via `supabase db push`

CREATE TABLE IF NOT EXISTS sessions (
  session_id  TEXT PRIMARY KEY,
  messages    JSONB NOT NULL DEFAULT '[]'::jsonb,
  trip_context JSONB NOT NULL DEFAULT '{}'::jsonb,
  scrape_cache JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at  TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '2 hours')
);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- Optional: scheduled cleanup via pg_cron (enable the extension first)
-- SELECT cron.schedule('cleanup-sessions', '0 * * * *', $$
--   DELETE FROM sessions WHERE expires_at < NOW();
-- $$);

-- Row-level security: only service role can read/write (no user auth needed for this app)
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service role full access" ON sessions
  USING (true)
  WITH CHECK (true);
