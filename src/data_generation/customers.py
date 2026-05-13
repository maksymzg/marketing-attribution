"""
Generator: customers table.

Generates ~10,000 synthetic customers for PLSygnet.pl.
Output: data/raw/customers.csv

Deterministic: uses fixed random seed for reproducibility.
"""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

# Reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
fake = Faker("pl_PL")  # Polish locale
Faker.seed(RANDOM_SEED)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "customers.csv"

# Configuration
NUM_CUSTOMERS = 10000

# Acquisition channel distribution — match real-world e-commerce patterns
# Total must sum to 1.0
CHANNEL_WEIGHTS = {
    "google_ads":    0.32,   # 32% — most customers come from search
    "meta_ads":      0.24,   # 24% — second-biggest paid channel
    "tiktok_ads":    0.12,   # 12% — younger demographic
    "influencer_ig": 0.14,   # 14% — bigger than expected (high engagement)
    "email":         0.13,   # 13% — owned channel, mostly returning customers
    "outdoor":       0.05,   # 5% — hard to attribute, low conversion
}

# Gender distribution — 80% men (target), 20% women (buying gifts)
GENDER_WEIGHTS = {
    "male":   0.80,
    "female": 0.18,
    "other":  0.02,
}

# Age range (years)
AGE_MIN = 20
AGE_MAX = 45

# Acquisition date range
ACQUIRED_START = date(2021, 1, 1)  # Company founded
ACQUIRED_END = date(2025, 12, 31)  # End of analysis period

def weighted_choice(weights: dict[str, float]) -> str:
    """
    Pick a key from a weighted distribution.
    
    Example: weighted_choice({"a": 0.7, "b": 0.3}) returns "a" ~70% of the time.
    """
    return random.choices(
        population=list(weights.keys()),
        weights=list(weights.values()),
        k=1,
    )[0]


def random_birth_date(min_age: int, max_age: int) -> date:
    """Generate a random birth date so that the person's age is in [min_age, max_age]."""
    today = date.today()
    earliest = today - timedelta(days=max_age * 365 + 365)
    latest = today - timedelta(days=min_age * 365)
    days_range = (latest - earliest).days
    return earliest + timedelta(days=random.randint(0, days_range))


def random_acquired_date(start: date, end: date) -> date:
    """Generate a random date between start and end (inclusive)."""
    days_range = (end - start).days
    return start + timedelta(days=random.randint(0, days_range))

def generate_customers(num_customers: int = NUM_CUSTOMERS) -> pd.DataFrame:
    """
    Generate the full customer dataset.

    Returns a DataFrame with num_customers rows, each representing one customer.
    """
    rows = []
    used_emails: set[str] = set()

    for _ in range(num_customers):
        first_name = fake.first_name()
        last_name = fake.last_name()

        # Generate unique email
        email = fake.unique.email()
        used_emails.add(email)

        rows.append({
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": random_birth_date(AGE_MIN, AGE_MAX),
            "gender": weighted_choice(GENDER_WEIGHTS),
            "city": fake.city(),
            "acquisition_channel": weighted_choice(CHANNEL_WEIGHTS),
            "acquired_at": random_acquired_date(ACQUIRED_START, ACQUIRED_END),
            "email": email,
        })

    return pd.DataFrame(rows)

def save_to_csv(df: pd.DataFrame, path: Path) -> None:
    """Save the customers DataFrame to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


if __name__ == "__main__":
    print(f"Generating {NUM_CUSTOMERS} customers with random seed {RANDOM_SEED}...")
    df = generate_customers()

    print(f"Generated {len(df)} customers.")
    print(f"Channel distribution:")
    print(df["acquisition_channel"].value_counts(normalize=True).round(3).to_string())

    save_to_csv(df, OUTPUT_PATH)
    print(f"\nSaved to {OUTPUT_PATH}")