"""
Regression tests for the food truck park financial model.

These lock down the invariants that have actually broken before during
development, rather than re-asserting arithmetic the engine obviously does
correctly. Two classes of bug motivated most of this file:

  1. "COTA total" undercounting. Several call sites reconstruct an event
     total from its parts; twice, adding a new event-day revenue stream
     (daytime beverages, then a since-removed tobacco stream) silently
     broke every one of them. test_cota_gross_is_sum_of_parts and friends
     catch that class directly.
  2. Cost totals drifting away from NOI. Whenever a new cost line is added
     to calc_monthly_total but not to summarize_annual (or vice versa), the
     full reconciliation below stops balancing.

Run with:  pytest -q
"""

import pytest

import food_truck_park_model as m


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def year1():
    """Default Year 1 projection (with ramps)."""
    months, annual = m.run_annual_projection()
    return months, annual


@pytest.fixture(scope="module")
def event_month():
    """A COTA event month, steady state (October carries F1)."""
    return m.calc_monthly_total(20, 58, 10)


# ---------------------------------------------------------------------------
# Reconciliation: every dollar of revenue is accounted for
# ---------------------------------------------------------------------------

def _total_variable_costs(annual):
    """All variable cost buckets exposed by summarize_annual."""
    return (
        annual["total_cogs"]
        + annual["total_grt"]
        + annual["total_mb_sales_tax"]
        + annual["total_daytime_beverage_cogs"]
        + annual["total_daytime_beverage_tax"]
        + annual["total_cc_processing"]
        + annual["total_shrinkage"]
        + annual["total_labor_wages"]
        + annual["total_payroll_burden"]
        + annual["total_cota_parking_upkeep"]
        + annual["total_cota_parking_sales_tax"]
        + annual["total_cota_cost"]
        + annual["total_utility_cost"]
        + annual["total_management_fee"]
        + annual["total_replacement_reserve"]
    )


def test_annual_reconciles_to_noi(year1):
    """Gross - variable - opex must equal true NOI exactly.

    This is the single most valuable assertion in the file: it fails the
    moment a cost is added to the monthly calc but omitted from the annual
    summary, which is exactly how the dashboard's cost tables go stale.
    NOI is defined BEFORE debt service (CRE convention), so this reconciles
    against ANNUAL_OPEX_NUT, not the full ANNUAL_NUT - see
    test_noi_reconciles_to_net_cash_flow for the debt-service step.
    """
    _, annual = year1
    residual = (annual["total_gross"]
                - _total_variable_costs(annual)
                - annual["total_opex"]
                - annual["total_noi"])
    assert abs(residual) < 1.0


def test_noi_reconciles_to_net_cash_flow(year1):
    """NOI minus debt service must equal net cash flow exactly.

    Locks in the NOI/CFADS split: NOI is before debt service (true CRE
    NOI), net_cash_flow is after it. If someone reintroduces LOC interest
    into the NOI calc (the bug this whole refactor fixed), this fails.
    """
    _, annual = year1
    residual = (annual["total_noi"] - m.ANNUAL_DEBT_SERVICE
                - annual["total_net_cash"])
    assert abs(residual) < 1.0


def test_noi_is_before_debt_service(year1):
    """NOI must exceed net cash flow by exactly the annual debt service."""
    _, annual = year1
    assert annual["total_noi"] > annual["total_net_cash"]
    assert (annual["total_noi"] - annual["total_net_cash"]) == pytest.approx(
        m.ANNUAL_DEBT_SERVICE)


def test_management_fee_and_reserve_scale_with_egi(year1):
    """Management fee (4%) and replacement reserve (3%) apply to EGI net of
    the pass-through utility billing, which carries no fee (it's a wash)."""
    _, annual = year1
    egi_ex_utility = annual["total_gross"] - annual["total_utility_billed"]
    assert annual["total_management_fee"] == pytest.approx(
        egi_ex_utility * m.MANAGEMENT_FEE_RATE)
    assert annual["total_replacement_reserve"] == pytest.approx(
        egi_ex_utility * m.REPLACEMENT_RESERVE_RATE)


def test_real_estate_and_business_contribution_reconcile(year1):
    """Segment contributions, less shared overhead, must equal NOI before opex."""
    _, annual = year1
    total_net_before_fixed = annual["total_noi"] + m.ANNUAL_OPEX_NUT
    residual = (annual["total_real_estate_contribution"]
                + annual["total_business_contribution"]
                - annual["total_cota_cost"]
                - annual["total_management_fee"]
                - annual["total_replacement_reserve"]
                - total_net_before_fixed)
    assert abs(residual) < 1.0


def test_monthly_gross_is_sum_of_streams(event_month):
    """total_gross_revenue must equal the six streams added up."""
    r = event_month
    parts = (r["truck_gross"] + r["bar_revenue"] + r["seasonal_revenue"]
             + r["daytime_beverage_revenue"]
             + r["utility_billed"]
             + r["cota_parking"] + r["cota_bar_uplift"]
             + r["cota_daytime_bev_uplift"])
    assert r["total_gross_revenue"] == pytest.approx(parts)


def test_cota_gross_is_sum_of_parts():
    """calc_cota_event_revenue's gross must include the beverage uplift.

    Regression guard: a new event-day revenue stream that isn't folded into
    `gross` makes every downstream "COTA total" undercount.
    """
    cota = m.calc_cota_event_revenue(["tier1_f1"])
    parts = (cota["parking"] + cota["bar_uplift"]
             + cota["daytime_bev_uplift"])
    assert cota["gross"] == pytest.approx(parts)


def test_no_events_returns_all_zero_keys():
    """An empty event list must still expose every key, all zeroed."""
    cota = m.calc_cota_event_revenue([])
    for key in ("parking", "bar_uplift", "daytime_bev_uplift",
                "gross", "incremental_cost", "net"):
        assert cota[key] == 0, f"{key} should be 0 with no events"


# ---------------------------------------------------------------------------
# COTA impact slider
# ---------------------------------------------------------------------------

def test_cota_impact_multiplier_default_matches_unscaled_baseline():
    """multiplier=1.0 (the implicit default) must be bit-for-bit identical
    to calling calc_cota_event_revenue with no multiplier argument at all -
    this is the guarantee that adding the slider doesn't silently change
    today's baseline numbers for anyone not touching it."""
    cota_default = m.calc_cota_event_revenue(["tier1_f1"])
    cota_explicit = m.calc_cota_event_revenue(["tier1_f1"], impact_multiplier=1.0)
    assert cota_default == cota_explicit


def test_cota_impact_multiplier_zero_zeroes_everything():
    """Slider at 0% (multiplier=0.0) must behave exactly like an empty
    calendar, even with real events passed in - "as if COTA didn't exist"."""
    cota = m.calc_cota_event_revenue(["tier1_f1", "tier2_nascar"], impact_multiplier=0.0)
    for key in ("parking", "bar_uplift", "daytime_bev_uplift",
                "gross", "incremental_cost", "net"):
        assert cota[key] == 0, f"{key} should be 0 at multiplier=0.0"


def test_cota_impact_multiplier_scales_linearly():
    baseline = m.calc_cota_event_revenue(["tier1_f1"])
    doubled = m.calc_cota_event_revenue(["tier1_f1"], impact_multiplier=2.0)
    assert doubled["parking"] == pytest.approx(baseline["parking"] * 2)
    assert doubled["bar_uplift"] == pytest.approx(baseline["bar_uplift"] * 2)
    assert doubled["daytime_bev_uplift"] == pytest.approx(baseline["daytime_bev_uplift"] * 2)
    assert doubled["incremental_cost"] == pytest.approx(baseline["incremental_cost"] * 2)


def test_cota_impact_multiplier_default_leaves_annual_projection_unchanged():
    """Threading the new parameter through run_annual_projection must not
    move any number for callers that don't pass it - regression guard for
    the whole wiring chain (calc_monthly_total -> run_annual_projection)."""
    _, without_arg = m.run_annual_projection(year=2)
    _, with_default = m.run_annual_projection(year=2, cota_impact_multiplier=1.0)
    assert without_arg == with_default


def test_cota_impact_multiplier_zero_removes_cota_but_not_truck_boost():
    """At 0%, COTA revenue disappears entirely and food trucks see NO boost
    (event_month_boost only applies above baseline, multiplier > 1.0)."""
    _, off = m.run_annual_projection(year=2, cota_impact_multiplier=0.0)
    _, baseline = m.run_annual_projection(year=2)
    assert off["total_cota_parking"] == 0
    assert off["total_cota_bar"] == 0
    assert off["total_cota_daytime_bev"] == 0
    assert off["total_cota_cost"] == 0
    assert off["total_trucks"] == pytest.approx(baseline["total_trucks"])
    assert off["total_gross"] < baseline["total_gross"]


def test_cota_impact_multiplier_above_baseline_boosts_truck_traffic():
    """Above 1.0, event months pull extra sales/occupancy into the food
    trucks themselves, not just parking/bar/beverage revenue - and that
    lifts total_daytime_beverage too, since it rides on truck traffic."""
    _, baseline = m.run_annual_projection(year=2)
    _, high = m.run_annual_projection(year=2, cota_impact_multiplier=2.0)
    assert high["total_trucks"] > baseline["total_trucks"]
    assert high["total_daytime_beverage"] > baseline["total_daytime_beverage"]
    assert high["total_cota_parking"] == pytest.approx(baseline["total_cota_parking"] * 2)


def test_cota_truck_boost_only_applies_in_event_months():
    """A month with no COTA events on the calendar must see zero truck
    boost even when the slider is maxed out - only event months benefit."""
    no_event_month = m.calc_monthly_total(20, 58, 1, cota_events=[],
                                          cota_impact_multiplier=2.0)
    baseline_no_boost = m.calc_monthly_total(20, 58, 1, cota_events=[])
    assert no_event_month["truck_gross"] == pytest.approx(baseline_no_boost["truck_gross"])


def test_tobacco_stream_is_fully_removed():
    """The tobacco/nicotine stream must stay gone, everywhere.

    It was dropped deliberately: Dollar General next door sells both
    cigarettes AND nicotine pouches, so the park had no competitive edge,
    and at ~68% blended COGS the stream inflated gross revenue far more
    than NOI. See the decision record in Section 1 of the model.

    This guards against a HALF-revert - re-adding a constant or a dict key
    without wiring it through every consumer is exactly how the "COTA
    total" bug bit 7+ call sites twice. If tobacco is ever genuinely
    re-introduced, delete this test in the same commit rather than
    weakening it.
    """
    leftovers = [n for n in dir(m) if "TOBACCO" in n]
    assert leftovers == [], f"tobacco constants still present: {leftovers}"
    assert not hasattr(m, "calc_tobacco_revenue")
    assert "tobacco_permit" not in m.FIXED_COSTS

    monthly = m.calc_monthly_total(20, 58, 10)
    cota = m.calc_cota_event_revenue(["tier1_f1"])
    _, annual = m.run_annual_projection()
    for key in list(monthly) + list(cota) + list(annual):
        assert "tobacco" not in key, f"stale tobacco key: {key}"

    for name, params in m.SCENARIOS.items():
        assert "tobacco_attach_rate" not in params, f"{name} still sets tobacco"


# ---------------------------------------------------------------------------
# Tax identities
# ---------------------------------------------------------------------------

def test_alcohol_variable_rate_includes_both_mixed_beverage_taxes():
    """COGS on the cash receipt; sales tax backed out before GRT."""
    receipts = 1_000.0
    grt, sales_tax = m.alcohol_taxes_on_inclusive_receipts(receipts)
    assert sales_tax == pytest.approx(receipts * m.MB_SALES_TAX_RATE / (1 + m.MB_SALES_TAX_RATE))
    assert grt == pytest.approx((receipts - sales_tax) * m.GRT_RATE)
    assert grt < receipts * m.GRT_RATE  # no tax-on-tax
    assert m.VARIABLE_COST_RATE == pytest.approx((m.COGS_RATE * receipts + grt + sales_tax) / receipts)


def test_bar_avg_check_derives_from_item_mix():
    """BAR_AVG_CHECK is drinks/visit x item mix, NOT a single item price."""
    expected_item = (m.DRAFT_BEER_MIX_PCT * m.DRAFT_BEER_PRICE
                     + m.BEER_MIX_PCT * m.BEER_PRICE
                     + m.SHOT_MIX_PCT * m.SHOT_PRICE
                     + m.COCKTAIL_MIX_PCT * m.COCKTAIL_PRICE)
    assert m.AVG_ITEM_PRICE == pytest.approx(expected_item)
    assert m.BAR_AVG_CHECK == pytest.approx(m.DRINKS_PER_VISIT * expected_item)
    assert m.BAR_AVG_CHECK > m.BEER_PRICE * 0.9  # sanity: not a per-item price


def test_item_mix_percentages_sum_to_one():
    assert (m.DRAFT_BEER_MIX_PCT + m.BEER_MIX_PCT + m.SHOT_MIX_PCT
            + m.COCKTAIL_MIX_PCT) == pytest.approx(1.0)


def test_cota_event_check_exceeds_normal_check():
    """Event days run premium pricing across all four items, so the event
    check must beat the everyday check - the COTA bar_uplift_per_weekend
    figures are sized off that ratio."""
    assert m.COTA_EVENT_AVG_CHECK > m.BAR_AVG_CHECK
    for item_price, event_price in [
        (m.DRAFT_BEER_PRICE, m.COTA_EVENT_DRAFT_BEER_PRICE),
        (m.BEER_PRICE, m.COTA_EVENT_BEER_PRICE),
        (m.SHOT_PRICE, m.COTA_EVENT_SHOT_PRICE),
        (m.COCKTAIL_PRICE, m.COTA_EVENT_COCKTAIL_PRICE),
    ]:
        assert event_price > item_price


def test_cocktails_are_priced_above_prepackaged_items():
    """A made-to-order cocktail is the premium item on the menu - if this
    ever inverts, the item mix and COGS weighting below it are wrong."""
    assert m.COCKTAIL_PRICE > m.BEER_PRICE > m.DRAFT_BEER_PRICE > m.SHOT_PRICE


def test_blended_alcohol_cogs_is_revenue_weighted():
    """COGS_RATE weights each item's COGS by its share of REVENUE, not of
    item count - the two differ because item prices differ."""
    expected = (m._draft_rev_frac * 0.37 + m._beer_rev_frac * 0.37
                + m._shot_rev_frac * 0.25 + m._cocktail_rev_frac * 0.30)
    assert m.COGS_RATE == pytest.approx(expected)
    assert (m._draft_rev_frac + m._beer_rev_frac + m._shot_rev_frac
            + m._cocktail_rev_frac) == pytest.approx(1.0)


def test_parking_sales_tax_is_charged(event_month):
    """Parking is a taxable service in TX - the tax must actually be taken."""
    r = event_month
    assert r["cota_parking"] > 0, "October should have F1 parking revenue"
    assert r["cota_parking_sales_tax"] == pytest.approx(
        r["cota_parking"] * m.PARKING_SALES_TAX_RATE / (1 + m.PARKING_SALES_TAX_RATE))


def test_payroll_burden_rides_on_all_wages(event_month):
    """Burden is 10% of scheduled wages, not of a retired beverage share."""
    assert m.BARTENDER_SHARE_RATE == 0.0
    assert event_month["payroll_burden"] == pytest.approx(
        event_month["labor_wages"] * m.EMPLOYER_PAYROLL_BURDEN_RATE)
    assert event_month["labor_wages"] > event_month["manager_salary"]


def test_se_tax_matches_schedule_se_formula():
    """SE tax = 92.35% of profit x 15.3%, below the SS wage base."""
    profit = 100_000
    assert m.calc_se_tax(profit) == pytest.approx(
        profit * m.SE_TAXABLE_SHARE * 0.153)


def test_scorp_beats_sole_prop_at_same_profit():
    """The whole point of the S-corp election is a lower SE/payroll base."""
    noi = 200_000
    sole = m.run_tax_strategy_analysis(noi, apply_depreciation=False,
                                       apply_scorp=False)
    scorp = m.run_tax_strategy_analysis(noi, apply_depreciation=False,
                                        apply_scorp=True)
    assert scorp["strategy_total_tax"] < sole["strategy_total_tax"]


def test_depreciation_cannot_exceed_noi():
    """A tiny-NOI year can't deduct more depreciation than it earned."""
    result = m.run_tax_strategy_analysis(5_000, accelerated_depreciation=True)
    assert result["depreciation_expense"] <= 5_000
    assert result["taxable_profit"] >= 0


def test_depreciable_basis_within_project_cost():
    buildout_only_basis = m.TOTAL_CAPITALIZED_BASIS - m.LAND_PURCHASE_PRICE
    assert 0 < m.TOTAL_DEPRECIABLE_BASIS <= buildout_only_basis
    assert (m.DEPRECIABLE_BASIS_5YR + m.DEPRECIABLE_BASIS_15YR
            == m.TOTAL_DEPRECIABLE_BASIS)


def test_depreciation_item_labels_resolve():
    """Guard: the basis lists look items up by exact label across
    PHASE_0_5_CAPITAL_IMPROVEMENTS + USE_OF_FUNDS.

    Renaming a line item in either list silently breaks the basis (or
    KeyErrors) unless the lists are updated with it.
    """
    labels = {label for label, _, _ in m.PHASE_0_5_CAPITAL_IMPROVEMENTS + m.USE_OF_FUNDS}
    for item in (m.DEPRECIATION_5YR_ITEMS + m.DEPRECIATION_15YR_ITEMS
                 + m.STARTUP_COST_ITEMS):
        assert item in labels, f"{item!r} no longer matches a known label"


def test_startup_costs_follow_section_195_structure():
    """Up to $5,000 immediately, remainder amortized over 15 years.

    Written to hold in BOTH Sec. 195 regimes rather than assuming the
    basis exceeds the cap: once the TABC permit moved out of the permits
    line (obtained and paid under the old LOC, so it lives in the payoff
    line instead), qualifying startup basis fell below $5,000 and the
    whole amount became immediately deductible with nothing to amortize.
    """
    immediate = min(m.STARTUP_COST_BASIS, m.STARTUP_IMMEDIATE_DEDUCTION_CAP)
    remainder = max(0.0, m.STARTUP_COST_BASIS - immediate)
    assert m.YEAR1_STARTUP_DEDUCTION == pytest.approx(
        immediate + remainder / m.STARTUP_AMORTIZATION_YEARS)
    assert m.ONGOING_STARTUP_AMORTIZATION == pytest.approx(
        remainder / m.STARTUP_AMORTIZATION_YEARS)
    assert m.ONGOING_STARTUP_AMORTIZATION <= m.YEAR1_STARTUP_DEDUCTION
    # Never deduct more than was actually spent.
    assert m.YEAR1_STARTUP_DEDUCTION <= m.STARTUP_COST_BASIS


def test_startup_and_depreciation_dont_double_count_basis():
    """A dollar of buildout is either depreciable OR a startup cost."""
    dep_items = set(m.DEPRECIATION_5YR_ITEMS) | set(m.DEPRECIATION_15YR_ITEMS)
    assert dep_items.isdisjoint(set(m.STARTUP_COST_ITEMS))


def test_first_year_gets_larger_startup_deduction_than_later_years():
    noi = 200_000
    yr1 = m.run_tax_strategy_analysis(noi, first_year=True)
    later = m.run_tax_strategy_analysis(noi, first_year=False)
    assert yr1["startup_amortization"] > later["startup_amortization"]
    assert yr1["strategy_total_tax"] < later["strategy_total_tax"]


def test_social_security_wage_base_is_current():
    """Stale wage bases silently misstate SE tax; 2026 figure is $184,500."""
    assert m.SOCIAL_SECURITY_WAGE_BASE == 184_500


# ---------------------------------------------------------------------------
# Ramps and lease-up (the park is a cold start with no signed contracts)
# ---------------------------------------------------------------------------

def test_year1_lot_is_not_full_on_opening_month():
    """No contracts are signed, so month 1 must not assume a full lot."""
    assert m.resolve_truck_count(1, m.TRUCK_SLOTS) < m.TRUCK_SLOTS


def test_lease_up_is_monotonic_and_reaches_full():
    counts = [m.resolve_truck_count(mo, m.TRUCK_SLOTS) for mo in range(1, 13)]
    assert counts == sorted(counts), "lease-up should never go backwards"
    assert counts[-1] == pytest.approx(m.TRUCK_SLOTS)


def test_steady_state_has_no_ramp():
    """year_month=None (Year 2+) means fully leased."""
    assert m.resolve_truck_count(None, m.TRUCK_SLOTS) == m.TRUCK_SLOTS


def test_bar_ramp_starts_low_and_reaches_full():
    assert m.BAR_Y1_RAMP[1] < 0.5, "cold start should open well below run-rate"
    ramps = [m.BAR_Y1_RAMP.get(mo, 1.0) for mo in range(1, 13)]
    assert ramps == sorted(ramps)
    assert ramps[-1] == 1.0


def test_sports_density_is_revenue_neutral():
    """The sports calendar redistributes traffic; it must not inflate it."""
    mean = sum(m.SPORTS_DENSITY.values()) / 12
    assert 0.99 <= mean <= 1.01, f"SPORTS_DENSITY mean {mean} should be ~1.0"


def test_sports_density_peaks_in_october():
    """October is the 'Sports Equinox' per the owner's research."""
    assert m.SPORTS_DENSITY[10] == max(m.SPORTS_DENSITY.values())
    assert m.SPORTS_DENSITY[2] < 1.0, "February is the quietest month"


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def test_scenarios_are_ordered_worst_to_best():
    order = ["Worst Case", "Stress Test", "Conservative", "Base Case", "Upside"]
    nois = [m.run_scenario_projection(m.SCENARIOS[n])[1]["total_noi"]
            for n in order]
    assert nois == sorted(nois), f"scenarios out of order: {nois}"


def test_downside_scenarios_haircut_attach_rates():
    """A failing bar shouldn't keep the base-case beverage attach rate."""
    worst = m.SCENARIOS["Worst Case"]
    base = m.SCENARIOS["Base Case"]
    assert worst["daytime_beverage_attach_rate"] < base["daytime_beverage_attach_rate"]


# ---------------------------------------------------------------------------
# Break-even
# ---------------------------------------------------------------------------

def test_zero_bar_test_zeroes_every_bar_driven_stream():
    """The no-bar view must also kill daytime beverages.

    That stream rides on truck traffic, not bar traffic, so it does NOT
    zero out just because bar customers are set to 0 - the analysis has to
    pass its attach rate explicitly.
    """
    result = m.run_breakeven_analysis(verbose=False)
    annual = result["no_bar_annual"]
    assert annual["total_bar"] == 0
    assert annual["total_daytime_beverage"] == 0
    assert annual["total_trucks"] > 0, "truck rent should survive"


# ---------------------------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------------------------

def test_monte_carlo_is_deterministic_for_a_given_seed():
    a = m.run_monte_carlo(50, seed=7)
    b = m.run_monte_carlo(50, seed=7)
    assert [r["noi"] for r in a] == [r["noi"] for r in b]


def test_monte_carlo_results_sorted_by_nut_coverage():
    results = m.run_monte_carlo(50, seed=1)
    covs = [r["nut_coverage"] for r in results]
    assert covs == sorted(covs)


def test_monte_carlo_respects_slider_inputs():
    """Regression guard: MC used to ignore several dashboard sliders."""
    median = lambda rs: sorted(r["noi"] for r in rs)[len(rs) // 2]
    base = m.run_monte_carlo(120, seed=3)
    more_slots = m.run_monte_carlo(120, seed=3, base_truck_slots=6)
    no_daytime_bev = m.run_monte_carlo(
        120, seed=3, base_daytime_beverage_attach_rate=0.0)
    assert median(more_slots) > median(base), "more truck slots must raise NOI"
    assert median(no_daytime_bev) < median(base), \
        "killing daytime beverages must lower NOI"


def test_monte_carlo_varies_the_beverage_attach_rate():
    results = m.run_monte_carlo(120, seed=5)
    bev = {round(r["daytime_beverage_attach_rate"], 4) for r in results}
    assert len(bev) > 10, "beverage attach rate should vary across sims"


# ---------------------------------------------------------------------------
# Financing
# ---------------------------------------------------------------------------

def test_loan_amortization_sweep_beats_contractual_schedule():
    """Sweeping extra free cash flow to principal must cost less interest
    than the contractual required-payment-only schedule."""
    result = m.run_loan_amortization_schedule(sweep_pct=1.0, verbose=False)
    assert result["total_interest_paid"] < result["required_schedule_interest"]


def test_loan_monthly_payment_derives_from_amortization_formula():
    """Carry the unrounded payment. Annual debt service is payment × 12."""
    exact = m._amortization_payment(
        m.LOAN_AMOUNT, m.LOAN_INTEREST_RATE, m.LOAN_TERM_YEARS)
    assert m.LOAN_MONTHLY_PAYMENT == exact
    assert m.ANNUAL_DEBT_SERVICE == pytest.approx(exact * 12)
    # Unrounded. The old $54,522 figure was the $500k loan, not this sized ask.
    assert m.ANNUAL_DEBT_SERVICE != pytest.approx(54_522, abs=1)
    assert m.ANNUAL_DEBT_SERVICE != round(exact) * 12


def test_amortization_balance_reaches_zero_at_term_end():
    balance = m._amortization_balance(
        m.LOAN_AMOUNT, m.LOAN_INTEREST_RATE, m.LOAN_TERM_YEARS,
        m.LOAN_TERM_YEARS * 12)
    assert balance == pytest.approx(0.0, abs=1.0)


def test_taxable_income_excludes_loan_principal():
    """Loan principal isn't deductible - only interest is - so the taxable
    base (NOI - interest) must exceed total_net_cash (NOI - full P&I) by
    exactly that year's principal paid, and narrow toward NOI over time as
    the loan amortizes (principal's share of the fixed payment grows)."""
    _, y1 = m.run_annual_projection(year=1)
    interest_y1 = m._amortization_interest_for_year(
        m.LOAN_AMOUNT, m.LOAN_INTEREST_RATE, m.LOAN_TERM_YEARS, 1)
    principal_y1 = m.ANNUAL_DEBT_SERVICE - interest_y1
    taxable_base_y1 = y1["total_noi"] - interest_y1
    assert taxable_base_y1 == pytest.approx(y1["total_net_cash"] + principal_y1)
    assert y1["income_tax"] == pytest.approx(
        max(0.0, taxable_base_y1) * m.EFFECTIVE_INCOME_TAX_RATE)

    all_years = m.run_multi_year_projection(years=5)
    interest_by_year = [
        m._amortization_interest_for_year(
            m.LOAN_AMOUNT, m.LOAN_INTEREST_RATE, m.LOAN_TERM_YEARS, yr)
        for yr, _, _ in all_years
    ]
    assert interest_by_year == sorted(interest_by_year, reverse=True), \
        "interest paid should shrink each year as the loan amortizes"


def test_use_of_funds_sums_to_total_project_cost():
    assert sum(a for _, a, _ in m.USE_OF_FUNDS) == m.TOTAL_PROJECT_COST
    assert m.ALREADY_SPENT + m.NEW_CASH_NEEDED == m.TOTAL_PROJECT_COST


def test_tabc_permit_is_not_double_counted_in_use_of_funds():
    """The $5,300 TABC Mixed Beverage permit has been obtained and paid,
    financed by the old personal LOC - so it sits inside the $120,000
    LOC-payoff line. Carrying it AGAIN as a forward-looking permits cost
    would double-count the same dollars and inflate the capitalized basis
    (which capitalizes the permits line but not the payoff)."""
    permits = [(label, amt) for label, amt, _ in m.USE_OF_FUNDS
               if label.startswith("Permits & soft costs")]
    assert len(permits) == 1, "expected exactly one permits line"
    label, amount = permits[0]
    assert "TABC" not in label and "MB permit" not in label, (
        f"permits line still advertises the already-paid TABC permit: {label!r}")
    # Health permit only. The $5,300 TABC permit stays inside the LOC payoff.
    assert amount == m.HEALTH_LICENSE == 1_700
    assert amount != 1_700 + 5_300
    assert m.ACE_CIVIL_RETAINER not in {a for _, a, _ in m.USE_OF_FUNDS}


def test_land_acreage_matches_the_deeded_tracts():
    """Two General Warranty Deeds (02/20/2026) convey 1.500 + 2.932 acres.
    A lender pulls the deed, so don't round back to 4.5."""
    assert m.LAND_ACRES == pytest.approx(1.500 + 2.932)


def test_phase_0_5_items_excluded_from_new_loan_use_of_funds():
    """The historical Phase 0.5 buildout (already funded via the old LOC)
    must not appear a second time in the new $500K loan's Use of Funds -
    that would double-count real dollars on top of the LOC payoff line."""
    phase_0_5_labels = {label for label, _, _ in m.PHASE_0_5_CAPITAL_IMPROVEMENTS}
    use_of_funds_labels = {label for label, _, _ in m.USE_OF_FUNDS}
    assert phase_0_5_labels.isdisjoint(use_of_funds_labels)


def test_monthly_nut_matches_fixed_costs():
    assert m.MONTHLY_NUT == sum(m.FIXED_COSTS.values())
    assert m.ANNUAL_NUT == m.MONTHLY_NUT * 12


def test_opex_and_debt_service_split_matches_fixed_costs():
    assert m.MONTHLY_OPEX_NUT == sum(m.OPERATING_FIXED_COSTS.values())
    assert m.ANNUAL_OPEX_NUT == m.MONTHLY_OPEX_NUT * 12
    assert m.MONTHLY_DEBT_SERVICE == m.FIXED_COSTS["loan_payment"]
    assert m.ANNUAL_DEBT_SERVICE == m.MONTHLY_DEBT_SERVICE * 12
    assert m.MONTHLY_OPEX_NUT + m.MONTHLY_DEBT_SERVICE == m.MONTHLY_NUT


def test_yield_on_cost_includes_land():
    loc_payoff_and_reserve = {
        "Payoff of existing high-interest line of credit (Phase 0.5 & pre-loan soft costs)",
        "Reserve & Safety Cash",
    }
    real_new_loan_capex = sum(
        a for label, a, _ in m.USE_OF_FUNDS if label not in loc_payoff_and_reserve)
    assert m.TOTAL_CAPITALIZED_BASIS == (
        m.LAND_PURCHASE_PRICE + m.PHASE_0_5_TOTAL + real_new_loan_capex)
    assert m.EQUITY_BASIS == m.TOTAL_CAPITALIZED_BASIS - m.LOAN_AMOUNT
    _, annual = m.run_annual_projection(year=2)
    result = m.calc_valuation_and_leverage(annual)
    assert result["yield_on_cost"] == pytest.approx(
        annual["total_noi"] / m.TOTAL_CAPITALIZED_BASIS)


# ---------------------------------------------------------------------------
# Multi-year
# ---------------------------------------------------------------------------

def test_year2_beats_year1_because_ramps_are_gone():
    all_years = m.run_multi_year_projection(years=2)
    y1 = all_years[0][2]["total_noi"]
    y2 = all_years[1][2]["total_noi"]
    assert y2 > y1, "losing the Year 1 ramp should outweigh cost inflation"


def test_utility_passthrough_is_noi_neutral(year1):
    """Billed at cost by law - it must add gross revenue but zero profit."""
    _, annual = year1
    assert annual["total_utility_billed"] == pytest.approx(
        annual["total_utility_cost"])


# ---------------------------------------------------------------------------
# CRE valuation & returns
# ---------------------------------------------------------------------------

def test_returns_analysis_irr_is_sane():
    """IRR stays in a sane band. Leverage direction follows the spread.

    When stabilized yield on cost is below the loan rate, debt is dilutive
    and levered IRR must sit below unlevered IRR. Hiding that inversion is
    the bug this test exists to catch.
    """
    result = m.run_returns_analysis()
    _, stabilized = m.run_annual_projection(year=2)
    yield_on_cost = stabilized["total_noi"] / m.TOTAL_CAPITALIZED_BASIS
    assert result["unlevered_irr"] is not None
    assert result["levered_irr"] is not None
    # Sane band. A 9% exit on a ~6% yield-on-cost can print a small negative
    # IRR. That is the underwriting result, not a solver failure.
    assert -0.5 < result["unlevered_irr"] < 0.5
    if yield_on_cost < m.LOAN_INTEREST_RATE:
        assert result["leverage_dilutive"] is True
        assert result["levered_irr"] < result["unlevered_irr"]
    else:
        assert result["leverage_dilutive"] is False
        assert result["levered_irr"] > result["unlevered_irr"]


def test_equity_multiple_is_defined_and_follows_the_exit_cap():
    """At a 9% exit cap and a yield on cost under that cap, the 5-year
    unlevered multiple does not clear 1.0x. Lock the direction, not a
    headline multiple."""
    result = m.run_returns_analysis()
    _, stabilized = m.run_annual_projection(year=2)
    yield_on_cost = stabilized["total_noi"] / m.TOTAL_CAPITALIZED_BASIS
    assert result["unlevered_equity_multiple"] > 0
    assert result["levered_equity_multiple"] > 0
    if yield_on_cost < m.MARKET_CAP_RATE:
        assert result["unlevered_equity_multiple"] < 1.0


def test_returns_analysis_respects_hold_period_and_cap_rate():
    """A shorter hold or a lower exit cap rate should raise unlevered IRR
    (less time for compounding to matter less; a lower cap rate means a
    richer exit value for the same NOI)."""
    base = m.run_returns_analysis(hold_years=5, exit_cap_rate=0.09)
    shorter_hold = m.run_returns_analysis(hold_years=3, exit_cap_rate=0.09)
    richer_exit = m.run_returns_analysis(hold_years=5, exit_cap_rate=0.07)
    assert shorter_hold["unlevered_irr"] != base["unlevered_irr"]
    assert richer_exit["unlevered_irr"] > base["unlevered_irr"]


def test_cre_sensitivity_grid_varies_with_revenue_and_cap_rate():
    grid = m.run_cre_sensitivity_grid(
        revenue_deltas=(-0.10, 0.0, 0.10), exit_cap_rates=(0.08, 0.10))
    assert len(grid) == 3
    low, base, high = grid
    assert low[0.08] < base[0.08] < high[0.08]      # more revenue -> higher IRR
    assert base[0.10] < base[0.08]                   # higher exit cap -> lower IRR


def test_dscr_matches_noi_over_annual_debt_service():
    _, annual = m.run_annual_projection(year=2)
    result = m.calc_valuation_and_leverage(annual)
    assert result["annual_debt_service"] == pytest.approx(m.ANNUAL_DEBT_SERVICE)
    assert result["dscr"] == pytest.approx(annual["total_noi"] / m.ANNUAL_DEBT_SERVICE)


def test_dscr_falls_as_loan_rate_rises():
    """Fixed NOI, higher rate -> bigger required payment -> lower DSCR."""
    _, annual = m.run_annual_projection(year=2)
    low_rate = m.calc_valuation_and_leverage(annual, loan_rate=0.08)
    high_rate = m.calc_valuation_and_leverage(annual, loan_rate=0.12)
    assert high_rate["dscr"] < low_rate["dscr"]


def test_rate_sensitivity_dscr_decreases_monotonically_with_rate():
    _, annual = m.run_annual_projection(year=2)
    rows = m.run_rate_sensitivity_analysis(
        rates=(0.08, 0.09, 0.10, 0.11, 0.12), annual=annual)
    dscrs = [row["dscr"] for row in rows]
    assert dscrs == sorted(dscrs, reverse=True)


def test_rate_sensitivity_leaves_unlevered_irr_unaffected():
    """NOI and unlevered cash flows are financing-neutral - only the
    levered side should move with the loan rate."""
    low = m.run_returns_analysis(loan_rate=0.08)
    high = m.run_returns_analysis(loan_rate=0.12)
    assert low["unlevered_irr"] == pytest.approx(high["unlevered_irr"])
    assert low["levered_irr"] > high["levered_irr"]


def test_run_returns_analysis_loan_rate_defaults_match_module_rate():
    """Omitting loan_rate must reproduce the exact figures every existing
    caller (the CRE tab, run_cre_sensitivity_grid) relies on."""
    default = m.run_returns_analysis()
    explicit = m.run_returns_analysis(loan_rate=m.LOAN_INTEREST_RATE)
    assert default["levered_irr"] == pytest.approx(explicit["levered_irr"])
    assert default["levered_cash_flows"] == explicit["levered_cash_flows"]


def test_bank_case_bar_assumptions_track_the_stress_test_scenario():
    """The Bank Case reads its bar traffic/check out of SCENARIOS["Stress
    Test"] rather than duplicating the numbers. Guards the drift that bit
    when the container-bar buildout moved BAR_AVG_CHECK $9.00 -> $11.45 and
    left a hardcoded $8.05 behind."""
    stress = m.SCENARIOS["Stress Test"]
    stress_years = m.run_multi_year_projection(
        base_weekday_customers=stress["weekday_customers"],
        base_weekend_customers=stress["weekend_customers"],
        base_check=stress["avg_check"],
        truck_occupancy=0.75, seasonal_pct=0.85,
        daytime_beverage_attach_rate=stress["daytime_beverage_attach_rate"],
        cota_impact_multiplier=0.5, years=m.HOLD_PERIOD_YEARS + 1)
    assert m.run_bank_case_underwriting()["stabilized_noi"] == pytest.approx(
        stress_years[1][2]["total_noi"])


def test_monte_carlo_check_clamp_does_not_truncate_the_upper_tail():
    """The avg-check clamp must leave real headroom above BAR_AVG_CHECK, or
    the simulation silently biases low. The old ceiling (13.0) sat barely
    1.5 sigma above the post-container-bar $11.45 mean."""
    sigma = 1.0                      # matches run_monte_carlo's gauss spread
    assert 20.0 >= m.BAR_AVG_CHECK + 3 * sigma


def test_bank_case_underwriting_is_more_conservative_than_base_case():
    _, base_annual = m.run_annual_projection(year=2)
    base = m.calc_valuation_and_leverage(base_annual)
    bank_case = m.run_bank_case_underwriting()

    assert bank_case["loan_rate"] > m.LOAN_INTEREST_RATE
    assert bank_case["loan_rate"] == pytest.approx(
        m.LOAN_INTEREST_RATE + m.BANK_CASE_RATE_STRESS)
    assert bank_case["stabilized_noi"] < base_annual["total_noi"]
    assert bank_case["dscr"] < base["dscr"]
    # Scheduled labor dropped stacked coverage through a 1.35x F&B floor.
    # That is the finding. If a later change lifts it back over the floor,
    # this assertion should fail — update it and say why coverage improved.
    assert bank_case["dscr"] < 1.35


def test_construction_period_delays_returns_engine_cash_flows():
    """run_returns_analysis() should discount every post-Year-0 cash flow
    CONSTRUCTION_PERIOD_MONTHS later than a same-cash-flows, zero-offset IRR
    would - capital sits in construction before Year 1 operations begin, so
    it shouldn't appear to earn a return during that gap. This is a timing
    correction only: same dollar cash flows, later discount points, and a
    strictly lower IRR/NPV as a result (assuming a positive construction
    period and a return-positive deal, both true at defaults)."""
    assert m.CONSTRUCTION_PERIOD_MONTHS == 1
    assert m.RETURNS_DELAY_MONTHS == m.MONTHS_TO_OPEN == 6
    result = m.run_returns_analysis()
    construction_years = m.RETURNS_DELAY_MONTHS / 12

    no_offset_irr = m._irr(result["unlevered_cash_flows"], period_offset=0.0)
    with_offset_irr = m._irr(result["unlevered_cash_flows"], period_offset=construction_years)
    assert with_offset_irr == pytest.approx(result["unlevered_irr"])
    assert with_offset_irr != pytest.approx(no_offset_irr)
    # When the exit is below cost, annualizing the loss over a longer gap
    # can make the IRR less negative. NPV is the check that the gap does
    # not create a return.

    no_offset_npv = m._npv(m.DISCOUNT_RATE, result["unlevered_cash_flows"], period_offset=0.0)
    with_offset_npv = m._npv(m.DISCOUNT_RATE, result["unlevered_cash_flows"], period_offset=construction_years)
    assert with_offset_npv == pytest.approx(result["unlevered_npv"])
    assert with_offset_npv < no_offset_npv


def test_irr_npv_period_offset_defaults_to_zero():
    """Backward-compat: calling _irr/_npv without period_offset (as every
    call site did before CONSTRUCTION_PERIOD_MONTHS existed) must reproduce
    the plain annual-period convention exactly."""
    cash_flows = [-100_000, 20_000, 30_000, 40_000, 130_000]
    assert m._irr(cash_flows) == pytest.approx(m._irr(cash_flows, period_offset=0.0))
    assert m._npv(0.10, cash_flows) == pytest.approx(m._npv(0.10, cash_flows, period_offset=0.0))


def test_equity_schedule_rows_sum():
    """Property equity and total economic equity are different, and both sum."""
    rows = {r["line"]: r["amount"] for r in m.equity_schedule_rows()}
    capitalized = (rows["Land (related-party transfer basis, not an appraisal)"]
                   + rows["Phase 0.5 capital improvements"]
                   + rows["New construction and soft costs (this loan)"])
    assert capitalized == pytest.approx(rows["Capitalized basis"])
    assert capitalized == pytest.approx(m.TOTAL_CAPITALIZED_BASIS)
    assert rows["Capitalized basis"] + rows["Less: bank loan"] == pytest.approx(
        rows["Property equity"])
    assert rows["Property equity"] + rows["Reserve cash (sources & uses; not capitalized)"] == pytest.approx(
        rows["Total economic equity"])
    assert rows["Property equity"] == pytest.approx(m.PROPERTY_EQUITY)
    assert rows["Total economic equity"] == pytest.approx(m.TOTAL_ECONOMIC_EQUITY)
    # Land + Phase 0.5 − the LOC payoff. True while every non-LOC, non-reserve
    # use is capitalized.
    assert rows["Total economic equity"] == pytest.approx(
        m.LAND_PURCHASE_PRICE + m.PHASE_0_5_TOTAL - m.LOC_PAYOFF_DRAWN)
    assert rows["Property equity"] == pytest.approx(
        rows["Total economic equity"] - m.RESERVE_AND_SAFETY_CASH)
    assert rows["Property equity"] != rows["Total economic equity"]


def test_opening_cash_derives_from_sources_and_uses():
    assert m.OPENING_MONTH == 3 and m.OPENING_YEAR == 2027
    assert m.PRE_OPEN_MONTHS == m.MONTHS_TO_OPEN == 6
    assert m.RESERVE_AND_SAFETY_CASH == m.RESERVE_FLOOR == 40_000
    # Land tax and vacant insurance are in LAND_CARRY, not in this burn.
    assert "property_tax" not in m.PRE_OPEN_COST_KEYS
    assert "insurance" not in m.PRE_OPEN_COST_KEYS
    assert m.OPENING_CASH_RESERVE == pytest.approx(
        m.RESERVE_AND_SAFETY_CASH - m.PRE_OPEN_BURN)
    assert m.OPENING_CASH_RESERVE != 15_000
    assert m.OPENING_CASH_RESERVE < m.RESERVE_AND_SAFETY_CASH


def test_scheduled_labor_replaces_revenue_share():
    _, y2 = m.run_annual_projection(year=2)
    assert y2["total_manager_salary"] == pytest.approx(m.MANAGER_ANNUAL_SALARY)
    assert m.BARTENDER_SHARE_RATE == 0.0
    assert m.LODGING_PROVIDED and not m.LODGING_EXPENSED
    # Wages plus burden replace the ~$12k share. The review's "~$96k" is the
    # order of magnitude of the cost the share did not carry.
    cash_labor = y2["total_labor_wages"] + y2["total_payroll_burden"]
    assert cash_labor > 90_000
    assert y2["total_event_extra_wages"] > 0
    assert y2["total_race_evening_premium"] > 0
    assert sum(m.LABOR_HOURS_SEASON.values()) == pytest.approx(12.0)


def test_inflation_is_line_by_line_and_spares_the_loan():
    years = m.run_multi_year_projection(years=2)
    y1 = years[0][2]
    y2 = years[1][2]
    assert y1["cost_inflation_adj"] == 0
    assert y2["cost_inflation_adj"] > 0
    assert y2["total_opex"] == pytest.approx(m.ANNUAL_OPEX_NUT * (1 + m.ANNUAL_COST_INFLATION))
    assert y2["total_labor_wages"] > y1["total_labor_wages"]
    # Debt service is the same unrounded annual payment in both years.
    assert (y1["total_noi"] - y1["total_net_cash"]) == pytest.approx(m.ANNUAL_DEBT_SERVICE)
    assert (y2["total_noi"] - y2["total_net_cash"]) == pytest.approx(m.ANNUAL_DEBT_SERVICE)


def test_breakeven_says_when_a_target_is_unreachable():
    result = m.run_breakeven_analysis(verbose=False)
    for row in result["bar_traffic_targets"]:
        assert "reachable" in row
        if not row["reachable"]:
            assert row["weekday_customers"] is None
            assert row["weekend_customers"] is None
            assert row["coverage_at_ceiling"] < row["target"]


def test_revenue_mix_labels_contractual_and_transactional():
    _, y2 = m.run_annual_projection(year=2)
    mix = m.calc_revenue_mix(y2)
    assert mix["property_and_parking_share"] == pytest.approx(0.504, abs=0.01)
    assert mix["contractual_pad_rent_share"] == pytest.approx(0.043, abs=0.005)
    assert "non-contractual" in mix["percentage_rent_label"]
    assert "transactional" in mix["event_parking_label"]


def test_delayed_opening_misses_f1():
    params = m.SCENARIOS["Delayed Opening (misses F1)"]
    assert "tier1_f1" not in params["cota_events"].get(10, [])
    _, delayed = m.run_scenario_projection(params)
    _, base = m.run_scenario_projection(m.SCENARIOS["Base Case"])
    assert delayed["total_noi"] < base["total_noi"]
    assert delayed["total_cota_parking"] < base["total_cota_parking"]


def test_event_names_match_the_calendar_review():
    assert "DuraMAX" in m.COTA_EVENT_TIERS["tier2_nascar"]["name"]
    assert "EchoPark" not in m.COTA_EVENT_TIERS["tier2_nascar"]["name"]
    assert m.F1_AGREEMENT_THROUGH_YEAR == 2034
    assert m.COTALAND_STATUS == "scheduled_competitor_not_park_revenue"
    for events in m.COTA_EVENTS_BY_MONTH.values():
        assert "cotaland" not in " ".join(events).lower()


def test_monte_carlo_spec_discloses_seed_and_bounds():
    assert m.MONTE_CARLO_DEFAULT_SEED == 42
    assert m.MONTE_CARLO_DRAWS_ARE_INDEPENDENT is True
    names = [row["name"] for row in m.MONTE_CARLO_SPEC]
    assert "weekday_customers" in names
    assert "cota_impact_multiplier" in names
    check = m._mc_spec("avg_check")
    assert check["low"] < m.BAR_AVG_CHECK < check["high"]
    held = [row for row in m.MONTE_CARLO_SPEC if row["distribution"] == "held_fixed"]
    assert held


def test_address_is_13901_not_13903():
    assert m.PROPERTY_ADDRESS.startswith("13901 FM 812")
    assert "13903" not in m.PROPERTY_ADDRESS


def test_paving_default_stays_asphalt():
    paving = next(a for label, a, _ in m.USE_OF_FUNDS if "Paved asphalt" in label)
    assert paving == m.PAVING_BUDGET == 50_000
    assert m.GRAVEL_ALT_BUDGET == 15_400
    assert m.GRAVEL_ALT_BUDGET != paving


def test_time_to_open_is_six_months_and_the_build_is_one_month():
    """Entitlement 5 + construction 1. The IRR delay is the full 6 months."""
    assert m.POST_PERMIT_BUILD_MONTHS == 1
    assert m.ENTITLEMENT_PERMIT_LAG_MONTHS == 5
    assert m.CONSTRUCTION_PERIOD_MONTHS == 1
    assert m.MONTHS_TO_OPEN == 6
    assert m.PRE_OPEN_MONTHS == 6
    assert m.RETURNS_DELAY_MONTHS == 6


def test_sized_ask_holds_forty_thousand_reserve_floor():
    """Base asphalt @ 10% ≈ $563.6k. Bank asphalt @ 15% ≈ $581.7k.
    The floor is held by raising the ask, not by cutting contingency."""
    base = m.build_use_of_funds()
    assert base["labeled_excluding_reserve"] == 523_626
    assert base["ask"] == 563_626
    assert base["residual_reserve"] == m.RESERVE_FLOOR == 40_000
    assert base["ask_bumped"] is True
    assert base["contingency"] == pytest.approx(36_200)
    bank = m.build_use_of_funds(contingency_rate=m.CONTINGENCY_RATE_BANK)
    assert bank["ask"] == 581_726
    assert bank["contingency"] == pytest.approx(54_300)
    assert bank["residual_reserve"] == 40_000
    assert sum(a for _, a, _ in base["use_of_funds"]) == base["ask"]


def test_contingency_includes_gc_and_septic_stays_gated():
    hard = m.SEPTIC + m.PAVING_BUDGET + m.BAR + m.GC_GENERAL_CONDITIONS_ALLOWANCE
    assert m.hard_cost_total() == hard == 362_000
    assert m.SEPTIC == 212_000
    assert m.SEPTIC_UNLOCKED is False
    assert m.contingency_amount() == pytest.approx(0.10 * hard)
    assert m.OSSF_DESIGN == 0


def test_ace_retainer_and_tabc_are_not_forward_uses():
    labels = [label for label, _, _ in m.USE_OF_FUNDS]
    assert not any("retainer" in label.lower() for label in labels)
    assert m.ACE_CIVIL_RETAINER == 3_000
    assert not any("TABC" in label for label in labels)


def test_gravel_alternative_rebuilds_the_ask():
    gravel = m.build_use_of_funds(mode="gravel")
    assert gravel["hard_cost_total"] == 212_000 + 15_400 + 50_000 + 50_000
    assert gravel["residual_reserve"] == 40_000
    assert gravel["ask"] == gravel["labeled_excluding_reserve"] + 40_000
    assert gravel["ask"] < m.LOAN_ASK


def test_reserve_floor_bumps_a_too_small_ask():
    forced = m.build_use_of_funds(ask=100_000)
    assert forced["residual_reserve"] == m.RESERVE_FLOOR
    assert forced["ask"] == forced["labeled_excluding_reserve"] + m.RESERVE_FLOOR
    assert forced["ask_bumped"] is True


def test_land_carry_is_six_months_of_vacant_bills():
    annual = m.LAND_TAX_PID_984219 + m.LAND_TAX_PID_300451 + m.VACANT_LAND_INSURANCE_ANNUAL
    assert annual == pytest.approx(7_448.80)
    assert m.LAND_CARRY_MONTHLY == 621
    assert m.LAND_CARRY == 3_726
    assert m.LAND_CARRY_MONTHS_PREPAID == 6


def test_labor_is_heavier_on_race_weekends_and_in_october():
    january = m.calc_scheduled_labor([], month=1)
    october_quiet = m.calc_scheduled_labor([], month=10)
    october_race = m.calc_scheduled_labor(m.COTA_EVENTS_BY_MONTH[10], month=10)
    assert october_quiet["labor_wages"] > january["labor_wages"]
    assert october_race["race_days"] > 0
    assert october_race["labor_wages"] > october_quiet["labor_wages"]
    assert october_race["event_extra_wages"] > 0
    assert m.LABOR_WEEKEND_EVENING_HOURS > m.LABOR_WEEKDAY_EVENING_HOURS
    assert m.LABOR_RACE_EVENING_HOURS > m.LABOR_WEEKEND_EVENING_HOURS


def test_no_cota_noi_is_below_base_and_is_a_named_scenario():
    _, base = m.run_annual_projection(year=2)
    _, quiet = m.run_annual_projection(year=2, cota_impact_multiplier=0.0)
    assert quiet["total_noi"] < base["total_noi"]
    assert quiet["total_cota_parking"] == 0
    _, scenario = m.run_scenario_projection(m.SCENARIOS["No COTA"])
    assert scenario["total_noi"] < base["total_noi"]


def test_product_dscr_504_payment_is_below_7a_and_750k_is_worse():
    pkg = m.run_loan_size_dscr()
    sized = round(m.LOAN_ASK)

    def cell(case, year, amount, product):
        return next(row for row in pkg["rows"]
                    if row["case"] == case and row["year"] == year
                    and row["loan_amount"] == amount and row["product"] == product)

    base_7a = cell("base", 2, sized, "sba_7a")
    base_504 = cell("base", 2, sized, "sba_504")
    base_750 = cell("base", 2, 750_000, "sba_7a")
    nocota = cell("no_cota", 2, sized, "sba_7a")
    assert base_504["annual_debt_service"] < base_7a["annual_debt_service"]
    assert base_504["dscr"] > base_7a["dscr"]
    assert base_750["dscr"] < base_7a["dscr"]
    assert nocota["noi"] < base_7a["noi"]
    assert cell("base", 2, 500_000, "sba_7a")["fits_uses"] is False
    assert base_750["unassigned_proceeds"] > 0
    assert base_7a["dscr"] == pytest.approx(base_7a["noi"] / base_7a["annual_debt_service"])


def test_dscr_matrix_keeps_base_and_bank_apart():
    matrix = m.run_dscr_matrix(years=(2,))
    base = matrix["lender_base"][2]["going_concern"][0.10]
    bank = matrix["bank_case"][2]["going_concern"][0.10]
    assert bank < base
    assert matrix["loan_amount_base"] == 563_626
    assert matrix["loan_amount_bank"] == 581_726
    assert matrix["meta"]["contingency_base"] == 0.10
    assert m.build_use_of_funds()["contingency_rate"] == 0.10


def test_propco_opco_lease_eliminates():
    _, annual = m.run_annual_projection(year=2)
    split = m.run_propco_opco_split(annual)
    assert split["consolidated_ties"] is True
    assert split["consolidated_noi"] == pytest.approx(annual["total_noi"])
    assert split["lease_payment"] == pytest.approx(
        m.INTERCOMPANY_BASE_RENT_ANNUAL + split["nnn_recovery"])
    assert split["propco_entity"] == "JVAM Capital LLC"
    assert split["opco_entity"] == "JVA Operations LLC"


def test_equity_bridge_ties():
    bridge = m.equity_bridge()
    assert bridge["ties"] is True
    assert bridge["uses_total"] == pytest.approx(bridge["loan_sources"])
    assert bridge["total_economic_equity"] == pytest.approx(
        bridge["economic_equity_identity"])


def test_assumption_export_names_its_sources():
    rows = m.export_assumptions_rows()
    sources = {row["source"] for row in rows}
    assert {"wage fix", "patch", "review", "sensitivity"} <= sources
    csv_text = m.export_assumptions_csv()
    assert "Bartender revenue share" in csv_text
    assert m.export_su_csv().startswith("line,amount,status")
    assert "m,phase,draw" in m.export_draw_schedule_csv()


# ---------------------------------------------------------------------------
# Carried over from the Sep 30 lender-review remediation (local branch)
# ---------------------------------------------------------------------------

FEDERAL_MINIMUM_WAGE = 7.25  # Texas adopts the federal floor (Tex. Lab. Code 62.051)


def test_scheduled_wage_rates_clear_the_federal_minimum():
    """Every hourly rate the schedule pays must clear $7.25 on its own.

    The defect the 2026-08-31 lender review found was a bartender paid ONLY
    a 5% revenue share - about $2.11/hr across the service window. Lodging
    is disclosed but never credited against wages, so the cash rate is the
    one that has to clear the floor."""
    for rate in (m.DAYTIME_ATTENDANT_WAGE, m.EVENING_BARTENDER_WAGE, m.EVENT_EXTRA_WAGE):
        assert rate >= FEDERAL_MINIMUM_WAGE
    assert m.BARTENDER_SHARE_RATE == 0.0
    assert not m.LODGING_EXPENSED


def test_labor_does_not_ramp_in_year_one():
    """The park is open the same hours in operating month 2 as at
    stabilization, so the wage bill must NOT scale with the Year 1
    discovery ramp."""
    month = m.operating_to_calendar_month(2)
    early = m.calc_monthly_total(20, 58, month, year_month=2)
    late = m.calc_monthly_total(20, 58, month, year_month=None)
    assert early["bar_revenue"] < late["bar_revenue"], "ramp should apply to revenue"
    assert early["labor_wages"] == pytest.approx(late["labor_wages"])


def test_mixed_beverage_taxes_are_not_stacked(event_month):
    """GRT applies to the SALES PRICE, not to a receipt that already
    includes the 8.25% mixed beverage sales tax (prices are tax-inclusive)."""
    r = event_month
    bar_like = r["bar_revenue"] + r["cota_bar_uplift"] + r["seasonal_revenue"]
    assert bar_like > 0
    sales_price = bar_like / (1 + m.MB_SALES_TAX_RATE)
    assert r["mb_sales_tax"] == pytest.approx(bar_like - sales_price)
    assert r["grt"] == pytest.approx(sales_price * m.GRT_RATE)
    assert r["grt"] < bar_like * m.GRT_RATE, "GRT must not be charged on the sales tax"


def test_business_plan_generates_from_the_model(tmp_path, monkeypatch):
    """build_business_plan.py must run end to end against the current engine.

    The generator reads ~70 engine names directly. When the engine is
    refactored and the generator is not, the plan silently stops building -
    this is the guard. Markdown output avoids a binary diff; the .docx path
    shares every section function."""
    pytest.importorskip("docx")
    import build_business_plan as bbp

    out = tmp_path / "plan.md"
    monkeypatch.setattr("sys.argv", ["build_business_plan.py", str(out)])
    bbp.main()
    text = out.read_text(encoding="utf-8")
    assert f"${m.LOAN_AMOUNT:,.0f}" in text
    assert "{" not in text.replace("{}", ""), "unformatted f-string placeholder in plan"
    assert "$-" not in text, "negative amounts must render as -$x"
    if m.OPENING_CASH_RESERVE < m.RESERVE_AND_SAFETY_CASH * 0.25:
        assert "does not cover that shortfall" in text or "thin point" in text


# ---------------------------------------------------------------------------
# Reserve options - how to close the pre-opening liquidity gap
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def reserve_options():
    return {row["key"]: row for row in m.run_reserve_options()["options"]}


def test_reserve_options_current_row_matches_the_tracker(reserve_options):
    """The 'current' row must reproduce the engine's own tracker exactly,
    so the comparison is anchored to the numbers everywhere else."""
    cur = reserve_options["current"]
    tracker = m.run_cash_reserve_tracker(verbose=False)
    assert cur["loan_amount"] == pytest.approx(m.LOAN_AMOUNT)
    assert cur["opening_cash"] == pytest.approx(m.OPENING_CASH_RESERVE)
    assert cur["min_balance"] == pytest.approx(tracker["min_balance"])
    assert cur["months_negative"] == tracker["months_negative"]


def test_reserve_options_leave_the_defaults_alone():
    before = (m.LOAN_AMOUNT, m.RESERVE_FLOOR, m.RESERVE_AND_SAFETY_CASH,
              m.OPENING_CASH_RESERVE, m.LOAN_MONTHLY_PAYMENT, m.PRE_OPEN_BURN)
    m.run_reserve_options(min_balance_target=25_000)
    after = (m.LOAN_AMOUNT, m.RESERVE_FLOOR, m.RESERVE_AND_SAFETY_CASH,
             m.OPENING_CASH_RESERVE, m.LOAN_MONTHLY_PAYMENT, m.PRE_OPEN_BURN)
    assert before == after


def test_solved_options_hit_the_liquidity_target(reserve_options):
    target = m.run_reserve_options()["min_balance_target"]
    for key in ("higher_floor", "sponsor_cash"):
        assert reserve_options[key]["min_balance"] == pytest.approx(target, abs=1.0)


def test_higher_floor_costs_more_than_sponsor_cash(reserve_options):
    """Borrowing the cushion raises the payment, which burns part of the
    cushion, so the floor must rise by MORE than the equivalent equity."""
    cur = reserve_options["current"]
    floor = reserve_options["higher_floor"]
    sponsor = reserve_options["sponsor_cash"]
    extra_debt = floor["loan_amount"] - cur["loan_amount"]
    assert extra_debt > sponsor["sponsor_cash"] > 0
    assert sponsor["loan_amount"] == pytest.approx(cur["loan_amount"])
    assert floor["stabilized_dscr"] < cur["stabilized_dscr"]
    assert sponsor["stabilized_dscr"] == pytest.approx(cur["stabilized_dscr"])


def test_interest_only_cuts_the_pre_opening_burn(reserve_options):
    cur = reserve_options["current"]
    full = reserve_options["io_full_balance"]
    drawn = reserve_options["io_drawn_balance"]
    assert drawn["pre_open_burn"] < full["pre_open_burn"] < cur["pre_open_burn"]
    # Same loan, same post-opening payment: IO only changes the pre-open months.
    for row in (full, drawn):
        assert row["loan_amount"] == pytest.approx(cur["loan_amount"])
        assert row["monthly_payment"] == pytest.approx(cur["monthly_payment"])
        assert row["min_balance"] - cur["min_balance"] == pytest.approx(
            cur["pre_open_burn"] - row["pre_open_burn"])
