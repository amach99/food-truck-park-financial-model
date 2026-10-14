"""
Generate the Del Valle Food Truck Park & Container Bar business plan / loan
proposal as a .docx, with every number pulled live from
`food_truck_park_model`.

WHY THIS EXISTS. The previous business plan was typed by hand. By the time an
independent lender review looked at it (2026-08-31) its Section 8 was already
stale against the engine - it had been written before the TABC double-count
fix, so every projected figure was off by about $108/yr. The reviewer
validated the document's internal arithmetic and had no way to detect the
drift. Generating the document removes that failure mode permanently and
satisfies the review's "reproducible projection workbook" request.

RULE: never hardcode a projected figure in this file. If a number belongs to
the model, read it from the model. Narrative prose is fine; arithmetic is not.

Usage:
    python build_business_plan.py [output.docx]
"""

import sys
from datetime import date

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

import food_truck_park_model as m


# --------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------

def money(x, cents=False):
    body = f"${abs(x):,.2f}" if cents else f"${abs(x):,.0f}"
    return f"-{body}" if round(x, 2 if cents else 0) < 0 else body


def pct(x, dp=1):
    return f"{x * 100:.{dp}f}%"


def ratio(x):
    return "n/a" if x is None else f"{x:.2f}x"


class PlanBuilder:
    """Thin wrapper over python-docx for the repetitive bits."""

    def __init__(self):
        self.doc = Document()
        base = self.doc.styles["Normal"]
        base.font.name = "Calibri"
        base.font.size = Pt(10.5)
        for section in self.doc.sections:
            section.left_margin = section.right_margin = Inches(0.9)
            section.top_margin = section.bottom_margin = Inches(0.8)

    def title(self, text, subtitle=None):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(22)
        if subtitle:
            sp = self.doc.add_paragraph()
            sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            srun = sp.add_run(subtitle)
            srun.font.size = Pt(12)
            srun.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    def h1(self, text):
        self.doc.add_heading(text, level=1)

    def h2(self, text):
        self.doc.add_heading(text, level=2)

    def h3(self, text):
        self.doc.add_heading(text, level=3)

    def para(self, text, bold=False, italic=False, size=None, center=False):
        p = self.doc.add_paragraph()
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        if size:
            run.font.size = Pt(size)
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return p

    def spacer(self):
        self.doc.add_paragraph()

    def placeholder(self, text):
        p = self.doc.add_paragraph()
        run = p.add_run("[" + text + "]")
        run.italic = True
        run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)

    def bullets(self, items):
        for it in items:
            self.doc.add_paragraph(str(it), style="List Bullet")

    def numbered(self, items):
        for it in items:
            self.doc.add_paragraph(str(it), style="List Number")

    def note(self, text):
        """A small grey caption - used for caveats and sourcing."""
        p = self.doc.add_paragraph()
        run = p.add_run(text)
        run.italic = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

    def table(self, headers, rows, widths=None):
        t = self.doc.add_table(rows=1, cols=len(headers))
        t.style = "Light Grid Accent 1"
        for i, h in enumerate(headers):
            cell = t.rows[0].cells[i]
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(h))
            run.bold = True
            run.font.size = Pt(9.5)
        for row in rows:
            cells = t.add_row().cells
            for i, val in enumerate(row):
                cells[i].text = ""
                run = cells[i].paragraphs[0].add_run("" if val is None else str(val))
                run.font.size = Pt(9.5)
                if isinstance(val, str) and val.startswith("**"):
                    run.text = val.strip("*")
                    run.bold = True
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Inches(w)
        self.doc.add_paragraph()
        return t

    def pagebreak(self):
        self.doc.add_page_break()

    def save(self, path):
        self.doc.save(path)



class MarkdownBuilder:
    """Same surface as PlanBuilder, emitting Markdown instead of .docx.

    Duck-typed deliberately: every section function below calls only the
    shared method names, so neither format can drift from the other. Used for
    Google Docs upload (Drive converts Markdown natively, giving real headings
    and tables rather than a round-tripped .docx).
    """

    def __init__(self):
        self.lines = []
        self.doc = self  # a few call sites reach for .doc

    # --- shared surface -------------------------------------------------
    def title(self, text, subtitle=None):
        self.lines.append(f"# {text}")
        if subtitle:
            self.lines.append(f"### {subtitle}")
        self.lines.append("")

    def h1(self, text):
        self.lines += ["", f"## {text}", ""]

    def h2(self, text):
        self.lines += ["", f"### {text}", ""]

    def h3(self, text):
        self.lines += ["", f"#### {text}", ""]

    def para(self, text, bold=False, italic=False, size=None, center=False):
        body = self._emphasize(text, bold, italic)
        self.lines += [body, ""]
        return self

    def spacer(self):
        self.lines.append("")

    def bullets(self, items):
        self.lines += [f"- {it}" for it in items] + [""]

    def numbered(self, items):
        self.lines += [f"{i}. {it}" for i, it in enumerate(items, 1)] + [""]

    def note(self, text):
        self.lines += [f"_{self._clean(text)}_", ""]

    def placeholder(self, text):
        self.lines += [f"> **[{self._clean(text)}]**", ""]

    def table(self, headers, rows, widths=None):
        head = [self._clean(str(h)) or " " for h in headers]
        self.lines.append("| " + " | ".join(head) + " |")
        self.lines.append("|" + "|".join(["---"] * len(head)) + "|")
        for row in rows:
            cells = []
            for val in row:
                v = "" if val is None else str(val)
                cells.append(f"**{v.strip('*')}**" if v.startswith("**")
                             else self._clean(v))
            cells += [""] * (len(head) - len(cells))
            self.lines.append("| " + " | ".join(cells) + " |")
        self.lines.append("")

    def pagebreak(self):
        self.lines += ["", "---", ""]

    def save(self, path):
        io_open = open(path, "w", encoding="utf-8")
        io_open.write("\n".join(self.lines).rstrip() + "\n")
        io_open.close()

    # --- helpers --------------------------------------------------------
    @staticmethod
    def _clean(text):
        # Pipes would break table rows; newlines would break any row.
        return str(text).replace("|", "\\|").replace("\n", " ")

    def _emphasize(self, text, bold, italic):
        body = self._clean(text).replace("\\|", "|")
        if bold:
            body = f"**{body}**"
        if italic:
            body = f"_{body}_"
        return body


# --------------------------------------------------------------------------
# Pull every figure from the model, once.
# --------------------------------------------------------------------------

def _event_share(annual):
    """Share of gross revenue that exists only because of COTA event days."""
    event = (annual["total_cota_parking"] + annual["total_cota_bar"]
             + annual["total_cota_daytime_bev"])
    return event / annual["total_gross"] if annual["total_gross"] else 0.0


def _pre_opening():
    """The pre-opening carry, read from the engine's PRE_OPEN_* constants."""
    return dict(
        months=m.PRE_OPEN_MONTHS,
        line_items={k: m.FIXED_COSTS[k] for k in m.PRE_OPEN_COST_KEYS},
        monthly_burn=m.PRE_OPEN_MONTHLY_BURN,
        total_burn=m.PRE_OPEN_BURN,
        opening_balance=m.OPENING_CASH_RESERVE,
    )


def _leverage(val, coll):
    """Loan-to-value on four bases. No single one is the headline."""
    return dict(
        segment_value=coll["segment_value"],
        ltv_vs_segment_value=coll["ltv_segment_indication"],
        ltv_vs_cost=m.LOAN_AMOUNT / m.TOTAL_CAPITALIZED_BASIS,
        ltv_vs_land_basis=coll["loan_over_related_party_land_basis"],
        blended_income_indication=val["implied_value"],
        ltv_vs_blended_indication=val["ltv"],
    )


def _guarantee_position():
    """Guarantor wording that follows the sponsor's recorded PG preference."""
    if m.SPONSOR_PG_PREFERENCE == "no_pg_land_only":
        return ("2 corporate; personal guarantees not offered (sponsor preference — "
                "SBA programs typically require one)")
    return "Personal and corporate"


def gather():
    no_cota = {mo: [] for mo in range(1, 13)}
    y1_months, y1 = m.run_annual_projection(year=1)
    y2_months, y2 = m.run_annual_projection(year=2)
    _, nocota = m.run_annual_projection(year=2, cota_events_override=no_cota)
    _, halfcota = m.run_annual_projection(year=2, cota_impact_multiplier=0.5)
    for annual in (y1, y2, nocota, halfcota):
        annual_mix = m.calc_revenue_mix(annual)
        annual["event_dependent_revenue_share"] = _event_share(annual)
        annual["real_property_revenue_share"] = annual_mix["property_and_parking_share"]
        annual["contractual_revenue_share"] = annual_mix["contractual_pad_rent_share"]
        annual["total_labor_cost"] = (annual["total_labor_wages"]
                                      + annual["total_payroll_burden"])
    val = m.calc_valuation_and_leverage(y2)
    coll = m.calc_collateral_indications(y2)
    mix = m.calc_revenue_mix(y2)
    tracker = m.run_cash_reserve_tracker(verbose=False)
    bank = m.run_bank_case_underwriting()
    scenarios = {name: m.run_scenario_projection(p)[1]
                 for name, p in m.SCENARIOS.items()}
    return dict(y1_months=y1_months, y1=y1, y2_months=y2_months, y2=y2,
                nocota=nocota, halfcota=halfcota, val=val, coll=coll, mix=mix,
                pre=_pre_opening(), tracker=tracker, bank=bank,
                ltv=_leverage(val, coll),
                scenarios=scenarios, loan_sizes=m.run_loan_size_dscr(),
                draws=m.build_construction_draw_schedule(),
                propco=m.run_propco_opco_split(y2))


# --------------------------------------------------------------------------
# Sections - ordered to the independent review's recommended lender narrative
# --------------------------------------------------------------------------

def cover(b, d):
    y2, val = d["y2"], d["val"]
    b.title("BUSINESS PLAN & LOAN PROPOSAL",
            "Del Valle Food Truck Park & Container Bar")
    b.para(f"13901 FM 812, Del Valle, Texas 78617  ·  "
           f"{m.LAND_ACRES} deeded acres  ·  Travis County",
           italic=True, center=True)
    b.spacer()

    b.table(["", ""], [
        ["Loan requested", f"{money(m.LOAN_AMOUNT)} (sized to the itemized uses)"],
        ["Purpose", "Refinance documented project expenditure, complete remaining "
                    "site improvements, and establish a controlled reserve"],
        ["Term requested", f"{m.LOAN_TERM_YEARS}-year fully amortizing"],
        ["Rate assumed", f"{pct(m.LOAN_INTEREST_RATE)} (placeholder pending the bank's quote)"],
        ["Products evaluated", ", ".join(p["label"] for p in m.LOAN_PRODUCTS.values())],
        ["Collateral", f"{m.LAND_ACRES} deeded acres owned free and clear, "
                       f"subject to independent appraisal"],
        ["Borrower", "JVAM Capital LLC (Texas)"],
        ["Projected DSCR — Year 1", ratio(d["y1"]["total_noi"] / m.ANNUAL_DEBT_SERVICE)],
        ["Projected DSCR — stabilized", ratio(val["dscr"])],
        ["Prepared", date.today().strftime("%B %d, %Y")],
    ], widths=[2.0, 4.6])

    b.h2("Request")
    b.para(
        f"JVAM Capital LLC requests a {money(m.LOAN_AMOUNT)} term facility to refinance "
        f"{money(_use('Payoff'))} of documented project expenditures, complete "
        f"{money(_new_improvements())} of remaining improvements, and establish a "
        f"{money(m.RESERVE_AND_SAFETY_CASH)} controlled operating and debt-service reserve. "
        "Primary repayment will come from combined property- and operating-company cash "
        "flow; secondary support will come from the restricted reserve, corporate "
        "guaranties and the unencumbered land. Collateral support remains subject to an "
        "independent evaluation of the property.")
    b.para(
        f"The request is sized from the bottom up rather than rounded: every named use is "
        f"added first, and the reserve is held at a {money(m.RESERVE_FLOOR)} floor. "
        f"Contingency is not cut to reach a round number. A {money(500_000)} facility "
        "does not fund the named uses and is shown only as a debt-service sensitivity.")

    b.note(
        "This plan supersedes the version dated August 26, 2026. It was revised following "
        "an independent third-party review completed August 31, 2026 and a further "
        "Sep 9 model audit, and it reflects the September 30, 2026 cost and timing "
        "decisions, including the $212,000 septic quote. Projected figures are generated "
        "directly from the underlying financial model rather than transcribed, so the "
        "narrative and the projections cannot diverge.")



def exec_summary(b, d):
    """Front-of-document summary. Leads with the strongest true facts.

    Deliberately placed before Sources & Uses: a credit officer reads the
    first page hardest, and the transaction's best features are structural
    (leverage, equity, collateral, debt yield) rather than operational.
    """
    y1, y2, val = d["y1"], d["y2"], d["val"]
    b.pagebreak()
    b.h1("Executive Summary")

    b.para(
        f"A {money(m.LOAN_AMOUNT)} term loan against {money(m.TOTAL_CAPITALIZED_BASIS)} of "
        f"total capitalized basis on land the borrower owns free and clear. Loan-to-cost is "
        f"{pct(m.LOAN_AMOUNT / m.TOTAL_CAPITALIZED_BASIS)}; the borrower's equity in the "
        f"asset is {money(m.EQUITY_BASIS)}, roughly "
        f"{m.EQUITY_BASIS / m.LOAN_AMOUNT:.1f} times the loan. Stabilized coverage is "
        f"{ratio(val['dscr'])} and stabilized debt yield is {pct(val['debt_yield'])}.",
        bold=True)

    b.h2("The Transaction at a Glance")
    b.table(["Metric", "This transaction", "Typical F&B benchmark"], [
        ["Loan amount", money(m.LOAN_AMOUNT), "—"],
        ["Loan-to-cost", pct(m.LOAN_AMOUNT / m.TOTAL_CAPITALIZED_BASIS), "60–75%"],
        ["Borrower equity in the asset", money(m.EQUITY_BASIS), "—"],
        ["Equity as a multiple of the loan",
         f"{m.EQUITY_BASIS / m.LOAN_AMOUNT:.1f}x", "—"],
        ["**Debt yield (stabilized)**", f"**{pct(val['debt_yield'])}**", "**11–13% minimum**"],
        ["**DSCR (stabilized)**", f"**{ratio(val['dscr'])}**", "**1.35–1.50x minimum**"],
        ["DSCR (Year 1, during lease-up)",
         ratio(y1["total_noi"] / m.ANNUAL_DEBT_SERVICE), "1.35–1.50x minimum"],
        ["Existing debt on the collateral", "None", "—"],
        ["Guarantees offered", _guarantee_position(), "—"],
    ], widths=[2.4, 1.9, 1.9])

    b.h2("What the Bank Is Lending Against")
    b.bullets([
        f"{m.LAND_ACRES} acres held in fee simple, free and clear, with no mortgage or deed "
        "of trust of record.",
        "A site fronting FM 812 directly opposite Circuit of the Americas property, "
        "separated only by the road right-of-way, with COTA event parking immediately "
        "across the road. This adjacency is not replicable by a competitor.",
        f"An absolute loan amount of {money(m.LOAN_AMOUNT)} — small relative to both the "
        "collateral and the borrower's equity — the lender's main structural protection "
        "if the operating business underperforms.",
        f"{money(m.RESERVE_AND_SAFETY_CASH)} of the proceeds held as a controlled reserve "
        "the lender can condition and monitor.",
        "Five independent revenue streams across two dayparts, rather than a single "
        "food-and-beverage concept.",
    ])

    b.h2("Liquidity, Stated Plainly")
    tracker = d["tracker"]
    b.para(
        f"The reserve is the thin point in this credit. {money(d['pre']['total_burn'])} of "
        f"the {money(m.RESERVE_AND_SAFETY_CASH)} reserve is consumed by {d['pre']['months']} "
        "months of loan payments before the park opens, leaving "
        f"{money(d['pre']['opening_balance'])} on opening day. "
        + (f"On the projected Year 1 ramp the operating cash balance reaches a low of "
           f"{money(tracker['min_balance'])} and is negative in "
           f"{tracker['months_negative']} months of the projection. Additional sponsor "
           "liquidity, a larger reserve or an interest-only construction period would be "
           "needed to close that gap."
           if tracker["min_balance"] < 0 else
           f"On the projected Year 1 ramp the balance does not fall below "
           f"{money(tracker['min_balance'])}."), bold=True)

    b.h2("Why the Numbers Should Be Trusted")
    b.para(
        "This plan was independently reviewed before submission, and the review was acted "
        "on rather than argued with. Every projection is generated directly from a "
        "regression-tested financial model rather than typed, and the model was corrected in "
        "several material respects as a result of that review — most significantly by adding "
        f"approximately {money(y2['total_labor_cost'])} of annual scheduled payroll that "
        "earlier drafts did not carry. The figures in this plan are lower than the figures "
        "in the version that preceded it. They are also right.")
    b.para(
        "A summary of every correction, including those that worked against the borrower, is "
        "available to the lender on request.")

    b.h2("The Principal Risk, Stated Up Front")
    b.para(
        f"COTA event weekends contribute {pct(y2['event_dependent_revenue_share'])} of "
        "stabilized revenue and there is no contract with COTA. This is the material risk in "
        "the credit and it is quantified in Section 8 rather than mitigated away. The "
        "borrower's position is that the concentration is real, that it is supported by a "
        "Formula 1 agreement running through 2034 and a multi-series event calendar, and "
        "that the low leverage and unencumbered collateral are what make it financeable.")


def credit_strengths(b, d):
    b.pagebreak()
    b.h1("Credit Strengths and Underwriting Considerations")
    y1, y2, val, ltv = d["y1"], d["y2"], d["val"], d["ltv"]
    ltvs = [ltv[k] for k in ("ltv_vs_segment_value", "ltv_vs_cost",
                             "ltv_vs_land_basis", "ltv_vs_blended_indication")]

    b.h2("Strengths")

    b.para("1.  Low leverage against real, unencumbered collateral.", bold=True)
    b.para(
        f"The borrower contributes {money(m.EQUITY_BASIS)} of equity against a "
        f"{money(m.LOAN_AMOUNT)} request — {pct(m.LOAN_AMOUNT / m.TOTAL_CAPITALIZED_BASIS)} "
        "loan-to-cost, well inside conventional limits. The land carries no existing debt. "
        "Every loan-to-value measure in Section 3, on four different bases, falls between "
        f"{pct(min(ltvs))} and {pct(max(ltvs))}.")

    b.para(f"2.  Debt yield of {val['debt_yield'] / 0.12:.1f} times a conventional minimum.",
           bold=True)
    b.para(
        f"Stabilized debt yield is {pct(val['debt_yield'])} against an 11–13% typical "
        "food-and-beverage floor. Debt yield is the one leverage test that cannot be moved "
        "by a cap-rate assumption or an appraisal, which is precisely why it is the most "
        "useful number in this plan: it holds regardless of what an independent evaluation "
        "concludes about value.")

    b.para("3.  An adjacency a competitor cannot buy.", bold=True)
    b.para(
        "The site sits directly across FM 812 from COTA property. Competing food truck parks "
        "are twenty to thirty minutes away in central Austin and cannot serve event parking; "
        "neighbouring lots sell bare gravel without food, drink, restrooms or a place to wait "
        "out post-event traffic. The site converts proximity into three separate revenue "
        "lines — parking, event-day bar uplift and event-day beverage uplift.")

    b.para("4.  Revenue diversified across streams and dayparts.", bold=True)
    b.para(
        "Five independent streams: contracted pad rent, percentage rent, an evening bar, an "
        "all-day beverage window and event parking. Food trucks drive daytime traffic and the "
        "bar drives evening traffic, so the site earns across the full operating day rather "
        f"than at a single peak. Roughly {pct(y2['real_property_revenue_share'])} of "
        "stabilized revenue is property-related rather than food-and-beverage operating "
        "income.")

    b.para("5.  A property company that covers its own debt.", bold=True)
    pc = d["propco"]
    b.para(
        f"On a stand-alone basis the borrower, {pc['propco_entity']}, earns "
        f"{money(pc['propco_noi'])} of stabilized NOI from pad rent, percentage rent, event "
        f"parking and the intercompany lease, against {money(pc['annual_debt_service'])} of "
        f"debt service — {ratio(pc['propco_noi'] / pc['annual_debt_service'])} coverage at "
        "the borrower level. Section 4 shows both entities and the consolidation.")

    b.para("6.  Corporate guarantor support and a land-secured structure.", bold=True)
    b.para(
        "Corporate guaranties from the holding company and the operating company, and an "
        "assignment of rents and of the intercompany lease. The sponsor's preference is a "
        "land-secured facility without personal guarantees; SBA programs typically require "
        "them, and Section 2 shows how coverage differs by product. Personal financial "
        "statements are available on request.")

    b.h2("Underwriting Considerations")
    b.para(
        "The borrower identifies these directly rather than leaving them to be discovered. "
        "Each is quantified in the section noted.")

    b.table(["Consideration", "Where quantified", "Borrower's position"], [
        ["Event revenue concentration —"
         f" {pct(y2['event_dependent_revenue_share'])} of stabilized revenue",
         "Section 8.3",
         "Real and material. Supported by a Formula 1 agreement through 2034 and a "
         "multi-series calendar; the low leverage is what makes it financeable."],
        ["No executed vendor leases", "Section 6",
         "Six operators interested, none signed. Projections already assume a half-leased "
         f"opening and a {pct(m.TRUCK_OCCUPANCY, 0)} occupancy haircut."],
        ["First-time operator in this format", "Section 4",
         "Mitigated by the share of income that is property-related rather than operating, "
         "and by resident on-site management."],
        [f"Year 1 coverage of {ratio(y1['total_noi'] / m.ANNUAL_DEBT_SERVICE)}, "
         "below the stabilized figure", "Section 8.1",
         "A lease-up and discovery year, not a run rate."],
        [f"Thin liquidity — {money(d['pre']['opening_balance'])} of reserve left at opening",
         "Section 5",
         "Pre-opening loan payments consume most of the reserve floor. Additional sponsor "
         "liquidity or an interest-only construction period would close the gap."],
        ["Yield on cost below the loan rate", "Section 3",
         "A consequence of a high land basis, which is itself collateral strength. The "
         "transaction is driven by coverage and low leverage, not accretive leverage."],
        ["Septic release is gated", "Section 1",
         f"The {money(m.SEPTIC)} septic quote is in the request but is not released to "
         "spend until its approval gate clears."],
        ["Opening date is an estimate", "Section 5",
         f"{_month_name(m.OPENING_MONTH)} {m.OPENING_YEAR} assumes "
         f"{m.ENTITLEMENT_PERMIT_LAG_MONTHS} months of entitlement and a "
         f"{m.CONSTRUCTION_PERIOD_MONTHS}-month build. Each month of delay costs "
         f"{money(d['pre']['monthly_burn'])} of loan payments with no revenue."],
    ], widths=[2.1, 1.1, 3.4])


def _use(prefix):
    return next(a for label, a, _ in m.USE_OF_FUNDS if label.startswith(prefix))


def _new_improvements():
    excluded = ("Payoff of existing", "Reserve & Safety Cash")
    return sum(a for label, a, _ in m.USE_OF_FUNDS
               if not label.startswith(excluded))


def s1_transaction(b, d):
    b.pagebreak()
    b.h1("1.  Transaction and Sources & Uses")

    b.h2("Use of Funds")
    status_text = {"done": "Already incurred", "gated": "Budgeted; release gated",
                   "tbd": "Amount TBD — quote pending", "not_started": "Not yet started"}
    b.table(["Use", "Amount", "Status"],
            [[label, money(amt), status_text.get(st, st)]
             for label, amt, st in m.USE_OF_FUNDS]
            + [["**Total**", f"**{money(m.TOTAL_PROJECT_COST)}**", ""]],
            widths=[4.0, 1.3, 1.3])

    b.para("Explanation of each use", bold=True)
    b.bullets([
        f"Refinance of existing line of credit — {money(_use('Payoff'))}. Initial site work "
        "was financed with a personal line of credit at 12.5%. Retiring it with term debt "
        "replaces revolving personal debt with amortizing business debt.",
        f"Septic system — {money(_use('Septic'))}. A real vendor quote. Required for "
        "permanent restrooms and full pad servicing; the largest remaining construction item "
        "and a precondition to operating at capacity. Counted in the request but gated: not "
        "released to spend until its approval clears.",
        f"Paved access — {money(_use('Paved'))}. Asphalt internal roads, necessary for "
        f"all-weather event parking. A {money(m.GRAVEL_ALT_BUDGET)} gravel alternate is "
        "documented and not selected.",
        f"Container bar buildout — {money(_use('Container'))}. Taps, coolers and mixed-drink "
        "service.",
        f"General contractor allowance — {money(_use('GC'))}, held until a GC bid replaces it.",
        f"Permits — {money(_use('Permits'))} for the health permit and business license. "
        "Site development, OSSF design, deed/legal, stormwater reinspection and the civil "
        "engineering remainder are listed separately at $0 because no quote exists yet; "
        "they are disclosed rather than guessed, and contingency carries them until quoted.",
        f"Land carry — {money(_use('Land carry'))}, six months of vacant-land property tax "
        "and insurance prepaid at closing.",
        f"Contingency — {money(_use('Contingency'))}, being "
        f"{pct(m.CONTINGENCY_RATE_BASE, 0)} of hard costs including the GC allowance "
        f"({pct(m.CONTINGENCY_RATE_BANK, 0)} in the bank case).",
        f"Reserve and safety cash — {money(m.RESERVE_AND_SAFETY_CASH)}. See below.",
    ])

    b.h2("Capital Structure")
    new_improvements = m.TOTAL_CAPITALIZED_BASIS - m.LAND_PURCHASE_PRICE - m.PHASE_0_5_TOTAL
    b.table(["Component", "Amount"], [
        ["Land, owned free and clear (related-party basis)", money(m.LAND_PURCHASE_PRICE)],
        ["Site work already completed (Phase 0.5)", money(m.PHASE_0_5_TOTAL)],
        ["New improvements funded by this loan", money(new_improvements)],
        ["Total capitalized basis", f"**{money(m.TOTAL_CAPITALIZED_BASIS)}**"],
        ["Less: bank term loan", f"({money(m.LOAN_AMOUNT)})"],
        ["**Owner equity in the capitalized asset**",
         f"**{money(m.EQUITY_BASIS)}**"],
        ["Add: unspent Reserve & Safety Cash", money(m.RESERVE_AND_SAFETY_CASH)],
        ["**Total economic equity**", f"**{money(m.TOTAL_ECONOMIC_EQUITY)}**"],
    ], widths=[4.4, 1.6])

    b.para(
        f"These are two different figures and are presented separately. Equity in the "
        f"capitalized asset ({money(m.EQUITY_BASIS)}) measures the borrower's stake in the "
        f"property itself. Total economic equity ({money(m.TOTAL_ECONOMIC_EQUITY)}) adds the "
        "unspent reserve, which is a real asset but not an improvement to the collateral. A "
        "prior version of this plan displayed rows totalling the second figure while "
        "labelling the result the first; that error has been corrected.")

    b.para(f"Loan-to-cost is {pct(m.LOAN_AMOUNT / m.TOTAL_CAPITALIZED_BASIS)}. "
           "Loan-to-value is addressed at Section 3, where the collateral is evaluated.")

    b.h2("How the Request Is Sized")
    itemized = m.TOTAL_PROJECT_COST - m.RESERVE_AND_SAFETY_CASH
    b.para(
        f"The itemized construction and refinancing scope totals {money(itemized)}. The "
        f"reserve is then held at a {money(m.RESERVE_FLOOR)} floor, giving a request of "
        f"{money(m.TOTAL_PROJECT_COST)}. The reserve is the plug, not contingency: if a "
        "quote rises, the request rises with it rather than the contingency being cut.")
    b.numbered([
        "The park is pre-revenue and will carry debt service through entitlement and "
        "construction before any income exists — quantified at Section 5.",
        "A first-time operator in this format should not run without a cushion. "
        "Construction overruns, a delayed permit and slower-than-projected lease-up are all "
        "realistic.",
        "Coverage ratios throughout this plan are calculated on debt service for the full "
        "loan. The reserve is not free money; the projections pay for it.",
    ])

    b.h2("Draw Schedule")
    draws = d["draws"]
    b.table(["Month from closing", "Phase", "Draw", "Cumulative drawn"],
            [[str(r["m"]), r["phase"].title(), money(r["draw"]), money(r["cumulative"])]
             for r in draws["months"]]
            + [["**Reserve held back (not drawn)**", "", "",
                f"**{money(draws['reserve_held_back'])}**"]],
            widths=[1.5, 1.5, 1.5, 1.8])
    b.note(draws["note"])
    b.para("Proposed reserve controls", bold=True)
    b.bullets([
        "Held in a segregated account at the lender.",
        "Draws limited to debt service, documented construction costs and operating "
        "shortfalls, on borrower certification.",
        "Minimum balance covenant, stepping down as operating history accumulates.",
        "Release to the borrower only after a defined period of sustained coverage, at the "
        "lender's discretion.",
    ])
    b.note("Reserve control terms are proposed for negotiation, not assumed.")


def s2_repayment(b, d):
    b.pagebreak()
    b.h1("2.  Repayment Sources")
    y1, y2, val = d["y1"], d["y2"], d["val"]

    b.h2("Primary — Operating Cash Flow")
    b.table(["Metric", "Year 1", "Stabilized"], [
        ["Gross revenue", money(y1["total_gross"]), money(y2["total_gross"])],
        ["Net operating income (before debt service)",
         money(y1["total_noi"]), money(y2["total_noi"])],
        ["Annual debt service", money(m.ANNUAL_DEBT_SERVICE), money(m.ANNUAL_DEBT_SERVICE)],
        ["Net cash flow after debt service",
         money(y1["total_net_cash"]), money(y2["total_net_cash"])],
        ["**Debt service coverage ratio**",
         f"**{ratio(y1['total_noi'] / m.ANNUAL_DEBT_SERVICE)}**", f"**{ratio(val['dscr'])}**"],
        ["Debt yield", pct(y1["total_noi"] / m.LOAN_AMOUNT), pct(val["debt_yield"])],
    ], widths=[3.4, 1.6, 1.6])

    b.para(
        f"Debt service is {money(m.ANNUAL_DEBT_SERVICE)} annually "
        f"({money(m.LOAN_MONTHLY_PAYMENT, cents=True)} monthly) at the assumed "
        f"{pct(m.LOAN_INTEREST_RATE)} rate over {m.LOAN_TERM_YEARS} years. Year 1 coverage "
        f"of {ratio(y1['total_noi'] / m.ANNUAL_DEBT_SERVICE)} reflects lease-up and "
        "discovery ramps; stabilized coverage is "
        f"{ratio(val['dscr'])}. A conventional food-and-beverage minimum is 1.35x–1.50x.")

    b.h2("Secondary — Reserve, Guarantors and Collateral")
    b.bullets([
        f"The controlled reserve, {money(m.RESERVE_AND_SAFETY_CASH)} at funding and "
        f"{money(d['pre']['opening_balance'])} projected at opening after the construction "
        "carry.",
        "Corporate guaranty of JVAM Ventures LLC, sole member of both Texas entities.",
        "Corporate guaranty of JVA Operations LLC, the operating company and TABC "
        "permittee, with an assignment of rents and of the intercompany lease.",
        "The unencumbered real property, subject to the independent evaluation at "
        "Section 3.",
        "Personal guarantees are not offered under the sponsor's stated preference for a "
        "land-secured facility. SBA 7(a) and 504 typically require them; this is a point "
        "for negotiation with the lender.",
    ])

    b.h2("Coverage by Loan Product and Size")
    b.para(
        "No product has been quoted. Stabilized coverage is shown below for the three "
        "structures under consideration, at the sized request and at the two round-number "
        "alternatives the borrower has been asked about.")
    rows = [r for r in d["loan_sizes"]["rows"] if r["case"] == "base" and r["year"] == 2]
    b.table(["Product", "Loan", "Annual debt service", "DSCR", "Funds the uses?",
             "PG typical?"],
            [[r["product_label"], money(r["loan_amount"]), money(r["annual_debt_service"]),
              ratio(r["dscr"]), "Yes" if r["fits_uses"] else "No",
              "Yes" if r["pg_conflict"] else "No"] for r in rows],
            widths=[1.5, 1.0, 1.3, 0.8, 1.0, 0.9])
    b.note("NOI here is operating Year 2 of the multi-year projection, which includes "
           "growth and cost inflation, so it differs slightly from the steady-state figure "
           f"above. {d['loan_sizes']['note_500k']} {d['loan_sizes']['note_750k']}")

    b.h2("Interest Rate Sensitivity")
    b.para("The rate is not yet quoted. Stabilized coverage across a candidate range:")
    rows = []
    for r in (0.085, 0.09, 0.095, 0.10, 0.105, 0.11, 0.115, 0.12):
        pay = m._amortization_payment(m.LOAN_AMOUNT, r, m.LOAN_TERM_YEARS)
        rows.append([pct(r), money(pay, cents=True), money(pay * 12),
                     ratio(y2["total_noi"] / (pay * 12))])
    b.table(["Rate", "Monthly P&I", "Annual debt service", "Stabilized DSCR"], rows,
            widths=[1.2, 1.5, 1.9, 1.6])
    b.note(f"{pct(m.LOAN_INTEREST_RATE)} is the rate assumed throughout this plan.")


def s3_collateral(b, d):
    b.pagebreak()
    b.h1("3.  Title, Independent Evaluation and Collateral")
    val = d["val"]

    b.h2("Title")
    b.para(
        "JVAM Capital LLC holds fee simple title to the property, acquired 02/20/2026 from "
        "Veerabhadra Macharla by two General Warranty Deeds recorded in the Official Public "
        "Records of Travis County: one conveying 1.500 acres and one conveying 2.932 acres, "
        "both out of the Peter C. Harrison Survey, Abstract No. 2104, being portions of "
        "Lot 2, Block A, Final Plat of Del Valle Dollar General (Document No. 201600109), "
        "together with an easement estate under the Joint Use Easement recorded under "
        f"County Clerk's File No. 2016033244. The two tracts total {m.LAND_ACRES} acres. The "
        "property is owned free and clear, with no mortgage or deed of trust of record.")
    b.para(
        "The conveyance was a related-party transfer of property already within the family "
        "group, not an arm's-length purchase. The "
        f"{money(m.LAND_PURCHASE_PRICE)} figure carried in this plan is therefore a "
        "cost basis, not evidence of market value, and is labelled as such wherever it "
        "appears. Title commitment, survey and deeds are available on request.")

    b.h2("Valuation — Property and Business Evaluated Separately")
    coll, ltv = d["coll"], d["ltv"]
    b.para(
        "A prior version of this plan derived a single loan-to-value ratio by capitalizing "
        "blended property, parking and bar income at one real-estate cap rate. That "
        "derivation has been withdrawn. An operating food-and-beverage business is not "
        "valued like a ground lease and does not support real-estate leverage on the same "
        "terms. The two income streams are evaluated separately below.")
    b.table(["Component", "Contribution", "Basis", "Indicated value"], [
        ["Real property income (pad rent, percentage rent, event parking)",
         money(coll["real_estate_contribution"]),
         f"{pct(m.PROPERTY_INCOME_CAP_RATE, 2)} cap rate",
         money(coll["segment_real_estate_value"])],
        ["Operating business (bar and beverage)",
         money(coll["business_contribution"]),
         f"{m.GOING_CONCERN_EBITDA_MULTIPLE:.1f}x contribution",
         money(coll["segment_business_value"])],
        ["**Combined**", "", "", f"**{money(coll['segment_value'])}**"],
    ], widths=[2.7, 1.2, 1.4, 1.3])
    b.note(
        "Shared overhead — management fee, replacement reserve and fixed operating costs — "
        "is not allocated between the segments, so both contributions are before it and the "
        "combined figure overstates value accordingly. Both the cap rate and the earnings "
        "multiple are estimates.")

    b.h2("Leverage, Stated Four Ways")
    b.para("No single loan-to-value figure is presented as the headline.")
    b.table(["Basis", "Value", "LTV"], [
        ["Combined segment value", money(ltv["segment_value"]),
         pct(ltv["ltv_vs_segment_value"])],
        ["Total capitalized cost", money(m.TOTAL_CAPITALIZED_BASIS), pct(ltv["ltv_vs_cost"])],
        ["Land cost basis (related party — not market value)",
         money(m.LAND_PURCHASE_PRICE), pct(ltv["ltv_vs_land_basis"])],
        [f"Blended income at a {pct(m.MARKET_CAP_RATE)} cap rate (not an appraisal)",
         money(ltv["blended_income_indication"]), pct(ltv["ltv_vs_blended_indication"])],
    ], widths=[3.6, 1.6, 1.2])
    b.para(
        "Every figure above is an indication. The borrower requests that the lender order an "
        "independent as-is and as-complete evaluation and allocate going-concern value, and "
        "will accept that evaluation as the basis for the collateral test.", bold=True)

    b.h2("Yield on Cost")
    b.para(
        f"Stabilized yield on cost is {pct(val['yield_on_cost'])} against total capitalized "
        f"basis of {money(m.TOTAL_CAPITALIZED_BASIS)}. At the {pct(m.LOAN_INTEREST_RATE)} "
        "assumed rate that sits below the cost of debt, so leverage is not currently "
        "accretive to equity returns. The borrower notes this rather than omitting it, and "
        "also notes what drives it: the denominator is dominated by land carried at "
        f"{money(m.LAND_PURCHASE_PRICE)}. A high land basis depresses yield on cost and "
        "simultaneously strengthens the lender's position — it is the reason loan-to-cost is "
        f"{pct(m.LOAN_AMOUNT / m.TOTAL_CAPITALIZED_BASIS)} rather than a conventional 65%.")
    b.para(
        "From the lender's side the relevant tests are coverage and debt yield, both of "
        f"which are strong ({ratio(val['dscr'])} and {pct(val['debt_yield'])} stabilized). "
        "Yield on cost is an equity-return measure, and the borrower is accepting a lower "
        "equity return in exchange for a conservatively levered balance sheet. The "
        "relationship reverses if net operating income exceeds projection or the quoted rate "
        "comes in below the placeholder.")

    b.h2("Not Offered as Collateral")
    b.para(
        "The TABC Mixed Beverage Permit is held by JVA Operations LLC. A TABC permit is not "
        "transferable and is not offered or presented as lender collateral.")


def s4_management(b, d):
    b.pagebreak()
    b.h1("4.  Ownership, Management and Guarantor Support")

    b.h2("Entity Structure")
    b.table(["Entity", "Jurisdiction", "Formed", "Role"], [
        ["JVAM Ventures LLC", "Wyoming", "01/14/2026",
         "Holding company; sole member of both Texas entities"],
        ["JVAM Capital LLC", "Texas — SOS 806400710", "01/20/2026",
         "BORROWER. Property company; holds fee title"],
        ["JVA Operations LLC", "Texas — SOS 806400601", "01/20/2026",
         "Operating company; holds the TABC Mixed Beverage Permit"],
    ], widths=[1.6, 1.6, 1.0, 2.4])

    b.para(
        "Both Texas entities are wholly owned by JVAM Ventures LLC, which is owned in equal "
        "quarters by four members of the Macharla family — Alok, Anoop, Veerabhadra and "
        "Jyothi — giving each a 25% indirect interest in the borrower. Both Texas entities "
        "were converted to manager-managed in May 2026 with Alok Macharla as sole Manager.")
    b.para(
        "Mortgaging the property and incurring indebtedness above $250,000 are Major "
        "Decisions under each operating agreement, requiring prior written consent of the "
        "Member. A written consent of all four members authorizing this loan and the deed of "
        "trust will be executed and delivered as a condition of closing.")

    b.h2("Intercompany Lease")
    b.para(
        "JVAM Capital LLC leases the property to JVA Operations LLC under an intercompany "
        "lease expressly carved out of the Major Decisions restrictions. Operating revenue "
        "supports debt service at the borrower level through that lease.")
    pc = d["propco"]
    b.para(
        "Projections elsewhere in this plan are presented on a COMBINED basis. The "
        "independent review asked for separate property-company and operating-company "
        "statements; they follow, at stabilization. The intercompany lease eliminates on "
        "consolidation, so the two entities sum exactly to the combined figure.")
    b.table(["", pc["propco_entity"] + " (borrower)", pc["opco_entity"], "Combined"], [
        ["Intercompany lease (base rent + NNN)", money(pc["lease_payment"]),
         f"({money(pc['lease_payment'])})", "—"],
        ["Net operating income", money(pc["propco_noi"]), money(pc["opco_noi"]),
         money(pc["consolidated_noi"])],
        ["Debt service", money(pc["annual_debt_service"]), "—",
         money(pc["annual_debt_service"])],
        ["Cash flow after debt service", money(pc["propco_cash_flow"]),
         money(pc["opco_cash_flow"]),
         money(pc["consolidated_noi"] - pc["annual_debt_service"])],
    ], widths=[2.4, 1.6, 1.4, 1.2])
    b.note(pc["lease_note"])
    if pc["opco_noi"] < 0:
        b.para(
            "The operating company runs at a loss on a stand-alone basis: it carries the "
            "payroll, the lease and the event costs, while event parking and percentage rent "
            "accrue to the property company. The borrower is prepared to structure the "
            "credit as co-borrowers, or with JVA Operations LLC as guarantor and its revenue "
            "assigned, so the lender is not exposed to that split.")

    b.h2("Management Experience")
    _placeholder(b,
        "TO BE COMPLETED BY BORROWER. This section is the one a credit officer reads most "
        "closely, and the independent review flagged it as an unfilled placeholder. For each "
        "principal and key employee provide: full name; years and nature of relevant "
        "experience; prior business ownership, management or P&L responsibility; "
        "food-and-beverage, hospitality, retail, real estate or construction experience; "
        "TABC certification status; and education. Where direct food-and-beverage operating "
        "experience is limited, state the relatable experience explicitly — property "
        "management, trade or contractor experience, prior small-business ownership, event "
        "operations or general management all bear directly on this business. Attach résumés.")

    b.h2("Professional Advisors")
    _placeholder(b,
        "TO BE COMPLETED BY BORROWER. Name the CPA firm, attorney and insurance agent "
        "engaged. A lender will expect a named CPA given the monthly Texas mixed-beverage "
        "filing obligation, and given the worker-classification and lodging questions "
        "identified at Section 5.")

    b.h2("Guarantor Support")
    b.bullets([
        "Corporate guaranty of JVAM Ventures LLC.",
        "Corporate guaranty of JVA Operations LLC, with assignment of rents and of the "
        "intercompany lease.",
        "Personal guarantees are not offered: the sponsor's preference is a land-secured "
        "facility. If the lender's program requires one, the borrower is prepared to "
        "discuss a limited guarantee with a burn-down tied to sustained coverage. Personal "
        "financial statements and tax returns are available on request.",
    ])

    b.h2("Tax Treatment")
    b.para(
        "No entity is a taxable corporation and no S-corporation election has been made. Both "
        "Texas entities are disregarded single-member LLCs; JVAM Ventures LLC files Form 1065 "
        "and issues K-1s to the four members. All taxable income flows to individual returns; "
        "Texas imposes no personal income tax. Franchise tax is $0 at projected revenue — the "
        "2026 no-tax-due threshold is $2.65 million — but annual reports and Public "
        f"Information Reports must still be filed. The {pct(m.EFFECTIVE_INCOME_TAX_RATE, 0)} "
        "blended federal rate used in the projections is an estimate, not a computed figure, "
        "and the borrower's CPA will confirm it.")


def _placeholder(b, text):
    """A red bracketed block the borrower must fill in before submission."""
    b.placeholder(text)


def s5_schedule(b, d):
    b.pagebreak()
    b.h1("5.  Permit, Construction and Opening Schedule")
    pre = d["pre"]

    b.para(
        "The independent review found the previously proposed September 2026 opening not "
        "credible, since the septic system, paved access, container bar and health permit "
        "were all unstarted at the plan date while projections began September 1 and booked "
        "event revenue in the opening month. That schedule has been withdrawn.")
    b.para(
        f"Projections in this plan assume operations begin "
        f"{_month_name(m.OPENING_MONTH)} {m.OPENING_YEAR}, {m.MONTHS_TO_OPEN} months after "
        f"closing: {m.ENTITLEMENT_PERMIT_LAG_MONTHS} months of entitlement and permitting, "
        f"then a {m.CONSTRUCTION_PERIOD_MONTHS}-month physical build.", bold=True)
    b.note(
        "The opening date is an estimate pending fixed bids, a construction schedule and "
        "permit issuance dates. It is a single input to the model; when the real date is "
        "known every projection in this plan moves with it.")

    b.h2("Pre-Opening Carry")
    b.para(
        "Debt service begins at closing, not at opening. A prior version of this plan "
        "ignored that entirely. The construction period now carries:")
    b.table(["Cost accruing during construction", "Monthly"],
            [[k.replace("_", " ").title(), money(v)]
             for k, v in pre["line_items"].items()]
            + [["**Total monthly burn**", f"**{money(pre['monthly_burn'])}**"]],
            widths=[4.0, 1.5])
    b.table(["Reserve", "Amount"], [
        ["Reserve & Safety Cash funded at closing", money(m.RESERVE_AND_SAFETY_CASH)],
        [f"Less {pre['months']}-month pre-opening carry", f"({money(pre['total_burn'])})"],
        ["**Reserve remaining at opening**", f"**{money(pre['opening_balance'])}**"],
    ], widths=[4.0, 1.5])
    b.note(
        "Vacant-land property tax and insurance for the pre-opening months are prepaid at "
        "closing as a separate use, so they are not charged again here. Utilities, waste "
        "service, marketing and point-of-sale subscriptions are excluded — there is nothing "
        "yet to power, haul, advertise or ring up.")
    if pre["opening_balance"] < 0.25 * m.RESERVE_AND_SAFETY_CASH:
        b.para(
            f"Only {money(pre['opening_balance'])} of the reserve remains at opening. That "
            "is not enough to absorb the Year 1 seasonal troughs on its own; see the "
            "liquidity discussion in the Executive Summary.", bold=True)

    b.h2("Permit Status Matrix")
    _placeholder(b,
        "TO BE COMPLETED BY BORROWER — the independent review asked specifically for this. "
        "For each of the following, state: authority, application date, status, expected "
        "issuance, and cost. Land use / site development (Travis County); on-site sewage "
        "facility (septic); commercial driveway access (TxDOT — FM 812 is a state road, so "
        "driveway construction or alteration requires TxDOT review); fire and life safety; "
        "health and food service; drainage and stormwater; accessibility; event parking; "
        "residential occupancy for on-site staff housing; certificate of occupancy; and any "
        "mass-gathering approval.")

    b.h2("Construction and Draw Schedule")
    _placeholder(b,
        "TO BE COMPLETED BY BORROWER. The septic quote is in hand. Attach fixed bids for "
        "paving, the container bar buildout and a general contractor (replacing the GC "
        "allowance), plus a construction schedule with milestone dates. The modelled draw "
        "sequence is at Section 1.")

    b.h2("Staffing Plan")
    y2 = d["y2"]
    b.para(
        "The independent review found labor underwritten, and it was. A prior version of "
        "this plan carried no scheduled wages at all: the manager was compensated solely "
        "with on-site housing and the bartender solely with a 5% revenue share. Across the "
        "modelled service window that share worked out to approximately $2.11 per hour in "
        "Year 1 — below the federal minimum wage, which Texas adopts. The projections in "
        "this plan now carry a real payroll.")
    b.table(["Role", "Scheduled hours", "Rate", "Stabilized cost"], [
        ["Beverage attendant — daytime window",
         f"{m.LABOR_WEEKDAY_DAYTIME_HOURS:.1f} weekday / "
         f"{m.LABOR_WEEKEND_DAYTIME_HOURS:.1f} weekend hrs/day",
         f"{money(m.DAYTIME_ATTENDANT_WAGE, cents=True)}/hr",
         money(y2["total_daytime_wages"])],
        ["Bartender — evening bar",
         f"{m.LABOR_WEEKDAY_EVENING_HOURS:.1f} weekday / "
         f"{m.LABOR_WEEKEND_EVENING_HOURS:.1f} weekend / "
         f"{m.LABOR_RACE_EVENING_HOURS:.1f} race-day hrs",
         f"{money(m.EVENING_BARTENDER_WAGE, cents=True)}/hr",
         money(y2["total_evening_wages"] + y2["total_race_evening_premium"])],
        ["Extra staff — COTA event days", f"{m.EVENT_EXTRA_BODIES} extra per event day",
         f"{money(m.EVENT_EXTRA_WAGE, cents=True)}/hr", money(y2["total_event_extra_wages"])],
        ["Park manager", "Salaried", f"{money(m.MANAGER_ANNUAL_SALARY)}/yr",
         money(y2["total_manager_salary"])],
        ["Overtime allowance", f"{pct(m.OVERTIME_ALLOWANCE_RATE, 0)} of hourly wages", "",
         money(y2["total_overtime_allowance"])],
        ["Employer payroll burden (FICA/FUTA/SUTA)", "All wages",
         pct(m.EMPLOYER_PAYROLL_BURDEN_RATE, 0), money(y2["total_payroll_burden"])],
        ["**Total annual labor cost**", "", "",
         f"**{money(y2['total_labor_wages'] + y2['total_payroll_burden'])}**"],
    ], widths=[2.0, 2.2, 1.0, 1.1])
    b.note("Hours flex by season: winter shifts are shorter and October is the busiest month.")
    b.para(
        "Both the manager and the bartender live on site. That housing is disclosed but "
        "is NOT treated as a cash expense and is NOT credited against wages. Whether it is "
        "excludable from the employees' income under IRC §119, and whether any lodging "
        "credit under FLSA §3(m) is available, are fact-specific questions for the "
        "borrower's CPA and counsel. The wages above clear the minimum wage on their own, so "
        "no lodging credit is claimed or required.")
    _placeholder(b,
        "TO BE COMPLETED BY BORROWER — the review asked for a weekly staffing schedule for "
        "normal days and event days, and for confirmation of worker classification. Wage "
        "rates above are market estimates and should be replaced with real offers.")


def _month_name(mo):
    return ["", "January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December"][mo]


def s6_vendors(b, d):
    b.pagebreak()
    b.h1("6.  Vendor Pipeline and Lease Economics")
    y2 = d["y2"]

    b.para(
        f"{m.TRUCK_SLOTS} serviced pads are being built. Intended terms are "
        f"{money(m.TRUCK_PAD_RENT)} per month base rent plus "
        f"{pct(m.TRUCK_REV_SHARE_RATE, 0)} of vendor gross sales on six-month contracts.")

    b.para("Status: no executed leases.", bold=True)
    b.para(
        "Six operators have expressed interest. None has signed. The projections do not "
        "assume otherwise: the lot is modelled as opening roughly half-leased and filling "
        f"over the first two to three quarters, with a {pct(m.TRUCK_OCCUPANCY, 0)} "
        "steady-state occupancy factor applied on top of that to reflect vacancy between "
        "tenancies.")

    b.h2("Lease Economics, Stated Honestly")
    implied = m.TRUCK_PAD_RENT + m.TRUCK_REV_SHARE_RATE * m.TRUCK_AVG_MONTHLY_SALES
    b.para(
        f"At the modelled {money(m.TRUCK_AVG_MONTHLY_SALES)} of monthly vendor sales, "
        f"effective rent is {money(implied)} per month, or "
        f"{pct(implied / m.TRUCK_AVG_MONTHLY_SALES)} of vendor gross before utility "
        "reimbursement. The independent review observed that this is aggressive, and the "
        "borrower accepts the observation. These are intended terms, not achieved terms. If "
        "leases sign at lower economics the projections move accordingly.")

    b.h2("Revenue Mix — Corrected")
    b.para(
        "A prior version of this plan claimed that roughly 58% of stabilized revenue was "
        "real-property income. That claim was overstated and has been corrected. At "
        "stabilization:")
    b.table(["Category", "Share of gross revenue", "Character"], [
        ["Fixed pad rent", pct(y2["contractual_revenue_share"]),
         "Contractual, once leases are signed"],
        ["Pad rent + percentage rent + event parking",
         pct(y2["real_property_revenue_share"]),
         "Property-related, but percentage rent varies with vendor sales"],
        ["Event-dependent revenue (parking, bar and beverage uplift)",
         pct(y2["event_dependent_revenue_share"]),
         "Transactional — not contractual"],
    ], widths=[2.6, 1.5, 2.2])
    b.note(
        "Event parking is transactional revenue, not contractual real-property income, and "
        "is no longer presented as the latter.")

    b.h2("Leasing Plan")
    b.bullets([
        "Convert the six expressions of interest into executed six-month leases, "
        "prioritizing complementary cuisines.",
        "Direct outreach to Austin-area operators without a permanent pad and to operators "
        "at parks with waiting lists.",
        "A defined, documented and time-limited rent abatement where necessary to secure an "
        "anchor vendor — not an open-ended discount.",
        "Maintain a waiting list so a departure is backfilled quickly, which is what the "
        f"{pct(m.TRUCK_OCCUPANCY, 0)} occupancy assumption represents.",
    ])
    b.para(
        f"Vendor leases will restrict trucks to food only, reserving generic soda, juice, "
        "water and coffee for the park while permitting vendors' own signature drinks. The "
        "daytime beverage projection depends on that lease term.")


def s7_market(b, d):
    b.pagebreak()
    b.h1("7.  Market, Competition, Parking and Event Comparables")

    b.h2("Location")
    b.para(
        "The site fronts FM 812 directly opposite Circuit of the Americas property; the two "
        "are separated only by the FM 812 right-of-way. COTA event parking operates "
        "immediately across the road. The nearest COTA parking facility (Lot T) is 0.5 miles "
        "by road, and the main public entrance at 9201 Circuit of the Americas Boulevard is "
        "1.3 miles by road.")
    b.note(
        "Distances re-measured September 2026. A prior version of this plan alternated "
        "between 0.5 miles and two miles without stating which measurement each referred to; "
        "the review flagged the inconsistency. Whether the land immediately across FM 812 is "
        "owned or merely operated by COTA is a title question and is on the evidence list.")

    b.table(["Attribute", "Detail"], [
        ["Address", "13901 FM 812, Del Valle, Texas 78617 (Travis County)"],
        ["Parcel size", f"{m.LAND_ACRES} acres (1.500 + 2.932 deeded tracts), owned free and clear"],
        ["Adjacent retail", "Dollar General immediately adjacent"],
        ["Site allocation", f"{m.TRUCK_SLOTS} serviced pads, container bar, covered seating; "
                            f"dedicated 3-acre event parking area "
                            f"({m.EVENT_PARKING_SPACES} spaces)"],
    ], widths=[1.6, 5.0])

    b.h2("Event Calendar as Modelled")
    b.para(
        f"Twelve event occasions are modelled per year across seven paid tiers plus one "
        "unpriced category. Multi-day weekends build toward the marquee day rather than "
        "selling out uniformly.")
    rows = []
    for key, tier in m.COTA_EVENT_TIERS.items():
        count = sum(1 for month in m.COTA_EVENTS_BY_MONTH.values() for k in month if k == key)
        rows.append([
            tier["name"],
            money(tier["parking_price"]) if tier["parking_price"] else "Free",
            str(len(tier["daily_occupancy"])),
            f"{count}x per year" if count else "Not in modelled year",
        ])
    b.table(["Event tier", "Parking", "Days", "Modelled frequency"], rows,
            widths=[3.0, 0.9, 0.7, 1.7])
    b.note(
        "A prior version described six tiers and named the NASCAR round the EchoPark Grand "
        "Prix. Both are corrected: seven paid tiers, and the 2027 COTA NASCAR event is the "
        "DuraMAX Texas Grand Prix. Each event should be tied to a named date and labelled "
        "Confirmed, Date TBD or Illustrative before submission.")
    _placeholder(b,
        "TO BE COMPLETED BY BORROWER — the review asked that each modelled event be tied to "
        "a named event, date, sellable days, capacity, price and occupancy, and labelled "
        "Confirmed / Date TBD / Illustrative. The 2026 Formula 1 United States Grand Prix is "
        "confirmed for Oct 22–25 and the COTA agreement runs through 2034.")

    b.h2("Competition")
    _placeholder(b,
        "TO BE COMPLETED BY BORROWER — the review rejected the claim that no competitor "
        "combines this site's advantages and asked for a documented competitor table. "
        "Include at minimum: COTALAND (opened September 26, 2026 — likely to generate "
        "year-round traffic but also directly competitive in dining, snacks and bar); "
        "established taco operators in the immediate trade area; at least one private COTA "
        "parking-and-food operator; established Austin food truck parks competing for "
        "vendors; and the adjacent Dollar General and nearby smoke shop for packaged goods. "
        "For each, note distance, offering, price point and how this site differs.")
    b.para(
        "The plan deliberately excludes tobacco, nicotine and packaged convenience goods "
        "from the revenue model, because the adjacent Dollar General sells them at prices "
        "this site cannot beat.")

    b.h2("Parking")
    b.para(
        f"The dedicated three-acre lot is modelled at {m.EVENT_PARKING_SPACES} spaces at "
        f"{m.PEOPLE_PER_CAR} occupants per vehicle. The independent review noted that this "
        "is geometrically possible at roughly 484 square feet per vehicle but is not "
        "validated without a sealed layout covering circulation, queuing, drainage, "
        "pedestrian routes, emergency access, lighting, accessible routes and accessible "
        "space count.")
    _placeholder(b,
        "TO BE COMPLETED BY BORROWER — sealed parking layout, TxDOT driveway approval, and "
        "three documented private-lot price comparisons supporting the modelled event "
        "parking rates.")


def s8_projections(b, d):
    b.pagebreak()
    b.h1("8.  Financial Projections")
    y1, y2, y1_months = d["y1"], d["y2"], d["y1_months"]

    b.para(
        "Every figure in this section is generated directly from the project's financial "
        "model, which computes each month from underlying unit assumptions — vendor counts, "
        "customer counts, item prices, event-day occupancy — rather than by escalating a "
        "starting revenue figure. The model carries an automated regression suite verifying "
        "that revenue, costs and net operating income reconcile exactly.")
    b.note(
        "This document is produced by a generator that imports the model directly, so the "
        "narrative and the projections cannot drift apart. A prior version was typed by hand "
        "and had already fallen out of step with the model by the time it was reviewed.")

    b.h2("8.1  Year 1 — Monthly Operating Statement")
    rows = []
    for mo in y1_months:
        rows.append([
            _month_name(mo["month"])[:3],
            money(mo["total_gross_revenue"]),
            money(mo["total_gross_revenue"] - mo["noi"] - mo["opex_charged"]),
            money(mo["opex_charged"]),
            money(mo["noi"]),
            money(mo["net_cash_flow"]),
            ratio(mo["noi"] / m.MONTHLY_DEBT_SERVICE),
        ])
    y1_variable = sum(mo["total_gross_revenue"] - mo["noi"] - mo["opex_charged"]
                      for mo in y1_months)
    rows.append(["**Year 1**", f"**{money(y1['total_gross'])}**",
                 f"**{money(y1_variable)}**",
                 f"**{money(m.ANNUAL_OPEX_NUT)}**", f"**{money(y1['total_noi'])}**",
                 f"**{money(y1['total_net_cash'])}**",
                 f"**{ratio(y1['total_noi'] / m.ANNUAL_DEBT_SERVICE)}**"])
    b.table(["Month", "Revenue", "Variable cost", "Fixed opex", "NOI", "Net cash", "DSCR"],
            rows, widths=[0.7, 1.0, 1.0, 0.9, 0.9, 0.9, 0.7])

    neg = [mo for mo in y1_months if mo["net_cash_flow"] < 0]
    if neg:
        worst = min(neg, key=lambda x: x["net_cash_flow"])
        b.para(
            f"{len(neg)} of 12 months show negative cash flow in Year 1, totalling "
            f"{money(abs(sum(x['net_cash_flow'] for x in neg)))}, with the worst single "
            f"month at {money(worst['net_cash_flow'])} in "
            f"{_month_name(worst['month'])}. "
            + (f"The reserve remaining at opening ({money(d['pre']['opening_balance'])}) "
               "covers that shortfall."
               if d["pre"]["opening_balance"] >= sum(abs(x["net_cash_flow"]) for x in neg)
               else f"The reserve remaining at opening ({money(d['pre']['opening_balance'])}) "
                    "does not cover that shortfall on its own — see the liquidity "
                    "discussion in the Executive Summary."))

    b.h2("8.2  Year 1 and Stabilized — Full Operating Statement")
    b.table(["Line item", "Year 1", "Stabilized"], [
        ["**REVENUE**", "", ""],
        ["Food truck pad rent", money(y1["total_truck_rent"]), money(y2["total_truck_rent"])],
        ["Food truck percentage rent", money(y1["total_truck_share"]), money(y2["total_truck_share"])],
        ["Evening bar", money(y1["total_bar"]), money(y2["total_bar"])],
        ["Daytime beverages", money(y1["total_daytime_beverage"]), money(y2["total_daytime_beverage"])],
        ["COTA events (parking, bar, beverage)",
         money(y1["total_cota_parking"] + y1["total_cota_bar"] + y1["total_cota_daytime_bev"]),
         money(y2["total_cota_parking"] + y2["total_cota_bar"] + y2["total_cota_daytime_bev"])],
        ["Seasonal watch parties", money(y1["total_seasonal"]), money(y2["total_seasonal"])],
        ["Utility rebilling (at cost)", money(y1["total_utility_billed"]), money(y2["total_utility_billed"])],
        ["**Gross revenue**", f"**{money(y1['total_gross'])}**", f"**{money(y2['total_gross'])}**"],
        ["**VARIABLE COSTS**", "", ""],
        ["Cost of goods — bar", money(y1["total_cogs"]), money(y2["total_cogs"])],
        ["Cost of goods — daytime beverages",
         money(y1["total_daytime_beverage_cogs"]), money(y2["total_daytime_beverage_cogs"])],
        ["TX mixed beverage gross receipts tax", money(y1["total_grt"]), money(y2["total_grt"])],
        ["TX mixed beverage sales tax", money(y1["total_mb_sales_tax"]), money(y2["total_mb_sales_tax"])],
        ["Sales tax — daytime beverages",
         money(y1["total_daytime_beverage_tax"]), money(y2["total_daytime_beverage_tax"])],
        ["Sales tax — event parking",
         money(y1["total_cota_parking_sales_tax"]), money(y2["total_cota_parking_sales_tax"])],
        ["Labor — scheduled wages", money(y1["total_labor_wages"]), money(y2["total_labor_wages"])],
        ["Employer payroll burden", money(y1["total_payroll_burden"]), money(y2["total_payroll_burden"])],
        ["Card processing", money(y1["total_cc_processing"]), money(y2["total_cc_processing"])],
        ["Shrinkage", money(y1["total_shrinkage"]), money(y2["total_shrinkage"])],
        ["COTA parking upkeep", money(y1["total_cota_parking_upkeep"]), money(y2["total_cota_parking_upkeep"])],
        ["COTA event staffing and facilities", money(y1["total_cota_cost"]), money(y2["total_cota_cost"])],
        ["Utility cost (offsets rebilling)", money(y1["total_utility_cost"]), money(y2["total_utility_cost"])],
        [f"Property management fee ({pct(m.MANAGEMENT_FEE_RATE, 0)} of EGI)",
         money(y1["total_management_fee"]), money(y2["total_management_fee"])],
        [f"Replacement reserve ({pct(m.REPLACEMENT_RESERVE_RATE, 0)} of EGI)",
         money(y1["total_replacement_reserve"]), money(y2["total_replacement_reserve"])],
        ["**Fixed operating costs**", f"**{money(m.ANNUAL_OPEX_NUT)}**", f"**{money(m.ANNUAL_OPEX_NUT)}**"],
        ["**NET OPERATING INCOME**", f"**{money(y1['total_noi'])}**", f"**{money(y2['total_noi'])}**"],
        ["Debt service (principal and interest)", money(m.ANNUAL_DEBT_SERVICE), money(m.ANNUAL_DEBT_SERVICE)],
        ["**Net cash flow before tax**", f"**{money(y1['total_net_cash'])}**",
         f"**{money(y2['total_net_cash'])}**"],
        [f"Estimated income tax ({pct(m.EFFECTIVE_INCOME_TAX_RATE, 0)} blended)",
         money(y1["income_tax"]), money(y2["income_tax"])],
        ["**DEBT SERVICE COVERAGE RATIO**",
         f"**{ratio(y1['total_noi'] / m.ANNUAL_DEBT_SERVICE)}**",
         f"**{ratio(y2['total_noi'] / m.ANNUAL_DEBT_SERVICE)}**"],
    ], widths=[3.4, 1.6, 1.6])
    b.note(
        "The stabilized column is a steady-state run rate at Year 1 cost levels. Multi-year "
        "projections apply cost inflation line by line to operating costs and wages; debt "
        "service does not inflate, being fixed by the amortization schedule.")

    b.h2("8.3  Risk Analysis and Mitigants")
    b.para(
        "Each downside the independent review asked for is modelled below, paired with what "
        "actually absorbs it. The borrower's view is that the transaction is underwritten by "
        "the balance sheet — low leverage, unencumbered collateral and corporate "
        "guarantees — rather than by the operating projections alone, and the cases below "
        "are presented in that light.")
    b.table(["Stabilized case", "Revenue", "NOI", "Net cash", "DSCR"], [
        ["Full event calendar (base)", money(d["y2"]["total_gross"]),
         money(d["y2"]["total_noi"]), money(d["y2"]["total_net_cash"]),
         f"**{ratio(d['y2']['total_noi'] / m.ANNUAL_DEBT_SERVICE)}**"],
        ["COTA activity halved", money(d["halfcota"]["total_gross"]),
         money(d["halfcota"]["total_noi"]), money(d["halfcota"]["total_net_cash"]),
         ratio(d["halfcota"]["total_noi"] / m.ANNUAL_DEBT_SERVICE)],
        ["No COTA revenue whatsoever", money(d["nocota"]["total_gross"]),
         money(d["nocota"]["total_noi"]), money(d["nocota"]["total_net_cash"]),
         f"**{ratio(d['nocota']['total_noi'] / m.ANNUAL_DEBT_SERVICE)}**"],
        [f"Combined stress at {pct(d['bank']['loan_rate'])} rate", "—",
         money(d["bank"]["stabilized_noi"]), "—", ratio(d["bank"]["dscr"])],
    ], widths=[2.2, 1.2, 1.2, 1.2, 0.9])

    b.h3("Event concentration — the material risk")
    nocota_dscr = d["nocota"]["total_noi"] / m.ANNUAL_DEBT_SERVICE
    half_dscr = d["halfcota"]["total_noi"] / m.ANNUAL_DEBT_SERVICE
    b.para(
        f"COTA event weekends contribute {pct(d['y1']['event_dependent_revenue_share'])} of "
        f"projected Year 1 revenue and {pct(d['y2']['event_dependent_revenue_share'])} at "
        "stabilization. There is no contractual relationship with COTA. This is the "
        "principal risk in the credit and the borrower does not present it as anything "
        "smaller.", bold=True)
    b.para(
        "A prior version of this plan argued that a permanent loss of COTA would still leave "
        "coverage at 1.94x, and concluded that COTA was 'the upside in this deal, not the "
        "foundation.' That conclusion rested on projections carrying no scheduled labor "
        f"cost, and it is withdrawn. With payroll loaded, a no-COTA year covers debt service "
        f"at {ratio(nocota_dscr)} with the full staffing schedule still in place. A real "
        "operator would cut hours in that case, so this is a floor on the outcome rather "
        "than a forecast — but it is well below a conventional 1.35x minimum, and a total, "
        "permanent loss of COTA is not something this credit absorbs on operating cash flow "
        "alone.")
    b.para("What supports the concentration:", bold=True)
    b.bullets([
        "The Formula 1 agreement with COTA runs through 2034 — a nine-year contracted "
        "runway at the venue that drives the single largest event weekend.",
        "The calendar is multi-series, not single-event: MotoGP, NASCAR, endurance racing, "
        "club racing and amphitheater concerts. Losing any one does not remove the category.",
        f"Halving all event activity — a far more probable scenario than total loss — "
        f"leaves {ratio(half_dscr)} coverage and {money(d['halfcota']['total_net_cash'])} of "
        "cash flow after debt service"
        + (", above a 1.35x floor." if half_dscr >= 1.35 else
           ", below a 1.35x floor, and the borrower states it that way."),
        f"The loan is {money(m.LOAN_AMOUNT)} against {money(m.EQUITY_BASIS)} of borrower "
        "equity and unencumbered land. The lender's exposure in a severe downside is "
        "governed by the collateral, not by the operating projections.",
    ])

    b.h3("Delayed opening and cost overrun")
    tracker = d["tracker"]
    b.para(
        f"Each additional month of delay consumes {money(d['pre']['monthly_burn'])} of loan "
        "payments and accounting with no offsetting revenue, and shifts the revenue ramp. "
        f"At the projected schedule the reserve already reaches a low of "
        f"{money(tracker['min_balance'])} after opening, so there is "
        + ("no reserve headroom for delay: any slip must be funded by the sponsor."
           if tracker["min_balance"] <= 0 else
           f"room for roughly {int(tracker['min_balance'] // d['pre']['monthly_burn'])} "
           "months of delay before the reserve is exhausted.")
        + f" Cost overrun is separately buffered by the {money(_use('Contingency'))} "
        "contingency, and the reserve is the plug, so a higher quote raises the request "
        "rather than eating the reserve.")
    b.note(
        "This is a simplification: a delayed opening also shifts the seasonal profile of the "
        "first operating year, which the figure above does not model.")

    b.h2("8.4  Named Scenarios")
    rows = []
    for name, ann in d["scenarios"].items():
        rows.append([name, money(ann["total_gross"]), money(ann["total_noi"]),
                     money(ann["total_net_cash"]),
                     ratio(ann["total_noi"] / m.ANNUAL_DEBT_SERVICE)])
    b.table(["Scenario", "Revenue", "NOI", "Net cash", "DSCR"], rows,
            widths=[1.8, 1.3, 1.3, 1.3, 0.9])
    b.note(
        "Scenario definitions vary vendor count, occupancy, bar traffic, check size, event "
        "calendar and seasonal strength together, and are shown on the Year 1 ramped basis. "
        "The labels predate the addition of scheduled payroll and should be read against "
        "what each actually assumes rather than by name: 'Conservative' assumes only three "
        "of four pads leased at 83% occupancy, and 'Stress Test' assumes three pads plus "
        "loss of all but the three largest events. Neither covers debt service once payroll "
        "is loaded. This is the same concentration point made above, approached from the "
        "vendor side: the combination of an unfilled lot and a thin event calendar is what "
        "breaks coverage, and either one alone does not.")

    b.h2("8.5  Monte Carlo — Disclosed Inputs")
    b.para(
        f"The simulation runs at random seed {m.MONTE_CARLO_DEFAULT_SEED} and is "
        "deterministic for a given seed. The review could not reproduce a previously quoted "
        "result, so the inputs are published here. Each parameter is drawn around the "
        "model's base-case value and clipped to the bounds shown.")
    b.table(["Parameter", "Distribution", "Spread or values", "Bounds"],
            [_mc_row(r) for r in m.MONTE_CARLO_SPEC],
            widths=[2.4, 1.3, 1.6, 1.3])
    b.para(
        "Every parameter is drawn independently. This is a real simplification and it "
        "understates the downside: in practice a poor year would depress bar traffic, vendor "
        "sales and event attendance together. The low percentiles should be read as "
        "optimistic, not conservative.", bold=True)


def _mc_row(spec):
    """One disclosed Monte Carlo input, whatever its distribution type."""
    name = spec["name"].replace("_", " ")
    kind = spec["distribution"].replace("_", " ")
    if "values" in spec:
        return [name, kind, ", ".join(str(v) for v in spec["values"]), "—"]
    if "sigma" in spec:
        return [name, kind, f"sigma {spec['sigma']}", f"{spec['low']} – {spec['high']}"]
    return [name, kind, "—", "—"]


def s9_appendix(b, d):
    b.pagebreak()
    b.h1("9.  Supporting Documents and Assumptions")

    b.h2("A.  Site Work Completed to Date")
    b.para(
        f"The following items, totalling {money(m.PHASE_0_5_TOTAL)}, were financed through "
        "the borrower's personal line of credit and are largely complete. They are excluded "
        "from the Use of Funds — this loan refinances the line of credit that paid for them, "
        "so counting them again would double-count the same dollars — but they are included "
        "in the capitalized basis.")
    items = [(label, amt) for label, amt, *_ in m.PHASE_0_5_CAPITAL_IMPROVEMENTS]
    half = (len(items) + 1) // 2
    rows = []
    for i in range(half):
        left = items[i]
        right = items[i + half] if i + half < len(items) else ("", "")
        rows.append([left[0], money(left[1]) if left[1] else "",
                     right[0], money(right[1]) if right[1] else ""])
    b.table(["Item", "Cost", "Item", "Cost"], rows, widths=[2.1, 0.9, 2.1, 0.9])

    b.h2("B.  Key Assumptions")
    b.table(["Assumption", "Value", "Basis"], [
        ["Food truck pads", str(m.TRUCK_SLOTS), "Budgeted scope"],
        ["Pad rent per month", money(m.TRUCK_PAD_RENT), "Intended terms — no signed leases"],
        ["Percentage rent", pct(m.TRUCK_REV_SHARE_RATE, 0), "Intended terms — no signed leases"],
        ["Assumed vendor monthly sales", money(m.TRUCK_AVG_MONTHLY_SALES), "Estimate"],
        ["Steady-state occupancy", pct(m.TRUCK_OCCUPANCY, 0), "Conservative — no leasing record"],
        ["Bar customers, weekday / weekend",
         f"{m.BAR_WEEKDAY_CUSTOMERS} / {m.BAR_WEEKEND_CUSTOMERS}", "Estimate"],
        ["Bar average check", money(m.BAR_AVG_CHECK, cents=True), "Derived from menu and item mix"],
        ["Bar cost of goods", pct(m.COGS_RATE), "Revenue-weighted; cocktail cost padded"],
        ["Daytime beverage attach rate", pct(m.DAYTIME_BEVERAGE_ATTACH_RATE, 0),
         "Estimate — least validated input"],
        ["Event parking spaces", str(m.EVENT_PARKING_SPACES), "3-acre lot — layout not sealed"],
        ["Beverage attendant / bartender wage",
         f"{money(m.DAYTIME_ATTENDANT_WAGE, cents=True)} / {money(m.EVENING_BARTENDER_WAGE, cents=True)}",
         "Market estimate — confirm with real offers"],
        ["Manager cash salary", money(m.MANAGER_ANNUAL_SALARY), "Below market; housing provided"],
        ["Loan rate assumed", pct(m.LOAN_INTEREST_RATE), "Placeholder pending bank quote"],
        ["Opening date", f"{_month_name(m.OPENING_MONTH)} {m.OPENING_YEAR}",
         "Estimate pending construction schedule"],
        ["Real estate cap rate", pct(m.PROPERTY_INCOME_CAP_RATE, 2), "Market estimate"],
        ["Business earnings multiple", f"{m.GOING_CONCERN_EBITDA_MULTIPLE:.1f}x", "Market estimate"],
        ["Blended income tax rate", pct(m.EFFECTIVE_INCOME_TAX_RATE, 0), "Estimate — confirm with CPA"],
    ], widths=[2.4, 1.6, 2.6])

    b.h2("C.  Texas Tax Treatment")
    b.para(
        "Menu and gate prices in this plan are tax-inclusive: a posted price is what the "
        "customer pays. The mixed beverage sales tax is therefore backed out of receipts to "
        "reach the taxable sales price, and the mixed beverage gross receipts tax is applied "
        "to that sales price rather than to the full receipt. Event parking is treated the "
        "same way. A prior version applied both rates to the full receipt, which taxed a tax.")
    b.table(["Tax", "Rate", "Applied to"], [
        ["Mixed beverage gross receipts tax", pct(m.GRT_RATE, 1),
         "Alcohol sales price (permittee's own liability)"],
        ["Mixed beverage sales tax", pct(m.MB_SALES_TAX_RATE, 2), "All alcoholic beverages"],
        ["Sales tax — daytime beverages", pct(m.DAYTIME_BEVERAGE_SALES_TAX_RATE, 2),
         "Non-alcoholic beverages"],
        ["Sales tax — event parking", pct(m.PARKING_SALES_TAX_RATE, 2),
         "Parking is a taxable service in Texas"],
        ["Property tax — land", money(m.FIXED_COSTS["property_tax"] * 12) + "/yr", "Actual bill"],
        ["Property tax — improvements",
         money(m.FIXED_COSTS["property_tax_improvements"] * 12) + "/yr",
         f"Estimated at {pct(m.PROPERTY_TAX_IMPROVEMENT_RATE, 1)} of capitalized improvements"],
        ["Employer payroll burden", pct(m.EMPLOYER_PAYROLL_BURDEN_RATE, 0), "All wages"],
        ["Texas franchise tax", "$0 owed", "Below the 2026 $2.65M threshold; report still filed"],
    ], widths=[2.4, 1.3, 2.9])
    b.note(
        "Utility rebilling is assumed to be at cost with no markup. The governing commercial "
        "submetering rule should be confirmed; a prior version asserted this as a legal "
        "requirement without qualification.")

    b.h2("D.  Documents to Accompany This Plan")
    b.bullets([
        "Résumés, personal financial statements and tax returns for each principal",
        "Entity formation documents, certificates of good standing, operating agreements, "
        "and the member consent authorizing this loan and deed of trust",
        "Deeds, title commitment, survey and most recent property tax statement",
        "Independent as-is and as-complete appraisal (to be ordered by the lender)",
        "Line of credit statements, invoices and lien waivers supporting the "
        f"{money(_use('Payoff'))} refinance",
        "Fixed vendor quotes for septic, paving and container bar buildout, with "
        "construction and draw schedules",
        "Permit matrix, sealed site and parking plan, TxDOT access approval, septic approval",
        "Executed vendor leases or letters of intent as obtained",
        "TABC Mixed Beverage Permit — permit number, issue and expiry dates, premises "
        "diagram and licensed premises description",
        "Certificate of insurance or binder quote, including liquor liability",
        "Weekly staffing schedule and confirmation of worker classification",
    ])

    b.h2("E.  Basis of Preparation")
    b.para(
        "Projections are produced by a purpose-built financial model of this property, which "
        "computes each projected month from underlying unit assumptions rather than by "
        "escalating a starting revenue figure. The model carries an automated regression "
        "suite verifying that revenue, variable costs, fixed costs and net operating income "
        "reconcile exactly, and that scenario ordering, tax identities and event-day totals "
        "remain internally consistent. This document is generated from that model. The "
        "borrower will provide the bank with access to the model on request.")
    b.para(
        "This plan contains forward-looking projections. Actual results will differ. Items "
        "identified as estimates — wage rates, insurance, utilities, cocktail cost of goods, "
        "vendor sales volumes, the daytime beverage attach rate, the opening date, the cap "
        "rate and the earnings multiple — carry the greatest uncertainty. The park is not "
        "yet open and has no operating history. Tax treatment, worker classification and the "
        "treatment of employer-provided lodging should be confirmed with a qualified CPA "
        "before filing.")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "Del Valle Food Truck Park - Business Plan.docx"
    d = gather()
    # Format follows the extension: .md emits Markdown (used for Google Docs
    # upload, which Drive converts natively), anything else emits .docx.
    b = MarkdownBuilder() if out.lower().endswith(".md") else PlanBuilder()
    cover(b, d)
    exec_summary(b, d)
    credit_strengths(b, d)
    s1_transaction(b, d)
    s2_repayment(b, d)
    s3_collateral(b, d)
    s4_management(b, d)
    s5_schedule(b, d)
    s6_vendors(b, d)
    s7_market(b, d)
    s8_projections(b, d)
    s9_appendix(b, d)
    b.save(out)
    print(f"Wrote {out}")
    print(f"  Opening:        {_month_name(m.OPENING_MONTH)} {m.OPENING_YEAR}")
    print(f"  Year 1 DSCR:    {d['y1']['total_noi'] / m.ANNUAL_DEBT_SERVICE:.2f}x")
    print(f"  Stabilized:     {d['val']['dscr']:.2f}x")
    print(f"  No-COTA DSCR:   {d['nocota']['total_noi'] / m.ANNUAL_DEBT_SERVICE:.2f}x")


if __name__ == "__main__":
    main()
