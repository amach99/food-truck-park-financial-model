# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A financial feasibility model for a food truck park + bar & beverage stand
(evening beer/liquor-shot bar plus an all-day soda/juice/water/coffee stand
— no cocktails, no RV park) on the same 4.5-acre property at 13901 FM
812, Del Valle, TX as the earlier "The Cube" sports bar plan and the
food-truck-+-RV-park alternative. This is the leanest of the three concepts:
~$81,600 startup cost, financed via a personal line of credit (LOC) at 12.5%
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

**Run the test suite after ANY change to the calculation engine:**

```bash
pytest -q
```

`test_model.py` locks down the invariants that have actually broken during
development — full revenue/cost/NOI reconciliation, COTA totals including
every event-day uplift, ramp monotonicity, scenario ordering, Monte Carlo
determinism and slider-responsiveness, and the tax identities. The
reconciliation test is the highest-value one: it fails the moment a cost is
added to `calc_monthly_total` but not to `summarize_annual`.

There is no linter or build step. For eyeballing output, the analysis
functions also run directly:

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
  cash-reserve tracker + LOC payoff schedule (Section 7), a tax-strategy
  analysis (depreciation + S-corp election, Section 8), and a CRE valuation
  & returns engine (cap-rate value, LTC/LTV, debt yield, unlevered/levered
  IRR/NPV/equity multiple, Section 9 — see "NOI vs. cash flow" and "Land
  basis" above). Section 10 is a plain `input()`-driven CLI menu (`main()`)
  for running the same analyses from a terminal.
- **`streamlit_app_ftp.py`** — imports `food_truck_park_model` as `model` and
  wraps it in a 12-tab dashboard (Dashboard, Annual Projection, Sensitivity,
  Break-Even, Monte Carlo, Scenarios, Multi-Year, Waterfall, Owner Summary,
  Tax Strategies, Model Overview, CRE Investment Summary). The first 11 tabs
  are deliberately plain-language and stay that way — CRE-specific
  vocabulary (NOI before debt service, cap rate, LTV, debt yield, IRR,
  equity multiple) lives only in the CRE Investment Summary tab, which reads
  the Section 9 functions above. All sidebar sliders default to the
  module's constants (e.g. `model.TRUCK_SLOTS`, `model.BAR_WEEKDAY_CUSTOMERS`),
  and `@st.cache_data`-wrapped wrapper functions (`get_annual`,
  `get_multi_year`, `get_monte_carlo`, `get_scenario_results`) call straight
  into the model's `run_*` functions — the dashboard has no calculation
  logic of its own.

### Financing: revolving LOC, not a term loan

The ~$81,600 buildout is drawn from a personal line of credit at 12.5%,
**not** an SBA/bank term loan. That means there is no fixed monthly
principal-and-interest payment or amortization schedule. The model handles
this in two places that must stay consistent when either changes:

1. **`FIXED_COSTS["loc_interest"]`** (`LOC_MONTHLY_INTEREST`, ~$850/mo) is a
   conservative, constant interest-only carrying cost baked into
   `MONTHLY_NUT`/`ANNUAL_NUT`, computed by assuming the *full* $81.6K balance
   stays drawn indefinitely. Every sensitivity/scenario/Monte Carlo/
   break-even function uses this fixed nut, so they're all internally
   consistent but deliberately pessimistic about financing cost.
2. **`run_loc_payoff_schedule()`** is the realistic counterpart: it
   simulates the LOC balance actually declining month-by-month as free cash
   flow (`m["noi"]`, already pre-debt-service — see below) is swept against
   interest on the declining balance first, then principal, and reports the
   real payoff month and total interest paid — always lower than what the
   flat-nut assumption implies. If you change `LOC_INTEREST_RATE` or
   `LOC_AMOUNT`, both places pick it up automatically since they derive from
   the same constants.

`DSCR` (the lender-facing coverage ratio from the RV-park version of this
model) doesn't apply in the owner-facing sense — there's no lender covenant
on a personal LOC. `monthly_nut_coverage` / `avg_monthly_nut_coverage` play
the same analytical role, but measure operating income before fixed costs
against the *total monthly nut* (including LOC interest) rather than
against a debt-service payment — this is a Fixed Charge Coverage Ratio
(FCCR), not a DSCR, and is labeled that way in the CRE Investment Summary
tab. `fcf_yield` (labeled "FCF Yield on Total Cost" in the UI) is
`total_net_cash` (cash flow AFTER debt service) divided by
`TOTAL_PROJECT_COST` — a levered returns metric on cash actually spent,
independent of how the $81.6K was financed. See "NOI vs. cash flow" below
for how this differs from `total_noi`.

### NOI vs. cash flow — two different bases, don't conflate them

`total_noi` and `total_net_cash` (and their monthly counterparts `noi`/
`net_cash_flow`) are **deliberately different numbers**, split out in
`calc_monthly_total()`:

- **`noi`** = operating income before fixed overhead, less `MONTHLY_OPEX_NUT`
  (fixed costs *excluding* LOC interest) and the new management fee /
  replacement reserve (see below). This is **NOI in the standard CRE
  sense — before debt service** — the correct numerator for a cap-rate
  valuation, yield-on-cost, or debt-yield calculation.
- **`net_cash_flow`** = `noi - MONTHLY_DEBT_SERVICE` (the LOC interest
  line). This is what the dashboard's plain-language "Free Cash Flow"
  metrics mean, and what's actually available to the owner.

`MONTHLY_NUT`/`ANNUAL_NUT` (opex + debt service combined) are unchanged and
remain the correct denominator for the coverage ratio above.
`OPERATING_FIXED_COSTS`/`MONTHLY_OPEX_NUT`/`ANNUAL_OPEX_NUT` and
`MONTHLY_DEBT_SERVICE`/`ANNUAL_DEBT_SERVICE` are the split-out pieces.

**Tax base:** federal income tax (`income_tax` in `summarize_annual`) and
the Tax Strategies tab's "Taxable Profit Basis" both apply to
`total_net_cash`, not `total_noi` — LOC interest is a deductible business
expense, so the owner's actual taxable profit is *after* debt service, not
before it. Do not repoint these back to `total_noi`; that was the bug this
split fixed (NOI used to be net of interest, conflating the two).

### Management fee & replacement reserve — real costs, not a display adjustment

`MANAGEMENT_FEE_RATE` (4%) and `REPLACEMENT_RESERVE_RATE` (3%) are real,
variable operating costs computed in `calc_monthly_total()` off EGI
excluding the utility pass-through (a fee on wash revenue would be
meaningless). They reduce `total_net_before_fixed` — and therefore every
downstream cash-flow figure across the whole dashboard, not just the CRE
tab — by roughly $25-30K/yr at stabilized. This is deliberate: a lender or
buyer always normalizes for a market management fee and a capital
replacement reserve regardless of how the current owner actually staffs
the property (the manager here works in exchange for free housing, not a
fee), and a working F&B property needs a real reserve whether or not this
owner sets one aside. If these rates change, `test_management_fee_and_reserve_scale_with_egi`
guards the identity.

### Land basis — `TOTAL_PROJECT_COST` vs. `TOTAL_CAPITALIZED_BASIS`

`TOTAL_PROJECT_COST` ($81,600, buildout only) remains the denominator for
every plain-language "FCF Yield" metric elsewhere in the dashboard — that's
"return on cash actually spent," a legitimate and different question from
a CRE yield-on-cost. `TOTAL_CAPITALIZED_BASIS = LAND_PURCHASE_PRICE +
TOTAL_PROJECT_COST` ($1,481,600) is the land-inclusive basis used **only**
by the CRE Valuation & Returns functions (`calc_valuation_and_leverage()`,
`run_returns_analysis()`, `run_cre_sensitivity_grid()`, Section 9) and
surfaced in the CRE Investment Summary tab. `EQUITY_BASIS =
TOTAL_CAPITALIZED_BASIS - LOC_AMOUNT` is the owner's actual equity in the
deal — since `LOC_AMOUNT == TOTAL_PROJECT_COST` (the LOC fully finances the
buildout and nothing else), `EQUITY_BASIS` numerically equals
`LAND_PURCHASE_PRICE`. Don't exclude land from a yield-on-cost calculation
just because it was owned outright rather than purchased with this
project's capital — no CRE metric does that.

### Development-period timing — `CONSTRUCTION_PERIOD_MONTHS`

`run_returns_analysis()`'s IRR/NPV used to discount the t=0 capital outlay
(`-TOTAL_CAPITALIZED_BASIS`/`-EQUITY_BASIS`) and Year 1's cash flow as if
they were exactly one year apart — i.e. as if the park opened the instant
capital was deployed, with zero construction time. `CONSTRUCTION_PERIOD_MONTHS`
(4 months) fixes that: `_irr`/`_npv` now take a `period_offset` (in years),
and `run_returns_analysis()` passes `CONSTRUCTION_PERIOD_MONTHS / 12` so
every post-Year-0 cash flow is discounted that much later — capital sitting
in a buildout for four months shouldn't appear to earn a return during that
gap. This is a **timing correction only** (drops unlevered IRR from 20.3%
to 18.7% at defaults): it does not add a construction draw schedule (
`USE_OF_FUNDS` is still spent as a lump sum at t=0), a capitalized interest
reserve, land carry during construction, or a developer fee — those are
real *costs*, not just a timing shift, and remain open items on
`CRE_UNDERWRITING_REVIEW.md`'s implementation tracker (item 6). Nothing
outside `run_returns_analysis()`/`run_cre_sensitivity_grid()` reads this
constant — `run_loc_payoff_schedule()`, `run_cash_reserve_tracker()`, and
every other tab's "month 1" still mean the first month of operations,
unaffected by this change.

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

Every monthly calculation (`calc_monthly_total`) composes six independent
streams: food truck pad rent + revenue share, evening bar (alcohol) sales,
COTA (Circuit of the Americas) event weekends (parking + bar uplift),
seasonal one-off watch parties, an at-cost utility pass-through (net-zero by
design — Texas PUC resale rules require sub-metered utilities to be billed
at cost, no markup), and daytime beverages (soda/juice/water/coffee — see
below). The evening bar + daytime beverages together make up the
"Bar & Beverage Stand" shown in the dashboard's overall naming. A seventh
tobacco/nicotine stream was removed — see "Tobacco & nicotine" below.
`run_annual_projection` sums 12 months. Year 1 applies TWO separate ramps
(see "Cold start" below); Year 2+ runs at steady state.
`run_multi_year_projection` layers annual growth/rent escalation/cost
inflation on top of that. The dashboard's **Projection View** radio in the
sidebar switches every tab between the ramped Year 1 view and the
steady-state run-rate view by passing `year=1` or `year=2` to `get_annual` —
useful because a slow first quarter otherwise confounds ramp effects with
winter seasonality.

Three independent monthly multipliers drive most of the complexity:
- **Seasonality** (`SEASONALITY`, 0.65–1.00) — Austin patio weather. The
  dominant one. Applies to bar-like and truck revenue-share income, not to
  truck pad rent (contracted, fixed).
- **Sports density** (`SPORTS_DENSITY`, 0.92–1.06) — how much watchable
  sport is on the big TVs that month, derived from the owner's
  sports-schedule research (October "Sports Equinox" peak, February
  quietest, June–August summer gap). Deliberately averages to ~1.00 so it
  **redistributes** evening-bar traffic across the year rather than handing
  the model free revenue; `test_sports_density_is_revenue_neutral` enforces
  that. Applies to the evening bar ONLY — daytime beverage sales ride on
  food-truck lunch traffic, which doesn't care what's on screen. Distinct from `SEASONAL_EVENTS`, which models three specific
  destination watch parties (Super Bowl, March Madness, NYE).
- **COTA event tiers** (`COTA_EVENT_TIERS`) are looked up per month via
  `COTA_EVENTS_BY_MONTH`, or can be overridden per-call (used heavily by the
  Monte Carlo simulator and the "Scenarios" feature to swap in
  pessimistic/optimistic event calendars).

### COTA impact slider — "what if COTA didn't exist / was exceptional"

`cota_impact_multiplier` (default `1.0`, threaded through `calc_monthly_total`
→ `calc_cota_event_revenue`/`calc_truck_revenue` → `run_annual_projection` →
`run_multi_year_projection`/`run_monte_carlo`/`run_cre_sensitivity_grid`) is a
dashboard-only exploratory lever, distinct from the calendar-driven levers
above. The sidebar's **"COTA Event Impact"** slider runs `0.0x`–`2.0x` and
*is* the multiplier directly (no conversion), so the midpoint (`1.0x`, the
default) reproduces today's baseline calendar exactly:

- **`0.0x`** zeroes every COTA revenue/cost line (`calc_cota_event_revenue`
  returns all-zero regardless of what's on the calendar) — "as if COTA
  didn't exist."
- **`2.0x`** doubles COTA parking/bar-uplift/daytime-bev-uplift/incremental-
  cost, AND — only in months that actually have an event on the calendar,
  and only for the portion of the multiplier above `1.0` — boosts
  food-truck sales and closes the vacancy gap toward full occupancy
  (`COTA_TRUCK_BOOST_MAX`, capped at +20% at the slider's max). This is the
  one place in the model where a COTA event spills over into truck revenue;
  everywhere else, COTA and truck traffic are independent. Daytime-beverage
  revenue rides along automatically since it derives from
  `truck_total_sales` (see below) — no separate wiring needed.

Held fixed (not randomized) across every Monte Carlo simulation via
`base_cota_impact_multiplier`, same convention as `base_truck_rent`/
`base_truck_share`. Not wired into `SCENARIOS`/`run_breakeven_analysis`/
`print_owner_summary`, matching the existing precedent that those use fixed
named parameter sets independent of the sidebar (same as `weekday_customers`
etc. already don't reach those either).

### Cold start: the park is NOT open yet (important context)

As of this model version the park is **still under construction**, has no
operating history, and has **no signed vendor contracts** (six operators
have expressed interest, which is not the same thing). Two Year 1 ramps
encode that, and both should be revisited once real data exists:

- **`TRUCK_Y1_FILL_RAMP`** — lease-up. The lot opens roughly half-leased and
  fills over the first two to three quarters. Applied inside
  `resolve_truck_count`, which returns a possibly-fractional slot count
  (an expected value, not a headcount) and is then multiplied by
  `TRUCK_OCCUPANCY` on top. An earlier version assumed all four hubs were
  leased from month 1; that is no longer true and
  `test_year1_lot_is_not_full_on_opening_month` guards against regressing.
- **`BAR_Y1_RAMP`** — discovery, governing the evening bar AND the
  daytime-beverage stream. Starts at 35% and reaches full
  run-rate at month 10. It used to start at 50%/month 8 on the theory that
  the park had already soft-opened and had traffic to convert — that
  premise was wrong, so the curve is now slower.

`TRUCK_OCCUPANCY` is likewise held at 0.85 rather than 0.90 because there
is no leasing track record to justify the tighter number.

**Estimating rule for this project:** when a number is uncertain, err
toward *higher expenses and lower revenue*. Understating the business is
acceptable; overstating it is not. Several assumptions here are
deliberately pessimistic for that reason and are flagged in-line.

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
**daytime-beverage uplift** directly from the same day-by-day parking
attendance used for parking revenue (`cars x PEOPLE_PER_CAR x attach rate x
price`) rather than a separate hardcoded per-tier number — a packed
event-day lot obviously sells more water/soda/coffee than a normal day.
That uplift (`cota_daytime_bev_uplift`) is additive with the everyday
truck-traffic-driven baseline, not a replacement for it. **Any UI code that
reconstructs a "COTA total" from `cota_parking` + `cota_bar_uplift` must
also add `cota_daytime_bev_uplift`**, or it will silently undercount vs.
`total_gross_revenue` (which already includes it via `cota["gross"]`) —
this class of bug already bit 7+ separate call sites twice (dashboard tabs
+ CLI prints, once when daytime beverages was added and again when the
since-removed tobacco stream was) before being centralized. Adding any
future event-day stream means auditing every one of those call sites again;
`test_cota_gross_is_sum_of_parts` guards the engine side only.

### Tobacco & nicotine: removed (deliberate — do not re-add casually)

An earlier version carried a seventh stream selling cigarettes, vapes, and
nicotine pouches (Zyn) from the same all-day window. **It was removed
entirely**, along with `calc_tobacco_revenue`, every `TOBACCO_*` constant,
the `cota_tobacco_uplift`, the `tobacco_permit` fixed cost, the dashboard
sliders, and the scenario/Monte Carlo levers. Why, so the decision isn't
silently reversed later:

1. **No competitive edge.** Dollar General next door (~30 sec walk) sells
   **both cigarettes and nicotine pouches**. The stream had been justified
   on the premise that DG stocked cigarettes but not vapes/Zyn, leaving a
   narrow edge on the higher-margin sub-products — that premise was wrong.
   A smoke shop across the road (~1–2 min) competes too.
2. **The margin never justified the top line.** At the old assumptions it
   grossed ~$84K/yr steady state (~16% of gross revenue) but produced only
   ~$12K of NOI (~5%), because blended COGS ran ~68%. It flattered revenue
   without moving cash flow — precisely what this model is built to avoid.
3. **Real costs and obligations.** Separate TX Comptroller
   cigarette/tobacco + e-cigarette retailer permits (a different regulatory
   track from TABC), Tobacco 21 age-verification liability, and shrinkage
   on a high-theft category.

Removal is consistent with the project's estimating rule (err toward lower
revenue). `test_tobacco_stream_is_fully_removed` guards against a partial
revert — re-adding a constant or dict key without wiring it through every
consumer is exactly the "COTA total" failure mode above. If tobacco is ever
genuinely re-introduced it needs its **own** stream with its own attach
rate and COGS; folding it into `DAYTIME_BEVERAGE_*` (22% COGS, 35% attach)
would overstate it badly.

The `USE_OF_FUNDS` permits line stays at **$7,000** even though the tobacco
permits are gone (~$270/2yr). It's a rounded planning bucket dominated by
the $5,300 two-year TABC MB permit, and unmodeled TABC surety bonds sit in
the same bucket — so `TOTAL_PROJECT_COST` is unchanged at $81,600.

### Texas tax stack (researched; several were missing before)

Texas has no personal income tax, but this business is far from untaxed.
What applies, and where it lives:

| Tax | Rate | Where modeled |
|---|---|---|
| Mixed Beverage **Gross Receipts** Tax | 6.7% of alcohol sales | `GRT_RATE` |
| Mixed Beverage **Sales** Tax | 8.25% of alcohol sales | `MB_SALES_TAX_RATE` |
| Sales tax — daytime beverages | 8.25% | `DAYTIME_BEVERAGE_SALES_TAX_RATE` |
| Sales tax — **event parking** | 8.25% | `PARKING_SALES_TAX_RATE` |
| Property tax — land | ~$4,000/yr actual | `FIXED_COSTS["property_tax"]` |
| Property tax — **improvements** | 2.0% of buildout | `FIXED_COSTS["property_tax_improvements"]` |
| Employer payroll (FICA/FUTA/SUTA) | ~10% of bartender comp | `EMPLOYER_PAYROLL_BURDEN_RATE` |
| Federal income + SE tax (pass-through) | ~28% blended | `EFFECTIVE_INCOME_TAX_RATE`, Section 8 |
| TX franchise tax | **$0 owed** | not modeled — see below |

Four of these were absent from earlier versions and together cost roughly
$25K/yr of NOI at steady state (~$23K in Year 1), so don't "simplify" them
back out:

1. **Mixed Beverage Sales Tax (8.25%)** is a *second, separate* tax from the
   6.7% GRT, and under an MB permit it hits **every** alcoholic beverage
   including canned beer — not just spirits. The model assumes **tax-inclusive
   menu pricing** (a "$7 beer" means the customer hands over $7), which is
   how bars actually post prices and is the conservative read. If the bar
   instead adds tax at the register, set `MB_SALES_TAX_RATE = 0.0`.
2. **Parking sales tax (8.25%)** — motor vehicle parking is an explicitly
   taxable service in Texas (34 TAC 3.315). With a full COTA calendar this
   is a five-figure annual line.
3. **Property tax on improvements** — the existing $4,000/yr bill taxes raw
   land only. Once built, the improvements join the tax roll.
4. **Employer payroll burden** — paying the bartender via revenue share does
   not avoid employer FICA/FUTA/SUTA if she's a W-2 employee, which her
   working arrangement strongly suggests.

**Franchise tax is $0** (2026 no-tax-due threshold is $2.65M of annualized
revenue; this business projects well under $1M) but a Public Information
Report must still be filed or the entity risks a penalty and loss of good
standing. That filing, plus the *monthly* mixed-beverage and sales-tax
returns an MB permittee owes, is why `FIXED_COSTS["accounting_tax_prep"]`
exists.

Permit costs are real money and were badly understated before: a TABC
**Mixed Beverage Permit is $5,300 for the first two years** ($2,650 at
renewal), which is most of why the `USE_OF_FUNDS` permits line is now
$7,000 rather than $1,500.

Everything above should be confirmed with a TABC-savvy CPA before filing —
the in-line comments flag which items are researched versus estimated.

### Cost totals: use the summarized fields, don't recompute from rates

`summarize_annual` exposes fully-summed variable-cost fields
(`total_cogs`, `total_grt`, `total_mb_sales_tax`,
`total_daytime_beverage_cogs`, `total_daytime_beverage_tax`,
`total_cc_processing`,
`total_shrinkage`, `total_bartender_share`, `total_payroll_burden`,
`total_cota_parking_upkeep`, `total_cota_parking_sales_tax`,
`total_cota_cost`, `total_utility_cost`, `total_management_fee`,
`total_replacement_reserve`) plus the real-estate/business segment split
(`total_real_estate_contribution`, `total_business_contribution` — see
"NOI vs. cash flow" above for what these are and aren't) so the dashboard's
Owner Summary and Waterfall tabs read them directly instead of re-deriving
`rate x revenue` locally in multiple places. Prefer reading these fields
over recomputing - see the COTA-total note above for what goes wrong when a
derived total is duplicated across call sites instead of computed once in
the engine. The Waterfall tab additionally asserts its hand-rolled cost
stack reconciles to `annual["after_tax_noi"]` at render time, so a
mismatched addition there fails loudly instead of silently drifting.

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
