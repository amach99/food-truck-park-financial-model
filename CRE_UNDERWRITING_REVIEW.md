# CRE Underwriting Review — Investment Committee Memo

**Asset:** Food truck park + bar & beverage stand, 13901 FM 812, Del Valle, TX (Travis County)
**Sponsor:** First-time F&B developer/operator
**Review date:** 2026-07-28
**Model reviewed at commit:** `ef92eb2` (`food_truck_park_model.py`, `streamlit_app_ftp.py`, `test_model.py`)
**Framing:** Reviewed as a lender / equity investment committee would review a ground-up development pro forma.

> All figures in this memo were computed directly from the model at the commit above, not estimated.
> Re-run the calculations in [Appendix A](#appendix-a--reproducing-the-figures) after any engine change.

---

## Table of contents

1. [Recommendation summary](#recommendation-summary)
2. [Model structure in CRE terms](#1-model-structure-in-cre-terms)
3. [Standard CRE metrics: present, absent, how to derive](#2-standard-cre-metrics-present-absent-and-how-to-derive)
4. [Underwriting assumptions — findings](#3-underwriting-assumptions--findings)
5. [Development pro forma benchmark](#4-development-pro-forma-benchmark)
6. [Capital stack assessment](#5-capital-stack-assessment)
7. [F&B / hospitality nuances](#6-fb--hospitality-nuances)
8. [Code and modeling hygiene](#7-code-and-modeling-hygiene)
9. [Proposed Summary Output](#8-proposed-summary-output)
10. [Implementation tracker](#implementation-tracker)
11. [Appendix A — reproducing the figures](#appendix-a--reproducing-the-figures)
12. [Glossary of CRE terms](#appendix-b--glossary-of-cre-terms)

---

## Recommendation summary

The model is a **well-built operating business projection** with genuinely sophisticated F&B demand
modeling — seasonality, sports-calendar density, event-day tiering, and Monte Carlo. It is **not yet a
CRE development pro forma**, and in its current form it cannot be underwritten by a lender or
institutional equity partner. Three issues are structural rather than cosmetic:

1. **NOI is defined net of interest expense** — non-standard, and it breaks every derived metric.
2. **Land is excluded from the basis** — so the headline 261% "FCF Yield on Total Cost" is not a yield on cost.
3. **~43% of stabilized revenue is operating-business income, not real property income** — and the model
   does not separate the two, which is the single biggest gap between what this model says and what a
   lender would credit.

None of this means the deal is bad. Restated properly it shows a **13.0% yield on cost** including land at
purchase price — a strong development yield. The problem is presentation and definition, not economics.

---

## 1. Model structure in CRE terms

### What a CRE development model normally contains, and what this model has

| Phase | Standard structure | This model |
|---|---|---|
| **Predevelopment / land** | Land basis, carry, entitlement | ❌ Absent. `LAND_PURCHASE_PRICE` exists but is explicitly commented *"not used in any calculation"* |
| **Development period** | Construction draw schedule, interest reserve, contingency, developer fee | ⚠️ Partial. `USE_OF_FUNDS` is a well-itemized construction budget with real vendor pricing and a contingency line, but has **no time dimension** |
| **Sources & Uses** | Debt/equity sources against total uses | ⚠️ Uses only (`USE_OF_FUNDS`); sources implied by `LOC_AMOUNT = TOTAL_PROJECT_COST` |
| **Lease-up** | Absorption schedule to stabilization | ✅ Strong. `TRUCK_Y1_FILL_RAMP` (50%→100% by mo. 9) and `BAR_Y1_RAMP` (35%→100% by mo. 10) |
| **Stabilized operations** | Steady-state NOI | ✅ `run_annual_projection(year=2)` |
| **Hold period** | 5–10 yr monthly/annual cash flows | ⚠️ `run_multi_year_projection(years=3)` default — too short |
| **Exit / reversion** | Terminal value at exit cap, sale costs | ❌ Absent entirely |

### Schedule mapping — where each CRE schedule lives in the code

| CRE schedule | Function / structure |
|---|---|
| Development budget | `USE_OF_FUNDS` list → `TOTAL_PROJECT_COST` (§1) |
| Operating cash flow | `calc_monthly_total()` → `run_annual_projection()` → `summarize_annual()` (§2–3) |
| Financing schedule | `run_loc_payoff_schedule()` (§7) — the only true debt schedule |
| Project-level returns | `fcf_yield` in `summarize_annual()` |
| Equity-level returns | ❌ None. `run_tax_strategy_analysis()` (§8) is the closest, but it's entity tax planning, not an equity waterfall |
| Working capital | `run_cash_reserve_tracker()` (§7) — good, and uncommon in amateur models |

**Structural verdict:** This is a **stabilized operating model with a lease-up ramp**. What's missing is
the *development period* on the front end and the *exit* on the back end — the two things that make a
development pro forma a development pro forma.

---

## 2. Standard CRE metrics: present, absent, and how to derive

### 2.1 Net Operating Income — ⚠️ PRESENT BUT MISDEFINED

**This is the most important finding in the memo.**

> **NOI (Net Operating Income)** = Effective Gross Income − operating expenses, **before** debt service,
> capital expenditure, depreciation, and income tax. The "before debt service" part is not optional — it's
> what makes NOI capital-structure-neutral and therefore comparable across assets. It is the numerator of
> cap rate, DSCR, and debt yield.

Current definition in `calc_monthly_total()`:

```python
noi = total_net_before_fixed - MONTHLY_NUT
```

and `MONTHLY_NUT = sum(FIXED_COSTS.values())`, where `FIXED_COSTS` includes:

```python
"loc_interest": LOC_MONTHLY_INTEREST,  # 12.5% interest-only on the LOC draw
```

**So NOI is net of interest expense.** In CRE terms that is not NOI — it is closer to *Cash Flow After Debt
Service* (pre-principal). Consequences: cap-rate valuation off `noi` understates value; DSCR computed off
it double-counts interest; debt yield is wrong; yield-on-cost is wrong.

**Restated:**

| | Year 1 | Stabilized (Yr 2) |
|---|---:|---:|
| EGI | $375,098 | $437,302 |
| Model `total_noi` (after LOC interest) | $174,509 | $212,650 |
| **+ Add back LOC interest** | +$10,200 | +$10,200 |
| **= True NOI (before debt service)** | **$184,709** | **$222,850** |
| Operating expense ratio | 50.8% | 49.0% |

**Fix — split the nut into operating and financing:**

```python
OPERATING_FIXED_COSTS = {k: v for k, v in FIXED_COSTS.items() if k != "loc_interest"}
MONTHLY_OPEX_NUT = sum(OPERATING_FIXED_COSTS.values())      # $4,342
MONTHLY_DEBT_SERVICE = FIXED_COSTS["loc_interest"]           # $850

noi = total_net_before_fixed - MONTHLY_OPEX_NUT              # ← true CRE NOI
cash_flow_after_debt_service = noi - MONTHLY_DEBT_SERVICE
```

The reconciliation test (`test_annual_reconciles_to_noi`) will catch any error here — run `pytest -q` after.

### 2.2 Cash flow before / after debt service — ⚠️ CONFLATED

Currently `net_cash_flow == noi` (identical values). After the split above the standard three-line stack
becomes available:

```
NOI                          →  before debt service
− Debt service               →  Cash Flow After Debt Service (CFADS)
− Capex / reserves           →  Cash Flow Available for Distribution
```

### 2.3 DSCR — ❌ ABSENT (deliberately)

> **DSCR (Debt Service Coverage Ratio)** = NOI ÷ annual debt service (principal + interest). A lender's core
> covenant. 1.25x means NOI covers debt service 1.25 times over. Typical minimums: **1.20–1.30x** general
> CRE; **1.35–1.50x** for hospitality/F&B-exposed assets, because the income is operating income rather
> than contractual rent.

`CLAUDE.md` correctly documents that DSCR doesn't apply — a personal revolving LOC carries no lender
covenant. The substitute is:

```python
nut_coverage = total_net_before_fixed / MONTHLY_NUT
```

This is a **Fixed Charge Coverage Ratio (FCCR)**, not DSCR — the denominator blends cash opex *and*
interest. That's a legitimate metric and arguably the more relevant one for an owner-operator, but
**label it FCCR**, because "coverage ratio" will be read as DSCR by any lender and this one is not
comparable.

**DSCR on the current facility:**

| Yr | Adj. NOI | Debt service (IO) | DSCR | Debt yield |
|---|---:|---:|---:|---:|
| 1 | $158,452 | $10,200 | 15.5x | 194% |
| 2 | $195,181 | $10,200 | 19.1x | 239% |
| 3 | $199,248 | $10,200 | 19.5x | 244% |
| 4 | $202,878 | $10,200 | 19.9x | 249% |
| 5 | $207,265 | $10,200 | 20.3x | 254% |

These are not meaningful coverage ratios — they reflect a trivially small loan, not a strong asset.

### 2.4 Cap rate and implied value — ❌ ABSENT

> **Cap rate (capitalization rate)** = NOI ÷ value. The market's required unlevered yield.
> **Value = NOI ÷ cap rate.** A 100bp cap-rate move on $200K of NOI swings value by ~$300K — which is why
> cap rate sensitivity is mandatory in any IC package.

```python
EXIT_CAP_RATE = 0.09
implied_value = annual["noi"] / EXIT_CAP_RATE
```

**But see §3.2 — the choice of *which* NOI to capitalize matters far more than the cap rate here.**

| Cap rate | Value (all-in adj. NOI $192,238) | Value (RE-only adj. NOI $17,808) |
|---|---:|---:|
| 7.0% | $2,746,264 | $254,407 |
| 8.0% | $2,402,981 | $222,606 |
| 9.0% | $2,135,983 | $197,872 |
| 10.0% | $1,922,384 | $178,085 |
| 11.5% | $1,671,639 | $154,856 |

### 2.5 LTV and debt yield — ❌ ABSENT

> **LTV** = loan ÷ value. **LTC** = loan ÷ total cost. **Debt yield** = NOI ÷ loan amount — a
> value-independent leverage test lenders adopted post-2008 precisely because it can't be gamed by
> cap-rate assumptions. Minimums: ~9–11% stabilized CRE, 11–13% hospitality/F&B.

```python
ltc = LOC_AMOUNT / TOTAL_CAPITALIZED_BASIS
ltv = LOC_AMOUNT / implied_value
debt_yield = annual["noi"] / LOC_AMOUNT
```

**Computed:** LTC 5.5% (land at cost) / 21.4% (land at assessment); LTV ~3.4% at a 9% cap; debt yield 236%.
Extraordinarily conservative — see §5.

### 2.6 IRR, NPV, equity multiple — ❌ ABSENT, and not derivable without an exit

> **IRR** = discount rate where NPV of all cash flows = 0; time-weighted. **Equity multiple** = total
> distributions ÷ equity invested; not time-weighted. Both are needed — a 2.0x over 3 years and over
> 10 years are very different deals.

These cannot be computed today because there is **no reversion (exit) event and no equity basis**. To add:

```python
HOLD_YEARS   = 5
EXIT_CAP     = 0.09
SALE_COST    = 0.03
EQUITY_BASIS = LAND_PURCHASE_PRICE + TOTAL_PROJECT_COST - LOC_AMOUNT

reversion = (noi_year6 / EXIT_CAP) * (1 - SALE_COST)
unlevered = [-TOTAL_CAPITALIZED_BASIS] + noi[0:4] + [noi[4] + reversion]
levered   = [-EQUITY_BASIS] + cfads[0:4] + [cfads[4] + reversion - loan_balance]
```

**Computed unlevered IRR, 5-yr hold:**

| Basis | Exit 8% | Exit 10% | Exit 12% |
|---|---:|---:|---:|
| Land at assessed $300K ($381,600 basis) | 75.1% / 9.25x | 70.5% / 7.91x | 67.0% / 7.01x |
| **Land at purchase $1.4M ($1,481,600 basis)** | **22.2% / 2.38x** | **18.1% / 2.04x** | **15.1% / 1.81x** |

The second row is the honest one. **18–22% unlevered IRR on a 2.0x multiple is an institutionally
attractive development return** — that is the number to lead with, not the 261% FCF yield.

### 2.7 Cash-on-cash and payback — ⚠️ PARTIAL

> **Cash-on-cash** = annual pre-tax cash flow after debt service ÷ equity invested. A current-yield
> measure, distinct from IRR.

`fcf_yield = total_noi / TOTAL_PROJECT_COST` is labeled "FCF Yield on Total Cost" but is really an
**unlevered yield on cost with an incomplete denominator** (see §3.1). Payback exists —
`run_cash_reserve_tracker()` sets `payback_month` when `cumulative_noi >= TOTAL_PROJECT_COST` — but again
against a basis that excludes land.

```python
cash_on_cash = cash_flow_after_debt_service / EQUITY_BASIS
```

---

## 3. Underwriting assumptions — findings

### 3.1 ❗ Land is not in the basis

```python
LAND_PURCHASE_PRICE = 1_400_000
LAND_VALUE = LAND_PURCHASE_PRICE  # kept for reference; not used in any calculation
```

`TOTAL_PROJECT_COST = $81,600` is hard + soft costs only. Every return metric divides by it, producing
yields of 214–261%. **No CRE metric excludes land from basis.** The land is contributed equity at its
opportunity cost whether or not cash moves at closing.

**Restated yield on cost:**

| Basis | Yield on cost (stabilized, adj. NOI) |
|---|---:|
| $81,600 (as modeled) | 235.6% ← not a real metric |
| $381,600 (land at assessment) | 50.4% |
| **$1,481,600 (land at purchase)** | **13.0%** ← the underwritable number |

13.0% yield on cost against a ~9% market cap rate is a **~400bp development spread** — healthy. Show that.

### 3.2 ❗ Real property income vs. operating business income is not separated

This is the finding that most changes what a lender will do.

| Stabilized revenue | $ | % of EGI | Character |
|---|---:|---:|---|
| Truck pad rent + % rent | $145,271 | 33% | Real property (contractual) |
| COTA event parking | $85,469 | 20% | Real property (land-based, volatile) |
| Utility recovery | $20,000 | 5% | Expense reimbursement |
| **Real-estate income** | **$250,740** | **57%** | |
| Evening bar + daytime beverage + events | $186,562 | 43% | **Operating business** |

Appraisers and lenders bifurcate **real property value** from **business enterprise value (BEV)**. A bank
lending against real estate underwrites the former. The **Zero-Bar Test** in `run_breakeven_analysis()`
already produces exactly this number:

- RE-only revenue: **$84,788**
- RE-only true NOI: **$21,200** (after mgmt fee: ~$17,808)

**Loan sizing on the two bases — the spread is the whole story:**

| Sizing test | All-in NOI ($195,181) | RE-only NOI ($17,808) |
|---|---:|---:|
| DSCR 1.25x @ 8.5%/20yr | $1,499,389 | $136,802 |
| DSCR 1.40x @ 8.5%/20yr | $1,338,740 | $122,145 |
| Debt yield @ 10% | $1,951,806 | $178,080 |
| Debt yield @ 12% | $1,626,505 | $148,400 |
| LTV 65% @ 9% cap | $1,409,638 | $128,613 |

**A real estate lender will size to the right-hand column.** The left column is only available from a
cash-flow/SBA lender underwriting the going concern — a different product, different rate, and typically
a personal guarantee. Model both, and label which is which.

### 3.3 ❗ No property management fee, no replacement reserves

`FIXED_COSTS` has no management line because the manager is compensated in-kind (free on-site housing).
**Every lender adds back a market management fee regardless of how the sponsor staffs it** — it normalizes
for a change of control. Same for reserves: `maintenance_reserve` of $400/mo is a repairs line, not a
capital replacement reserve.

| Adjustment | $ | Note |
|---|---:|---|
| True NOI (stabilized) | $222,850 | |
| − Market mgmt fee @ 4% EGI | −$17,492 | model has $0 |
| − Replacement/FF&E reserve @ 3% EGI | −$13,119 | model has $0 |
| **= Lender-adjusted NOI** | **$192,238** | **−9.6% vs. reported** |

Note: the IRC §119 employer-convenience housing exclusion (already flagged in the project's open
questions) is a *tax* position; it does not change the underwriting add-back.

### 3.4 Revenue assumptions — generally strong

✅ Pad rent $500 + 10% revenue share, occupancy haircut 0.85, lease-up ramp, event tiering by day,
seasonality, sports density, Monte Carlo on the soft variables. More rigorous than most first-time
sponsor models.

⚠️ **Percentage rent has no natural breakpoint.** `TRUCK_REV_SHARE_RATE = 0.10` applies from dollar one.
Standard retail structure is base rent + % of sales *above* a breakpoint (typically base ÷ pct =
$500 ÷ 0.10 = $60,000/yr). At $20K/mo per truck the dollars are similar — but the *structure* is
non-market and a leasing broker will flag it.

⚠️ **Vacancy is a single blended factor.** `TRUCK_OCCUPANCY = 0.85` is applied as an expected-value
haircut to both rent and % rent. With 4 pads there is no rent roll, no lease expiration schedule, no
explicit downtime between tenants, no separate **credit loss** provision (bad debt, typically 0.5–1% of
PGI, distinct from vacancy).

⚠️ **COTA parking is 20% of EGI and depends on a third party's event calendar.** No contractual right, no
shuttle agreement, no COTA relationship modeled. A lender will haircut this severely or exclude it from
sizing. The `bar_uplift_per_weekend` figures are also flagged in the project docs as inherited artifacts.

### 3.5 Expense assumptions

✅ Excellent Texas tax work — MB GRT + MB sales tax, parking sales tax, property tax on improvements,
employer payroll burden. Better than most professional models.

❌ Missing / oversimplified:

- **Management fee** and **replacement reserves** (§3.3)
- **Cost inflation is a lump-sum penalty**, not line-item growth:
  ```python
  inflation_penalty = ANNUAL_NUT * (cost_mult - 1)
  annual["total_noi"] -= inflation_penalty
  ```
  This inflates *only fixed costs*, and does so as a single subtraction below the line rather than growing
  each expense. It also means the inflation adjustment never appears in `summarize_annual`'s cost fields —
  the Waterfall tab won't show it. Grow each line in `FIXED_COSTS` instead.
- **Income tax sits below NOI** (`after_tax_noi`). Property-level NOI is pre-tax by definition; entity tax
  belongs in the equity waterfall. Minor, but it means `after_tax_fcf_yield` isn't a metric anyone will
  recognize.
- **Utility pass-through inflates EGI by $20K.** Correct to include as recovery income, but it must be
  excluded from per-pad and margin metrics or they'll be overstated.

### 3.6 Debt terms

Modeled: rate (12.5%), interest-only, revolving, and a genuine declining-balance payoff simulation.
**Not modeled:** amortization, IO period expiry, maturity/balloon, covenants, extension options,
refinance, prepayment, origination fees, or any construction-to-perm takeout. Appropriate for a personal
LOC; insufficient the moment an institution is approached.

---

## 4. Development pro forma benchmark

| Standard element | Present? | Comment |
|---|---|---|
| Total project cost | ⚠️ | Excludes land |
| Sources & Uses | ⚠️ | Uses only |
| Construction draw schedule | ❌ | `USE_OF_FUNDS` has status flags but no timeline |
| Interest reserve | ❌ | Construction-period interest is not capitalized |
| Contingency | ✅ | $6,300 (7.7% of hard cost — light; 10% typical) |
| Developer fee | ❌ | Standard 3–5% of cost, even if sponsor waives it |
| Land carry | ❌ | Property tax + insurance during construction |
| Permitting / soft costs | ✅ | $7,000 permits line, well-researched |
| TI / leasing commissions | ❌ | Pads are unimproved, so TI ≈ $0 — but state the assumption |
| Lease-up reserve | ⚠️ | `OPENING_CASH_RESERVE = $15,000` serves this role |

**Biggest gap:** the model begins at operating month 1. There is no month −6 to 0. Every dollar in
`USE_OF_FUNDS` is treated as spent at t=0 with no carry cost and no draw timing, which understates total
capitalized cost and makes the equity timing wrong for IRR.

---

## 5. Capital stack assessment

**Current:** $81,600 revolving personal LOC @ 12.5%, interest-only, against a 4.5-acre site owned free and
clear with a $1.4M cost basis.

| Metric | Value | Lender view |
|---|---:|---|
| LTC (land at cost) | 5.5% | Effectively an all-equity deal |
| LTV @ 9% cap | ~3.4% | Immaterial leverage |
| Debt yield | 236% | vs. 10% minimum |
| DSCR | 19.1x | vs. 1.35x minimum for F&B |

**Verdict: the capital stack is not a credit concern — it is arguably too conservative to be efficient.**
Observations for committee:

1. **This is a self-funded micro-development, not a leveraged CRE deal.** Reframe the question from
   "is the leverage safe" to "is the sponsor under-deploying capital."
2. **12.5% is expensive money for a 5.5% LTC position.** With land free and clear, a small land-secured
   commercial facility should price 350–450bp inside a personal LOC. However — `run_loc_payoff_schedule()`
   shows payoff by **Year 1, March**, with total interest of $3,184 vs. $30,600 under the flat assumption.
   The refinance saving is a few hundred dollars. **Not worth pursuing.**
3. **The real capital question is land utilization.** 4 pads on 4.5 acres, with 3 acres held for event
   parking, is very low intensity for a $1.4M basis. The 13.0% yield on cost is good; the question IC
   should ask is whether a $250K–$400K buildout (8–10 pads, permanent restrooms, covered pavilion)
   produces a materially better risk-adjusted return on the same land. The model can answer this —
   `TRUCK_SLOTS` is already a slider and the `Upside` scenario runs 6 pads — but it isn't framed as a
   capital-allocation decision.
4. **First-time F&B sponsor with no signed leases** is the actual credit issue, not leverage. Six LOIs ≠
   executed leases. Any institutional lender will require signed leases on 50–75% of pads before funding.

---

## 6. F&B / hospitality nuances

**Handled well — better than typical:**

- ✅ Seasonality (`SEASONALITY`, 0.65–1.00) — Austin patio weather
- ✅ Weekday/weekend split (`BAR_WEEKDAY_CUSTOMERS` / `BAR_WEEKEND_CUSTOMERS`)
- ✅ Event spikes (`COTA_EVENT_TIERS` with day-by-day occupancy curves + premium event pricing)
- ✅ Sports calendar (`SPORTS_DENSITY`, normalized to ~1.00 so it redistributes rather than inflates —
  genuinely disciplined)
- ✅ Correct F&B margin structure (COGS, shrinkage, card processing, tip/share comp)

**Missing:**

- ❌ **Weather as a stochastic variable.** `SEASONALITY` is deterministic. A rained-out F1 weekend is a
  real single-event tail risk on a 20%-of-EGI line. Add a rain-out probability to the Monte Carlo COTA draw.
- ❌ **No weather contingency in the physical plant.** Shade sails and mist fans are in `USE_OF_FUNDS`;
  there's no enclosed/covered fallback, so revenue is fully weather-exposed. Lenders will ask.
- ❌ **No sensitivity to a truck's own failure.** Vendor economics drive % rent; if a truck's sales fall
  the model haircuts occupancy but never sales-per-truck as a correlated shock.

**Operating metrics to add** (mirrors how F&B/hospitality lenders read an asset — the RevPAR analog):

```python
occupied_pads     = annual["total_trucks"] / (TRUCK_PAD_RENT * 12)     # effective
rev_per_occ_pad   = annual["total_trucks"] / occupied_pads             # RevPOP
rev_per_avail_pad = annual["total_trucks"] / TRUCK_SLOTS               # RevPAP ← the RevPAR analog
noi_per_pad       = annual["noi"] / TRUCK_SLOTS
revenue_per_acre  = annual["total_gross"] / LAND_ACRES
opex_ratio        = 1 - annual["noi"] / annual["total_gross"]
breakeven_occ     = ANNUAL_OPEX_NUT / (annual["total_gross"] / TRUCK_OCCUPANCY)
```

**RevPAP is the metric to lead with** — it captures rate and occupancy in one number and is what a
hospitality-trained credit officer will look for first.

---

## 7. Code and modeling hygiene

**Strengths — genuinely above amateur grade:**

- ✅ Clean separation of assumptions (§1) from calculation logic (§2–3); zero UI code in the engine
- ✅ 38-test regression suite with a full revenue/cost/NOI reconciliation test
- ✅ One-way sensitivity (`run_sensitivity_analysis`), 5 named scenarios, and Monte Carlo
- ✅ Assumptions carry inline provenance ("actual vendor quote" vs. "estimate") — auditors love this
- ✅ Deliberate conservatism rule, consistently applied and documented

**Refactors, in priority order:**

1. **Split the nut** (§2.1). One-line change, unblocks every lender metric.
2. **Return a time-indexed DataFrame, not dicts of scalars.** A lender auditing this wants to trace a line
   item across periods:
   ```python
   df = pd.DataFrame(months).set_index("period")   # rows = line items, cols = periods
   ```
   This is the single change that makes the model read like an Excel underwriting workbook.
3. **Replace the 12-parameter function signatures with a frozen `Assumptions` dataclass.**
   `calc_monthly_total()` takes 12 arguments; `run_monte_carlo()` takes 11. This is where scenario bugs
   hide (three have already been fixed).
   ```python
   @dataclass(frozen=True)
   class Assumptions:
       truck_slots: int = 4
       truck_pad_rent: float = 500
       exit_cap_rate: float = 0.09
       ...
   ```
   Immutable, so a scenario is `replace(base, truck_slots=6)`.
4. **Add two-way sensitivity (data tables).** Currently one-way only. IC expects rent × cap rate and
   rate × DSCR grids.
5. **Externalize scenarios to YAML/JSON.** `SCENARIOS` and `COTA_EVENT_TIERS` hardcode values that must be
   hand-updated when constants change — `CLAUDE.md` already flags this as a known drift risk.
6. **Add an explicit line-item pro forma ordering** so output reads top-down:
   PGI → vacancy → EGI → opex → NOI → debt service → CFADS → capex → CFAD.

---

## 8. Proposed Summary Output

```
════════════════════════════════════════════════════════════════════
  DEVELOPMENT SUMMARY — FOOD TRUCK PARK, DEL VALLE TX
════════════════════════════════════════════════════════════════════
  SOURCES & USES
    Land (contributed, at basis)              $1,400,000    94.5%
    Hard costs                                $   68,300     4.6%
    Soft costs (permits, contingency)         $   13,300     0.9%
    Total Uses                                $1,481,600   100.0%
    ── Sources ──
    Sponsor equity (land + cash)              $1,400,000    94.5%
    Personal LOC @ 12.5% IO                   $   81,600     5.5%

  STABILIZED OPERATIONS (Year 2)
    Effective Gross Income                    $  437,302
    Operating expenses (49.0%)                $ (214,452)
    Mgmt fee @ 4% / reserves @ 3%             $  (30,611)
    Net Operating Income                      $  192,238
      of which real property                  $   17,808     9%
      of which operating business (F&B)       $  174,430    91%

  VALUATION & LEVERAGE            @9.0% cap
    Implied value                             $2,136,000
    Yield on cost                                  13.0%
    Development spread                             +400 bp
    LTC / LTV / Debt yield              5.5% / 3.8% / 236%
    DSCR (stabilized)                             19.1x

  RETURNS (5-yr hold, 9.0% exit cap, 3% sale cost)
    Unlevered IRR / equity multiple         19.8% / 2.15x
    Levered IRR / equity multiple           21.4% / 2.28x
    Cash-on-cash, stabilized                       12.9%
    Payback (cumulative CF)                     Year 8

  SENSITIVITY — Unlevered IRR
                    Exit Cap Rate
    Rent      8.0%     9.0%    10.0%    11.0%
    −10%     19.1%    16.4%    14.2%    12.4%
    Base     22.2%    19.8%    18.1%    15.9%
    +10%     25.0%    22.7%    20.6%    18.8%
════════════════════════════════════════════════════════════════════
```

**Presentation formats institutional investors expect:**

- **Two-way data tables** (seaborn/matplotlib heatmap or styled DataFrame) — rent × cap rate,
  cap rate × interest rate
- **Tornado chart** for single-variable sensitivity, ranked by NOI impact — the data already exists in
  `run_sensitivity_analysis()`
- **Sources & Uses stacked bar**
- **Monthly cash flow waterfall** with cumulative equity line and payback marker
- **Monte Carlo CDF, not histogram** — read "P(IRR ≥ 15%)" directly off the curve; currently histograms
- **Annual pro forma table** with line items as rows, periods as columns — the format every analyst reads first

---

## Implementation tracker

Work top-down. Items 1–4 are mechanical and the existing test suite will verify them. Items 5–6 are new
modules. Run `pytest -q` after every change.

> **Status (2026-07-29):** Items 1–5 are implemented, plus a new "CRE Investment Summary" 12th
> dashboard tab surfacing all of it. **Implementation diverged from the literal wording below in one
> way, by explicit user direction:** the original 11 tabs keep their existing plain-language field names
> and labels (`noi`, `fcf_yield`, `monthly_nut_coverage`, "FCF Yield", "Nut Coverage") completely
> unchanged — `fcf_yield` was **not** renamed to `yield_on_cost`, and `monthly_nut_coverage` was **not**
> renamed to `fixed_charge_coverage` in the engine. Instead, `total_noi` itself was corrected at the
> source (now genuinely pre-debt-service), and every new CRE-specific metric (yield on cost including
> land, cap rate value, LTC/LTV/debt yield, IRR/NPV/equity multiple) was added as new, separate functions/
> fields consumed **only** by the new tab, which uses full CRE vocabulary with tooltip definitions. See
> `CLAUDE.md`'s "NOI vs. cash flow" and "Land basis" sections for the exact mechanics. Items 6–14 remain
> outstanding.

### Critical — blocks any lender/LP conversation

- [x] **1. Restate NOI before debt service.** ~~Split `FIXED_COSTS` into `OPERATING_FIXED_COSTS` +
      `MONTHLY_DEBT_SERVICE`. Update `calc_monthly_total()`, `summarize_annual()`, and every dashboard tab
      that reads `noi`. Rename `monthly_nut_coverage` → `fixed_charge_coverage` (FCCR).~~ Done as
      described except the rename: `monthly_nut_coverage` keeps its name/formula in the engine and
      existing tabs (unchanged value); the CRE tab labels the same figure "FCCR" for display only.
- [x] **2. Include land in basis.** Added `TOTAL_CAPITALIZED_BASIS = LAND_PURCHASE_PRICE + TOTAL_PROJECT_COST`
      and `EQUITY_BASIS`. `fcf_yield` was **kept as-is** (buildout-only denominator, unchanged name/value
      in the 11 existing tabs) per the "existing tabs stay plain-language" decision — the land-inclusive
      `yield_on_cost` is a new, separate field (`calc_valuation_and_leverage()`), shown only on the CRE tab.
- [x] **3. Bifurcate real property NOI from operating business NOI.** Added `real_estate_contribution` /
      `business_contribution` (monthly) and `total_real_estate_contribution` / `total_business_contribution`
      (annual) — pre-shared-overhead segment contribution, not fully-loaded segment NOI (documented in
      both files as a deliberate simplification: the operating nut, management fee, reserve, and per-event
      COTA staffing cost aren't allocated between segments). Surfaced on the CRE tab.

### High — required for a credible development pro forma

- [x] **4. Add market management fee (4% EGI) + replacement/FF&E reserve (3% EGI).** Implemented as real
      variable costs in `calc_monthly_total()` (% of EGI ex. utility pass-through), by explicit user
      decision to flow through the *entire* model's cash flow, not just the CRE tab's valuation math —
      stabilized NOI/Free Cash Flow across all 11 existing tabs dropped by the expected ~$25–30K/yr.
- [x] **5. Add exit/reversion and a returns engine.** Implemented as `run_returns_analysis()` (Section 9)
      with `MARKET_CAP_RATE`/`HOLD_PERIOD_YEARS`/`SALE_COST_PCT`/`DISCOUNT_RATE` constants, all exposed as
      sliders on the new tab. Computes unlevered + levered IRR, NPV, equity multiple, and Year-1
      cash-on-cash (finally against a real `EQUITY_BASIS`, not cost). `run_cre_sensitivity_grid()` adds
      the revenue × exit-cap-rate IRR grid. Debt is held flat through the hold (same conservative
      convention as `MONTHLY_NUT` elsewhere), not the declining balance from `run_loc_payoff_schedule()` —
      a deliberate consistency choice, documented in the function's docstring.
- [ ] **6. Model the development period.** Construction draw schedule over `USE_OF_FUNDS`, capitalized
      interest reserve, land carry, developer fee. Shift operating month 1 to follow it. **Not started.**
- [ ] **7. Obtain signed leases on ≥50% of pads** before treating `TRUCK_Y1_FILL_RAMP` as anything but a
      guess. *(Business action, not code.)*

### Medium — quality and presentation

- [ ] **8. Line-item cost inflation** instead of the lump-sum `inflation_penalty` subtraction.
- [ ] **9. Add operating metrics:** RevPAP, RevPOP, NOI/pad, revenue/acre, opex ratio, break-even occupancy.
- [ ] **10. Two-way sensitivity tables** (rent × cap rate, cap rate × interest rate) + tornado chart.
- [ ] **11. Weather stochastics** in Monte Carlo (rain-out probability on COTA event days).
- [ ] **12. Credit loss provision** separate from vacancy (0.5–1% of PGI).
- [ ] **13. Percentage-rent breakpoint** structure on `TRUCK_REV_SHARE_RATE`.
- [ ] **14. Move income tax below NOI** into an equity waterfall; retire `after_tax_fcf_yield`.

### Structural refactors

- [ ] **15. `Assumptions` frozen dataclass** replacing 12-parameter signatures.
- [ ] **16. Time-indexed DataFrame output** for auditability.
- [ ] **17. Externalize `SCENARIOS` / `COTA_EVENT_TIERS`** to YAML.
- [ ] **18. Line-item pro forma ordering** in all output (PGI → vacancy → EGI → opex → NOI → DS → CFADS).

---

## Appendix A — reproducing the figures

**Superseded by the implementation.** The original version of this appendix hand-rolled a
"lender-adjusted NOI" (adding back LOC interest, subtracting management fee/reserve) because none of
that existed in the engine yet. As of items 1–5 landing, `annual["total_noi"]` **already is** that figure
— no manual reconstruction needed — and dedicated functions exist for everything else. Regenerate the
figures below with:

```bash
.venv/bin/python - <<'EOF'
import food_truck_park_model as M

for yr in (1, 2):
    _, a = M.run_annual_projection(year=yr)
    print(f"Year {yr}: EGI ${a['total_gross']:,.0f} | "
          f"true NOI ${a['total_noi']:,.0f} | "
          f"cash flow after debt service ${a['total_net_cash']:,.0f}")

_, stab = M.run_annual_projection(year=2)
val = M.calc_valuation_and_leverage(stab)
print(f"Yield on cost: {val['yield_on_cost']:.2%} | "
      f"Implied value @ {val['cap_rate']:.0%} cap: ${val['implied_value']:,.0f} | "
      f"LTC {val['ltc']:.1%} | LTV {val['ltv']:.1%} | debt yield {val['debt_yield']:.1%}")
print(f"Real estate contribution: ${stab['total_real_estate_contribution']:,.0f} | "
      f"Business contribution: ${stab['total_business_contribution']:,.0f}")

returns = M.run_returns_analysis()
print(f"Unlevered IRR {returns['unlevered_irr']:.1%} / {returns['unlevered_equity_multiple']:.2f}x | "
      f"Levered IRR {returns['levered_irr']:.1%} / {returns['levered_equity_multiple']:.2f}x")
EOF
```

**Key figures as implemented (Year 1 / stabilized, default assumptions):**

| Figure | Value |
|---|---:|
| EGI, Year 1 / stabilized | $375,098 / $437,302 |
| True NOI (before debt service), Yr 1 / stabilized | $159,256 / $193,238 |
| Cash flow after debt service, Yr 1 / stabilized | $149,056 / $183,038 |
| Real estate / business contribution, stabilized | $217,202 / $87,631 |
| Yield on cost (land + buildout, stabilized) | 13.0% |
| Implied value @ 9% cap | $2,147,089 |
| LTC / LTV / debt yield | 5.5% / 3.8% / 236.8% |
| Unlevered IRR / equity multiple, 5-yr @ 9% exit cap | 20.3% / 2.22x |
| Levered IRR / equity multiple, 5-yr @ 9% exit cap | 20.7% / 2.25x |
| Monthly nut (opex + LOC interest) | $5,192 |

Note the true-NOI figures here are *lower* than the pre-implementation draft's "adjusted NOI" estimates
(e.g. $193,238 vs. the old draft's $192,238 estimate for stabilized) — close, but not identical, because
the actual management-fee/reserve base (EGI excluding utility pass-through) differs slightly from the
draft's back-of-envelope calculation. This table is the authoritative one; treat the earlier draft
figures in git history as superseded.

---

## Appendix B — glossary of CRE terms

| Term | Definition |
|---|---|
| **NOI** | Net Operating Income = EGI − operating expenses, **before** debt service, capex, depreciation, income tax |
| **EGI** | Effective Gross Income = potential gross income − vacancy − credit loss + recovery income |
| **PGI** | Potential Gross Income — revenue at 100% occupancy |
| **Cap rate** | NOI ÷ value. The market's required unlevered yield. Value = NOI ÷ cap rate |
| **Yield on cost** | Stabilized NOI ÷ total capitalized basis. Compare to market cap rate; the gap is the **development spread** |
| **DSCR** | NOI ÷ annual debt service. Min 1.20–1.30x general CRE; 1.35–1.50x hospitality/F&B |
| **FCCR** | Fixed Charge Coverage Ratio — like DSCR but the denominator includes cash opex as well as debt service |
| **Debt yield** | NOI ÷ loan amount. Value-independent leverage test. Min ~9–11% CRE, 11–13% F&B |
| **LTV / LTC** | Loan ÷ value / Loan ÷ total cost |
| **CFADS** | Cash Flow Available for Debt Service — NOI less reserves, before principal and interest |
| **Reversion** | Sale proceeds at end of hold = terminal NOI ÷ exit cap rate, less sale costs |
| **Equity multiple** | Total distributions ÷ equity invested. Not time-weighted |
| **IRR** | Discount rate at which NPV of all cash flows = 0. Time-weighted |
| **Cash-on-cash** | Annual pre-tax cash flow after debt service ÷ equity invested |
| **BEV** | Business Enterprise Value — the going-concern value of an operating business, distinct from real property value |
| **RevPAR / RevPAP** | Revenue per available room (hospitality) / per available pad (this asset). Captures rate and occupancy in one number |
| **TI / LC** | Tenant improvements / leasing commissions |
| **Interest reserve** | Construction-period interest funded from the loan rather than paid from operations |
| **Developer fee** | Compensation to the sponsor for developing, typically 3–5% of total cost |
| **Stabilization** | The point at which the asset reaches sustainable occupancy and NOI |
