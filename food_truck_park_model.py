#!/usr/bin/env python3
"""
Food Truck Park + Bar & Beverage Stand | Del Valle
Interactive Financial Model (leanest concept on the same land as The Cube /
the food-truck-+-RV-park alternative)

Concept:
  - Food truck park (pad rent $500-$1,000 + 5-10% revenue share)
  - Bar & beverage stand: evening bar with prepackaged canned/bottled beer +
    liquor shots in sealed plastic shot glasses only (NO mixed drinks, no
    cocktails, no RV park), plus an all-day non-alcohol window selling
    soda/juice/water/coffee and tobacco/nicotine (cigarettes/vapes/Zyn)
  - Power/water/waste/wifi for the truck hubs, sub-metered and billed at cost
    (Texas PUC utility-resale rules: PURA Sec. 39.107 - resale at cost, no
    markup)

Startup cost: ~$76K, drawn entirely from a personal line of credit (LOC) at
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
  - Food truck park + bar & beverage stand + large TVs = on-site entertainment
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
# The permits line was raised from the tracker's $1,500 placeholder to
# $7,000 after checking real TABC pricing: a Mixed Beverage Permit (MB) -
# required to sell liquor shots by the drink - is $5,300 for the first two
# years alone (TABC two-year fee schedule, in force since Sept 2021), on top
# of the health permit, business license, and the TX Comptroller tobacco
# ($180/2yr) + e-cigarette ($90/2yr with a tobacco permit) retailer permits.
# A new MB permittee may also have to post a conduct surety bond and a tax
# security bond; only the annual premium would be an operating cost, and it
# is NOT modeled - confirm bonding requirements with TABC.
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
    ("Permits & soft costs (TABC MB permit, health, tobacco, business license)", 7_000, "not_started"),
    ("Contingency", 6_300, "not_started"),
]
TOTAL_PROJECT_COST = sum(a for _, a, _ in USE_OF_FUNDS)  # $81,600
ALREADY_SPENT = sum(a for _, a, status in USE_OF_FUNDS if status == "done")  # $39,181
NEW_CASH_NEEDED = TOTAL_PROJECT_COST - ALREADY_SPENT                          # $42,419

# --- Capital (financed via personal line of credit, not a bank term loan) ---
LOC_AMOUNT = TOTAL_PROJECT_COST  # fully drawn to fund the buildout
LOC_INTEREST_RATE = 0.125        # revolving LOC rate (interest-only, no fixed term)
LOC_MONTHLY_INTEREST = round(LOC_AMOUNT * LOC_INTEREST_RATE / 12)  # assumes full balance stays drawn (conservative)

# --- Land / Site ---
LAND_ACRES = 4.5
LAND_PURCHASE_PRICE = 1_400_000  # what the owner actually paid (owned outright, not financed here)
LAND_ASSESSED_VALUE = 300_000    # county tax assessment - basis for the ~$4K/yr property tax bill
LAND_VALUE = LAND_PURCHASE_PRICE  # kept for reference; not used in any calculation
# The existing $4,000/yr bill taxes RAW LAND only. Once the buildout is
# finished, Travis County adds the improvements (gravel lot, electrical,
# plumbing, structures, shade, lighting) to the tax roll and the bill goes
# up - a real recurring cost the model previously ignored. Conservatively
# assume the FULL project cost becomes assessed value (some line items -
# inventory, contingency, permits - arguably aren't taxable real property,
# so this overstates rather than understates) at a 2.0% effective rate.
# 2.0% is above the ~1.33% the owner's own land bill implies ($4,000 on a
# $300K assessment) and above the ~1.54% Travis County median, chosen
# deliberately on the "conservative = higher expense" rule.
PROPERTY_TAX_IMPROVEMENT_RATE = 0.020
PROPERTY_TAX_IMPROVEMENTS_MONTHLY = round(
    TOTAL_PROJECT_COST * PROPERTY_TAX_IMPROVEMENT_RATE / 12)
# Dedicated 3-acre lot within the property, laid out for COTA event parking.
# Owner estimate: fits 240-300 cars -> using the midpoint.
EVENT_PARKING_SPACES = 270       # spaces available for COTA event parking
# Typical carpool occupancy for a motorsport/event day crowd - used to turn
# parked cars into an attendee count for the daytime-beverage COTA uplift
# below (a car full of people buys more drinks than the car itself).
PEOPLE_PER_CAR = 2.5
# Lot upkeep on event-parking revenue: trash/debris cleanup, striping wear,
# gravel replenishment from the added traffic - distinct from the flat
# per-tier `incremental_cost` (staffing/porta-potty), which doesn't scale
# with parking volume.
PARKING_UPKEEP_RATE = 0.05
# Motor vehicle parking is an explicitly TAXABLE SERVICE in Texas (34 TAC
# 3.315) at the full combined Del Valle/Travis County rate. Event lots
# charge a round cash price at the gate ($80 a spot, not $80 + tax), so the
# tax comes out of that price rather than being added on top - the same
# tax-inclusive logic used for the bar. This was missing entirely before;
# on a full COTA calendar it is a real five-figure annual cost.
PARKING_SALES_TAX_RATE = 0.0825

# --- Food Truck Park ---
# 4 utility hubs are being BUILT (the park is still under construction as of
# this model version - it is not yet open and has no operating history).
# Owner plans to run with these 4 for at least a year; building more hubs
# costs additional capital that isn't budgeted. TRUCK_SLOTS stays adjustable
# (via the slider/scenarios) for exploring a future expansion.
#
# IMPORTANT: no vendor contracts are signed yet. Six operators have
# expressed interest, which is encouraging but is not the same as a signed
# 6-month lease, so the model does NOT assume a full lot on day one - see
# TRUCK_Y1_FILL_RAMP below.
TRUCK_SLOTS = 4                  # utility-hub slots being built
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
# Expected fraction of built slots actually rented at any given time, once
# the lot has reached its steady state. Vendors sign 6-month contracts,
# which bounds churn, but a vendor leaving at term leaves a slot empty for a
# re-leasing gap. 1.0 = always full / waitlist; lower = more vacancy.
# Applied as an expected-value haircut on BOTH pad rent and revenue share.
# Held at 0.85 rather than 0.90 because there is no leasing track record yet
# to justify the tighter number (see TRUCK_Y1_FILL_RAMP) - re-tighten once
# real renewal behavior is observed.
TRUCK_OCCUPANCY = 0.85
# Year 1 lease-up curve for the built slots, as a fraction of TRUCK_SLOTS.
# With zero signed contracts at model time, assuming a full lot in month 1
# would be the single least defensible assumption in the model. Six
# interested operators plausibly converts to about half the lot at open,
# filling over the first two to three quarters as the park proves it draws
# traffic. Multiplied by TRUCK_OCCUPANCY on top, so month 1 is ~1.7
# effective trucks out of 4 built - deliberately pessimistic.
# Months 9+ = 1.0 (fully leased, subject only to the occupancy haircut).
TRUCK_Y1_FILL_RAMP = {
    1: 0.50, 2: 0.50, 3: 0.60, 4: 0.70, 5: 0.75, 6: 0.80, 7: 0.85, 8: 0.95,
}

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

# --- Evening Bar (prepackaged beer + liquor shots ONLY) ---
# Evening-only operation (6pm-10:30/11pm, ~4.5 hrs/day). No mixed drinks, no
# pre-packaged cocktails - just canned/bottled beer and liquor poured/sealed
# into single-serve plastic shot glasses. Simpler than a full container bar:
# no bartender skill/speed requirement, no cocktail markup, minimal equipment
# (coolers + a shot-pour/seal station).
# The ALCOHOL side of the bar (beer + shots) stays evening-only for TABC/
# demand reasons; the all-day extension is the non-alcoholic beverage
# window (soda/juice/water/coffee - see DAYTIME_BEVERAGE_* below), so the
# alcohol traffic assumptions (BAR_WEEKDAY/WEEKEND_CUSTOMERS) are unchanged.
BAR_HOURS_PER_DAY = 4.5           # alcohol service window: 6pm-10:30pm average
DAYTIME_BEVERAGE_HOURS_PER_DAY = 11.0  # all-day non-alcoholic window (~11am-close)
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
# --- Alcohol taxes: TWO separate Texas taxes, both apply ---
# Selling liquor "by the drink" (shots poured/sealed on premises) requires a
# TABC Mixed Beverage Permit (MB). Under an MB permit, EVERY alcoholic
# beverage sold - including canned/bottled beer - falls under BOTH mixed
# beverage taxes, not standard sales tax:
#   1. Mixed Beverage Gross Receipts Tax, 6.7%. Statutorily the permittee's
#      own liability; it may NOT be added to the menu price as a separate
#      line or backed out of the amount received. Always a true cost.
#   2. Mixed Beverage SALES Tax, 8.25%. Legally collected FROM the customer,
#      so a bar that adds it on top of a posted price passes it through at
#      zero cost. But bars overwhelmingly post tax-INCLUSIVE prices (a "$7
#      beer" means the customer hands over $7), which makes the 8.25% come
#      out of that $7 instead. This model assumes tax-inclusive pricing -
#      the conservative read, and the one matching how BEER_PRICE/SHOT_PRICE
#      are described above. If the bar instead posts prices pre-tax and adds
#      8.25% at the register, set MB_SALES_TAX_RATE = 0.0 and revenue is
#      unaffected.
# Both were previously missing #2, which understated alcohol variable cost
# by 8.25 points. Confirm the permit type and pricing convention with a
# TABC-savvy CPA.
GRT_RATE = 0.067                 # TX Mixed Beverage Gross Receipts Tax (permittee's own liability)
MB_SALES_TAX_RATE = 0.0825       # TX Mixed Beverage Sales Tax (assumed tax-inclusive pricing)
VARIABLE_COST_RATE = COGS_RATE + GRT_RATE + MB_SALES_TAX_RATE  # ~50.5% on alcohol revenue
CC_PROCESSING_RATE = 0.028
CC_CARD_USAGE_RATE = 0.85
SHRINKAGE_RATE = 0.025           # of beverage COGS value (grab-and-go single-serve
                                  # items may be easier to pilfer than pours - watch this)
BARTENDER_SHARE_RATE = 0.05      # bartender's variable-cost comp: 5% of bar-like revenue
# Employer-side payroll burden on the bartender's comp. She works set hours
# on the owner's premises under the owner's direction, so she is very likely
# a W-2 EMPLOYEE rather than a 1099 contractor - which means the business
# owes employer FICA (7.65%) plus federal and Texas unemployment insurance
# on top of whatever she's paid. Revenue-share comp does not avoid this.
# ~10% is a deliberately conservative blended estimate (FICA 7.65% + TX SUTA
# new-employer rate + FUTA, the latter two capped at low wage bases so the
# true blended figure lands a bit under 10%). Confirm classification with a
# CPA - misclassification penalties are steep.
# NOTE: the free on-site housing given to the manager and bartender is NOT
# modeled as taxable wages here. IRC Sec. 119 excludes lodging furnished for
# the employer's convenience on the business premises as a condition of
# employment, which plausibly fits live-on-site caretakers - but it is a
# fact-specific test and a CPA should confirm before relying on it.
EMPLOYER_PAYROLL_BURDEN_RATE = 0.10

# --- All-Day Beverages (soda, juice, water, coffee) ---
# Extends the bar's operating window from evening-only (BAR_HOURS_PER_DAY)
# to all-day. Staffed by the same on-site bartender - no new fixed labor
# line, since she lives on-site (like the park manager), so the "two
# people, no fixed labor cost" staffing model holds even with longer hours.
# Vendor leases restrict food trucks to food only from Day 1 (no truck
# contracts had been signed as of this addition, so there's no phase-in
# needed) - specialty drinks (a truck's own signature agua fresca,
# lemonade, etc.) are still allowed, but generic soda/juice/water/coffee
# sales are reserved for the bar. Without that restriction, this revenue
# would leak back to truck-sold drinks instead of the park's bar.
DAYTIME_BEVERAGE_ITEMS = ["Soda", "Juice", "Water", "Coffee"]
DAYTIME_BEVERAGE_AVG_PRICE = 2.75    # blended price across the 4 items
# Packaged soft drinks/water/coffee carry a much thinner unit cost than
# alcohol (no excise-inflated wholesale price) - ~20-25% COGS is typical
# for grab-and-go canned/bottled drinks and drip coffee.
DAYTIME_BEVERAGE_COGS_RATE = 0.22
# NOT the alcohol Mixed Beverage GRT (GRT_RATE) - these aren't alcoholic,
# so standard TX sales tax applies instead. Verify with a CPA (some to-go
# food/drink categories carry exemptions).
DAYTIME_BEVERAGE_SALES_TAX_RATE = 0.0825
DAYTIME_BEVERAGE_VARIABLE_COST_RATE = DAYTIME_BEVERAGE_COGS_RATE + DAYTIME_BEVERAGE_SALES_TAX_RATE
# Fraction of food-truck customers who also buy a drink from the bar while
# at the park - a grab-and-go beverage attach rate alongside a food-truck
# meal, similar in spirit to a movie-theater concession attach rate.
# Assumed moderate since some customers bring their own drinks.
DAYTIME_BEVERAGE_ATTACH_RATE = 0.35
# Typical food-truck ticket size, used ONLY to convert truck gross sales
# into an implied daytime customer count for this calc (not a pricing
# lever elsewhere) - trucks are the park's only real daytime foot-traffic
# driver, so this ties the new stream to that same traffic axis rather
# than inventing an independent daytime headcount.
AVG_TRUCK_TICKET = 14.00

# --- Tobacco & Nicotine (cigarettes, vapes, nicotine pouches/Zyn) ---
# All-day, same window and same on-site bartender as the beverage stand -
# she already cards for alcohol, so age verification (21+, federal Tobacco
# 21) adds no new labor. Sized off the same implied truck-traffic customer
# count as daytime beverages (see AVG_TRUCK_TICKET above), since food
# trucks are still the only real foot-traffic driver.
#
# COMPETITIVE CONTEXT: Dollar General next door (~30 sec walk) already
# sells cigarettes, which directly undercuts the "one-stop-shop" pitch for
# that specific product - a customer isn't walking to the park just for a
# pack of Marlboros when DG is closer. A smoke shop across the busy road
# (~1-2 min incl. a road crossing) is real competition too, but the extra
# friction makes it less of a threat than DG for quick impulse buys. Vapes
# and nicotine pouches are less consistently stocked at Dollar General, so
# the park's edge is real there, just not for cigarettes specifically. The
# attach rate below is set low to reflect this - it is NOT a beverage-level
# "everyone's thirsty" assumption, more like "some fraction of truck
# customers happen to want a nicotine product and grab it here instead of
# walking somewhere else."
TOBACCO_ITEMS = ["Cigarettes", "Vapes", "Nicotine Pouches (Zyn)"]
TOBACCO_AVG_PRICE = 12.00        # blended: ~$9 pack of cigs, ~$20 vape, ~$6 Zyn can
# Cigarette retail margin is notoriously thin (~15-18%, most of the
# shelf price is wholesale cost + built-in excise tax); vapes/Zyn run much
# better (~40-50%). Blended COGS assumes a mix weighted toward cigs+vape
# (~40/35/25 cigs/vape/Zyn) - materially worse margin than any beverage
# stream in this model, which is realistic for this product category.
TOBACCO_COGS_RATE = 0.68
# Standard TX sales tax (same as daytime beverages) - cigarette excise tax
# is already baked into wholesale cost via distributor stamps, not remitted
# separately by the retailer. Verify with a CPA/TX Comptroller.
TOBACCO_SALES_TAX_RATE = 0.0825
TOBACCO_VARIABLE_COST_RATE = TOBACCO_COGS_RATE + TOBACCO_SALES_TAX_RATE
# Deliberately much lower than DAYTIME_BEVERAGE_ATTACH_RATE (35%) - nicotine
# use is a smaller slice of the population than "wants a drink," and
# Dollar General's proximity caps the upside specifically on cigarettes
# (the biggest line in the product mix). Adjust via the dashboard slider if
# real sales data suggests otherwise once operating.
TOBACCO_ATTACH_RATE = 0.12
# TX Comptroller Cigarette/Tobacco Products Retailer Permit + separate
# E-Cigarette Retailer Permit (different regulatory track from the TABC
# alcohol permit already in FIXED_COSTS) - ESTIMATE, confirm actual fee
# with the Comptroller before budgeting.
TOBACCO_PERMIT_MONTHLY = 15

# Year 1 ramp for every customer-facing revenue stream that has to be
# DISCOVERED: the evening bar, daytime beverages, and tobacco/nicotine.
# (Truck lease-up is separate - see TRUCK_Y1_FILL_RAMP.)
#
# An earlier version of this model used a faster curve on the theory that
# the park had already soft-opened and had traffic to convert. That is not
# the case: the park is still under construction with no operating history,
# so this is a genuine cold start. Word-of-mouth in a semi-rural location
# takes time, so the curve now starts lower (35% vs 50%) and reaches full
# run-rate at month 10 rather than month 8.
BAR_Y1_RAMP = {
    1: 0.35, 2: 0.45, 3: 0.55, 4: 0.65, 5: 0.72, 6: 0.80,
    7: 0.86, 8: 0.92, 9: 0.96,
}  # months 10+ = 1.0

# --- Seasonality (outdoor venue, Austin climate) ---
# Spring/fall patio weather peaks, winter cold + deep-summer heat dips.
SEASONALITY = {
    1: 0.65, 2: 0.70, 3: 0.90, 4: 1.00, 5: 1.00, 6: 0.90,
    7: 0.85, 8: 0.85, 9: 0.95, 10: 1.00, 11: 0.90, 12: 0.70,
}

# --- Background sports-calendar density (the big TVs, everyday games) ---
# Distinct from SEASONAL_EVENTS below, which models three specific
# destination watch parties (Super Bowl, March Madness, NYE). This dict
# captures the quieter, always-on effect: a bar with large TVs draws a
# somewhat different evening crowd in a month packed with watchable games
# than in a dead month, even with no marquee event on the calendar.
#
# Shape is taken from the owner's sports-schedule research, which analyzed
# ~16,500 annual events across every major league:
#   - OCTOBER is the variety peak (the "Sports Equinox" - the only time the
#     Big 4 North American leagues all overlap with European soccer,
#     NASCAR, F1, and major esports). Highest multiplier.
#   - APRIL is the raw-volume peak (MLB fully active daily, NBA/NHL final
#     regular-season stretch, European league run-ins).
#   - FEBRUARY is the quietest month despite hosting the Super Bowl (MLB and
#     MLS inactive, NFL plays exactly one game). The Super Bowl spike itself
#     is already counted separately in SEASONAL_EVENTS, so this multiplier
#     reflects the empty rest of the month.
#   - JUNE-AUGUST is the "summer gap" - NBA, NFL, NHL, and European soccer
#     all dark, with only MLB, MLS, esports, F1, and NASCAR carrying the
#     calendar. July is the thinnest.
#
# Deliberately kept as a NARROW band (0.92-1.06) that averages to ~1.00, so
# it redistributes evening bar traffic across the year rather than handing
# the model a free revenue increase - consistent with the rule that
# uncertain revenue assumptions should not be optimistic. Applied to the
# evening bar only: the TVs are what make a sports-heavy month matter, and
# daytime beverage/tobacco sales ride on food-truck lunch traffic that has
# little to do with what's on screen.
SPORTS_DENSITY = {
    1: 1.03,   # NFL playoffs, NBA + NHL midseason, college hoops
    2: 0.94,   # PDF's quietest month (Super Bowl handled in SEASONAL_EVENTS)
    3: 1.03,   # MLB opens, NASCAR ramps, NBA/NHL push (Madness counted separately)
    4: 1.05,   # PDF's highest-volume month
    5: 1.02,   # NBA/NHL playoffs + MLB daily + European finals
    6: 0.96,   # summer gap begins - MLB and MLS carry it
    7: 0.92,   # thinnest month of the year
    8: 0.94,   # still thin; NFL preseason only
    9: 1.04,   # NFL returns, MLB pennant race, college football
    10: 1.06,  # "Sports Equinox" - PDF's variety peak
    11: 1.02,  # NFL/NBA/NHL/college football all live
    12: 1.01,  # NFL stretch run, bowl season, NBA Christmas
}

# --- Seasonal one-off events (watch parties on the big TVs) ---
# Bar opens EARLY / stays open full-day for these, so volume assumptions
# hold from the original (larger) model - only the check size is rescaled
# for the beer/shots-only offering: ratio = new BAR_AVG_CHECK ($9.00) /
# old mixed-drink check ($18.00) = 0.50
#
# YEAR 1 CALENDAR CHECK (operating year Sep 2026 - Aug 2027), comparing the
# owner's sports-schedule research against what actually falls in the window:
#   - Super Bowl LXI: Sun Feb 14, 2027 (SoFi Stadium). IN WINDOW - modeled.
#   - March Madness 2027: Mar-Apr 2027. IN WINDOW - modeled.
#   - NYE: Dec 31, 2026. IN WINDOW - modeled.
#   - FIFA World Cup 2026: ran Jun 11 - Jul 19, 2026 and is already OVER
#     before this park opens. The research deck annualizes ~250 World Cup
#     matches per year, but Year 1 gets NONE of them. No watch-party line
#     is modeled for it, correctly.
#   - Olympics: Milan-Cortina Winter was Feb 2026 (past); LA28 Summer is
#     Jul 2028. NEITHER falls in Year 1, so the deck's ~500 annualized
#     Olympic events also do not apply here.
# Net: Year 1 is a comparatively quiet year for global mega-events, which
# is another reason SPORTS_DENSITY above is kept neutral rather than
# additive. Revisit for Year 3 (LA28 Summer Olympics + 2027 Rugby/Cricket
# World Cups would all land in a later operating year).
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
# Multi-day weekends build up rather than selling out flat every day - e.g.
# F1 Friday is a practice-only day with a fraction of Sunday race-day
# traffic. "daily_occupancy" is one fraction per event day (Fri, Sat, Sun,
# ...); the last entry is the peak/marquee day and matches what the tier
# used to model as a single flat occupancy. ESTIMATE - validate against a
# real event's actual day-by-day sell-through once you have one on record.
COTA_EVENT_TIERS = {
    "tier1_f1": {
        "name": "F1 US Grand Prix",
        "parking_price": 80, "daily_occupancy": [0.45, 0.75, 1.00],  # Fri practice / Sat quali / Sun race
        "bar_uplift_per_weekend": 10_165,
        "incremental_cost": 10_800,
    },
    "tier2_motogp": {
        "name": "MotoGP Grand Prix of the Americas",
        "parking_price": 55, "daily_occupancy": [0.40, 0.70, 0.93],  # Fri practice / Sat quali / Sun race
        "bar_uplift_per_weekend": 4_545,
        "incremental_cost": 6_300,
    },
    "tier2_nascar": {
        "name": "NASCAR Cup Series (EchoPark Grand Prix)",
        "parking_price": 50, "daily_occupancy": [0.55, 0.80],  # Sat support races / Sun race
        "bar_uplift_per_weekend": 2_545,
        "incremental_cost": 4_500,
    },
    "tier3_wec": {
        "name": "WEC 6 Hours of COTA",
        "parking_price": 35, "daily_occupancy": [0.45, 0.70],
        "bar_uplift_per_weekend": 1_520,
        "incremental_cost": 2_160,
    },
    "tier3_gt_transam": {
        "name": "GT World Challenge / TransAm / Other Races",
        "parking_price": 25, "daily_occupancy": [0.25, 0.35],
        "bar_uplift_per_weekend": 775,
        "incremental_cost": 900,
    },
    "tier3_concert": {
        "name": "Major Concert (Germania Amphitheater)",
        "parking_price": 30, "daily_occupancy": [0.55],
        "bar_uplift_per_weekend": 510,
        "incremental_cost": 720,
    },
    "tier3_festival": {
        "name": "Festival (FoodieLand, etc.)",
        "parking_price": 30, "daily_occupancy": [0.35, 0.45],
        "bar_uplift_per_weekend": 425,
        "incremental_cost": 720,
    },
    "tier4_trackday": {
        "name": "Track Day / Car Club / Bike Night",
        "parking_price": 0, "daily_occupancy": [0.10],
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
# that labor cost is a housing trade, not a cash expense. The bartender also
# lives on-site (same housing-trade logic) and is comped via a revenue share
# (BARTENDER_SHARE_RATE, variable cost - see VARIABLE_COST_RATE), not a
# salary - the only bartender at all times, including events, now covering
# both the evening alcohol bar AND the all-day non-alcohol beverage window
# (see DAYTIME_BEVERAGE_* below) since living on-site makes the longer day
# feasible without a second hire.
# waste_service, wifi_internet, and pos_tech_subscriptions are actual
# recurring vendor costs from the owner's Phase 0.5 tracker (porta-potty +
# dumpster, StarLink, Clover POS respectively) - not estimates. water_bill/
# electric_bill/septic have no vendor number yet (Notion shows them as real
# but unpriced) so they're estimates pending an actual bill; "Merch" is
# excluded entirely (no longer planned, no spend).
#
# `accounting_tax_prep` is a compliance cost this model previously omitted.
# An MB permittee files MONTHLY mixed beverage GRT and mixed beverage sales
# tax returns, plus sales tax on parking/beverages/tobacco, plus payroll
# filings, plus the annual federal return and the Texas franchise-tax Public
# Information Report. That is a real bookkeeper/CPA engagement, not
# something to leave at $0.
#
# TEXAS FRANCHISE TAX: not a line item because none is owed. The 2026
# no-tax-due threshold is $2.65M of annualized total revenue and this
# business projects well under $1M, so franchise tax due is $0 - but the
# entity must still file a Public Information Report or face a $50 penalty
# and loss of good standing. That filing is covered by accounting_tax_prep.
FIXED_COSTS = {
    "insurance": 900,                # GL + liquor liability (beer/shots only) + park liability (estimate)
    "water_bill": 150,               # estimate pending first bill
    "electric_bill": 350,            # estimate pending first bill (common-area: lights, TVs, misters, bar coolers)
    "septic": 100,                   # estimate - drainage beyond the rented porta-potty unit
    "marketing": 750,                # $500 marketing person + $150/mo ad spend
    "waste_service": 388,            # actual: porta-potty $268 (TX Disposal Systems) + dumpster $120
    "wifi_internet": 165,            # actual: StarLink
    "pos_tech_subscriptions": 120,   # actual: Clover POS
    "licenses_permits": 300,         # TABC MB permit renewal ($2,650/2yr = $110/mo) + health permit + business license
    "tobacco_permit": TOBACCO_PERMIT_MONTHLY,  # TX Comptroller cigarette/tobacco + e-cig retailer permits
    "maintenance_reserve": 400,      # supplies/materials only, not labor (estimate)
    "property_tax": 333,             # actual: $4,000/yr bill / 12 (county assesses LAND at $300K, not the $1.4M purchase price)
    "property_tax_improvements": PROPERTY_TAX_IMPROVEMENTS_MONTHLY,  # buildout gets added to the tax roll once complete
    "accounting_tax_prep": 250,      # bookkeeping + monthly TX tax filings + annual returns (see note above)
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

# --- Income Tax ---
# Texas has no state income tax, but the park's profit is still federal
# taxable income to the owner (pass-through: self-employment + federal
# income tax). 28% is a blended effective-rate ESTIMATE for profit in the
# $150K-$250K range - the real rate depends on entity structure, other
# household income, and deductions (Section 179 on the buildout, LOC
# interest, etc.). Confirm with a CPA. Applied to positive annual NOI only;
# pre-tax figures remain the primary operating metrics.
EFFECTIVE_INCOME_TAX_RATE = 0.28

# --- Market context ---
LOCAL_HOUSEHOLDS = 8_754
ANNUAL_COTA_VISITORS = 700_000   # 1.5M total visitors/year, 700K event-attending portion
ANNUAL_COTA_VISITOR_SPENDING = 50  # avg spend per visitor at bar/parking


# =============================================================================
# SECTION 2: REVENUE MODEL FUNCTIONS
# =============================================================================

def resolve_truck_count(year_month, max_slots):
    """
    Trucks leased in a given Year 1 operating month.

    Two separate effects, both pointing the same direction:
      1. LEASE-UP. No vendor contracts are signed yet, so the lot does not
         open full. TRUCK_Y1_FILL_RAMP fills it from ~half to fully leased
         over the first two to three quarters.
      2. BUILD-OUT of hypothetical extra hubs. max_slots > TRUCK_SLOTS means
         exploring an expansion beyond the 4 budgeted hubs; those extra
         slots also need construction time, phasing in by month 7.

    Returns a possibly-fractional slot count (the lease-up curve is an
    expected value, not an integer headcount). Year 2+ passes
    year_month=None and gets max_slots with no ramp.
    """
    if year_month is None:
        return max_slots

    built = min(max_slots, TRUCK_SLOTS)
    if max_slots > TRUCK_SLOTS:
        extra_slots = max_slots - TRUCK_SLOTS
        added = extra_slots if year_month >= 7 else round(extra_slots * year_month / 7)
        built = min(max_slots, TRUCK_SLOTS + added)

    fill = TRUCK_Y1_FILL_RAMP.get(year_month, 1.0)
    return built * fill


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

    slots_active = resolve_truck_count(year_month, max_slots)

    # Expected occupied trucks after vacancy haircut (may be fractional).
    trucks = slots_active * occ
    season = SEASONALITY.get(month, 0.85)
    rent_income = trucks * rent
    share_income = trucks * sales * share * season
    gross = rent_income + share_income
    # Total customer $ spent AT the trucks (not the park's rent/share cut) -
    # used by calc_daytime_beverage_revenue as the traffic proxy for daytime
    # foot traffic, since food trucks are the park's only real daytime draw.
    truck_total_sales = trucks * sales * season
    return {"gross": gross, "net": gross * TRUCK_MARGIN, "trucks": trucks,
            "slots_active": slots_active, "occupancy": occ,
            "rent_income": rent_income, "share_income": share_income,
            "truck_total_sales": truck_total_sales}


def calc_bar_revenue(weekday_customers, weekend_customers, month,
                     year_month=None, avg_check=None, sports_density=True):
    """Evening bar (beer + shots) monthly revenue with seasonality, sports
    density, and the Year 1 ramp. Weekday (Mon-Thu) and weekend (Fri-Sun)
    traffic are weighted by their average day-counts per month (see
    WEEKDAY_DAYS_PER_MONTH / WEEKEND_DAYS_PER_MONTH) rather than one flat
    daily average.

    Three independent monthly multipliers stack here:
      - SEASONALITY: Austin patio weather (the big one, 0.65-1.00)
      - SPORTS_DENSITY: how much watchable sport is on the TVs (0.92-1.06,
        averages to ~1.00 so it redistributes rather than inflates)
      - BAR_Y1_RAMP: cold-start discovery curve, Year 1 only
    Pass sports_density=False to isolate the weather-only view.
    """
    check = avg_check if avg_check is not None else BAR_AVG_CHECK
    season = SEASONALITY.get(month, 0.85)
    sports = SPORTS_DENSITY.get(month, 1.0) if sports_density else 1.0
    ramp = BAR_Y1_RAMP.get(year_month, 1.0) if year_month else 1.0
    monthly_customers = (weekday_customers * WEEKDAY_DAYS_PER_MONTH
                         + weekend_customers * WEEKEND_DAYS_PER_MONTH)
    return monthly_customers * check * season * sports * ramp


def calc_daytime_beverage_revenue(truck_total_sales, year_month=None,
                                  attach_rate=None, avg_price=None):
    """
    All-day soda/juice/water/coffee sales, sized off implied food-truck
    customer traffic (truck_total_sales / AVG_TRUCK_TICKET) rather than an
    independent daytime headcount - food trucks are the park's only real
    daytime foot-traffic driver, so this ties the new stream to the same
    traffic axis instead of inventing a separate one. Ramps up in Year 1
    like the bar itself, since it's a new offering customers need to
    discover. Requires vendor leases restricting trucks to food-only (see
    DAYTIME_BEVERAGE_* notes in Section 1) or this demand leaks to
    truck-sold drinks instead.
    """
    rate = attach_rate if attach_rate is not None else DAYTIME_BEVERAGE_ATTACH_RATE
    price = avg_price if avg_price is not None else DAYTIME_BEVERAGE_AVG_PRICE
    ramp = BAR_Y1_RAMP.get(year_month, 1.0) if year_month else 1.0

    implied_customers = truck_total_sales / AVG_TRUCK_TICKET
    return implied_customers * rate * price * ramp


def calc_tobacco_revenue(truck_total_sales, year_month=None,
                         attach_rate=None, avg_price=None):
    """
    All-day cigarette/vape/nicotine-pouch sales, same truck-traffic-derived
    customer count as calc_daytime_beverage_revenue (trucks are the park's
    only real foot-traffic driver), but with its own much lower attach rate
    and thinner margin - see TOBACCO_* notes in Section 1 for why (Dollar
    General next door already sells cigarettes, capping the "one-stop-shop"
    upside for that specific product). Ramps up in Year 1 like the bar,
    since it's a new offering.
    """
    rate = attach_rate if attach_rate is not None else TOBACCO_ATTACH_RATE
    price = avg_price if avg_price is not None else TOBACCO_AVG_PRICE
    ramp = BAR_Y1_RAMP.get(year_month, 1.0) if year_month else 1.0

    implied_customers = truck_total_sales / AVG_TRUCK_TICKET
    return implied_customers * rate * price * ramp


def calc_seasonal_event_revenue(month, year_month=None, seasonal_pct=1.0):
    """Watch-party spikes (Super Bowl, March Madness, NYE) at the bar."""
    ramp = BAR_Y1_RAMP.get(year_month, 1.0) if year_month else 1.0
    total = 0
    for event in SEASONAL_EVENTS.values():
        if event["month"] == month:
            total += event["rev_base"] * seasonal_pct
    return total * ramp


def calc_cota_event_revenue(event_list, parking_spaces=None,
                            daytime_beverage_attach_rate=None,
                            daytime_beverage_avg_price=None,
                            tobacco_attach_rate=None,
                            tobacco_avg_price=None):
    """
    COTA event weekends: paid parking + bar uplift + daytime-beverage
    uplift + tobacco/nicotine uplift. Parking and both product uplifts are
    summed day-by-day using each tier's daily_occupancy curve (lighter
    early days, peak on the marquee day) rather than one flat rate x days.
    Both uplifts are derived directly from that same parking attendance
    (cars x PEOPLE_PER_CAR x attach rate x avg price) rather than separate
    hardcoded per-tier numbers - a packed event-day parking lot obviously
    sells more water/soda/coffee/cigarettes than a normal day, and this
    ties that directly to the crowd size the model already computes for
    parking.
    event_list: list of tier keys, e.g. ["tier1_f1", "tier3_concert"].
    """
    spaces = parking_spaces if parking_spaces is not None else EVENT_PARKING_SPACES
    bev_rate = (daytime_beverage_attach_rate if daytime_beverage_attach_rate is not None
                else DAYTIME_BEVERAGE_ATTACH_RATE)
    bev_price = (daytime_beverage_avg_price if daytime_beverage_avg_price is not None
                 else DAYTIME_BEVERAGE_AVG_PRICE)
    tobacco_rate = (tobacco_attach_rate if tobacco_attach_rate is not None
                    else TOBACCO_ATTACH_RATE)
    tobacco_price = (tobacco_avg_price if tobacco_avg_price is not None
                     else TOBACCO_AVG_PRICE)
    if not event_list:
        return {"parking": 0, "bar_uplift": 0, "daytime_bev_uplift": 0,
                "tobacco_uplift": 0, "gross": 0, "incremental_cost": 0, "net": 0}

    total_parking = 0
    total_bar = 0
    total_daytime_bev = 0
    total_tobacco = 0
    total_cost = 0
    for tier_key in event_list:
        tier = COTA_EVENT_TIERS.get(tier_key, COTA_EVENT_TIERS["tier3_gt_transam"])
        for day_occupancy in tier["daily_occupancy"]:
            cars = int(spaces * day_occupancy)
            total_parking += cars * tier["parking_price"]
            attendees = cars * PEOPLE_PER_CAR
            total_daytime_bev += attendees * bev_rate * bev_price
            total_tobacco += attendees * tobacco_rate * tobacco_price
        total_bar += tier["bar_uplift_per_weekend"]
        total_cost += tier["incremental_cost"]

    gross = total_parking + total_bar + total_daytime_bev + total_tobacco
    return {"parking": total_parking, "bar_uplift": total_bar,
            "daytime_bev_uplift": total_daytime_bev,
            "tobacco_uplift": total_tobacco, "gross": gross,
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
                       truck_occupancy=None, seasonal_pct=1.0,
                       daytime_beverage_attach_rate=None,
                       daytime_beverage_avg_price=None,
                       tobacco_attach_rate=None,
                       tobacco_avg_price=None):
    """
    Full monthly calculation across all streams:
      1. Food truck rent+share  5. Utility pass-through (net zero)
      2. Evening bar             6. All-day beverages (soda/juice/water/coffee)
      3. COTA events            7. Tobacco & nicotine (cigarettes/vapes/Zyn)
      4. Seasonal watch parties
    Returns detailed breakdown dict.
    """
    trucks = calc_truck_revenue(month, year_month, truck_slots, truck_rent,
                                truck_share_rate, truck_avg_sales, truck_occupancy)
    bar_rev = calc_bar_revenue(weekday_customers, weekend_customers, month,
                               year_month, avg_check)
    seasonal_rev = calc_seasonal_event_revenue(month, year_month, seasonal_pct)
    daytime_bev_rev = calc_daytime_beverage_revenue(
        trucks["truck_total_sales"], year_month,
        daytime_beverage_attach_rate, daytime_beverage_avg_price)
    tobacco_rev = calc_tobacco_revenue(
        trucks["truck_total_sales"], year_month,
        tobacco_attach_rate, tobacco_avg_price)

    if cota_events is not None:
        event_list = cota_events
    else:
        event_list = COTA_EVENTS_BY_MONTH.get(month, [])
    cota = calc_cota_event_revenue(
        event_list, daytime_beverage_attach_rate=daytime_beverage_attach_rate,
        daytime_beverage_avg_price=daytime_beverage_avg_price,
        tobacco_attach_rate=tobacco_attach_rate,
        tobacco_avg_price=tobacco_avg_price)

    utilities = calc_utility_passthrough(trucks["trucks"])

    total_gross = (trucks["gross"] + bar_rev + seasonal_rev
                   + cota["gross"] + utilities["billed"] + daytime_bev_rev
                   + tobacco_rev)

    # Variable costs apply to bar-like (alcohol), daytime beverage
    # (non-alcohol), and tobacco/nicotine revenue SEPARATELY - each has a
    # different tax treatment and COGS rate. Each bucket folds in its own
    # COTA uplift (bar_uplift / daytime_bev_uplift / tobacco_uplift) for
    # cost-rate purposes, same as bar_like always has.
    bar_like = bar_rev + cota["bar_uplift"] + seasonal_rev
    daytime_bev_like = daytime_bev_rev + cota["daytime_bev_uplift"]
    tobacco_like = tobacco_rev + cota["tobacco_uplift"]
    cogs = bar_like * COGS_RATE
    grt = bar_like * GRT_RATE
    mb_sales_tax = bar_like * MB_SALES_TAX_RATE
    daytime_bev_cogs = daytime_bev_like * DAYTIME_BEVERAGE_COGS_RATE
    daytime_bev_tax = daytime_bev_like * DAYTIME_BEVERAGE_SALES_TAX_RATE
    tobacco_cogs = tobacco_like * TOBACCO_COGS_RATE
    tobacco_tax = tobacco_like * TOBACCO_SALES_TAX_RATE
    bar_variable_costs = cogs + grt + mb_sales_tax
    daytime_bev_variable_costs = daytime_bev_cogs + daytime_bev_tax
    tobacco_variable_costs = tobacco_cogs + tobacco_tax
    all_bev_rev = bar_like + daytime_bev_like + tobacco_like

    bartender_share = all_bev_rev * BARTENDER_SHARE_RATE
    payroll_burden = bartender_share * EMPLOYER_PAYROLL_BURDEN_RATE
    cc_processing = all_bev_rev * CC_PROCESSING_RATE * CC_CARD_USAGE_RATE
    shrinkage = (bar_like * COGS_RATE * SHRINKAGE_RATE
                 + daytime_bev_like * DAYTIME_BEVERAGE_COGS_RATE * SHRINKAGE_RATE
                 + tobacco_like * TOBACCO_COGS_RATE * SHRINKAGE_RATE)

    gross_margin = (bar_like * (1 - VARIABLE_COST_RATE)
                     + daytime_bev_like * (1 - DAYTIME_BEVERAGE_VARIABLE_COST_RATE)
                     + tobacco_like * (1 - TOBACCO_VARIABLE_COST_RATE))
    bev_net = (gross_margin - bartender_share - payroll_burden
               - cc_processing - shrinkage)
    parking_upkeep = cota["parking"] * PARKING_UPKEEP_RATE
    parking_sales_tax = cota["parking"] * PARKING_SALES_TAX_RATE
    parking_net = cota["parking"] - parking_upkeep - parking_sales_tax

    total_net_before_fixed = (bev_net + trucks["net"] + parking_net
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
        "daytime_beverage_revenue": daytime_bev_rev,
        "daytime_beverage_variable_costs": daytime_bev_variable_costs,
        "daytime_beverage_cogs": daytime_bev_cogs,
        "daytime_beverage_tax": daytime_bev_tax,
        "tobacco_revenue": tobacco_rev,
        "tobacco_variable_costs": tobacco_variable_costs,
        "tobacco_cogs": tobacco_cogs,
        "tobacco_tax": tobacco_tax,
        "seasonal_revenue": seasonal_rev,
        "cota_parking": cota["parking"],
        "cota_bar_uplift": cota["bar_uplift"],
        "cota_daytime_bev_uplift": cota["daytime_bev_uplift"],
        "cota_tobacco_uplift": cota["tobacco_uplift"],
        "cota_parking_upkeep": parking_upkeep,
        "cota_parking_sales_tax": parking_sales_tax,
        "cota_incremental_cost": cota["incremental_cost"],
        "utility_billed": utilities["billed"],
        "utility_cost": utilities["cost"],
        "total_gross_revenue": total_gross,
        "bar_variable_costs": bar_variable_costs,
        "cogs": cogs,
        "grt": grt,
        "mb_sales_tax": mb_sales_tax,
        "bartender_share": bartender_share,
        "payroll_burden": payroll_burden,
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
                          truck_occupancy=None, seasonal_pct=1.0,
                          daytime_beverage_attach_rate=None,
                          daytime_beverage_avg_price=None,
                          tobacco_attach_rate=None,
                          tobacco_avg_price=None):
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
            daytime_beverage_attach_rate, daytime_beverage_avg_price,
            tobacco_attach_rate, tobacco_avg_price,
        )
        months.append(result)

    annual = summarize_annual(months)
    return months, annual


def summarize_annual(months):
    """Build the annual summary dict from 12 monthly results.
    Includes after-tax views: income_tax applies EFFECTIVE_INCOME_TAX_RATE
    to positive annual NOI (pass-through federal tax; TX has no state income
    tax). Pre-tax NOI remains the primary operating metric."""
    total_noi = sum(m["noi"] for m in months)
    income_tax = max(0.0, total_noi) * EFFECTIVE_INCOME_TAX_RATE
    after_tax_noi = total_noi - income_tax
    return {
        "total_gross": sum(m["total_gross_revenue"] for m in months),
        "total_trucks": sum(m["truck_gross"] for m in months),
        "total_truck_rent": sum(m["truck_rent"] for m in months),
        "total_truck_share": sum(m["truck_share"] for m in months),
        "total_bar": sum(m["bar_revenue"] for m in months),
        "total_daytime_beverage": sum(m["daytime_beverage_revenue"] for m in months),
        "total_tobacco": sum(m["tobacco_revenue"] for m in months),
        "total_seasonal": sum(m["seasonal_revenue"] for m in months),
        "total_cota_parking": sum(m["cota_parking"] for m in months),
        "total_cota_bar": sum(m["cota_bar_uplift"] for m in months),
        "total_cota_daytime_bev": sum(m["cota_daytime_bev_uplift"] for m in months),
        "total_cota_tobacco": sum(m["cota_tobacco_uplift"] for m in months),
        "total_cota_parking_upkeep": sum(m["cota_parking_upkeep"] for m in months),
        "total_cota_parking_sales_tax": sum(m["cota_parking_sales_tax"] for m in months),
        "total_cota_cost": sum(m["cota_incremental_cost"] for m in months),
        "total_utility_billed": sum(m["utility_billed"] for m in months),
        "total_utility_cost": sum(m["utility_cost"] for m in months),
        "total_bartender_share": sum(m["bartender_share"] for m in months),
        "total_payroll_burden": sum(m["payroll_burden"] for m in months),
        "total_cc_processing": sum(m["cc_processing"] for m in months),
        "total_shrinkage": sum(m["shrinkage"] for m in months),
        "total_cogs": sum(m["cogs"] for m in months),
        "total_grt": sum(m["grt"] for m in months),
        "total_mb_sales_tax": sum(m["mb_sales_tax"] for m in months),
        "total_daytime_beverage_cogs": sum(m["daytime_beverage_cogs"] for m in months),
        "total_daytime_beverage_tax": sum(m["daytime_beverage_tax"] for m in months),
        "total_tobacco_cogs": sum(m["tobacco_cogs"] for m in months),
        "total_tobacco_tax": sum(m["tobacco_tax"] for m in months),
        "total_noi": total_noi,
        "total_net_cash": sum(m["net_cash_flow"] for m in months),
        "income_tax": income_tax,
        "after_tax_noi": after_tax_noi,
        "after_tax_fcf_yield": after_tax_noi / TOTAL_PROJECT_COST,
        "avg_monthly_nut_coverage": sum(m["monthly_nut_coverage"] for m in months) / 12,
        "min_monthly_nut_coverage": min(m["monthly_nut_coverage"] for m in months),
        "max_monthly_nut_coverage": max(m["monthly_nut_coverage"] for m in months),
        "annual_nut": ANNUAL_NUT,
        "fcf_yield": total_noi / TOTAL_PROJECT_COST,
    }


def run_multi_year_projection(base_weekday_customers=None, base_weekend_customers=None,
                              years=3, base_check=None,
                              truck_slots=None, truck_rent=None,
                              truck_share_rate=None, truck_avg_sales=None,
                              truck_occupancy=None, seasonal_pct=1.0,
                              daytime_beverage_attach_rate=None,
                              daytime_beverage_avg_price=None,
                              tobacco_attach_rate=None,
                              tobacco_avg_price=None):
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
            daytime_beverage_attach_rate=daytime_beverage_attach_rate,
            daytime_beverage_avg_price=daytime_beverage_avg_price,
            tobacco_attach_rate=tobacco_attach_rate,
            tobacco_avg_price=tobacco_avg_price,
        )

        if yr > 1:
            inflation_penalty = ANNUAL_NUT * (cost_mult - 1)
            annual["total_noi"] -= inflation_penalty
            annual["total_net_cash"] -= inflation_penalty
            annual["cost_inflation_adj"] = inflation_penalty
            annual["fcf_yield"] = annual["total_noi"] / TOTAL_PROJECT_COST
            # Recompute after-tax figures on the inflation-adjusted NOI
            annual["income_tax"] = max(0.0, annual["total_noi"]) * EFFECTIVE_INCOME_TAX_RATE
            annual["after_tax_noi"] = annual["total_noi"] - annual["income_tax"]
            annual["after_tax_fcf_yield"] = annual["after_tax_noi"] / TOTAL_PROJECT_COST
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
                    base_truck_occupancy=None, base_seasonal_pct=1.0,
                    base_truck_slots=None, base_truck_avg_sales=None,
                    base_daytime_beverage_attach_rate=None,
                    base_daytime_beverage_avg_price=None,
                    base_tobacco_attach_rate=None,
                    base_tobacco_avg_price=None):
    """
    Randomized Year 1 scenarios. Varies: truck sales, truck occupancy
    (vacancy), weekday/weekend bar traffic and check, COTA event mix,
    seasonal event strength, and the daytime-beverage / tobacco attach
    rates. Truck COUNT, rent, and revenue share are held FIXED across every
    simulation (built slots + contracted terms, not uncertain) - lease-up
    risk is expressed through occupancy instead.

    Every base_* argument mirrors a dashboard slider so the simulation
    tracks whatever the user has dialed in; passing none of them reproduces
    the module defaults. Returns a list of per-simulation result dicts
    sorted by nut coverage.
    """
    _wd_custs = base_weekday_customers if base_weekday_customers is not None else BAR_WEEKDAY_CUSTOMERS
    _we_custs = base_weekend_customers if base_weekend_customers is not None else BAR_WEEKEND_CUSTOMERS
    _check = base_check if base_check is not None else BAR_AVG_CHECK
    _trent = base_truck_rent if base_truck_rent is not None else TRUCK_PAD_RENT
    _tshare = base_truck_share if base_truck_share is not None else TRUCK_REV_SHARE_RATE
    _tocc = base_truck_occupancy if base_truck_occupancy is not None else TRUCK_OCCUPANCY
    _tslots = base_truck_slots if base_truck_slots is not None else TRUCK_SLOTS
    _tsales = base_truck_avg_sales if base_truck_avg_sales is not None else TRUCK_AVG_MONTHLY_SALES
    _dbev_attach = (base_daytime_beverage_attach_rate
                    if base_daytime_beverage_attach_rate is not None
                    else DAYTIME_BEVERAGE_ATTACH_RATE)
    _dbev_price = (base_daytime_beverage_avg_price
                   if base_daytime_beverage_avg_price is not None
                   else DAYTIME_BEVERAGE_AVG_PRICE)
    _tob_attach = (base_tobacco_attach_rate if base_tobacco_attach_rate is not None
                   else TOBACCO_ATTACH_RATE)
    _tob_price = (base_tobacco_avg_price if base_tobacco_avg_price is not None
                  else TOBACCO_AVG_PRICE)

    random.seed(seed)
    results = []

    for _ in range(n_simulations):
        wd_custs = max(5, min(50, random.gauss(_wd_custs, 5)))
        we_custs = max(15, min(100, random.gauss(_we_custs, 12)))
        check = max(5.0, min(13.0, random.gauss(_check, 1.0)))
        truck_sales = max(10_000, min(35_000, random.gauss(_tsales, 5_000)))
        # Truck vacancy is the real fleet risk (6-mo contracts bound it):
        # randomize occupancy rather than the integer slot count.
        truck_occ = max(0.60, min(1.0, random.gauss(_tocc, 0.08)))
        seasonal_pct = max(0.4, min(1.5, random.gauss(base_seasonal_pct, 0.2)))
        # The two attach rates are the least-validated numbers in the whole
        # model (no operating history, and Dollar General competes directly
        # on cigarettes), so they get wide bands rather than being pinned.
        dbev_attach = max(0.10, min(0.60, random.gauss(_dbev_attach, 0.08)))
        tob_attach = max(0.02, min(0.30, random.gauss(_tob_attach, 0.04)))

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
            truck_slots=_tslots,
            truck_rent=_trent, truck_share_rate=_tshare,
            truck_avg_sales=truck_sales, truck_occupancy=truck_occ,
            seasonal_pct=seasonal_pct,
            daytime_beverage_attach_rate=dbev_attach,
            daytime_beverage_avg_price=_dbev_price,
            tobacco_attach_rate=tob_attach,
            tobacco_avg_price=_tob_price,
        )

        results.append({
            "revenue": ann["total_gross"],
            "noi": ann["total_noi"],
            "nut_coverage": sum(m["monthly_nut_coverage"] for m in months) / 12,
            "cash_flow": ann["total_net_cash"],
            "bar_custs_weekday": wd_custs,
            "bar_custs_weekend": we_custs,
            "truck_occupancy": truck_occ,
            "daytime_beverage_attach_rate": dbev_attach,
            "tobacco_attach_rate": tob_attach,
        })

    results.sort(key=lambda x: x["nut_coverage"])
    return results


# =============================================================================
# SECTION 5: SCENARIOS
# =============================================================================

# Truck count varies by scenario to reflect vendor attrition risk in the
# downside cases: "Worst Case" assumes only 2 of the 4 built hubs stay
# leased, and "Stress Test"/"Conservative" assume 3 of 4. Only "Base
# Case" holds the full built fleet (4, TRUCK_SLOTS); "Upside" explores a
# hypothetical future expansion to 6 hubs (not currently budgeted). Rent/
# share are fixed at the actual intended terms ($500 + 10%) throughout.
#
# The daytime-beverage and tobacco attach rates ALSO move with the
# scenario. A world where the bar is failing and vendors are churning is
# not a world where the same share of remaining truck customers still buys
# a soda and a pack of cigarettes - holding those rates flat while every
# other lever degrades would quietly make the downside cases too kind.
SCENARIOS = {
    "Worst Case": {
        "desc": "2 trucks (severe vendor attrition), 70% occ, weak bar, no COTA, weak attach rates",
        "weekday_customers": 12, "weekend_customers": 34, "avg_check": 7.45,
        "truck_slots": 2, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 0.70,
        "daytime_beverage_attach_rate": 0.20, "tobacco_attach_rate": 0.06,
        "cota_events": {m: [] for m in range(1, 13)},
        "seasonal_pct": 0.5,
    },
    "Stress Test": {
        "desc": "3 trucks (partial vendor attrition), 78% occ, soft bar, big-3 COTA events only",
        "weekday_customers": 15, "weekend_customers": 43, "avg_check": 8.05,
        "truck_slots": 3, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 0.78,
        "daytime_beverage_attach_rate": 0.25, "tobacco_attach_rate": 0.08,
        "cota_events": {m: [] for m in range(1, 13)},  # filled below
        "seasonal_pct": 0.75,
    },
    "Conservative": {
        "desc": "3 trucks (partial vendor attrition), 83% occ, full COTA calendar",
        "weekday_customers": 17, "weekend_customers": 48, "avg_check": 8.55,
        "truck_slots": 3, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 0.83,
        "daytime_beverage_attach_rate": 0.30, "tobacco_attach_rate": 0.10,
        "cota_events": None,
        "seasonal_pct": 0.75,
    },
    "Base Case": {
        "desc": "4 trucks (all built hubs leased) at $500 + 10%, 85% occ, 20 weekday / 58 weekend bar customers",
        "weekday_customers": BAR_WEEKDAY_CUSTOMERS, "weekend_customers": BAR_WEEKEND_CUSTOMERS, "avg_check": 9.00,
        "truck_slots": TRUCK_SLOTS, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": TRUCK_OCCUPANCY,
        "daytime_beverage_attach_rate": DAYTIME_BEVERAGE_ATTACH_RATE,
        "tobacco_attach_rate": TOBACCO_ATTACH_RATE,
        "cota_events": None,
        "seasonal_pct": 1.0,
    },
    "Upside": {
        "desc": "6 trucks (hypothetical future expansion, not currently budgeted), full occ, strong evening bar",
        "weekday_customers": 28, "weekend_customers": 82, "avg_check": 9.95,
        "truck_slots": 6, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 1.0,
        "daytime_beverage_attach_rate": 0.45, "tobacco_attach_rate": 0.16,
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
        daytime_beverage_attach_rate=params.get("daytime_beverage_attach_rate"),
        tobacco_attach_rate=params.get("tobacco_attach_rate"),
    )


def run_scenario_comparison():
    """Run all five scenarios side by side (prints table, returns results)."""
    print(f"\n{'=' * 86}")
    print("  SCENARIO COMPARISON — FOOD TRUCK PARK + BAR & BEVERAGE STAND")
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
        ("After-Tax NOI", lambda n: f"${scenario_results[n]['after_tax_noi']:>14,.0f}"),
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
    # View 1: no bar at all, base truck slots. daytime_beverage_attach_rate=0
    # and tobacco_attach_rate=0 zero those streams too - they're driven by
    # truck traffic (not weekday/weekend bar customers), so they wouldn't
    # zero out otherwise.
    months, no_bar = run_annual_projection(
        0, 0, avg_check=0,
        cota_events_override={m: [] for m in range(1, 13)},
        seasonal_pct=0.0, daytime_beverage_attach_rate=0.0, tobacco_attach_rate=0.0,
    )

    # View 2: minimum EVENING bar traffic for nut-coverage targets (weak
    # truck base: 4 trucks @ $600 + 5%, no COTA, no daytime beverages -
    # daytime_beverage_attach_rate=0 isolates what the alcohol bar needs to
    # contribute, same as View 1, since that revenue is tied to truck
    # traffic rather than the bar traffic this test is sizing). Searches a
    # single multiplier applied to both weekday and weekend traffic
    # together, holding their ratio fixed at the "weak" Worst Case split
    # (12 weekday / 34 weekend).
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
                seasonal_pct=0.0, daytime_beverage_attach_rate=0.0, tobacco_attach_rate=0.0,
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
        cota_rev = (ann["total_cota_parking"] + ann["total_cota_bar"]
                   + ann["total_cota_daytime_bev"] + ann["total_cota_tobacco"])
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
    """Owner-facing summary for the LOC-financed food truck park + bar & beverage stand concept."""
    print(f"\n{'=' * 70}")
    print("  OWNER SUMMARY")
    print("  Food Truck Park + Bar & Beverage Stand | Del Valle, TX")
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
    print(f"  {'Annual NOI (pre-tax)':<25} ${conservative['total_noi']:>15,.0f} ${base['total_noi']:>15,.0f}")
    print(f"  {'Est. Income Tax (28%)':<25} ${conservative['income_tax']:>15,.0f} ${base['income_tax']:>15,.0f}")
    print(f"  {'After-Tax NOI':<25} ${conservative['after_tax_noi']:>15,.0f} ${base['after_tax_noi']:>15,.0f}")
    print(f"  {'FCF Yield (pre-tax)':<25} {conservative['fcf_yield']:>15.1%} {base['fcf_yield']:>15.1%}")
    print(f"  {'FCF Yield (after-tax)':<25} {conservative['after_tax_fcf_yield']:>15.1%} {base['after_tax_fcf_yield']:>15.1%}")

    print(f"\n  REVENUE STREAMS (Base Case, Year 1)")
    print(f"  {'Food Trucks (rent + share)':<32} ${base['total_trucks']:>14,.0f}")
    print(f"  {'Evening Bar (beer + shots)':<32} ${base['total_bar']:>14,.0f}")
    print(f"  {'All-Day Beverages (soda/juice/water/coffee)':<32} ${base['total_daytime_beverage']:>14,.0f}")
    print(f"  {'Tobacco & Nicotine (cigs/vapes/Zyn)':<32} ${base['total_tobacco']:>14,.0f}")
    print(f"  {'COTA Events (all)':<32} "
          f"${base['total_cota_parking'] + base['total_cota_bar'] + base['total_cota_daytime_bev'] + base['total_cota_tobacco']:>14,.0f}")
    print(f"  {'Seasonal Watch Parties':<32} ${base['total_seasonal']:>14,.0f}")
    print(f"  {'Utility Pass-Through (at cost)':<32} ${base['total_utility_billed']:>14,.0f}")

    print(f"\n  RISK MITIGANTS")
    print(f"  - LOC is revolving/interest-only (no fixed amortization) - free cash "
          f"flow can sweep the ${LOC_AMOUNT:,.0f} balance down faster than the "
          f"conservative flat-interest nut assumes")
    print(f"  - Land owned outright - no rent/mortgage in the nut, and most of "
          f"the buildout ({ALREADY_SPENT/TOTAL_PROJECT_COST:.0%}) is already paid for")
    print(f"  - Simple offering (beer + sealed shots only) = minimal labor skill/speed needs")
    print(f"  - Utilities sub-metered and billed at cost (no margin leakage)")
    print(f"  - COTA event upside preserved: parking + bar uplift")


# =============================================================================
# SECTION 8: TAX STRATEGY ANALYSIS
# =============================================================================
# Two independent, stackable levers an owner can use on top of the flat
# EFFECTIVE_INCOME_TAX_RATE (28%) estimate used everywhere else in this file:
#
#   1. Depreciation - the Phase 0.5 buildout is a real capital asset. Written
#      off over its useful life (or immediately via Section 179 / bonus
#      depreciation), depreciation is a non-cash deduction: it lowers
#      taxable income without reducing actual cash NOI.
#   2. S-corp election - a sole prop / single-member LLC (the default
#      assumed elsewhere in this model) owes self-employment (SE) tax on
#      100% of net profit. Electing S-corp status lets the owner split
#      profit into a "reasonable salary" (subject to payroll tax, the
#      SE-tax equivalent) and distributions (federal income tax only, no
#      SE/payroll tax) - saving 15.3% on the distribution portion.
#
# This section builds a more granular income-tax + SE-tax breakdown than
# the blended 28% shorthand, so the two levers are visible; at the profit
# levels this model projects, FEDERAL_INCOME_TAX_RATE_ONLY + a real SE-tax
# calc lands close to that same ~28% baseline (a rough internal-consistency
# check, not a coincidence). None of this changes the pre-tax NOI reported
# elsewhere - it only estimates incremental tax savings. Illustrative only;
# confirm entity choice, reasonable-compensation level, and depreciation
# elections with a CPA before filing.

# --- Depreciation: classify the real Phase 0.5 buildout into MACRS-style
# classes (IRS Pub 946): 5-year for equipment/electronics/fixtures, 15-year
# for land improvements (fencing, lighting, drainage, grading). Inventory,
# permits, and contingency are excluded - not depreciable capital assets.
DEPRECIATION_5YR_ITEMS = [
    "TVs", "TV Mounts", "TV encasing", "Security system",
    "Sound System / Speakers", "StarLink Internet equipment",
    "Mist Fans (pole-mounted)", "Refrigerators (bar coolers)",
    "Bar shed - Walmart (fridges, shelves, POS)", "Benches",
]
DEPRECIATION_15YR_ITEMS = [
    "Turf", "Sail Shades", "Gates", "Pole Lighting / String Lights",
    "Signs", "Electrical", "Plumbing", "Telephone pole",
    "Full land clearing", "Yard Multi-Purpose Poles (set & anchor)",
    "Gravel", "Trash Cans", "Storage Shed (wooden, general)",
]
_use_of_funds_cost = {label: amt for label, amt, _ in USE_OF_FUNDS}
DEPRECIABLE_BASIS_5YR = sum(_use_of_funds_cost[i] for i in DEPRECIATION_5YR_ITEMS)
DEPRECIABLE_BASIS_15YR = sum(_use_of_funds_cost[i] for i in DEPRECIATION_15YR_ITEMS)
TOTAL_DEPRECIABLE_BASIS = DEPRECIABLE_BASIS_5YR + DEPRECIABLE_BASIS_15YR
NON_DEPRECIABLE_COST = TOTAL_PROJECT_COST - TOTAL_DEPRECIABLE_BASIS  # inventory, permits, contingency

# Straight-line, no half-year convention (a CPA would apply the IRS
# half-year/mid-quarter convention). The "accelerated" alternative below
# front-loads the entire basis into Year 1.
#
# That full-basis write-off is on firm footing as of this model version:
# the One Big Beautiful Bill Act permanently restored **100% bonus
# depreciation** under IRC Sec. 168(k) for qualified property acquired
# after Jan 19, 2025 (IRS Notice 2026-11 gives interim guidance). Bonus is
# no longer phasing down, so a Year 1 buildout can be expensed in full.
#
# Mechanism differs by asset class, which matters if a CPA asks:
#   - 5-year equipment/fixtures qualify for BOTH Section 179 and bonus.
#   - 15-year LAND IMPROVEMENTS (gravel, lighting, fencing, grading) are
#     generally NOT Section 179-eligible, but they ARE bonus-eligible - so
#     100% bonus is what actually gets this portion expensed in Year 1.
# Either way the modeled deduction is the same; the label "Sec 179/Bonus"
# is shorthand for whichever applies to that asset.
ANNUAL_STRAIGHT_LINE_DEPRECIATION = (DEPRECIABLE_BASIS_5YR / 5) + (DEPRECIABLE_BASIS_15YR / 15)
YEAR1_ACCELERATED_DEPRECIATION = TOTAL_DEPRECIABLE_BASIS  # 100% bonus (+ Sec 179 where eligible)

# --- Startup cost amortization (IRC Sec. 195) ---
# Permits, licenses, and pre-opening costs are NOT depreciable property,
# but they aren't lost either: startup and organizational expenditures get
# up to $5,000 deducted immediately in the year the business opens, with
# the remainder amortized straight-line over 15 years. This became worth
# modeling once the permits line was corrected to $7,000 (a TABC Mixed
# Beverage Permit alone is $5,300 for two years).
# Only the genuinely pre-opening portion qualifies - inventory is
# inventory, and contingency is a budgeting buffer rather than a real
# incurred cost, so neither is included here.
STARTUP_COST_ITEMS = [
    "Permits & soft costs (TABC MB permit, health, tobacco, business license)",
    "Cleaning",
]
STARTUP_COST_BASIS = sum(_use_of_funds_cost[i] for i in STARTUP_COST_ITEMS)
STARTUP_IMMEDIATE_DEDUCTION_CAP = 5_000   # IRC Sec. 195(b)(1)(A)
STARTUP_AMORTIZATION_YEARS = 15
_startup_immediate = min(STARTUP_COST_BASIS, STARTUP_IMMEDIATE_DEDUCTION_CAP)
_startup_remainder = max(0.0, STARTUP_COST_BASIS - _startup_immediate)
# Year 1 gets the immediate chunk plus one year of amortization on the rest.
YEAR1_STARTUP_DEDUCTION = _startup_immediate + _startup_remainder / STARTUP_AMORTIZATION_YEARS
ONGOING_STARTUP_AMORTIZATION = _startup_remainder / STARTUP_AMORTIZATION_YEARS

# --- Self-employment tax vs. S-corp salary/distribution split ---
SE_TAXABLE_SHARE = 0.9235        # IRS Sch SE: only 92.35% of net earnings is subject to SE tax
SOCIAL_SECURITY_WAGE_BASE = 184_500  # 2026 SSA wage base - earnings above owe Medicare (2.9%) only
ADDITIONAL_MEDICARE_THRESHOLD = 200_000  # single-filer 0.9% Medicare surtax threshold
ADDITIONAL_MEDICARE_RATE = 0.009
FEDERAL_INCOME_TAX_RATE_ONLY = 0.15  # estimate, excludes SE/payroll tax - see note above
# Illustrative "reasonable compensation" for the S-corp salary split. Set
# lower than a full-time operator's wage because the on-site manager and
# bartender (see staffing section above) handle day-to-day labor; the
# owner's role is closer to part-time oversight. A CPA reasonable-
# compensation study should confirm the final number before electing S-corp.
REASONABLE_OWNER_SALARY = 36_000


def calc_se_tax(taxable_profit):
    """Self-employment tax on 100% of net profit (sole prop / single-member LLC)."""
    se_base = max(0.0, taxable_profit) * SE_TAXABLE_SHARE
    tax = min(se_base, SOCIAL_SECURITY_WAGE_BASE) * 0.124 + se_base * 0.029
    if se_base > ADDITIONAL_MEDICARE_THRESHOLD:
        tax += (se_base - ADDITIONAL_MEDICARE_THRESHOLD) * ADDITIONAL_MEDICARE_RATE
    return tax


def calc_payroll_tax_on_salary(salary):
    """Combined employee + employer FICA on an S-corp owner salary."""
    salary = max(0.0, salary)
    tax = min(salary, SOCIAL_SECURITY_WAGE_BASE) * 0.124 + salary * 0.029
    if salary > ADDITIONAL_MEDICARE_THRESHOLD:
        tax += (salary - ADDITIONAL_MEDICARE_THRESHOLD) * ADDITIONAL_MEDICARE_RATE
    return tax


def run_tax_strategy_analysis(annual_noi, owner_salary=None,
                              accelerated_depreciation=False,
                              apply_depreciation=True, apply_scorp=True,
                              first_year=True):
    """
    Compare today's default tax posture (sole prop / single-member LLC, no
    depreciation election called out) against depreciation and/or an S-corp
    election, on a given year's pre-tax NOI.

    Federal income tax applies to NOI net of depreciation either way (it's
    an ordinary Schedule C/K-1 deduction regardless of entity choice), so
    depreciation shields both federal income tax and SE tax equally. Only
    the SE/payroll-tax base differs between sole-prop (SE tax on 100% of
    taxable profit) and S-corp (payroll tax on salary only, no SE tax on
    distributions).

    `first_year=True` includes the IRC Sec. 195 startup-cost deduction (up
    to $5,000 immediately plus one year of 15-year amortization on the
    rest); set it False for a Year 2+ view, which only gets the ongoing
    amortization slice.

    NOTE ON TEXAS TAXES: every Texas tax this business pays (mixed beverage
    GRT and sales tax, sales tax on parking/beverages/tobacco, property tax,
    employer payroll) is an ordinary operating expense already deducted
    inside `annual_noi` before this function sees it. What's modeled here is
    only the FEDERAL layer - income tax plus self-employment/payroll tax.
    Texas has no personal income tax, which is why there is no state layer.
    """
    salary = owner_salary if owner_salary is not None else REASONABLE_OWNER_SALARY
    depreciation = (YEAR1_ACCELERATED_DEPRECIATION if accelerated_depreciation
                    else ANNUAL_STRAIGHT_LINE_DEPRECIATION) if apply_depreciation else 0.0
    # Startup-cost amortization rides along with the depreciation election -
    # it's the same "capitalize now, deduct over time" idea applied to the
    # non-depreciable pre-opening spend (permits, licensing, cleaning).
    startup_deduction = 0.0
    if apply_depreciation:
        startup_deduction = (YEAR1_STARTUP_DEDUCTION if first_year
                             else ONGOING_STARTUP_AMORTIZATION)
    total_deduction = min(depreciation + startup_deduction, max(0.0, annual_noi))
    # Report the two pieces proportionally if NOI capped the total.
    if depreciation + startup_deduction > 0:
        _scale = total_deduction / (depreciation + startup_deduction)
        depreciation *= _scale
        startup_deduction *= _scale
    taxable_profit = max(0.0, annual_noi - total_deduction)

    federal_income_tax = taxable_profit * FEDERAL_INCOME_TAX_RATE_ONLY

    baseline_se_tax = calc_se_tax(taxable_profit)
    baseline_total_tax = federal_income_tax + baseline_se_tax
    baseline_after_tax = annual_noi - baseline_total_tax

    if apply_scorp:
        salary = min(salary, taxable_profit)
        distribution = taxable_profit - salary
        strategy_se_tax = calc_payroll_tax_on_salary(salary)
    else:
        salary, distribution = 0.0, taxable_profit
        strategy_se_tax = baseline_se_tax

    strategy_total_tax = federal_income_tax + strategy_se_tax
    strategy_after_tax = annual_noi - strategy_total_tax

    # Reference-only: what today's flat blended-rate estimate would show,
    # for comparison against this more granular breakdown.
    blended_baseline_tax = max(0.0, annual_noi) * EFFECTIVE_INCOME_TAX_RATE

    # NOTE: "baseline_*" fields below are the sole-prop/no-S-corp figures on
    # this call's taxable_profit (i.e. after whatever this call's own
    # apply_depreciation/accelerated_depreciation settings did to it) - they
    # are NOT automatically the true zero-strategy baseline. To measure the
    # dollar impact of a lever, diff two calls (e.g. a no-strategy call vs.
    # a combined call), don't rely on a single call's baseline_* fields.
    return {
        "annual_noi": annual_noi,
        "depreciation_expense": depreciation,
        "startup_amortization": startup_deduction,
        "total_deduction": total_deduction,
        "taxable_profit": taxable_profit,
        "federal_income_tax": federal_income_tax,
        "owner_salary": salary,
        "distribution": distribution,
        "baseline_se_tax": baseline_se_tax,
        "baseline_total_tax": baseline_total_tax,
        "baseline_after_tax": baseline_after_tax,
        "strategy_se_tax": strategy_se_tax,
        "strategy_total_tax": strategy_total_tax,
        "strategy_after_tax": strategy_after_tax,
        "blended_baseline_tax": blended_baseline_tax,
    }


def print_tax_strategy_analysis(annual_noi=None):
    """CLI view of the depreciation + S-corp tax strategy analysis, on Base Case Year 1 NOI by default."""
    if annual_noi is None:
        _, base = run_scenario_projection(SCENARIOS["Base Case"])
        annual_noi = base["total_noi"]

    no_strategy = run_tax_strategy_analysis(annual_noi, apply_depreciation=False, apply_scorp=False)
    dep_only = run_tax_strategy_analysis(annual_noi, accelerated_depreciation=False, apply_scorp=False)
    scorp_only = run_tax_strategy_analysis(annual_noi, apply_depreciation=False, apply_scorp=True)
    combined = run_tax_strategy_analysis(annual_noi, accelerated_depreciation=True, apply_scorp=True)

    print(f"\n{'=' * 70}")
    print("  TAX STRATEGY ANALYSIS")
    print(f"{'=' * 70}")
    print(f"\n  Annual NOI (pre-tax): ${annual_noi:,.0f}")
    print(f"\n  DEPRECIATION BASIS")
    print(f"  {'5-Year (equipment/fixtures)':<32} ${DEPRECIABLE_BASIS_5YR:>10,.0f}")
    print(f"  {'15-Year (land improvements)':<32} ${DEPRECIABLE_BASIS_15YR:>10,.0f}")
    print(f"  {'Total depreciable basis':<32} ${TOTAL_DEPRECIABLE_BASIS:>10,.0f}")
    print(f"  {'Straight-line annual expense':<32} ${ANNUAL_STRAIGHT_LINE_DEPRECIATION:>10,.0f}")
    print(f"  {'Accelerated (100% bonus, Yr 1)':<32} ${YEAR1_ACCELERATED_DEPRECIATION:>10,.0f}")
    print(f"\n  STARTUP COSTS (IRC Sec. 195 - not depreciable property)")
    print(f"  {'Qualifying startup basis':<32} ${STARTUP_COST_BASIS:>10,.0f}")
    print(f"  {'Year 1 deduction ($5K + amort.)':<32} ${YEAR1_STARTUP_DEDUCTION:>10,.0f}")
    print(f"  {'Year 2+ amortization':<32} ${ONGOING_STARTUP_AMORTIZATION:>10,.0f}")

    print(f"\n  {'':<24} {'No Strategy':>13} {'+Depreciation':>15} {'+S-Corp Only':>14} {'+Both (Combined)':>18}")
    print("  " + "-" * 88)
    print(f"  {'Total Tax':<24} ${no_strategy['strategy_total_tax']:>12,.0f} "
          f"${dep_only['strategy_total_tax']:>14,.0f} ${scorp_only['strategy_total_tax']:>13,.0f} "
          f"${combined['strategy_total_tax']:>17,.0f}")
    print(f"  {'After-Tax Cash Flow':<24} ${no_strategy['strategy_after_tax']:>12,.0f} "
          f"${dep_only['strategy_after_tax']:>14,.0f} ${scorp_only['strategy_after_tax']:>13,.0f} "
          f"${combined['strategy_after_tax']:>17,.0f}")
    combined_savings = no_strategy["strategy_total_tax"] - combined["strategy_total_tax"]
    print(f"\n  Owner salary (S-corp split): ${combined['owner_salary']:,.0f} "
          f"| Distributions: ${combined['distribution']:,.0f}")
    print(f"  Total tax savings, combined vs. no-strategy baseline: "
          f"${combined_savings:,.0f} "
          f"({combined_savings / no_strategy['strategy_total_tax']:.0%})")


# =============================================================================
# SECTION 9: CLI MENU
# =============================================================================

def print_annual_summary(months, annual, label=""):
    """Pretty-print a full annual projection."""
    month_names = MONTH_NAMES
    print(f"\n{'=' * 93}")
    if label:
        print(f"  {label}")
    print(f"{'=' * 93}")
    print(f"{'Month':<7} {'Gross':>10} {'Trucks':>9} {'Bar':>9} {'DayBev':>8} {'Tobacco':>8} "
          f"{'COTA':>9} {'NOI':>10} {'NutCov':>7}")
    print("-" * 93)
    for m in months:
        cota = (m["cota_parking"] + m["cota_bar_uplift"] + m["cota_daytime_bev_uplift"]
               + m["cota_tobacco_uplift"])
        print(f"{month_names[m['month']]:<7} ${m['total_gross_revenue']:>9,.0f} "
              f"${m['truck_gross']:>8,.0f} "
              f"${m['bar_revenue']:>8,.0f} ${m['daytime_beverage_revenue']:>7,.0f} "
              f"${m['tobacco_revenue']:>7,.0f} "
              f"${cota:>8,.0f} "
              f"${m['noi']:>9,.0f} {m['monthly_nut_coverage']:>6.2f}x")
    print("-" * 93)
    cota_total = (annual["total_cota_parking"] + annual["total_cota_bar"]
                 + annual["total_cota_daytime_bev"] + annual["total_cota_tobacco"])
    print(f"{'YEAR':<7} ${annual['total_gross']:>9,.0f} "
          f"${annual['total_trucks']:>8,.0f} ${annual['total_bar']:>8,.0f} "
          f"${annual['total_daytime_beverage']:>7,.0f} "
          f"${annual['total_tobacco']:>7,.0f} "
          f"${cota_total:>8,.0f} ${annual['total_noi']:>9,.0f} "
          f"{annual['avg_monthly_nut_coverage']:>6.2f}x")
    print(f"\n  Annual Nut:              ${ANNUAL_NUT:,.0f}")
    print(f"  Free Cash Flow (pre-tax): ${annual['total_net_cash']:,.0f}")
    print(f"  Est. Income Tax ({EFFECTIVE_INCOME_TAX_RATE:.0%}):   ${annual['income_tax']:,.0f}")
    print(f"  After-Tax Cash Flow:     ${annual['after_tax_noi']:,.0f}")
    print(f"  FCF Yield pre/after tax: {annual['fcf_yield']:.1%} / {annual['after_tax_fcf_yield']:.1%}")


def main():
    menu = """
==================================================
  FOOD TRUCK PARK + BAR & BEVERAGE STAND | Financial Model
==================================================
  1. Annual Projection (Base Case)
  2. Sensitivity Analysis
  3. Break-Even Analysis
  4. Monte Carlo (10K scenarios)
  5. Scenario Comparison
  6. Owner Summary
  7. Cash Reserve Tracker
  8. LOC Payoff Schedule
  9. Tax Strategy Analysis
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
        elif choice == "9":
            print_tax_strategy_analysis()
        elif choice == "0":
            print("\n  Goodbye!")
            break
        else:
            print("  Invalid choice. Try again.")


if __name__ == "__main__":
    main()
