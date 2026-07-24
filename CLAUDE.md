# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A financial feasibility model for a food truck park + bar & beverage stand
(evening beer/liquor-shot bar plus an all-day soda/juice/water/coffee stand
— no cocktails, no RV park) on the same 4.5-acre property at 13901 FM
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
  scenarios (Section 5), break-even/sensitivity analysis (Section 6), a
  cash-reserve tracker + LOC payoff schedule (Section 7), and a tax-strategy
  analysis (depreciation + S-corp election, Section 8). Section 9 is a plain
  `input()`-driven CLI menu (`main()`) for running the same analyses from a
  terminal.
- **`streamlit_app_ftp.py`** — imports `food_truck_park_model` as `model` and
  wraps it in an 11-tab dashboard (Dashboard, Annual Projection, Sensitivity,
  Break-Even, Monte Carlo, Scenarios, Multi-Year, Waterfall, Owner Summary,
  Tax Strategies, Model Overview). All sidebar sliders default to the
  module's constants (e.g. `model.TRUCK_SLOTS`, `model.BAR_DAILY_CUSTOMERS`),
  and `@st.cache_data`-wrapped wrapper functions (`get_annual`,
  `get_multi_year`, `get_monte_carlo`, `get_scenario_results`) call straight
  into the model's `run_*` functions — the dashboard has no calculation
  logic of its own.

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

The park runs on exactly two people, both living on-site rent-free: a park
manager who runs day-to-day operations (cleaning, maintenance, general
oversight), and one bartender. Neither shows up as a line item in
`FIXED_COSTS`:
- The manager's compensation is in-kind (free housing), not a cash expense,
  so there's no "maintenance/cleaning labor" cost in the nut — only
  `maintenance_reserve` for supplies/materials.
- The bartender is paid via `BARTENDER_SHARE_RATE` (5%) of combined bar-like
  + daytime-beverage revenue (see `calc_monthly_total`), a variable cost,
  not a salary — and is the only bartender at all times, covering both the
  evening alcohol bar AND the all-day non-alcohol beverage window (see
  "Daytime beverage stream" below), including COTA/major-event days. Living
  on-site is what makes the longer combined day feasible without a second
  hire. There is no second-bartender or event-labor cost anywhere in the
  model. If staffing assumptions change (e.g. hiring a second bartender for
  big events, or either on-site arrangement changes), that needs a new
  fixed or variable cost line, not a revival of the old
  `EXTRA_BARTENDER_COST`/`BIG_EVENT_MONTHS` mechanism (removed).

### Revenue model shape

Every monthly calculation (`calc_monthly_total`) composes seven independent
streams: food truck pad rent + revenue share, evening bar (alcohol) sales,
COTA (Circuit of the Americas) event weekends (parking + bar uplift),
seasonal one-off watch parties, an at-cost utility pass-through (net-zero by
design — Texas PUC resale rules require sub-metered utilities to be billed
at cost, no markup), daytime beverages (soda/juice/water/coffee — see
below), and tobacco & nicotine (cigarettes/vapes/Zyn — see below). The
evening bar + daytime beverages + tobacco/nicotine together make up the
"Bar & Beverage Stand" shown in the dashboard's overall naming.
`run_annual_projection` sums 12 months; Year 1 applies ramp schedules
(`TRUCK_Y1_RAMP`, `BAR_Y1_RAMP`) for gradual fill-up, Year 2+ runs at steady
state. `run_multi_year_projection` layers on annual growth/rent
escalation/cost inflation on top of that.

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

### Daytime beverage stream (important, easy to regress)

`calc_daytime_beverage_revenue` models all-day soda/juice/water/coffee sales
that extend the bar's window from evening-only alcohol service to an
all-day non-alcohol offering (~11am-close). It is sized off implied
food-truck customer traffic — `trucks["truck_total_sales"] / AVG_TRUCK_TICKET
× DAYTIME_BEVERAGE_ATTACH_RATE × DAYTIME_BEVERAGE_AVG_PRICE` — **not** an
independent daytime headcount, since food trucks are the park's only real
daytime foot-traffic driver. This has two consequences that are easy to
miss when touching truck or bar params:
- It scales automatically with `truck_slots`/`truck_avg_sales`/
  `truck_occupancy` (more/bigger/fuller trucks → more implied daytime
  customers → more beverage revenue), but is **independent of**
  `weekday_customers`/`weekend_customers` (the evening alcohol bar's
  traffic). A "no bar" test must pass `daytime_beverage_attach_rate=0.0`
  separately to zero it out — see `run_breakeven_analysis`'s Zero-Bar Test
  and Min-Bar-Traffic search, both of which do this explicitly.
- It carries its **own** COGS/tax treatment
  (`DAYTIME_BEVERAGE_COGS_RATE` + `DAYTIME_BEVERAGE_SALES_TAX_RATE`,
  ~30% combined), separate from the alcohol bar's `VARIABLE_COST_RATE`
  (`COGS_RATE` + the Mixed Beverage `GRT_RATE`, ~42%) — these aren't
  alcoholic beverages, so standard TX sales tax applies instead of the
  Mixed Beverage GRT. `calc_monthly_total` computes each separately, then
  combines them only for `bartender_share`/`cc_processing` (both variable
  costs that apply to *all* beverage revenue, not just alcohol).

This revenue depends on vendor leases restricting food trucks to **food
only** (specialty drinks like a truck's own agua fresca/lemonade are still
allowed, but generic soda/juice/water/coffee is reserved for the park's
bar) — without that restriction the demand would leak to truck-sold drinks
instead. As of this model version no truck contracts had been signed yet,
so the restriction applies from Day 1 with no phase-in (contrast with the
truck-count Worst Case/Stress Test scenarios, which model *existing*
vendors churning out gradually).

On COTA event days, `calc_cota_event_revenue` also derives a
**daytime-beverage uplift** and a **tobacco/nicotine uplift** directly from
the same day-by-day parking attendance used for parking revenue (`cars x
PEOPLE_PER_CAR x attach rate x price`, one calc per product) rather than
separate hardcoded per-tier numbers — a packed event-day lot obviously
sells more water/soda/cigarettes than a normal day. Both uplifts
(`cota_daytime_bev_uplift`, `cota_tobacco_uplift`) are additive with their
everyday truck-traffic-driven baselines, not a replacement for them. **Any
UI code that reconstructs a "COTA total" from `cota_parking` +
`cota_bar_uplift` must also add `cota_daytime_bev_uplift` AND
`cota_tobacco_uplift`**, or it will silently undercount vs.
`total_gross_revenue` (which already includes both via `cota["gross"]`) —
this class of bug already bit 7+ separate call sites twice (dashboard tabs
+ CLI prints, once when daytime beverages was added and again when tobacco
was) before being centralized.

### Tobacco & nicotine stream (thinner margin, real nearby competition)

`calc_tobacco_revenue` mirrors `calc_daytime_beverage_revenue` exactly (same
truck-traffic-derived customer count, same all-day window, same on-site
bartender covering it - she already cards for alcohol, so Tobacco 21 age
verification adds no new labor), but with materially different economics:
- `TOBACCO_ATTACH_RATE` (12%) is much lower than
  `DAYTIME_BEVERAGE_ATTACH_RATE` (35%) - nicotine use is a smaller slice of
  the population than "wants a drink," and it's set low deliberately
  because **Dollar General next door (~30 sec walk) already sells
  cigarettes**, directly undercutting the one-stop-shop pitch for that
  specific product. Vapes/nicotine pouches are less consistently stocked at
  Dollar General, so the real edge is narrower than the beverage stand's,
  not zero.
- `TOBACCO_COGS_RATE` (68%) is much higher than any beverage stream's -
  cigarette retail margin is famously thin (~15-18%), dragging down the
  blended margin even though vapes/Zyn run better (~40-50%).
- Requires a **separate regulatory permit** from the TABC alcohol permit -
  TX Comptroller cigarette/tobacco + e-cigarette retailer permits
  (`TOBACCO_PERMIT_MONTHLY` in `FIXED_COSTS["tobacco_permit"]`, estimate,
  confirm actual fee with the Comptroller).

If real operating data later shows Dollar General does NOT carry vapes/Zyn
(only cigarettes), consider splitting the attach rate/price by sub-product
instead of one blended `TOBACCO_*` set - not done here to avoid adding a
third pricing axis before there's real sales data to calibrate it against.

### Cost totals: use the summarized fields, don't recompute from rates

`summarize_annual` exposes fully-summed variable-cost fields
(`total_cogs`, `total_grt`, `total_daytime_beverage_cogs`,
`total_daytime_beverage_tax`, `total_tobacco_cogs`, `total_tobacco_tax`,
`total_cc_processing`, `total_shrinkage`, `total_bartender_share`,
`total_cota_parking_upkeep` (`PARKING_UPKEEP_RATE`, 5% of COTA parking
revenue), `total_cota_cost`, `total_utility_cost`) so the dashboard's Owner
Summary and Waterfall tabs read them directly instead of re-deriving `rate x
revenue` locally in multiple places. Prefer reading these fields over
recomputing - see the COTA-total note above for what goes wrong when a
derived total is duplicated across call sites instead of computed once in
the engine.

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
