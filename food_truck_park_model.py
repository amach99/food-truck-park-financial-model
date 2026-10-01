#!/usr/bin/env python3
"""
Food Truck Park + Bar & Beverage Stand | Del Valle
Interactive Financial Model

Concept:
  - Food truck park (pad rent $500-$1,000 + 5-10% revenue share)
  - Bar & beverage stand: evening container bar pouring draft beer (taps),
    canned/bottled beer (coolers), liquor shots, and made-to-order cocktails,
    plus an all-day non-alcohol window selling
    soda/juice/water/coffee (NO tobacco/nicotine - see Section 1)
  - Power/water/waste/wifi for the truck hubs, sub-metered and billed at cost
    (Texas PUC utility-resale rules: PURA Sec. 39.107 - resale at cost, no
    markup)

Loan request: $500,000, financed by a bank term loan (fixed-payment, fully
amortizing - rate/term are placeholders pending an actual bank quote; see
LOAN_INTEREST_RATE/LOAN_TERM_YEARS). USE_OF_FUNDS is the Sources & Uses of
that $500,000: payoff of the owner's existing personal LOC ($120,000
actually drawn against it), septic, paving, the container bar buildout,
remaining permits, contingency, and a Reserve & Safety Cash plug that absorbs
whatever's left after those named items. The owner's real "Phase 0.5
Master Plan" cost tracker (Notion) totaled $80,100 of itemized, real
vendor-quoted buildout, mostly already done or in progress; the $66,800
of it actually drawn against that (now-being-paid-off) personal LOC lives
separately in PHASE_0_5_CAPITAL_IMPROVEMENTS - it isn't part of the new
loan's Use of Funds (that would double-count the LOC payoff), but it's
real capital investment in the property and still feeds depreciation and
the capitalized basis (Section 9). Of the tracker's remaining $13,300
(permits + contingency), the $5,300 TABC Mixed Beverage permit has since
been obtained and paid under the old LOC - so it sits inside the $120,000
payoff, not in USE_OF_FUNDS, which carries only the still-unpaid $1,700
of health permit / business license plus contingency. Of the $500,000 loan, $120,000 is already committed
(the LOC payoff) and $380,000 is new cash still to be drawn.
Line items the owner flagged as planning-only and never implemented
(generator, grease removal service, propane tank service) are excluded
entirely rather than estimated.

The loan is a fixed-payment amortizing term loan (unlike the smaller
personal LOC that financed the original Phase 0.5 buildout), so the fixed
monthly nut already reflects the real, contractual P&I payment - no
"conservative flat balance" assumption needed. A separate amortization
schedule (Section 7) shows the year-by-year principal/interest split, plus
an optional scenario for sweeping extra free cash flow toward early payoff.
A "Nut Coverage Ratio" (operating income before fixed costs / monthly nut,
nut now including the loan payment) is the plain-language coverage metric
- though with a real bank loan now in place, it's worth comparing against
an actual DSCR calc too (see the CRE Investment Summary tab).

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

# --- Historical Phase 0.5 buildout (financed by the OLD personal LOC) ---
# Sourced from the owner's real "Phase 0.5 Master Plan" cost tracker
# (Notion), itemized at actual vendor-quoted prices, plus a few real costs
# the tracker doesn't capture yet (refrigerators, initial bar inventory).
# Each entry carries its real build status. Excluded entirely (per owner
# instruction - these were planning-only line items never actually
# implemented, with no cost attached): a second/backup generator, grease
# removal service, propane tank service. The original Phase 0.5 plan
# floated a container bar with no price ever set, then substituted a
# cheap $1,500 Walmart shed instead - the loan-funded Phase 2 buildout
# below now funds the real container bar (see USE_OF_FUNDS), which
# supersedes and replaces the placeholder shed.
#
# This list is real capital investment in the property regardless of how
# it was financed, so it still feeds depreciation classification and the
# property's capitalized basis (Section 9) below. But it is NOT part of
# the new $500,000 bank loan's Use of Funds (USE_OF_FUNDS, below): the
# owner's original Phase 0.5 tracker totaled $80,100, of which the $66,800
# below (Electrical, Gravel, Plumbing, and 22 smaller items) was already
# drawn against the owner's original, separate personal LOC. That LOC gets
# paid off in full by the new loan (see the "Payoff of existing line of
# credit" line in USE_OF_FUNDS) - counting these items again in the new
# loan's Use of Funds, on top of paying off the LOC that already funded
# them, would double-count the same real dollars. The remaining $13,300 of
# the original $80,100 - permits and contingency, the two items that
# genuinely hadn't been spent yet under the old LOC - live in USE_OF_FUNDS
# instead, as real forward-looking costs the new loan needs to cover.
PHASE_0_5_CAPITAL_IMPROVEMENTS = [
    # -- Done (already paid, via the original personal LOC) --
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
    # -- Not started (LOC funds already drawn/allocated, work pending) --
    ("Gravel", 15_400, "not_started"),
    ("Trash Cans", 200, "not_started"),
    ("Storage Shed (wooden, general)", 3_119, "not_started"),
    ("Refrigerators (bar coolers)", 3_000, "not_started"),
    ("Initial beverage inventory (beer + liquor stock)", 3_600, "not_started"),
]
PHASE_0_5_TOTAL = sum(a for _, a, _ in PHASE_0_5_CAPITAL_IMPROVEMENTS)  # $66,800

# --- $500,000 Bank Loan: Sources & Uses ---
# The owner is financing a larger next phase via a $500,000 bank term loan
# rather than continuing to draw the original Phase 0.5 personal LOC.
# Septic and paving are new infrastructure the Phase 0.5 tracker above
# never covered; the container bar replaces the $1,500 Walmart shed
# placeholder (see PHASE_0_5_CAPITAL_IMPROVEMENTS) with a real full
# buildout; the LOC payoff retires the existing personal LOC in full
# ($120,000 actually drawn against it - not its full $170,000 facility
# limit); contingency is the one Phase 0.5 item that hadn't been spent yet
# (see above).
#
# PERMITS LINE - $1,700, NOT $7,000. This line previously carried $7,000,
# dominated by the $5,300 TABC Mixed Beverage Permit (two-year fee, TABC
# schedule in force since Sept 2021). **The MB permit has since been
# obtained and paid for**, funded by the old personal LOC - so its $5,300
# is already inside the $120,000 LOC-payoff line above, as part of the
# "pre-loan soft costs" that make up the difference between that $120,000
# draw and the $66,800 of itemized Phase 0.5 capital improvements. Leaving
# $5,300 here as a forward-looking cost double-counted the same dollars
# against the payoff (and inflated TOTAL_CAPITALIZED_BASIS, which
# capitalizes this line). What remains is the health permit and business
# license, still to be paid. The freed $5,300 moved to Reserve & Safety
# Cash so TOTAL_PROJECT_COST stays at exactly $500,000.
#
# Note the MB permit is deliberately NOT added to
# PHASE_0_5_CAPITAL_IMPROVEMENTS: that list is physical capital
# improvements feeding depreciation classification, and a liquor license is
# an intangible on a different tax footing. It is captured (correctly, once)
# via the LOC payoff. A new MB permittee may also have to post a conduct
# surety bond and a tax security bond; bonding is NOT modeled - confirm
# requirements with TABC.
#
# "Reserve & Safety Cash" is what's left of the $500,000 ask after every
# named big-ticket item above it - held back rather than earmarked to a
# specific cost, sized as a plug so the grand total lands on exactly
# $500,000. The owner deliberately chose to keep the loan request at the
# full $500,000 (rather than trimming it to match itemized buildout costs)
# so the leftover sits in reserve as safety cash instead.
#
# Permits and contingency were raised after the Aug 31 independent review
# ($1,700 → $12,000; $6,300 → $24,000) and funded OUT OF this reserve plug,
# so the ask stays $500,000 and the reserve falls $172,000 → $144,000.
# The already-paid TABC Mixed Beverage permit is still NOT in this line
# (it sits inside the LOC payoff). Paving stays the $50,000 asphalt base
# (Sep 30 lock). GRAVEL_ALT_BUDGET is the unselected alternate — do not
# swap it in without rebuilding the plug. A later Sep 30 draft wanted
# additional named softs (several still TBD) and a ~$25k/10% contingency;
# those amounts are not locked, so they are not applied here.
PAVING_BUDGET = 50_000            # asphalt base (selected). Not the gravel alternate.
GRAVEL_ALT_BUDGET = 15_400        # unselected alternate; Phase 0.5 gravel line is separate
PERMITS_AND_SOFT_COSTS = 12_000   # site development, OSSF, health, TxDOT, fire, CO
PERMITS_AND_SOFT_COSTS_LABEL = (
    "Permits & soft costs (site development, OSSF, health, TxDOT driveway, "
    "fire/life safety, certificate of occupancy)"
)
CONTINGENCY_BUDGET = 24_000
_NAMED_USES_BEFORE_RESERVE = [
    ("Payoff of existing high-interest line of credit (Phase 0.5 & pre-loan soft costs)", 120_000, "done"),
    ("Septic system installation", 100_000, "not_started"),
    ("Paved asphalt roads / internal access improvements", PAVING_BUDGET, "not_started"),
    ("Container Bar (full buildout)", 50_000, "not_started"),
    (PERMITS_AND_SOFT_COSTS_LABEL, PERMITS_AND_SOFT_COSTS, "not_started"),
    ("Contingency", CONTINGENCY_BUDGET, "not_started"),
]
LOAN_ASK = 500_000
RESERVE_AND_SAFETY_CASH = LOAN_ASK - sum(a for _, a, _ in _NAMED_USES_BEFORE_RESERVE)
USE_OF_FUNDS = _NAMED_USES_BEFORE_RESERVE + [
    ("Reserve & Safety Cash", RESERVE_AND_SAFETY_CASH, "not_started"),
]
TOTAL_PROJECT_COST = sum(a for _, a, _ in USE_OF_FUNDS)  # $500,000
ALREADY_SPENT = sum(a for _, a, status in USE_OF_FUNDS if status == "done")  # $120,000
NEW_CASH_NEEDED = TOTAL_PROJECT_COST - ALREADY_SPENT                          # $380,000

# --- Capital (financed via a $500,000 bank term loan, fixed-payment,
# fully amortizing - NOT the original personal LOC financing the Phase 0.5
# buildout above relied on). Rate/term are placeholders pending an actual
# bank quote: 10% is the conservative end of a 9.5-10% range the owner
# gave, and 25 years matches typical SBA-loan amortization. LOAN_AMOUNT is
# re-derived from TOTAL_PROJECT_COST (not a second hardcoded 500_000) so
# the two stay in sync by construction if USE_OF_FUNDS ever changes again.
LOAN_AMOUNT = TOTAL_PROJECT_COST      # fully drawn at closing to fund the buildout
LOAN_INTEREST_RATE = 0.10             # placeholder pending an actual bank quote
LOAN_TERM_YEARS = 25                  # placeholder - typical SBA amortization


def _amortization_payment(principal, annual_rate, term_years):
    """Fixed monthly principal + interest payment for a fully amortizing loan."""
    monthly_rate = annual_rate / 12
    n_payments = term_years * 12
    return principal * monthly_rate / (1 - (1 + monthly_rate) ** -n_payments)


def _amortization_balance(principal, annual_rate, term_years, months_elapsed):
    """Remaining principal balance after `months_elapsed` monthly payments."""
    monthly_rate = annual_rate / 12
    n_payments = term_years * 12
    months_elapsed = min(months_elapsed, n_payments)
    growth = (1 + monthly_rate) ** n_payments
    return principal * (growth - (1 + monthly_rate) ** months_elapsed) / (growth - 1)


def _amortization_interest_for_year(principal, annual_rate, term_years, year_index):
    """Total interest paid during loan-year `year_index` (1-based) - the
    deductible portion of that year's debt service (principal is not)."""
    n_payments = term_years * 12
    months_start = (year_index - 1) * 12
    months_end = min(year_index * 12, n_payments)
    if months_start >= n_payments:
        return 0.0
    balance_start = _amortization_balance(principal, annual_rate, term_years, months_start)
    balance_end = _amortization_balance(principal, annual_rate, term_years, months_end)
    payment = _amortization_payment(principal, annual_rate, term_years)
    total_paid = payment * (months_end - months_start)
    principal_paid = balance_start - balance_end
    return total_paid - principal_paid


# Unrounded. Annual debt service is this × 12 (~$54,522 at the placeholder
# 10% / 25-year terms). Round only when displaying a dollar figure — rounding
# the monthly payment first and then × 12 was the $54,528 figure.
LOAN_MONTHLY_PAYMENT = _amortization_payment(LOAN_AMOUNT, LOAN_INTEREST_RATE, LOAN_TERM_YEARS)

# --- Land / Site ---
# Deeded acreage, per the two General Warranty Deeds dated 02/20/2026
# conveying the property to JVAM Capital LLC: a 1.500-acre tract and a
# 2.932-acre tract, both out of the Peter C. Harrison Survey, Abstract
# No. 2104 (portions of Lot 2, Block A, Final Plat of Del Valle Dollar
# General, Travis County Doc. No. 201600109). Earlier versions of this
# model rounded to 4.5; use the deeded figure, since a lender pulls the
# deed. The ~2.932-acre tract is the dedicated event parking area
# (EVENT_PARKING_SPACES below); the 1.500-acre tract carries the pads,
# bar, and seating.
LAND_ACRES = 4.432
LAND_PURCHASE_PRICE = 1_400_000  # what the owner actually paid (owned outright, not financed here)
LAND_ASSESSED_VALUE = 300_000    # county tax assessment - basis for the ~$4K/yr property tax bill
LAND_VALUE = LAND_PURCHASE_PRICE  # kept for reference; use TOTAL_CAPITALIZED_BASIS for basis math
# The real capitalized basis for any yield-on-cost / cap-rate valuation: no
# CRE metric excludes land from basis just because it was owned outright
# rather than purchased with this project's capital. TOTAL_PROJECT_COST
# alone (the $500,000 loan) is no longer the right basis here, since it now
# includes two purely financial line items that aren't capital improvements
# at all - the LOC payoff (refinancing existing debt) and Reserve & Safety
# Cash (uncommitted cash, not yet spent on anything). Instead: land, plus
# PHASE_0_5_TOTAL (the real historical buildout - a capital investment in
# the property regardless of which loan financed it), plus every
# USE_OF_FUNDS line except those same two financial items. This basis is
# used only by the CRE valuation/returns functions (Section 9);
# TOTAL_PROJECT_COST (buildout-only, but now meaning "the loan") remains the
# right denominator for "return on what I actually spent in cash" - that's
# what the existing FCF Yield metrics on the main dashboard tabs mean and
# continue to mean.
_LOC_PAYOFF_AND_RESERVE_LABELS = {
    "Payoff of existing high-interest line of credit (Phase 0.5 & pre-loan soft costs)",
    "Reserve & Safety Cash",
}
TOTAL_CAPITALIZED_BASIS = (
    LAND_PURCHASE_PRICE + PHASE_0_5_TOTAL
    + sum(a for label, a, _ in USE_OF_FUNDS if label not in _LOC_PAYOFF_AND_RESERVE_LABELS)
)
# The existing $4,000/yr bill taxes RAW LAND only. Once the buildout is
# finished, Travis County adds the improvements (gravel lot, electrical,
# plumbing, structures, shade, lighting) to the tax roll and the bill goes
# up - a real recurring cost the model previously ignored. Conservatively
# assume the FULL capitalized buildout (TOTAL_CAPITALIZED_BASIS less land -
# i.e. excluding the LOC payoff and Reserve, which are financial, not
# physical, and would badly overstate a county assessment if taxed as
# improvements) becomes assessed value (some line items - inventory,
# contingency, permits - arguably aren't taxable real property, so this
# still overstates rather than understates) at a 2.0% effective rate.
# 2.0% is above the ~1.33% the owner's own land bill implies ($4,000 on a
# $300K assessment) and above the ~1.54% Travis County median, chosen
# deliberately on the "conservative = higher expense" rule.
PROPERTY_TAX_IMPROVEMENT_RATE = 0.020
PROPERTY_TAX_IMPROVEMENTS_MONTHLY = round(
    (TOTAL_CAPITALIZED_BASIS - LAND_PURCHASE_PRICE) * PROPERTY_TAX_IMPROVEMENT_RATE / 12)
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

# --- COTA Impact Slider (dashboard-adjustable "what if COTA didn't happen /
# was exceptional" lever) ---
# COTA_IMPACT_MULTIPLIER scales the COTA parking/bar-uplift/daytime-bev-
# uplift/incremental-cost totals computed by calc_cota_event_revenue(): 0.0
# = COTA has zero effect (as if the event calendar didn't exist), 1.0 =
# today's default modeled calendar (COTA_EVENTS_BY_MONTH / COTA_EVENT_TIERS
# as-is, unchanged from before this lever existed), up to 2.0 = a
# deliberately optimistic "very high performing events" scenario. The
# dashboard slider runs 0-100% and maps to this 0.0-2.0 range so the
# midpoint (50%) reproduces today's baseline exactly.
COTA_IMPACT_MULTIPLIER_DEFAULT = 1.0
# Above a multiplier of 1.0 (i.e. sliding past today's baseline toward
# "exceptional events"), COTA event months ALSO pull extra foot traffic
# into the food trucks themselves - not just parking/bar/beverage revenue.
# COTA_TRUCK_BOOST_MAX is the ceiling on that effect: at multiplier 2.0
# (slider all the way right), truck sales in event months run up to 20%
# hotter, and vacant slots close the gap toward full occupancy by up to
# 20% of the remaining gap. Zero at multiplier <= 1.0, so today's baseline
# behavior is completely unaffected by this lever's existence.
COTA_TRUCK_BOOST_MAX = 0.20

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
# Operations begin March 2027. The August 2026 plan's September 2026 open
# was not credible (septic, paving, bar, and permits still unfinished, and
# it booked September event revenue the site could not have hosted).
# "Operating month 1" in BAR_Y1_RAMP means "1st month since opening," NOT
# January — it maps to this calendar month. Sid's Sep 30 timing lock is the
# same open (within ~6 months, ~Mar 2027): 5 months of entitlement/permit
# lag plus 1 month of post-permit build. That 6-month clock is
# CONSTRUCTION_PERIOD_MONTHS (IRR timing). The 4-month pre-open cash burn
# below is a different clock — debt service and a few fixed bills against
# zero revenue — and is not a substitute for the 6-month IRR lag.
OPENING_MONTH = 3   # March
OPENING_YEAR = 2027
POST_PERMIT_BUILD_MONTHS = 1
ENTITLEMENT_PERMIT_LAG_MONTHS = 5
TIME_TO_OPEN_MONTHS = POST_PERMIT_BUILD_MONTHS + ENTITLEMENT_PERMIT_LAG_MONTHS  # 6


def operating_to_calendar_month(op_month, opening_month=None):
    """Map an operating-month index (1-12, months since opening) to the
    calendar month (1-12) it actually falls in, given OPENING_MONTH."""
    start = opening_month if opening_month is not None else OPENING_MONTH
    return ((start - 1 + (op_month - 1)) % 12) + 1

# --- Evening Bar (full container bar: draft + canned beer, shots, cocktails) ---
# Evening-only operation (6pm-10:30/11pm, ~4.5 hrs/day). The park is building
# out a FULL container bar ($50,000, "Container Bar (full buildout)" in
# USE_OF_FUNDS): taps for draft beer, coolers for canned/bottled, a
# shot-pour station, and a made-to-order cocktail well. This replaces the
# earlier prepackaged-only plan (canned beer + sealed shots, no mixed
# drinks) - see the "Unit pricing" block below for the four-item menu, mix,
# and the resulting check/COGS. Cocktails carry a real bartender
# skill/speed requirement the prepackaged plan avoided. Staffing is scheduled
# wages (see DAYTIME_ATTENDANT_WAGE / EVENING_BARTENDER_WAGE), not a revenue
# share. The ALCOHOL side of the bar stays evening-only for TABC/
# demand reasons; the all-day extension is the non-alcoholic beverage
# window (soda/juice/water/coffee - see DAYTIME_BEVERAGE_* below), so the
# alcohol traffic assumptions (BAR_WEEKDAY/WEEKEND_CUSTOMERS) are unchanged.
BAR_HOURS_PER_DAY = 4.5           # alcohol service window: 6pm-10:30pm average
DAYTIME_BEVERAGE_HOURS_PER_DAY = 11.0  # all-day non-alcoholic window (~11am-close)
# Weekday (Mon-Thu) vs weekend (Fri-Sun) traffic, ESTIMATES needing field
# validation. Split rather than a single flat daily average because a bar's
# staffing doesn't change with customer count (scheduled hours, not a
# revenue share), so the only value in more granularity is
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
# Unit pricing (owner-specified). Four items now that the container bar
# (coolers + taps + mixed-drink setup, $50,000 in USE_OF_FUNDS - see
# "Container Bar (full buildout)") replaces the original beer/shots-only
# stand: draft beer (via taps), canned/bottled beer (via coolers), single-
# serve shots, and made-to-order cocktails.
DRAFT_BEER_PRICE = 6.00           # per pour, via taps
BEER_PRICE = 7.00                 # per canned/bottled beer, via coolers
SHOT_PRICE = 3.00                 # per single-serve plastic shot glass
COCKTAIL_PRICE = 12.00            # made-to-order mixed drink
# Item mix (owner-specified): beer is 45% of items sold, split 70% draft /
# 30% canned now that taps are installed (draft pours faster and cheaper,
# so it becomes the default once available); shots 20%; cocktails 35%.
DRAFT_BEER_MIX_PCT = 0.45 * 0.70   # 31.5% of items
BEER_MIX_PCT = 0.45 * 0.30         # 13.5% of items (canned/bottled)
SHOT_MIX_PCT = 0.20
COCKTAIL_MIX_PCT = 0.35
DRINKS_PER_VISIT = 1.5            # avg items per customer visit (unchanged - a
                                    # fuller bar changes WHAT people order, not
                                    # how many rounds they have)
AVG_ITEM_PRICE = (DRAFT_BEER_MIX_PCT * DRAFT_BEER_PRICE + BEER_MIX_PCT * BEER_PRICE
                   + SHOT_MIX_PCT * SHOT_PRICE + COCKTAIL_MIX_PCT * COCKTAIL_PRICE)  # $7.635
BAR_AVG_CHECK = DRINKS_PER_VISIT * AVG_ITEM_PRICE   # $11.45/visit
# Pre-packaged/single-serve goods carry less margin than pouring liquor into
# mixed drinks (reselling a manufactured/portioned product vs. marking up a
# poured ingredient). COGS weighted by REVENUE share of each item (not item
# count), since items carry different prices: draft/canned beer ~37% COGS
# each (draft kept at the same conservative rate as canned - no assumed
# margin improvement without a real keg-cost quote), shot ~25% COGS,
# cocktail ~30% COGS (liquor + mixers + garnish + cup - an ESTIMATE pending
# real recipe costing; typical bar cocktail COGS runs lower, ~20-25%, so
# this is deliberately padded per the project's err-toward-higher-expenses
# rule).
_draft_rev_frac = (DRAFT_BEER_MIX_PCT * DRAFT_BEER_PRICE) / AVG_ITEM_PRICE
_beer_rev_frac = (BEER_MIX_PCT * BEER_PRICE) / AVG_ITEM_PRICE
_shot_rev_frac = (SHOT_MIX_PCT * SHOT_PRICE) / AVG_ITEM_PRICE
_cocktail_rev_frac = (COCKTAIL_MIX_PCT * COCKTAIL_PRICE) / AVG_ITEM_PRICE
COGS_RATE = (_draft_rev_frac * 0.37 + _beer_rev_frac * 0.37
             + _shot_rev_frac * 0.25 + _cocktail_rev_frac * 0.30)   # ~32.2%
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
#
# Tax-inclusive prices: back the 8.25% sales tax out of the cash receipt
# BEFORE applying the 6.7% GRT. Applying GRT to a base that already includes
# sales tax taxes a tax. VARIABLE_COST_RATE is the effective rate on the
# cash receipt under that order (COGS stays on the full receipt).
GRT_RATE = 0.067                 # TX Mixed Beverage Gross Receipts Tax (permittee's own liability)
MB_SALES_TAX_RATE = 0.0825       # TX Mixed Beverage Sales Tax (assumed tax-inclusive pricing)


def _inclusive_sales_tax(receipts, rate):
    """Sales tax embedded in a tax-inclusive cash price (rate / (1 + rate))."""
    if not receipts or rate <= 0:
        return 0.0
    return receipts * rate / (1.0 + rate)


def alcohol_taxes_on_inclusive_receipts(receipts):
    """(GRT, MB sales tax) with sales tax backed out before GRT."""
    sales_tax = _inclusive_sales_tax(receipts, MB_SALES_TAX_RATE)
    grt = (receipts - sales_tax) * GRT_RATE
    return grt, sales_tax


_MB_TAX_ON_RECEIPT = (MB_SALES_TAX_RATE / (1.0 + MB_SALES_TAX_RATE)
                      if MB_SALES_TAX_RATE else 0.0)
_GRT_ON_RECEIPT = GRT_RATE / (1.0 + MB_SALES_TAX_RATE) if MB_SALES_TAX_RATE else GRT_RATE
VARIABLE_COST_RATE = COGS_RATE + _GRT_ON_RECEIPT + _MB_TAX_ON_RECEIPT
CC_PROCESSING_RATE = 0.028
CC_CARD_USAGE_RATE = 0.85
SHRINKAGE_RATE = 0.025           # of beverage COGS value (grab-and-go single-serve
                                  # items may be easier to pilfer than pours - watch this)
# The old 5% beverage-revenue share is retired. It paid about $2–$3/hr
# across the open hours — below minimum wage. Labor is now scheduled hours.
# BARTENDER_SHARE_RATE remains 0 so a stale caller cannot silently re-add
# the share on top of wages.
BARTENDER_SHARE_RATE = 0.0
# Scheduled labor (estimates — wage quotes are still evidence, not facts).
# Daytime attendant covers the non-alcohol window only (11-hour beverage
# day minus the 4.5-hour evening bar ≈ 6.5 hours). One attendant plus one
# evening bartender is still a light crew for an 11-hour day; the event
# extra body is the only relief, and only on COTA event days.
DAYTIME_ATTENDANT_WAGE = 13.00    # $/hr, all-day non-alcohol window
EVENING_BARTENDER_WAGE = 16.00    # $/hr, alcohol service window
EVENT_EXTRA_WAGE = 15.00          # $/hr, one extra body on each COTA event day
EVENT_EXTRA_HOURS_PER_DAY = DAYTIME_BEVERAGE_HOURS_PER_DAY  # full open day
OVERTIME_ALLOWANCE_RATE = 0.10    # flat allowance on hourly wages, not a timecard
MANAGER_ANNUAL_SALARY = 24_000    # cash salary; lodging is not part of this
# Employer-side payroll burden on ALL cash wages (hourly + OT allowance +
# manager salary). ~10% is a deliberately conservative blend (FICA 7.65% +
# TX SUTA new-employer rate + FUTA). Confirm classification with a CPA.
# Lodging is disclosed and NOT expensed. IRC Sec. 119 and FLSA Sec. 3(m)
# can exclude lodging furnished for the employer's convenience on the
# premises as a condition of employment, but both are fact-specific. Do not
# treat the exclusion as established.
LODGING_PROVIDED = True
LODGING_EXPENSED = False
EMPLOYER_PAYROLL_BURDEN_RATE = 0.10

# --- All-Day Beverages (soda, juice, water, coffee) ---
# Extends the bar's operating window from evening-only (BAR_HOURS_PER_DAY)
# to all-day. Staffed by a separate daytime attendant at DAYTIME_ATTENDANT_WAGE,
# not by the evening bartender working the whole day unpaid.
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

# --- Tobacco & Nicotine: REMOVED (deliberate, do not re-add without data) ---
# An earlier version of this model carried a seventh revenue stream selling
# cigarettes, vapes, and nicotine pouches (Zyn) from the same all-day window
# as the beverage stand. It has been removed entirely. The reasoning, kept
# here so the decision isn't silently re-litigated later:
#
#   1. NO COMPETITIVE EDGE. Dollar General next door (~30 sec walk) sells
#      BOTH cigarettes AND nicotine pouches. The stream was originally
#      justified on the theory that DG stocked cigarettes but not vapes/Zyn,
#      leaving the park a narrow edge on the higher-margin sub-products.
#      That premise turned out to be wrong. A customer already walking past
#      a DG has no reason to buy nicotine at a food truck park, and there is
#      also a smoke shop across the road (~1-2 min).
#   2. THE MARGIN NEVER JUSTIFIED IT. At the old assumptions the stream
#      grossed ~$84K/yr at steady state (~16% of gross revenue) but threw
#      off only ~$12K of NOI (~5%), because blended COGS ran ~68% -
#      cigarette retail margin is famously thin. It inflated the top line
#      far more than the bottom line, which is exactly the kind of flattery
#      this model is supposed to avoid.
#   3. IT CARRIED REAL COSTS AND OBLIGATIONS. A separate TX Comptroller
#      cigarette/tobacco retailer permit plus an e-cigarette retailer
#      permit (a different regulatory track from the TABC alcohol permit),
#      age-verification liability under federal Tobacco 21, and inventory
#      shrinkage on a high-theft product category.
#
# Removing it is consistent with this project's estimating rule: when
# uncertain, err toward lower revenue. If real operating data later shows
# genuine walk-up nicotine demand the park is uniquely positioned to serve,
# re-add it as its own stream with its own attach rate and COGS - do not
# fold it into DAYTIME_BEVERAGE_*, whose ~22% COGS and "everyone's thirsty"
# attach rate would badly overstate it.

# Year 1 ramp for every customer-facing revenue stream that has to be
# DISCOVERED: the evening bar and daytime beverages.
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
# daytime beverage sales ride on food-truck lunch traffic that has little
# to do with what's on screen.
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
# hold - only the check size is rescaled to the current BAR_AVG_CHECK.
# rev_base was $9.00-check figures (the beer/shots-only era); rescaled here
# by BAR_AVG_CHECK ($11.45) / old BAR_AVG_CHECK ($9.00) = 1.2725 now that
# the container bar (draft + canned beer, shots, cocktails) is back in the
# mix - see the "Unit pricing" note above.
#
# YEAR 1 CALENDAR CHECK (operating year Mar 2027 - Feb 2028), comparing the
# owner's sports-schedule research against what actually falls in the window:
#   - Super Bowl LXI: Sun Feb 14, 2027 — BEFORE the March 2027 open. Not in
#     Year 1. The February seasonal line is the following Super Bowl (2028).
#   - March Madness 2027: Mar-Apr 2027. IN WINDOW - modeled (opening month).
#   - NYE: Dec 31, 2027. IN WINDOW - modeled.
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
    "super_bowl":    {"month": 2,  "rev_base": 1_253},   # was 985 at the $9.00 check
    "march_madness": {"month": 3,  "rev_base": 1_572},   # was 1,235 at the $9.00 check
    "nye":           {"month": 12, "rev_base": 1_572},   # was 1,235 at the $9.00 check
}

# --- Utility Pass-Through (sub-metered, billed AT COST) ---
# Texas PUC resale rules (PURA Sec. 39.107, 16 TAC 24.281-24.288): sub-metered
# tenants are billed at cost, no markup. Modeled as offsetting revenue/cost so
# gross billings are visible but NOI impact is zero.
UTILITY_BILL_PER_TRUCK = 350     # trucks pull heavy 50A loads

# --- COTA Event Tiers ---
# F1's COTA agreement runs through 2034 (the one contracted horizon). This
# model does not invent a post-2034 F1 calendar. NASCAR at COTA is the
# DuraMAX Texas Grand Prix, not the EchoPark Grand Prix. COTALAND is a
# scheduled competitor (announced opening), NOT park revenue — it is not
# in COTA_EVENTS_BY_MONTH.
F1_AGREEMENT_THROUGH_YEAR = 2034
COTALAND_STATUS = "scheduled_competitor_not_park_revenue"
# Parking uses the dedicated 3-acre lot (EVENT_PARKING_SPACES = 270 spaces)
# on event days. The F1 tier price of $80/spot is an estimate checked against
# neighboring lots on F1 weekends - and this lot offers more
# value (on-site food trucks, bar, and a place to hang out while post-event
# traffic clears), which supports both the price and repeat/word-of-mouth
# demand vs. a bare gravel lot. "incremental_cost" is hired parking-operations
# staff (to organize/run the lot) + extra porta-potty rental for the weekend
# - not a big-venue staffing budget - scaled up ~1.8x from the original
# 150-space sizing to cover the larger lot's staffing needs.
# Bar uplift: on event days the bar extends hours / opens early to serve
# event crowds AND runs premium event pricing across all four items instead
# of the normal $6/$7/$3/$12, so uplift = customer-volume uplift x the event
# check. The stored bar_uplift_per_weekend dollar figures below were sized at
# the old $15.375 event check (beer/shots only) and are rescaled by
# $17.055/$15.375 = 1.109 now that the container bar pours draft and
# cocktails at event pricing too - the VOLUME assumptions behind them are
# unchanged (see the note about not double-counting the hours restriction).
COTA_EVENT_DRAFT_BEER_PRICE = 10.00
COTA_EVENT_BEER_PRICE = 12.00
COTA_EVENT_SHOT_PRICE = 5.00
COTA_EVENT_COCKTAIL_PRICE = 16.00
COTA_EVENT_AVG_CHECK = DRINKS_PER_VISIT * (
    DRAFT_BEER_MIX_PCT * COTA_EVENT_DRAFT_BEER_PRICE
    + BEER_MIX_PCT * COTA_EVENT_BEER_PRICE
    + SHOT_MIX_PCT * COTA_EVENT_SHOT_PRICE
    + COCKTAIL_MIX_PCT * COTA_EVENT_COCKTAIL_PRICE)  # $17.055
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
        "bar_uplift_per_weekend": 11_276,
        "incremental_cost": 10_800,
    },
    "tier2_motogp": {
        "name": "MotoGP Grand Prix of the Americas",
        "parking_price": 55, "daily_occupancy": [0.40, 0.70, 0.93],  # Fri practice / Sat quali / Sun race
        "bar_uplift_per_weekend": 5_042,
        "incremental_cost": 6_300,
    },
    "tier2_nascar": {
        "name": "NASCAR Cup Series (DuraMAX Texas Grand Prix)",
        "parking_price": 50, "daily_occupancy": [0.55, 0.80],  # Sat support races / Sun race
        "bar_uplift_per_weekend": 2_823,
        "incremental_cost": 4_500,
    },
    "tier3_wec": {
        "name": "WEC 6 Hours of COTA",
        "parking_price": 35, "daily_occupancy": [0.45, 0.70],
        "bar_uplift_per_weekend": 1_686,
        "incremental_cost": 2_160,
    },
    "tier3_gt_transam": {
        "name": "GT World Challenge / TransAm / Other Races",
        "parking_price": 25, "daily_occupancy": [0.25, 0.35],
        "bar_uplift_per_weekend": 860,
        "incremental_cost": 900,
    },
    "tier3_concert": {
        "name": "Major Concert (Germania Amphitheater)",
        "parking_price": 30, "daily_occupancy": [0.55],
        "bar_uplift_per_weekend": 566,
        "incremental_cost": 720,
    },
    "tier3_festival": {
        "name": "Festival (FoodieLand, etc.)",
        "parking_price": 30, "daily_occupancy": [0.35, 0.45],
        "bar_uplift_per_weekend": 471,
        "incremental_cost": 720,
    },
    "tier4_trackday": {
        "name": "Track Day / Car Club / Bike Night",
        "parking_price": 0, "daily_occupancy": [0.10],
        "bar_uplift_per_weekend": 294,
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
# including the fixed monthly principal + interest payment on the $500,000
# bank term loan (see run_loan_amortization_schedule for the year-by-year
# principal/interest split, and for the optional extra-prepayment scenario).
# Cash labor is NOT in this dict. The manager is paid MANAGER_ANNUAL_SALARY
# and the floor is paid scheduled hourly wages (daytime attendant, evening
# bartender, plus one extra body on COTA event days) inside
# calc_scheduled_labor(). Lodging is still provided and still not expensed
# (LODGING_EXPENSED is False). One attendant plus one bartender is a light
# crew for the combined day — flagged, not padded with an invented second
# shift.
# waste_service, wifi_internet, and pos_tech_subscriptions are actual
# recurring vendor costs from the owner's Phase 0.5 tracker (porta-potty +
# dumpster, StarLink, Clover POS respectively) - not estimates. water_bill/
# electric_bill/septic have no vendor number yet (Notion shows them as real
# but unpriced) so they're estimates pending an actual bill; "Merch" is
# excluded entirely (no longer planned, no spend).
#
# `accounting_tax_prep` is a compliance cost this model previously omitted.
# An MB permittee files MONTHLY mixed beverage GRT and mixed beverage sales
# tax returns, plus sales tax on parking and daytime beverages, plus payroll
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
    "insurance": 900,                # GL + liquor liability + park liability (estimate - revisit now
                                      # that the bar pours cocktails, not just prepackaged items)
    "water_bill": 150,               # estimate pending first bill
    "electric_bill": 350,            # estimate pending first bill (common-area: lights, TVs, misters, bar coolers)
    "septic": 100,                   # estimate - drainage beyond the rented porta-potty unit
    "marketing": 750,                # $500 marketing person + $150/mo ad spend
    "waste_service": 388,            # actual: porta-potty $268 (TX Disposal Systems) + dumpster $120
    "wifi_internet": 165,            # actual: StarLink
    "pos_tech_subscriptions": 120,   # actual: Clover POS
    "licenses_permits": 300,         # TABC MB permit renewal ($2,650/2yr = $110/mo) + health permit + business license
    "maintenance_reserve": 400,      # supplies/materials only, not labor (estimate)
    "property_tax": 333,             # actual: $4,000/yr bill / 12 (county assesses LAND at $300K, not the $1.4M purchase price)
    "property_tax_improvements": PROPERTY_TAX_IMPROVEMENTS_MONTHLY,  # buildout gets added to the tax roll once complete
    "accounting_tax_prep": 250,      # bookkeeping + monthly TX tax filings + annual returns (see note above)
    "loan_payment": LOAN_MONTHLY_PAYMENT,  # fixed P&I on the $500,000 bank term loan @ 10%/25yr (placeholder terms)
}
MONTHLY_NUT = sum(FIXED_COSTS.values())
ANNUAL_NUT = MONTHLY_NUT * 12

# Operating costs vs. debt service, split out of the same FIXED_COSTS dict
# (not a second source of truth - OPERATING_FIXED_COSTS is just FIXED_COSTS
# minus the one financing line). NOI is defined before debt service in CRE
# terms; MONTHLY_NUT/ANNUAL_NUT (opex + debt service) remain the correct,
# unchanged denominator for the nut coverage ratio elsewhere in this file.
OPERATING_FIXED_COSTS = {k: v for k, v in FIXED_COSTS.items() if k != "loan_payment"}
MONTHLY_OPEX_NUT = sum(OPERATING_FIXED_COSTS.values())
ANNUAL_OPEX_NUT = MONTHLY_OPEX_NUT * 12
MONTHLY_DEBT_SERVICE = FIXED_COSTS["loan_payment"]
ANNUAL_DEBT_SERVICE = MONTHLY_DEBT_SERVICE * 12

# --- Multi-Year Growth ---
ANNUAL_GROWTH_RATE = 0.03        # bar traffic + truck sales growth
ANNUAL_RENT_GROWTH = 0.03        # truck rent escalation
ANNUAL_COST_INFLATION = 0.03

# --- Working Capital / Cash Reserve ---
# The cash tracker used to start from an unexplained $15,000. The reserve
# is the Sources & Uses plug (RESERVE_AND_SAFETY_CASH). Before opening, four
# months of debt service, insurance, property tax (land + improvements), and
# accounting accrue against zero revenue and are drawn from that reserve.
# Cash at open is the residual — derived, not a second constant.
PRE_OPEN_MONTHS = 4
PRE_OPEN_COST_KEYS = (
    "loan_payment",
    "insurance",
    "property_tax",
    "property_tax_improvements",
    "accounting_tax_prep",
)
PRE_OPEN_MONTHLY_BURN = sum(FIXED_COSTS[k] for k in PRE_OPEN_COST_KEYS)
PRE_OPEN_BURN = PRE_OPEN_MONTHLY_BURN * PRE_OPEN_MONTHS
OPENING_CASH_RESERVE = RESERVE_AND_SAFETY_CASH - PRE_OPEN_BURN

# --- Income Tax ---
# Texas has no state income tax, but the park's profit is still federal
# taxable income to the owner (pass-through: self-employment + federal
# income tax). 28% is a blended effective-rate ESTIMATE for profit in the
# $150K-$250K range - the real rate depends on entity structure, other
# household income, and deductions (Section 179 on the buildout, loan
# interest, etc.). Confirm with a CPA. Applied to positive taxable profit
# only (NOI minus deductible loan interest - see summarize_annual);
# pre-tax figures remain the primary operating metrics.
EFFECTIVE_INCOME_TAX_RATE = 0.28

# --- Market context ---
LOCAL_HOUSEHOLDS = 8_754
ANNUAL_COTA_VISITORS = 700_000   # 1.5M total visitors/year, 700K event-attending portion
ANNUAL_COTA_VISITOR_SPENDING = 50  # avg spend per visitor at bar/parking

# --- CRE Valuation & Returns (Section 9) ---
# Management fee and replacement reserve are variable costs (% of revenue),
# not flat dollar amounts, so they're computed per-month in calc_monthly_total
# rather than living in FIXED_COSTS. Both are REAL costs now, not a
# valuation-tab-only adjustment - a change of operator/manager would bring a
# market fee whether or not this owner charges themselves one, and a
# working F&B-adjacent property needs a real capital replacement reserve
# regardless of who's collecting it. Rates are standard commercial property
# management / FF&E reserve market ranges.
MANAGEMENT_FEE_RATE = 0.04           # % of EGI ex. utility pass-through
REPLACEMENT_RESERVE_RATE = 0.03      # % of EGI ex. utility pass-through
# Going-in AND default exit cap rate for the valuation/returns engine below.
# Both directions (implied value today, reversion value at exit) default to
# the same rate unless overridden via the dashboard sliders - a real
# cap-rate-expansion assumption is a sensitivity to run, not a baked-in view.
MARKET_CAP_RATE = 0.09
HOLD_PERIOD_YEARS = 5
SALE_COST_PCT = 0.03                 # broker + closing costs at exit
DISCOUNT_RATE = 0.10                 # NPV discount rate default
# +150bp over LOAN_INTEREST_RATE (itself a placeholder pending an actual
# bank quote) for the "Bank Case" underwriting stress test below - standard
# lender practice is to stress the rate above the point estimate, not just
# use it as given.
BANK_CASE_RATE_STRESS = 0.015
# Two equity figures, and they are not the same number.
# Property equity = capitalized basis (land + real improvements) minus the
# full loan. Total economic equity adds back the reserve cash the loan
# left in the bank, which is an asset but not real property. Dropping the
# reserve, or dropping the new improvements, is how a table stops adding up.
# EQUITY_BASIS stays the property-equity figure the levered-returns engine
# already used (capitalized basis − loan).
EQUITY_BASIS = TOTAL_CAPITALIZED_BASIS - LOAN_AMOUNT
PROPERTY_EQUITY = EQUITY_BASIS
TOTAL_ECONOMIC_EQUITY = PROPERTY_EQUITY + RESERVE_AND_SAFETY_CASH
# Land basis is what the owner paid in a related-party transfer. It is not
# market value and it is not an appraisal. Do not headline loan / this
# figure as LTV.
LAND_BASIS_IS_RELATED_PARTY = True
PROPERTY_ADDRESS = "13901 FM 812, Del Valle, TX 78617"
BORROWER_ENTITY = "JVAM Capital LLC"
OPERATING_ENTITY = "JVA Operations LLC"
PARENT_ENTITY = "JVAM Ventures LLC"
# Sep 30 guarantor preference. Disclosure only — not a lender term sheet.
# Prefer land collateral and no personal guarantee. If a product requires
# a guaranty, it is all JVAM Ventures stakeholders, not one person.
SPONSOR_PG_PREFERENCE = "no_pg_land_only"
SPONSOR_PG_FALLBACK = "all_jvam_ventures_stakeholders"
# Months between capital deployment (t=0) and the first operating month.
# Sid's Sep 30 lock: 6 months to a March 2027 open (5 months entitlement
# lag + 1 month post-permit build), replacing the old 4-month construction
# constant. This is still a TIMING correction for IRR/NPV only. It does not
# model a draw schedule, capitalized interest, or a developer fee. The
# 4-month pre-open cash burn (PRE_OPEN_BURN) is the operating-cost clock
# and is not added again here. Sid's narrower land-carry estimate
# (tax + insurance × 6 months) is a different, still-unapplied draft — it
# is not stacked on top of PRE_OPEN_BURN.
CONSTRUCTION_PERIOD_MONTHS = TIME_TO_OPEN_MONTHS


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
                       share_rate=None, avg_sales=None, occupancy=None,
                       event_month_boost=0.0):
    """
    Food truck income: pad rent + revenue share.
    Rent is not seasonal (monthly agreements); the revenue-share portion
    follows bar-traffic seasonality since truck sales track park foot traffic.
    `occupancy` (0-1) is an expected-value haircut for vendor vacancy/churn -
    applied to both rent and revenue share, since an empty slot earns neither.

    `event_month_boost` (0.0-COTA_TRUCK_BOOST_MAX) is the COTA-impact-slider
    driven bump for months with an event on the calendar and the slider
    pushed past its baseline position (see COTA_TRUCK_BOOST_MAX) - it lifts
    per-truck sales directly and closes the vacancy gap toward full
    occupancy proportionally, rather than pushing occupancy past 1.0.
    Zero by default, so existing callers are unaffected.
    """
    max_slots = slots if slots is not None else TRUCK_SLOTS
    rent = pad_rent if pad_rent is not None else TRUCK_PAD_RENT
    share = share_rate if share_rate is not None else TRUCK_REV_SHARE_RATE
    sales = avg_sales if avg_sales is not None else TRUCK_AVG_MONTHLY_SALES
    occ = occupancy if occupancy is not None else TRUCK_OCCUPANCY
    if event_month_boost:
        occ = occ + (1.0 - occ) * event_month_boost
        sales = sales * (1 + event_month_boost)

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
    """Evening container bar (draft + canned beer, shots, cocktails) monthly
    revenue with seasonality, sports
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
                            impact_multiplier=1.0):
    """
    COTA event weekends: paid parking + bar uplift + daytime-beverage
    uplift. Parking and the beverage uplift are summed day-by-day using
    each tier's daily_occupancy curve (lighter early days, peak on the
    marquee day) rather than one flat rate x days. The beverage uplift is
    derived directly from that same parking attendance (cars x
    PEOPLE_PER_CAR x attach rate x avg price) rather than a separate
    hardcoded per-tier number - a packed event-day parking lot obviously
    sells more water/soda/coffee than a normal day, and this ties that
    directly to the crowd size the model already computes for parking.
    event_list: list of tier keys, e.g. ["tier1_f1", "tier3_concert"].

    `impact_multiplier` scales every total (including incremental_cost -
    a bigger event needs more staffing too) uniformly: 0.0 zeroes COTA out
    entirely regardless of the calendar passed in, 1.0 (default) is
    unchanged/baseline behavior, values above 1.0 amplify it. See
    COTA_IMPACT_MULTIPLIER_DEFAULT for the dashboard slider mapping.
    """
    spaces = parking_spaces if parking_spaces is not None else EVENT_PARKING_SPACES
    bev_rate = (daytime_beverage_attach_rate if daytime_beverage_attach_rate is not None
                else DAYTIME_BEVERAGE_ATTACH_RATE)
    bev_price = (daytime_beverage_avg_price if daytime_beverage_avg_price is not None
                 else DAYTIME_BEVERAGE_AVG_PRICE)
    if not event_list or impact_multiplier <= 0:
        return {"parking": 0, "bar_uplift": 0, "daytime_bev_uplift": 0,
                "gross": 0, "incremental_cost": 0, "net": 0}

    total_parking = 0
    total_bar = 0
    total_daytime_bev = 0
    total_cost = 0
    for tier_key in event_list:
        tier = COTA_EVENT_TIERS.get(tier_key, COTA_EVENT_TIERS["tier3_gt_transam"])
        for day_occupancy in tier["daily_occupancy"]:
            cars = int(spaces * day_occupancy)
            total_parking += cars * tier["parking_price"]
            attendees = cars * PEOPLE_PER_CAR
            total_daytime_bev += attendees * bev_rate * bev_price
        total_bar += tier["bar_uplift_per_weekend"]
        total_cost += tier["incremental_cost"]

    total_parking *= impact_multiplier
    total_bar *= impact_multiplier
    total_daytime_bev *= impact_multiplier
    total_cost *= impact_multiplier

    gross = total_parking + total_bar + total_daytime_bev
    return {"parking": total_parking, "bar_uplift": total_bar,
            "daytime_bev_uplift": total_daytime_bev, "gross": gross,
            "incremental_cost": total_cost, "net": gross - total_cost}


def event_days(event_list):
    """Sellable days on the given tier list (one entry per daily_occupancy slot)."""
    days = 0
    for tier_key in event_list or []:
        tier = COTA_EVENT_TIERS.get(tier_key)
        if tier:
            days += len(tier["daily_occupancy"])
    return days


def calc_scheduled_labor(event_list, cost_inflation_mult=1.0):
    """Cash wages for the month. Lodging is not included.

    Daytime attendant hours are the beverage window minus the evening bar
    (they do not both get paid for the same evening hour). Overtime is a
    flat allowance on hourly wages. The manager salary is 1/12 of
    MANAGER_ANNUAL_SALARY. Employer burden applies to the whole cash wage
    bill. cost_inflation_mult scales every wage line and the burden; it
    must not be applied to the loan payment.
    """
    days = WEEKDAY_DAYS_PER_MONTH + WEEKEND_DAYS_PER_MONTH
    daytime_hours = max(0.0, DAYTIME_BEVERAGE_HOURS_PER_DAY - BAR_HOURS_PER_DAY)
    mult = cost_inflation_mult
    daytime_wages = days * daytime_hours * DAYTIME_ATTENDANT_WAGE * mult
    evening_wages = days * BAR_HOURS_PER_DAY * EVENING_BARTENDER_WAGE * mult
    extra_wages = (event_days(event_list) * EVENT_EXTRA_HOURS_PER_DAY
                   * EVENT_EXTRA_WAGE * mult)
    hourly = daytime_wages + evening_wages + extra_wages
    overtime = hourly * OVERTIME_ALLOWANCE_RATE
    manager = (MANAGER_ANNUAL_SALARY / 12) * mult
    labor_wages = hourly + overtime + manager
    return {
        "daytime_wages": daytime_wages,
        "evening_wages": evening_wages,
        "event_extra_wages": extra_wages,
        "overtime_allowance": overtime,
        "manager_salary": manager,
        "labor_wages": labor_wages,
        "payroll_burden": labor_wages * EMPLOYER_PAYROLL_BURDEN_RATE,
    }


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
                       cota_impact_multiplier=1.0,
                       cost_inflation_mult=1.0):
    """
    Full monthly calculation across all streams:
      1. Food truck rent+share  4. Seasonal watch parties
      2. Evening bar            5. Utility pass-through (net zero)
      3. COTA events            6. All-day beverages (soda/juice/water/coffee)
    Returns detailed breakdown dict.

    `cota_impact_multiplier` (default 1.0 = today's baseline calendar) is
    the dashboard's "COTA Event Impact" slider: 0.0 zeroes every COTA
    revenue/cost line as if the event calendar didn't exist; values above
    1.0 amplify it AND, in months with events on the calendar, spill over
    into extra food-truck sales/occupancy (COTA_TRUCK_BOOST_MAX) - a
    high-performing COTA weekend pulls in more than just parking and bar
    customers.
    """
    if cota_events is not None:
        event_list = cota_events
    else:
        event_list = COTA_EVENTS_BY_MONTH.get(month, [])

    # Extra truck traffic only kicks in once the slider is pushed past
    # baseline (multiplier > 1.0), and only in months with an event.
    event_month_boost = (max(0.0, cota_impact_multiplier - 1.0) * COTA_TRUCK_BOOST_MAX
                         if event_list else 0.0)

    trucks = calc_truck_revenue(month, year_month, truck_slots, truck_rent,
                                truck_share_rate, truck_avg_sales, truck_occupancy,
                                event_month_boost)
    bar_rev = calc_bar_revenue(weekday_customers, weekend_customers, month,
                               year_month, avg_check)
    seasonal_rev = calc_seasonal_event_revenue(month, year_month, seasonal_pct)
    daytime_bev_rev = calc_daytime_beverage_revenue(
        trucks["truck_total_sales"], year_month,
        daytime_beverage_attach_rate, daytime_beverage_avg_price)

    cota = calc_cota_event_revenue(
        event_list, daytime_beverage_attach_rate=daytime_beverage_attach_rate,
        daytime_beverage_avg_price=daytime_beverage_avg_price,
        impact_multiplier=cota_impact_multiplier)

    utilities = calc_utility_passthrough(trucks["trucks"])

    total_gross = (trucks["gross"] + bar_rev + seasonal_rev
                   + cota["gross"] + utilities["billed"] + daytime_bev_rev)

    # Variable costs apply to bar-like (alcohol) and daytime beverage
    # (non-alcohol) revenue SEPARATELY - each has a different tax treatment
    # and COGS rate. Each bucket folds in its own COTA uplift (bar_uplift /
    # daytime_bev_uplift) for cost-rate purposes, same as bar_like always has.
    bar_like = bar_rev + cota["bar_uplift"] + seasonal_rev
    daytime_bev_like = daytime_bev_rev + cota["daytime_bev_uplift"]
    cogs = bar_like * COGS_RATE
    grt, mb_sales_tax = alcohol_taxes_on_inclusive_receipts(bar_like)
    daytime_bev_cogs = daytime_bev_like * DAYTIME_BEVERAGE_COGS_RATE
    daytime_bev_tax = daytime_bev_like * DAYTIME_BEVERAGE_SALES_TAX_RATE
    bar_variable_costs = cogs + grt + mb_sales_tax
    daytime_bev_variable_costs = daytime_bev_cogs + daytime_bev_tax
    all_bev_rev = bar_like + daytime_bev_like

    labor = calc_scheduled_labor(event_list, cost_inflation_mult)
    labor_wages = labor["labor_wages"]
    payroll_burden = labor["payroll_burden"]
    cc_processing = all_bev_rev * CC_PROCESSING_RATE * CC_CARD_USAGE_RATE
    shrinkage = (bar_like * COGS_RATE * SHRINKAGE_RATE
                 + daytime_bev_like * DAYTIME_BEVERAGE_COGS_RATE * SHRINKAGE_RATE)

    gross_margin = (bar_like * (1 - VARIABLE_COST_RATE)
                     + daytime_bev_like * (1 - DAYTIME_BEVERAGE_VARIABLE_COST_RATE))
    bev_net = (gross_margin - labor_wages - payroll_burden
               - cc_processing - shrinkage)
    parking_upkeep = cota["parking"] * PARKING_UPKEEP_RATE
    parking_sales_tax = _inclusive_sales_tax(cota["parking"], PARKING_SALES_TAX_RATE)
    parking_net = cota["parking"] - parking_upkeep - parking_sales_tax

    # Real estate vs. operating-business segment CONTRIBUTION (pre-shared-
    # overhead - management fee, replacement reserve, and per-event COTA
    # staffing costs apply to the consolidated property, not to either
    # segment individually, so they're not allocated between the two here).
    real_estate_contribution = trucks["net"] + parking_net + utilities["net"]
    business_contribution = bev_net

    # Management fee + replacement reserve: real, variable operating costs
    # (market-rate % of EGI), not a valuation-tab-only adjustment - a change
    # of manager would bring a market fee regardless of this owner's in-kind
    # arrangement, and a working F&B property needs a real capital reserve.
    # Excludes the utility pass-through (net-zero by design; a fee on wash
    # revenue would be economically meaningless).
    egi_ex_utility = total_gross - utilities["billed"]
    management_fee = egi_ex_utility * MANAGEMENT_FEE_RATE
    replacement_reserve = egi_ex_utility * REPLACEMENT_RESERVE_RATE

    total_net_before_fixed = (real_estate_contribution + business_contribution
                              - cota["incremental_cost"]
                              - management_fee - replacement_reserve)
    # Each operating fixed line inflates; the loan payment does not.
    opex_charged = MONTHLY_OPEX_NUT * cost_inflation_mult
    noi = total_net_before_fixed - opex_charged   # TRUE NOI - before debt service
    net_cash_flow = noi - MONTHLY_DEBT_SERVICE    # NOI after debt service (pre-tax)

    # "Nut Coverage Ratio" plays the role DSCR played when there was a loan:
    # how many times over does operating income before fixed overhead cover
    # the fixed monthly nut (opex + debt service)? Formula is unchanged -
    # it just now reflects the management fee/reserve deduction automatically
    # via the lower total_net_before_fixed.
    monthly_nut_charged = opex_charged + MONTHLY_DEBT_SERVICE
    nut_coverage = (total_net_before_fixed / monthly_nut_charged
                    if monthly_nut_charged > 0 else 0)

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
        "seasonal_revenue": seasonal_rev,
        "cota_parking": cota["parking"],
        "cota_bar_uplift": cota["bar_uplift"],
        "cota_daytime_bev_uplift": cota["daytime_bev_uplift"],
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
        "labor_wages": labor_wages,
        "daytime_wages": labor["daytime_wages"],
        "evening_wages": labor["evening_wages"],
        "event_extra_wages": labor["event_extra_wages"],
        "overtime_allowance": labor["overtime_allowance"],
        "manager_salary": labor["manager_salary"],
        "payroll_burden": payroll_burden,
        "opex_charged": opex_charged,
        "cc_processing": cc_processing,
        "shrinkage": shrinkage,
        "management_fee": management_fee,
        "replacement_reserve": replacement_reserve,
        "real_estate_contribution": real_estate_contribution,
        "business_contribution": business_contribution,
        "fixed_costs": monthly_nut_charged,
        "total_net_before_fixed": total_net_before_fixed,
        "noi": noi,
        "monthly_nut_coverage": nut_coverage,
        "net_cash_flow": net_cash_flow,
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
                          cota_impact_multiplier=1.0,
                          cost_inflation_mult=1.0):
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
            cota_impact_multiplier, cost_inflation_mult,
        )
        months.append(result)

    annual = summarize_annual(months, loan_year=year)
    return months, annual


def summarize_annual(months, loan_year=1):
    """Build the annual summary dict from 12 monthly results.
    Includes after-tax views: income_tax applies EFFECTIVE_INCOME_TAX_RATE
    to taxable profit, which is NOI minus the loan's INTEREST portion for
    that year only - loan principal is not a deductible business expense,
    only interest is (total_net_cash, by contrast, is cash flow after the
    full P&I payment, since principal is a real cash outflow even though
    it isn't deductible). `loan_year` (1-based) picks which year of the
    loan's amortization schedule to pull the interest/principal split from;
    `run_annual_projection` passes its own `year` argument through here
    directly. For standalone calls where `year` means "ramp-state" rather
    than a true loan-calendar-year (1 = ramp, 2 = generic steady-state),
    this is a documented approximation - see run_multi_year_projection for
    the exact per-calendar-year version. Pre-tax NOI remains the primary
    operating metric; fcf_yield/after_tax_fcf_yield are the owner-facing
    "return on what I actually spent" figures against TOTAL_PROJECT_COST
    (buildout only) - see calc_valuation_and_leverage() in Section 9 for
    the land-inclusive CRE yield-on-cost metric."""
    total_noi = sum(m["noi"] for m in months)
    total_net_cash = sum(m["net_cash_flow"] for m in months)
    interest_paid = _amortization_interest_for_year(
        LOAN_AMOUNT, LOAN_INTEREST_RATE, LOAN_TERM_YEARS, loan_year)
    taxable_profit = max(0.0, total_noi - interest_paid)
    income_tax = taxable_profit * EFFECTIVE_INCOME_TAX_RATE
    after_tax_noi = total_net_cash - income_tax
    return {
        "total_gross": sum(m["total_gross_revenue"] for m in months),
        "total_trucks": sum(m["truck_gross"] for m in months),
        "total_truck_rent": sum(m["truck_rent"] for m in months),
        "total_truck_share": sum(m["truck_share"] for m in months),
        "total_bar": sum(m["bar_revenue"] for m in months),
        "total_daytime_beverage": sum(m["daytime_beverage_revenue"] for m in months),
        "total_seasonal": sum(m["seasonal_revenue"] for m in months),
        "total_cota_parking": sum(m["cota_parking"] for m in months),
        "total_cota_bar": sum(m["cota_bar_uplift"] for m in months),
        "total_cota_daytime_bev": sum(m["cota_daytime_bev_uplift"] for m in months),
        "total_cota_parking_upkeep": sum(m["cota_parking_upkeep"] for m in months),
        "total_cota_parking_sales_tax": sum(m["cota_parking_sales_tax"] for m in months),
        "total_cota_cost": sum(m["cota_incremental_cost"] for m in months),
        "total_utility_billed": sum(m["utility_billed"] for m in months),
        "total_utility_cost": sum(m["utility_cost"] for m in months),
        "total_labor_wages": sum(m["labor_wages"] for m in months),
        "total_daytime_wages": sum(m["daytime_wages"] for m in months),
        "total_evening_wages": sum(m["evening_wages"] for m in months),
        "total_event_extra_wages": sum(m["event_extra_wages"] for m in months),
        "total_overtime_allowance": sum(m["overtime_allowance"] for m in months),
        "total_manager_salary": sum(m["manager_salary"] for m in months),
        "total_payroll_burden": sum(m["payroll_burden"] for m in months),
        "total_opex": sum(m["opex_charged"] for m in months),
        "total_cc_processing": sum(m["cc_processing"] for m in months),
        "total_shrinkage": sum(m["shrinkage"] for m in months),
        "total_cogs": sum(m["cogs"] for m in months),
        "total_grt": sum(m["grt"] for m in months),
        "total_mb_sales_tax": sum(m["mb_sales_tax"] for m in months),
        "total_daytime_beverage_cogs": sum(m["daytime_beverage_cogs"] for m in months),
        "total_daytime_beverage_tax": sum(m["daytime_beverage_tax"] for m in months),
        "total_management_fee": sum(m["management_fee"] for m in months),
        "total_replacement_reserve": sum(m["replacement_reserve"] for m in months),
        "total_real_estate_contribution": sum(m["real_estate_contribution"] for m in months),
        "total_business_contribution": sum(m["business_contribution"] for m in months),
        "total_noi": total_noi,
        "total_net_cash": total_net_cash,
        "loan_interest_paid": interest_paid,
        "income_tax": income_tax,
        "after_tax_noi": after_tax_noi,
        "after_tax_fcf_yield": after_tax_noi / TOTAL_PROJECT_COST,
        "avg_monthly_nut_coverage": sum(m["monthly_nut_coverage"] for m in months) / 12,
        "min_monthly_nut_coverage": min(m["monthly_nut_coverage"] for m in months),
        "max_monthly_nut_coverage": max(m["monthly_nut_coverage"] for m in months),
        "annual_nut": sum(m["fixed_costs"] for m in months),
        "fcf_yield": total_net_cash / TOTAL_PROJECT_COST,
    }


def run_multi_year_projection(base_weekday_customers=None, base_weekend_customers=None,
                              years=3, base_check=None,
                              truck_slots=None, truck_rent=None,
                              truck_share_rate=None, truck_avg_sales=None,
                              truck_occupancy=None, seasonal_pct=1.0,
                              daytime_beverage_attach_rate=None,
                              daytime_beverage_avg_price=None,
                              cota_impact_multiplier=1.0):
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
            cota_impact_multiplier=cota_impact_multiplier,
            cost_inflation_mult=cost_mult,
        )

        # Inflation is already inside each opex line and each wage line.
        # cost_inflation_adj reports that dollar increase. It is not a second
        # haircut, and it never includes the loan payment.
        wage_bill = annual["total_labor_wages"] + annual["total_payroll_burden"]
        if cost_mult == 1:
            annual["cost_inflation_adj"] = 0.0
        else:
            annual["cost_inflation_adj"] = (
                (annual["total_opex"] - ANNUAL_OPEX_NUT)
                + wage_bill * (1 - 1 / cost_mult)
            )

        annual["year"] = yr
        annual["growth_mult"] = growth
        all_years.append((yr, months, annual))

    return all_years


# =============================================================================
# SECTION 4: MONTE CARLO SIMULATION
# =============================================================================

# What the simulator actually draws. Independent draws (no correlations),
# so the joint downside tail is fatter than this distribution shows.
# Reproducible only for a stated seed — an undisclosed run is not.
MONTE_CARLO_DEFAULT_SEED = 42
MONTE_CARLO_DRAWS_ARE_INDEPENDENT = True
MONTE_CARLO_SPEC = (
    {"name": "weekday_customers", "distribution": "gaussian", "sigma": 5, "low": 5, "high": 50},
    {"name": "weekend_customers", "distribution": "gaussian", "sigma": 12, "low": 15, "high": 100},
    {"name": "avg_check", "distribution": "gaussian", "sigma": 1.0, "low": 5.0, "high": 20.0},
    {"name": "truck_avg_monthly_sales", "distribution": "gaussian", "sigma": 5_000, "low": 10_000, "high": 35_000},
    {"name": "truck_occupancy", "distribution": "gaussian", "sigma": 0.08, "low": 0.60, "high": 1.0},
    {"name": "seasonal_pct", "distribution": "gaussian", "sigma": 0.2, "low": 0.4, "high": 1.5},
    {"name": "daytime_beverage_attach_rate", "distribution": "gaussian", "sigma": 0.08, "low": 0.10, "high": 0.60},
    # Repeated entries are weights, not a uniform draw over the unique values.
    {"name": "n_concerts", "distribution": "weighted_discrete", "values": (2, 3, 3, 4, 4, 4, 5, 6)},
    {"name": "n_festivals", "distribution": "weighted_discrete", "values": (1, 2, 2, 2, 3)},
    {"name": "n_gt", "distribution": "weighted_discrete", "values": (0, 1, 1, 2, 2)},
    {"name": "truck_slots", "distribution": "held_fixed"},
    {"name": "truck_pad_rent", "distribution": "held_fixed"},
    {"name": "truck_rev_share", "distribution": "held_fixed"},
    {"name": "cota_impact_multiplier", "distribution": "held_fixed"},
)


def _mc_spec(name):
    return next(row for row in MONTE_CARLO_SPEC if row["name"] == name)


def _mc_gauss(name, mean):
    spec = _mc_spec(name)
    return max(spec["low"], min(spec["high"], random.gauss(mean, spec["sigma"])))


def run_monte_carlo(n_simulations=10_000, seed=MONTE_CARLO_DEFAULT_SEED,
                    base_weekday_customers=None, base_weekend_customers=None,
                    base_check=None, base_truck_rent=None, base_truck_share=None,
                    base_truck_occupancy=None, base_seasonal_pct=1.0,
                    base_truck_slots=None, base_truck_avg_sales=None,
                    base_daytime_beverage_attach_rate=None,
                    base_daytime_beverage_avg_price=None,
                    base_cota_impact_multiplier=1.0):
    """
    Randomized Year 1 scenarios. Varies: truck sales, truck occupancy
    (vacancy), weekday/weekend bar traffic and check, COTA event mix,
    seasonal event strength, and the daytime-beverage attach rate.
    Truck COUNT, rent, and revenue share are held FIXED across every
    simulation (built slots + contracted terms, not uncertain) - lease-up
    risk is expressed through occupancy instead. The COTA impact multiplier
    is also held fixed at whatever the dashboard slider is set to (not
    randomized) - the event MIX is already randomized below independently.

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

    random.seed(seed)
    results = []

    for _ in range(n_simulations):
        wd_custs = _mc_gauss("weekday_customers", _wd_custs)
        we_custs = _mc_gauss("weekend_customers", _we_custs)
        # Clamp matches the dashboard's Avg Check slider range (5-20).
        check = _mc_gauss("avg_check", _check)
        truck_sales = _mc_gauss("truck_avg_monthly_sales", _tsales)
        # Truck vacancy is the real fleet risk (6-mo contracts bound it):
        # randomize occupancy rather than the integer slot count.
        truck_occ = _mc_gauss("truck_occupancy", _tocc)
        seasonal_pct = _mc_gauss("seasonal_pct", base_seasonal_pct)
        # The beverage attach rate is the least-validated number in the
        # whole model (no operating history at all), so it gets a wide band
        # rather than being pinned.
        dbev_attach = _mc_gauss("daytime_beverage_attach_rate", _dbev_attach)

        # COTA mix: big 4 fixed, concerts/festivals/GT variable.
        # Draws are independent of each other and of the gaussians above.
        n_concerts = random.choice(_mc_spec("n_concerts")["values"])
        n_festivals = random.choice(_mc_spec("n_festivals")["values"])
        n_gt = random.choice(_mc_spec("n_gt")["values"])
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
            cota_impact_multiplier=base_cota_impact_multiplier,
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
# The daytime-beverage attach rate ALSO moves with the scenario. A world
# where the bar is failing and vendors are churning is not a world where
# the same share of remaining truck customers still buys a soda - holding
# that rate flat while every other lever degrades would quietly make the
# downside cases too kind.
SCENARIOS = {
    "Worst Case": {
        "desc": "2 trucks (severe vendor attrition), 70% occ, weak bar, no COTA, weak attach rate",
        "weekday_customers": 12, "weekend_customers": 34, "avg_check": 9.48,
        "truck_slots": 2, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 0.70,
        "daytime_beverage_attach_rate": 0.20,
        "cota_events": {m: [] for m in range(1, 13)},
        "seasonal_pct": 0.5,
    },
    "Stress Test": {
        "desc": "3 trucks (partial vendor attrition), 78% occ, soft bar, big-3 COTA events only",
        "weekday_customers": 15, "weekend_customers": 43, "avg_check": 10.24,
        "truck_slots": 3, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 0.78,
        "daytime_beverage_attach_rate": 0.25,
        "cota_events": {m: [] for m in range(1, 13)},  # filled below
        "seasonal_pct": 0.75,
    },
    "Conservative": {
        "desc": "3 trucks (partial vendor attrition), 83% occ, full COTA calendar",
        "weekday_customers": 17, "weekend_customers": 48, "avg_check": 10.88,
        "truck_slots": 3, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 0.83,
        "daytime_beverage_attach_rate": 0.30,
        "cota_events": None,
        "seasonal_pct": 0.75,
    },
    "Base Case": {
        "desc": "4 trucks (all built hubs leased) at $500 + 10%, 85% occ, 20 weekday / 58 weekend bar customers",
        "weekday_customers": BAR_WEEKDAY_CUSTOMERS, "weekend_customers": BAR_WEEKEND_CUSTOMERS, "avg_check": BAR_AVG_CHECK,
        "truck_slots": TRUCK_SLOTS, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": TRUCK_OCCUPANCY,
        "daytime_beverage_attach_rate": DAYTIME_BEVERAGE_ATTACH_RATE,
        "cota_events": None,
        "seasonal_pct": 1.0,
    },
    "Upside": {
        "desc": "6 trucks (hypothetical future expansion, not currently budgeted), full occ, strong evening bar",
        "weekday_customers": 28, "weekend_customers": 82, "avg_check": 12.66,
        "truck_slots": 6, "truck_rent": TRUCK_PAD_RENT, "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": 1.0,
        "daytime_beverage_attach_rate": 0.45,
        "cota_events": None,
        "seasonal_pct": 1.25,
    },
    # Timing case, not a demand case. It is intentionally NOT part of the
    # worst-to-best ordering test.
    "Delayed Opening (misses F1)": {
        "desc": ("Base-case demand, but the open slips past the October F1 "
                 "weekend, so Year 1 has no F1 parking or F1 bar uplift. "
                 "Percentage rent is still non-contractual; no leases are executed."),
        "weekday_customers": BAR_WEEKDAY_CUSTOMERS,
        "weekend_customers": BAR_WEEKEND_CUSTOMERS,
        "avg_check": BAR_AVG_CHECK,
        "truck_slots": TRUCK_SLOTS,
        "truck_rent": TRUCK_PAD_RENT,
        "truck_share_rate": TRUCK_REV_SHARE_RATE,
        "truck_occupancy": TRUCK_OCCUPANCY,
        "daytime_beverage_attach_rate": DAYTIME_BEVERAGE_ATTACH_RATE,
        "cota_events": {
            m: [t for t in COTA_EVENTS_BY_MONTH.get(m, []) if t != "tier1_f1"]
            for m in range(1, 13)
        },
        "seasonal_pct": 1.0,
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
    # zeroes that stream too - it's driven by truck traffic (not weekday/
    # weekend bar customers), so it wouldn't zero out otherwise.
    months, no_bar = run_annual_projection(
        0, 0, avg_check=0,
        cota_events_override={m: [] for m in range(1, 13)},
        seasonal_pct=0.0, daytime_beverage_attach_rate=0.0,
    )

    # View 2: minimum EVENING bar traffic for nut-coverage targets (weak
    # truck base: 4 trucks @ $600 + 5%, no COTA, no daytime beverages -
    # daytime_beverage_attach_rate=0 isolates what the alcohol bar needs to
    # contribute, same as View 1, since that revenue is tied to truck
    # traffic rather than the bar traffic this test is sizing). Searches a
    # single multiplier applied to both weekday and weekend traffic
    # together, holding their ratio fixed at the "weak" Worst Case split
    # (12 weekday / 34 weekend). The check is the Worst Case check, which
    # was rescaled with the four-item menu. The old $7.45 figure is a
    # retired pre-cocktail price and must not drive this search.
    weak_weekday, weak_weekend = 12, 34
    weak_check = SCENARIOS["Worst Case"]["avg_check"]
    targets = [("Break-even", 1.0), ("Comfortable", 1.25),
               ("Strong", 1.50), ("Excellent", 2.0)]
    # Hard ceiling. A target the search cannot reach used to come back as
    # this ceiling and print a customer count that was not a break-even.
    search_ceiling = 4.0
    custs_results = []
    for label, target in targets:
        _, at_ceiling = run_annual_projection(
            weak_weekday * search_ceiling, weak_weekend * search_ceiling,
            avg_check=weak_check,
            truck_slots=4, truck_rent=600, truck_share_rate=0.05,
            cota_events_override={m: [] for m in range(1, 13)},
            seasonal_pct=0.0, daytime_beverage_attach_rate=0.0,
        )
        if at_ceiling["avg_monthly_nut_coverage"] < target:
            custs_results.append({
                "label": label,
                "target": target,
                "reachable": False,
                "weekday_customers": None,
                "weekend_customers": None,
                "coverage_at_ceiling": at_ceiling["avg_monthly_nut_coverage"],
                "ceiling_multiple": search_ceiling,
            })
            continue
        lo, hi = 0.0, search_ceiling
        for _ in range(25):
            mid = (lo + hi) / 2
            _, ann = run_annual_projection(
                weak_weekday * mid, weak_weekend * mid, avg_check=weak_check,
                truck_slots=4, truck_rent=600, truck_share_rate=0.05,
                cota_events_override={m: [] for m in range(1, 13)},
                seasonal_pct=0.0, daytime_beverage_attach_rate=0.0,
            )
            if ann["avg_monthly_nut_coverage"] >= target:
                hi = mid
            else:
                lo = mid
        custs_results.append({
            "label": label,
            "target": target,
            "reachable": True,
            "weekday_customers": round(weak_weekday * hi),
            "weekend_customers": round(weak_weekend * hi),
            "coverage_at_ceiling": at_ceiling["avg_monthly_nut_coverage"],
            "ceiling_multiple": search_ceiling,
        })

    if verbose:
        print(f"\n{'=' * 70}")
        print("  BREAK-EVEN ANALYSIS")
        print(f"{'=' * 70}")
        print(f"\n  Monthly Nut (all fixed operating costs): ${MONTHLY_NUT:>10,.0f}")
        print(f"  (Includes ${LOAN_MONTHLY_PAYMENT:,.0f}/mo bank loan payment, {LOAN_INTEREST_RATE:.1%}/{LOAN_TERM_YEARS}yr)")
        print(f"\n  1. ZERO-BAR TEST (4 trucks, no bar, no COTA):")
        print(f"     Annual NOI:  ${no_bar['total_noi']:>12,.0f}")
        print(f"     Nut Coverage: {no_bar['avg_monthly_nut_coverage']:>11.2f}x")
        verdict = "COVERS THE NUT" if no_bar["avg_monthly_nut_coverage"] >= 1.0 else "DOES NOT COVER"
        print(f"     -> Truck rent alone {verdict}")
        print(f"\n  2. MIN BAR TRAFFIC BY NUT-COVERAGE TARGET")
        print(f"     (weak base: 4 trucks @ $600 + 5%, ${weak_check:.2f} check, "
              "Year 1 ramp, no COTA, scheduled labor still paid)")
        for row in custs_results:
            if row["reachable"]:
                print(f"     {row['label']:<14} ({row['target']:.2f}x): "
                      f"{row['weekday_customers']:>4} weekday / "
                      f"{row['weekend_customers']:>4} weekend bar customers")
            else:
                print(f"     {row['label']:<14} ({row['target']:.2f}x): "
                      f"UNREACHABLE at {row['ceiling_multiple']:.1f}x traffic "
                      f"(coverage there is {row['coverage_at_ceiling']:.2f}x)")

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
                   + ann["total_cota_daytime_bev"])
        print(f"  {pct:>13}% ${cota_rev:>11,.0f} {ann['avg_monthly_nut_coverage']:>8.2f}x")


# =============================================================================
# SECTION 7: CASH RESERVE + LOAN AMORTIZATION TRACKER
# =============================================================================

def run_cash_reserve_tracker(all_years=None, verbose=True):
    """Track working-capital balance month-by-month from OPENING_CASH_RESERVE,
    plus the month cumulative NOI reaches the $500K total capital deployed."""
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
            # net_cash_flow already reflects line-by-line opex and wage
            # inflation from run_multi_year_projection. Do not haircut again.
            cf = m["net_cash_flow"]
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


def run_loan_amortization_schedule(all_years=None, sweep_pct=1.0, verbose=True):
    """
    Simulate the bank loan's balance over time. The REQUIRED fixed P&I
    payment (LOAN_MONTHLY_PAYMENT) already fully amortizes the loan on its
    own per LOAN_TERM_YEARS - unlike the old revolving personal LOC, there's
    no "conservative flat assumption" to contrast against, because a
    fixed-payment amortizing loan already has a real, defined schedule.
    What's still worth simulating: `sweep_pct` (1.0 by default) of free
    cash flow BEYOND the required payment optionally sweeps to EXTRA
    principal prepayment each month, showing how much sooner the loan
    retires and how much interest is saved if the owner chooses to overpay.
    Set sweep_pct=0.0 to see the contractual schedule alone. (Caveat: many
    bank/SBA term loans restrict or penalize early prepayment - this models
    the cash-flow upside only, not any prepayment-penalty cost.)
    """
    if all_years is None:
        all_years = run_multi_year_projection()

    monthly_rate = LOAN_INTEREST_RATE / 12
    balance = LOAN_AMOUNT
    required_balance = LOAN_AMOUNT  # contractual schedule, no extra prepayment - the comparison baseline
    total_interest_paid = 0.0
    total_required_interest = 0.0
    payoff_month = None
    series = []

    for yr, months, annual in all_years:
        for m in months:
            # m["noi"] is already pre-debt-service and, for year 2+, already
            # net of inflated opex and wages. Do not haircut it again.
            noi_before_financing = m["noi"]

            if required_balance > 0.01:
                req_interest = required_balance * monthly_rate
                req_principal = min(required_balance, LOAN_MONTHLY_PAYMENT - req_interest)
                required_balance -= req_principal
                total_required_interest += req_interest

            if balance <= 0.01:
                interest, principal_payment = 0.0, 0.0
            else:
                interest = balance * monthly_rate
                scheduled_principal = min(balance, LOAN_MONTHLY_PAYMENT - interest)
                extra_available = max(0.0, noi_before_financing - LOAN_MONTHLY_PAYMENT) * sweep_pct
                extra_principal = min(balance - scheduled_principal, extra_available)
                principal_payment = scheduled_principal + extra_principal
                balance -= principal_payment
                total_interest_paid += interest

            if payoff_month is None and balance <= 0.01:
                payoff_month = (yr, m["month"])
            series.append({"year": yr, "month": m["month"],
                           "balance": max(balance, 0.0), "interest": interest,
                           "principal_payment": principal_payment})

    if verbose:
        print(f"\n{'=' * 70}")
        print("  LOAN AMORTIZATION SCHEDULE")
        print(f"{'=' * 70}")
        print(f"\n  Loan: ${LOAN_AMOUNT:,.0f} @ {LOAN_INTEREST_RATE:.1%}, {LOAN_TERM_YEARS}-year amortization")
        print(f"  Required payment: ${LOAN_MONTHLY_PAYMENT:,.0f}/mo (${LOAN_MONTHLY_PAYMENT * 12:,.0f}/yr)")
        if sweep_pct > 0:
            if payoff_month:
                print(f"  Payoff sweeping {sweep_pct:.0%} of free cash flow beyond the "
                      f"required payment to extra principal: Year {payoff_month[0]}, {MONTH_NAMES[payoff_month[1]]}")
            else:
                print(f"  Not paid off within the projection window at this sweep rate.")
            print(f"  Interest paid over the window: ${total_interest_paid:,.0f} "
                  f"(vs. ${total_required_interest:,.0f} on the required schedule alone - "
                  f"${total_required_interest - total_interest_paid:,.0f} saved)")
        else:
            print(f"  Contractual schedule only (no extra prepayment) - "
                  f"interest paid over the window: ${total_interest_paid:,.0f}")

    return {"payoff_month": payoff_month, "total_interest_paid": total_interest_paid,
            "required_schedule_interest": total_required_interest,
            "final_balance": max(balance, 0.0), "series": series}


def print_owner_summary():
    """Owner-facing summary for the bank-loan-financed food truck park + bar & beverage stand concept."""
    print(f"\n{'=' * 70}")
    print("  OWNER SUMMARY")
    print("  Food Truck Park + Bar & Beverage Stand | Del Valle, TX")
    print(f"{'=' * 70}")

    print(f"\n  STARTUP COST — FINANCED VIA $500,000 BANK TERM LOAN")
    print(f"  {'Total Project Cost:':<30} ${TOTAL_PROJECT_COST:>14,.0f}")
    print(f"  {'Loan Amount / Rate / Term:':<30} ${LOAN_AMOUNT:>10,.0f} @ {LOAN_INTEREST_RATE:.1%}, {LOAN_TERM_YEARS}yr")
    print(f"  {'Already Spent:':<30} ${ALREADY_SPENT:>14,.0f}")
    print(f"  {'Remaining to Spend:':<30} ${NEW_CASH_NEEDED:>14,.0f}")

    print(f"\n  USE OF FUNDS")
    for label, amt, status in USE_OF_FUNDS:
        print(f"  {label:<52} ${amt:>10,.0f}  [{status}]")
    print(f"  {'TOTAL':<52} ${TOTAL_PROJECT_COST:>10,.0f}")

    print(f"\n  MONTHLY OPERATING COSTS (The Nut, incl. loan payment)")
    for label, amt in FIXED_COSTS.items():
        print(f"  {label.replace('_', ' ').title():<35} ${amt:>10,.0f}")
    print(f"  {'Total Monthly Nut':<35} ${MONTHLY_NUT:>10,.0f}")
    print(f"  {'Total Annual Nut':<35} ${ANNUAL_NUT:>10,.0f}")
    print(f"  (Loan payment line is the fixed monthly P&I on a fully "
          f"amortizing ${LOAN_AMOUNT:,.0f} loan - see "
          f"run_loan_amortization_schedule() for the year-by-year "
          f"principal/interest split, and for the optional extra-"
          f"prepayment scenario.)")

    _, conservative = run_scenario_projection(SCENARIOS["Conservative"])
    _, base = run_scenario_projection(SCENARIOS["Base Case"])

    print(f"\n  PROJECTED PERFORMANCE (Year 1)")
    print(f"  {'':>25} {'Conservative':>16} {'Base Case':>16}")
    print("  " + "-" * 58)
    print(f"  {'Annual Revenue':<25} ${conservative['total_gross']:>15,.0f} ${base['total_gross']:>15,.0f}")
    print(f"  {'Management Fee (4% EGI)':<25} ${conservative['total_management_fee']:>15,.0f} ${base['total_management_fee']:>15,.0f}")
    print(f"  {'Replacement Reserve (3%)':<25} ${conservative['total_replacement_reserve']:>15,.0f} ${base['total_replacement_reserve']:>15,.0f}")
    print(f"  {'Annual NOI (pre-tax)':<25} ${conservative['total_noi']:>15,.0f} ${base['total_noi']:>15,.0f}")
    print(f"  {'  (before loan payment)':<25}")
    print(f"  {'Free Cash Flow (pre-tax)':<25} ${conservative['total_net_cash']:>15,.0f} ${base['total_net_cash']:>15,.0f}")
    print(f"  {'Est. Income Tax (28%)':<25} ${conservative['income_tax']:>15,.0f} ${base['income_tax']:>15,.0f}")
    print(f"  {'After-Tax Cash Flow':<25} ${conservative['after_tax_noi']:>15,.0f} ${base['after_tax_noi']:>15,.0f}")
    print(f"  {'FCF Yield (pre-tax)':<25} {conservative['fcf_yield']:>15.1%} {base['fcf_yield']:>15.1%}")
    print(f"  {'FCF Yield (after-tax)':<25} {conservative['after_tax_fcf_yield']:>15.1%} {base['after_tax_fcf_yield']:>15.1%}")

    print(f"\n  REVENUE STREAMS (Base Case, Year 1)")
    print(f"  {'Food Trucks (rent + share)':<32} ${base['total_trucks']:>14,.0f}")
    print(f"  {'Evening Bar (container bar)':<32} ${base['total_bar']:>14,.0f}")
    print(f"  {'All-Day Beverages (soda/juice/water/coffee)':<32} ${base['total_daytime_beverage']:>14,.0f}")
    print(f"  {'COTA Events (all)':<32} "
          f"${base['total_cota_parking'] + base['total_cota_bar'] + base['total_cota_daytime_bev']:>14,.0f}")
    print(f"  {'Seasonal Watch Parties':<32} ${base['total_seasonal']:>14,.0f}")
    print(f"  {'Utility Pass-Through (at cost)':<32} ${base['total_utility_billed']:>14,.0f}")

    print(f"\n  RISK MITIGANTS")
    print(f"  - Free cash flow beyond the required payment can be swept to "
          f"extra principal, retiring the ${LOAN_AMOUNT:,.0f} loan faster and "
          f"saving interest vs. the contractual {LOAN_TERM_YEARS}-year schedule")
    print(f"  - Land owned outright - no rent/mortgage in the nut, and "
          f"${ALREADY_SPENT:,.0f} of the total project cost is already spent")
    print(f"  - Full container bar (draft, canned, shots, cocktails) = higher "
          f"check (${BAR_AVG_CHECK:.2f}) and better blended margin than a "
          f"prepackaged-only stand")
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

# --- Depreciation: classify the real Phase 0.5 + Phase 2 buildout into
# MACRS-style classes (IRS Pub 946): 5-year for equipment/electronics/
# fixtures, 15-year for land improvements and structures (fencing,
# lighting, drainage, grading, septic, paving, the container bar shell).
# Items are looked up by label across BOTH PHASE_0_5_CAPITAL_IMPROVEMENTS
# (the historical buildout - real capital investment regardless of which
# loan financed it) and USE_OF_FUNDS (the new loan's septic/paving/
# container-bar lines). Inventory, permits, and contingency are excluded -
# not depreciable capital assets. Also excluded: the LOC-payoff item (a
# refinancing event, not a new capital asset) and Reserve & Safety Cash
# (conservative - no depreciation shield assumed for cash held back, not
# yet spent on a specific asset). All three fall into NON_DEPRECIABLE_COST
# automatically since it's derived, not a separate list to maintain.
DEPRECIATION_5YR_ITEMS = [
    "TVs", "TV Mounts", "TV encasing", "Security system",
    "Sound System / Speakers", "StarLink Internet equipment",
    "Mist Fans (pole-mounted)", "Refrigerators (bar coolers)", "Benches",
]
DEPRECIATION_15YR_ITEMS = [
    "Turf", "Sail Shades", "Gates", "Pole Lighting / String Lights",
    "Signs", "Electrical", "Plumbing", "Telephone pole",
    "Full land clearing", "Yard Multi-Purpose Poles (set & anchor)",
    "Gravel", "Trash Cans", "Storage Shed (wooden, general)",
    "Septic system installation",
    "Paved asphalt roads / internal access improvements",
    "Container Bar (full buildout)",
]
_use_of_funds_cost = {label: amt for label, amt, _ in PHASE_0_5_CAPITAL_IMPROVEMENTS + USE_OF_FUNDS}
DEPRECIABLE_BASIS_5YR = sum(_use_of_funds_cost[i] for i in DEPRECIATION_5YR_ITEMS)
DEPRECIABLE_BASIS_15YR = sum(_use_of_funds_cost[i] for i in DEPRECIATION_15YR_ITEMS)
TOTAL_DEPRECIABLE_BASIS = DEPRECIABLE_BASIS_5YR + DEPRECIABLE_BASIS_15YR
# The non-depreciable slice of the real capitalized buildout (inventory,
# permits, contingency) - i.e. TOTAL_CAPITALIZED_BASIS less land (which was
# never depreciable capital-improvement basis to begin with) less what IS
# depreciable. The LOC payoff and Reserve & Safety Cash are already
# excluded from TOTAL_CAPITALIZED_BASIS (see Section 1), so they don't leak
# into this figure either.
NON_DEPRECIABLE_COST = (TOTAL_CAPITALIZED_BASIS - LAND_PURCHASE_PRICE) - TOTAL_DEPRECIABLE_BASIS

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
# modeling when the permits line still carried the $5,300 TABC Mixed
# Beverage Permit. That permit is now obtained and paid (financed by the
# old LOC, hence inside the LOC-payoff line). The forward-looking permits
# line is the still-unpaid site, health, and access permits
# (PERMITS_AND_SOFT_COSTS), and the Sec. 195 treatment still
# applies to genuinely pre-opening spend.
# Only the genuinely pre-opening portion qualifies - inventory is
# inventory, and contingency is a budgeting buffer rather than a real
# incurred cost, so neither is included here.
STARTUP_COST_ITEMS = [
    PERMITS_AND_SOFT_COSTS_LABEL,
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
    GRT and sales tax, sales tax on parking and daytime beverages, property tax,
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
    """CLI view of the depreciation + S-corp tax strategy analysis, on Base
    Case Year 1 taxable profit by default.

    `annual_noi` here means taxable profit AFTER loan INTEREST only (a
    deductible business expense) - despite the parameter name (kept for
    backward compatibility with callers), this is NOI minus loan_interest_paid,
    NOT total_net_cash. Loan principal is a real cash outflow but is not
    tax-deductible, so total_net_cash (NOI minus the FULL principal +
    interest payment) would understate taxable profit now that debt service
    is a fixed-payment amortizing loan rather than interest-only."""
    if annual_noi is None:
        _, base = run_scenario_projection(SCENARIOS["Base Case"])
        annual_noi = base["total_noi"] - base["loan_interest_paid"]

    no_strategy = run_tax_strategy_analysis(annual_noi, apply_depreciation=False, apply_scorp=False)
    dep_only = run_tax_strategy_analysis(annual_noi, accelerated_depreciation=False, apply_scorp=False)
    scorp_only = run_tax_strategy_analysis(annual_noi, apply_depreciation=False, apply_scorp=True)
    combined = run_tax_strategy_analysis(annual_noi, accelerated_depreciation=True, apply_scorp=True)

    print(f"\n{'=' * 70}")
    print("  TAX STRATEGY ANALYSIS")
    print(f"{'=' * 70}")
    print(f"\n  Annual Taxable Profit (NOI after loan interest only): ${annual_noi:,.0f}")
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
# SECTION 9: CRE VALUATION & RETURNS ANALYSIS
# =============================================================================
# Standard commercial real estate underwriting metrics that this model didn't
# previously compute: cap-rate valuation, LTC/LTV, debt yield, and a full
# unlevered/levered returns engine (IRR, NPV, equity multiple, cash-on-cash).
# These are ADDITIONAL to the existing owner-facing metrics elsewhere in this
# file (fcf_yield, monthly_nut_coverage, etc.), which keep their original
# meaning and denominator (TOTAL_PROJECT_COST, buildout only) - the functions
# here use TOTAL_CAPITALIZED_BASIS (land + buildout), the technically correct
# basis for a CRE yield-on-cost or valuation figure. Surfaced in the
# dashboard's dedicated "CRE Investment Summary" tab.

def equity_schedule_rows():
    """Capital bridge. Subtotal rows equal the sum of the rows that feed them.

    Property equity is capitalized basis minus the loan. Total economic
    equity adds the reserve cash, which is not a real-property asset.
    Land is a related-party transfer basis, not an appraised value.
    """
    new_capex = sum(
        a for label, a, _ in USE_OF_FUNDS if label not in _LOC_PAYOFF_AND_RESERVE_LABELS)
    rows = [
        {"line": "Land (related-party transfer basis, not an appraisal)",
         "amount": LAND_PURCHASE_PRICE, "role": "component"},
        {"line": "Phase 0.5 capital improvements",
         "amount": PHASE_0_5_TOTAL, "role": "component"},
        {"line": "New construction and soft costs (this loan)",
         "amount": new_capex, "role": "component"},
        {"line": "Capitalized basis",
         "amount": TOTAL_CAPITALIZED_BASIS, "role": "subtotal"},
        {"line": "Less: bank loan",
         "amount": -LOAN_AMOUNT, "role": "component"},
        {"line": "Property equity",
         "amount": PROPERTY_EQUITY, "role": "subtotal"},
        {"line": "Reserve cash (sources & uses; not capitalized)",
         "amount": RESERVE_AND_SAFETY_CASH, "role": "component"},
        {"line": "Total economic equity",
         "amount": TOTAL_ECONOMIC_EQUITY, "role": "total"},
    ]
    return rows


def calc_revenue_mix(annual):
    """Stabilized (or any year) revenue mix, computed once so labels can't drift.

    Property + parking includes contractual pad rent, non-contractual
    percentage rent, and transactional event parking. Shares are of total
    gross revenue, which is the denominator behind the ~50.4% / ~4.3% figures.
    """
    gross = annual["total_gross"]
    pad = annual["total_truck_rent"]
    share = annual["total_truck_share"]
    parking = annual["total_cota_parking"]
    property_and_parking = pad + share + parking

    def _share(part):
        return part / gross if gross else 0.0

    return {
        "gross": gross,
        "contractual_pad_rent": pad,
        "noncontractual_percentage_rent": share,
        "transactional_event_parking": parking,
        "property_and_parking": property_and_parking,
        "property_and_parking_share": _share(property_and_parking),
        "contractual_pad_rent_share": _share(pad),
        "percentage_rent_label": "non-contractual — no executed vendor leases",
        "event_parking_label": "transactional event parking, not contractual rent",
        "pad_rent_label": "contractual pad rent (intended terms; leases not executed)",
    }


# Real-property income and the bar are not the same collateral. These are
# indications pending an independent appraisal, not a headline LTV.
PROPERTY_INCOME_CAP_RATE = 0.085
GOING_CONCERN_EBITDA_MULTIPLE = 2.5


def calc_collateral_indications(annual):
    """Several leverage readings. None of them is an appraisal.

    Segment value capitalizes real-estate contribution at
    PROPERTY_INCOME_CAP_RATE and the operating-business contribution at
    GOING_CONCERN_EBITDA_MULTIPLE. Shared overhead (management fee, reserve,
    fixed opex) is not allocated between them — disclosed as such.
    Loan / the $1.4M land figure is a related-party basis ratio, not LTV.
    """
    re_contrib = annual["total_real_estate_contribution"]
    biz_contrib = annual["total_business_contribution"]
    re_value = re_contrib / PROPERTY_INCOME_CAP_RATE if PROPERTY_INCOME_CAP_RATE else 0.0
    biz_value = max(biz_contrib, 0.0) * GOING_CONCERN_EBITDA_MULTIPLE
    segment_value = re_value + biz_value
    return {
        "related_party_land_basis": LAND_PURCHASE_PRICE,
        "loan_over_related_party_land_basis": LOAN_AMOUNT / LAND_PURCHASE_PRICE,
        "ltc_on_capitalized_cost": LOAN_AMOUNT / TOTAL_CAPITALIZED_BASIS,
        "real_estate_contribution": re_contrib,
        "business_contribution": biz_contrib,
        "segment_real_estate_value": re_value,
        "segment_business_value": biz_value,
        "segment_value": segment_value,
        "ltv_segment_indication": (LOAN_AMOUNT / segment_value if segment_value else None),
        "shared_overhead_unallocated": True,
        "appraisal_status": "indication_only_pending_independent_appraisal",
    }


def calc_valuation_and_leverage(annual, cap_rate=None, loan_rate=None):
    """
    Cap-rate valuation, yield on cost, LTC/LTV, debt yield, and DSCR off a
    given year's annual NOI (before debt service - see summarize_annual).

    cap_rate: the market capitalization rate used to convert NOI into an
    implied asset value (value = NOI / cap_rate). Defaults to MARKET_CAP_RATE.

    loan_rate: the rate used to size annual debt service for DSCR. Defaults
    to LOAN_INTEREST_RATE (10%, itself a placeholder pending an actual bank
    quote - see CLAUDE.md's "Financing" section) - pass a different rate to
    see DSCR under a different quote (see run_rate_sensitivity_analysis).
    """
    cap_rate = cap_rate if cap_rate is not None else MARKET_CAP_RATE
    loan_rate = loan_rate if loan_rate is not None else LOAN_INTEREST_RATE
    noi = annual["total_noi"]
    implied_value = noi / cap_rate if cap_rate > 0 else 0
    yield_on_cost = noi / TOTAL_CAPITALIZED_BASIS
    annual_debt_service = _amortization_payment(LOAN_AMOUNT, loan_rate, LOAN_TERM_YEARS) * 12
    return {
        "cap_rate": cap_rate,
        "loan_rate": loan_rate,
        "implied_value": implied_value,
        "yield_on_cost": yield_on_cost,
        "development_spread": yield_on_cost - cap_rate,
        "total_capitalized_basis": TOTAL_CAPITALIZED_BASIS,
        "ltc": LOAN_AMOUNT / TOTAL_CAPITALIZED_BASIS,
        "ltv": LOAN_AMOUNT / implied_value if implied_value > 0 else 0,
        "debt_yield": noi / LOAN_AMOUNT if LOAN_AMOUNT > 0 else 0,
        "annual_debt_service": annual_debt_service,
        "dscr": noi / annual_debt_service if annual_debt_service > 0 else None,
        "equity_basis": EQUITY_BASIS,
        "property_equity": PROPERTY_EQUITY,
        "total_economic_equity": TOTAL_ECONOMIC_EQUITY,
        # Positive leverage only when yield on cost clears the loan rate.
        # Below that, debt dilutes equity returns — report it, don't hide it.
        "leverage_dilutive": yield_on_cost < loan_rate,
        "land_basis_label": "related-party transfer basis, not an appraisal",
    }


def _period_times(n, period_offset=0.0):
    """Discount-period timeline for a cash-flow list of length n: t=0 for the
    initial outlay (index 0), then i + period_offset for every later entry -
    i.e. every post-t=0 cash flow arrives period_offset years later than the
    no-offset convention (used to push the whole operating cash-flow stream
    out by the construction period - see CONSTRUCTION_PERIOD_MONTHS)."""
    return [0.0] + [i + period_offset for i in range(1, n)]


def _irr(cash_flows, lo=-0.95, hi=10.0, iterations=200, period_offset=0.0):
    """Bisection IRR solver - no external dependency required.

    Returns None if there's no sign change across [lo, hi] (IRR undefined
    or outside a sane range for this size of cash flow stream).
    """
    times = _period_times(len(cash_flows), period_offset)

    def npv_at(rate):
        return sum(cf / (1 + rate) ** t for t, cf in zip(times, cash_flows))

    if npv_at(lo) * npv_at(hi) > 0:
        return None
    for _ in range(iterations):
        mid = (lo + hi) / 2
        if npv_at(lo) * npv_at(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def _npv(rate, cash_flows, period_offset=0.0):
    times = _period_times(len(cash_flows), period_offset)
    return sum(cf / (1 + rate) ** t for t, cf in zip(times, cash_flows))


def run_returns_analysis(hold_years=None, exit_cap_rate=None, sale_cost_pct=None,
                         discount_rate=None, base_years=None, loan_rate=None):
    """
    Unlevered and levered IRR/NPV/equity multiple over a hold period, with
    reversion (sale) at a forward-looking cap rate applied to the NOI of the
    year immediately AFTER the hold ends (standard convention - the buyer is
    pricing off their first year of ownership, not the seller's last).

    Debt is paid off at sale using its ACTUAL remaining amortized balance
    at the exit year (via _amortization_balance), not the original
    LOAN_AMOUNT - a fixed-payment amortizing loan genuinely pays down
    principal over the hold, unlike the old revolving personal LOC this
    engine originally modeled, so there's no "conservative flat balance"
    convention to preserve here anymore. ncf_by_year already reflects the
    real fixed monthly P&I payment (see MONTHLY_DEBT_SERVICE), so levered
    cash flows are consistent with the exit payoff amount below.

    The t=0 outlay (-TOTAL_CAPITALIZED_BASIS / -EQUITY_BASIS) still happens
    at time zero, but every subsequent year's cash flow is discounted
    CONSTRUCTION_PERIOD_MONTHS/12 years later than the no-construction-period
    convention would put it - capital sits in a buildout for that long before
    Year 1 operations (and their cash flow) begin. This is a timing
    correction only; the dollar amounts of TOTAL_CAPITALIZED_BASIS and each
    year's NOI/net cash flow are unchanged (no draw schedule, capitalized
    interest, land carry, or developer fee - see CONSTRUCTION_PERIOD_MONTHS).

    base_years: optionally pass a pre-computed run_multi_year_projection()
    result (used by run_cre_sensitivity_grid to avoid recomputing it).

    loan_rate: defaults to LOAN_INTEREST_RATE (the placeholder 10% baked
    into every year's annual["total_net_cash"]). Pass a different rate to
    see levered returns under a different quote - NOI/unlevered returns are
    financing-neutral and don't change, but levered cash flow and the exit
    payoff balance are recomputed off this rate instead of reusing
    total_net_cash (see run_rate_sensitivity_analysis, which sweeps this).
    """
    hold_years = hold_years if hold_years is not None else HOLD_PERIOD_YEARS
    exit_cap_rate = exit_cap_rate if exit_cap_rate is not None else MARKET_CAP_RATE
    sale_cost_pct = sale_cost_pct if sale_cost_pct is not None else SALE_COST_PCT
    discount_rate = discount_rate if discount_rate is not None else DISCOUNT_RATE
    loan_rate = loan_rate if loan_rate is not None else LOAN_INTEREST_RATE
    years = (base_years if base_years is not None
             else run_multi_year_projection(years=hold_years + 1))

    noi_by_year = [ann["total_noi"] for _, _, ann in years]
    if loan_rate == LOAN_INTEREST_RATE:
        ncf_by_year = [ann["total_net_cash"] for _, _, ann in years]
    else:
        rate_debt_service = _amortization_payment(LOAN_AMOUNT, loan_rate, LOAN_TERM_YEARS) * 12
        ncf_by_year = [noi - rate_debt_service for noi in noi_by_year]

    reversion_noi = noi_by_year[hold_years]        # year hold+1's NOI (forward cap convention)
    reversion_gross = reversion_noi / exit_cap_rate if exit_cap_rate > 0 else 0
    reversion_net = reversion_gross * (1 - sale_cost_pct)

    exit_loan_balance = _amortization_balance(
        LOAN_AMOUNT, loan_rate, LOAN_TERM_YEARS, hold_years * 12)

    unlevered_cash_flows = ([-TOTAL_CAPITALIZED_BASIS] + noi_by_year[:hold_years - 1]
                            + [noi_by_year[hold_years - 1] + reversion_net])
    levered_cash_flows = ([-EQUITY_BASIS] + ncf_by_year[:hold_years - 1]
                          + [ncf_by_year[hold_years - 1] + reversion_net - exit_loan_balance])
    construction_years = CONSTRUCTION_PERIOD_MONTHS / 12
    unlevered_irr = _irr(unlevered_cash_flows, period_offset=construction_years)
    levered_irr = _irr(levered_cash_flows, period_offset=construction_years)

    return {
        "hold_years": hold_years, "exit_cap_rate": exit_cap_rate,
        "sale_cost_pct": sale_cost_pct, "discount_rate": discount_rate,
        "loan_rate": loan_rate,
        "reversion_gross": reversion_gross, "reversion_net": reversion_net,
        "exit_loan_balance": exit_loan_balance,
        "unlevered_cash_flows": unlevered_cash_flows,
        "levered_cash_flows": levered_cash_flows,
        "unlevered_irr": unlevered_irr,
        "levered_irr": levered_irr,
        "unlevered_npv": _npv(discount_rate, unlevered_cash_flows, period_offset=construction_years),
        "levered_npv": _npv(discount_rate, levered_cash_flows, period_offset=construction_years),
        "unlevered_equity_multiple": sum(unlevered_cash_flows[1:]) / TOTAL_CAPITALIZED_BASIS,
        "levered_equity_multiple": (sum(levered_cash_flows[1:]) / EQUITY_BASIS
                                    if EQUITY_BASIS > 0 else None),
        "cash_on_cash_year1": ncf_by_year[0] / EQUITY_BASIS if EQUITY_BASIS > 0 else None,
        "leverage_dilutive": (
            levered_irr is not None and unlevered_irr is not None
            and levered_irr < unlevered_irr
        ),
    }


def run_cre_sensitivity_grid(revenue_deltas=(-0.10, 0.0, 0.10),
                             exit_cap_rates=(0.08, 0.09, 0.10, 0.11),
                             hold_years=None,
                             base_weekday_customers=None, base_weekend_customers=None,
                             base_check=None, base_truck_avg_sales=None,
                             truck_slots=None, truck_rent=None, truck_share_rate=None,
                             truck_occupancy=None, seasonal_pct=1.0,
                             daytime_beverage_attach_rate=None,
                             daytime_beverage_avg_price=None,
                             cota_impact_multiplier=1.0):
    """
    Unlevered IRR grid: revenue scenario x exit cap rate, for the CRE tab's
    sensitivity table. Scales bar traffic, avg check, and truck avg sales
    together by revenue_delta (a blanket revenue-strength scenario, not a
    single-lever sensitivity). Every base_* argument mirrors a dashboard
    slider, same convention as run_monte_carlo/run_multi_year_projection -
    passing none of them reproduces the module defaults.
    """
    hold_years = hold_years if hold_years is not None else HOLD_PERIOD_YEARS
    wd0 = base_weekday_customers if base_weekday_customers is not None else BAR_WEEKDAY_CUSTOMERS
    we0 = base_weekend_customers if base_weekend_customers is not None else BAR_WEEKEND_CUSTOMERS
    check0 = base_check if base_check is not None else BAR_AVG_CHECK
    tsales0 = base_truck_avg_sales if base_truck_avg_sales is not None else TRUCK_AVG_MONTHLY_SALES

    grid = []
    for delta in revenue_deltas:
        row = {"revenue_delta": delta}
        years = run_multi_year_projection(
            base_weekday_customers=wd0 * (1 + delta),
            base_weekend_customers=we0 * (1 + delta),
            base_check=check0 * (1 + delta),
            truck_avg_sales=tsales0 * (1 + delta),
            truck_slots=truck_slots, truck_rent=truck_rent,
            truck_share_rate=truck_share_rate, truck_occupancy=truck_occupancy,
            seasonal_pct=seasonal_pct,
            daytime_beverage_attach_rate=daytime_beverage_attach_rate,
            daytime_beverage_avg_price=daytime_beverage_avg_price,
            cota_impact_multiplier=cota_impact_multiplier,
            years=hold_years + 1,
        )
        for cap in exit_cap_rates:
            result = run_returns_analysis(hold_years=hold_years, exit_cap_rate=cap, base_years=years)
            row[cap] = result["unlevered_irr"]
        grid.append(row)
    return grid


def run_rate_sensitivity_analysis(rates=None, annual=None, hold_years=None,
                                  exit_cap_rate=None, base_years=None):
    """
    DSCR and levered returns across a range of candidate loan interest
    rates. LOAN_INTEREST_RATE (10%) is explicitly a placeholder pending an
    actual bank quote (see CLAUDE.md's "Financing" section) - this shows
    how sensitive debt-service coverage and levered returns actually are to
    the rate that gets quoted, which is the number most likely to move
    before closing. Unlevered IRR and yield on cost are financing-neutral
    and don't vary by row - shown once by the caller, not repeated here.

    annual: the stabilized (year 2) annual dict used for DSCR. Defaults to
    a default-assumption run if not supplied.
    """
    rates = rates if rates is not None else (0.085, 0.09, 0.095, 0.10, 0.105, 0.11, 0.115, 0.12)
    if annual is None:
        _, annual = run_annual_projection(year=2)
    noi = annual["total_noi"]

    rows = []
    for rate in rates:
        monthly_payment = _amortization_payment(LOAN_AMOUNT, rate, LOAN_TERM_YEARS)
        annual_debt_service = monthly_payment * 12
        returns = run_returns_analysis(hold_years=hold_years, exit_cap_rate=exit_cap_rate,
                                       base_years=base_years, loan_rate=rate)
        rows.append({
            "rate": rate,
            "monthly_payment": monthly_payment,
            "annual_debt_service": annual_debt_service,
            "dscr": noi / annual_debt_service if annual_debt_service > 0 else None,
            "levered_irr": returns["levered_irr"],
            "levered_equity_multiple": returns["levered_equity_multiple"],
        })
    return rows


def run_bank_case_underwriting(loan_rate=None, hold_years=None, exit_cap_rate=None):
    """
    A single packaged conservative case for a lender's underwriting file -
    more useful to a loan officer than the five generic SCENARIOS (which
    drive the plain-language Scenarios tab via single-year
    run_scenario_projection) because it stacks the SPECIFIC risks this
    deal actually carries into one number, at CRE vocabulary:

      - No signed truck leases yet (six LOIs are not executed leases) -
        occupancy stressed to 0.75 (below TRUCK_OCCUPANCY's 0.85, above
        the Worst-Case scenario's 0.70).
      - A softer evening bar - traffic/check/daytime-attach read straight
        out of SCENARIOS["Stress Test"] rather than duplicated here, so a
        re-tuned scenario (or a bar-menu change that moves BAR_AVG_CHECK,
        as the container-bar buildout did) can't leave this case stale.
      - No contractual relationship with COTA (parking/bar/beverage uplift
        depends on a third party's event calendar) - cota_impact_multiplier
        halved rather than zeroed, since COTA events are real and
        calendared, just not guaranteed to recur at full strength.
      - A softer season overall (seasonal_pct 0.85 vs. 1.0).
      - A rate stress of +150bp over LOAN_INTEREST_RATE (BANK_CASE_RATE_STRESS)
        rather than the placeholder point estimate, since that's the number
        most likely to move before closing.

    Uses the multi-year/CRE engine (run_multi_year_projection +
    run_returns_analysis), not SCENARIOS, so it can report DSCR, LTC/LTV,
    yield on cost, and levered/unlevered IRR under the stacked stresses.
    """
    hold_years = hold_years if hold_years is not None else HOLD_PERIOD_YEARS
    exit_cap_rate = exit_cap_rate if exit_cap_rate is not None else MARKET_CAP_RATE
    loan_rate = loan_rate if loan_rate is not None else LOAN_INTEREST_RATE + BANK_CASE_RATE_STRESS

    stress = SCENARIOS["Stress Test"]
    years = run_multi_year_projection(
        base_weekday_customers=stress["weekday_customers"],
        base_weekend_customers=stress["weekend_customers"],
        base_check=stress["avg_check"],
        truck_occupancy=0.75, seasonal_pct=0.85,
        daytime_beverage_attach_rate=stress["daytime_beverage_attach_rate"],
        cota_impact_multiplier=0.5,
        years=hold_years + 1,
    )
    stabilized = years[1][2]   # year 2 = first steady-state year, same convention as elsewhere

    valuation = calc_valuation_and_leverage(stabilized, cap_rate=exit_cap_rate, loan_rate=loan_rate)
    returns = run_returns_analysis(hold_years=hold_years, exit_cap_rate=exit_cap_rate,
                                   base_years=years, loan_rate=loan_rate)

    return {
        "loan_rate": loan_rate,
        "stabilized_egi": stabilized["total_gross"],
        "stabilized_noi": stabilized["total_noi"],
        **valuation,
        "unlevered_irr": returns["unlevered_irr"],
        "levered_irr": returns["levered_irr"],
        "unlevered_equity_multiple": returns["unlevered_equity_multiple"],
        "levered_equity_multiple": returns["levered_equity_multiple"],
    }


# =============================================================================
# SECTION 10: CLI MENU
# =============================================================================

def print_annual_summary(months, annual, label=""):
    """Pretty-print a full annual projection."""
    month_names = MONTH_NAMES
    print(f"\n{'=' * 93}")
    if label:
        print(f"  {label}")
    print(f"{'=' * 93}")
    print(f"{'Month':<7} {'Gross':>10} {'Trucks':>9} {'Bar':>9} {'DayBev':>8} "
          f"{'COTA':>9} {'NOI':>10} {'NutCov':>7}")
    print("-" * 93)
    for m in months:
        cota = (m["cota_parking"] + m["cota_bar_uplift"]
               + m["cota_daytime_bev_uplift"])
        print(f"{month_names[m['month']]:<7} ${m['total_gross_revenue']:>9,.0f} "
              f"${m['truck_gross']:>8,.0f} "
              f"${m['bar_revenue']:>8,.0f} ${m['daytime_beverage_revenue']:>7,.0f} "
              f"${cota:>8,.0f} "
              f"${m['noi']:>9,.0f} {m['monthly_nut_coverage']:>6.2f}x")
    print("-" * 93)
    cota_total = (annual["total_cota_parking"] + annual["total_cota_bar"]
                 + annual["total_cota_daytime_bev"])
    print(f"{'YEAR':<7} ${annual['total_gross']:>9,.0f} "
          f"${annual['total_trucks']:>8,.0f} ${annual['total_bar']:>8,.0f} "
          f"${annual['total_daytime_beverage']:>7,.0f} "
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
  8. Loan Amortization Schedule
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
            run_loan_amortization_schedule()
        elif choice == "9":
            print_tax_strategy_analysis()
        elif choice == "0":
            print("\n  Goodbye!")
            break
        else:
            print("  Invalid choice. Try again.")


if __name__ == "__main__":
    main()
