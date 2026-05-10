# Marketing Attribution Analysis - PLSygnet.pl

> A case study analyzing the effectiveness of marketing channels for a fictional Polish e-commerce company in the men's jewelry segment.

---
## TL;DR

**Business problem:** PLSygnet.pl, a Polish men's jewelry e-commerce company (PLN 7M annual revenue, growth-mode), allocates a PLN 1.26M marketing budget across 6 channels — but Marketing Manager Marek Kot has no consolidated view of which channels deliver real returns. He needs to defend a 2026 budget reallocation proposal to the board within 8 weeks.

**Approach:** End-to-end analytics pipeline — synthetic data generation in Python, loaded into PostgreSQL, analyzed via SQL (last-click vs. first-click vs. linear attribution), visualized in Python (Matplotlib/Seaborn), and summarized in a business-language report.

**Key analytical questions:** ROAS per channel, customer LTV by acquisition source, basket composition by channel, lift study for offline (outdoor), and feasibility check for new channel (YouTube Ads).

**Tech stack:** Python (pandas, SQLAlchemy), PostgreSQL, Jupyter, Matplotlib/Seaborn, Git/GitHub.

**Out of scope (intentional):** ML models, real-time pipelines, web dashboards, statistical inference (full list in Section 5).

---

## 1. Company Context

**PLSygnet.pl** is a fictional e-commerce company inspired by the Polish men's jewelry market. Founded in 2020, the company is currently in an aggressive growth phase, deliberately sacrificing profit margin to accelerate customer acquisition.

### Business profile

| Metric | Value |
|---|---|
| Annual revenue | **PLN 7M** |
| Orders per month | ~1,500 |
| Average Order Value (AOV) | ~PLN 390 |
| Annual marketing budget | **PLN 1.26M** (18% of revenue) |
| Repeat customer rate | ~25% |
| Years on market | 5 (founded 2020) |

### Product catalog

The company sells 7 categories of men's jewelry and accessories:

- Signet rings (flagship category)
- Bracelets
- Necklaces and chains
- Rings (non-signet)
- Watches (highest AOV in the mix)
- Men's earrings
- Suit accessories (cufflinks, tie clips, lapel pins)

### Target customer

Men aged **20–45**, primarily living in cities of 100k+ inhabitants, with mid-to-upper income levels and an active interest in fashion and lifestyle. **~80% of purchases are self-purchases**, with ~20% being gifts (signaled by the choice of gift wrapping at checkout).

### Marketing channels

The PLN 1.26M annual budget is allocated across 6 channels:

| Channel | Type | Trackability |
|---|---|---|
| Google Ads | Paid search + shopping | High (UTM, click-through) |
| Meta Ads | Paid social (FB + IG) | High (Pixel, UTM) |
| TikTok Ads | Paid social | High (UTM, pixel) |
| Influencer marketing (IG) | Paid partnerships | Medium (promo codes, UTM) |
| Email marketing | Owned channel | High (email tracking) |
| Outdoor | Offline (billboards, citylights) | **Low — "dark channel"** |

### Strategic context

The company operates in **growth mode** — the elevated marketing budget (18% of revenue vs. industry benchmark of 8–15%) is a deliberate board-level decision. The strategic goal is **30% YoY revenue growth** over the next 2 years, followed by margin optimization. **This project aims to optimize the channel mix _within_ this budget**, not to reduce the budget itself.

---

## 2. Persona & Pain Points

### Marek Kot — Marketing Manager

| Attribute | Value |
|---|---|
| Role | Marketing Manager |
| Age | 32 |
| Tenure at PLSygnet | 3 years (joined 2022) |
| Background | Previously worked in performance marketing at another Polish e-commerce company |
| Reports to | CEO (founder) |
| Team | 2 specialists (1 paid social, 1 content/email) — no in-house analyst |

### The problem on Marek's desk

PLSygnet has scaled from PLN 2M to PLN 7M in revenue over 5 years, with marketing spend growing in lockstep. The board has approved a **budget increase for 2026** to fuel continued growth — but before allocating it, the CEO has asked Marek a simple question:

> *"Where exactly is our marketing money working — and where is it being wasted?"*

Marek doesn't have a confident answer. He suspects parts of the budget are underperforming, but his current data setup makes it impossible to prove.

### Pain points

**1. Traditional vs. digital — no apples-to-apples comparison.**
Marek rented 2 billboard spots in central Warsaw for a 12-month campaign (PLN 240,000). He suspects traditional advertising is less effective than digital channels and generates fewer leads — but he has no data to prove it. Outdoor is a *dark channel*: there is no click-through, no UTM, no native attribution.

**2. Influencer marketing — gut feeling, no proof.**
Marek invested PLN 75,000 in influencer marketing across 3 partnerships: one macro-influencer (PLN 40,000), one mid-tier (PLN 20,000), and one micro-influencer (PLN 15,000). He saw conversions, but is unsure whether to continue with influencers at this scale or reallocate budget to paid digital ads instead.

**3. Cross-channel customer behavior — invisible.**
Marek doesn't know whether customers acquired via influencers behave differently from customers acquired via Google Ads — in basket size, repeat purchase rate, or category preferences. Without this view, he cannot judge the *quality* of traffic from each channel, only its volume.

**4. New channels — afraid to commit blindly.**
PLSygnet has not yet invested in YouTube Ads. Marek is considering launching it as a new channel, but wants an analytical view of its expected ROI before committing budget — he has been burned before by launching channels on intuition alone.

**5. Siloed data — no single source of truth.**
Marek's current visibility is limited to **vanity metrics**: Instagram story views, post likes, and aggregate website visit counts. Each platform (Google Ads, Meta Ads, TikTok Ads) reports its own attribution using last-click bias — totals don't reconcile across dashboards. He has no consolidated view of the customer journey, no attribution model linking channels to conversions, and no cost-per-acquisition (CAC) by channel.

### What Marek needs to decide

Based on this analysis, Marek will:

- **Reallocate the channel mix** for the 2026 marketing budget (which channels get more, which get less)
- **Decide whether to launch YouTube Ads** as a new channel — and at what initial budget
- **Decide the future of influencer marketing** — scale up, scale down, or shift toward different influencer tiers
- **Present the proposal to the board** for budget approval

### Constraints

- **Reporting deadline:** Marek must present the budget reallocation proposal at the next board meeting — **8 weeks from now**. The analysis cannot be open-ended; it must lead to actionable recommendations within that window.
- **Vendor lock-in:** Annual contracts are already signed with the billboard agency (until December 2026) and 2 of the 3 influencers (until Q3 2026). These channels cannot be cut mid-contract — the analysis must work *with* this constraint, not around it.

---
## 3. Analytical Questions

The pain points above translate into 8 concrete analytical questions. Each question maps to a specific business decision Marek will make based on the answer.

### Pain Point 1 — Traditional vs. Digital (Outdoor billboards)

**Q1.1:** What is the lift in organic traffic and direct-to-site sales in Warsaw during the billboard campaign period, compared to the same period in cities without billboard exposure (Kraków, Wrocław, Poznań)?
**Decision:** Whether to renew the outdoor contract for 2027 (or scale up/down).

**Q1.2:** What is the redemption rate of the dedicated billboard promo code, and what revenue can be attributed to it?
**Decision:** Whether outdoor delivers measurable conversions or functions purely as brand awareness.

### Pain Point 2 — Influencer Marketing

**Q2.1:** What is the ROAS for each influencer partnership (macro: PLN 40k, mid-tier: PLN 20k, micro: PLN 15k), measured via attributed promo codes and UTM-tagged links?
**Decision:** Renew, downgrade, or drop each partnership for 2026.

**Q2.2:** What is the engagement rate (engagement / reach) for each influencer's branded content, and how does it correlate with conversion rate?
**Decision:** Whether to prioritize macro (reach) or micro (engagement) tier in the 2026 budget.

### Pain Point 3 — Cross-channel Customer Behavior

**Q3.1:** What is the AOV, gross profit per order, and 12-month customer LTV, broken down by acquisition channel?
**Decision:** Whether to optimize the channel mix for **volume** (low-AOV high-volume channels) or **value** (high-AOV low-volume channels).

**Q3.2:** What is the basket composition (% of revenue by product category) for customers acquired via each channel, and how does the repeat-purchase rate within 6 months differ between channels?
**Decision:** Whether to align channel-specific creative content with the categories that channel attracts.

### Pain Point 4 — New Channel (YouTube Ads)

**Q4.1:** What is the historical ROAS, CPM, and conversion rate of PLSygnet's existing paid video channels (TikTok Ads, Meta video creatives) — and what is the implied range of expected YouTube Ads ROAS based on this internal benchmark?
**Decision:** Whether the expected YouTube ROAS clears the minimum threshold (ROAS ≥ 2.0) for a 2026 test budget.

**Q4.2:** What is the demographic overlap between PLSygnet's existing customer base and YouTube Poland's audience profile, and which audience segments show highest affinity for jewelry/men's lifestyle content?
**Decision:** If overlap is strong, launch a PLN 30k pilot campaign for 3 months; if weak, reallocate to a higher-confidence channel.

---
## 4. Data Entities

To answer the analytical questions above, the project requires the following data entities. Detailed schema (columns, data types, constraints) is defined in Phase 1.

### Core entities

| Entity | Purpose | Key questions it serves |
|---|---|---|
| `customers` | Customer master data — demographics, location, acquisition channel | Q3.1, Q3.2, Q4.2 |
| `orders` | Order-level transactions — date, amount, customer, products | Q1.2, Q2.1, Q3.1, Q3.2 |
| `order_items` | Line items per order — products, quantities, prices | Q3.2 |
| `products` | Product catalog — category, price, gross margin | Q3.1, Q3.2 |
| `marketing_spend` | Daily/weekly spend per channel and campaign | Q1.1, Q2.1, Q4.1 |
| `marketing_touchpoints` | Customer interaction events — channel, timestamp, campaign, attribution data (UTM, promo code) | Q1.2, Q2.1, Q2.2, Q4.1 |

### Relationships (high-level)

- `customers` → `orders` (1-to-many)
- `orders` → `order_items` (1-to-many)
- `order_items` → `products` (many-to-1)
- `customers` → `marketing_touchpoints` (1-to-many)
- `marketing_touchpoints` → `marketing_spend` (many-to-1, via channel + date)

### Note on data realism

All data will be **synthetically generated** in Python with realistic distributions (e.g., AOV log-normal around PLN 390, conversion rates aligned with industry benchmarks for niche e-commerce). Generation logic is documented in `src/data_generation/` and reproducible via a fixed random seed.

---
## 5. Definition of Done

The project is considered complete when **all** of the following criteria are met:

### Deliverables

- [ ] **Data generation pipeline** — Python module that generates synthetic data for all 6 entities, reproducibly (fixed random seed), runnable via single CLI command
- [ ] **Database** — local PostgreSQL instance with all 6 tables loaded, indexed, and documented (schema in `/docs/schema.md`)
- [ ] **SQL analysis** — at least 8 documented queries (one per analytical question Q1.1–Q4.2), each with a header comment explaining the business question and stored in `/sql/`
- [ ] **Python notebook** (`analysis.ipynb`) — connects to the database, runs queries, produces visualizations (Matplotlib/Seaborn) for each analytical question
- [ ] **Final report** (`/reports/final_report.md`) — written for Marek as the audience: business-language summary of findings, recommendations per pain point, and explicit acknowledgment of analysis limitations

### Code quality

- [ ] **Logging** — all data generation and ETL operations log key steps to console + log file
- [ ] **Error handling** — pipeline fails gracefully with informative error messages
- [ ] **Docstrings** — all functions have type hints and docstrings
- [ ] **README.md** — professional, complete, includes: project overview, business context, methodology, key findings (with 2–3 highlight charts), tech stack, how-to-run instructions, project structure

### Git hygiene

- [ ] **At least 10 commits** following Conventional Commits style (`feat:`, `fix:`, `docs:`, `refactor:`)
- [ ] **At least 1 feature branch + merged PR** to `main` (demonstrates branch workflow understanding)
- [ ] **`.gitignore`** properly excludes `venv/`, `__pycache__/`, `.env`, large data files
- [ ] **Final tag** `v1.0` marking the release version

### Out of scope (explicitly excluded)

To prevent scope creep, the following are **deliberately excluded** from this project:

- ❌ Machine learning models (predictive attribution, churn prediction)
- ❌ Real-time data pipeline (batch processing only)
- ❌ Web dashboard (BI tool, Streamlit, etc.) — analysis output is markdown report + notebook
- ❌ Statistical significance testing (descriptive analysis only — proper inference would require real data)
- ❌ Advanced attribution models (Markov chains, Shapley values) — uses last-click + first-click + linear attribution as comparison

These exclusions are intentional and documented to demonstrate **scope discipline**.

---

## Project Status

**Phase 0 — Project Brief:** ✅ Complete (this document)
**Phase 1 — Data Generation & ETL:** ⬜ In progress
**Phase 2 — SQL Analysis:** ⬜ Not started
**Phase 3 — Visualization & Reporting:** ⬜ Not started
**Phase 4 — Documentation & Polish:** ⬜ Not started