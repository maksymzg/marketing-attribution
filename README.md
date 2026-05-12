# Marketing Attribution Analysis - PLSygnet.pl

> A case study analyzing the effectiveness of marketing channels for a fictional Polish e-commerce company in the men's jewelry segment.

🚧 **Status:** Phase 1 - Data Generation & ETL (in progress)

---

## Overview

End-to-end marketing analytics pipeline for **PLSygnet.pl**, a fictional Polish e-commerce company in the men's jewelry market. The Marketing Manager has 8 weeks to deliver a budget reallocation proposal to the board - this project answers the analytical questions behind that decision.

**Business problem:** PLN 1.26M annual marketing budget across 6 channels (Google Ads, Meta Ads, TikTok Ads, influencer marketing, email, outdoor) - but no consolidated view of which channels deliver real returns.

**Approach:** synthetic data generation → PostgreSQL → SQL analysis (last-click vs. first-click vs. linear attribution) → Python visualization → business report.

📄 **Full project brief:** [project_brief.md](./project_brief.md)

## Tech stack

- **Python:** pandas, NumPy, Faker, SQLAlchemy
- **Database:** PostgreSQL
- **Analysis:** Jupyter Notebooks, Matplotlib, Seaborn
- **Version control:** Git, GitHub
- **Standards:** Conventional Commits, type hints, docstrings

## Project structure

```
marketing-attribution/
├── data/                  # Raw and processed datasets
├── src/                   # Source code (data generation, ETL, analysis)
├── sql/                   # SQL queries (one per analytical question)
├── notebooks/             # Jupyter exploration & analysis
├── reports/               # Final business report + charts
├── tests/                 # Unit tests
├── project_brief.md       # Full project documentation
└── requirements.txt       # Python dependencies
```

## Getting started

```bash
# Clone the repo
git clone https://github.com/maksymzg/marketing-attribution.git
cd marketing-attribution

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Roadmap

- [x] **Phase 0** - Project brief, repo setup, environment
- [ ] **Phase 1** - Synthetic data generation & PostgreSQL ETL
- [ ] **Phase 2** - SQL analysis (8 analytical questions)
- [ ] **Phase 3** - Visualization & exploratory analysis
- [ ] **Phase 4** - Final business report
- [ ] **Phase 5** - Documentation & polish

## Author

**Maksym Wieczorek** - Master's student in Economic Data Analytics, UEP Poznań

---

*This is a portfolio project - all data is synthetically generated for educational purposes.*
