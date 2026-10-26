-- Esquema v1 — Sistema de reservas de laboratorio
-- SQLite 3, claves foráneas habilitadas por conexión (PRAGMA foreign_keys = ON)

CREATE TABLE IF NOT EXISTS units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,          -- Código único: MIC-01, MIC-02, OSC-01, MUL-01, FUE-01
    name TEXT NOT NULL,                 -- Nombre: puede repetirse (ej. "Microscopio digital")
    type TEXT NOT NULL,                 -- Categoría: Microscopía, Medición, Potencia
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE RESTRICT,
    user TEXT NOT NULL,
    start_utc TEXT NOT NULL,            -- ISO 8601 UTC: YYYY-MM-DD HH:MM:SS
    end_utc TEXT NOT NULL,              -- ISO 8601 UTC: YYYY-MM-DD HH:MM:SS
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'activa' CHECK (status IN ('activa','cancelada')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    cancelled_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_reservations_unit_time ON reservations(unit_id, start_utc, end_utc);
CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);