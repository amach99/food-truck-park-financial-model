# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A financial feasibility model for a food truck park + bar & beverage stand
(evening container bar — draft + canned beer, liquor shots, and cocktails —
plus an all-day soda/juice/water/coffee stand) on the 4.432-acre property at
13901 FM 812, Del Valle, TX — the same land as the earlier "The Cube"
sports bar plan. This is the leanest concept modeled for the site,
financed via a bank term loan (fixed-payment, fully amortizing — placeholder
terms pending an actual bank quote). The buildout started smaller and
personal-LOC-financed (~$81,600); the next phase (septic, paving, payoff of
the existing personal LOC, and remaining construction) is funded by a loan
**sized to its itemized uses** — about $563.6K in the Base case — rather than
the earlier round $500,000. See "Financing" below.

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

Dependencies live in the project's `.venv/` (Python 3.14). Run `source
.venv/bin/activate` first, or call it directly as `.venv/bin/python -m
pytest -q`. A bare `pytest` outside the venv may resolve to a stale global
shim (`/usr/local/bin/pytest`, hard-wired to a removed Python 3.7) and fail
with `bad interpreter` before any test runs.

```bash
pytest -q

# Run a single test
pytest -q test_model.py::test_annual_reconciles_to_noi
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
python3 -c "import food_truck_park_model as m; m.run_loan_amortization_schedule()"
```

**Lender business plan.** `build_business_plan.py` generates the business
plan / loan proposal from the engine — `.docx` by default, Markdown when the
output path ends in `.md` (used for Google Docs upload):

```bash
python build_business_plan.py "Del Valle Food Truck Park - Business Plan.docx"
python build_business_plan.py plan.md
```

Never hand-edit the generated document, and never hardcode a projected
figure in the generator — read it from the model. Narrative that depends on
a number (e.g. whether the reserve covers the Year 1 troughs) must be
conditional on that number, not written for today's value.
`test_business_plan_generates_from_the_model` fails if an engine rename
breaks the generator. `python-docx` is needed only for the generator.

When editing dashboard-facing constants (bar/truck assumptions), verify both
the CLI output above *and* the Streamlit dashboard, since the dashboard
sliders default to the module's constants and several tabs hardcode
descriptive text/labels derived from those same numbers (see Architecture).

## Architecture

Two core files, strict separation of concerns, plus a document generator:

- **`food_truck_park_model.py`** — pure calculation engine, no UI code. All
  business assumptions live here as module-level constants (Section 1),
  followed by revenue/cost functions (Section 2), annual/multi-year
  projection runners (Section 3), a Monte Carlo simulator (Section 4), named
  scenarios (Section 5), break-even/sensitivity analysis (Section 6), a
  cash-reserve tracker + loan amortization schedule (Section 7), a tax-strategy
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
- **`build_business_plan.py`** — imports the model and emits the lender
  business plan (see Commands). Like the dashboard, it holds no calculation
  logic; it only formats engine output and conditional narrative.

### Financing: sized bank term loan, fixed-payment amortizing (v3)

Lender-ready v3 sizes the ask instead of holding a $500,000 round number.
Base asphalt at 10% contingency is about **$563,626**. Bank asphalt at 15%
is about **$581,726**. Both leave a **$40,000** reserve floor. Contingency
is 10%/15% of hard cost including the $50,000 GC allowance, and it is not
cut to force the old ask. Septic is **$212,000** and gated. OSSF design is
$0 until a vendor is chosen. Health permit is $1,700. The $3,000 ACE
retainer is already paid and is not a use. Land carry is PID 984219
($2,289.23) + PID 300451 ($4,459.57) + $700 vacant-land insurance, rounded
to $621/month and prepaid for 6 months ($3,726). Entitlement is 5 months,
`CONSTRUCTION_PERIOD_MONTHS` is 1, and `MONTHS_TO_OPEN` is 6 (open March
2027, the March/April window). IRR delays cash flows by `MONTHS_TO_OPEN`,
not by the 1-month build alone. A $500,000 loan and a $750,000 loan are
debt-service sensitivities: $500,000 does not fund the uses, and $750,000
has no named use for the extra proceeds. DSCR is shown for SBA 7(a) at 10%
variable / 25 years, an SBA 504 blend (50% bank at about 7.5% and 40% CDC
at 6.97%, both 25 years), and a conventional placeholder at 9.5%.

The paragraphs below describe the earlier $500,000 plug. Where they disagree
with this block, this block is the one the engine implements.

### Financing history: the $500,000 round ask

The buildout was originally financed by a smaller personal line of credit
(LOC) at 12.5%, interest-only/revolving. The owner's real "Phase 0.5
Master Plan" cost tracker (Notion) itemizes $80,100 of real, vendor-quoted
buildout across 27 line items, mostly already done or in progress — but
only $66,800 of that (25 of the 27 items - everything except permits and
contingency, which hadn't been spent yet) was actually drawn against the
old LOC (not its full $170,000 facility limit; only $120,000 was drawn).
The owner is now pursuing a real **$500,000 bank term loan** instead, to
pay that LOC off in full ($120,000) and fund a larger buildout (septic,
paving, container bar, plus the still-unspent permits and contingency
lines), with whatever's left over held back as reserve cash — see
`USE_OF_FUNDS` in `food_truck_park_model.py` for the itemized $500,000
Sources & Uses. `LOAN_AMOUNT`, `LOAN_INTEREST_RATE` (10%), and
`LOAN_TERM_YEARS` (25) are placeholder terms pending an actual bank quote
— 10% is the conservative end of a 9.5-10% range the owner gave, and 25
years matches typical SBA-loan amortization.

`LOAN_AMOUNT = TOTAL_PROJECT_COST` by construction, both $500,000 — but
unlike the original single-purpose loan version of this model,
`TOTAL_PROJECT_COST` no longer means "the buildout cost." It means "the
loan," which funds three different things: real new construction/soft
costs, payoff of old debt (not a new asset), and an uncommitted cash
reserve. The $66,800 of the Phase 0.5 tracker that was actually drawn
against the old LOC lives in a **separate** constant,
`PHASE_0_5_CAPITAL_IMPROVEMENTS` (`PHASE_0_5_TOTAL` for its sum),
explicitly excluded from `USE_OF_FUNDS`/`TOTAL_PROJECT_COST` so paying off
the old LOC and re-listing the assets it already bought don't
double-count the same dollars. That list still feeds depreciation
classification and the property's capitalized basis (see "Land basis"
below) — it's real capital investment in the property no matter which loan
financed it. Of the original $80,100 tracker's remaining $13,300
(permits + contingency), the $5,300 TABC Mixed Beverage permit has since
been **obtained and paid under the old LOC**, so it sits inside the
$120,000 payoff line rather than in `USE_OF_FUNDS`. Forward permits and
soft costs on this loan are `PERMITS_AND_SOFT_COSTS` ($12,000) and
`CONTINGENCY_BUDGET` ($24,000). Both were raised after the Sep 9 review
and funded out of the reserve plug, so the loan stays $500,000 and
`RESERVE_AND_SAFETY_CASH` is the residual ($144,000 at these lines). A
later Sep 30 draft listed extra soft costs that are still TBD and a
smaller residual reserve; those amounts are not in `USE_OF_FUNDS`.
Paving stays the $50,000 asphalt line (`PAVING_BUDGET`); the $15,400
gravel alternate is documented and not selected.

Unlike the old revolving LOC, a fixed-payment amortizing loan already has
a real, defined schedule — there's no "conservative flat balance"
assumption needed:

1. **`FIXED_COSTS["loan_payment"]`** (`LOAN_MONTHLY_PAYMENT`, computed via
   `_amortization_payment()`, ~$4,544/mo) is the fixed monthly principal +
   interest payment, baked into `MONTHLY_NUT`/`ANNUAL_NUT`. This genuinely
   doesn't change month to month for the life of the loan — no
   "conservative vs. realistic" split needed here anymore.
2. **`run_loan_amortization_schedule()`** shows the year-by-year
   principal/interest split via `_amortization_balance()`, plus an
   optional scenario (`sweep_pct`, default 1.0) for sweeping free cash flow
   *beyond* the required payment toward extra principal prepayment —
   showing how much sooner the loan retires and how much interest is
   saved if the owner chooses to overpay. `_amortization_interest_for_year()`
   computes just the deductible interest portion of a given loan year (see
   "NOI vs. cash flow" below — this matters for the tax base, since loan
   principal isn't deductible but interest is).

With a real bank loan now in place, `DSCR` is a real, meaningful metric
(shown in the CRE Investment Summary tab), not just an analogy.
`monthly_nut_coverage` / `avg_monthly_nut_coverage` still play a related
but distinct role — a **Fixed Charge Coverage Ratio** (FCCR) measuring
operating income before fixed costs against the *total monthly nut*
(opex + the loan payment), which is broader than a lender's DSCR (opex
isn't usually in a DSCR denominator). `fcf_yield` (labeled "FCF Yield on
Total Cost" in the UI) is `total_net_cash` (cash flow AFTER the full loan
payment) divided by `TOTAL_PROJECT_COST` — a levered returns metric on
cash actually spent, independent of the specific loan structure. See "NOI
vs. cash flow" below for how this differs from `total_noi`.

### NOI vs. cash flow — two different bases, don't conflate them

`total_noi` and `total_net_cash` (and their monthly counterparts `noi`/
`net_cash_flow`) are **deliberately different numbers**, split out in
`calc_monthly_total()`:

- **`noi`** = operating income before fixed overhead, less `MONTHLY_OPEX_NUT`
  (fixed costs *excluding* the loan payment) and the new management fee /
  replacement reserve (see below). This is **NOI in the standard CRE
  sense — before debt service** — the correct numerator for a cap-rate
  valuation, yield-on-cost, or debt-yield calculation.
- **`net_cash_flow`** = `noi - MONTHLY_DEBT_SERVICE` (the loan's full
  principal + interest payment). This is what the dashboard's
  plain-language "Free Cash Flow" metrics mean, and what's actually
  available to the owner.

`MONTHLY_NUT`/`ANNUAL_NUT` (opex + debt service combined) are unchanged and
remain the correct denominator for the coverage ratio above.
`OPERATING_FIXED_COSTS`/`MONTHLY_OPEX_NUT`/`ANNUAL_OPEX_NUT` and
`MONTHLY_DEBT_SERVICE`/`ANNUAL_DEBT_SERVICE` are the split-out pieces.

**Tax base:** federal income tax (`income_tax` in `summarize_annual`) and
the Tax Strategies tab's "Taxable Profit Basis" apply to `total_noi` minus
`loan_interest_paid` — **not** `total_net_cash`. This is a real distinction
now that debt service is a fixed-payment amortizing loan rather than
interest-only: loan **interest** is a deductible business expense, but loan
**principal** is not (it's a real cash outflow, just not a tax deduction),
so `total_net_cash` (NOI minus the *full* P&I payment) understates taxable
profit. `loan_interest_paid` (in the `summarize_annual`/
`run_multi_year_projection` output) isolates just the deductible interest
portion for the relevant loan year via `_amortization_interest_for_year()`
— `run_multi_year_projection` uses the exact loan-calendar year; standalone
`run_annual_projection()`/`summarize_annual()` calls (where `year` means
ramp-state, not loan-calendar-year) approximate using loan Year 1 or Year 2
interest. Do not repoint `income_tax` back to plain `total_net_cash`; that
reintroduces the double-counted-principal bug this split fixed.

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

`TOTAL_PROJECT_COST` ($500,000, the loan) remains the denominator for every
plain-language "FCF Yield" metric elsewhere in the dashboard — that's
"return on cash actually spent via this loan," a legitimate and different
question from a CRE yield-on-cost. It is **not** the right basis for CRE
valuation anymore, though, since it now includes two purely financial line
items that are not capital assets: the LOC payoff (retiring old debt) and
Reserve & Safety Cash (uncommitted). `TOTAL_CAPITALIZED_BASIS` is built
instead from the real capital stack: `LAND_PURCHASE_PRICE +
PHASE_0_5_TOTAL + (every USE_OF_FUNDS line except the LOC payoff and
Reserve & Safety Cash)` — land, plus the real historical buildout already
drawn against the old LOC ($66,800), plus the real new construction/soft
costs this loan directly funds (septic + paving + container bar + permits
+ contingency). At the current permits ($12,000) and contingency ($24,000)
that new-capex stack is $236,000, so capitalized basis is $1,400,000 +
$66,800 + $236,000 = $1,702,800. Used **only** by
the CRE Valuation & Returns functions (`calc_valuation_and_leverage()`,
`run_returns_analysis()`, `run_cre_sensitivity_grid()`, Section 9) and
surfaced in the CRE Investment Summary tab. `EQUITY_BASIS` /
`PROPERTY_EQUITY` = `TOTAL_CAPITALIZED_BASIS - LOAN_AMOUNT` ($1,202,800).
`TOTAL_ECONOMIC_EQUITY` adds the reserve cash ($1,202,800 + $144,000 =
$1,346,800). Those two equity figures are different on purpose;
`equity_schedule_rows()` is the table that sums. Land at $1,400,000 is a
related-party transfer basis, not an appraisal — do not headline
loan / $1,400,000 as LTV. Don't exclude
land from a yield-on-cost calculation just because it was owned outright
rather than purchased with this project's capital — no CRE metric does
that. Also don't "fix" `PROPERTY_TAX_IMPROVEMENTS_MONTHLY` back onto
`TOTAL_PROJECT_COST` — it taxes `TOTAL_CAPITALIZED_BASIS - LAND_PURCHASE_PRICE`
instead, specifically so the LOC payoff and Reserve & Safety Cash (neither
a physical improvement) don't inflate a simulated county tax assessment.

### Development-period timing — `CONSTRUCTION_PERIOD_MONTHS`

`run_returns_analysis()`'s IRR/NPV used to discount the t=0 capital outlay
(`-TOTAL_CAPITALIZED_BASIS`/`-EQUITY_BASIS`) and Year 1's cash flow as if
they were exactly one year apart — i.e. as if the park opened the instant
capital was deployed, with zero construction time. `CONSTRUCTION_PERIOD_MONTHS`
(6 months: `ENTITLEMENT_PERMIT_LAG_MONTHS` 5 + `POST_PERMIT_BUILD_MONTHS` 1,
Sid's Sep 30 time-to-open lock, with `OPENING_MONTH` = March 2027) fixes
that: `_irr`/`_npv` now take a `period_offset` (in years),
and `run_returns_analysis()` passes `CONSTRUCTION_PERIOD_MONTHS / 12` so
every post-Year-0 cash flow is discounted that much later — capital sitting
through that six-month clock shouldn't appear to earn a return during the
gap. The separate cash-burn clock is `PRE_OPEN_MONTHS` (4): debt service,
insurance, property tax, and accounting against zero revenue, drawn from
`RESERVE_AND_SAFETY_CASH`. `OPENING_CASH_RESERVE` is that reserve minus
`PRE_OPEN_BURN`. Sid's narrower land-carry draft (tax + insurance × 6) is
not stacked on the 4-month burn. This IRR lag is a **timing correction only** (a few points of unlevered IRR at
current defaults - the exact figure moves with `TOTAL_CAPITALIZED_BASIS`
and the loan terms, see below): it does not add a
construction draw schedule (`USE_OF_FUNDS` is still spent as a lump sum at
t=0), a capitalized interest reserve, land carry during construction, or a
developer fee — those are real *costs*, not just a timing shift, and
remain open items on `CRE_UNDERWRITING_REVIEW.md`'s implementation tracker
(item 6). Don't hardcode these IRR figures elsewhere - they move whenever
`TOTAL_CAPITALIZED_BASIS` or the loan terms change; treat them as
directional, not exact. Nothing outside
`run_returns_analysis()`/`run_cre_sensitivity_grid()` reads this constant —
`run_loan_amortization_schedule()`, `run_cash_reserve_tracker()`, and every
other tab's "month 1" still mean the first month of operations, unaffected
by this change.

### Staffing: scheduled wages, still a light crew

Cash labor is `calc_scheduled_labor()`, not a line in `FIXED_COSTS` and
not a percent of beverage sales. `BARTENDER_SHARE_RATE` is 0 so the old
5% share cannot stack on top of wages.
- Daytime attendant: `DAYTIME_ATTENDANT_WAGE` ($13/hr) for the non-alcohol
  window (`DAYTIME_BEVERAGE_HOURS_PER_DAY` − `BAR_HOURS_PER_DAY`).
- Evening bartender: `EVENING_BARTENDER_WAGE` ($16/hr) for the alcohol window.
- One extra body on each COTA event day: `EVENT_EXTRA_WAGE` ($15/hr).
- `OVERTIME_ALLOWANCE_RATE` (10%) on hourly wages only.
- Manager: `MANAGER_ANNUAL_SALARY` ($24,000). Lodging is provided
  (`LODGING_PROVIDED`) and not expensed (`LODGING_EXPENSED` is False).
  IRC §119 / FLSA §3(m) are flagged, not assumed.
- Employer burden: `EMPLOYER_PAYROLL_BURDEN_RATE` (10%) on all cash wages.
`maintenance_reserve` is still supplies only. One attendant plus one
bartender is a light crew for an 11-hour day; wage rates are estimates
pending quotes. Do not revive `EXTRA_BARTENDER_COST` / `BIG_EVENT_MONTHS`.

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
inflation on top of that. Cost inflation is applied line by line inside
`calc_monthly_total` (`cost_inflation_mult` on each opex line and each
wage line). The loan payment is never inflated. There is no lump NOI
haircut, and the cash tracker does not subtract opex inflation a second
time. `cost_inflation_adj` is the dollar increase only. The dashboard's **Projection View** radio in the
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

### Bar operating model — full container bar (four items, easy to regress)

The bar is **evening-only** (6pm–close, ~4.5 hrs/day) and is a **full
container bar** ($50,000, the `USE_OF_FUNDS` "Container Bar (full
buildout)" line) pouring **four** items: draft beer via taps
(`DRAFT_BEER_PRICE`, $6), canned/bottled beer via coolers (`BEER_PRICE`,
$7), single-serve liquor shots (`SHOT_PRICE`, $3), and made-to-order
cocktails (`COCKTAIL_PRICE`, $12).

**This reverses an earlier, deliberately locked-down constraint.** Prior
versions of this model served *prepackaged beer and sealed shots only —
no cocktails, no mixed drinks* — and that restriction was documented here
as an invariant. The owner is now building the full container bar, so the
restriction is gone. Don't reintroduce "no cocktails" language; equally,
don't assume anything downstream still holds from the two-item era without
checking, because the change cascaded:

- `BAR_AVG_CHECK` is `DRINKS_PER_VISIT` (1.5) times the blended
  `AVG_ITEM_PRICE` across all four items — **not** a single item's price;
  don't conflate "average check" with "price of one drink" when tuning it.
  It moved $9.00 → **$11.45** (+27%).
- Item mix is `DRAFT_BEER_MIX_PCT`/`BEER_MIX_PCT`/`SHOT_MIX_PCT`/
  `COCKTAIL_MIX_PCT` = 31.5%/13.5%/20%/35%. Beer is 45% of items overall,
  split 70/30 draft-vs-canned now that taps exist. `DRINKS_PER_VISIT`
  stayed at 1.5 deliberately — a fuller bar changes *what* people order,
  not how many rounds they have.
- `COGS_RATE` is **revenue**-weighted (not item-count-weighted, since
  prices differ): draft/canned beer 37% each, shots 25%, cocktails 30%.
  It *improved* 35.5% → **32.2%** because cocktails carry a better markup
  than reselling manufactured single-serve items. The 30% cocktail COGS is
  an ESTIMATE padded above the typical 20–25% per the project's
  err-toward-higher-expenses rule — replace it with real recipe costing
  when available.

On COTA/major-event days, the bar extends hours to capture the event crowd
**and** charges premium event pricing across all four items
(`COTA_EVENT_DRAFT_BEER_PRICE`/`COTA_EVENT_BEER_PRICE`/
`COTA_EVENT_SHOT_PRICE`/`COTA_EVENT_COCKTAIL_PRICE` = $10/$12/$5/$16 vs.
the normal $6/$7/$3/$12), giving `COTA_EVENT_AVG_CHECK` $17.06.
`COTA_EVENT_TIERS[...]["bar_uplift_per_weekend"]` values are dollar
figures = customer-*volume* uplift × the event check; when the check
changes they must be rescaled by the **event**-check ratio (they were
rescaled ×1.109 for this change, $15.375 → $17.055), and
`SEASONAL_EVENTS[...]["rev_base"]` by the **normal**-check ratio (×1.2725).
Both sets are hardcoded and hand-maintained — same drift risk `SCENARIOS`
carries. Don't apply the reduced-customer-count logic to event-day figures
— that would double-count the hours restriction — and don't forget the
premium-pricing multiplier if these numbers are re-derived.

The `SCENARIOS` `avg_check` values were rescaled by the same ×1.2725 normal
-check ratio ($7.45/$8.05/$8.55/$9.00/$9.95 →
$9.48/$10.24/$10.88/`BAR_AVG_CHECK`/$12.66); Base Case now references
`BAR_AVG_CHECK` directly rather than duplicating the number.

Labor does not scale with the check. The evening bartender is an hourly
wage (`EVENING_BARTENDER_WAGE`), so a higher cocktail check does not raise
her pay. Cocktails still carry a skill/speed requirement the prepackaged
plan avoided, and the crew is still light. The
`FIXED_COSTS["insurance"]` estimate ($900/mo) is flagged in-line for
revisiting now that the bar pours cocktails rather than only prepackaged
items.

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
  (`COGS_RATE` + GRT on the receipt after sales tax is backed out + the
  embedded mixed-beverage sales tax) — these aren't
  alcoholic beverages, so standard TX sales tax applies instead of the
  Mixed Beverage GRT. `calc_monthly_total` computes each separately.
  Credit-card processing applies to alcohol and daytime beverage revenue.
  Labor is scheduled hours, not a share of that revenue.

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

### TABC permit: obtained and paid — do not re-add it to `USE_OF_FUNDS`

The `USE_OF_FUNDS` permits line is **$12,000** (`PERMITS_AND_SOFT_COSTS`),
and it must not contain the TABC permit. The $5,300 two-year TABC Mixed
Beverage permit **has been obtained and paid**, financed by the old
personal LOC — so those dollars are already inside the $120,000
LOC-payoff line. Carrying $5,300 in the permits line as well would
double-count the same dollars *and* inflate `TOTAL_CAPITALIZED_BASIS`,
which capitalizes the permits line but deliberately excludes the payoff.
The model records the permit as paid. It does not store a permit number,
and it does not treat the license as transferable collateral.

The permit is deliberately **not** added to
`PHASE_0_5_CAPITAL_IMPROVEMENTS`: that list is physical improvements
feeding depreciation classification, and a liquor license is an intangible
on a different tax footing. `test_tabc_permit_is_not_double_counted_in_use_of_funds`
guards the whole arrangement. Sec. 195 startup basis now includes the
$12,000 permits line, so it can exceed the $5,000 immediate-deduction cap;
`test_startup_costs_follow_section_195_structure` holds in both regimes.
Unmodeled TABC surety bonds remain out of scope.

### Texas tax stack (researched; several were missing before)

Texas has no personal income tax, but this business is far from untaxed.
What applies, and where it lives:

| Tax | Rate | Where modeled |
|---|---|---|
| Mixed Beverage **Gross Receipts** Tax | 6.7% of alcohol receipts after sales tax is backed out | `alcohol_taxes_on_inclusive_receipts` |
| Mixed Beverage **Sales** Tax | 8.25% embedded in the tax-inclusive price (`rate / (1 + rate)`) | `MB_SALES_TAX_RATE` |
| Sales tax — daytime beverages | 8.25% | `DAYTIME_BEVERAGE_SALES_TAX_RATE` |
| Sales tax — **event parking** | 8.25% | `PARKING_SALES_TAX_RATE` |
| Property tax — land | ~$4,000/yr actual | `FIXED_COSTS["property_tax"]` |
| Property tax — **improvements** | 2.0% of buildout | `FIXED_COSTS["property_tax_improvements"]` |
| Employer payroll (FICA/FUTA/SUTA) | ~10% of all cash wages | `EMPLOYER_PAYROLL_BURDEN_RATE` |
| Federal income + SE tax (pass-through) | ~28% blended | `EFFECTIVE_INCOME_TAX_RATE`, Section 8 |
| TX franchise tax | **$0 owed** | not modeled — see below |

Four of these were absent from earlier versions and together cost roughly
$25K/yr of NOI at steady state (~$23K in Year 1), so don't "simplify" them
back out:

1. **Mixed Beverage Sales Tax (8.25%)** is a *second, separate* tax from the
   6.7% GRT, and under an MB permit it hits **every** alcoholic beverage
   including canned beer — not just spirits. The model assumes **tax-inclusive
   menu pricing** (a "$7 beer" means the customer hands over $7). Sales tax
   is backed out of that receipt **before** GRT, so GRT is not charged on
   the sales tax. If the bar instead adds tax at the register, set
   `MB_SALES_TAX_RATE = 0.0`.
2. **Parking sales tax (8.25%)** — motor vehicle parking is an explicitly
   taxable service in Texas (34 TAC 3.315). It is extracted from the
   tax-inclusive parking price the same way (`_inclusive_sales_tax`). With a
   full COTA calendar this is a five-figure annual line.
3. **Property tax on improvements** — the existing $4,000/yr bill taxes raw
   land only. Once built, the improvements join the tax roll.
4. **Employer payroll burden** — 10% of all cash wages (hourly, the overtime
   allowance, and the manager salary). Lodging is not in that base.

**Franchise tax is $0** (2026 no-tax-due threshold is $2.65M of annualized
revenue; this business projects well under $1M) but a Public Information
Report must still be filed or the entity risks a penalty and loss of good
standing. That filing, plus the *monthly* mixed-beverage and sales-tax
returns an MB permittee owes, is why `FIXED_COSTS["accounting_tax_prep"]`
exists.

Permit costs are real money and were badly understated before: a TABC
**Mixed Beverage Permit is $5,300 for the first two years** ($2,650 at
renewal). That permit has now been obtained and paid under the old LOC —
see "TABC permit" above for why it lives in the payoff line rather than
the `USE_OF_FUNDS` permits line, which is $12,000 and does not include it.

Everything above should be confirmed with a TABC-savvy CPA before filing —
the in-line comments flag which items are researched versus estimated.

### Cost totals: use the summarized fields, don't recompute from rates

`summarize_annual` exposes fully-summed variable-cost fields
(`total_cogs`, `total_grt`, `total_mb_sales_tax`,
`total_daytime_beverage_cogs`, `total_daytime_beverage_tax`,
`total_cc_processing`,
`total_shrinkage`, `total_labor_wages`, `total_payroll_burden`,
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
  results. The draws, bounds, and default seed live in `MONTE_CARLO_SPEC`
  / `MONTE_CARLO_DEFAULT_SEED` and are shown on the Monte Carlo tab.
  Reproducibility is for a stated seed. Draws are independent, so the
  joint downside tail is fatter than the chart. A sixth named case,
  "Delayed Opening (misses F1)", strips the October F1 weekend and is
  excluded from the worst-to-best order test.
- `run_breakeven_analysis` returns a dict per coverage target. If the
  search hits the 4.0× traffic ceiling without reaching the target,
  `reachable` is false and the customer counts are None — the UI says
  unreachable instead of printing the ceiling as if it were the answer.
- When yield on cost is below the loan rate, `leverage_dilutive` is true.
  Levered IRR below unlevered IRR is reported the same way. Do not hide
  the levered figure.
- NASCAR on the calendar is the DuraMAX Texas Grand Prix.
  `F1_AGREEMENT_THROUGH_YEAR` is 2034. `COTALAND_STATUS` is a scheduled
  competitor, not park revenue.
- Opening operations are March 2027 (`OPENING_MONTH` / `OPENING_YEAR`).
  Debt service in the engine is the unrounded payment × 12; round only
  at display.

All three read from the same underlying constants/functions, so changing a
constant (e.g. `TRUCK_AVG_MONTHLY_SALES`) shifts every analysis
consistently — there's no separate "scenario data" to keep in sync, except
in `SCENARIOS` and `COTA_EVENT_TIERS`, which hardcode their own parameter
values rather than deriving from the module defaults, and must be updated
by hand when the underlying assumptions change (e.g. bar check size).

## Related models on the same land

Sibling repos exist for earlier/alternative concepts on this property (`The
Cube`, a $3M sports bar; and a $300K-SBA-loan variant in
`../ftp-rv-park-financial-model`). This model's engine descends from the
latter's codebase, which is why some inherited comments and figures trace
back to it — but **the concept modeled here does not include an RV park,
and no user-facing output should mention one.** Those sibling repos are
historical reference only; don't reintroduce their scope into this model's
docs, dashboard, or assumptions.
