"""
Regression tests for the food truck park financial model.

These lock down the invariants that have actually broken before during
development, rather than re-asserting arithmetic the engine obviously does
correctly. Two classes of bug motivated most of this file:

  1. "COTA total" undercounting. Several call sites reconstruct an event
     total from its parts; twice, adding a new event-day revenue stream
     (daytime beverages, then tobacco) silently broke every one of them.
     test_cota_gross_is_sum_of_parts and friends catch that class directly.
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
        + annual["total_tobacco_cogs"]
        + annual["total_tobacco_tax"]
        + annual["total_cc_processing"]
        + annual["total_shrinkage"]
        + annual["total_bartender_share"]
        + annual["total_payroll_burden"]
        + annual["total_cota_parking_upkeep"]
        + annual["total_cota_parking_sales_tax"]
        + annual["total_cota_cost"]
        + annual["total_utility_cost"]
    )


def test_annual_reconciles_to_noi(year1):
    """Gross - variable - fixed must equal NOI exactly.

    This is the single most valuable assertion in the file: it fails the
    moment a cost is added to the monthly calc but omitted from the annual
    summary, which is exactly how the dashboard's cost tables go stale.
    """
    _, annual = year1
    residual = (annual["total_gross"]
                - _total_variable_costs(annual)
                - m.ANNUAL_NUT
                - annual["total_noi"])
    assert abs(residual) < 1.0


def test_monthly_gross_is_sum_of_streams(event_month):
    """total_gross_revenue must equal the seven streams added up."""
    r = event_month
    parts = (r["truck_gross"] + r["bar_revenue"] + r["seasonal_revenue"]
             + r["daytime_beverage_revenue"] + r["tobacco_revenue"]
             + r["utility_billed"]
             + r["cota_parking"] + r["cota_bar_uplift"]
             + r["cota_daytime_bev_uplift"] + r["cota_tobacco_uplift"])
    assert r["total_gross_revenue"] == pytest.approx(parts)


def test_cota_gross_is_sum_of_parts():
    """calc_cota_event_revenue's gross must include BOTH product uplifts.

    Regression guard: a new event-day revenue stream that isn't folded into
    `gross` makes every downstream "COTA total" undercount.
    """
    cota = m.calc_cota_event_revenue(["tier1_f1"])
    parts = (cota["parking"] + cota["bar_uplift"]
             + cota["daytime_bev_uplift"] + cota["tobacco_uplift"])
    assert cota["gross"] == pytest.approx(parts)


def test_no_events_returns_all_zero_keys():
    """An empty event list must still expose every key, all zeroed."""
    cota = m.calc_cota_event_revenue([])
    for key in ("parking", "bar_uplift", "daytime_bev_uplift",
                "tobacco_uplift", "gross", "incremental_cost", "net"):
        assert cota[key] == 0, f"{key} should be 0 with no events"


# ---------------------------------------------------------------------------
# Tax identities
# ---------------------------------------------------------------------------

def test_alcohol_variable_rate_includes_both_mixed_beverage_taxes():
    """Alcohol carries COGS + 6.7% GRT + 8.25% MB sales tax."""
    assert m.VARIABLE_COST_RATE == pytest.approx(
        m.COGS_RATE + m.GRT_RATE + m.MB_SALES_TAX_RATE)


def test_bar_avg_check_derives_from_item_mix():
    """BAR_AVG_CHECK is drinks/visit x item mix, NOT a single item price."""
    expected_item = (m.BEER_MIX_PCT * m.BEER_PRICE
                     + m.SHOT_MIX_PCT * m.SHOT_PRICE)
    assert m.AVG_ITEM_PRICE == pytest.approx(expected_item)
    assert m.BAR_AVG_CHECK == pytest.approx(m.DRINKS_PER_VISIT * expected_item)
    assert m.BAR_AVG_CHECK > m.BEER_PRICE * 0.9  # sanity: not a per-item price


def test_item_mix_percentages_sum_to_one():
    assert m.BEER_MIX_PCT + m.SHOT_MIX_PCT == pytest.approx(1.0)


def test_parking_sales_tax_is_charged(event_month):
    """Parking is a taxable service in TX - the tax must actually be taken."""
    r = event_month
    assert r["cota_parking"] > 0, "October should have F1 parking revenue"
    assert r["cota_parking_sales_tax"] == pytest.approx(
        r["cota_parking"] * m.PARKING_SALES_TAX_RATE)


def test_payroll_burden_rides_on_bartender_share(event_month):
    assert event_month["payroll_burden"] == pytest.approx(
        event_month["bartender_share"] * m.EMPLOYER_PAYROLL_BURDEN_RATE)


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
    assert 0 < m.TOTAL_DEPRECIABLE_BASIS <= m.TOTAL_PROJECT_COST
    assert (m.DEPRECIABLE_BASIS_5YR + m.DEPRECIABLE_BASIS_15YR
            == m.TOTAL_DEPRECIABLE_BASIS)


def test_depreciation_item_labels_resolve():
    """Guard: the basis lists look items up by exact USE_OF_FUNDS label.

    Renaming a line item in USE_OF_FUNDS silently breaks the basis (or
    KeyErrors) unless the lists are updated with it.
    """
    labels = {label for label, _, _ in m.USE_OF_FUNDS}
    for item in (m.DEPRECIATION_5YR_ITEMS + m.DEPRECIATION_15YR_ITEMS
                 + m.STARTUP_COST_ITEMS):
        assert item in labels, f"{item!r} no longer matches a USE_OF_FUNDS label"


def test_startup_costs_follow_section_195_structure():
    """Up to $5,000 immediately, remainder amortized over 15 years."""
    assert m.STARTUP_COST_BASIS > m.STARTUP_IMMEDIATE_DEDUCTION_CAP
    remainder = m.STARTUP_COST_BASIS - m.STARTUP_IMMEDIATE_DEDUCTION_CAP
    assert m.YEAR1_STARTUP_DEDUCTION == pytest.approx(
        m.STARTUP_IMMEDIATE_DEDUCTION_CAP
        + remainder / m.STARTUP_AMORTIZATION_YEARS)
    assert m.ONGOING_STARTUP_AMORTIZATION < m.YEAR1_STARTUP_DEDUCTION


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
    """A failing bar shouldn't keep base-case beverage/tobacco attach."""
    worst = m.SCENARIOS["Worst Case"]
    base = m.SCENARIOS["Base Case"]
    assert worst["daytime_beverage_attach_rate"] < base["daytime_beverage_attach_rate"]
    assert worst["tobacco_attach_rate"] < base["tobacco_attach_rate"]


# ---------------------------------------------------------------------------
# Break-even
# ---------------------------------------------------------------------------

def test_zero_bar_test_zeroes_every_bar_driven_stream():
    """The no-bar view must also kill daytime beverages and tobacco.

    Those two ride on truck traffic, not bar traffic, so they do NOT zero
    out just because bar customers are set to 0 - the analysis has to pass
    their attach rates explicitly.
    """
    result = m.run_breakeven_analysis(verbose=False)
    annual = result["no_bar_annual"]
    assert annual["total_bar"] == 0
    assert annual["total_daytime_beverage"] == 0
    assert annual["total_tobacco"] == 0
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
    no_tobacco = m.run_monte_carlo(120, seed=3, base_tobacco_attach_rate=0.0)
    assert median(more_slots) > median(base), "more truck slots must raise NOI"
    assert median(no_tobacco) < median(base), "killing tobacco must lower NOI"


def test_monte_carlo_varies_the_new_attach_rates():
    results = m.run_monte_carlo(120, seed=5)
    tob = {round(r["tobacco_attach_rate"], 4) for r in results}
    bev = {round(r["daytime_beverage_attach_rate"], 4) for r in results}
    assert len(tob) > 10, "tobacco attach rate should vary across sims"
    assert len(bev) > 10, "beverage attach rate should vary across sims"


# ---------------------------------------------------------------------------
# Financing
# ---------------------------------------------------------------------------

def test_loc_actual_interest_beats_flat_assumption():
    """The declining-balance sweep must cost less than the flat-nut view."""
    result = m.run_loc_payoff_schedule(verbose=False)
    flat = m.LOC_MONTHLY_INTEREST * len(result["series"])
    assert result["total_interest_paid"] < flat


def test_loc_monthly_interest_derives_from_rate_and_amount():
    assert m.LOC_MONTHLY_INTEREST == round(
        m.LOC_AMOUNT * m.LOC_INTEREST_RATE / 12)


def test_use_of_funds_sums_to_total_project_cost():
    assert sum(a for _, a, _ in m.USE_OF_FUNDS) == m.TOTAL_PROJECT_COST
    assert m.ALREADY_SPENT + m.NEW_CASH_NEEDED == m.TOTAL_PROJECT_COST


def test_monthly_nut_matches_fixed_costs():
    assert m.MONTHLY_NUT == sum(m.FIXED_COSTS.values())
    assert m.ANNUAL_NUT == m.MONTHLY_NUT * 12


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
