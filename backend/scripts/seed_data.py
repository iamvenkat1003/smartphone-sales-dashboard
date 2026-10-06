import argparse
import calendar
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parents[1] / "smartphone_sales.db"
RANDOM_SEED = 20261002
HISTORY_START = date(2024, 10, 1)
HISTORY_END = date(2026, 9, 30)

TABLES = (
    "manufacturer",
    "phone",
    "user",
    "user_contact",
    "purchase",
    "promotion",
    "purchase_promotion",
    "admin",
)

# Child rows must be removed before the parent rows they reference.
SEED_DELETE_ORDER = (
    "purchase_promotion",
    "purchase",
    "promotion",
    "user_contact",
    "user",
    "phone",
    "manufacturer",
)

PHONE_STATUSES = (
    "PRIMARY",
    "SECONDARY",
    "PREVIOUS",
    "RETURNED",
    "TRADED_IN",
)

FULL_MANUFACTURERS = (
    (1, "Apple", "United States", "https://www.apple.com"),
    (2, "Samsung", "South Korea", "https://www.samsung.com"),
    (3, "Google", "United States", "https://store.google.com"),
    (4, "OnePlus", "China", "https://www.oneplus.com"),
    (5, "Motorola", "United States", "https://www.motorola.com"),
    (6, "Nothing", "United Kingdom", "https://nothing.tech"),
)

# key, manufacturer, model, release date, storage, RAM, launch price,
# operating system, market tier, and relative demand weight.
# Mainstream models intentionally receive more demand than premium/niche models.
FULL_PHONE_SPECS = (
    ("iphone_16", "Apple", "iPhone 16", "2024-09-20", 128, 8, 799.00, "iOS", "mainstream", 10.5),
    ("iphone_15", "Apple", "iPhone 15", "2023-09-22", 128, 6, 799.00, "iOS", "mainstream", 7.5),
    ("iphone_16_plus", "Apple", "iPhone 16 Plus", "2024-09-20", 128, 8, 899.00, "iOS", "mainstream", 4.0),
    ("iphone_16_pro", "Apple", "iPhone 16 Pro", "2024-09-20", 256, 8, 1099.00, "iOS", "premium", 5.0),
    ("iphone_16_pro_max", "Apple", "iPhone 16 Pro Max", "2024-09-20", 256, 8, 1199.00, "iOS", "premium", 3.5),
    ("galaxy_s25", "Samsung", "Galaxy S25", "2025-02-07", 128, 12, 799.99, "Android", "mainstream", 9.5),
    ("galaxy_s24_fe", "Samsung", "Galaxy S24 FE", "2024-10-03", 128, 8, 649.99, "Android", "mainstream", 7.5),
    ("galaxy_a55", "Samsung", "Galaxy A55", "2024-03-15", 128, 8, 449.99, "Android", "midrange", 6.0),
    ("galaxy_a35", "Samsung", "Galaxy A35", "2024-03-15", 128, 6, 399.99, "Android", "midrange", 4.5),
    ("galaxy_s25_plus", "Samsung", "Galaxy S25+", "2025-02-07", 256, 12, 999.99, "Android", "premium", 3.0),
    ("galaxy_s25_ultra", "Samsung", "Galaxy S25 Ultra", "2025-02-07", 256, 12, 1299.99, "Android", "premium", 4.5),
    ("pixel_9", "Google", "Pixel 9", "2024-08-22", 128, 12, 799.00, "Android", "mainstream", 5.5),
    ("pixel_9a", "Google", "Pixel 9a", "2025-04-10", 128, 8, 499.00, "Android", "midrange", 4.5),
    ("pixel_8a", "Google", "Pixel 8a", "2024-05-14", 128, 8, 499.00, "Android", "midrange", 3.0),
    ("pixel_9_pro", "Google", "Pixel 9 Pro", "2024-09-04", 256, 16, 1099.00, "Android", "premium", 2.8),
    ("oneplus_12", "OnePlus", "OnePlus 12", "2024-02-06", 256, 12, 799.99, "Android", "mainstream", 2.0),
    ("oneplus_13", "OnePlus", "OnePlus 13", "2025-01-07", 256, 12, 899.99, "Android", "mainstream", 2.2),
    ("oneplus_13r", "OnePlus", "OnePlus 13R", "2025-01-14", 256, 12, 599.99, "Android", "midrange", 3.2),
    ("oneplus_nord_n30", "OnePlus", "Nord N30 5G", "2023-06-15", 128, 8, 299.99, "Android", "budget", 2.0),
    ("motorola_razr_plus", "Motorola", "Razr+ 2024", "2024-07-10", 256, 12, 999.99, "Android", "premium", 0.8),
    ("motorola_edge_2025", "Motorola", "Edge 2025", "2025-06-05", 256, 8, 549.99, "Android", "midrange", 1.5),
    ("moto_g_power_2025", "Motorola", "Moto G Power 2025", "2025-02-06", 128, 8, 299.99, "Android", "budget", 2.5),
    ("moto_g_stylus_2025", "Motorola", "Moto G Stylus 2025", "2025-05-29", 256, 8, 399.99, "Android", "midrange", 2.2),
    ("moto_g_5g_2024", "Motorola", "Moto G 5G 2024", "2024-03-21", 128, 4, 249.99, "Android", "budget", 2.3),
    ("nothing_phone_2", "Nothing", "Phone (2)", "2023-07-17", 256, 12, 599.00, "Android", "midrange", 0.8),
    ("nothing_phone_2a", "Nothing", "Phone (2a)", "2024-03-12", 128, 8, 349.00, "Android", "budget", 1.4),
    ("nothing_phone_3a", "Nothing", "Phone (3a)", "2025-03-11", 128, 8, 379.00, "Android", "midrange", 1.5),
    ("cmf_phone_1", "Nothing", "CMF Phone 1", "2024-07-12", 128, 8, 239.00, "Android", "budget", 1.2),
)

SECOND_PROMOTION_PHONE_KEYS = {
    "iphone_16",
    "iphone_15",
    "iphone_16_pro",
    "galaxy_s25",
    "galaxy_s24_fe",
    "galaxy_a55",
    "pixel_9",
    "pixel_9a",
    "oneplus_13r",
    "moto_g_power_2025",
}

FIRST_NAMES = (
    "Ava", "Liam", "Olivia", "Noah", "Emma", "Ethan", "Mia", "Lucas",
    "Sophia", "Mason", "Isabella", "Logan", "Amelia", "Elijah", "Harper",
    "James", "Evelyn", "Benjamin", "Luna", "Henry", "Camila", "Alexander",
    "Sofia", "Daniel", "Aria", "Michael", "Layla", "Jackson", "Nora", "Maya",
)

LAST_NAMES = (
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Patel",
)

# city, state, ZIP, area code, and relative population weight.
LOCATIONS = (
    ("New York", "NY", "10001", "212", 14),
    ("Los Angeles", "CA", "90012", "213", 11),
    ("Chicago", "IL", "60601", "312", 9),
    ("Houston", "TX", "77002", "713", 9),
    ("Phoenix", "AZ", "85004", "602", 7),
    ("Philadelphia", "PA", "19103", "215", 7),
    ("San Antonio", "TX", "78205", "210", 6),
    ("San Diego", "CA", "92101", "619", 6),
    ("Dallas", "TX", "75201", "214", 7),
    ("Seattle", "WA", "98101", "206", 6),
    ("Denver", "CO", "80202", "303", 6),
    ("Atlanta", "GA", "30303", "404", 6),
    ("Boston", "MA", "02108", "617", 4),
    ("Miami", "FL", "33130", "305", 5),
)

STREET_NAMES = (
    "Main Street", "Oak Avenue", "Maple Drive", "Cedar Lane", "Park Avenue",
    "Washington Street", "Lakeview Drive", "Sunset Boulevard", "Market Street",
    "Highland Avenue", "Riverside Drive", "Pine Street",
)

# occupation, possible income ranges, income weights, occupation weight.
OCCUPATIONS = (
    ("Software Engineer", ("$100,000-$149,999", "$150,000-$199,999"), (70, 30), 10),
    ("Teacher", ("$50,000-$74,999", "$75,000-$99,999"), (70, 30), 9),
    ("Healthcare Professional", ("$75,000-$99,999", "$100,000-$149,999"), (55, 45), 9),
    ("Sales Representative", ("$50,000-$74,999", "$75,000-$99,999"), (60, 40), 8),
    ("Financial Analyst", ("$75,000-$99,999", "$100,000-$149,999"), (60, 40), 7),
    ("Operations Manager", ("$75,000-$99,999", "$100,000-$149,999"), (50, 50), 7),
    ("Marketing Specialist", ("$50,000-$74,999", "$75,000-$99,999"), (55, 45), 7),
    ("Small Business Owner", ("$50,000-$74,999", "$100,000-$149,999"), (55, 45), 6),
    ("Student", ("Under $35,000", "$35,000-$49,999"), (75, 25), 8),
    ("Skilled Tradesperson", ("$50,000-$74,999", "$75,000-$99,999"), (65, 35), 7),
    ("Administrative Assistant", ("$35,000-$49,999", "$50,000-$74,999"), (50, 50), 6),
    ("Consultant", ("$100,000-$149,999", "$150,000-$199,999"), (65, 35), 5),
    ("Designer", ("$50,000-$74,999", "$75,000-$99,999"), (60, 40), 6),
    ("Retired", ("$35,000-$49,999", "$50,000-$74,999"), (60, 40), 5),
)

# November/December and release periods receive moderate uplift.
MONTH_WEIGHTS = (
    (2024, 10, 1.05), (2024, 11, 1.35), (2024, 12, 1.50),
    (2025, 1, 1.00), (2025, 2, 1.08), (2025, 3, 0.90),
    (2025, 4, 0.85), (2025, 5, 0.90), (2025, 6, 0.95),
    (2025, 7, 0.90), (2025, 8, 1.00), (2025, 9, 1.25),
    (2025, 10, 1.10), (2025, 11, 1.45), (2025, 12, 1.55),
    (2026, 1, 1.05), (2026, 2, 1.10), (2026, 3, 0.90),
    (2026, 4, 0.85), (2026, 5, 0.90), (2026, 6, 0.95),
    (2026, 7, 0.90), (2026, 8, 1.00), (2026, 9, 1.30),
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rebuild deterministic development data for the dashboard."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--small", action="store_true", help="Load the compact learning dataset.")
    mode.add_argument("--full", action="store_true", help="Load the interview demo dataset.")
    return parser.parse_args()


def verify_schema(connection):
    existing_tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    missing_tables = set(TABLES) - existing_tables
    if missing_tables:
        missing = ", ".join(sorted(missing_tables))
        raise RuntimeError(f"Database schema is missing tables: {missing}")

    trigger = connection.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type = 'trigger'
          AND name = 'max_two_promotions_per_purchase'
        """
    ).fetchone()
    if not trigger:
        raise RuntimeError("The maximum-two-promotions trigger is missing")


def clear_seed_data(connection):
    for table in SEED_DELETE_ORDER:
        connection.execute(f"DELETE FROM {table}")

    # Reset only emptied seed-table counters so IDs remain reproducible.
    connection.executemany(
        "DELETE FROM sqlite_sequence WHERE name = ?",
        ((table,) for table in SEED_DELETE_ORDER),
    )


def insert_manufacturers(connection, rows):
    connection.executemany(
        """
        INSERT INTO manufacturer (manufacturer_id, name, country, website)
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )


def insert_phones(connection, rows):
    connection.executemany(
        """
        INSERT INTO phone (
            phone_id, manufacturer_id, model_name, release_date,
            storage_gb, ram_gb, launch_price, operating_system,
            image_path, is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def seed_small(connection):
    manufacturers = (
        (1, "Apple", "United States", "https://www.apple.com"),
        (2, "Samsung", "South Korea", "https://www.samsung.com"),
    )
    phones = (
        (1, 1, "iPhone 15", "2023-09-22", 128, 6, 799.00, "iOS", "phones/iphone-15.jpg", 1),
        (2, 1, "iPhone 15 Pro", "2023-09-22", 256, 8, 1099.00, "iOS", "phones/iphone-15-pro.jpg", 1),
        (3, 2, "Galaxy S24", "2024-01-31", 128, 8, 799.99, "Android", "phones/galaxy-s24.jpg", 1),
        (4, 2, "Galaxy S24 Ultra", "2024-01-31", 256, 12, 1299.99, "Android", "phones/galaxy-s24-ultra.jpg", 1),
    )
    users = (
        (1, "Olivia", "Carter", "1992-04-18", "Female", "Product Manager", "$100,000-$149,999", "2024-09-01 09:00:00"),
        (2, "Ethan", "Brooks", "1987-11-03", "Male", "Software Engineer", "$150,000-$199,999", "2024-09-01 09:00:00"),
        (3, "Maya", "Patel", "1998-07-26", "Female", "Financial Analyst", "$75,000-$99,999", "2024-09-01 09:00:00"),
    )
    contacts = (
        (1, 1, "olivia.carter@example.com", "+1-212-555-0101", "125 Hudson Street", "New York", "NY", "10013", "United States"),
        (2, 2, "ethan.brooks@example.com", "+1-415-555-0102", "480 Market Street", "San Francisco", "CA", "94105", "United States"),
        (3, 3, "maya.patel@example.com", "+1-312-555-0103", "210 West Adams Street", "Chicago", "IL", "60606", "United States"),
    )
    promotions = (
        (1, 1, "APPLE100", "Apple $100 Savings", "FIXED", 100.00, "2025-01-01", "2025-03-31", "Save $100 on iPhone 15.", 1),
        (2, 1, "APPLE10", "Apple 10% Special", "PERCENTAGE", 10.00, "2025-02-01", "2025-02-28", "Ten percent off iPhone 15.", 1),
        (3, 3, "SAMSUNG15", "Galaxy S24 15% Off", "PERCENTAGE", 15.00, "2025-03-01", "2025-08-31", "Fifteen percent off Galaxy S24.", 1),
        (4, 4, "ULTRA150", "Ultra $150 Savings", "FIXED", 150.00, "2025-05-01", "2025-12-31", "Save $150 on Galaxy S24 Ultra.", 1),
    )
    purchases = (
        (1, 1, 1, "2025-02-14", 619.10, 1, "PRIMARY"),
        (2, 1, 3, "2025-07-10", 679.99, 1, "SECONDARY"),
        (3, 1, 4, "2024-11-22", 1249.99, 1, "PREVIOUS"),
        (4, 2, 3, "2025-03-20", 679.99, 1, "PRIMARY"),
        (5, 2, 2, "2025-06-05", 999.00, 1, "SECONDARY"),
        (6, 2, 1, "2025-08-02", 749.00, 1, "RETURNED"),
        (7, 3, 4, "2025-05-18", 1149.99, 2, "PRIMARY"),
        (8, 3, 1, "2024-12-12", 699.00, 1, "TRADED_IN"),
    )
    purchase_promotions = (
        (1, 1, 1, 100.00),
        (2, 1, 2, 79.90),
        (3, 2, 3, 120.00),
        (4, 7, 4, 150.00),
    )

    insert_manufacturers(connection, manufacturers)
    insert_phones(connection, phones)
    connection.executemany(
        """
        INSERT INTO user (
            user_id, first_name, last_name, date_of_birth, gender,
            occupation, income_range, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        users,
    )
    connection.executemany(
        """
        INSERT INTO user_contact (
            contact_id, user_id, email, phone_number, street,
            city, state, zip_code, country
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        contacts,
    )
    connection.executemany(
        """
        INSERT INTO promotion (
            promotion_id, phone_id, promo_code, promo_name, discount_type,
            discount_value, start_date, end_date, description, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        promotions,
    )
    connection.executemany(
        """
        INSERT INTO purchase (
            purchase_id, user_id, phone_id, purchase_date,
            sale_price, quantity, phone_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        purchases,
    )
    connection.executemany(
        """
        INSERT INTO purchase_promotion (
            purchase_promo_id, purchase_id, promotion_id, discount_amount
        ) VALUES (?, ?, ?, ?)
        """,
        purchase_promotions,
    )


def full_phone_catalog():
    manufacturer_ids = {row[1]: row[0] for row in FULL_MANUFACTURERS}
    catalog = []
    for phone_id, spec in enumerate(FULL_PHONE_SPECS, start=1):
        key, manufacturer, model, release, storage, ram, price, os_name, tier, weight = spec
        catalog.append(
            {
                "phone_id": phone_id,
                "key": key,
                "manufacturer": manufacturer,
                "manufacturer_id": manufacturer_ids[manufacturer],
                "model": model,
                "release": release,
                "release_date": date.fromisoformat(release),
                "storage": storage,
                "ram": ram,
                "price": price,
                "os": os_name,
                "tier": tier,
                "weight": weight,
            }
        )
    return catalog


def build_full_promotions(phone_catalog):
    rows = []
    by_phone = {phone["phone_id"]: [] for phone in phone_catalog}
    promotion_id = 1

    for phone in phone_catalog:
        if phone["tier"] == "premium":
            discount_type, discount_value = "FIXED", 100.00
        elif phone["tier"] == "mainstream":
            discount_type, discount_value = "PERCENTAGE", 10.00
        elif phone["tier"] == "midrange":
            discount_type, discount_value = "PERCENTAGE", 8.00
        else:
            discount_type, discount_value = "FIXED", 30.00

        start = max(HISTORY_START, phone["release_date"])
        code_root = phone["key"].upper()
        primary = {
            "promotion_id": promotion_id,
            "promo_code": f"{code_root}_UPGRADE",
            "discount_type": discount_type,
            "discount_value": discount_value,
            "start": start,
            "end": HISTORY_END,
            "popularity": 1.0,
        }
        rows.append(
            (
                promotion_id,
                phone["phone_id"],
                primary["promo_code"],
                f"{phone['model']} Upgrade Offer",
                discount_type,
                discount_value,
                start.isoformat(),
                HISTORY_END.isoformat(),
                f"Demo upgrade savings for {phone['model']}.",
                1,
            )
        )
        by_phone[phone["phone_id"]].append(primary)
        promotion_id += 1

        if phone["key"] in SECOND_PROMOTION_PHONE_KEYS:
            loyalty_value = {
                "premium": 75.00,
                "mainstream": 50.00,
                "midrange": 35.00,
                "budget": 25.00,
            }[phone["tier"]]
            loyalty_start = max(start, date(2025, 1, 1))
            secondary = {
                "promotion_id": promotion_id,
                "promo_code": f"{code_root}_LOYALTY",
                "discount_type": "FIXED",
                "discount_value": loyalty_value,
                "start": loyalty_start,
                "end": HISTORY_END,
                "popularity": 0.35,
            }
            rows.append(
                (
                    promotion_id,
                    phone["phone_id"],
                    secondary["promo_code"],
                    f"{phone['model']} Loyalty Bonus",
                    "FIXED",
                    loyalty_value,
                    loyalty_start.isoformat(),
                    HISTORY_END.isoformat(),
                    f"Additional loyalty savings for {phone['model']}.",
                    1,
                )
            )
            by_phone[phone["phone_id"]].append(secondary)
            promotion_id += 1

    return rows, by_phone


def choose_location(rng):
    return rng.choices(LOCATIONS, weights=[row[4] for row in LOCATIONS], k=1)[0]


def choose_occupation_and_income(rng):
    occupation = rng.choices(
        OCCUPATIONS,
        weights=[row[3] for row in OCCUPATIONS],
        k=1,
    )[0]
    income = rng.choices(occupation[1], weights=occupation[2], k=1)[0]
    return occupation[0], income


def random_birth_date(rng):
    birth_year = round(rng.triangular(1954, 2005, 1990))
    birth_month = rng.randint(1, 12)
    last_day = calendar.monthrange(birth_year, birth_month)[1]
    return date(birth_year, birth_month, rng.randint(1, last_day))


def random_purchase_date(rng):
    year, month, _ = rng.choices(
        MONTH_WEIGHTS,
        weights=[row[2] for row in MONTH_WEIGHTS],
        k=1,
    )[0]
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, rng.randint(1, last_day))


def purchase_dates_for_customer(rng, purchase_count):
    dates = set()
    while len(dates) < purchase_count:
        dates.add(random_purchase_date(rng))
    return sorted(dates)


def months_since(release_date, purchase_date):
    return max(
        0,
        (purchase_date.year - release_date.year) * 12
        + purchase_date.month
        - release_date.month,
    )


def demand_weight(phone, purchase_date):
    age_months = months_since(phone["release_date"], purchase_date)
    if age_months < 3:
        recency_factor = 1.30
    elif age_months < 9:
        recency_factor = 1.12
    elif age_months > 20:
        recency_factor = 0.82
    else:
        recency_factor = 1.0
    return phone["weight"] * recency_factor


def weighted_phone_choice(rng, phones, purchase_date):
    return rng.choices(
        phones,
        weights=[demand_weight(phone, purchase_date) for phone in phones],
        k=1,
    )[0]


def choose_phone(rng, phone_catalog, purchase_date, previous_phone):
    available = [
        phone for phone in phone_catalog
        if phone["release_date"] <= purchase_date
    ]
    if previous_phone is None:
        return weighted_phone_choice(rng, available, purchase_date)

    behavior = rng.random()
    if behavior < 0.18:
        return previous_phone
    if behavior < 0.60:
        same_brand = [
            phone for phone in available
            if phone["manufacturer"] == previous_phone["manufacturer"]
        ]
        return weighted_phone_choice(rng, same_brand, purchase_date)

    other_brands = [
        phone for phone in available
        if phone["manufacturer"] != previous_phone["manufacturer"]
    ]
    return weighted_phone_choice(rng, other_brands, purchase_date)


def base_sale_price(rng, phone, purchase_date):
    age_months = months_since(phone["release_date"], purchase_date)
    base_rate, monthly_rate, maximum_rate = {
        "premium": (0.01, 0.004, 0.12),
        "mainstream": (0.02, 0.006, 0.20),
        "midrange": (0.03, 0.007, 0.24),
        "budget": (0.04, 0.008, 0.28),
    }[phone["tier"]]
    discount_rate = min(maximum_rate, base_rate + age_months * monthly_rate)
    discount_rate += rng.uniform(-0.012, 0.012)
    discount_rate = min(max(discount_rate, 0), maximum_rate)
    return round(phone["price"] * (1 - discount_rate), 2)


def choose_promotions(rng, promotions, purchase_date):
    eligible = [
        promotion for promotion in promotions
        if promotion["start"] <= purchase_date <= promotion["end"]
    ]
    if not eligible:
        return []

    usage_roll = rng.random()
    if usage_roll < 0.68:
        return []
    if usage_roll < 0.95 or len(eligible) == 1:
        return rng.choices(
            eligible,
            weights=[promotion["popularity"] for promotion in eligible],
            k=1,
        )
    return eligible[:2]


def apply_promotions(base_price, quantity, promotions):
    current_price = base_price
    applied = []
    for promotion in promotions:
        if promotion["discount_type"] == "PERCENTAGE":
            per_unit_discount = current_price * promotion["discount_value"] / 100
        else:
            per_unit_discount = promotion["discount_value"]

        # A single offer cannot consume more than 25% of the remaining price.
        per_unit_discount = round(min(per_unit_discount, current_price * 0.25), 2)
        current_price = round(current_price - per_unit_discount, 2)
        applied.append(
            (promotion["promotion_id"], round(per_unit_discount * quantity, 2))
        )
    return current_price, applied


def choose_phone_status(rng, purchase_number):
    weights = (70, 14, 8, 4, 4) if purchase_number == 0 else (48, 23, 14, 5, 10)
    return rng.choices(PHONE_STATUSES, weights=weights, k=1)[0]


def build_full_dataset():
    rng = random.Random(RANDOM_SEED)
    phone_catalog = full_phone_catalog()
    promotions, promotions_by_phone = build_full_promotions(phone_catalog)
    manufacturer_ids = {row[1]: row[0] for row in FULL_MANUFACTURERS}
    phone_rows = [
        (
            phone["phone_id"],
            manufacturer_ids[phone["manufacturer"]],
            phone["model"],
            phone["release"],
            phone["storage"],
            phone["ram"],
            phone["price"],
            phone["os"],
            f"phones/{phone['key'].replace('_', '-')}.jpg",
            1,
        )
        for phone in phone_catalog
    ]

    # 2,700 x 1 + 1,700 x 2 + 500 x 3 + 100 x 4 = 8,000 purchases.
    purchase_counts = [1] * 2700 + [2] * 1700 + [3] * 500 + [4] * 100
    rng.shuffle(purchase_counts)

    user_rows = []
    contact_rows = []
    purchase_rows = []
    purchase_promotion_rows = []
    purchase_id = 1
    purchase_promo_id = 1

    for user_id, purchase_count in enumerate(purchase_counts, start=1):
        purchase_dates = purchase_dates_for_customer(rng, purchase_count)
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)
        birth_date = random_birth_date(rng)
        gender = rng.choices(
            ("Female", "Male", "Non-binary", "Prefer not to say"),
            weights=(48, 47, 3, 2),
            k=1,
        )[0]
        occupation, income_range = choose_occupation_and_income(rng)
        created_date = purchase_dates[0] - timedelta(days=rng.randint(1, 240))
        user_rows.append(
            (
                user_id,
                first_name,
                last_name,
                birth_date.isoformat(),
                gender,
                occupation,
                income_range,
                f"{created_date.isoformat()} 09:00:00",
            )
        )

        city, state, zip_code, area_code, _ = choose_location(rng)
        email = f"{first_name.lower()}.{last_name.lower()}.{user_id:04d}@example.com"
        phone_number = f"+1-{area_code}-555-{user_id:04d}"
        street_number = 100 + (user_id * 37) % 9800
        contact_rows.append(
            (
                user_id,
                user_id,
                email,
                phone_number,
                f"{street_number} {rng.choice(STREET_NAMES)}",
                city,
                state,
                zip_code,
                "United States",
            )
        )

        previous_phone = None
        for purchase_number, purchase_date in enumerate(purchase_dates):
            phone = choose_phone(rng, phone_catalog, purchase_date, previous_phone)
            quantity = 2 if rng.random() < 0.04 else 1
            selected_promotions = choose_promotions(
                rng,
                promotions_by_phone[phone["phone_id"]],
                purchase_date,
            )
            pre_promotion_price = base_sale_price(rng, phone, purchase_date)
            sale_price, applied_promotions = apply_promotions(
                pre_promotion_price,
                quantity,
                selected_promotions,
            )
            purchase_rows.append(
                (
                    purchase_id,
                    user_id,
                    phone["phone_id"],
                    purchase_date.isoformat(),
                    sale_price,
                    quantity,
                    choose_phone_status(rng, purchase_number),
                )
            )

            for promotion_id, discount_amount in applied_promotions:
                purchase_promotion_rows.append(
                    (purchase_promo_id, purchase_id, promotion_id, discount_amount)
                )
                purchase_promo_id += 1

            purchase_id += 1
            previous_phone = phone

    return {
        "manufacturers": FULL_MANUFACTURERS,
        "phones": phone_rows,
        "users": user_rows,
        "contacts": contact_rows,
        "promotions": promotions,
        "purchases": purchase_rows,
        "purchase_promotions": purchase_promotion_rows,
    }


def insert_full_dataset(connection, dataset):
    insert_manufacturers(connection, dataset["manufacturers"])
    insert_phones(connection, dataset["phones"])
    connection.executemany(
        """
        INSERT INTO user (
            user_id, first_name, last_name, date_of_birth, gender,
            occupation, income_range, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        dataset["users"],
    )
    connection.executemany(
        """
        INSERT INTO user_contact (
            contact_id, user_id, email, phone_number, street,
            city, state, zip_code, country
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        dataset["contacts"],
    )
    connection.executemany(
        """
        INSERT INTO promotion (
            promotion_id, phone_id, promo_code, promo_name, discount_type,
            discount_value, start_date, end_date, description, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        dataset["promotions"],
    )
    connection.executemany(
        """
        INSERT INTO purchase (
            purchase_id, user_id, phone_id, purchase_date,
            sale_price, quantity, phone_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        dataset["purchases"],
    )
    connection.executemany(
        """
        INSERT INTO purchase_promotion (
            purchase_promo_id, purchase_id, promotion_id, discount_amount
        ) VALUES (?, ?, ?, ?)
        """,
        dataset["purchase_promotions"],
    )


def row_counts(connection):
    return {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in TABLES
    }


def validate_data(connection):
    counts = row_counts(connection)
    foreign_key_violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    integrity_result = connection.execute("PRAGMA integrity_check").fetchone()[0]

    users_without_one_contact = connection.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT u.user_id, COUNT(uc.contact_id) AS contact_count
            FROM user AS u
            LEFT JOIN user_contact AS uc ON uc.user_id = u.user_id
            GROUP BY u.user_id
            HAVING contact_count <> 1
        )
        """
    ).fetchone()[0]
    duplicate_emails = connection.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT email FROM user_contact
            WHERE email IS NOT NULL
            GROUP BY email HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]
    invalid_statuses = connection.execute(
        """
        SELECT COUNT(*) FROM purchase
        WHERE phone_status NOT IN (
            'PRIMARY', 'SECONDARY', 'PREVIOUS', 'RETURNED', 'TRADED_IN'
        )
        """
    ).fetchone()[0]
    purchases_over_promotion_limit = connection.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT purchase_id FROM purchase_promotion
            GROUP BY purchase_id HAVING COUNT(*) > 2
        )
        """
    ).fetchone()[0]
    promotion_distribution = dict(
        connection.execute(
            """
            SELECT promotion_count, COUNT(*) FROM (
                SELECT p.purchase_id, COUNT(pp.purchase_promo_id) AS promotion_count
                FROM purchase AS p
                LEFT JOIN purchase_promotion AS pp ON pp.purchase_id = p.purchase_id
                GROUP BY p.purchase_id
            ) GROUP BY promotion_count
            """
        ).fetchall()
    )
    quantity_two = connection.execute(
        "SELECT COUNT(*) FROM purchase WHERE quantity = 2"
    ).fetchone()[0]
    repeat_customers = connection.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT user_id FROM purchase
            GROUP BY user_id HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]
    multi_phone_customers = connection.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT user_id FROM purchase
            GROUP BY user_id HAVING COUNT(DISTINCT phone_id) > 1
        )
        """
    ).fetchone()[0]
    multi_manufacturer_customers = connection.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT p.user_id
            FROM purchase AS p
            JOIN phone AS ph ON ph.phone_id = p.phone_id
            GROUP BY p.user_id
            HAVING COUNT(DISTINCT ph.manufacturer_id) > 1
        )
        """
    ).fetchone()[0]
    mismatched_promotions = connection.execute(
        """
        SELECT COUNT(*)
        FROM purchase_promotion AS pp
        JOIN purchase AS p ON p.purchase_id = pp.purchase_id
        JOIN promotion AS pr ON pr.promotion_id = pp.promotion_id
        WHERE p.phone_id <> pr.phone_id
        """
    ).fetchone()[0]

    problems = []
    if foreign_key_violations:
        problems.append("foreign-key violations exist")
    if integrity_result != "ok":
        problems.append(f"integrity check returned {integrity_result!r}")
    if users_without_one_contact:
        problems.append("not every user has exactly one contact")
    if duplicate_emails:
        problems.append("duplicate contact emails exist")
    if invalid_statuses:
        problems.append("invalid phone statuses exist")
    if purchases_over_promotion_limit:
        problems.append("a purchase has more than two promotions")
    if any(promotion_distribution.get(count, 0) == 0 for count in (0, 1, 2)):
        problems.append("promotion distribution is missing zero, one, or two uses")
    if quantity_two == 0:
        problems.append("no quantity-two purchases exist")
    if repeat_customers == 0:
        problems.append("no repeat customers exist")
    if multi_phone_customers == 0:
        problems.append("no multi-phone customers exist")
    if multi_manufacturer_customers == 0:
        problems.append("no multi-manufacturer customers exist")
    if mismatched_promotions:
        problems.append("a promotion is attached to the wrong phone")
    if problems:
        raise RuntimeError("; ".join(problems))

    return {
        "counts": counts,
        "foreign_key_violations": len(foreign_key_violations),
        "integrity_result": integrity_result,
        "promotion_distribution": promotion_distribution,
        "quantity_two": quantity_two,
        "repeat_customers": repeat_customers,
        "multi_phone_customers": multi_phone_customers,
        "multi_manufacturer_customers": multi_manufacturer_customers,
    }


def rebuild_seed_data(mode):
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        verify_schema(connection)
        connection.execute("BEGIN IMMEDIATE")
        clear_seed_data(connection)

        if mode == "small":
            seed_small(connection)
        else:
            insert_full_dataset(connection, build_full_dataset())

        validation = validate_data(connection)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    print(f"{mode.capitalize()} seed data is ready in {DATABASE_PATH}")
    for table in TABLES:
        print(f"{table}: {validation['counts'][table]}")
    print(f"foreign_key_violations: {validation['foreign_key_violations']}")
    print(f"integrity_check: {validation['integrity_result']}")


def main():
    args = parse_args()
    rebuild_seed_data("small" if args.small else "full")


if __name__ == "__main__":
    main()
