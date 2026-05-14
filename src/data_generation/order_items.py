"""
Generator: order_items table.

Generates line items for each order in orders.csv.
Each order has 1-3 items (weighted: most have 1 item).

Output: data/raw/order_items.csv

Snapshotted unit_price and unit_cost — frozen at time of order,
not linked to current products.selling_price_pln.

Deterministic: uses fixed random seed for reproducibility.
"""

import random
from pathlib import Path

import pandas as pd

# Reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ORDERS_PATH = PROJECT_ROOT / "data" / "raw" / "orders.csv"
PRODUCTS_PATH = PROJECT_ROOT / "data" / "raw" / "products.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "order_items.csv"

# Number of items per order — most orders have 1 item, rarely 2-3
ITEMS_PER_ORDER_WEIGHTS = {
    1: 0.70,
    2: 0.22,
    3: 0.08,
}

# Price variance — snapshotted price can vary ±5% from current catalog price
# Simulates discounts, price changes over time
PRICE_VARIANCE = 0.05

def load_orders() -> pd.DataFrame:
    """Load orders.csv with order_id assigned 1..N (matches PostgreSQL SERIAL)."""
    if not ORDERS_PATH.exists():
        raise FileNotFoundError(
            f"orders.csv not found at {ORDERS_PATH}. Run orders.py first."
        )
    
    df = pd.read_csv(ORDERS_PATH, parse_dates=["order_date"])
    df["order_id"] = range(1, len(df) + 1)
    return df


def load_products() -> pd.DataFrame:
    """Load products.csv with product_id assigned 1..N (matches PostgreSQL SERIAL)."""
    if not PRODUCTS_PATH.exists():
        raise FileNotFoundError(
            f"products.csv not found at {PRODUCTS_PATH}. Run products.py first."
        )
    
    df = pd.read_csv(PRODUCTS_PATH)
    df["product_id"] = range(1, len(df) + 1)
    return df


def weighted_choice_int(weights: dict[int, float]) -> int:
    """Pick an integer key from a weighted distribution."""
    return random.choices(
        population=list(weights.keys()),
        weights=list(weights.values()),
        k=1,
    )[0]

def generate_order_items() -> pd.DataFrame:
    """
    Generate order line items.
    
    For each order:
      1. Determine how many items (1-3) using weighted distribution
      2. Sample unique products (no duplicates within an order)
      3. Snapshot unit_price and unit_cost with ±PRICE_VARIANCE
    """
    orders = load_orders()
    products = load_products()
    
    rows = []
    
    for _, order in orders.iterrows():
        num_items = weighted_choice_int(ITEMS_PER_ORDER_WEIGHTS)
        
        # Sample unique products for this order (no duplicates)
        sampled_products = products.sample(n=num_items, replace=False)
        
        for _, product in sampled_products.iterrows():
            # Snapshot prices with ±5% variance (simulates discounts / price changes over time)
            price_multiplier = 1 + random.uniform(-PRICE_VARIANCE, PRICE_VARIANCE)
            unit_price = round(product["selling_price_pln"] * price_multiplier, 2)
            unit_cost = round(product["cost_price_pln"] * price_multiplier, 2)
            
            # Quantity — almost always 1 for jewelry, occasionally 2
            quantity = 1 if random.random() < 0.95 else 2
            
            rows.append({
                "order_id": int(order["order_id"]),
                "product_id": int(product["product_id"]),
                "quantity": quantity,
                "unit_price": unit_price,
                "unit_cost": unit_cost,
            })
    
    return pd.DataFrame(rows)

def save_to_csv(df: pd.DataFrame, path: Path) -> None:
    """Save the order_items DataFrame to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


if __name__ == "__main__":
    print("Generating order items...")
    df = generate_order_items()
    
    print(f"Generated {len(df)} order items across {df['order_id'].nunique()} orders.")
    print(f"Total line revenue: PLN {(df['unit_price'] * df['quantity']).sum():,.2f}")
    print(f"Total line cost: PLN {(df['unit_cost'] * df['quantity']).sum():,.2f}")
    
    items_per_order = df.groupby("order_id").size().value_counts().sort_index()
    print(f"\nItems per order distribution:")
    print(items_per_order.to_string())
    
    save_to_csv(df, OUTPUT_PATH)
    print(f"\nSaved to {OUTPUT_PATH}")