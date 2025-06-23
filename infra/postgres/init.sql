CREATE TABLE IF NOT EXISTS search_logs (
  id SERIAL PRIMARY KEY,
  user_id TEXT,
  session_id TEXT,
  keyword TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_keyword_time ON search_logs (keyword, created_at);
