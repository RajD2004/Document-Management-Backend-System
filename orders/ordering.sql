DROP TABLE IF EXISTS orders;

CREATE TABLE orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    product TEXT,
    quantity INTEGER,
    price REAL,
    timestamp REAL
);