PRAGMA foreign_keys = ON;

-- =====================
-- Tabla: APIs
-- =====================
CREATE TABLE IF NOT EXISTS APIs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT (datetime('now','localtime'))
);

-- =====================
-- Tabla: logs
-- =====================
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('UP', 'DOWN')),
    status_code INTEGER,
    latency REAL,
    response TEXT,
    timestamp DATETIME DEFAULT (datetime('now','localtime')),

    FOREIGN KEY (api_id) REFERENCES APIs(id) ON DELETE CASCADE
);

-- =====================
-- Tabla: api_state
-- Último estado + métricas actuales para dashboard
-- =====================
CREATE TABLE IF NOT EXISTS api_state (
    api_id INTEGER PRIMARY KEY,
    last_status TEXT CHECK (last_status IN ('UP', 'DOWN')),
    last_status_code INTEGER,
    last_latency REAL,
    last_checked_at DATETIME,
    last_alert_at DATETIME,

    FOREIGN KEY (api_id) REFERENCES APIs(id) ON DELETE CASCADE
);

-- =====================
-- Índices
-- =====================
CREATE INDEX IF NOT EXISTS idx_logs_api_id ON logs(api_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
