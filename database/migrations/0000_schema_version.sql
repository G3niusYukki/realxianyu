CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER,
    name TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
