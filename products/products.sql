DROP TABLE IF EXISTS productInformation;

CREATE TABLE productInformation(
    name TEXT UNIQUE PRIMARY KEY,
    price REAL,
    category TEXT
);