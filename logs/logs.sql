DROP TABLE IF EXISTS logs;

CREATE TABLE logs(
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    product_name TEXT,
    event TEXT,
    timestamp REAL
);