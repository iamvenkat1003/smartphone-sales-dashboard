PRAGMA foreign_keys = ON;

CREATE TABLE manufacturer (
    manufacturer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    country TEXT,
    website TEXT
);

CREATE TABLE phone (
    phone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    release_date TEXT,
    storage_gb INTEGER CHECK (storage_gb > 0),
    ram_gb INTEGER CHECK (ram_gb > 0),
    launch_price REAL CHECK (launch_price >= 0),
    operating_system TEXT NOT NULL,
    image_path TEXT,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    FOREIGN KEY (manufacturer_id)
        REFERENCES manufacturer (manufacturer_id),
    UNIQUE (manufacturer_id, model_name, storage_gb)
);

CREATE TABLE user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth TEXT,
    gender TEXT,
    occupation TEXT,
    income_range TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_contact (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    email TEXT UNIQUE,
    phone_number TEXT,
    street TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    country TEXT,
    FOREIGN KEY (user_id)
        REFERENCES user (user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE purchase (
    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    phone_id INTEGER NOT NULL,
    purchase_date TEXT NOT NULL,
    sale_price REAL NOT NULL CHECK (sale_price >= 0),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    phone_status TEXT NOT NULL CHECK (
        phone_status IN (
            'PRIMARY',
            'SECONDARY',
            'PREVIOUS',
            'RETURNED',
            'TRADED_IN'
        )
    ),
    FOREIGN KEY (user_id)
        REFERENCES user (user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (phone_id)
        REFERENCES phone (phone_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE promotion (
    promotion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_id INTEGER NOT NULL,
    promo_code TEXT NOT NULL UNIQUE,
    promo_name TEXT NOT NULL,
    discount_type TEXT NOT NULL CHECK (
        discount_type IN ('PERCENTAGE', 'FIXED')
    ),
    discount_value REAL NOT NULL CHECK (discount_value > 0),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL CHECK (end_date >= start_date),
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    FOREIGN KEY (phone_id)
        REFERENCES phone (phone_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE purchase_promotion (
    purchase_promo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER NOT NULL,
    promotion_id INTEGER NOT NULL,
    discount_amount REAL NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    FOREIGN KEY (purchase_id)
        REFERENCES purchase (purchase_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (promotion_id)
        REFERENCES promotion (promotion_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    UNIQUE (purchase_id, promotion_id)
);

CREATE TRIGGER max_two_promotions_per_purchase
BEFORE INSERT ON purchase_promotion
FOR EACH ROW
WHEN (
    SELECT COUNT(*)
    FROM purchase_promotion
    WHERE purchase_id = NEW.purchase_id
) >= 2
BEGIN
    SELECT RAISE(
        ABORT,
        'A purchase can have a maximum of two promotions'
    );
END;

CREATE TABLE admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_by INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by)
        REFERENCES admin (admin_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_phone_manufacturer
    ON phone (manufacturer_id);

CREATE INDEX IF NOT EXISTS idx_purchase_user
    ON purchase (user_id);

CREATE INDEX IF NOT EXISTS idx_purchase_phone
    ON purchase (phone_id);

CREATE INDEX IF NOT EXISTS idx_purchase_date
    ON purchase (purchase_date);

CREATE INDEX IF NOT EXISTS idx_promotion_phone
    ON promotion (phone_id);

CREATE INDEX IF NOT EXISTS idx_purchase_promotion_purchase
    ON purchase_promotion (purchase_id);

CREATE INDEX IF NOT EXISTS idx_purchase_promotion_promotion
    ON purchase_promotion (promotion_id);
