# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A financial feasibility model for a food truck park + limited bar (prepackaged
canned/bottled beer and liquor shots poured into sealed plastic shot glasses
only — no cocktails, no RV park) on the same 4.5-acre property at 13901 FM
812, Del Valle, TX as the earlier "The Cube" sports bar plan and the
food-truck-+-RV-park alternative. This is the leanest of the three concepts:
~$75,000 startup cost, financed via a personal line of credit (LOC) at 12.5%
interest rather than a bank term loan.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the interactive Streamlit dashboard
streamlit run streamlit_app_ftp.py

# Run the CLI model (text-menu driven)
python food_truck_park_model.py
```

There is no test suite, linter, or build step configured in this repo. To
sanity-check a change to the calculation engine, import the module and run
its analysis functions directly, e.g.:

```bash
python3 -c "import food_truck_park_model as m; m.run_scenario_comparison()"
python3 -c "import food_truck_park_model as m; m.run_sensitivity_analysis()"
python3 -c "import food_truck_park_model as m; m.run_breakeven_analysis()"
python3 -c "import food_truck_park_model as m; m.run_loc_payoff_schedule()"
```

When editing dashboard-facing constants (bar/truck assumptions), verify both
the CLI output above *and* the Streamlit dashboard, since the dashboard
sliders default to the module's constants and several tabs hardcode
descriptive text/labels derived from those same numbers (see Architecture).

## Architecture

Two files, strict separation of concerns:

- **`food_truck_park_model.py`** — pure calculation engine, no UI code. All
  business assumptions live here as module-level constants (Section 1),
  followed by revenue/cost functions (Section 2), annual/multi-year
  projection runners (Section 3), a Monte Carlo simulator (Section 4), named
  scenarios (Section 5), break-even/sensitivity analysis (Section 6), and a
  cash-reserve tracker + LOC payoff schedule (Section 7). Section 8 is a
  plain `input()`-driven CLI menu (`main()`) for running the same analyses
  from a terminal.
- **`streamlit_app_ftp.py`** — imports `food_truck_park_model` as `model` and
  wraps it in a 10-tab dashboard (Dashboard, Annual Projection, Sensitivity,
  Break-Even, Monte Carlo, Scenarios, Multi-Year, Waterfall, Owner Summary,
  Model Overview). All sidebar sliders default to the module's constants
  (e.g. `model.TRUCK_SLOTS`, `model.BAR_DAILY_CUSTOMERS`), and
  `@st.cache_data`-wrapped wrapper functions (`get_annual`, `get_multi_year`,
  `get_monte_carlo`, `get_scenario_results`) call straight into the model's
  `run_*` functions — the dashboard has no calculation logic of its own.

### Financing: revolving LOC, not a term loan

The $75,000 buildout is drawn from a personal line of credit at 12.5%,
**not** an SBA/bank term loan. That means there is no fixed monthly
principal-and-interest payment or amortization schedule. The model handles
this in two places that must stay consistent when either changes:

1. **`FIXED_COSTS["loc_interest"]`** (`LOC_MONTHLY_INTEREST`, ~$793/mo) is a
   conservative, constant interest-only carrying cost baked into
   `MONTHLY_NUT`/`ANNUAL_NUT`, computed by assuming the *full* $75K balance
   stays drawn indefinitely. Every sensitivity/scenario/Monte Carlo/
   break-even function uses this fixed nut, so they're all internally
   consistent but deliberately pessimistic about financing cost.
2. **`run_loc_payoff_schedule()`** is the realistic counterpart: it
   simulates the LOC balance actually declining month-by-month as free cash
   flow (computed by adding `LOC_MONTHLY_INTEREST` back into each month's
   `noi`, then re-subtracting *actual* interest on the declining balance) is
   swept against principal, and reports the real payoff month and total
   interest paid — always lower than what the flat-nut assumption implies.
   If you change `LOC_INTEREST_RATE` or `LOC_AMOUNT`, both places pick it up
   automatically since they derive from the same constants.

`DSCR` (the lender-facing coverage ratio from the RV-park version of this
model) doesn't apply — there's no lender covenant on a personal LOC.
`monthly_nut_coverage` / `avg_monthly_nut_coverage` play the same analytical
role, but measure operating income before fixed costs against the *total
monthly nut* (including LOC interest) rather than against a debt-service
payment. `fcf_yield` (labeled "FCF Yield on Total Cost" in the UI) is annual
NOI divided by `TOTAL_PROJECT_COST` — a returns metric independent of how
the $75K was actually financed.

### Staffing: two people, no fixed labor line in the nut

The park runs on exactly two people: a park manager who lives on-site
rent-free in exchange for running day-to-day operations (cleaning,
maintenance, general oversight), and one bartender. Neither shows up as a
line item in `FIXED_COSTS`:
- The manager's compensation is in-kind (free housing), not a cash expense,
  so there's no "maintenance/cleaning labor" cost in the nut — only
  `maintenance_reserve` for supplies/materials.
- The bartender is paid via a 5% revenue share on bar-like revenue (see
  `VARIABLE_COST_RATE`/`bartender_share` in `calc_monthly_total`), a
  variable cost, not a salary — and is the only bartender at all times,
  including COTA/major-event days. There is no second-bartender or
  event-labor cost anywhere in the model. If staffing assumptions change
  (e.g. hiring a second bartender for big events, or the manager arrangement
  changes), that needs a new fixed or variable cost line, not a revival of
  the old `EXTRA_BARTENDER_COST`/`BIG_EVENT_MONTHS` mechanism (removed).

### Revenue model shape

Every monthly calculation (`calc_monthly_total`) composes five independent
streams: food truck pad rent + revenue share, limited bar sales, COTA
(Circuit of the Americas) event weekends (parking + bar uplift), seasonal
one-off watch parties, and an at-cost utility pass-through (net-zero by
design — Texas PUC resale rules require sub-metered utilities to be billed
at cost, no markup). `run_annual_projection` sums 12 months; Year 1 applies
ramp schedules (`TRUCK_Y1_RAMP`, `BAR_Y1_RAMP`) for gradual fill-up, Year 2+
runs at steady state. `run_multi_year_projection` layers on annual
growth/rent escalation/cost inflation on top of that.

Two independent axes drive most of the complexity:
- **Seasonality** (`SEASONALITY` dict, per-month multiplier) applies to
  bar-like and truck revenue-share income, not to truck pad rent
  (contracted, fixed).
- **COTA event tiers** (`COTA_EVENT_TIERS`) are looked up per month via
  `COTA_EVENTS_BY_MONTH`, or can be overridden per-call (used heavily by the
  Monte Carlo simulator and the "Scenarios" feature to swap in
  pessimistic/optimistic event calendars).

### Bar operating-model constraint (important, easy to regress)

The bar is **evening-only** (6pm–close, ~4.5 hrs/day) and serves
**prepackaged beer and liquor shots only** — canned/bottled beer at
`BEER_PRICE` ($7) and liquor poured/sealed into single-serve plastic shot
glasses at `SHOT_PRICE` ($3). **No cocktails, no mixed drinks made to
order.** `BAR_AVG_CHECK` is `DRINKS_PER_VISIT` (1.5) times the item mix
(`BEER_MIX_PCT`/`SHOT_MIX_PCT`, 75%/25%) — **not** a single item's price;
don't conflate "average check" with "price of one drink" when tuning this.

On COTA/major-event days, the bar extends hours to capture the event crowd
**and** charges premium event pricing (`COTA_EVENT_BEER_PRICE`/
`COTA_EVENT_SHOT_PRICE`, $12/$5 vs. the normal $7/$3), so
`COTA_EVENT_TIERS[...]["bar_uplift_per_weekend"]` values are the normal-
check uplift scaled by `COTA_EVENT_AVG_CHECK / BAR_AVG_CHECK` (~1.71x) on
top of the original (larger) customer-*volume* assumptions carried over
from the earlier mixed-drink models. Don't apply the reduced-customer-count
logic to event-day figures — that would double-count the hours restriction,
and don't forget the premium-pricing multiplier if these numbers are
re-derived.

### Scenario / sensitivity / Monte Carlo relationship

- `SCENARIOS` (Section 5) are five named, hand-tuned parameter sets (Worst
  Case → Upside) run once each via `run_scenario_projection`.
- `run_sensitivity_analysis` sweeps one lever at a time (truck count, truck
  avg sales, bar traffic, COTA event count) holding others at defaults.
- `run_monte_carlo` randomizes nearly every lever simultaneously
  (Gaussian/uniform draws per parameter, per simulation) to produce a nut-
  coverage/cash-flow distribution — this is the only function that doesn't
  take fixed inputs and instead returns a sorted list of per-simulation
  results.

All three read from the same underlying constants/functions, so changing a
constant (e.g. `TRUCK_AVG_MONTHLY_SALES`) shifts every analysis
consistently — there's no separate "scenario data" to keep in sync, except
in `SCENARIOS` and `COTA_EVENT_TIERS`, which hardcode their own parameter
values rather than deriving from the module defaults, and must be updated
by hand when the underlying assumptions change (e.g. bar check size).

## Related models on the same land

- `../ftp-rv-park-financial-model` — food truck park + container bar + RV
  park, $300K SBA loan. This model is a scaled-down variant of that one with
  the RV park removed, the bar simplified to beer+shots, and the financing
  changed from an SBA term loan to a personal LOC.
