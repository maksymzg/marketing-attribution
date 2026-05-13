"""
Generator: marketing_spend table.

Generates daily marketing spend across 6 channels and multiple campaigns.
Output: data/raw/marketing_spend.csv

Time period: 2021-01-01 to 2025-12-31 (5 years).
Deterministic: uses fixed random seed for reproducibility.
"""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# Reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "marketing_spend.csv"

# Time period
START_DATE = date(2021, 1, 1)
END_DATE = date(2025, 12, 31)

# Campaigns per channel
# Each campaign runs for a defined period and has a daily spend range
CAMPAIGNS = {
    "google_ads": [
        {"name": "brand_search",     "start": date(2021, 1, 1), "end": date(2025, 12, 31), "daily_min": 200, "daily_max": 400},
        {"name": "spring_sale_2024", "start": date(2024, 3, 1), "end": date(2024, 5, 31), "daily_min": 300, "daily_max": 600},
        {"name": "christmas_2024",   "start": date(2024, 11, 15), "end": date(2024, 12, 24), "daily_min": 400, "daily_max": 800},
    ],
    "meta_ads": [
        {"name": "brand_awareness",  "start": date(2021, 1, 1), "end": date(2025, 12, 31), "daily_min": 150, "daily_max": 350},
        {"name": "retargeting",      "start": date(2022, 6, 1), "end": date(2025, 12, 31), "daily_min": 100, "daily_max": 250},
    ],
    "tiktok_ads": [
        {"name": "gen_z_targeting",  "start": date(2023, 1, 1), "end": date(2025, 12, 31), "daily_min": 100, "daily_max": 300},
    ],
    "email": [
        {"name": "newsletter",       "start": date(2021, 1, 1), "end": date(2025, 12, 31), "daily_min": 15, "daily_max": 50},
    ],
    "influencer_ig": [
        # Annual contracts — spread evenly across the year
        {"name": "macro_jan_kowal",  "start": date(2024, 1, 1), "end": date(2024, 12, 31), "daily_min": 109, "daily_max": 110},  # 40k / 365
        {"name": "midtier_zofia_n",  "start": date(2024, 1, 1), "end": date(2024, 12, 31), "daily_min": 54, "daily_max": 55},   # 20k / 365
        {"name": "micro_pawel_w",    "start": date(2024, 1, 1), "end": date(2024, 12, 31), "daily_min": 41, "daily_max": 42},   # 15k / 365
    ],
    "outdoor": [
        # Warsaw billboard contract — 240k / 365 days
        {"name": "warsaw_billboard", "start": date(2024, 1, 1), "end": date(2024, 12, 31), "daily_min": 657, "daily_max": 658},
    ],
}

def generate_marketing_spend() -> pd.DataFrame:
    """
    Generate daily marketing spend records.

    For each day in [START_DATE, END_DATE], iterate over all active campaigns
    and emit a row with a random daily spend in the campaign's range.
    """
    rows = []
    current_date = START_DATE

    while current_date <= END_DATE:
        for channel, campaigns in CAMPAIGNS.items():
            for campaign in campaigns:
                # Skip if the campaign is not active on this date
                if not (campaign["start"] <= current_date <= campaign["end"]):
                    continue

                spend = round(random.uniform(campaign["daily_min"], campaign["daily_max"]), 2)

                rows.append({
                    "date": current_date,
                    "channel": channel,
                    "campaign": campaign["name"],
                    "spend_pln": spend,
                })

        current_date += timedelta(days=1)

    return pd.DataFrame(rows)

def save_to_csv(df: pd.DataFrame, path: Path) -> None:
    """Save the marketing_spend DataFrame to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


if __name__ == "__main__":
    print(f"Generating marketing spend from {START_DATE} to {END_DATE}...")
    df = generate_marketing_spend()

    print(f"Generated {len(df)} spend records.")
    print(f"Total spend: PLN {df['spend_pln'].sum():,.2f}")
    print(f"\nSpend by channel:")
    print(df.groupby("channel")["spend_pln"].sum().round(2).sort_values(ascending=False).to_string())

    save_to_csv(df, OUTPUT_PATH)
    print(f"\nSaved to {OUTPUT_PATH}")