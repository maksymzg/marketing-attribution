# PLSygnet Marketing Attribution — Key Insights

## Q1.1 — Channel ROAS Comparison

### Findings

**Top performers (ROAS 20+):**
- **Email** — ROAS 24.84, revenue 1.48M PLN on 60k PLN spend
- **Influencer_ig** — ROAS 23.56, revenue 1.77M PLN on 75k PLN spend

**Workhorse channels (ROAS 6-7):**
- **TikTok_ads** — ROAS 6.43
- **Google_ads** — ROAS 6.11 (largest volume — 9,569 orders)

**Underperformer:**
- **Outdoor** — ROAS 2.43 (lowest), 240k PLN budget → only 143% return
- **Meta_ads** — ROAS 4.01 (lower than expected; retargeting overload?)

### Recommendations for Marketing Manager (Marek)

1. **Increase investment in email + influencer_ig** — highest ROI channels
2. **Reconsider outdoor contract renewal** in 2026 — 240k PLN budget gives weakest return
3. **Audit Meta retargeting campaign** — may be over-spending given low conversion vs Google
4. **Keep Google_ads as workhorse** — high volume, solid ROAS, scalable

### Data quality notes
- All channels show consistent AOV (~390 PLN), suggesting product preferences are channel-agnostic
- ROAS ratios match design expectations from data generation logic

## Q1.2 — Outdoor WAW20 attribution

### Findings

**WAW20 is the dominant driver of outdoor revenue:**
- 69% of outdoor orders use WAW20 promo code
- WAW20 orders generated 403k PLN (vs 182k without promo)
- AOV nearly identical (392 vs 398 PLN) — promo doesn't cannibalize order value

**Outdoor channel scale:**
- Only ~0.8 orders/day from billboard (1,485 orders over 5 years)
- Total revenue 585k PLN over 5 years
- ROAS 2.43 — confirmed lowest of all channels (from Q1.1)

### Data quality note

WAW20 represents a 20% discount in business context, but our dataset doesn't 
apply the discount to `total_amount` (code is a marker only). In a real 
implementation, revenue with WAW20 would be ~20% lower than shown here, 
further reducing outdoor ROAS to ~2.0.

### Recommendations

1. **Outdoor decision:** Without measurable brand-awareness value, redirect 
   240k PLN annual budget to email or influencer channels (ROAS 23-24x)
2. **If outdoor must continue:** Consider performance-based deals where 
   billboard provider gets paid per redeemed WAW20 code, not flat fee
3. **WAW20 working as designed:** 69% redemption rate is solid — keep the code, 
   it converts outdoor exposure to attributable sales