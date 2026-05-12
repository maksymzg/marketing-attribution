"""
Generator: products table.

Generates ~70 synthetic SKUs across 7 categories for PLSygnet.pl catalog.
Output: data/raw/products.csv

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
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "products.csv"

# Categories matching the CHECK constraint in sql/schema.sql
CATEGORIES = [
    "signet_rings",
    "bracelets",
    "necklaces",
    "rings",
    "watches",
    "earrings",
    "suit_accessories",
]

# SKU prefix per category (3 letters)
SKU_PREFIX = {
    "signet_rings": "SIG",
    "bracelets": "BRA",
    "necklaces": "NEC",
    "rings": "RIN",
    "watches": "WAT",
    "earrings": "EAR",
    "suit_accessories": "SUI",
}

# Price ranges per category: (min_cost_pln, max_cost_pln, markup_min, markup_max)
# Markup = multiplier from cost to selling price (e.g. 2.5 means selling = cost × 2.5)
PRICE_CONFIG = {
    "signet_rings":     (80, 350, 2.5, 3.5),
    "bracelets":        (60, 250, 2.4, 3.2),
    "necklaces":        (90, 400, 2.5, 3.5),
    "rings":            (50, 200, 2.5, 3.5),
    "watches":          (200, 1500, 2.0, 2.8),
    "earrings":         (40, 180, 2.6, 3.6),
    "suit_accessories": (40, 200, 2.8, 4.0),
}

# Number of SKUs per category
SKUS_PER_CATEGORY = 10

def generate_products() -> pd.DataFrame:
    """
    Generate the full product catalog.

    Returns a DataFrame with 70 SKUs (10 per category × 7 categories).
    """
    rows = []

    for category in CATEGORIES:
        prefix = SKU_PREFIX[category]
        min_cost, max_cost, markup_min, markup_max = PRICE_CONFIG[category]

        for i in range(1, SKUS_PER_CATEGORY + 1):
            sku = f"{prefix}-{i:03d}"

            cost = round(random.uniform(min_cost, max_cost), 2)
            markup = random.uniform(markup_min, markup_max)
            selling_price = round(cost * markup, 2)

            rows.append({
                "sku": sku,
                "name": f"{prefix} product {i}",
                "category": category,
                "selling_price_pln": selling_price,
                "cost_price_pln": cost,
                "is_active": True,
            })

    return pd.DataFrame(rows)

def save_to_csv(df: pd.DataFrame, path: Path) -> None:
    """Save the products DataFrame to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


if __name__ == "__main__":
    print(f"Generating products with random seed {RANDOM_SEED}...")
    df = generate_products()

    print(f"Generated {len(df)} products across {df['category'].nunique()} categories.")

    save_to_csv(df, OUTPUT_PATH)
    print(f"Saved to {OUTPUT_PATH}")