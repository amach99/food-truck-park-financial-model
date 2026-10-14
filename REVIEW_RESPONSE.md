# Response to the Independent Review

> **Superseded figures — read this first (updated 2026-10-14).** This memo records the
> 2026-09-04 response, written against the earlier **$500,000** version of the model. Its
> verdicts still stand, but its dollar figures and DSCRs do not. Since then the engine took
> the Sep 9 audit and the Sep 30 cost and timing decisions (see `ANOOP_SEP9_AUDIT.md`): the
> loan is now **sized to its uses** (about $563.6K Base), septic is the real **$212,000**
> quote (gated), the reserve floor is **$40,000**, opening is six months after closing, and
> labor is scheduled by weekday, weekend, season and race day (about $108K/yr). Two items
> this memo lists as open are now done in the engine: **PropCo/OpCo statements with the
> intercompany lease** (`run_propco_opco_split()`) and a **construction draw schedule**
> (`build_construction_draw_schedule()`). Some test names cited below were renamed in that
> merge. For current numbers, run `python build_business_plan.py plan.md`, which reads every
> figure from the engine.

**Review:** *Independent Review of the Del Valle Food Truck Park & Container Bar Business Plan*
— business plan dated 2026-08-26, review completed 2026-08-31, recommendation
**"Hold for revision before lender submission."**

**This response:** 2026-09-04. Every item below was checked against the calculation engine
(`food_truck_park_model.py`) rather than against the business plan, because the plan itself
turned out to be stale — see [What the reviewer could not see](#what-the-reviewer-could-not-see).

**Bottom line:** the reviewer was right on substantially every point, and on the labor item
they *understated* the problem. Correcting it changes the credit story materially. The base
case still services debt comfortably. The claim that the deal is safe without COTA does not
survive, and that claim has been withdrawn rather than re-argued.

---

## The one finding that changes the deal

The reviewer wrote that "a manager plus one bartender cannot credibly cover the proposed hours
without scheduled wages, overtime, payroll taxes, relief coverage, and proper treatment of
employer-provided lodging." That is correct, and it was worse than a presentation problem.

The model paid the bartender **only** a 5% share of beverage revenue. Across the modelled
11-hour daily service window, 365 days a year, that worked out to:

| | Effective hourly compensation |
|---|---|
| Year 1 | **$2.11/hr** |
| Year 2 | **$2.72/hr** |
| Federal / Texas minimum | $7.25/hr |

That is a wage-and-hour exposure, not a modelling preference. Labor is now built from hours in
`calc_labor_cost()`: a daytime beverage attendant at $13/hr, an evening bartender at $16/hr, an
extra body on every COTA event day, a 10% overtime allowance, a $24,000 manager salary, and
10% employer burden on all of it — about **$96,000/yr** of cost the model did not previously
carry.

**What that does to coverage:**

| Stabilized case | DSCR before | DSCR now |
|---|---|---|
| Base | 3.77x | **2.27x** |
| COTA halved | 2.86x | **1.33x** |
| **No COTA at all** | **1.94x** | **0.46x** |
| Stacked bank-case stress | 1.99x | **0.52x** |

Year 1 coverage is **1.48x** (was 3.08x), just under the 1.50x end of a typical F&B floor.

**The plan's central credit argument is withdrawn.** It read: *"if COTA closed permanently and
the park never sold another event parking space, projected stabilized coverage would be 1.94x
… COTA is the upside in this deal, not the foundation."* With labor properly loaded, a no-COTA
year produces **negative** cash flow of about $29,600 and covers 0.46x of debt service. COTA is
the foundation. The revised plan says so, and leans on the fact that COTA's F1 contract runs
through 2034 rather than pretending the concentration is not there.

This is the single most important thing in this document. It was not caught by the reviewer's
own arithmetic, and it would have been caught by the bank.

---

## Highest-priority corrections

| # | Reviewer item | Verdict | What changed |
|---|---|---|---|
| C1 | Equity schedule ($1,346,800 vs $1,174,800) | **Agree** | The engine was right; the plan's *table* was wrong — its rows omitted the new improvements and deducted only the LOC payoff. `EQUITY_BASIS` (equity in the capitalized asset) and `TOTAL_ECONOMIC_EQUITY` (that plus unspent reserve) are now separate named constants. At revised figures: **$1,202,800** and **$1,346,800**. The dashboard table now shows every row and sums. `test_economic_equity_exceeds_capitalized_equity_by_the_reserve` |
| C2 | Opening timeline not credible | **Agree** | `OPENING_MONTH` moved **Sept 2026 → March 2027**. `run_pre_opening_period()` is new: 4 months of debt service, insurance, property tax and accounting accrue against zero revenue ($26,126), drawn from the reserve. The model previously had *no* pre-opening cost at all. `test_pre_opening_period_burns_reserve_before_any_revenue` |
| C3 | Labor and housing | **Agree — understated by the reviewer** | See above. Lodging is disclosed, not expensed, with IRC §119 and FLSA §3(m) both flagged as counsel/CPA items rather than assumed. |
| C4 | Collateral value / 21.9% LTV | **Agree** | Blended-income LTV is gone as a headline. Real property income is capitalized at 8.5%; the bar is valued at 2.5x EBITDA as a going concern. LTV is reported **four ways** (segment 40.2%, cost 29.4%, land basis 35.7%, blended indication 36.3%). The $1.4M land basis is labelled a related-party transfer price wherever it appears. `test_valuation_splits_real_estate_from_the_operating_business` |
| H1 | Vendor revenue — no executed leases | **Agree, no model change** | Business action. The lease-up ramp and 85% occupancy haircut already encode it; percentage rent is now explicitly labelled non-contractual (see H6). Signed LOIs remain outstanding. |
| H2 | Permits and contingency not credible | **Agree** | Permits **$1,700 → $12,000** (site development, OSSF/septic, health, TxDOT driveway, fire/life safety, CO). Contingency **$6,300 → $24,000** — 3% → 12% of remaining hard costs. Both funded from Reserve & Safety Cash, so the ask stays exactly $500,000. Still needs a real permit matrix and fixed bids. `test_contingency_is_a_credible_share_of_remaining_hard_costs` |
| H3 | $172K reserve vaguely defined | **Agree** | Reduced to **$144,000** by H2, and it is no longer notional: `RESERVE_AND_SAFETY_CASH` derives from `USE_OF_FUNDS`, the pre-opening burn is deducted, and the tracker opens from **$117,874**. Draw conditions, minimum balance and release covenant are drafting items for the plan, not the model. |
| H4 | Liquor permit — held or applied for? | **Agree, document fix** | Reconciled to "held" throughout; the appendix no longer asks for application status. The permit is also now stated to be **not transferable lender collateral**. |
| H5 | Monte Carlo not reproducible | **Partly agree** | The simulation was already deterministic for a given seed and tested as such. What was missing was *disclosure*. `MONTE_CARLO_DISTRIBUTIONS` and `MONTE_CARLO_FIXED_PARAMETERS` now publish seed, per-parameter distribution, spread and bounds, rendered into both the dashboard and the plan appendix. **Volunteered against interest:** every parameter is drawn independently, so the true downside tail is fatter than the simulation shows. |
| H6 | 58% revenue-mix claim unsupported | **Agree** | Modelled stabilized figures: **50.4%** property-and-parking (matching the reviewer's own 50.4%), of which strictly contractual pad rent is **4.3%**. Event parking is labelled transactional. Computed in `summarize_annual()` so no document can drift. `test_revenue_mix_shares_match_a_hand_computation` |

---

## Corrections and clarifications table

| Reviewer item | Verdict | Resolution |
|---|---|---|
| Year 1 debt yield shown as 41.1% | **Agree** | 41.1% was the stabilized figure. Year 1 is **16.2%** at revised NOI; stabilized is **24.8%**. Both now labelled by year. |
| Loan-to-cost 29.8% | **Agree** | Now **29.4%** on the revised basis of $1,702,800. |
| Debt service $54,528 | **Agree** | The payment was rounded to $4,544 then multiplied by 12. `LOAN_MONTHLY_PAYMENT` is now carried unrounded and `ANNUAL_DEBT_SERVICE` is **$54,522**; rounding happens at display only. This also removes a mismatch where the interest calculation used the exact payment while cash flow used the rounded one. `test_loan_monthly_payment_derives_from_amortization_formula` |
| "Six" event tiers | **Agree** | **Seven paid** tiers plus one free (track day, not in the modelled calendar). `test_seven_paid_event_tiers_are_modelled` |
| Rounding variances | **Agree** | Addressed by the unrounded payment above; component totals now come from `summarize_annual()` rather than being re-derived per call site. |
| Mixed-beverage tax on cash receipts | **Agree** | Prices are tax-inclusive, and the model was applying the 6.7% gross receipts tax to a base that already included the 8.25% sales tax — taxing a tax. Sales tax is now backed out first; parking tax likewise. Worth ~$1.6K/yr, **in the model's favour**, and disclosed as such. `test_mixed_beverage_taxes_are_not_stacked` |
| NASCAR event named EchoPark | **Agree** | Now **DuraMAX Texas Grand Prix**. `test_nascar_tier_names_the_correct_2027_event` |
| "Positive from the fifth month onward" | **Agree** | Month five was negative. Corrected; the monthly table now speaks for itself under the March 2027 calendar. |
| Fixed costs don't inflate despite the methodology | **Agree** | Inflation was a single lump subtracted from annual NOI, so no line ever moved. Now applied line by line via `opex_multiplier`, covering operating costs **and wages**, never the loan payment. `test_operating_costs_inflate_line_by_line_in_later_years` |
| COTA distance alternates 0.5 / two miles | **Agree** | Re-measured. The parcel sits north of the Dollar General and fronts FM 812 **directly opposite COTA property**, separated only by the road right-of-way. Nearest COTA parking facility (Lot T) 0.5 mi by road; main gate 1.3 mi by road. The old "two miles" traces to the 2.24 mi road distance to the amphitheater. Both figures now stated separately and labelled. |
| Utility rebilling "legally required" | **Agree** | Softened from an assertion to an assumption pending confirmation of the governing commercial submetering rule. |
| $500 + 10% pad rent is aggressive | **Acknowledged, no change** | The reviewer is right that effective rent is ~$2,500/mo (12.5% of sales) at modelled volumes. These are the intended terms, not achieved terms, and they are labelled as such. If leases sign at lower economics the model takes it directly through `TRUCK_PAD_RENT` / `TRUCK_REV_SHARE_RATE`. |
| Parking capacity, TxDOT, ADA | **Agree, out of model scope** | 270 spaces on three acres is a site-engineering question, not a financial one. Sealed layout, TxDOT driveway review and accessible-space count are on the evidence list. |
| Entities — separate propco/opco | **Agree, deferred** | See [Not done](#not-done-and-why). |

---

## What the reviewer could not see

Three things surfaced only by checking the plan against the live engine.

**1. The business plan's Section 8 was already stale.** The document was produced before the
TABC double-count fix (commit `73547c7`). It carried property tax on improvements of $5,604/yr
against the model's $5,496 — so every figure in Sections 8.1–8.3 was off by roughly $108/yr
(plan NOI $168,070 vs engine $168,178). The reviewer validated the document's *internal*
arithmetic and could not have detected this.

**This is why the plan is now generated, not typed.** `build_business_plan.py` imports the model
and emits the document, so the two cannot diverge again. It also satisfies the reviewer's
"reproducible projection workbook" request.

**2. The reserve in the narrative was not the reserve in the model.** The plan said $172,000 of
reserve covered the winter trough. `run_cash_reserve_tracker()` was running off an unexplained
`OPENING_CASH_RESERVE = 15_000` — a figure eleven times smaller. Now derived from
`USE_OF_FUNDS`, net of the pre-opening burn.

**3. There was no pre-opening period at all.** Debt service starts at closing; the model's month
one already had revenue in it. `CONSTRUCTION_PERIOD_MONTHS` existed but only shifted IRR
discounting — it carried no cost. Fixed by C2 above.

**4. The break-even search was silently saturating.** Its bisection had a hard 4.0x ceiling and
returned that ceiling when a target could not be reached — so once labor entered the cost base,
every coverage target printed the *same* customer count and read like a real break-even.
Unreachable targets now say so. `test_breakeven_search_reports_unreachable_targets_honestly`

---

## Two consequences worth stating plainly

**Leverage is currently dilutive.** At stabilized NOI, yield on cost is **7.3%** against a 10%
loan rate, so levered IRR now sits *below* unlevered IRR and the development spread against a
9% cap rate is **−1.7 points**. This is arithmetic, not an error, and it flips the moment NOI
rises or the rate comes in below the placeholder. It is a direct consequence of carrying the
$1.4M land basis and $96K of labor against this income. `test_returns_analysis_irr_is_sane` now
asserts the leverage *direction conditionally on that spread* rather than assuming the deal
out-earns its debt.

**The all-day beverage window barely covers its own labor.** It generates about $48,600/yr at
stabilization and consumes roughly $30,800/yr of daytime attendant wages before COGS and tax.
That is a real operating decision — shortening the daytime window would cut cost faster than
revenue — and it is now visible because labor is scheduled by hour. Not changed unilaterally,
because it alters the concept rather than correcting an error.

---

## Not done, and why

**Separate property-company and operating-company projections with the intercompany lease.**
The reviewer is right that a lender secured by real property will want these split. It is
deliberately deferred: it is an entity-reporting refactor rather than an underwriting
correction, and folding it into this change would roughly double its size while delaying every
correction above. Logged as item 24 on `CRE_UNDERWRITING_REVIEW.md`'s tracker. The model already
computes the property/business segment split that such a separation would build on.

---

## Evidence still required before submission

Unchanged from the reviewer's list — none of it is code, and none of it is satisfied by this
revision:

- [ ] Executed vendor leases or robust LOIs for at least two pads, with deposits and vendor sales support
- [ ] Title commitment, survey, lien search, environmental review, deed and related-party basis documentation
- [ ] **Independent as-is / as-complete appraisal** — the single most important open item, since every LTV in the model is an indication until it exists
- [ ] Whether COTA **owns** or merely operates the land across FM 812 (title question; changes the wording of the adjacency claim)
- [ ] Permit matrix, site and traffic plan, sealed 270-space layout, septic approval, TxDOT access approval, residential-occupancy determination
- [ ] Fixed bids, construction schedule, draw schedule — which will replace the March 2027 opening estimate with a real date
- [ ] Current tax bill, post-improvement tax estimate, insurance and liquor-liability quotes (insurance is still a $900/mo estimate and should be re-quoted now that the bar pours cocktails)
- [ ] Guarantor personal financial statements, tax returns, liquidity evidence, global debt-service analysis
- [ ] Property-company and operating-company projections, intercompany lease, cash-management structure, reserve controls
- [ ] LOC statements, invoices, lien waivers and payoff support for the $120,000 refinance
- [ ] **A staffing schedule and wage confirmation.** The $13/$16/$15 rates and the $24,000 manager salary are estimates. They are now the second-largest cost in the model and deserve real quotes.
- [ ] CPA confirmation of worker classification, the lodging treatment under IRC §119 and FLSA §3(m), and the 28% blended tax rate

---

## Verification

```bash
pytest -q
```

90 tests pass. Sixteen are new and lock down the corrections above; each is named in the tables.
Two pre-existing tests were rewritten rather than deleted, and both rewrites are commented with
why:

- `test_payroll_burden_rides_on_bartender_share` → `test_payroll_burden_rides_on_all_wages`
- `test_bank_case_underwriting_is_more_conservative_than_base_case` now asserts the stacked
  stress case falls **below** 1.35x. That is the finding, recorded so it stays visible. If a
  future change lifts it back over the floor, that test should fail — update it and say why
  coverage improved.
