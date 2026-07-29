# Food Truck Park + Bar & Beverage Stand | Financial Model

Financial feasibility model for a food truck park with a bar & beverage
stand — an evening bar (prepackaged beer + liquor shots in sealed plastic
shot glasses, no cocktails) plus an all-day soda/juice/water/coffee stand —
at 13901 FM 812, Del Valle, TX. ~$81,600 startup cost, financed via a
personal line of credit at 12.5% interest.

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

11 tabs: Dashboard, Annual Projection, Sensitivity, Break-Even, Monte Carlo,
Scenarios, Multi-Year (including an LOC payoff schedule), Waterfall, Owner
Summary, Tax Strategies (depreciation + S-corp election), and a Model
Overview walkthrough.

See `CLAUDE.md` for architecture details and modeling assumptions.
