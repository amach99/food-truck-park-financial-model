#!/usr/bin/env python3
"""
Food Truck Park + Limited Bar | Del Valle
Interactive Financial Model (leanest concept on the same land as The Cube /
the food-truck-+-RV-park alternative)

Concept:
  - Food truck park (pad rent $500-$1,000 + 5-10% revenue share)
  - Limited bar: prepackaged canned/bottled beer + liquor shots poured into
    sealed plastic shot glasses only. NO mixed drinks, no cocktails, no RV
    park.
  - Power/water/waste/wifi for the truck hubs, sub-metered and billed at cost
    (Texas PUC utility-resale rules: PURA Sec. 39.107 - resale at cost, no
    markup)

Startup cost: ~$75,000, drawn entirely from a personal line of credit (LOC)
at 12.5% interest - not a bank term loan. Of that, ~$48.7K is Phase 0.5 work
already invoiced (site prep, electrical/plumbing rough-in, road base) - the
food truck park itself already opened June 2026. The remaining ~$26K funds
the limited bar buildout, fencing, restroom facility, wifi/cameras, permits,
and contingency.

The LOC is revolving and interest-only (no fixed amortization schedule), so
the model treats the full $75K balance as outstanding for planning purposes
(conservative) inside the fixed monthly nut, while a separate payoff
schedule (Section 7) simulates the balance actually shrinking as free cash
flow gets swept against principal. A "Nut Coverage Ratio" (operating income
before fixed costs / monthly nut, nut now including LOC interest) plays the
analytical role DSCR played in the RV-park version.

Location advantages baked into assumptions:
  - Dollar General next door = easy groceries for park customers/staff
  - Food truck park + limited bar + large TVs = on-site entertainment
  - COTA proximity = event parking + bar uplift on race weekends
"""

import random

# =============================================================================
# SECTION 1: CORE ASSUMPTIONS
# =============================================================================

# --- Capital (financed via personal line of credit, not a bank term loan) ---
TOTAL_PROJECT_COST = 75_000      # all-in startup cost
LOC_AMOUNT = TOTAL_PROJECT_COST  # fully drawn to fund the buildout
LOC_INTEREST_RATE = 0.125        # revolving LOC rate (interest-only, no fixed term)
LOC_MONTHLY_INTEREST = round(LOC_AMOUNT * LOC_INTEREST_RATE / 12)  # $781, assumes full balance stays drawn (conservative)

# --- Use of Funds ---
# Phase 0.5 lines are ACTUALS from DM Remodeling invoices (May-Jul 2026) for
# the food truck park infrastructure, already spent. Those invoices ran
# $15K-$20K over market, so the remaining NEW line items below are priced at
# market rates with 3 bids assumed.
USE_OF_FUNDS = [
    ("Phase 0.5 (paid): site prep, trenching, excavator", 6_700),
    ("Phase 0.5 (paid): electrical + plumbing rough-in", 21_625),
    ("Phase 0.5 (paid): road base, posts, framing, cables", 20_409),
    ("Limited bar buildout (coolers, shot station, POS, stand)", 10_000),
    ("Perimeter fencing + two gates", 6_000),
    ("Restroom facility", 3_500),
    ("WiFi mesh + security cameras", 2_000),
    ("Permits & soft costs", 1_500),
    ("Contingency", 3_266),
]  # totals $75,000
ALREADY_SPENT = sum(a for label, a in USE_OF_FUNDS if "paid" in label)   # $48,734
NEW_CASH_NEEDED = TOTAL_PROJECT_COST - ALREADY_SPENT                     # ~$26,266

# --- Land / Site ---
LAND_ACRES = 4.5
LAND_VALUE = 1_400_000           # same land as The Cube / FTP+RV plans (owned, not financed here)
EVENT_PARKING_SPACES = 150       # spaces available for COTA event parking

# --- Food Truck Park ---
TRUCK_SLOTS = 6                  # utility-hub slots (4 built in Phase 0.5, expandable)
TRUCK_PAD_RENT = 750             # $500-$1,000 range -> midpoint default
TRUCK_REV_SHARE_RATE = 0.075     # 5%-10% range -> midpoint default
TRUCK_AVG_MONTHLY_SALES = 20_000  # per truck gross sales
TRUCK_MARGIN = 1.0               # pure profit (trucks carry their own OpEx)

# Year 1 truck ramp (Phase 0.5 opened with 4 hubs / anchor vendors)
TRUCK_Y1_RAMP = {
    1: 4, 2: 4, 3: 4, 4: 4, 5: 5, 6: 5,
    7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 12: 6,
}

# --- Limited Bar (prepackaged beer + liquor shots ONLY) ---
# Evening-only operation (6pm-10:30/11pm, ~4.5 hrs/day). No mixed drinks, no
# pre-packaged cocktails - just canned/bottled beer and liquor poured/sealed
# into single-serve plastic shot glasses. Simpler than a full container bar:
# no bartender skill/speed requirement, no cocktail markup, minimal equipment
# (coolers + a shot-pour/seal station).
# NEEDS FIELD VALIDATION: throughput (customers/hr) is an estimate.
BAR_HOURS_PER_DAY = 4.5           # 6pm-10:30pm average
BAR_CUSTOMERS_PER_HOUR = 8        # ESTIMATE - validate against comparable venues
BAR_DAILY_CUSTOMERS = round(BAR_HOURS_PER_DAY * BAR_CUSTOMERS_PER_HOUR)  # 36
# Weighted avg check, beer + shots only (no cocktails):
#   75% beer @ $6.00, 25% shot @ $5.00
BAR_AVG_CHECK = 0.75 * 6.00 + 0.25 * 5.00   # $5.75
# Pre-packaged/single-serve goods carry less margin than pouring well liquor
# into mixed drinks (reselling a manufactured/portioned product).
# Weighted COGS: 75% beer ~37% + 25% shot ~25%
COGS_RATE = 0.75 * 0.37 + 0.25 * 0.25       # 34.0%
# NEEDS VERIFICATION: TX Mixed Beverage Gross Receipts Tax (GRT) applies to
# mixed-beverage permit holders. Even single-serve shots dispensed by the
# drink typically still fall under a TABC Mixed Beverage Permit (spirits
# sold "by the drink," not by the sealed factory container, the way canned
# beer is) - confirm with a TABC-savvy CPA before finalizing, since it
# materially affects the variable cost rate below.
GRT_RATE = 0.067                 # TX Mixed Beverage Gross Receipts Tax (verify applicability)
VARIABLE_COST_RATE = COGS_RATE + GRT_RATE  # ~40.7% on bar revenue
CC_PROCESSING_RATE = 0.028
CC_CARD_USAGE_RATE = 0.85
SHRINKAGE_RATE = 0.025           # of beverage COGS value (grab-and-go single-serve
                                  # items may be easier to pilfer than pours - watch this)

# Year 1 bar ramp (park already soft-opened June 2026 -> faster than a new build)
BAR_Y1_RAMP = {
    1: 0.50, 2: 0.60, 3: 0.70, 4: 0.80, 5: 0.85, 6: 0.90, 7: 0.95,
}  # months 8+ = 1.0

# --- Seasonality (outdoor venue, Austin climate) ---
# Spring/fall patio weather peaks, winter cold + deep-summer heat dips.
SEASONALITY = {
    1: 0.65, 2: 0.70, 3: 0.90, 4: 1.00, 5: 1.00, 6: 0.90,
    7: 0.85, 8: 0.85, 9: 0.95, 10: 1.00, 11: 0.90, 12: 0.70,
}

# --- Seasonal one-off events (watch parties on the big TVs) ---
# Bar opens EARLY / stays open full-day for these, so volume assumptions
# hold from the original (larger) model - only the check size is rescaled
# down for the beer/shots-only offering: ratio = new BAR_AVG_CHECK ($5.75) /
# old mixed-drink check ($18.00) = 0.319
SEASONAL_EVENTS = {
    "super_bowl":    {"month": 2,  "rev_base": 630},
    "march_madness": {"month": 3,  "rev_base": 790},
    "nye":           {"month": 12, "rev_base": 790},
}

# --- Utility Pass-Through (sub-metered, billed AT COST) ---
# Texas PUC resale rules (PURA Sec. 39.107, 16 TAC 24.281-24.288): sub-metered
# tenants are billed at cost, no markup. Modeled as offsetting revenue/cost so
# gross billings are visible but NOI impact is zero.
UTILITY_BILL_PER_TRUCK = 350     # trucks pull heavy 50A loads

# --- COTA Event Tiers ---
# Parking uses the 150 spaces available on event days. Incremental costs are
# low: no big venue to staff, just temp parking help + extra porta-potties.
# Bar uplift: on event days the bar extends hours / opens early to serve
# event crowds, so original VOLUME assumptions hold - only the check size is
# rescaled down for the beer/shots-only offering (ratio = $5.75/$18.00 = 0.319).
COTA_EVENT_TIERS = {
    "tier1_f1": {
        "name": "F1 US Grand Prix",
        "parking_price": 80, "parking_occupancy": 1.00, "parking_days": 3,
        "bar_uplift_per_weekend": 3_800,
        "incremental_cost": 6_000,
    },
    "tier2_motogp": {
        "name": "MotoGP Grand Prix of the Americas",
        "parking_price": 55, "parking_occupancy": 0.93, "parking_days": 3,
        "bar_uplift_per_weekend": 1_700,
        "incremental_cost": 3_500,
    },
    "tier2_nascar": {
        "name": "NASCAR Cup Series (EchoPark Grand Prix)",
        "parking_price": 50, "parking_occupancy": 0.80, "parking_days": 2,
        "bar_uplift_per_weekend": 950,
        "incremental_cost": 2_500,
    },
    "tier3_wec": {
        "name": "WEC 6 Hours of COTA",
        "parking_price": 35, "parking_occupancy": 0.70, "parking_days": 2,
        "bar_uplift_per_weekend": 570,
        "incremental_cost": 1_200,
    },
    "tier3_gt_transam": {
        "name": "GT World Challenge / TransAm / Other Races",
        "parking_price": 25, "parking_occupancy": 0.35, "parking_days": 2,
        "bar_uplift_per_weekend": 290,
        "incremental_cost": 500,
    },
    "tier3_concert": {
        "name": "Major Concert (Germania Amphitheater)",
        "parking_price": 30, "parking_occupancy": 0.55, "parking_days": 1,
        "bar_uplift_per_weekend": 190,
        "incremental_cost": 400,
    },
    "tier3_festival": {
        "name": "Festival (FoodieLand, etc.)",
        "parking_price": 30, "parking_occupancy": 0.45, "parking_days": 2,
        "bar_uplift_per_weekend": 160,
        "incremental_cost": 400,
    },
    "tier4_trackday": {
        "name": "Track Day / Car Club / Bike Night",
        "parking_price": 0, "parking_occupancy": 0.10, "parking_days": 1,
        "bar_uplift_per_weekend": 100,
        "incremental_cost": 100,
    },
}

# Same annual calendar as the other Del Valle models (12 events)
COTA_EVENTS_BY_MONTH = {
    1:  [],
    2:  ["tier3_wec"],
    3:  ["tier2_nascar"],
    4:  ["tier2_motogp", "tier3_gt_transam"],
    5:  ["tier3_concert"],
    6:  ["tier3_concert", "tier3_festival"],
    7:  ["tier3_concert"],
    8:  ["tier3_festival"],
    9:  ["tier3_concert"],
    10: ["tier1_f1", "tier3_gt_transam"],
    11: [],
    12: [],
}

# --- Fixed Monthly Costs ("The Nut") ---
# This dict IS the answer to "what are the monthly operating costs" -
# including the LOC interest-only carrying cost (conservative: assumes the
# full $75K balance stays drawn; see run_loc_payoff_schedule for the more
# realistic declining-balance view as free cash flow pays it down).
FIXED_COSTS = {
    "maintenance_cleaning": 1_000,   # part-time cleaner/maintenance
    "insurance": 900,                # GL + liquor liability (beer/shots only) + park liability
    "common_area_utilities": 700,    # lights, TVs, wifi backhaul, office (trucks meter their own power)
    "marketing": 600,                # social + Google
    "waste_service": 400,            # dumpster + porta-potty service
    "wifi_internet": 250,            # park-wide mesh backhaul
    "pos_tech_subscriptions": 250,
    "licenses_permits": 300,         # TABC beer/liquor retailer + health permit renewals
    "maintenance_reserve": 400,
    "property_tax": 2_600,           # land (~$1.4M) + modest improvements @ ~2.1%
    "loc_interest": LOC_MONTHLY_INTEREST,  # 12.5% interest-only on $75K LOC draw
}
MONTHLY_NUT = sum(FIXED_COSTS.values())
ANNUAL_NUT = MONTHLY_NUT * 12

# --- Event-Based Labor (additional bartender for big events only) ---
# Bartender is compensated via 5% revenue share (variable cost, not fixed salary).
# Additional bartender hired only for Super Bowl, NBA Finals, COTA tier1/tier2 events.
EXTRA_BARTENDER_COST = 2_200       # monthly cost if hired for an event week

BIG_EVENT_MONTHS = {
    2: "super_bowl",     # February
    6: "nba_finals",     # June (typically)
}

COTA_TIER1_TIER2_KEYS = ["tier1_f1", "tier2_motogp", "tier2_nascar"]

# --- Multi-Year Growth ---
ANNUAL_GROWTH_RATE = 0.03        # bar traffic + truck sales growth
ANNUAL_RENT_GROWTH = 0.03        # truck rent escalation
ANNUAL_COST_INFLATION = 0.03

# --- Working Capital / Cash Reserve ---
OPENING_CASH_RESERVE = 15_000    # operating buffer held back beyond the $75K buildout

# --- Market context ---
LOCAL_HOUSEHOLDS = 8_754
ANNUAL_COTA_VISITORS = 700_000   # 1.5M total visitors/year, 700K event-attending portion
ANNUAL_COTA_VISITOR_SPENDING = 50  # avg spend per visitor at bar/parking


# =============================================================================
# SECTION 2: REVENUE MODEL FUNCTIONS
# =============================================================================

def has_big_event(month, event_list):
    """Check if month has a big event (Super Bowl, NBA Finals, or COTA tier1/2)."""
    if month in BIG_EVENT_MONTHS:
        return True
    if event_list:
        for tier_key in event_list:
            if tier_key in COTA_TIER1_TIER2_KEYS:
                return True
    return False


def calc_event_labor_cost(month, event_list):
    """Extra bartender cost for big events only (Super Bowl, NBA Finals, COTA tier1/2)."""
    if has_big_event(month, event_list):
        return EXTRA_BARTENDER_COST
    return 0


def calc_truck_revenue(month, year_month=None, slots=None, pad_rent=None,
                       share_rate=None, avg_sales=None):
    """
    Food truck income: pad rent + revenue share.
    Rent is not seasonal (monthly agreements); the revenue-share portion
    follows bar-traffic seasonality since truck sales track park foot traffic.
    """
    max_slots = slots if slots is not None else TRUCK_SLOTS
    rent = pad_rent if pad_rent is not None else TRUCK_PAD_RENT
    share = share_rate if share_rate is not None else TRUCK_REV_SHARE_RATE
    sales = avg_sales if avg_sales is not None else TRUCK_AVG_MONTHLY_SALES

    if year_month is not None:
        trucks = min(max_slots, TRUCK_Y1_RAMP.get(year_month, max_slots))
    else:
        trucks = max_slots

    season = SEASONALITY.get(month, 0.85)
    rent_income = trucks * rent
    share_income = trucks * sales * share * season
    gross = rent_income + share_income
    return {"gross": gross, "net": gross * TRUCK_MARGIN, "trucks": trucks,
            "rent_income": rent_income, "share_income": share_income}


def calc_bar_revenue(daily_customers, month, year_month=None, avg_check=None):
    """Limited bar (beer + shots) monthly revenue with seasonality + Year 1 ramp."""
    check = avg_check if avg_check is not None else BAR_AVG_CHECK
    season = SEASONALITY.get(month, 0.85)
    ramp = BAR_Y1_RAMP.get(year_month, 1.0) if year_month else 1.0
    return daily_customers * check * 30.4 * season * ramp


def calc_seasonal_event_revenue(month, year_month=None, seasonal_pct=1.0):
    """Watch-party spikes (Super Bowl, March Madness, NYE) at the bar."""
    ramp = BAR_Y1_RAMP.get(year_month, 1.0) if year_month else 1.0
    total = 0
    for event in SEASONAL_EVENTS.values():
        if event["month"] == month:
            total += event["rev_base"] * seasonal_pct
    return total * ramp


def calc_cota_event_revenue(event_list, parking_spaces=None):
    """
    COTA event weekends: paid parking + bar uplift.
    event_list: list of tier keys, e.g. ["tier1_f1", "tier3_concert"].
    """
    spaces = parking_spaces if parking_spaces is not None else EVENT_PARKING_SPACES
    if not event_list:
        return {"parking": 0, "bar_uplift": 0,
                "gross": 0, "incremental_cost": 0, "net": 0}

    total_parking = 0
    total_bar = 0
    total_cost = 0
    for tier_key in event_list:
        tier = COTA_EVENT_TIERS.get(tier_key, COTA_EVENT_TIERS["tier3_gt_transam"])
        cars = int(spaces * tier["parking_occupancy"])
        total_parking += cars * tier["parking_price"] * tier["parking_days"]
        total_bar += tier["bar_uplift_per_weekend"]
        total_cost += tier["incremental_cost"]

    gross = total_parking + total_bar
    return {"parking": total_parking, "bar_uplift": total_bar, "gross": gross,
            "incremental_cost": total_cost, "net": gross - total_cost}


def calc_utility_passthrough(active_trucks):
    """
    Sub-metered utility billings. Billed at cost per Texas PUC resale rules,
    so revenue and cost offset exactly (zero NOI impact, shown for visibility).
    """
    billed = active_trucks * UTILITY_BILL_PER_TRUCK
    return {"billed": billed, "cost": billed, "net": 0}


def calc_monthly_total(bar_customers, month, year_month=None,
                       avg_check=None, cota_events=None,
                       truck_slots=None, truck_rent=None,
                       truck_share_rate=None, truck_avg_sales=None,
                       seasonal_pct=1.0):
    """
    Full monthly calculation across all streams:
      1. Food truck rent+share  3. COTA events (parking + bar uplift)
      2. Limited bar             4. Seasonal watch parties
                                  5. Utility pass-through (net zero)
    Returns detailed breakdown dict.
    """
    trucks = calc_truck_revenue(month, year_month, truck_slots, truck_rent,
                                truck_share_rate, truck_avg_sales)
    bar_rev = calc_bar_revenue(bar_customers, month, year_month, avg_check)
    seasonal_rev = calc_seasonal_event_revenue(month, year_month, seasonal_pct)

    if cota_events is not None:
        event_list = cota_events
    else:
        event_list = COTA_EVENTS_BY_MONTH.get(month, [])
    cota = calc_cota_event_revenue(event_list)

    utilities = calc_utility_passthrough(trucks["trucks"])

    total_gross = (trucks["gross"] + bar_rev + seasonal_rev
                   + cota["gross"] + utilities["billed"])

    # Variable costs apply to bar-like revenue only
    bar_like = bar_rev + cota["bar_uplift"] + seasonal_rev
    bar_variable_costs = bar_like * VARIABLE_COST_RATE
    bartender_share = bar_like * 0.05        # bartender gets 5% of bar revenue (variable)
    cc_processing = bar_like * CC_PROCESSING_RATE * CC_CARD_USAGE_RATE
    shrinkage = bar_like * COGS_RATE * SHRINKAGE_RATE

    event_labor_cost = calc_event_labor_cost(month, event_list)
    fixed_costs = MONTHLY_NUT + event_labor_cost

    bar_net = bar_like * (1 - VARIABLE_COST_RATE) - bartender_share - cc_processing - shrinkage
    parking_net = cota["parking"] * 0.95

    total_net_before_fixed = (bar_net + trucks["net"] + parking_net
                              + utilities["net"] - cota["incremental_cost"])
    noi = total_net_before_fixed - fixed_costs

    # "Nut Coverage Ratio" plays the role DSCR played when there was a loan:
    # how many times over does operating income before fixed overhead cover
    # the fixed monthly nut (excluding the one-off event-labor bump)?
    nut_coverage = total_net_before_fixed / MONTHLY_NUT if MONTHLY_NUT > 0 else 0

    return {
        "month": month,
        "truck_rent": trucks["rent_income"],
        "truck_share": trucks["share_income"],
        "truck_gross": trucks["gross"],
        "trucks_active": trucks["trucks"],
        "bar_revenue": bar_rev,
        "seasonal_revenue": seasonal_rev,
        "cota_parking": cota["parking"],
        "cota_bar_uplift": cota["bar_uplift"],
        "cota_incremental_cost": cota["incremental_cost"],
        "utility_billed": utilities["billed"],
        "utility_cost": utilities["cost"],
        "total_gross_revenue": total_gross,
        "bar_variable_costs": bar_variable_costs,
        "bartender_share": bartender_share,
        "cc_processing": cc_processing,
        "shrinkage": shrinkage,
        "event_labor_cost": event_labor_cost,
        "fixed_costs": fixed_costs,
        "total_net_before_fixed": total_net_before_fixed,
        "noi": noi,
        "monthly_nut_coverage": nut_coverage,
        "net_cash_flow": noi,
    }


# =============================================================================
# SECTION 3: ANNUAL AND MULTI-YEAR PROJECTIONS
# =============================================================================

def run_annual_projection(bar_customers=None, year=1, avg_check=None,
                          cota_events_override=None,
                          truck_slots=None, truck_rent=None,
                          truck_share_rate=None, truck_avg_sales=None,
                          seasonal_pct=1.0):
    """
    Full 12-month projection. Returns (months_list, annual_dict).
    Year 1 applies the truck and bar ramps; Year 2+ is steady state.
    """
    custs = bar_customers if bar_customers is not None else BAR_DAILY_CUSTOMERS
    months = []
    for m in range(1, 13):
        year_month = m if year == 1 else None
        if cota_events_override is not None:
            events = cota_events_override.get(m, COTA_EVENTS_BY_MONTH.get(m, []))
        else:
            events = None
        result = calc_monthly_total(
            custs, m, year_month, avg_check, events,
            truck_slots, truck_rent, truck_share_rate, truck_avg_sales,
            seasonal_pct,
        )
        months.append(result)

    annual = summarize_annual(months)
    return months, annual


def summarize_annual(months):
    """Build the annual summary dict from 12 monthly results."""
    return {
        "total_gross": sum(m["total_gross_revenue"] for m in months),
        "total_trucks": sum(m["truck_gross"] for m in months),
        "total_truck_rent": sum(m["truck_rent"] for m in months),
        "total_truck_share": sum(m["truck_share"] for m in months),
        "total_bar": sum(m["bar_revenue"] for m in months),
        "total_seasonal": sum(m["seasonal_revenue"] for m in months),
        "total_cota_parking": sum(m["cota_parking"] for m in months),
        "total_cota_bar": sum(m["cota_bar_uplift"] for m in months),
        "total_cota_cost": sum(m["cota_incremental_cost"] for m in months),
        "total_utility_billed": sum(m["utility_billed"] for m in months),
        "total_bartender_share": sum(m["bartender_share"] for m in months),
        "total_cc_processing": sum(m["cc_processing"] for m in months),
        "total_shrinkage": sum(m["shrinkage"] for m in months),
        "total_event_labor": sum(m["event_labor_cost"] for m in months),
        "total_noi": sum(m["noi"] for m in months),
        "total_net_cash": sum(m["net_cash_flow"] for m in months),
        "avg_monthly_nut_coverage": sum(m["monthly_nut_coverage"] for m in months) / 12,
        "min_monthly_nut_coverage": min(m["monthly_nut_coverage"] for m in months),
        "max_monthly_nut_coverage": max(m["monthly_nut_coverage"] for m in months),
        "annual_nut": ANNUAL_NUT,
        "fcf_yield": sum(m["noi"] for m in months) / TOTAL_PROJECT_COST,
    }


def run_multi_year_projection(base_customers=None, years=3, base_check=None,
                              truck_slots=None, truck_rent=None,
                              truck_share_rate=None, truck_avg_sales=None,
                              seasonal_pct=1.0):
    """
    Year 1 with ramps; Year 2+ steady state with growth and cost inflation.
    Returns list of (year, months, annual) tuples.
    """
    custs0 = base_customers if base_customers is not None else BAR_DAILY_CUSTOMERS
    check0 = base_check if base_check is not None else BAR_AVG_CHECK
    trent0 = truck_rent if truck_rent is not None else TRUCK_PAD_RENT
    tsales0 = truck_avg_sales if truck_avg_sales is not None else TRUCK_AVG_MONTHLY_SALES

    all_years = []
    for yr in range(1, years + 1):
        growth = (1 + ANNUAL_GROWTH_RATE) ** (yr - 1)
        rent_growth = (1 + ANNUAL_RENT_GROWTH) ** (yr - 1)
        cost_mult = (1 + ANNUAL_COST_INFLATION) ** (yr - 1)

        months, annual = run_annual_projection(
            int(custs0 * growth), year=yr, avg_check=check0 * growth,
            truck_slots=truck_slots, truck_rent=trent0 * rent_growth,
            truck_share_rate=truck_share_rate,
            truck_avg_sales=tsales0 * growth,
            seasonal_pct=seasonal_pct,
        )

        if yr > 1:
            inflation_penalty = ANNUAL_NUT * (cost_mult - 1)
            annual["total_noi"] -= inflation_penalty
            annual["total_net_cash"] -= inflation_penalty
            annual["cost_inflation_adj"] = inflation_penalty
            annual["fcf_yield"] = annual["total_noi"] / TOTAL_PROJECT_COST
        else:
            annual["cost_inflation_adj"] = 0

        annual["year"] = yr
        annual["growth_mult"] = growth
        all_years.append((yr, months, annual))

    return all_years


# =============================================================================
# SECTION 4: MONTE CARLO SIMULATION
# =============================================================================

def run_monte_carlo(n_simulations=10_000, seed=42,
                    base_customers=None, base_check=None,
                    base_truck_rent=None, base_truck_share=None,
                    base_seasonal_pct=1.0):
    """
    Randomized Year 1 scenarios. Varies: truck count / rent / revenue share /
    sales, bar traffic and check, COTA event mix, and seasonal event strength.
    Returns list of result dicts (revenue, noi, nut_coverage, cash_flow).
    """
    _custs = base_customers if base_customers is not None else BAR_DAILY_CUSTOMERS
    _check = base_check if base_check is not None else BAR_AVG_CHECK
    _trent = base_truck_rent if base_truck_rent is not None else TRUCK_PAD_RENT
    _tshare = base_truck_share if base_truck_share is not None else TRUCK_REV_SHARE_RATE

    random.seed(seed)
    results = []

    for _ in range(n_simulations):
        custs = max(10, min(70, random.gauss(_custs, 9)))
        check = max(3.5, min(8.0, random.gauss(_check, 0.6)))
        truck_rent = max(500, min(1_000, random.gauss(_trent, 125)))
        truck_share = max(0.05, min(0.10, random.gauss(_tshare, 0.0125)))
        truck_sales = max(10_000, min(35_000, random.gauss(TRUCK_AVG_MONTHLY_SALES, 5_000)))
        slots = random.choice([TRUCK_SLOTS - 2, TRUCK_SLOTS - 1, TRUCK_SLOTS,
                               TRUCK_SLOTS, TRUCK_SLOTS])
        seasonal_pct = max(0.4, min(1.5, random.gauss(base_seasonal_pct, 0.2)))

        # COTA mix: big 4 fixed, concerts/festivals/GT variable
        n_concerts = random.choice([2, 3, 3, 4, 4, 4, 5, 6])
        n_festivals = random.choice([1, 2, 2, 2, 3])
        n_gt = random.choice([0, 1, 1, 2, 2])
        override = {m: [] for m in range(1, 13)}
        override[10].append("tier1_f1")
        override[4].append("tier2_motogp")
        override[3].append("tier2_nascar")
        override[2].append("tier3_wec")
        flexible = (["tier3_concert"] * n_concerts
                    + ["tier3_festival"] * n_festivals
                    + ["tier3_gt_transam"] * n_gt)
        flex_months = [4, 5, 6, 7, 8, 9, 10, 11]
        random.shuffle(flexible)
        for i, tier_key in enumerate(flexible):
            override[flex_months[i % len(flex_months)]].append(tier_key)

        months, ann = run_annual_projection(
            int(custs), year=1, avg_check=check,
            cota_events_override=override,
            truck_slots=slots, truck_rent=truck_rent,
            truck_share_rate=truck_share, truck_avg_sales=truck_sales,
            seasonal_pct=seasonal_pct,
        )

        results.append({
            "revenue": ann["total_gross"],
            "noi": ann["total_noi"],
            "nut_coverage": sum(m["monthly_nut_coverage"] for m in months) / 12,
            "cash_flow": ann["total_net_cash"],
            "bar_custs": custs,
        })

    results.sort(key=lambda x: x["nut_coverage"])
    return results


# =============================================================================
# SECTION 5: SCENARIOS
# =============================================================================

SCENARIOS = {
    "Worst Case": {
        "desc": "3 trucks at floor rent/share, weak bar, no COTA",
        "bar_customers": 21, "avg_check": 4.75,
        "truck_slots": 3, "truck_rent": 500, "truck_share_rate": 0.05,
        "cota_events": {m: [] for m in range(1, 13)},
        "seasonal_pct": 0.5,
    },
    "Stress Test": {
        "desc": "4 trucks, soft bar, big-3 COTA events only",
        "bar_customers": 27, "avg_check": 5.15,
        "truck_slots": 4, "truck_rent": 600, "truck_share_rate": 0.06,
        "cota_events": {m: [] for m in range(1, 13)},  # filled below
        "seasonal_pct": 0.75,
    },
    "Conservative": {
        "desc": "5 trucks at low-mid rent, full COTA calendar",
        "bar_customers": 30, "avg_check": 5.45,
        "truck_slots": 5, "truck_rent": 650, "truck_share_rate": 0.06,
        "cota_events": None,
        "seasonal_pct": 0.75,
    },
    "Base Case": {
        "desc": "6 trucks at $750 + 7.5%, 36 bar customers/evening",
        "bar_customers": 36, "avg_check": 5.75,
        "truck_slots": 6, "truck_rent": 750, "truck_share_rate": 0.075,
        "cota_events": None,
        "seasonal_pct": 1.0,
    },
    "Upside": {
        "desc": "8 trucks at $1,000 + 10%, strong evening bar",
        "bar_customers": 51, "avg_check": 6.35,
        "truck_slots": 8, "truck_rent": 1_000, "truck_share_rate": 0.10,
        "cota_events": None,
        "seasonal_pct": 1.25,
    },
}
_stress_cota = {3: ["tier2_nascar"], 4: ["tier2_motogp"], 10: ["tier1_f1"]}
SCENARIOS["Stress Test"]["cota_events"].update(_stress_cota)


def run_scenario_projection(params):
    """Run an annual projection from a SCENARIOS params dict."""
    return run_annual_projection(
        params["bar_customers"], avg_check=params["avg_check"],
        cota_events_override=params["cota_events"],
        truck_slots=params["truck_slots"], truck_rent=params["truck_rent"],
        truck_share_rate=params["truck_share_rate"],
        seasonal_pct=params.get("seasonal_pct", 1.0),
    )


def run_scenario_comparison():
    """Run all five scenarios side by side (prints table, returns results)."""
    print(f"\n{'=' * 86}")
    print("  SCENARIO COMPARISON — FOOD TRUCK PARK + LIMITED BAR")
    print(f"{'=' * 86}")

    scenario_results = {}
    for name, params in SCENARIOS.items():
        _, ann = run_scenario_projection(params)
        scenario_results[name] = ann

    print(f"\n  {'':>20} ", end="")
    for name in SCENARIOS:
        print(f"{name:>16}", end="")
    print()
    print("  " + "-" * (20 + 16 * len(SCENARIOS)))

    metrics = [
        ("Truck Slots", lambda n: f"{SCENARIOS[n]['truck_slots']:>16}"),
        ("Bar Customers", lambda n: f"{SCENARIOS[n]['bar_customers']:>16}"),
        ("Annual Revenue", lambda n: f"${scenario_results[n]['total_gross']:>14,.0f}"),
        ("Annual NOI", lambda n: f"${scenario_results[n]['total_noi']:>14,.0f}"),
        ("Free Cash Flow", lambda n: f"${scenario_results[n]['total_net_cash']:>14,.0f}"),
        ("FCF Yield on Total Cost", lambda n: f"{scenario_results[n]['fcf_yield']:>15.1%}"),
        ("Nut Coverage", lambda n: f"{scenario_results[n]['avg_monthly_nut_coverage']:>15.2f}x"),
    ]
    for label, fmt in metrics:
        print(f"  {label:>20} ", end="")
        for name in SCENARIOS:
            print(fmt(name), end="")
        print()

    print()
    for name, params in SCENARIOS.items():
        print(f"  {name}: {params['desc']}")

    return scenario_results


# =============================================================================
# SECTION 6: BREAK-EVEN + SENSITIVITY
# =============================================================================

def run_breakeven_analysis(verbose=True):
    """
    Two break-even views:
      1. Can food trucks alone cover the nut (zero bar)?
      2. Minimum bar traffic to hit nut-coverage targets with a weak-truck base.
    Returns a dict of results.
    """
    # View 1: no bar at all, base truck slots
    months, no_bar = run_annual_projection(
        0, avg_check=0,
        cota_events_override={m: [] for m in range(1, 13)},
        seasonal_pct=0.0,
    )

    # View 2: minimum bar traffic for nut-coverage targets (weak truck base:
    # 4 trucks @ $600 + 5%, no COTA)
    targets = [("Break-even", 1.0), ("Comfortable", 1.25),
               ("Strong", 1.50), ("Excellent", 2.0)]
    custs_results = []
    for label, target in targets:
        lo, hi = 0.0, 150.0
        for _ in range(25):
            mid = (lo + hi) / 2
            _, ann = run_annual_projection(
                mid, avg_check=4.75,
                truck_slots=4, truck_rent=600, truck_share_rate=0.05,
                cota_events_override={m: [] for m in range(1, 13)},
                seasonal_pct=0.0,
            )
            if ann["avg_monthly_nut_coverage"] >= target:
                hi = mid
            else:
                lo = mid
        custs_results.append((label, target, hi))

    if verbose:
        print(f"\n{'=' * 70}")
        print("  BREAK-EVEN ANALYSIS")
        print(f"{'=' * 70}")
        print(f"\n  Monthly Nut (all fixed operating costs): ${MONTHLY_NUT:>10,.0f}")
        print(f"  (Includes ${LOC_MONTHLY_INTEREST:,.0f}/mo LOC interest-only carrying cost)")
        print(f"\n  1. ZERO-BAR TEST (6 trucks, no bar, no COTA):")
        print(f"     Annual NOI:  ${no_bar['total_noi']:>12,.0f}")
        print(f"     Nut Coverage: {no_bar['avg_monthly_nut_coverage']:>11.2f}x")
        verdict = "COVERS THE NUT" if no_bar["avg_monthly_nut_coverage"] >= 1.0 else "DOES NOT COVER"
        print(f"     -> Truck rent alone {verdict}")
        print(f"\n  2. MIN BAR TRAFFIC BY NUT-COVERAGE TARGET")
        print(f"     (weak base: 4 trucks @ $600 + 5%, $4.75 check, no COTA)")
        for label, target, custs in custs_results:
            print(f"     {label:<14} ({target:.2f}x): {custs:>5.0f} bar customers/evening")

    return {"no_bar_annual": no_bar, "bar_traffic_targets": custs_results}


def run_sensitivity_analysis():
    """Grid sensitivities on the three main levers."""
    print(f"\n{'=' * 70}")
    print("  SENSITIVITY ANALYSIS")
    print(f"{'=' * 70}")

    print(f"\n  1. Food Truck Count Impact (base bar)")
    print(f"  {'Trucks':>12} {'Annual Rev':>14} {'NOI':>12} {'Nut Cov':>9} {'Cash Flow':>12}")
    print("  " + "-" * 62)
    for slots in [2, 3, 4, 5, 6, 8]:
        _, ann = run_annual_projection(truck_slots=slots)
        print(f"  {slots:>12} ${ann['total_gross']:>13,.0f} ${ann['total_noi']:>11,.0f} "
              f"{ann['avg_monthly_nut_coverage']:>8.2f}x ${ann['total_net_cash']:>11,.0f}")

    print(f"\n  2. Truck Avg Monthly Sales Impact (base trucks + bar)")
    print(f"  {'Avg Sales/Truck':>16} {'Annual Rev':>14} {'NOI':>12} {'Nut Cov':>9} {'Cash Flow':>12}")
    print("  " + "-" * 66)
    for sales in [10_000, 15_000, 20_000, 25_000, 30_000, 35_000]:
        _, ann = run_annual_projection(truck_avg_sales=sales)
        print(f"  ${sales:>15,} ${ann['total_gross']:>13,.0f} ${ann['total_noi']:>11,.0f} "
              f"{ann['avg_monthly_nut_coverage']:>8.2f}x ${ann['total_net_cash']:>11,.0f}")

    print(f"\n  3. Bar Traffic Impact (base trucks, evening-only bar)")
    print(f"  {'Customers/Evening':>14} {'Annual Rev':>14} {'NOI':>12} {'Nut Cov':>9} {'Cash Flow':>12}")
    print("  " + "-" * 64)
    for custs in [12, 21, 30, 36, 45, 54, 66]:
        _, ann = run_annual_projection(custs)
        print(f"  {custs:>14} ${ann['total_gross']:>13,.0f} ${ann['total_noi']:>11,.0f} "
              f"{ann['avg_monthly_nut_coverage']:>8.2f}x ${ann['total_net_cash']:>11,.0f}")

    print(f"\n  4. COTA Decline Stress Test (base case)")
    full_events = []
    for m in range(1, 13):
        for tier in COTA_EVENTS_BY_MONTH.get(m, []):
            full_events.append((m, tier))
    print(f"  {'COTA Decline':>14} {'COTA Rev':>12} {'Nut Cov':>9}")
    print("  " + "-" * 38)
    for pct in [0, 50, 100]:
        remaining = max(0, int(len(full_events) * (1 - pct / 100)))
        override = {m: [] for m in range(1, 13)}
        for month, tier in full_events[:remaining]:
            override[month].append(tier)
        _, ann = run_annual_projection(cota_events_override=override)
        cota_rev = ann["total_cota_parking"] + ann["total_cota_bar"]
        print(f"  {pct:>13}% ${cota_rev:>11,.0f} {ann['avg_monthly_nut_coverage']:>8.2f}x")


# =============================================================================
# SECTION 7: CASH RESERVE + LOC PAYOFF TRACKER
# =============================================================================

def run_cash_reserve_tracker(all_years=None, verbose=True):
    """Track working-capital balance month-by-month from OPENING_CASH_RESERVE,
    plus the month cumulative NOI reaches the $75K total capital deployed."""
    if all_years is None:
        all_years = run_multi_year_projection()

    balance = OPENING_CASH_RESERVE
    min_balance = balance
    min_balance_month = (1, 1)
    months_negative = 0
    cumulative_cf = 0
    cumulative_noi = 0
    break_even_month = None
    payback_month = None
    series = []

    for yr, months, annual in all_years:
        for m in months:
            cf = m["net_cash_flow"]
            if yr > 1:
                cost_mult = (1 + ANNUAL_COST_INFLATION) ** (yr - 1)
                cf -= MONTHLY_NUT * (cost_mult - 1)
            cumulative_cf += cf
            cumulative_noi += cf
            balance += cf
            if balance < min_balance:
                min_balance = balance
                min_balance_month = (yr, m["month"])
            if cf < 0:
                months_negative += 1
            if break_even_month is None and cumulative_cf > 0:
                break_even_month = (yr, m["month"])
            if payback_month is None and cumulative_noi >= TOTAL_PROJECT_COST:
                payback_month = (yr, m["month"])
            series.append({"year": yr, "month": m["month"], "cf": cf,
                           "cumulative": cumulative_cf, "balance": balance,
                           "cumulative_noi": cumulative_noi})

    if verbose:
        print(f"\n{'=' * 70}")
        print("  CASH RESERVE TRACKER")
        print(f"{'=' * 70}")
        print(f"\n  Opening Operating Reserve: ${OPENING_CASH_RESERVE:,.0f}")
        print(f"  Lowest balance: ${min_balance:,.0f} "
              f"(Year {min_balance_month[0]}, Month {min_balance_month[1]})")
        print(f"  Months with negative CF: {months_negative}")
        if payback_month:
            print(f"  ${TOTAL_PROJECT_COST:,.0f} total capital deployed recouped "
                  f"(cumulative NOI) by: Year {payback_month[0]}, Month {payback_month[1]}")
        else:
            print(f"  Capital deployed NOT recouped within the projection window.")

    return {"min_balance": min_balance, "min_month": min_balance_month,
            "months_negative": months_negative,
            "break_even_month": break_even_month,
            "payback_month": payback_month, "series": series}


def run_loc_payoff_schedule(all_years=None, sweep_pct=1.0, verbose=True):
    """
    Simulate the $75K LOC balance actually shrinking over time, rather than
    the conservative "full balance always drawn" assumption baked into
    MONTHLY_NUT. Each month, `sweep_pct` of free cash flow (before the flat
    LOC_MONTHLY_INTEREST assumption) goes to interest on the DECLINING
    balance first, then principal. Returns the payoff month and total
    interest actually paid, which will run lower than the conservative nut
    implies once the balance starts coming down.
    """
    if all_years is None:
        all_years = run_multi_year_projection()

    balance = LOC_AMOUNT
    total_interest_paid = 0.0
    payoff_month = None
    series = []

    for yr, months, annual in all_years:
        cost_mult = (1 + ANNUAL_COST_INFLATION) ** (yr - 1) if yr > 1 else 1.0
        for m in months:
            noi_before_financing = m["noi"] + LOC_MONTHLY_INTEREST
            if yr > 1:
                noi_before_financing -= MONTHLY_NUT * (cost_mult - 1)

            if balance <= 0.01:
                interest, principal_payment = 0.0, 0.0
            else:
                interest = balance * LOC_INTEREST_RATE / 12
                available = max(0.0, noi_before_financing - interest) * sweep_pct
                principal_payment = min(balance, available)
                balance -= principal_payment
                total_interest_paid += interest

            if payoff_month is None and balance <= 0.01:
                payoff_month = (yr, m["month"])
            series.append({"year": yr, "month": m["month"],
                           "balance": max(balance, 0.0), "interest": interest,
                           "principal_payment": principal_payment})

    if verbose:
        print(f"\n{'=' * 70}")
        print("  LOC PAYOFF SCHEDULE")
        print(f"{'=' * 70}")
        print(f"\n  Starting LOC Balance: ${LOC_AMOUNT:,.0f} @ {LOC_INTEREST_RATE:.1%}")
        print(f"  Conservative nut assumption: ${LOC_MONTHLY_INTEREST:,.0f}/mo "
              f"interest (full balance held flat)")
        if payoff_month:
            print(f"  Actual payoff (sweeping {sweep_pct:.0%} of free cash flow "
                  f"to principal): Year {payoff_month[0]}, Month {payoff_month[1]}")
        else:
            print(f"  Not paid off within the projection window at this sweep rate.")
        print(f"  Total interest actually paid: ${total_interest_paid:,.0f} "
              f"(vs. ${LOC_MONTHLY_INTEREST * len(series):,.0f} under the flat assumption)")

    return {"payoff_month": payoff_month, "total_interest_paid": total_interest_paid,
            "final_balance": max(balance, 0.0), "series": series}


def print_owner_summary():
    """Owner-facing summary for the LOC-financed food truck park + limited bar concept."""
    print(f"\n{'=' * 70}")
    print("  OWNER SUMMARY")
    print("  Food Truck Park + Limited Bar (Beer & Shots) | Del Valle, TX")
    print(f"{'=' * 70}")

    print(f"\n  STARTUP COST — FINANCED VIA PERSONAL LINE OF CREDIT")
    print(f"  {'Total Startup Cost:':<30} ${TOTAL_PROJECT_COST:>14,.0f}")
    print(f"  {'LOC Draw / Rate:':<30} ${LOC_AMOUNT:>10,.0f} @ {LOC_INTEREST_RATE:.1%}")
    print(f"  {'Already Spent (Phase 0.5):':<30} ${ALREADY_SPENT:>14,.0f}")
    print(f"  {'New Draw Needed:':<30} ${NEW_CASH_NEEDED:>14,.0f}")

    print(f"\n  USE OF FUNDS")
    for label, amt in USE_OF_FUNDS:
        print(f"  {label:<52} ${amt:>10,.0f}")
    print(f"  {'TOTAL':<52} ${sum(a for _, a in USE_OF_FUNDS):>10,.0f}")

    print(f"\n  MONTHLY OPERATING COSTS (The Nut, incl. LOC interest)")
    for label, amt in FIXED_COSTS.items():
        print(f"  {label.replace('_', ' ').title():<35} ${amt:>10,.0f}")
    print(f"  {'Total Monthly Nut':<35} ${MONTHLY_NUT:>10,.0f}")
    print(f"  {'Total Annual Nut':<35} ${ANNUAL_NUT:>10,.0f}")
    print(f"  (LOC interest line assumes the full ${LOC_AMOUNT:,.0f} balance stays "
          f"drawn - conservative. See run_loc_payoff_schedule() for the declining-"
          f"balance view as free cash flow pays it down.)")

    _, conservative = run_scenario_projection(SCENARIOS["Conservative"])
    _, base = run_scenario_projection(SCENARIOS["Base Case"])

    print(f"\n  PROJECTED PERFORMANCE (Year 1)")
    print(f"  {'':>25} {'Conservative':>16} {'Base Case':>16}")
    print("  " + "-" * 58)
    print(f"  {'Annual Revenue':<25} ${conservative['total_gross']:>15,.0f} ${base['total_gross']:>15,.0f}")
    print(f"  {'Annual NOI':<25} ${conservative['total_noi']:>15,.0f} ${base['total_noi']:>15,.0f}")
    print(f"  {'Free Cash Flow':<25} ${conservative['total_net_cash']:>15,.0f} ${base['total_net_cash']:>15,.0f}")
    print(f"  {'FCF Yield on Total Cost':<25} {conservative['fcf_yield']:>15.1%} {base['fcf_yield']:>15.1%}")

    print(f"\n  REVENUE STREAMS (Base Case, Year 1)")
    print(f"  {'Food Trucks (rent + share)':<32} ${base['total_trucks']:>14,.0f}")
    print(f"  {'Limited Bar (beer + shots)':<32} ${base['total_bar']:>14,.0f}")
    print(f"  {'COTA Events (all)':<32} "
          f"${base['total_cota_parking'] + base['total_cota_bar']:>14,.0f}")
    print(f"  {'Seasonal Watch Parties':<32} ${base['total_seasonal']:>14,.0f}")
    print(f"  {'Utility Pass-Through (at cost)':<32} ${base['total_utility_billed']:>14,.0f}")

    print(f"\n  RISK MITIGANTS")
    print(f"  - LOC is revolving/interest-only (no fixed amortization) - free cash "
          f"flow can sweep the ${LOC_AMOUNT:,.0f} balance down faster than the "
          f"conservative flat-interest nut assumes")
    print(f"  - Phase 0.5 food truck park already operating (opened June 2026)")
    print(f"  - Simple offering (beer + sealed shots only) = minimal labor skill/speed needs")
    print(f"  - Land collateral (${LAND_VALUE:,.0f}) already owned, not financed here")
    print(f"  - Utilities sub-metered and billed at cost (no margin leakage)")
    print(f"  - COTA event upside preserved: parking + bar uplift")


# =============================================================================
# SECTION 8: CLI MENU
# =============================================================================

def print_annual_summary(months, annual, label=""):
    """Pretty-print a full annual projection."""
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    print(f"\n{'=' * 76}")
    if label:
        print(f"  {label}")
    print(f"{'=' * 76}")
    print(f"{'Month':<7} {'Gross':>10} {'Trucks':>9} {'Bar':>9} "
          f"{'COTA':>9} {'NOI':>10} {'NutCov':>7}")
    print("-" * 76)
    for m in months:
        cota = m["cota_parking"] + m["cota_bar_uplift"]
        print(f"{month_names[m['month']]:<7} ${m['total_gross_revenue']:>9,.0f} "
              f"${m['truck_gross']:>8,.0f} "
              f"${m['bar_revenue']:>8,.0f} ${cota:>8,.0f} "
              f"${m['noi']:>9,.0f} {m['monthly_nut_coverage']:>6.2f}x")
    print("-" * 76)
    cota_total = annual["total_cota_parking"] + annual["total_cota_bar"]
    print(f"{'YEAR':<7} ${annual['total_gross']:>9,.0f} "
          f"${annual['total_trucks']:>8,.0f} ${annual['total_bar']:>8,.0f} "
          f"${cota_total:>8,.0f} ${annual['total_noi']:>9,.0f} "
          f"{annual['avg_monthly_nut_coverage']:>6.2f}x")
    print(f"\n  Annual Nut:              ${ANNUAL_NUT:,.0f}")
    print(f"  Free Cash Flow:          ${annual['total_net_cash']:,.0f}")
    print(f"  FCF Yield on Total Cost: {annual['fcf_yield']:.1%}")


def main():
    menu = """
==================================================
  FOOD TRUCK PARK + LIMITED BAR | Financial Model
==================================================
  1. Annual Projection (Base Case)
  2. Sensitivity Analysis
  3. Break-Even Analysis
  4. Monte Carlo (10K scenarios)
  5. Scenario Comparison
  6. Owner Summary
  7. Cash Reserve Tracker
  8. LOC Payoff Schedule
  0. Exit
=================================================="""
    while True:
        print(menu)
        try:
            choice = input("\n  Select option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if choice == "1":
            months, ann = run_annual_projection()
            print_annual_summary(months, ann,
                                 "BASE CASE: 6 trucks, 36 bar customers/evening")
        elif choice == "2":
            run_sensitivity_analysis()
        elif choice == "3":
            run_breakeven_analysis()
        elif choice == "4":
            results = run_monte_carlo()
            covs = sorted(r["nut_coverage"] for r in results)
            cfs = sorted(r["cash_flow"] for r in results)
            n = len(results)
            print(f"\n  MONTE CARLO ({n:,} scenarios)")
            print(f"  Median Nut Coverage: {covs[n // 2]:.2f}x | "
                  f"P5: {covs[int(n * 0.05)]:.2f}x | "
                  f"P95: {covs[int(n * 0.95)]:.2f}x")
            print(f"  Median Free CF: ${cfs[n // 2]:,.0f}")
            print(f"  P(Nut Coverage >= 1.0x): "
                  f"{sum(1 for c in covs if c >= 1.0) / n * 100:.1f}%")
        elif choice == "5":
            run_scenario_comparison()
        elif choice == "6":
            print_owner_summary()
        elif choice == "7":
            run_cash_reserve_tracker()
        elif choice == "8":
            run_loc_payoff_schedule()
        elif choice == "0":
            print("\n  Goodbye!")
            break
        else:
            print("  Invalid choice. Try again.")


if __name__ == "__main__":
    main()
