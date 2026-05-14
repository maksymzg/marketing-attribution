"""
Generator: marketing_touchpoints table.

Generates customer journey events — clicks, impressions, page views,
email opens, promo code redemptions. Each customer has multiple touchpoints
before purchase (and some after).

Output: data/raw/marketing_touchpoints.csv

Expected size: ~500k+ rows (largest table in the project).
Deterministic: uses fixed random seed for reproducibility.
"""

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
ORDERS_PATH = PROJECT_ROOT / "data" / "raw" / "orders.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "marketing_touchpoints.csv"

# Time period
END_DATE = date(2025, 12, 31)

# Average touchpoints per customer (before any purchase)
# Most customers have 3-10 touchpoints before converting
TOUCHPOINTS_MIN = 3
TOUCHPOINTS_MAX = 20
# Touchpoint type distribution — what % of touchpoints are each type
# Higher-funnel events (impressions) more common than lower-funnel (conversions)
TOUCHPOINT_TYPE_WEIGHTS = {
    "impression":            0.45,   # Most common — passive view of an ad
    "click":                 0.25,   # Less common — active engagement
    "page_view":             0.15,   # Came to the site (organic or direct)
    "email_open":            0.08,
    "email_click":           0.05,
    "promo_code_redemption": 0.02,   # Rare — conversion event
}

# Channel-touchpoint compatibility — which channels can produce which touchpoint types
# E.g., "email_open" can only come from "email" channel
VALID_TOUCHPOINTS_PER_CHANNEL = {
    "google_ads":    ["impression", "click", "page_view"],
    "meta_ads":      ["impression", "click", "page_view"],
    "tiktok_ads":    ["impression", "click", "page_view"],
    "influencer_ig": ["impression", "click", "page_view", "promo_code_redemption"],
    "email":         ["email_open", "email_click"],
    "outdoor":       ["impression", "promo_code_redemption"],
}

# Channel mix — % of customer's touchpoints from their acquisition_channel vs other channels
# Even if Marek was acquired via Google, he may also see Meta ads and emails
PRIMARY_CHANNEL_RATIO = 0.60   # 60% touchpoints from acquisition channel
SECONDARY_CHANNELS_RATIO = 0.40  # 40% from other channels


def weighted_choice(weights: dict[str, float]) -> str:
    """Pick a key from a weighted distribution."""
    return random.choices(
        population=list(weights.keys()),
        weights=list(weights.values()),
        k=1,
    )[0]

def load_customers() -> pd.DataFrame:
    """Load customers.csv with customer_id assigned 1..N."""
    if not CUSTOMERS_PATH.exists():
        raise FileNotFoundError(
            f"customers.csv not found at {CUSTOMERS_PATH}. Run customers.py first."
        )
    
    df = pd.read_csv(CUSTOMERS_PATH, parse_dates=["acquired_at"])
    df["customer_id"] = range(1, len(df) + 1)
    return df


def load_orders() -> pd.DataFrame:
    """Load orders.csv with order_id assigned 1..N."""
    if not ORDERS_PATH.exists():
        raise FileNotFoundError(
            f"orders.csv not found at {ORDERS_PATH}. Run orders.py first."
        )
    
    df = pd.read_csv(ORDERS_PATH, parse_dates=["order_date"])
    df["order_id"] = range(1, len(df) + 1)
    return df


def pick_channel_for_touchpoint(primary_channel: str, all_channels: list[str]) -> str:
    """
    Pick a channel for a touchpoint.
    
    60% chance to use primary (acquisition) channel, 40% chance other random channel.
    """
    if random.random() < PRIMARY_CHANNEL_RATIO:
        return primary_channel
    
    # Pick a random other channel
    other_channels = [c for c in all_channels if c != primary_channel]
    return random.choice(other_channels)


def random_timestamp_between(start: datetime, end: datetime) -> datetime:
    """Generate a random datetime between start and end (inclusive)."""
    delta = end - start
    delta_seconds = int(delta.total_seconds())
    if delta_seconds <= 0:
        return start
    random_seconds = random.randint(0, delta_seconds)
    return start + timedelta(seconds=random_seconds)

# All marketing channels
ALL_CHANNELS = list(VALID_TOUCHPOINTS_PER_CHANNEL.keys())


def generate_journey_for_customer(
    customer: pd.Series,
    customer_orders: pd.DataFrame,
) -> list[dict]:
    """
    Generate marketing touchpoints for one customer.
    
    Logic:
    1. Determine number of touchpoints (3-20 random)
    2. Generate touchpoints between acquired_at and END_DATE
    3. Mix channels (60% primary, 40% other)
    4. Pick touchpoint_type matching the channel
    5. Link promo_code_redemption to actual orders (if customer used promo code)
    """
    touchpoints = []
    
    primary_channel = customer["acquisition_channel"]
    customer_id = int(customer["customer_id"])
    
    # Date range for touchpoints
    acquired_at = customer["acquired_at"].to_pydatetime()
    end_datetime = datetime.combine(END_DATE, datetime.max.time())
    
    # Step 1: Number of touchpoints
    num_touchpoints = random.randint(TOUCHPOINTS_MIN, TOUCHPOINTS_MAX)
    
    # Step 2: Generate regular touchpoints (impressions, clicks, etc.)
    for _ in range(num_touchpoints):
        # Pick channel (primary or other)
        channel = pick_channel_for_touchpoint(primary_channel, ALL_CHANNELS)
        
        # Pick a valid touchpoint type for that channel
        valid_types = VALID_TOUCHPOINTS_PER_CHANNEL[channel]
        # Filter type weights to only valid types for this channel
        filtered_weights = {
            t: TOUCHPOINT_TYPE_WEIGHTS[t]
            for t in valid_types
            if t != "promo_code_redemption"  # Handled separately below
        }
        
        if not filtered_weights:
            continue  # Edge case: channel only has promo_code_redemption (shouldn't happen but safe)
        
        touchpoint_type = weighted_choice(filtered_weights)
        
        timestamp = random_timestamp_between(acquired_at, end_datetime)
        
        touchpoints.append({
            "customer_id": customer_id,
            "timestamp": timestamp,
            "channel": channel,
            "campaign": "unknown",  # Simplified — could be linked to marketing_spend.campaign
            "touchpoint_type": touchpoint_type,
            "order_id": None,
        })
    
    # Step 3: Add promo_code_redemption touchpoints for orders WITH promo_code
    orders_with_promo = customer_orders[customer_orders["promo_code"].notna()]
    
    for _, order in orders_with_promo.iterrows():
        # Determine channel based on promo code
        promo_code = order["promo_code"]
        if promo_code == "WAW20":
            channel = "outdoor"
        else:
            channel = "influencer_ig"
        
        # Redemption happens AT the order timestamp (or just before)
        order_dt = order["order_date"].to_pydatetime()
        # Touchpoint timestamp = order_date minus 0-2 minutes (realistic — click → buy in seconds)
        redemption_time = order_dt - timedelta(minutes=random.randint(0, 2))
        
        touchpoints.append({
            "customer_id": customer_id,
            "timestamp": redemption_time,
            "channel": channel,
            "campaign": "promo_code",
            "touchpoint_type": "promo_code_redemption",
            "order_id": int(order["order_id"]),
        })
    
    return touchpoints

def generate_marketing_touchpoints() -> pd.DataFrame:
    """
    Generate marketing touchpoints for ALL customers.
    
    For each customer:
      1. Get their orders
      2. Generate journey (random + promo redemptions)
      3. Add to global list
    
    Returns aggregated DataFrame sorted by timestamp.
    """
    customers = load_customers()
    orders = load_orders()
    
    # Group orders by customer for fast lookup
    orders_by_customer = {
        customer_id: group
        for customer_id, group in orders.groupby("customer_id")
    }
    
    all_touchpoints = []
    
    for idx, customer in customers.iterrows():
        customer_id = int(customer["customer_id"])
        
        # Get this customer's orders (empty DataFrame if none)
        customer_orders = orders_by_customer.get(customer_id, orders.iloc[0:0])
        
        journey = generate_journey_for_customer(customer, customer_orders)
        all_touchpoints.extend(journey)
        
        # Progress logging every 1000 customers
        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1} / {len(customers)} customers, {len(all_touchpoints)} touchpoints so far...")
    
    df = pd.DataFrame(all_touchpoints)
    df = df.sort_values("timestamp").reset_index(drop=True)
    
    return df


def save_to_csv(df: pd.DataFrame, path: Path) -> None:
    """Save the marketing_touchpoints DataFrame to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


if __name__ == "__main__":
    print("Generating marketing touchpoints...")
    df = generate_marketing_touchpoints()
    
    print(f"\nGenerated {len(df)} touchpoints across {df['customer_id'].nunique()} customers.")
    print(f"\nTouchpoint type distribution:")
    print(df["touchpoint_type"].value_counts(normalize=True).round(3).to_string())
    print(f"\nChannel distribution:")
    print(df["channel"].value_counts(normalize=True).round(3).to_string())
    print(f"\nRedemption touchpoints linked to orders: {df['order_id'].notna().sum()}")
    
    save_to_csv(df, OUTPUT_PATH)
    print(f"\nSaved to {OUTPUT_PATH}")