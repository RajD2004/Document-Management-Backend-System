DROP TABLE IF EXISTS userInformation;
DROP TABLE IF EXISTS pastPasswords;

CREATE TABLE userInformation(
    first_name TEXT,
    last_name TEXT,
    username TEXT PRIMARY KEY,
    email_address TEXT,
    employee TEXT,
    password_hash TEXT,
    salt TEXT
);

CREATE TABLE pastPasswords(
    passwordID INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password_hash TEXT,
    FOREIGN KEY (username) REFERENCES userInformation(username) ON DELETE CASCADE
);