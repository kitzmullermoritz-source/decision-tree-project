-- Idempotent schema for the decision tree application.
-- Safe to run against an existing database: tables are only created
-- if they do not already exist.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    root_node_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (root_node_id) REFERENCES nodes (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    node_type TEXT NOT NULL CHECK (node_type IN ('decision', 'chance', 'outcome')),
    label TEXT NOT NULL,
    utility REAL,
    pos_x REAL,
    pos_y REAL,
    FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    source_node_id INTEGER NOT NULL,
    target_node_id INTEGER NOT NULL,
    label TEXT,
    probability REAL,
    FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE,
    FOREIGN KEY (source_node_id) REFERENCES nodes (id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES nodes (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_nodes_analysis_id ON nodes (analysis_id);
CREATE INDEX IF NOT EXISTS idx_edges_analysis_id ON edges (analysis_id);
CREATE INDEX IF NOT EXISTS idx_edges_source_node_id ON edges (source_node_id);
