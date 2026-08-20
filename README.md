# Food Truck Park + Bar & Beverage Stand | Financial Model

Financial feasibility model for a food truck park with a bar & beverage
stand — an evening bar (prepackaged beer + liquor shots in sealed plastic
shot glasses, no cocktails) plus an all-day soda/juice/water/coffee stand —
at 13901 FM 812, Del Valle, TX. $500,000 total project cost, financed via a
bank term loan (fixed-payment, fully amortizing — rate/term are placeholders
pending an actual bank quote).

This is the leanest of three concepts modeled on the same land, alongside
`The Cube` ($3M sports bar) and a food-truck-+-RV-park variant ($300K SBA
loan) — see `CLAUDE.md` for how this model relates to those.

## Quick start

```bash
pip install -r requirements.txt
streamlit run streamlit_app_ftp.py
```

Or run the CLI menu:

```bash
python food_truck_park_model.py
```

## What's in the dashboard

12 tabs: Dashboard, Annual Projection, Sensitivity, Break-Even, Monte Carlo,
Scenarios, Multi-Year (including a loan amortization schedule), Waterfall,
Owner Summary, Tax Strategies (depreciation + S-corp election), a Model
Overview walkthrough, and a CRE Investment Summary (cap-rate valuation,
leverage, unlevered/levered returns).

See `CLAUDE.md` for architecture details and modeling assumptions.
