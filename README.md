# Microservices System: User, Products, Search, Ordering, and Logging

This project implements a full microservice-based architecture using Flask, SQLite, and internal service-to-service communication.  
It includes five services that work together to handle authentication, product management, searching, ordering, and activity logging.

## Services Overview

### 1. User Service  
**Files:** `app.py` :contentReference[oaicite:0]{index=0} · `helperFunctions.py` :contentReference[oaicite:1]{index=1}  
Manages:
- User creation  
- Password validation + hashing  
- Login  
- JWT generation & verification  
- Employee permissions  
- Past password tracking

Database: `users.db` with `userInformation` and `pastPasswords`.

---

### 2. Search Service  
**File:** `app.py` (Search) :contentReference[oaicite:2]{index=2}  
Allows authenticated users to:
- Search products by **name**
- Search products by **category**
- View last modifier of each product (via logs)
- Logs each search event

Relies on:
- User service for JWT verification  
- Products service for product info  
- Logs service for last-modified data

---

### 3. Products Service  
**File:** `app.py` (Products) :contentReference[oaicite:3]{index=3}  
Supports:
- Creating new products (employees only)  
- Editing product price/category (employees only)  
- Fetching individual product info  
- Fetching product lists by category  
- Logs product creation & edits

Database: `products.db`.

---

### 4. Ordering Service  
**File:** `app.py` (Ordering) :contentReference[oaicite:4]{index=4}  
Responsibilities:
- Creates orders for authenticated users  
- Pulls product prices from Products service  
- Computes total cost  
- Inserts order records into database  
- Logs every ordered product

Database: `ordering.db`.

---

### 5. Logging Service  
**File:** `app.py` (Logs) :contentReference[oaicite:5]{index=5}  
Stores logs for all services. Tracks:
- Who performed an action  
- Which product was involved  
- What event occurred  
- Timestamp

Allows:
- Users to view **their own logs**  
- Employees to view **product logs**  
- Logs every action coming from the other services

Database: `logs.db`.

---

## Architecture Summary
- **User service** authenticates and issues JWTs.  
- **Products service** manages product data (employee restricted).  
- **Search service** allows lookups across the system.  
- **Ordering service** processes purchases using data from Products.  
- **Logging service** records every action across every service.  

Each service runs independently and communicates via HTTP.

---

## How to Run
Start each service separately (typical Docker setup):

```bash
python3 app.py
```
