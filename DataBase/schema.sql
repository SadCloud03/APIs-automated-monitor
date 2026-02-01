-- Activar integridad referencial
PRAGMA foreign_keys = ON;

-- =====================
-- Tabla: apis
-- =====================
CREATE TABLE IF NOT EXISTS APIs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (api_id) REFERENCES apis(id) ON DELETE CASCADE
);

-- =====================
-- Índices (performance)
-- =====================
CREATE INDEX IF NOT EXISTS idx_logs_api_id ON logs(api_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
