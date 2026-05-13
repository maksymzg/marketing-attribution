"""
Generator: orders table.

Generates ~30,000 order headers across 5 years (2021-2025).
Reads customers.csv to assign each order to an existing customer.
Output: data/raw/orders.csv

Time period: 2021-01-01 to 2025-12-31.
Deterministic: uses fixed random seed for reproducibility.
"""

import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

# Reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUSTOMERS_PATH = PROJECT_ROOT / "data" / "raw" / "customers.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "orders.csv"

# Configuration
NUM_ORDERS = 30000
START_DATE = date(2021, 1, 1)
END_DATE = date(2025, 12, 31)

def load_customers() -> pd.DataFrame:
    """
    Load customers from CSV.
    
    Returns DataFrame with customer_id (assigned as 1..N based on row order,
    matching PostgreSQL SERIAL auto-increment behavior).
    """
    if not CUSTOMERS_PATH.exists():
        raise FileNotFoundError(
            f"customers.csv not found at {CUSTOMERS_PATH}. "
            f"Run customers.py first."
        )

    df = pd.read_csv(CUSTOMERS_PATH, parse_dates=["date_of_birth", "acquired_at"])
    df["customer_id"] = range(1, len(df) + 1)
    return df

# Payment method distribution (Polish e-commerce reality 2024)
PAYMENT_WEIGHTS = {
    "blik":     0.45,   # Most popular in Poland
    "card":     0.35,
    "transfer": 0.15,
    "cod":      0.05,   # Cash on delivery — niche
}

# Order status distribution
# Most orders are delivered; small % returned, very small % pending
STATUS_WEIGHTS = {
    "delivered": 0.85,
    "returned":  0.07,
    "shipped":   0.04,   # Still in transit (recent orders)
    "paid":      0.03,   # Paid but not yet shipped
    "pending":   0.01,   # Payment in progress
}

# AOV configuration (Average Order Value)
# Log-normal distribution centered around ~390 PLN (per brief)
AOV_MEAN_LOG = 5.85      # exp(5.85) ≈ 347 → with shape it averages ~390
AOV_STD_LOG = 0.5

# Shipping cost — flat fees by tier
SHIPPING_TIERS = [
    {"min_order": 0,    "shipping": 15.00},   # Standard
    {"min_order": 300,  "shipping": 0.00},    # Free above 300 PLN
]


def weighted_choice(weights: dict[str, float]) -> str:
    """Pick a key from a weighted distribution."""
    return random.choices(
        population=list(weights.keys()),
        weights=list(weights.values()),
        k=1,
    )[0]


def generate_order_amount() -> float:
    """Generate a realistic order amount using log-normal distribution."""
    amount = math.exp(random.gauss(AOV_MEAN_LOG, AOV_STD_LOG))
    return round(amount, 2)


def get_shipping_cost(order_amount: float) -> float:
    """Return shipping cost based on order amount tiers."""
    for tier in sorted(SHIPPING_TIERS, key=lambda t: -t["min_order"]):
        if order_amount >= tier["min_order"]:
            return tier["shipping"]
    return SHIPPING_TIERS[0]["shipping"]

def generate_orders() -> pd.DataFrame:
    """
    Generate order headers.
    
    Each order is assigned to an existing customer, with order_date AFTER the
    customer's acquired_at date. Number of orders per customer follows
    weighted distribution (most buy 1-3 times, few buy 10+).
    """
    customers = load_customers()
    
    rows = []
    
    for _ in range(NUM_ORDERS):
        # Sample a random customer (with replacement — customers can buy multiple times)
        customer = customers.sample(n=1).iloc[0]
        
        # Order date must be AFTER customer acquisition date
        days_since_acquired = (END_DATE - customer["acquired_at"].date()).days
        if days_since_acquired <= 0:
            continue  # Edge case: customer acquired on END_DATE
        
        random_days = random.randint(0, days_since_acquired)
        order_date = customer["acquired_at"] + timedelta(days=random_days)
        
        # Add random hours and minutes for realistic timestamp
        order_datetime = datetime.combine(
            order_date.date() if hasattr(order_date, "date") else order_date,
            datetime.min.time()
        ) + timedelta(
            hours=random.randint(8, 22),
            minutes=random.randint(0, 59),
        )
        
        # Order details
        total_amount = generate_order_amount()
        shipping_cost = get_shipping_cost(total_amount)
        payment_method = weighted_choice(PAYMENT_WEIGHTS)
        status = weighted_choice(STATUS_WEIGHTS)
        
        # Promo code logic — match to acquisition channel
        promo_code = None
        if customer["acquisition_channel"] == "outdoor" and random.random() < 0.7:
            promo_code = "WAW20"
        elif customer["acquisition_channel"] == "influencer_ig" and random.random() < 0.4:
            promo_code = random.choice(["JANKOWAL15", "ZOFIA10", "PAWEL10"])
        
        # Shipping city — snapshotted (from customer's city at time of order)
        shipping_city = customer["city"]
        
        rows.append({
            "customer_id": int(customer["customer_id"]),
            "order_date": order_datetime,
            "total_amount": total_amount,
            "shipping_cost": shipping_cost,
            "payment_method": payment_method,
            "status": status,
            "promo_code": promo_code,
            "shipping_city": shipping_city,
        })
    
    return pd.DataFrame(rows)


def save_to_csv(df: pd.DataFrame, path: Path) -> None:
    """Save the orders DataFrame to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


if __name__ == "__main__":
    print(f"Generating {NUM_ORDERS} orders from {START_DATE} to {END_DATE}...")
    df = generate_orders()
    
    print(f"Generated {len(df)} orders.")
    print(f"Total revenue: PLN {df['total_amount'].sum():,.2f}")
    print(f"Average order value: PLN {df['total_amount'].mean():.2f}")
    print(f"\nPromo code usage:")
    print(df["promo_code"].value_counts(dropna=False).to_string())
    
    save_to_csv(df, OUTPUT_PATH)
    print(f"\nSaved to {OUTPUT_PATH}")
