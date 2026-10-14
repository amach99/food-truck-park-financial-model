# Anoop Sep 9 review — financial model audit

**v3 update.** The Sep 30 locks this file left unapplied (septic $212k,
6-month land carry, sized ask, 1-month build, product DSCR, PropCo/OpCo
lease) are now in the engine. Dollar figures in the tables below are the
Sep 9 draft, not the v3 ask. Use `build_use_of_funds()` and
`run_loan_size_dscr()` for current numbers.



Draft only. This file maps each review item to the public model in this
repo (`food_truck_park_model.py`, `streamlit_app_ftp.py`, `test_model.py`).
Business-plan and loan-package documents live outside the repo. This audit
does not create lender submissions.

GitHub `main` at `73547c7` (last engine push before this branch) did **not**
contain the engine corrections described in the Sep 4 response. Those
corrections are in this draft.

Figures below are what the engine prints after this draft. They are not
copied from the Sep 4 memo. Where a memo headline moved, the engine number
is the one to use.

## Already in place (before this draft)

- Street address is `13901 FM 812, Del Valle, TX 78617`. The string `13903`
  is not in the model.
- Deeded acreage is 4.432 (1.500 + 2.932), not a rounded 4.5.
- The $5,300 TABC Mixed Beverage permit is not a second time in `USE_OF_FUNDS`.
  It sits inside the $120,000 LOC payoff. It is not in `PHASE_0_5`.
- Paving in sources and uses was already the $50,000 asphalt line.
- Phase 0.5 capital improvements sum to $66,800 and stay out of the new loan's
  uses (the payoff line is the financing of that spend).
- NOI is before debt service. DSCR exists. The loan payment is amortizing,
  not a flat interest-only balance.
- Monte Carlo was already deterministic for a stated seed. What was missing
  was disclosure of the seed, the distributions, and the bounds.
- Management fee (4%) and replacement reserve (3%) already reduce NOI.
- Tobacco is already removed.
- Stabilized gross already produced about 50.4% property + parking and about
  4.3% contractual pad rent. The labels (contractual vs non-contractual vs
  transactional) were not on the outputs.
- COTALAND was not a revenue line. The NASCAR tier was still named EchoPark.

## Changed in this draft

### 1. Labor rebuild — changed

`calc_scheduled_labor()` replaces the 5% beverage-revenue share.
`BARTENDER_SHARE_RATE` is 0 so the share cannot stack on the wages.

| Line | Assumption | Stabilized year (engine) |
|---|---|---|
| Daytime attendant | $13/hr × 6.5 hr × 364.8 days | $30,826 |
| Evening bartender | $16/hr × 4.5 hr | $26,266 |
| COTA extra body | $15/hr × 11 hr × event days | $3,630 |
| Overtime allowance | 10% of hourly wages | $6,072 |
| Manager | $24,000 cash salary | $24,000 |
| Employer burden | 10% of all cash wages | $9,079 |
| Cash wages + burden | | **$99,873** |

Lodging is `LODGING_PROVIDED` and `LODGING_EXPENSED = False`. IRC §119 and
FLSA §3(m) are flagged in comments and on the dashboard. They are not
treated as established.

The retired 5% share was on the order of $12k. The new cash labor bill is
about $88k higher, not a hardcoded +$96k. The review's "$96k" is the same
order of magnitude. Hours were not padded to force $96k. The crew is still
one daytime attendant, one evening bartender, and one extra body only on
COTA event days. That is light for an 11-hour day. Wage rates are estimates.

### 2. Equity schedule — changed

`equity_schedule_rows()` is the table the CRE tab shows. Each subtotal
equals the rows that feed it.

| Line | Amount |
|---|---|
| Land (related-party transfer basis, not an appraisal) | $1,400,000 |
| Phase 0.5 capital improvements | $66,800 |
| New construction and soft costs | $236,000 |
| Capitalized basis | $1,702,800 |
| Less: bank loan | ($500,000) |
| Property equity | **$1,202,800** |
| Reserve cash (not capitalized) | $144,000 |
| Total economic equity | **$1,346,800** |

`EQUITY_BASIS` remains property equity. Levered IRR still uses that figure,
not total economic equity.

### 3. March 2027 open and pre-open burn — changed

`OPENING_MONTH = 3`, `OPENING_YEAR = 2027`. Four months of loan payment,
insurance, land tax, improvements tax, and accounting accrue against zero
revenue.

- Pre-open burn: **$26,126**
- Cash at open: reserve $144,000 − burn = **$117,874**

Sid's 6-month time-to-open is the IRR clock (`CONSTRUCTION_PERIOD_MONTHS = 6`
= 5 months entitlement lag + 1 month post-permit build). It is not a second
cash burn. Sid's narrower land-carry draft (tax + insurance × 6 = $7,398)
is not stacked on the $26,126.

### 4. Reserve tied to sources and uses — changed

`RESERVE_AND_SAFETY_CASH` is the plug:
$500,000 − ($120,000 payoff + $100,000 septic + $50,000 paving + $50,000 bar
+ $12,000 permits + $24,000 contingency) = **$144,000**.

The cash tracker starts at `OPENING_CASH_RESERVE`, not an unexplained $15,000.

### 5. Monte Carlo disclosure — changed

`MONTE_CARLO_SPEC` and `MONTE_CARLO_DEFAULT_SEED` (42) are what the simulator
draws and what the Monte Carlo tab lists. Draws are independent
(`MONTE_CARLO_DRAWS_ARE_INDEPENDENT`). Reproducibility is for a stated seed.
The joint downside tail is fatter than the chart because correlations are
not modeled. Truck slots, pad rent, revenue share, and the COTA impact
multiplier stay held fixed.

### 6. Mixed-beverage tax — changed

`alcohol_taxes_on_inclusive_receipts()` backs sales tax out of the cash
receipt, then applies 6.7% GRT to the remainder. On a $100 inclusive
receipt that is $7.62 sales tax and $6.19 GRT ($13.81 combined), versus
$14.95 if both rates hit the full receipt. Parking sales tax uses the same
inclusive extraction. COGS stays on the full cash receipt.

Daytime-beverage sales tax is still the statutory rate times revenue. The
review item was the alcohol GRT-on-tax stack. Daytime beverages are not in
that stack.

### 7. Unrounded debt service — changed

Monthly payment is the unrounded amortization result
($4,543.5037…). Annual debt service is payment × 12 = **$54,522.04**.
`round(monthly) × 12` is $54,528 and is not what the engine carries.
Display helpers round to the dollar.

### 8. Inflation — changed

`cost_inflation_mult` scales each operating-cost line and each wage line
inside the monthly calculation. Year 2 opex equals Year-1 opex × 1.03.
Year 2 wages are higher than Year 1. The loan payment is the same unrounded
annual amount in both years. `cost_inflation_adj` reports the dollar
increase. It is not subtracted again. The cash tracker and the prepayment
sweep do not take a second opex haircut.

### 9. Break-even search — changed

Each target returns `reachable`. If coverage at 4.0× traffic is still below
the target, weekday and weekend counts are `None` and the dashboard says
unreachable. It does not print the ceiling as a customer count.

With scheduled labor, a weak truck base, no COTA, and the Year 1 ramp, the
1.0× nut-coverage target is unreachable inside that ceiling. The search
check is the Worst Case check ($9.48), the rescaled four-item menu price.
The retired $7.45 pre-cocktail price no longer drives the search.

### 10. Dilutive leverage — changed

Stabilized yield on cost is **7.04%**, below the 10% placeholder loan rate,
so `leverage_dilutive` is true on the valuation. At a 5-year hold and a 9%
exit cap, unlevered IRR is about **3.4%** and levered IRR is about **1.0%**.
The CRE tab warns when levered IRR is below unlevered IRR. The bank case
keeps the unlevered IRR on screen when the levered solver has no root.

### Pro forma items encoded in the model

- **Delayed opening that misses October F1.** Scenario
  `Delayed Opening (misses F1)` strips `tier1_f1` from October and is
  excluded from the worst-to-best order test. It is a demand-calendar case
  on the Year 1 operating window, not a second construction-draw model.
- **Related-party basis.** Land is labeled a related-party transfer basis.
  The dashboard does not headline loan / $1,400,000 as LTV. Cap-rate LTV is
  labeled an indication. `calc_collateral_indications()` also shows loan /
  capitalized cost (LTC **29.4%**) and loan / related-party land basis
  (**35.7%**). Segment indications use an 8.5% cap on unallocated
  real-estate contribution and 2.5× on operating-business contribution.
  Shared overhead is unallocated. None of this is an appraisal.
- **Revenue mix.** Stabilized (Year 2) property + parking is **50.4%** of
  total gross. Contractual pad rent is **4.3%**. Percentage rent is labeled
  non-contractual (no executed leases). Event parking is labeled
  transactional. Year 1 mix is higher (about 54.9%) because the truck ramp
  is still filling while the event-parking calendar is not ramped. The
  50.4% figure is the steady state.
- **Permits $12,000 / contingency $24,000.** Both are in `USE_OF_FUNDS` and
  funded from the reserve plug. Paving stays $50,000 asphalt.
  `GRAVEL_ALT_BUDGET` ($15,400) is documented and not selected.
- **Liquor permit.** Still "obtained and paid" inside the LOC payoff. The
  permits line label does not say TABC. The model does not store a permit
  number and does not treat the license as collateral.
- **Calendar.** NASCAR tier name is DuraMAX Texas Grand Prix.
  `F1_AGREEMENT_THROUGH_YEAR = 2034`. `COTALAND_STATUS` is
  `scheduled_competitor_not_park_revenue`. COTALAND is not on the event list.
- **Entities (constants only).** Borrower `JVAM Capital LLC` (the deed
  grantee in the land comment). Operating `JVA Operations LLC`. Parent
  `JVAM Ventures LLC`. Personal-guarantee preference constants:
  `no_pg_land_only`, fallback `all_jvam_ventures_stakeholders`. These are
  labels, not a loan product.

## Remaining — documents and evidence, not this engine

- Wage quotes, a staffing schedule, and a CPA opinion on §119 / FLSA §3(m)
  and on the 28% blended tax rate.
- Executed vendor leases or LOIs. Percentage rent stays non-contractual
  until then.
- An independent appraisal. Do not send any LTV in this model as collateral
  value. The Sep 4 four-way set (40.2% / 29.4% / 35.7% / 36.3%) is not
  reproduced as four official outputs. This draft exposes LTC 29.4%, loan /
  related-party land 35.7%, a cap-rate indication, and an unallocated
  segment indication. The 40.2% and 36.3% readings are not rebuilt.
- Permit matrix, fixed bids, sealed parking layout, TxDOT, ADA.
- Liquor "held vs applied" beyond "paid via the old LOC." Transferability
  is a legal question.
- Propco / opco split and any intercompany lease. Not modeled.
- Formation state, good standing, guarantor PFS, title, insurance quotes,
  and LOC payoff support. Human diligence. This draft does not invent them.
- "TO BE COMPLETED" blanks in the plan document. They are not engine fields.
- Bank-loan package evidence and hold items, other than the address check
  above and the entity-name constants.

## Conflict with later Sid locks (Sep 30)

Both clocks are in the model, and they are not the same thing:

| Clock | What it is | Where |
|---|---|---|
| 4-month pre-open burn | Debt service, insurance, tax, accounting vs zero revenue (~$26,126) | `PRE_OPEN_BURN` |
| 6-month time to open | 5-month entitlement lag + 1-month post-permit build; IRR timing only | `TIME_TO_OPEN_MONTHS` |

Not applied, on purpose:

- Sid's land-carry of about $7,398 (tax + insurance × 6) is not added on
  top of the $26,126 burn.
- A later sources-and-uses draft (contingency nearer $25,000, residual
  reserve nearer $96,000, and other soft costs still marked TBD) is not in
  `USE_OF_FUNDS`. Amounts were not locked, and applying them would move the
  equity totals off $1,202,800 / $1,346,800.
- Gravel paving ($15,400) is not the selected use. Asphalt $50,000 stays.
- The personal-guarantee preference is a constant. NCC / Harvest / LiftFund
  (or any other product) is not modeled.
- Addendum 5 was a draft pending a construction co-sign. This branch does
  not treat it as a lender submission.

## Engine readings that moved vs the Sep 4 memo

Do not put the old headlines back on a one-pager without re-running the model.

| Reading | This engine |
|---|---|
| Stabilized DSCR (10% / 25-year, unrounded debt service) | 2.20× |
| Year 1 DSCR (March 2027–February 2028, ramped) | 1.41× |
| Stabilized DSCR with COTA impact at 0 | 0.31× |
| Bank-case DSCR (stacked stress, 11.5% rate) | 0.45× (below 1.35×) |
| Stabilized NOI | about $119,900 |
| Year 1 NOI | about $77,000 |
| Yield on cost | 7.04% (below the 10% loan rate) |
| Unlevered / levered IRR (5-year, 9% exit, 6-month lag) | about 3.4% / 1.0% |
| Bank-case levered IRR | undefined in the solver's range |

Year 1 no longer includes the February 2027 Super Bowl (that date is before
a March 2027 open). The February line in Year 1 is the 2028 game. F1 in
October 2027 is inside Year 1 unless the delayed-opening scenario strips it.
