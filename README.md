# Smartphone Sales Dashboard

A public interview-demo dashboard backed by FastAPI, SQLAlchemy, and SQLite, with a Vite/React analytics frontend.

## Database design

```mermaid
erDiagram
    MANUFACTURER ||--o{ PHONE : produces
    PHONE ||--o{ PURCHASE : sold_in
    USER ||--o{ PURCHASE : makes
    USER ||--o| USER_CONTACT : has
    PHONE ||--o{ PROMOTION : receives
    PURCHASE ||--o{ PURCHASE_PROMOTION : uses
    PROMOTION ||--o{ PURCHASE_PROMOTION : applied_through
    ADMIN o|--o{ ADMIN : creates

    MANUFACTURER {
        INTEGER manufacturer_id PK
        TEXT name UK
        TEXT country
        TEXT website
    }

    PHONE {
        INTEGER phone_id PK
        INTEGER manufacturer_id FK
        TEXT model_name
        TEXT release_date
        INTEGER storage_gb
        INTEGER ram_gb
        REAL launch_price
        TEXT operating_system
        TEXT image_path
        INTEGER is_active
    }

    USER {
        INTEGER user_id PK
        TEXT first_name
        TEXT last_name
        TEXT date_of_birth
        TEXT gender
        TEXT occupation
        TEXT income_range
        TEXT created_at
    }

    USER_CONTACT {
        INTEGER contact_id PK
        INTEGER user_id FK, UK
        TEXT email UK
        TEXT phone_number
        TEXT street
        TEXT city
        TEXT state
        TEXT zip_code
        TEXT country
    }

    PURCHASE {
        INTEGER purchase_id PK
        INTEGER user_id FK
        INTEGER phone_id FK
        TEXT purchase_date
        REAL sale_price
        INTEGER quantity
        TEXT phone_status
    }

    PROMOTION {
        INTEGER promotion_id PK
        INTEGER phone_id FK
        TEXT promo_code UK
        TEXT promo_name
        TEXT discount_type
        REAL discount_value
        TEXT start_date
        TEXT end_date
        TEXT description
        INTEGER is_active
    }

    PURCHASE_PROMOTION {
        INTEGER purchase_promo_id PK
        INTEGER purchase_id FK
        INTEGER promotion_id FK
        REAL discount_amount
    }

    ADMIN {
        INTEGER admin_id PK
        TEXT first_name
        TEXT last_name
        TEXT email UK
        TEXT password_hash
        INTEGER is_active
        INTEGER created_by FK
        TEXT created_at
    }
```

Key relationship rules:

- A manufacturer can have many phone configurations; each phone belongs to one manufacturer.
- A customer can make many purchases and can have at most one contact record.
- `purchase_promotion` resolves the many-to-many relationship between purchases and promotions. A unique constraint prevents duplicate promotion assignments, and a trigger limits each purchase to two promotions.
- Promotions belong to a specific phone, while purchases record the customer, phone, quantity, sale price, and device status at the time of sale.
- Administrators have a self-referencing creator relationship. The root administrator has `created_by = NULL`.

## First-time setup

### Backend environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the generated value after `JWT_SECRET=` in `backend/.env`. The local `.env` file is ignored by Git.

Create the first administrator interactively:

```bash
python scripts/create_admin.py
```

The script securely prompts for the password and stores only its bcrypt hash. Once a root admin exists, create additional admins from the protected Admins page.

### Frontend environment

```bash
cd ../frontend
npm install
```

## Run locally

Open two terminal windows from the project root.

### Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open:

- Public dashboard: http://127.0.0.1:5173
- Admin login: http://127.0.0.1:5173/#/admin/login
- Backend: http://127.0.0.1:8000
- Swagger API docs: http://127.0.0.1:8000/docs

The frontend uses `http://127.0.0.1:8000` by default. To use another backend, set `VITE_API_BASE_URL` before starting Vite.
