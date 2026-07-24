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

Startup cost: ~$75K, drawn entirely from a personal line of credit (LOC) at
12.5% interest - not a bank term loan. USE_OF_FUNDS is sourced from the
owner's actual "Phase 0.5 Master Plan" cost tracker (Notion), itemized with
real vendor-quoted prices rather than estimated buckets, plus a few real
costs the tracker doesn't capture yet (refrigerators, initial beer/liquor
inventory). Of that, ~$39.2K is already paid, ~$2.3K is in progress, and
~$34.6K (including permits/contingency) is not yet started. Line items the
owner flagged as planning-only and never implemented (generator, grease
removal service, propane tank service) are excluded entirely rather than
estimated.

The LOC is revolving and interest-only (no fixed amortization schedule), so
the model treats the full LOC balance as outstanding for planning purposes
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

MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# =============================================================================
# SECTION 1: CORE ASSUMPTIONS
# =============================================================================

# --- Use of Funds ---
# Sourced from the owner's real "Phase 0.5 Master Plan" cost tracker
# (Notion), itemized at actual vendor-quoted prices, plus a few real costs
# the tracker doesn't capture yet (refrigerators, initial bar inventory).
# Each entry carries its real build status. Excluded entirely (per owner
# instruction - these were planning-only line items never actually
# implemented, with no cost attached): a second/backup generator, grease
# removal service, propane tank service. "Container Bar" (no price ever set
# in the tracker) is replaced below by the actual plan: a $1,500 Walmart
# shed fitted out with fridges, shelves, and a POS station.
USE_OF_FUNDS = [
    # -- Done (already paid) --
    ("Turf", 1_500, "done"),
    ("Sail Shades", 3_378, "done"),
    ("Security system", 710, "done"),
    ("Gates", 1_000, "done"),
    ("TVs", 2_600, "done"),
    ("TV Mounts", 188, "done"),
    ("Mist Fans (pole-mounted)", 780, "done"),
    ("Pole Lighting / String Lights", 303, "done"),
    ("Signs", 134, "done"),
    ("Deluxe Porta Potty setup", 120, "done"),
    ("StarLink Internet equipment", 50, "done"),
    ("Benches", 968, "done"),
    ("Electrical", 17_000, "done"),
    ("Plumbing", 5_850, "done"),
    ("Telephone pole", 550, "done"),
    ("TV encasing", 1_150, "done"),
    ("Full land clearing", 2_000, "done"),
    ("Yard Multi-Purpose Poles (set & anchor)", 900, "done"),
    # -- In progress --
    ("Cleaning", 2_100, "in_progress"),
    ("Sound System / Speakers", 200, "in_progress"),
    # -- Not started --
    ("Gravel", 15_400, "not_started"),
    ("Trash Cans", 200, "not_started"),
    ("Storage Shed (wooden, general)", 3_119, "not_started"),
    ("Bar shed - Walmart (fridges, shelves, POS)", 1_500, "not_started"),
    ("Refrigerators (bar coolers)", 3_000, "not_started"),
    ("Initial beverage inventory (beer + liquor stock)", 3_600, "not_started"),
    ("Permits & soft costs (TABC, health, business license)", 1_500, "not_started"),
    ("Contingency", 6_300, "not_started"),
]
TOTAL_PROJECT_COST = sum(a for _, a, _ in USE_OF_FUNDS)  # ~$75,000
ALREADY_SPENT = sum(a for _, a, status in USE_OF_FUNDS if status == "done")  # $10,763
NEW_CASH_NEEDED = TOTAL_PROJECT_COST - ALREADY_SPENT                          # $58,737

# --- Capital (financed via personal line of credit, not a bank term loan) ---
LOC_AMOUNT = TOTAL_PROJECT_COST  # fully drawn to fund the buildout
LOC_INTEREST_RATE = 0.125        # revolving LOC rate (interest-only, no fixed term)
LOC_MONTHLY_INTEREST = round(LOC_AMOUNT * LOC_INTEREST_RATE / 12)  # assumes full balance stays drawn (conservative)

# --- Land / Site ---
LAND_ACRES = 4.5
LAND_VALUE = 1_400_000           # same land as The Cube / FTP+RV plans (owned, not financed here)
# Dedicated 3-acre lot within the property, laid out for COTA event parking.
# Owner estimate: fits 240-300 cars -> using the midpoint.
EVENT_PARKING_SPACES = 270       # spaces available for COTA event parking

# --- Food Truck Park ---
# 4 utility hubs built and operating today. Owner plans to run with these 4
# for at least a year - building more hubs (to get beyond 4) costs additional
# capital that isn't budgeted, so there's no Year 1 ramp: all 4 are active
# from month 1. TRUCK_SLOTS stays adjustable (via the slider/scenarios) for
# exploring a future expansion, but the default reflects today's reality.
TRUCK_SLOTS = 4                  # utility-hub slots built and active today
TRUCK_PAD_RENT = 500             # actual starting terms: $500 base rent
TRUCK_REV_SHARE_RATE = 0.10      # actual starting terms: 10% revenue share
# Per-truck gross sales. Vendors report ~$20K/mo TODAY from a poor location
# (in front of a house, no foot traffic). This park sits on a busy road next
# to a Dollar General hotspot, which pushes the other way (more foot traffic),
# while co-locating 4 trucks could split demand somewhat. Net effect is
# uncertain, so $20K is held as a deliberately conservative base with clear
# upside - adjust via the slider to test a busier-location premium.
TRUCK_AVG_MONTHLY_SALES = 20_000  # per truck gross sales (conservative base)
TRUCK_MARGIN = 1.0               # pure profit (trucks carry their own OpEx)
# Expected fraction of built slots actually rented at any given time. Vendors
# sign 6-month contracts, which bounds churn, but a vendor leaving at term
# leaves a slot empty for a re-leasing gap (~1-1.5 mo/yr per slot at 90%).
# 1.0 = always full / waitlist; lower = more vacancy. Applied as an expected-
# value haircut on BOTH pad rent and revenue share.
TRUCK_OCCUPANCY = 0.90

# --- Opening Date ---
# Operations begin September 2026 (owner's target: mid-Aug/early-Sep - using
# the later, more conservative date). "Operating month 1" in BAR_Y1_RAMP
# means "1st month since opening," NOT January - it maps to this calendar
# month, and each subsequent operating month advances the calendar by one,
# wrapping year-end. Update OPENING_MONTH if the actual open date shifts;
# everything else (seasonality, COTA calendar) derives from it.
OPENING_MONTH = 9   # September
OPENING_YEAR = 2026


def operating_to_calendar_month(op_month, opening_month=None):
    """Map an operating-month index (1-12, months since opening) to the
    calendar month (1-12) it actually falls in, given OPENING_MONTH."""
    start = opening_month if opening_month is not None else OPENING_MONTH
    return ((start - 1 + (op_month - 1)) % 12) + 1

# --- Limited Bar (prepackaged beer + liquor shots ONLY) ---
# Evening-only operation (6pm-10:30/11pm, ~4.5 hrs/day). No mixed drinks, no
# pre-packaged cocktails - just canned/bottled beer and liquor poured/sealed
# into single-serve plastic shot glasses. Simpler than a full container bar:
# no bartender skill/speed requirement, no cocktail markup, minimal equipment
# (coolers + a shot-pour/seal station).
BAR_HOURS_PER_DAY = 4.5           # 6pm-10:30pm average
# Weekday (Mon-Thu) vs weekend (Fri-Sun) traffic, ESTIMATES needing field
# validation. Split rather than a single flat daily average because a bar's
# staffing doesn't change either way (one bartender, comped via revenue
# share - see FIXED_COSTS comment), so the only value in more granularity is
# revenue accuracy: a flat average would understate true weekend volume
# (dragged down by quiet weekdays) right where COTA event uplift needs an
# accurate weekend baseline to build on. Not split further than this (e.g.
# day-by-day or hourly) since that would add complexity with no cost-side
# payoff.
BAR_WEEKDAY_CUSTOMERS = 20        # Mon-Thu evening average
BAR_WEEKEND_CUSTOMERS = 58        # Fri-Sun evening average
# Average days/month split 4:3 (Mon-Thu : Fri-Sun) rather than an exact
# calendar lookup, consistent with how the rest of the model treats months.
WEEKDAY_DAYS_PER_MONTH = 30.4 * 4 / 7   # ~17.37
WEEKEND_DAYS_PER_MONTH = 30.4 * 3 / 7   # ~13.03
# Blended average, for display/back-compat only - NOT used in revenue math.
BAR_DAILY_CUSTOMERS = round(
    (BAR_WEEKDAY_CUSTOMERS * WEEKDAY_DAYS_PER_MONTH
     + BAR_WEEKEND_CUSTOMERS * WEEKEND_DAYS_PER_MONTH) / 30.4
)  # ~36, same order of magnitude as the prior flat estimate
# Unit pricing (owner-specified):
BEER_PRICE = 7.00                 # per canned/bottled beer
SHOT_PRICE = 3.00                 # per single-serve plastic shot glass
BEER_MIX_PCT = 0.75                # 75% of items sold are beer, 25% shots
SHOT_MIX_PCT = 0.25
DRINKS_PER_VISIT = 1.5            # avg items (beer + shots combined) per customer visit
AVG_ITEM_PRICE = BEER_MIX_PCT * BEER_PRICE + SHOT_MIX_PCT * SHOT_PRICE  # $6.00
BAR_AVG_CHECK = DRINKS_PER_VISIT * AVG_ITEM_PRICE   # $9.00/visit
# Pre-packaged/single-serve goods carry less margin than pouring well liquor
# into mixed drinks (reselling a manufactured/portioned product).
# COGS weighted by REVENUE share of each item (not item count), since beer
# and shots carry different prices: beer ~37% COGS, shot ~25% COGS.
_beer_rev_frac = (BEER_MIX_PCT * BEER_PRICE) / AVG_ITEM_PRICE   # 87.5% of $ revenue
_shot_rev_frac = (SHOT_MIX_PCT * SHOT_PRICE) / AVG_ITEM_PRICE   # 12.5% of $ revenue
COGS_RATE = _beer_rev_frac * 0.37 + _shot_rev_frac * 0.25        # 35.5%
# NEEDS VERIFICATION: TX Mixed Beverage Gross Receipts Tax (GRT) applies to
# mixed-beverage permit holders. Even single-serve shots dispensed by the
# drink typically still fall under a TABC Mixed Beverage Permit (spirits
# sold "by the drink," not by the sealed factory container, the way canned
# beer is) - confirm with a TABC-savvy CPA before finalizing, since it
# materially affects the variable cost rate below.
GRT_RATE = 0.067                 # TX Mixed Beverage Gross Receipts Tax (verify applicability)
VARIABLE_COST_RATE = COGS_RATE + GRT_RATE  # ~42.2% on bar revenue
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
# for the beer/shots-only offering: ratio = new BAR_AVG_CHECK ($9.00) /
# old mixed-drink check ($18.00) = 0.50
SEASONAL_EVENTS = {
    "super_bowl":    {"month": 2,  "rev_base": 985},
    "march_madness": {"month": 3,  "rev_base": 1_235},
    "nye":           {"month": 12, "rev_base": 1_235},
}

# --- Utility Pass-Through (sub-metered, billed AT COST) ---
# Texas PUC resale rules (PURA Sec. 39.107, 16 TAC 24.281-24.288): sub-metered
# tenants are billed at cost, no markup. Modeled as offsetting revenue/cost so
# gross billings are visible but NOI impact is zero.
UTILITY_BILL_PER_TRUCK = 350     # trucks pull heavy 50A loads

# --- COTA Event Tiers ---
# Parking uses the dedicated 3-acre lot (EVENT_PARKING_SPACES = 270 spaces)
# on event days. The F1 tier price of $80/spot is VALIDATED against what
# neighboring lots actually charge on F1 weekends - and this lot offers more
# value (on-site food trucks, bar, and a place to hang out while post-event
# traffic clears), which supports both the price and repeat/word-of-mouth
# demand vs. a bare gravel lot. "incremental_cost" is hired parking-operations
# staff (to organize/run the lot) + extra porta-potty rental for the weekend
# - not a big-venue staffing budget - scaled up ~1.8x from the original
# 150-space sizing to cover the larger lot's staffing needs.
# Bar uplift: on event days the bar extends hours / opens early to serve
# event crowds AND runs premium event pricing ($12 beer / $5 shot instead of
# the normal $7/$3), so uplift = normal-check uplift x (event check / normal
# check) = x($15.375/$9.00) = x1.708.
COTA_EVENT_BEER_PRICE = 12.00
COTA_EVENT_SHOT_PRICE = 5.00
COTA_EVENT_AVG_CHECK = DRINKS_PER_VISIT * (BEER_MIX_PCT * COTA_EVENT_BEER_PRICE
                                            + SHOT_MIX_PCT * COTA_EVENT_SHOT_PRICE)  # $15.375
COTA_EVENT_TIERS = {
    "tier1_f1": {
        "name": "F1 US Grand Prix",
        "parking_price": 80, "parking_occupancy": 1.00, "parking_days": 3,
        "bar_uplift_per_weekend": 10_165,
        "incremental_cost": 10_800,
    },
    "tier2_motogp": {
        "name": "MotoGP Grand Prix of the Americas",
        "parking_price": 55, "parking_occupancy": 0.93, "parking_days": 3,
        "bar_uplift_per_weekend": 4_545,
        "incremental_cost": 6_300,
    },
    "tier2_nascar": {
        "name": "NASCAR Cup Series (EchoPark Grand Prix)",
        "parking_price": 50, "parking_occupancy": 0.80, "parking_days": 2,
        "bar_uplift_per_weekend": 2_545,
        "incremental_cost": 4_500,
    },
    "tier3_wec": {
        "name": "WEC 6 Hours of COTA",
        "parking_price": 35, "parking_occupancy": 0.70, "parking_days": 2,
        "bar_uplift_per_weekend": 1_520,
        "incremental_cost": 2_160,
    },
    "tier3_gt_transam": {
        "name": "GT World Challenge / TransAm / Other Races",
        "parking_price": 25, "parking_occupancy": 0.35, "parking_days": 2,
        "bar_uplift_per_weekend": 775,
        "incremental_cost": 900,
    },
    "tier3_concert": {
        "name": "Major Concert (Germania Amphitheater)",
        "parking_price": 30, "parking_occupancy": 0.55, "parking_days": 1,
        "bar_uplift_per_weekend": 510,
        "incremental_cost": 720,
    },
    "tier3_festival": {
        "name": "Festival (FoodieLand, etc.)",
        "parking_price": 30, "parking_occupancy": 0.45, "parking_days": 2,
        "bar_uplift_per_weekend": 425,
        "incremental_cost": 720,
    },
    "tier4_trackday": {
        "name": "Track Day / Car Club / Bike Night",
        "parking_price": 0, "parking_occupancy": 0.10, "parking_days": 1,
        "bar_uplift_per_weekend": 265,
        "incremental_cost": 180,
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
# full LOC balance stays drawn; see run_loc_payoff_schedule for the more
# realistic declining-balance view as free cash flow pays it down).
# No cleaning/maintenance labor line: the park manager lives on-site rent-free
# in exchange for running the park (cleaning, upkeep, day-to-day ops), so
# that labor cost is a housing trade, not a cash expense. The bartender is
# comped via a 5% revenue share (variable cost - see VARIABLE_COST_RATE),
# not a salary, and is the only bartender at all times, including events.
# waste_service, wifi_internet, and pos_tech_subscriptions are actual
# recurring vendor costs from the owner's Phase 0.5 tracker (porta-potty +
# dumpster, StarLink, Clover POS respectively) - not estimates. water_bill/
# electric_bill/septic have no vendor number yet (Notion shows them as real
# but unpriced) so they're estimates pending an actual bill; "Merch" is
# excluded entirely (no longer planned, no spend).
FIXED_COSTS = {
    "insurance": 900,                # GL + liquor liability (beer/shots only) + park liability (estimate)
    "water_bill": 150,               # estimate pending first bill
    "electric_bill": 350,            # estimate pending first bill (common-area: lights, TVs, misters, bar coolers)
    "septic": 100,                   # estimate - drainage beyond the rented porta-potty unit
    "marketing": 750,                # $500 marketing person + $150/mo ad spend
    "waste_service": 388,            # actual: porta-potty $268 (TX Disposal Systems) + dumpster $120
    "wifi_internet": 165,            # actual: StarLink
    "pos_tech_subscriptions": 120,   # actual: Clover POS
    "licenses_permits": 300,         # TABC beer/liquor retailer + health permit renewals (estimate)
    "maintenance_reserve": 400,      # supplies/materials only, not labor (estimate)
    "property_tax": 4_000,           # actual: owner-reported monthly property tax bill
    "loc_interest": LOC_MONTHLY_INTEREST,  # 12.5% interest-only on the LOC draw
}
MONTHLY_NUT = sum(FIXED_COSTS.values())
ANNUAL_NUT = MONTHLY_NUT * 12

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

def resolve_truck_count(year_month, max_slots):
    """
    Trucks active in a given operating month. The 4 built hubs are already
    running, so max_slots <= TRUCK_SLOTS (4) needs no ramp - all requested
    slots are active from month 1. max_slots > TRUCK_SLOTS means exploring
    a hypothetical future expansion (more hubs than are currently built);
    those extra slots phase in gradually (construction time), reaching
    max_slots by month 7 and holding.
    """
    if max_slots <= TRUCK_SLOTS:
        return max_slots
    if year_month >= 7:
        return max_slots
    extra_slots = max_slots - TRUCK_SLOTS
    added = round(extra_slots * year_month / 7)
    return min(max_slots, TRUCK_SLOTS + added)


def calc_truck_revenue(month, year_month=None, slots=None, pad_rent=None,
                       share_rate=None, avg_sales=None, occupancy=None):
    """
    Food truck income: pad rent + revenue share.
    Rent is not seasonal (monthly agreements); the revenue-share portion
    follows bar-traffic seasonality since truck sales track park foot traffic.
    `occupancy` (0-1) is an expected-value haircut for vendor vacancy/churn -
    applied to both rent and revenue share, since an empty slot earns neither.
    """
    max_slots = slots if slots is not None else TRUCK_SLOTS
    rent = pad_rent if pad_rent is not None else TRUCK_PAD_RENT
    share = share_rate if share_rate is not None else TRUCK_REV_SHARE_RATE
    sales = avg_sales if avg_sales is not None else TRUCK_AVG_MONTHLY_SALES
    occ = occupancy if occupancy is not None else TRUCK_OCCUPANCY

    if year_month is not None:
        slots_active = resolve_truck_count(year_month, max_slots)
    else:
        slots_active = max_slots

    # Expected occupied trucks after vacancy haircut (may be fractional).
    trucks = slots_active * occ
    season = SEASONALITY.get(month, 0.85)
    rent_income = trucks * rent
    share_income = trucks * sales * share * season
    gross = rent_income + share_income
    return {"gross": gross, "net": gross * TRUCK_MARGIN, "trucks": trucks,
            "slots_active": slots_active, "occupancy": occ,
            "rent_income": rent_income, "share_income": share_income}


def calc_bar_revenue(weekday_customers, weekend_customers, month,
                     year_month=None, avg_check=None):
    """Limited bar (beer + shots) monthly revenue with seasonality + Year 1
    ramp. Weekday (Mon-Thu) and weekend (Fri-Sun) traffic are weighted by
    their average day-counts per month (see WEEKDAY_DAYS_PER_MONTH /
    WEEKEND_DAYS_PER_MONTH) rather than one flat daily average."""
    check = avg_check if avg_check is not None else BAR_AVG_CHECK
    season = SEASONALITY.get(month, 0.85)
    ramp = BAR_Y1_RAMP.get(year_month, 1.0) if year_month else 1.0
    monthly_customers = (weekday_customers * WEEKDAY_DAYS_PER_MONTH
                         + weekend_customers * WEEKEND_DAYS_PER_MONTH)
    return monthly_customers * check * season * ramp


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


def calc_monthly_total(weekday_customers, weekend_customers, month, year_month=None,
                       avg_check=None, cota_events=None,
                       truck_slots=None, truck_rent=None,
                       truck_share_rate=None, truck_avg_sales=None,
                       truck_occupancy=None, seasonal_pct=1.0):
    """
    Full monthly calculation across all streams:
      1. Food truck rent+share  3. COTA events (parking + bar uplift)
      2. Limited bar             4. Seasonal watch parties
                                  5. Utility pass-through (net zero)
    Returns detailed breakdown dict.
    """
    trucks = calc_truck_revenue(month, year_month, truck_slots, truck_rent,
                                truck_share_rate, truck_avg_sales, truck_occupancy)
    bar_rev = calc_bar_revenue(weekday_customers, weekend_customers, month,
                               year_month, avg_check)
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

    bar_net = bar_like * (1 - VARIABLE_COST_RATE) - bartender_share - cc_processing - shrinkage
    parking_net = cota["parking"] * 0.95

    total_net_before_fixed = (bar_net + trucks["net"] + parking_net
                              + utilities["net"] - cota["incremental_cost"])
    noi = total_net_before_fixed - MONTHLY_NUT

    # "Nut Coverage Ratio" plays the role DSCR played when there was a loan:
    # how many times over does operating income before fixed overhead cover
    # the fixed monthly nut?
    nut_coverage = total_net_before_fixed / MONTHLY_NUT if MONTHLY_NUT > 0 else 0

    return {
        "month": month,
        "truck_rent": trucks["rent_income"],
        "truck_share": trucks["share_income"],
        "truck_gross": trucks["gross"],
        "trucks_active": trucks["slots_active"],      # slots available (capacity)
        "trucks_occupied": trucks["trucks"],          # expected occupied after vacancy
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
        "fixed_costs": MONTHLY_NUT,
        "total_net_before_fixed": total_net_before_fixed,
        "noi": noi,
        "monthly_nut_coverage": nut_coverage,
        "net_cash_flow": noi,
    }


# =============================================================================
# SECTION 3: ANNUAL AND MULTI-YEAR PROJECTIONS
# =============================================================================

def run_annual_projection(weekday_customers=None, weekend_customers=None, year=1,
                          avg_check=None, cota_events_override=None,
                          truck_slots=None, truck_rent=None,
                          truck_share_rate=None, truck_avg_sales=None,
                          truck_occupancy=None, seasonal_pct=1.0):
    """
    Full 12-month projection. Returns (months_list, annual_dict).
    Year 1 applies the truck and bar ramps; Year 2+ is steady state.

    `m` below is the OPERATING month index (1 = first month of operation,
    i.e. OPENING_MONTH) - it drives the Year 1 ramps. Seasonality, the COTA
    calendar, and seasonal one-off events all key off the actual CALENDAR
    month (`cal_month`), which wraps around the year via OPENING_MONTH so
    Year 1 doesn't incorrectly assume a January start.
    """
    wd_custs = weekday_customers if weekday_customers is not None else BAR_WEEKDAY_CUSTOMERS
    we_custs = weekend_customers if weekend_customers is not None else BAR_WEEKEND_CUSTOMERS
    months = []
    for m in range(1, 13):
        year_month = m if year == 1 else None
        cal_month = operating_to_calendar_month(m)
        if cota_events_override is not None:
            events = cota_events_override.get(cal_month, COTA_EVENTS_BY_MONTH.get(cal_month, []))
        else:
            events = None
        result = calc_monthly_total(
            wd_custs, we_custs, cal_month, year_month, avg_check, events,
            truck_slots, truck_rent, truck_share_rate, truck_avg_sales,
            truck_occupancy, seasonal_pct,
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
        "total_noi": sum(m["noi"] for m in months),
        "total_net_cash": sum(m["net_cash_flow"] for m in months),
        "avg_monthly_nut_coverage": sum(m["monthly_nut_coverage"] for m in months) / 12,
        "min_monthly_nut_coverage": min(m["monthly_nut_coverage"] for m in months),
        "max_monthly_nut_coverage": max(m["monthly_nut_coverage"] for m in months),
        "annual_nut": ANNUAL_NUT,
        "fcf_yield": sum(m["noi"] for m in months) / TOTAL_PROJECT_COST,
    }


def run_multi_year_projection(base_weekday_customers=None, base_weekend_customers=None,
                              years=3, base_check=None,
                              truck_slots=None, truck_rent=None,
                              truck_share_rate=None, truck_avg_sales=None,
                              truck_occupancy=None, seasonal_pct=1.0):
    """
    Year 1 with ramps; Year 2+ steady state with growth and cost inflation.
    Returns list of (year, months, annual) tuples.
    """
    wd_custs0 = base_weekday_customers if base_weekday_customers is not None else BAR_WEEKDAY_CUSTOMERS
    we_custs0 = base_weekend_customers if base_weekend_customers is not None else BAR_WEEKEND_CUSTOMERS
    check0 = base_check if base_check is not None else BAR_AVG_CHECK
    trent0 = truck_rent if truck_rent is not None else TRUCK_PAD_RENT
    tsales0 = truck_avg_sales if truck_avg_sales is not None else TRUCK_AVG_MONTHLY_SALES

    all_years = []
    for yr in range(1, years + 1):
        growth = (1 + ANNUAL_GROWTH_RATE) ** (yr - 1)
        rent_growth = (1 + ANNUAL_RENT_GROWTH) ** (yr - 1)
        cost_mult = (1 + ANNUAL_COST_INFLATION) ** (yr - 1)

        months, annual = run_annual_projection(
            int(wd_custs0 * growth), int(we_custs0 * growth), year=yr,
            avg_check=check0 * growth,
            truck_slots=truck_slots, truck_rent=trent0 * rent_growth,
            truck_share_rate=truck_share_rate,
            truck_avg_sales=tsales0 * growth,
            truck_occupancy=truck_occupancy,
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
                    base_weekday_customers=None, base_weekend_customers=None,
                    base_check=None, base_truck_rent=None, base_truck_share=None,
                    base_truck_occupancy=None, base_seasonal_pct=1.0):
    """
    Randomized Year 1 scenarios. Varies: truck sales, truck occupancy
    (vacancy), weekday/weekend bar traffic and check, COTA event mix, and
    seasonal event strength. Truck count, rent, and revenue share are held
    FIXED across every simulation (actual fleet + contracted terms, not
    uncertain) - but still adjustable via the base_* args so sidebar sliders
    keep working. Returns list of result dicts (revenue, noi, nut_coverage,
    cash_flow).
    """
    _wd_custs = base_weekday_customers if base_weekday_customers is not None else BAR_WEEKDAY_CUSTOMERS
    _we_custs = base_weekend_customers if base_weekend_customers is not None else BAR_WEEKEND_CUSTOMERS
    _check = base_check if base_check is not None else BAR_AVG_CHECK
    _trent = base_truck_rent if base_truck_rent is not None else TRUCK_PAD_RENT
    _tshare = base_truck_share if base_truck_share is not None else TRUCK_REV_SHARE_RATE
    _tocc = base_truck_occupancy if base_truck_occupancy is not None else TRUCK_OCCUPANCY

    random.seed(seed)
    results = []

    for _ in range(n_simulations):
        wd_custs = max(5, min(50, random.gauss(_wd_custs, 5)))
        we_custs = max(15, min(100, random.gauss(_we_custs, 12)))
        check = max(5.0, min(13.0, random.gauss(_check, 1.0)))
        truck_sales = max(10_000, min(35_000, random.gauss(TRUCK_AVG_MONTHLY_SALES, 5_000)))
        # Truck vacancy is the real fleet risk (6-mo contracts bound it):
        # randomize occupancy rather than the integer slot count.
        truck_occ = max(0.60, min(1.0, random.gauss(_tocc, 0.08)))
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
            int(wd_custs), int(we_custs), year=1, avg_check=check,
            cota_events_override=override,
            truck_rent=_trent, truck_share_rate=_tshare,
            truck_avg_sales=truck_sales, truck_occupancy=truck_occ,
            seasonal_pct=seasonal_pct,
        )

        results.append({
            "revenue": ann["total_gross"],
            "noi": ann["total_noi"],
            "nut_coverage": sum(m["monthly_nut_coverage"] for m in months) / 12,
            "cash_flow": ann["total_net_cash"],
            "bar_custs_weekday": wd_custs,
            "bar_custs_weekend": we_custs,
            "truck_occupancy": truck_occ,
        })

    results.sort(key=lambda x: x["nut_coverage"])
    return results


# =============================================================================
# SECTION 5: SCENARIOS
# =============================================================================

# Truck count is held at the actual current fleet (4, TRUCK_SLOTS) in every
# scenario except "Upside," which explores a hypothetical future expansion
# to 6 hubs (not currently budgeted). Rent/share are also fixed at the
# actual contracted terms ($500 + 10%) throughout. Only bar traffic/check,
# COTA turnout, and seasonal strength vary across the other four scenarios.
SCENARIOS = {
    "Worst Case": {
        "desc": "4 trucks (current fleet), 75% occ, weak bar, no COTA",
        "weekday_customers": 12, "weekend_customers": 34, "avg_check": 7.45,
        "truck_slots": TRUCK_SLOTS, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 0.75,
        "cota_events": {m: [] for m in range(1, 13)},
        "seasonal_pct": 0.5,
    },
    "Stress Test": {
        "desc": "4 trucks (current fleet), 83% occ, soft bar, big-3 COTA events only",
        "weekday_customers": 15, "weekend_customers": 43, "avg_check": 8.05,
        "truck_slots": TRUCK_SLOTS, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 0.83,
        "cota_events": {m: [] for m in range(1, 13)},  # filled below
        "seasonal_pct": 0.75,
    },
    "Conservative": {
        "desc": "4 trucks (current fleet), 88% occ, full COTA calendar",
        "weekday_customers": 17, "weekend_customers": 48, "avg_check": 8.55,
        "truck_slots": TRUCK_SLOTS, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 0.88,
        "cota_events": None,
        "seasonal_pct": 0.75,
    },
    "Base Case": {
        "desc": "4 trucks (current fleet) at $500 + 10%, 90% occ, 20 weekday / 58 weekend bar customers",
        "weekday_customers": BAR_WEEKDAY_CUSTOMERS, "weekend_customers": BAR_WEEKEND_CUSTOMERS, "avg_check": 9.00,
        "truck_slots": TRUCK_SLOTS, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": TRUCK_OCCUPANCY,
        "cota_events": None,
        "seasonal_pct": 1.0,
    },
    "Upside": {
        "desc": "6 trucks (hypothetical future expansion, not currently budgeted), full occ, strong evening bar",
        "weekday_customers": 28, "weekend_customers": 82, "avg_check": 9.95,
        "truck_slots": 6, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 1.0,
        "cota_events": None,
        "seasonal_pct": 1.25,
    },
}
_stress_cota = {3: ["tier2_nascar"], 4: ["tier2_motogp"], 10: ["tier1_f1"]}
SCENARIOS["Stress Test"]["cota_events"].update(_stress_cota)


def run_scenario_projection(params):
    """Run an annual projection from a SCENARIOS params dict."""
    return run_annual_projection(
        params["weekday_customers"], params["weekend_customers"],
        avg_check=params["avg_check"],
        cota_events_override=params["cota_events"],
        truck_slots=params["truck_slots"], truck_rent=params["truck_rent"],
        truck_share_rate=params["truck_share_rate"],
        truck_occupancy=params.get("truck_occupancy"),
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
        ("Truck Occupancy", lambda n: f"{SCENARIOS[n]['truck_occupancy']:>15.0%}"),
        ("Bar Custs (Wkday/Wkend)", lambda n: f"{str(SCENARIOS[n]['weekday_customers'])+'/'+str(SCENARIOS[n]['weekend_customers']):>16}"),
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
        0, 0, avg_check=0,
        cota_events_override={m: [] for m in range(1, 13)},
        seasonal_pct=0.0,
    )

    # View 2: minimum bar traffic for nut-coverage targets (weak truck base:
    # 4 trucks @ $600 + 5%, no COTA). Searches a single multiplier applied to
    # both weekday and weekend traffic together, holding their ratio fixed
    # at the "weak" Worst Case split (12 weekday / 34 weekend).
    weak_weekday, weak_weekend = 12, 34
    targets = [("Break-even", 1.0), ("Comfortable", 1.25),
               ("Strong", 1.50), ("Excellent", 2.0)]
    custs_results = []
    for label, target in targets:
        lo, hi = 0.0, 4.0
        for _ in range(25):
            mid = (lo + hi) / 2
            _, ann = run_annual_projection(
                weak_weekday * mid, weak_weekend * mid, avg_check=7.45,
                truck_slots=4, truck_rent=600, truck_share_rate=0.05,
                cota_events_override={m: [] for m in range(1, 13)},
                seasonal_pct=0.0,
            )
            if ann["avg_monthly_nut_coverage"] >= target:
                hi = mid
            else:
                lo = mid
        custs_results.append((label, target, round(weak_weekday * hi), round(weak_weekend * hi)))

    if verbose:
        print(f"\n{'=' * 70}")
        print("  BREAK-EVEN ANALYSIS")
        print(f"{'=' * 70}")
        print(f"\n  Monthly Nut (all fixed operating costs): ${MONTHLY_NUT:>10,.0f}")
        print(f"  (Includes ${LOC_MONTHLY_INTEREST:,.0f}/mo LOC interest-only carrying cost)")
        print(f"\n  1. ZERO-BAR TEST (4 trucks, no bar, no COTA):")
        print(f"     Annual NOI:  ${no_bar['total_noi']:>12,.0f}")
        print(f"     Nut Coverage: {no_bar['avg_monthly_nut_coverage']:>11.2f}x")
        verdict = "COVERS THE NUT" if no_bar["avg_monthly_nut_coverage"] >= 1.0 else "DOES NOT COVER"
        print(f"     -> Truck rent alone {verdict}")
        print(f"\n  2. MIN BAR TRAFFIC BY NUT-COVERAGE TARGET")
        print(f"     (weak base: 4 trucks @ $600 + 5%, $7.45 check, no COTA)")
        for label, target, wd, we in custs_results:
            print(f"     {label:<14} ({target:.2f}x): {wd:>4} weekday / {we:>4} weekend bar customers")

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
    print(f"  {'Weekday/Weekend':>16} {'Annual Rev':>14} {'NOI':>12} {'Nut Cov':>9} {'Cash Flow':>12}")
    print("  " + "-" * 68)
    for mult in [0.33, 0.6, 0.83, 1.0, 1.25, 1.5, 1.83]:
        wd, we = round(BAR_WEEKDAY_CUSTOMERS * mult), round(BAR_WEEKEND_CUSTOMERS * mult)
        _, ann = run_annual_projection(wd, we)
        print(f"  {wd:>7}/{we:<7} ${ann['total_gross']:>13,.0f} ${ann['total_noi']:>11,.0f} "
              f"{ann['avg_monthly_nut_coverage']:>8.2f}x ${ann['total_net_cash']:>11,.0f}")

    print(f"\n  4. Truck Occupancy Impact (vacancy/churn, base trucks + bar)")
    print(f"  {'Occupancy':>12} {'Annual Rev':>14} {'NOI':>12} {'Nut Cov':>9} {'Cash Flow':>12}")
    print("  " + "-" * 62)
    for occ in [0.60, 0.70, 0.80, 0.90, 1.0]:
        _, ann = run_annual_projection(truck_occupancy=occ)
        print(f"  {occ:>11.0%} ${ann['total_gross']:>13,.0f} ${ann['total_noi']:>11,.0f} "
              f"{ann['avg_monthly_nut_coverage']:>8.2f}x ${ann['total_net_cash']:>11,.0f}")

    print(f"\n  5. COTA Decline Stress Test (base case)")
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
    min_balance_month = (1, OPENING_MONTH)  # placeholder: opening balance, before month 1
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
              f"(Year {min_balance_month[0]}, {MONTH_NAMES[min_balance_month[1]]})")
        print(f"  Months with negative CF: {months_negative}")
        if payback_month:
            print(f"  ${TOTAL_PROJECT_COST:,.0f} total capital deployed recouped "
                  f"(cumulative NOI) by: Year {payback_month[0]}, {MONTH_NAMES[payback_month[1]]}")
        else:
            print(f"  Capital deployed NOT recouped within the projection window.")

    return {"min_balance": min_balance, "min_month": min_balance_month,
            "months_negative": months_negative,
            "break_even_month": break_even_month,
            "payback_month": payback_month, "series": series}


def run_loc_payoff_schedule(all_years=None, sweep_pct=1.0, verbose=True):
    """
    Simulate the LOC balance actually shrinking over time, rather than the
    conservative "full balance always drawn" assumption baked into
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
                  f"to principal): Year {payoff_month[0]}, {MONTH_NAMES[payoff_month[1]]}")
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
    for label, amt, status in USE_OF_FUNDS:
        print(f"  {label:<52} ${amt:>10,.0f}  [{status}]")
    print(f"  {'TOTAL':<52} ${TOTAL_PROJECT_COST:>10,.0f}")

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
    print(f"  - Utilities sub-metered and billed at cost (no margin leakage)")
    print(f"  - COTA event upside preserved: parking + bar uplift")


# =============================================================================
# SECTION 8: CLI MENU
# =============================================================================

def print_annual_summary(months, annual, label=""):
    """Pretty-print a full annual projection."""
    month_names = MONTH_NAMES
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
                                 "BASE CASE: 4 trucks, 20 weekday / 58 weekend bar customers")
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
