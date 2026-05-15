"""
ETL: Load synthetic data from CSV files to PostgreSQL.

Reads 6 CSV files from data/raw/ and loads them to the plsygnet_attribution
database using PostgreSQL's COPY command (bulk insert).

Tables loaded in FK dependency order:
  1. customers       (no FK)
  2. products        (no FK)
  3. orders          (FK to customers)
  4. order_items     (FK to orders + products)
  5. marketing_spend (no FK)
  6. marketing_touchpoints (FK to customers + orders)

Idempotent: truncates tables before loading (safe to re-run).
"""

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Database connection parameters (loaded from .env)
DB_CONFIG = {
    "host":     os.environ["DB_HOST"],
    "port":     os.environ["DB_PORT"],
    "database": os.environ["DB_NAME"],
    "user":     os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
}

# Tables in FK dependency order (load order)
# IMPORTANT: don't change order — would violate foreign keys
TABLES_IN_ORDER = [
    "customers",
    "products",
    "orders",
    "order_items",
    "marketing_spend",
    "marketing_touchpoints",
]

# Columns to load per table (excludes auto-generated columns: id, created_at)
COLUMNS_PER_TABLE = {
    "customers": [
        "first_name", "last_name", "date_of_birth", "gender",
        "city", "acquisition_channel", "acquired_at", "email",
    ],
    "products": [
        "sku", "name", "category", "selling_price_pln",
        "cost_price_pln", "is_active",
    ],
    "orders": [
        "customer_id", "order_date", "total_amount", "shipping_cost",
        "payment_method", "status", "promo_code", "shipping_city",
    ],
    "order_items": [
        "order_id", "product_id", "quantity", "unit_price", "unit_cost",
    ],
    "marketing_spend": [
        "date", "channel", "campaign", "spend_pln",
    ],
    "marketing_touchpoints": [
        "customer_id", "timestamp", "channel", "campaign",
        "touchpoint_type", "order_id",
    ],
}


def truncate_tables(conn) -> None:
    """
    Truncate all tables in REVERSE FK order (safe deletion).
    
    Using TRUNCATE ... CASCADE handles FK constraints automatically.
    Resets SERIAL sequences to 1.
    """
    cursor = conn.cursor()
    
    # Reverse order — delete children before parents
    for table in reversed(TABLES_IN_ORDER):
        print(f"  Truncating {table}...")
        cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
    
    conn.commit()
    cursor.close()
    print("All tables truncated.")


def load_table_from_csv(conn, table_name: str, csv_path: Path) -> int:
    """
    Load a CSV file into a PostgreSQL table using COPY with explicit columns.
    
    Returns the number of rows inserted.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    
    columns = COLUMNS_PER_TABLE[table_name]
    columns_str = ", ".join(columns)
    
    cursor = conn.cursor()
    
    with open(csv_path, "r", encoding="utf-8") as f:
        cursor.copy_expert(
            sql=f"COPY {table_name} ({columns_str}) FROM STDIN WITH CSV HEADER",
            file=f,
        )
    
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    row_count = cursor.fetchone()[0]
    
    conn.commit()
    cursor.close()
    
    return row_count

def load_all_tables(conn) -> dict[str, int]:
    """
    Load all 6 CSV files into PostgreSQL tables.
    
    Returns dict mapping table_name -> row count loaded.
    """
    results = {}
    
    for table in TABLES_IN_ORDER:
        csv_path = DATA_DIR / f"{table}.csv"
        print(f"  Loading {table} from {csv_path.name}...")
        
        row_count = load_table_from_csv(conn, table, csv_path)
        results[table] = row_count
        
        print(f"    → {row_count:,} rows loaded.")
    
    return results


def verify_loads(conn, expected_results: dict[str, int]) -> None:
    """Print summary of loaded data."""
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("LOAD SUMMARY")
    print("=" * 60)
    
    total = 0
    for table in TABLES_IN_ORDER:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        actual = cursor.fetchone()[0]
        expected = expected_results.get(table, 0)
        status = "✓" if actual == expected else "✗"
        print(f"  {status} {table:<25} {actual:>10,} rows")
        total += actual
    
    print("-" * 60)
    print(f"    TOTAL                     {total:>10,} rows")
    print("=" * 60)
    
    cursor.close()


if __name__ == "__main__":
    print("=" * 60)
    print("PLSygnet ETL: CSV → PostgreSQL")
    print("=" * 60)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        print("Step 1: Truncating tables...")
        truncate_tables(conn)
        print()
        
        print("Step 2: Loading data...")
        results = load_all_tables(conn)
        print()
        
        print("Step 3: Verifying...")
        verify_loads(conn, results)
        
    finally:
        conn.close()
        print("\nConnection closed.")