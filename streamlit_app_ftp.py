"""
Food Truck Park + Bar & Beverage Stand | Del Valle
Streamlit Financial Model Dashboard (financed via a $500,000 bank term loan)

Run with: streamlit run streamlit_app_ftp.py
"""

import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
import food_truck_park_model as model

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Food Truck Park + Bar & Beverage Stand | Financial Model",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_dollar(val):
    if val < 0:
        return f"-${abs(val):,.0f}"
    return f"${val:,.0f}"


def fmt_pct(val):
    return f"{val:.1f}%"


# =============================================================================
# SIDEBAR — GLOBAL INPUTS
# =============================================================================
st.sidebar.title("Food Truck Park")
st.sidebar.caption("Food Trucks + Bar & Beverage Stand — Del Valle")
st.sidebar.markdown("---")

st.sidebar.subheader("Food Trucks")
truck_slots = st.sidebar.slider("Truck Slots", 2, 10, model.TRUCK_SLOTS, step=1)
truck_rent = st.sidebar.slider("Truck Pad Rent ($/mo)", 500, 1000,
                               model.TRUCK_PAD_RENT, step=50, format="$%d")
truck_share = st.sidebar.slider("Revenue Share (%)", 5.0, 10.0,
                                model.TRUCK_REV_SHARE_RATE * 100, step=0.5) / 100
truck_sales = st.sidebar.slider("Avg Truck Sales ($/mo)", 10_000, 35_000,
                                model.TRUCK_AVG_MONTHLY_SALES, step=1_000,
                                format="$%d")
truck_occupancy = st.sidebar.slider(
    "Truck Occupancy (%)", 50, 100, int(round(model.TRUCK_OCCUPANCY * 100)),
    step=5,
    help="Expected fraction of built slots rented at any time. 6-month "
         "contracts bound churn; a slot sits empty during re-leasing gaps. "
         "100% = always full.") / 100

st.sidebar.subheader("Evening Bar (6pm-close, container bar)")
weekday_customers = st.sidebar.slider("Weekday Customers/Evening (Mon-Thu)", 5, 50,
                                      model.BAR_WEEKDAY_CUSTOMERS, step=1)
weekend_customers = st.sidebar.slider("Weekend Customers/Evening (Fri-Sun)", 15, 100,
                                      model.BAR_WEEKEND_CUSTOMERS, step=2)
avg_check = st.sidebar.slider("Avg Check ($)", 5.0, 20.0, model.BAR_AVG_CHECK,
                              step=0.25, format="$%.2f",
                              help=f"Default \\${model.BAR_AVG_CHECK:.2f} = "
                                   f"{model.DRINKS_PER_VISIT} drinks/visit x the "
                                   f"\\${model.AVG_ITEM_PRICE:.2f} blended item price "
                                   f"(\\${model.DRAFT_BEER_PRICE:.0f} draft / "
                                   f"\\${model.BEER_PRICE:.0f} canned / "
                                   f"\\${model.SHOT_PRICE:.0f} shot / "
                                   f"\\${model.COCKTAIL_PRICE:.0f} cocktail).")

st.sidebar.subheader("All-Day Beverages (soda/juice/water/coffee)")
daytime_bev_price = st.sidebar.slider(
    "Avg Price ($)", 1.5, 5.0, model.DAYTIME_BEVERAGE_AVG_PRICE, step=0.25,
    format="$%.2f")
daytime_bev_attach = st.sidebar.slider(
    "Truck-Customer Attach Rate (%)", 0, 75,
    int(round(model.DAYTIME_BEVERAGE_ATTACH_RATE * 100)), step=5,
    help="Fraction of food-truck customers who also buy a canned/bottled "
         "drink from the bar. Sized off truck traffic (trucks are the "
         "park's only real daytime foot-traffic driver), not an "
         "independent daytime headcount. Requires vendor leases to "
         "restrict trucks to food-only, or this demand leaks to "
         "truck-sold drinks instead.") / 100

st.sidebar.subheader("Other")
seasonal_pct = st.sidebar.slider("Seasonal Event Strength", 0.0, 2.0, 1.0, step=0.25)
cota_impact_multiplier = st.sidebar.slider(
    "COTA Event Impact", 0.0, 2.0, 1.0, step=0.1, format="%.1fx",
    help="0.0x = COTA has no effect at all — parking, bar uplift, and "
         "daytime-beverage uplift all zero out, as if the event calendar "
         "didn't exist. 1.0x (default) reproduces today's baseline modeled "
         "calendar exactly. 2.0x is a deliberately optimistic 'exceptional "
         "events' scenario: COTA revenue runs at 2x today's baseline, AND "
         "event-weekend months pull extra foot traffic into the food "
         "trucks themselves (up to +20% truck sales/occupancy in those "
         "months only) — not just parking and bar customers.")
projection_view = st.sidebar.radio(
    "Projection View",
    ["Year 1 (with ramps)", "Steady state (no ramps)"],
    help="Year 1 applies the cold-start discovery curve to the bar and "
         "beverage streams AND the lease-up curve to the truck slots, so a "
         "slow first few months mixes together ramp effects and winter "
         "seasonality. Steady state strips both ramps out to show the "
         "run-rate business — useful for judging whether the concept works "
         "once it's established, separately from how long it takes to get "
         "there.",
)
projection_year = 1 if projection_view.startswith("Year 1") else 2
view_label = "Year 1" if projection_year == 1 else "Steady State"

st.sidebar.markdown("---")
st.sidebar.subheader("Monte Carlo")
mc_seed = st.sidebar.number_input("Random Seed", value=42, step=1)
mc_sims = st.sidebar.selectbox("Simulations", [1000, 5000, 10000], index=1)


# =============================================================================
# CACHED COMPUTATIONS
# =============================================================================
@st.cache_data
def get_annual(wd_custs, we_custs, check, slots, t_rent, t_share, t_sales, t_occ, seasonal,
               dbev_attach, dbev_price, cota_impact=1.0, yr=1):
    return model.run_annual_projection(
        wd_custs, we_custs, year=yr, avg_check=check,
        truck_slots=slots, truck_rent=t_rent,
        truck_share_rate=t_share, truck_avg_sales=t_sales,
        truck_occupancy=t_occ, seasonal_pct=seasonal,
        daytime_beverage_attach_rate=dbev_attach,
        daytime_beverage_avg_price=dbev_price,
        cota_impact_multiplier=cota_impact,
    )


@st.cache_data
def get_multi_year(wd_custs, we_custs, check, slots, t_rent, t_share, t_sales, t_occ, seasonal,
                   dbev_attach, dbev_price, cota_impact=1.0, years=3):
    return model.run_multi_year_projection(
        wd_custs, we_custs, years=years, base_check=check,
        truck_slots=slots, truck_rent=t_rent,
        truck_share_rate=t_share, truck_avg_sales=t_sales,
        truck_occupancy=t_occ, seasonal_pct=seasonal,
        daytime_beverage_attach_rate=dbev_attach,
        daytime_beverage_avg_price=dbev_price,
        cota_impact_multiplier=cota_impact,
    )


@st.cache_data
def get_monte_carlo(n_sims, seed, wd_custs, we_custs, check, t_rent, t_share, t_occ, seasonal,
                    slots, t_sales, dbev_attach, dbev_price, cota_impact=1.0):
    return model.run_monte_carlo(
        n_sims, seed,
        base_weekday_customers=wd_custs, base_weekend_customers=we_custs,
        base_check=check, base_truck_rent=t_rent, base_truck_share=t_share,
        base_truck_occupancy=t_occ, base_seasonal_pct=seasonal,
        base_truck_slots=slots, base_truck_avg_sales=t_sales,
        base_daytime_beverage_attach_rate=dbev_attach,
        base_daytime_beverage_avg_price=dbev_price,
        base_cota_impact_multiplier=cota_impact,
    )


@st.cache_data
def get_scenario_results():
    results = {}
    for name, params in model.SCENARIOS.items():
        _, ann = model.run_scenario_projection(params)
        results[name] = ann
    return results


def months_to_df(months):
    rows = []
    for m in months:
        cota = (m["cota_parking"] + m["cota_bar_uplift"]
               + m["cota_daytime_bev_uplift"])
        rows.append({
            "Month": MONTH_NAMES[m["month"] - 1],
            "Gross Revenue": m["total_gross_revenue"],
            "Food Trucks": m["truck_gross"],
            "Evening Bar": m["bar_revenue"],
            "Daytime Beverages": m["daytime_beverage_revenue"],
            "COTA": cota,
            "Seasonal": m["seasonal_revenue"],
            "Utilities (pass-thru)": m["utility_billed"],
            "Trucks Active": m["trucks_active"],
            "NOI": m["noi"],
            "Nut Coverage": m["monthly_nut_coverage"],
            "Cash Flow": m["net_cash_flow"],
        })
    return pd.DataFrame(rows)


# Shared computation for current sidebar inputs. `projection_year` is 1 for
# the ramped Year 1 view and 2 for the steady-state run-rate view; the model
# applies ramps only when year == 1.
months, annual = get_annual(weekday_customers, weekend_customers, avg_check,
                            truck_slots, truck_rent, truck_share, truck_sales,
                            truck_occupancy, seasonal_pct,
                            daytime_bev_attach, daytime_bev_price,
                            cota_impact_multiplier, yr=projection_year)
df = months_to_df(months)


# =============================================================================
# MAIN CONTENT — TABS
# =============================================================================
st.title("Food Truck Park + Bar & Beverage Stand")
st.caption(f"{model.PROPERTY_ADDRESS}  •  "
           f"Project Cost: \\${model.TOTAL_PROJECT_COST:,.0f} "
           f"(loan @ {model.LOAN_INTEREST_RATE:.1%}/{model.LOAN_TERM_YEARS}yr)")
st.caption(
    f"Borrower: {model.BORROWER_ENTITY}. Operating: {model.OPERATING_ENTITY}. "
    f"Parent: {model.PARENT_ENTITY}. Address on the deeded site is 13901 FM 812 "
    "(not 13903). Formation state, good standing, and guarantor documents are "
    "outside this model."
)

h0, h1, h2, h3 = st.columns(4)
h0.metric(f"Gross Monthly Revenue ({view_label})",
          fmt_dollar(annual["total_gross"] / 12),
          help="Average month across all revenue streams (food trucks, "
               "evening bar, daytime beverages, COTA events, seasonal "
               "watch parties, and the at-cost utility pass-through), at "
               "the current sidebar inputs. This is an average — individual "
               "months swing widely with Austin patio seasonality and the "
               "COTA event calendar; see the Dashboard's monthly chart. "
               "Switch Year 1 / Steady State with the sidebar's Projection "
               "View toggle.")
h1.metric("Monthly Loan Payment", fmt_dollar(model.LOAN_MONTHLY_PAYMENT),
          help="Fixed principal + interest on the bank loan. See Owner "
               "Summary for the year-by-year principal/interest split.")
h2.metric("Other Monthly Fixed Costs", fmt_dollar(model.MONTHLY_OPEX_NUT),
          help=f"{len(model.OPERATING_FIXED_COSTS)} other line items — "
               "insurance, property tax, utilities, "
               "licenses, marketing, and more. See Owner Summary for the "
               "full itemized breakdown.")
h3.metric("Total Monthly Nut", fmt_dollar(model.MONTHLY_NUT),
          help="Loan payment + all other fixed costs — what the business "
               "must cover every month regardless of revenue.")

tabs = st.tabs([
    "Dashboard",
    "Annual Projection",
    "Sensitivity",
    "Break-Even",
    "Monte Carlo",
    "Scenarios",
    "Multi-Year",
    "Waterfall",
    "Owner Summary",
    "Tax Strategies",
    "📖 Model Overview",
    "🏦 CRE Investment Summary",
])


# =============================================================================
# TAB 0: DASHBOARD
# =============================================================================
with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annual Revenue", fmt_dollar(annual["total_gross"]))
    c2.metric("FCF Yield (pre-tax)", fmt_pct(annual["fcf_yield"] * 100))
    c3.metric("Free Cash Flow (pre-tax)", fmt_dollar(annual["total_net_cash"]))
    c4.metric("Min Monthly Nut Coverage", f"{annual['min_monthly_nut_coverage']:.2f}x")

    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Est. Income Tax (28%)", fmt_dollar(annual["income_tax"]),
              help="Blended effective federal + self-employment rate estimate "
                   "on pass-through profit. TX has no state income tax. "
                   "Confirm actual rate with a CPA.")
    t2.metric("After-Tax FCF Yield", fmt_pct(annual["after_tax_fcf_yield"] * 100))
    t3.metric("After-Tax Cash Flow", fmt_dollar(annual["after_tax_noi"]))
    t4.metric("Monthly Nut", fmt_dollar(model.MONTHLY_NUT))

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader(f"Revenue Breakdown ({view_label})")
        cota_total = (annual["total_cota_parking"] + annual["total_cota_bar"]
                     + annual["total_cota_daytime_bev"])
        rev_data = {
            "Stream": ["Food Trucks", "Evening Bar", "Daytime Beverages",
                       "COTA Events", "Seasonal", "Utilities (at cost)"],
            "Revenue": [annual["total_trucks"], annual["total_bar"],
                        annual["total_daytime_beverage"],
                        cota_total, annual["total_seasonal"],
                        annual["total_utility_billed"]],
        }
        fig_pie = px.pie(
            pd.DataFrame(rev_data), values="Revenue", names="Stream",
            hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("Monthly Revenue & Nut Coverage")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["Month"], y=df["Gross Revenue"],
            name="Gross Revenue", marker_color="#4E79A7"
        ))
        fig.add_trace(go.Scatter(
            x=df["Month"], y=df["Nut Coverage"],
            name="Nut Coverage", yaxis="y2",
            mode="lines+markers", marker_color="#E15759", line=dict(width=3)
        ))
        fig.add_hline(y=1.0, line_dash="dash", line_color="red",
                      annotation_text="Break-even (1.0x)", yref="y2")
        fig.update_layout(
            yaxis=dict(title="Revenue ($)", tickformat="$,.0f"),
            yaxis2=dict(title="Nut Coverage", overlaying="y", side="right", tickformat=".1f"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"Fill Trajectory ({view_label})")
    fig_fill = go.Figure()
    fig_fill.add_trace(go.Scatter(
        x=df["Month"], y=df["Trucks Active"], name="Trucks Active",
        mode="lines+markers", line=dict(color="#F28E2B", width=3)
    ))
    fig_fill.update_layout(
        yaxis=dict(title="Count"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig_fill, use_container_width=True)


# =============================================================================
# TAB 1: ANNUAL PROJECTION
# =============================================================================
with tabs[1]:
    st.header(f"Annual Projection — {view_label}")

    stream_cols = ["Food Trucks", "Evening Bar", "Daytime Beverages", "COTA", "Seasonal"]
    fig_stack = go.Figure()
    colors = px.colors.qualitative.Set2
    for i, col in enumerate(stream_cols):
        fig_stack.add_trace(go.Bar(
            x=df["Month"], y=df[col], name=col,
            marker_color=colors[i % len(colors)]
        ))
    fig_stack.update_layout(
        barmode="stack",
        yaxis=dict(title="Revenue ($)", tickformat="$,.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", fmt_dollar(annual["total_gross"]))
    c2.metric("FCF Yield", fmt_pct(annual["fcf_yield"] * 100))
    c3.metric("Free Cash Flow", fmt_dollar(annual["total_net_cash"]))
    c4.metric("Scheduled Labor (wages)", fmt_dollar(annual["total_labor_wages"]))

    st.subheader("Revenue Streams")
    stream_data = {
        "Stream": ["Food Truck Rent", "Food Truck Rev Share",
                   "Evening Bar", "Daytime Beverages",
                   "COTA Parking", "COTA Bar Uplift", "COTA Daytime Bev Uplift",
                   "Seasonal Events",
                   "Utility Pass-Through (at cost)"],
        "Annual": [annual["total_truck_rent"], annual["total_truck_share"],
                   annual["total_bar"], annual["total_daytime_beverage"],
                   annual["total_cota_parking"],
                   annual["total_cota_bar"], annual["total_cota_daytime_bev"],
                   annual["total_seasonal"],
                   annual["total_utility_billed"]],
    }
    stream_df = pd.DataFrame(stream_data)
    stream_df["% of Total"] = stream_df["Annual"] / annual["total_gross"] * 100
    stream_df["Annual"] = stream_df["Annual"].apply(fmt_dollar)
    stream_df["% of Total"] = stream_df["% of Total"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(stream_df, use_container_width=True, hide_index=True)

    st.caption("Utility pass-through is billed at cost per Texas PUC resale rules "
               "(PURA §39.107) — it adds gross revenue but zero NOI.")

    st.subheader("Monthly Detail")
    display_df = df[["Month", "Gross Revenue", "Food Trucks", "Evening Bar",
                     "Daytime Beverages", "COTA", "NOI",
                     "Cash Flow", "Nut Coverage"]].copy()
    for col in ["Gross Revenue", "Food Trucks", "Evening Bar", "Daytime Beverages",
               "COTA", "NOI", "Cash Flow"]:
        display_df[col] = display_df[col].apply(fmt_dollar)
    display_df["Nut Coverage"] = display_df["Nut Coverage"].apply(lambda x: f"{x:.2f}x")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# =============================================================================
# TAB 2: SENSITIVITY
# =============================================================================
with tabs[2]:
    st.header("Sensitivity Analysis")

    st.subheader("1. Food Truck Count Impact")
    slot_rows = []
    for slots in [2, 3, 4, 5, 6, 8, 10]:
        _, ann = model.run_annual_projection(
            weekday_customers, weekend_customers, avg_check=avg_check,
            truck_slots=slots, truck_rent=truck_rent,
            truck_share_rate=truck_share, truck_avg_sales=truck_sales,
            truck_occupancy=truck_occupancy,
            cota_impact_multiplier=cota_impact_multiplier,
        )
        slot_rows.append({
            "Trucks": slots,
            "Annual Revenue": ann["total_gross"],
            "Free Cash Flow": ann["total_net_cash"],
            "Nut Coverage": ann["avg_monthly_nut_coverage"],
        })
    slot_df = pd.DataFrame(slot_rows)
    fig_slot = go.Figure()
    fig_slot.add_trace(go.Bar(
        x=slot_df["Trucks"], y=slot_df["Free Cash Flow"],
        name="Free Cash Flow", marker_color="#4E79A7"
    ))
    fig_slot.add_trace(go.Scatter(
        x=slot_df["Trucks"], y=slot_df["Nut Coverage"],
        name="Nut Coverage", yaxis="y2", mode="lines+markers",
        marker_color="#E15759", line=dict(width=3)
    ))
    fig_slot.add_hline(y=1.0, line_dash="dash", line_color="red",
                       annotation_text="Break-even", yref="y2")
    fig_slot.update_layout(
        yaxis=dict(title="Free Cash Flow ($)", tickformat="$,.0f"),
        yaxis2=dict(title="Nut Coverage", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_slot, use_container_width=True)
    disp = slot_df.copy()
    for col in ["Annual Revenue", "Free Cash Flow"]:
        disp[col] = disp[col].apply(fmt_dollar)
    disp["Nut Coverage"] = disp["Nut Coverage"].apply(lambda x: f"{x:.2f}x")
    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.subheader("2. Truck Count x Avg Sales Grid (Nut Coverage)")
    grid_rows = []
    for sales in [10_000, 15_000, 20_000, 25_000, 30_000]:
        row = {"Avg Truck Sales": fmt_dollar(sales)}
        for slots in [3, 4, 5, 6, 8]:
            _, ann = model.run_annual_projection(
                weekday_customers, weekend_customers, avg_check=avg_check,
                truck_slots=slots, truck_rent=truck_rent,
                truck_share_rate=truck_share, truck_avg_sales=sales,
                truck_occupancy=truck_occupancy,
                cota_impact_multiplier=cota_impact_multiplier,
            )
            row[f"{slots} trucks"] = f"{ann['avg_monthly_nut_coverage']:.2f}x"
        grid_rows.append(row)
    st.dataframe(pd.DataFrame(grid_rows), use_container_width=True, hide_index=True)

    st.subheader("3. Bar Traffic Impact")
    st.caption("Scales weekday and weekend customer counts together, holding "
               "their current ratio fixed.")
    bar_rows = []
    for mult in [0.33, 0.6, 0.83, 1.0, 1.25, 1.5, 1.83]:
        wd = round(weekday_customers * mult)
        we = round(weekend_customers * mult)
        _, ann = model.run_annual_projection(
            wd, we, avg_check=avg_check,
            truck_slots=truck_slots, truck_rent=truck_rent,
            truck_share_rate=truck_share, truck_avg_sales=truck_sales,
            truck_occupancy=truck_occupancy,
            cota_impact_multiplier=cota_impact_multiplier,
        )
        bar_rows.append({
            "Weekday/Weekend Customers": f"{wd} / {we}",
            "Annual Revenue": fmt_dollar(ann["total_gross"]),
            "Free Cash Flow": fmt_dollar(ann["total_net_cash"]),
            "Nut Coverage": f"{ann['avg_monthly_nut_coverage']:.2f}x",
        })
    st.dataframe(pd.DataFrame(bar_rows), use_container_width=True, hide_index=True)

    st.subheader("4. Truck Occupancy Impact (vendor vacancy / churn)")
    occ_rows = []
    for occ in [0.60, 0.70, 0.80, 0.90, 1.0]:
        _, ann = model.run_annual_projection(
            weekday_customers, weekend_customers, avg_check=avg_check,
            truck_slots=truck_slots, truck_rent=truck_rent,
            truck_share_rate=truck_share, truck_avg_sales=truck_sales,
            truck_occupancy=occ,
            cota_impact_multiplier=cota_impact_multiplier,
        )
        occ_rows.append({
            "Occupancy": f"{occ:.0%}",
            "Annual Revenue": fmt_dollar(ann["total_gross"]),
            "Free Cash Flow": fmt_dollar(ann["total_net_cash"]),
            "Nut Coverage": f"{ann['avg_monthly_nut_coverage']:.2f}x",
        })
    st.dataframe(pd.DataFrame(occ_rows), use_container_width=True, hide_index=True)


# =============================================================================
# TAB 3: BREAK-EVEN
# =============================================================================
with tabs[3]:
    st.header("Break-Even Analysis")

    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly Fixed Costs (Nut)", fmt_dollar(model.MONTHLY_NUT))
    c2.metric("Annual Nut", fmt_dollar(model.ANNUAL_NUT))
    c3.metric("Total Project Cost (Loan)", fmt_dollar(model.TOTAL_PROJECT_COST))

    be = model.run_breakeven_analysis(verbose=False)
    no_bar = be["no_bar_annual"]

    st.subheader("Zero-Bar Test")
    st.caption("Can food truck rent + revenue share alone (4 trucks, no bar, "
               "no COTA) cover the monthly nut?")
    z1, z2, z3 = st.columns(3)
    z1.metric("Annual NOI (no bar)", fmt_dollar(no_bar["total_noi"]))
    z2.metric("Nut Coverage (no bar)", f"{no_bar['avg_monthly_nut_coverage']:.2f}x")
    verdict = "✅ Truck rent alone covers the nut" if no_bar["avg_monthly_nut_coverage"] >= 1.0 \
        else "❌ Truck rent alone does NOT cover the nut"
    z3.metric("Verdict", verdict.split(" ", 1)[0], delta=verdict.split(" ", 1)[1],
              delta_color="off")

    st.subheader("Minimum Bar Traffic by Nut-Coverage Target")
    st.caption(
        "Weak truck base (4 trucks @ $600 + 5%), no COTA, Year 1 ramp, and "
        f"the Worst Case check (\\${model.SCENARIOS['Worst Case']['avg_check']:.2f}). "
        "Scheduled wages still run. If a target is past the 4.0× traffic "
        "ceiling, the row says unreachable — it does not print that ceiling "
        "as a customer count."
    )
    be_rows = []
    for row in be["bar_traffic_targets"]:
        if row["reachable"]:
            customers = f"~{row['weekday_customers']} / ~{row['weekend_customers']}"
        else:
            customers = (
                f"Unreachable at {row['ceiling_multiple']:.1f}× traffic "
                f"(coverage there is {row['coverage_at_ceiling']:.2f}×)"
            )
        be_rows.append({
            "Nut Coverage Target": f"{row['label']} ({row['target']:.2f}x)",
            "Min Weekday/Weekend Customers": customers,
        })
    st.dataframe(pd.DataFrame(be_rows), use_container_width=True, hide_index=True)

    st.info(f"Market: {model.LOCAL_HOUSEHOLDS:,} local households, "
            f"{model.ANNUAL_COTA_VISITORS:,} annual COTA visitors. "
            f"Dollar General next door anchors daily foot traffic.")


# =============================================================================
# TAB 4: MONTE CARLO
# =============================================================================
with tabs[4]:
    st.header(f"Monte Carlo Simulation ({mc_sims:,} scenarios)")
    st.caption(
        f"Reproducible for seed {mc_seed} "
        f"(module default {model.MONTE_CARLO_DEFAULT_SEED}). "
        "Draws are independent — correlations are not modeled, so the joint "
        "downside tail is fatter than this chart. An undisclosed run is not "
        "a reproducible result."
    )
    with st.expander("Disclosed draws (distribution, spread, bounds)"):
        spec_rows = []
        for row in model.MONTE_CARLO_SPEC:
            if row["distribution"] == "gaussian":
                spread = str(row.get("sigma", ""))
            elif "values" in row:
                spread = ", ".join(str(v) for v in row["values"])
            else:
                spread = "held fixed at the sidebar value"
            spec_rows.append({
                "Parameter": row["name"],
                "Distribution": row["distribution"],
                "Spread / values": spread,
                "Low": "" if "low" not in row else str(row["low"]),
                "High": "" if "high" not in row else str(row["high"]),
            })
        st.dataframe(pd.DataFrame(spec_rows), use_container_width=True, hide_index=True)

    mc_results = get_monte_carlo(mc_sims, mc_seed, weekday_customers, weekend_customers,
                                 avg_check, truck_rent, truck_share, truck_occupancy,
                                 seasonal_pct, truck_slots, truck_sales,
                                 daytime_bev_attach, daytime_bev_price,
                                 cota_impact_multiplier)

    revenues = sorted(r["revenue"] for r in mc_results)
    covs = sorted(r["nut_coverage"] for r in mc_results)
    cfs = sorted(r["cash_flow"] for r in mc_results)

    def percentile(data, pct):
        idx = int(len(data) * pct / 100)
        return data[min(idx, len(data) - 1)]

    st.subheader("Probability Analysis")
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("P(Nut Coverage >= 1.0x)",
              f"{sum(1 for c in covs if c >= 1.0) / len(covs) * 100:.1f}%")
    p2.metric("P(Nut Coverage >= 1.5x)",
              f"{sum(1 for c in covs if c >= 1.5) / len(covs) * 100:.1f}%")
    p3.metric("P(Nut Coverage >= 2.0x)",
              f"{sum(1 for c in covs if c >= 2.0) / len(covs) * 100:.1f}%")
    p4.metric("P(Nut Coverage >= 3.0x)",
              f"{sum(1 for c in covs if c >= 3.0) / len(covs) * 100:.1f}%")
    p5.metric("P(CF > $0)",
              f"{sum(1 for c in cfs if c > 0) / len(cfs) * 100:.1f}%")

    st.subheader("Distribution Summary")
    perc_data = {
        "Metric": ["Annual Revenue", "Nut Coverage", "Free Cash Flow"],
        "P5": [fmt_dollar(percentile(revenues, 5)),
               f"{percentile(covs, 5):.2f}x", fmt_dollar(percentile(cfs, 5))],
        "P25": [fmt_dollar(percentile(revenues, 25)),
                f"{percentile(covs, 25):.2f}x", fmt_dollar(percentile(cfs, 25))],
        "Median": [fmt_dollar(percentile(revenues, 50)),
                   f"{percentile(covs, 50):.2f}x", fmt_dollar(percentile(cfs, 50))],
        "P75": [fmt_dollar(percentile(revenues, 75)),
                f"{percentile(covs, 75):.2f}x", fmt_dollar(percentile(cfs, 75))],
        "P95": [fmt_dollar(percentile(revenues, 95)),
                f"{percentile(covs, 95):.2f}x", fmt_dollar(percentile(cfs, 95))],
    }
    st.dataframe(pd.DataFrame(perc_data), use_container_width=True, hide_index=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Nut Coverage Distribution")
        fig_cov = px.histogram(x=covs, nbins=60, labels={"x": "Avg Monthly Nut Coverage"},
                                color_discrete_sequence=["#4E79A7"])
        fig_cov.add_vline(x=1.0, line_dash="dash", line_color="red",
                          annotation_text="Break-even")
        fig_cov.update_layout(margin=dict(t=40, b=40), showlegend=False)
        st.plotly_chart(fig_cov, use_container_width=True)
    with col_r:
        st.subheader("Free Cash Flow Distribution")
        fig_cf = px.histogram(x=cfs, nbins=60, labels={"x": "Free Cash Flow ($)"},
                              color_discrete_sequence=["#59A14F"])
        fig_cf.add_vline(x=0, line_dash="dash", line_color="red",
                         annotation_text="Break-even")
        fig_cf.update_layout(margin=dict(t=40, b=40), showlegend=False,
                             xaxis_tickformat="$,.0f")
        st.plotly_chart(fig_cf, use_container_width=True)

    st.caption(
        "Randomized around whatever the sidebar sliders are set to: truck "
        "occupancy (vacancy/churn, ±8pts), truck sales (\\$10K-\\$35K/mo), bar "
        "customers/evening, avg check (\\$5-\\$20), COTA event mix (big 4 fixed; "
        "concerts/festivals/GT vary), seasonal strength (40%-150%), and the "
        "daytime-beverage attach rate (±8pts), which gets the widest relative "
        "band because it's the least-validated number in the model. Truck "
        "count, rent, and revenue share are held "
        "fixed across every simulation (built slots + intended contract terms); "
        "lease-up risk shows up through occupancy instead."
    )


# =============================================================================
# TAB 5: SCENARIOS
# =============================================================================
with tabs[5]:
    st.header("Scenario Comparison")

    scenario_results = get_scenario_results()
    rows = []
    for name in model.SCENARIOS:
        ann = scenario_results[name]
        params = model.SCENARIOS[name]
        rows.append({
            "Scenario": name,
            "Truck Slots": params["truck_slots"],
            "Bar Custs (Wkday/Wkend)": f"{params['weekday_customers']}/{params['weekend_customers']}",
            "Annual Revenue": ann["total_gross"],
            "Free Cash Flow": ann["total_net_cash"],
            "Nut Coverage": ann["avg_monthly_nut_coverage"],
            "Min Month Coverage": ann["min_monthly_nut_coverage"],
        })
    sc_df = pd.DataFrame(rows)

    fig_sc = go.Figure()
    fig_sc.add_trace(go.Bar(
        x=sc_df["Scenario"], y=sc_df["Annual Revenue"],
        name="Annual Revenue", marker_color="#4E79A7"
    ))
    fig_sc.add_trace(go.Bar(
        x=sc_df["Scenario"], y=sc_df["Free Cash Flow"],
        name="Free Cash Flow", marker_color="#59A14F"
    ))
    fig_sc.add_trace(go.Scatter(
        x=sc_df["Scenario"], y=sc_df["Nut Coverage"],
        name="Nut Coverage", yaxis="y2", mode="lines+markers",
        marker_color="#E15759", line=dict(width=3),
    ))
    fig_sc.add_hline(y=1.0, line_dash="dash", line_color="red",
                     annotation_text="Break-even", yref="y2")
    fig_sc.update_layout(
        barmode="group",
        yaxis=dict(title="Dollars ($)", tickformat="$,.0f"),
        yaxis2=dict(title="Nut Coverage", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    disp_sc = sc_df.copy()
    for col in ["Annual Revenue", "Free Cash Flow"]:
        disp_sc[col] = disp_sc[col].apply(fmt_dollar)
    disp_sc["Nut Coverage"] = disp_sc["Nut Coverage"].apply(lambda x: f"{x:.2f}x")
    disp_sc["Min Month Coverage"] = disp_sc["Min Month Coverage"].apply(lambda x: f"{x:.2f}x")
    st.dataframe(disp_sc, use_container_width=True, hide_index=True)

    st.subheader("Scenario Definitions")
    for name, params in model.SCENARIOS.items():
        st.markdown(f"**{name}:** {params['desc']}")


# =============================================================================
# TAB 6: MULTI-YEAR
# =============================================================================
with tabs[6]:
    st.header("Multi-Year Projection (Years 1-3)")

    all_years = get_multi_year(weekday_customers, weekend_customers, avg_check,
                               truck_slots, truck_rent, truck_share, truck_sales,
                               truck_occupancy, seasonal_pct,
                               daytime_bev_attach, daytime_bev_price,
                               cota_impact_multiplier)

    my_rows = []
    for yr, months_data, ann in all_years:
        cota_total = (ann["total_cota_parking"] + ann["total_cota_bar"]
                     + ann["total_cota_daytime_bev"])
        my_rows.append({
            "Year": f"Year {yr}",
            "Annual Revenue": ann["total_gross"],
            "Food Trucks": ann["total_trucks"],
            "Evening Bar": ann["total_bar"],
            "Daytime Beverages": ann["total_daytime_beverage"],
            "COTA": cota_total,
            "Cost Inflation": ann["cost_inflation_adj"],
            "Free Cash Flow": ann["total_net_cash"],
            "FCF Yield": ann["fcf_yield"],
        })
    my_df = pd.DataFrame(my_rows)

    fig_my = go.Figure()
    fig_my.add_trace(go.Bar(
        x=my_df["Year"], y=my_df["Annual Revenue"],
        name="Revenue", marker_color="#4E79A7"
    ))
    fig_my.add_trace(go.Bar(
        x=my_df["Year"], y=my_df["Free Cash Flow"],
        name="Free Cash Flow", marker_color="#59A14F"
    ))
    fig_my.add_trace(go.Scatter(
        x=my_df["Year"], y=my_df["FCF Yield"] * 100,
        name="FCF Yield (%)", yaxis="y2", mode="lines+markers",
        marker_color="#E15759", line=dict(width=3, dash="dot"),
        marker=dict(size=12)
    ))
    fig_my.update_layout(
        barmode="group",
        yaxis=dict(title="Dollars ($)", tickformat="$,.0f"),
        yaxis2=dict(title="FCF Yield (%)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_my, use_container_width=True)

    disp_my = my_df.copy()
    for col in ["Annual Revenue", "Food Trucks", "Evening Bar", "Daytime Beverages",
                "COTA", "Cost Inflation", "Free Cash Flow"]:
        disp_my[col] = disp_my[col].apply(fmt_dollar)
    disp_my["FCF Yield"] = disp_my["FCF Yield"].apply(lambda x: f"{x:.1%}")
    st.dataframe(disp_my, use_container_width=True, hide_index=True)

    # Cash reserve + payback tracker (compact)
    st.subheader("Cash Reserve + Payback Tracker")
    tracker = model.run_cash_reserve_tracker(all_years, verbose=False)
    tr_rows = [{
        "Period": f"Y{s['year']} {MONTH_NAMES[s['month'] - 1]}",
        "Monthly CF": s["cf"], "Cash Balance": s["balance"],
    } for s in tracker["series"]]
    tr_df = pd.DataFrame(tr_rows)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "Cash at open (after pre-open burn)",
        fmt_dollar(model.OPENING_CASH_RESERVE),
        help=(
            f"Reserve at close is ${model.RESERVE_AND_SAFETY_CASH:,.0f} "
            f"(the floor). {model.PRE_OPEN_MONTHS} pre-open months of "
            f"contractual principal-and-interest plus accounting "
            f"(${model.PRE_OPEN_BURN:,.0f}) come out of it before revenue starts. "
            "Vacant-land tax and insurance are already in the land-carry use "
            "and are not charged again. Opening is "
            f"{model.OPENING_MONTH}/{model.OPENING_YEAR}."
        ),
    )
    k2.metric("Lowest Balance", fmt_dollar(tracker["min_balance"]))
    k3.metric("Months Negative CF", str(tracker["months_negative"]))
    payback = tracker["payback_month"]
    k4.metric("Startup Cost Recouped", f"Y{payback[0]} {MONTH_NAMES[payback[1]-1]}"
              if payback else "Not within window")

    fig_cr = go.Figure()
    fig_cr.add_trace(go.Scatter(
        x=tr_df["Period"], y=tr_df["Cash Balance"],
        name="Cash Balance", fill="tozeroy",
        line=dict(color="#4E79A7", width=2),
        fillcolor="rgba(78, 121, 167, 0.2)"
    ))
    fig_cr.add_hline(y=0, line_color="gray")
    fig_cr.update_layout(
        yaxis=dict(title="Dollars ($)", tickformat="$,.0f"),
        margin=dict(t=40, b=40), xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig_cr, use_container_width=True)

    # Ways to close the pre-opening cash gap (read-only comparison)
    st.subheader("Ways to Close the Cash Gap")
    ro = model.run_reserve_options(all_years=all_years)
    st.caption(
        f"Loan payments start at closing, {model.PRE_OPEN_MONTHS} months before the park "
        "opens, so most of the reserve is spent before the first sale. Each option below is "
        "measured against one goal: the lowest cash balance should still cover "
        f"{ro['target_months_of_payment']} months of loan payments "
        f"(\\${ro['min_balance_target']:,.0f}). This is a comparison only — the rest of the "
        "dashboard still uses the current structure.")
    ro_df = pd.DataFrame([{
        "Option": o["label"],
        "Loan": fmt_dollar(o["loan_amount"]),
        "Owner Cash Added": fmt_dollar(o["sponsor_cash"]),
        "Monthly Payment": fmt_dollar(o["monthly_payment"]),
        "Spent Before Opening": fmt_dollar(o["pre_open_burn"]),
        "Cash at Opening": fmt_dollar(o["opening_cash"]),
        "Lowest Balance": fmt_dollar(o["min_balance"]),
        "Short of Goal": fmt_dollar(o["gap_to_target"]) if o["gap_to_target"] > 0.5 else "—",
    } for o in ro["options"]])
    st.dataframe(ro_df, use_container_width=True, hide_index=True)
    st.caption(
        "Borrowing a bigger reserve costs more than adding the same cushion as owner cash, "
        "because the extra loan raises the monthly payment. Interest-only before opening "
        "depends on the loan type: on the full loan it saves little; on a construction "
        "loan that charges interest only on money drawn so far, it saves most of the "
        "pre-opening cost. Both interest-only rows assume normal payments begin at opening.")

    # Loan amortization schedule
    st.subheader("Loan Amortization Schedule")
    st.caption(f"The \\${model.LOAN_AMOUNT:,.0f} loan (@ {model.LOAN_INTEREST_RATE:.1%}, "
               f"{model.LOAN_TERM_YEARS}-year amortization) already has a fixed, "
               "contractual payoff schedule — this shows how much sooner it "
               "retires, and how much interest is saved, if free cash flow "
               "beyond the required payment is swept to extra principal.")
    loan_sched = model.run_loan_amortization_schedule(all_years, verbose=False)
    loan_rows = [{
        "Period": f"Y{s['year']} {MONTH_NAMES[s['month'] - 1]}",
        "Balance": s["balance"], "Interest": s["interest"],
    } for s in loan_sched["series"]]
    loan_df = pd.DataFrame(loan_rows)

    l1, l2, l3 = st.columns(3)
    payoff = loan_sched["payoff_month"]
    l1.metric("Loan Payoff Month (with sweep)", f"Y{payoff[0]} {MONTH_NAMES[payoff[1]-1]}"
              if payoff else "Not within window")
    l2.metric("Interest Paid (with sweep)", fmt_dollar(loan_sched["total_interest_paid"]))
    l3.metric("vs. Required-Schedule Interest",
              fmt_dollar(loan_sched["required_schedule_interest"]))

    fig_loan = go.Figure()
    fig_loan.add_trace(go.Scatter(
        x=loan_df["Period"], y=loan_df["Balance"],
        name="Loan Balance", fill="tozeroy",
        line=dict(color="#E15759", width=2),
        fillcolor="rgba(225, 87, 89, 0.2)"
    ))
    fig_loan.update_layout(
        yaxis=dict(title="Loan Balance ($)", tickformat="$,.0f"),
        margin=dict(t=40, b=40), xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig_loan, use_container_width=True)


# =============================================================================
# TAB 7: WATERFALL
# =============================================================================
with tabs[7]:
    st.header(f"Cash Flow Waterfall — {view_label}")

    # Read the engine's summed cost fields directly rather than re-deriving
    # `rate x revenue` here — recomputing locally is how this tab silently
    # drifted out of sync with NOI twice before.
    gross = annual["total_gross"]
    cogs = annual["total_cogs"]
    grt = annual["total_grt"]
    mb_sales_tax = annual["total_mb_sales_tax"]
    daytime_bev_cogs = annual["total_daytime_beverage_cogs"]
    daytime_bev_tax = annual["total_daytime_beverage_tax"]
    cc = annual["total_cc_processing"]
    shrinkage = annual["total_shrinkage"]
    utility_cost = annual["total_utility_cost"]  # pass-through at cost
    parking_cost = annual["total_cota_parking_upkeep"]
    parking_tax = annual["total_cota_parking_sales_tax"]
    cota_cost = annual["total_cota_cost"]
    labor_wages = annual["total_labor_wages"]
    payroll_burden = annual["total_payroll_burden"]
    management_fee = annual["total_management_fee"]
    replacement_reserve = annual["total_replacement_reserve"]
    opex = model.ANNUAL_OPEX_NUT
    loan_payment = model.ANNUAL_DEBT_SERVICE
    pre_tax_cf = (gross - cogs - grt - mb_sales_tax
                  - daytime_bev_cogs - daytime_bev_tax - cc
                  - shrinkage - utility_cost - parking_cost - parking_tax
                  - cota_cost - labor_wages - payroll_burden
                  - management_fee - replacement_reserve
                  - opex - loan_payment)
    # Taxable profit is NOI minus the loan's INTEREST portion only - loan
    # principal (part of loan_payment above) isn't deductible, so this must
    # mirror summarize_annual's tax-base fix, not just re-tax pre_tax_cf
    # (which is already net of the full, non-deductible principal too).
    taxable_profit = max(0.0, annual["total_noi"] - annual["loan_interest_paid"])
    income_tax = taxable_profit * model.EFFECTIVE_INCOME_TAX_RATE
    free_cf = pre_tax_cf - income_tax

    # The hand-built waterfall above must reconcile to the engine's own
    # authoritative after-tax cash flow - if a cost line is ever added to
    # calc_monthly_total but not mirrored here, this catches it visually
    # instead of the chart silently drifting out of sync (see CLAUDE.md).
    assert abs(free_cf - annual["after_tax_noi"]) < 1.0, (
        "Waterfall's hand-rolled cash flow drifted from annual['after_tax_noi'] "
        "- a cost line was added to calc_monthly_total without being mirrored here."
    )

    labels = ["Gross Revenue", f"COGS ({model.COGS_RATE:.0%})",
              f"TX Mixed Bev GRT ({model.GRT_RATE:.1%})",
              f"TX Mixed Bev Sales Tax ({model.MB_SALES_TAX_RATE:.2%})",
              f"Daytime Bev COGS ({model.DAYTIME_BEVERAGE_COGS_RATE:.0%})",
              f"Daytime Bev Sales Tax ({model.DAYTIME_BEVERAGE_SALES_TAX_RATE:.2%})",
              "CC Processing", "Shrinkage", "Utility Pass-Thru", "Parking Upkeep",
              f"Parking Sales Tax ({model.PARKING_SALES_TAX_RATE:.2%})",
              "COTA Costs", "Scheduled Labor", "Employer Payroll Burden",
              f"Management Fee ({model.MANAGEMENT_FEE_RATE:.0%})",
              f"Replacement Reserve ({model.REPLACEMENT_RESERVE_RATE:.0%})",
              "Operating Fixed Costs", "Loan Payment (P&I)",
              f"Income Tax ({model.EFFECTIVE_INCOME_TAX_RATE:.0%})",
              "After-Tax Cash Flow"]
    values = [gross, -cogs, -grt, -mb_sales_tax,
              -daytime_bev_cogs, -daytime_bev_tax, -cc, -shrinkage,
              -utility_cost, -parking_cost, -parking_tax,
              -cota_cost, -labor_wages, -payroll_burden,
              -management_fee, -replacement_reserve,
              -opex, -loan_payment, -income_tax, 0]
    measures = ["absolute"] + ["relative"] * (len(values) - 2) + ["total"]

    fig_wf = go.Figure(go.Waterfall(
        x=labels, y=values, measure=measures,
        connector={"line": {"color": "rgba(0,0,0,0.3)", "width": 1}},
        increasing={"marker": {"color": "#4E79A7"}},
        decreasing={"marker": {"color": "#E15759"}},
        totals={"marker": {"color": "#59A14F" if free_cf >= 0 else "#E15759"}},
        textposition="outside",
        text=[fmt_dollar(abs(v)) if v != 0 else fmt_dollar(free_cf) for v in values],
    ))
    fig_wf.update_layout(
        yaxis=dict(title="Dollars ($)", tickformat="$,.0f"),
        margin=dict(t=40, b=40), showlegend=False,
    )
    st.plotly_chart(fig_wf, use_container_width=True)
    st.caption(
        "Mixed-beverage sales tax is backed out of the tax-inclusive alcohol "
        "receipt before the 6.7% GRT is applied, so GRT is not 6.7% of the "
        "cash the customer handed over. Event-parking sales tax is extracted "
        "from the tax-inclusive parking price the same way. Dollar bars are "
        "rounded for display; the loan payment underneath is the unrounded "
        "annual debt service (monthly payment × 12)."
    )

    st.subheader("Margin Analysis")
    c1, c2, c3 = st.columns(3)
    core_rev = gross - annual["total_utility_billed"]
    c1.metric("After-Tax CF Margin (core revenue)",
              f"{free_cf / core_rev * 100:.1f}%" if core_rev else "n/a")
    c2.metric("After-Tax Cash Flow", fmt_dollar(free_cf))
    c3.metric("After-Tax FCF Yield",
              f"{free_cf / model.TOTAL_PROJECT_COST * 100:.1f}%")


# =============================================================================
# TAB 8: OWNER SUMMARY
# =============================================================================
with tabs[8]:
    st.header("Owner Summary")
    st.subheader("Food Truck Park + Bar & Beverage Stand | Del Valle, TX")

    st.markdown("---")
    st.subheader(f"Total Project Cost — Financed via a ${model.LOAN_ASK:,.0f} Bank Term Loan")
    lt1, lt2, lt3, lt4 = st.columns(4)
    lt1.metric("Total Project Cost", fmt_dollar(model.TOTAL_PROJECT_COST))
    lt2.metric("Loan Rate / Term", f"{model.LOAN_INTEREST_RATE:.1%} / {model.LOAN_TERM_YEARS}yr")
    lt3.metric("Already Spent", fmt_dollar(model.ALREADY_SPENT))
    lt4.metric("Remaining to Spend", fmt_dollar(model.NEW_CASH_NEEDED))

    st.markdown("---")
    st.subheader(f"Use of Funds — ${model.LOAN_ASK:,.0f} sized ask")
    status_labels = {
        "done": "✅ Done",
        "in_progress": "🔧 In Progress",
        "not_started": "⬜ Not Started",
        "gated": "🚧 Gated",
        "tbd": "❓ TBD",
    }
    use_df = pd.DataFrame(model.USE_OF_FUNDS, columns=["Item", "Amount", "Status"])
    use_df["Status"] = use_df["Status"].map(status_labels)
    use_df["Amount"] = use_df["Amount"].apply(fmt_dollar)
    st.dataframe(use_df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total: {fmt_dollar(model.TOTAL_PROJECT_COST)}**")
    st.caption(
        "The ask is sized so Reserve & Safety Cash equals the "
        f"${model.RESERVE_FLOOR:,.0f} floor. Contingency is "
        f"{model.CONTINGENCY_RATE_BASE:.0%} of hard cost including GC "
        f"(${model.CONTINGENCY_BUDGET:,.0f}) and is not cut to hit a round number. "
        f"Septic is ${model.SEPTIC:,.0f} and gated. Health permit is "
        f"${model.HEALTH_LICENSE:,.0f}. The $5,300 TABC permit is already paid "
        "and sits inside the $120,000 LOC payoff. The $3,000 ACE retainer is "
        "already paid and is not a forward use. Paving default is the "
        f"${model.PAVING_BUDGET:,.0f} asphalt line "
        f"(gravel alternate ${model.GRAVEL_ALT_BUDGET:,.0f}). "
        f"Land carry of ${model.LAND_CARRY:,.0f} is six months of vacant-land "
        "tax and insurance, prepaid."
    )

    with st.expander("Historical Phase 0.5 buildout (already funded, not part of this loan)"):
        phase_df = pd.DataFrame(model.PHASE_0_5_CAPITAL_IMPROVEMENTS,
                                 columns=["Item", "Amount", "Status"])
        phase_df["Status"] = phase_df["Status"].map(status_labels)
        phase_df["Amount"] = phase_df["Amount"].apply(fmt_dollar)
        st.dataframe(phase_df, use_container_width=True, hide_index=True)
        st.markdown(f"**Total: {fmt_dollar(model.PHASE_0_5_TOTAL)}**")
        st.caption("Real, itemized construction spend from the owner's "
                   "actual Phase 0.5 cost tracker (Notion), at actual "
                   "vendor-quoted prices — not estimated buckets. This was "
                   "already financed via a smaller, separate personal line "
                   "of credit, which this loan pays off in "
                   "full — so these items aren't counted again in the loan's "
                   "Use of Funds (that would double-count the same dollars), "
                   "but they're real capital investment in the property and "
                   "still factor into depreciation and the CRE Investment "
                   "Summary tab's capitalized basis. Planning-only line "
                   "items that were never actually implemented (generator, "
                   "grease removal, propane tank service) are excluded "
                   "rather than estimated.")

    st.markdown("---")
    st.subheader("Monthly Operating Costs (The Nut)")
    nut_rows = [{"Expense": k.replace("_", " ").title(), "Monthly": fmt_dollar(v)}
                for k, v in model.FIXED_COSTS.items()]
    st.dataframe(pd.DataFrame(nut_rows), use_container_width=True, hide_index=True)
    st.markdown(f"**Total Monthly Nut: \\${model.MONTHLY_NUT:,.0f}** | "
                f"**Annual: \\${model.ANNUAL_NUT:,.0f}**")
    st.caption(f"Includes \\${model.LOAN_MONTHLY_PAYMENT:,.0f}/mo fixed "
               f"principal + interest on the \\${model.LOAN_AMOUNT:,.0f} bank "
               f"loan (@ {model.LOAN_INTEREST_RATE:.1%}, {model.LOAN_TERM_YEARS}-year "
               "amortization) — see the Multi-Year tab for the year-by-year "
               "principal/interest split and the optional extra-prepayment "
               "scenario. This is FIXED costs only — see Variable Operating "
               "Costs below for COGS, taxes, and everything else that scales "
               "with revenue.")

    st.markdown("---")
    st.subheader("Variable Operating Costs (Scale with Revenue)")
    st.caption("Not part of \"The Nut\" above — these move with sales volume "
               "rather than being fixed monthly bills, so they're netted "
               "against revenue in NOI instead of sitting in FIXED_COSTS. "
               "Dollar figures below are Base Case Year 1.")
    _, conservative = model.run_scenario_projection(model.SCENARIOS["Conservative"])
    _, base = model.run_scenario_projection(model.SCENARIOS["Base Case"])
    var_cost_rows = [
        {"Expense": "COGS — Evening Bar (container bar)",
         "Rate": f"{model.COGS_RATE:.1%} of alcohol revenue",
         "Annual (Base Case)": base["total_cogs"]},
        {"Expense": "TX Mixed Beverage GRT",
         "Rate": (f"{model.GRT_RATE:.1%} of alcohol receipts after sales tax "
                  "is backed out (no tax-on-tax)"),
         "Annual (Base Case)": base["total_grt"]},
        {"Expense": "TX Mixed Beverage Sales Tax",
         "Rate": (f"{model.MB_SALES_TAX_RATE:.2%} / "
                  f"{1 + model.MB_SALES_TAX_RATE:.4f} of the tax-inclusive receipt"),
         "Annual (Base Case)": base["total_mb_sales_tax"]},
        {"Expense": "COGS — Daytime Beverages",
         "Rate": f"{model.DAYTIME_BEVERAGE_COGS_RATE:.0%} of daytime beverage revenue",
         "Annual (Base Case)": base["total_daytime_beverage_cogs"]},
        {"Expense": "TX Sales Tax — Daytime Beverages",
         "Rate": f"{model.DAYTIME_BEVERAGE_SALES_TAX_RATE:.2%} of daytime beverage revenue",
         "Annual (Base Case)": base["total_daytime_beverage_tax"]},
        {"Expense": "Credit Card Processing",
         "Rate": f"{model.CC_PROCESSING_RATE:.1%} × {model.CC_CARD_USAGE_RATE:.0%} card usage",
         "Annual (Base Case)": base["total_cc_processing"]},
        {"Expense": "Shrinkage",
         "Rate": f"{model.SHRINKAGE_RATE:.1%} of COGS value",
         "Annual (Base Case)": base["total_shrinkage"]},
        {"Expense": "Scheduled labor (daytime, evening, event extra, OT, manager)",
         "Rate": (f"${model.DAYTIME_ATTENDANT_WAGE:.0f}/hr daytime, "
                  f"${model.EVENING_BARTENDER_WAGE:.0f}/hr evening, "
                  f"${model.EVENT_EXTRA_WAGE:.0f}/hr event extra, "
                  f"{model.OVERTIME_ALLOWANCE_RATE:.0%} OT, "
                  f"${model.MANAGER_ANNUAL_SALARY:,.0f} manager. Lodging not expensed."),
         "Annual (Base Case)": base["total_labor_wages"]},
        {"Expense": "Employer Payroll Burden (FICA/FUTA/SUTA)",
         "Rate": f"{model.EMPLOYER_PAYROLL_BURDEN_RATE:.0%} on all cash wages",
         "Annual (Base Case)": base["total_payroll_burden"]},
        {"Expense": "COTA Parking Lot Upkeep",
         "Rate": f"{model.PARKING_UPKEEP_RATE:.0%} of event parking revenue",
         "Annual (Base Case)": base["total_cota_parking_upkeep"]},
        {"Expense": "TX Sales Tax — Event Parking",
         "Rate": (f"{model.PARKING_SALES_TAX_RATE:.2%} / "
                  f"{1 + model.PARKING_SALES_TAX_RATE:.4f} of the tax-inclusive price"),
         "Annual (Base Case)": base["total_cota_parking_sales_tax"]},
        {"Expense": "COTA Incremental Costs (event staffing/porta-potty)",
         "Rate": "flat per event tier",
         "Annual (Base Case)": base["total_cota_cost"]},
        {"Expense": "Utility Pass-Through Cost (at cost, net-zero)",
         "Rate": "billed at cost, no markup",
         "Annual (Base Case)": base["total_utility_cost"]},
        {"Expense": "Management Fee",
         "Rate": f"{model.MANAGEMENT_FEE_RATE:.0%} of EGI ex. utility pass-through",
         "Annual (Base Case)": base["total_management_fee"]},
        {"Expense": "Replacement Reserve",
         "Rate": f"{model.REPLACEMENT_RESERVE_RATE:.0%} of EGI ex. utility pass-through",
         "Annual (Base Case)": base["total_replacement_reserve"]},
    ]
    var_df = pd.DataFrame(var_cost_rows)
    total_variable = var_df["Annual (Base Case)"].sum()
    var_df["Annual (Base Case)"] = var_df["Annual (Base Case)"].apply(fmt_dollar)
    st.dataframe(var_df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total Variable Costs (Base Case, Year 1): {fmt_dollar(total_variable)}**")
    st.caption("Utility pass-through nets to $0 NOI impact (revenue and cost "
               "offset exactly — PURA §39.107) but is listed here for a "
               "complete expense picture. COTA incremental costs and "
               "event extra labor only applies in months with COTA events / "
               "beverage sales respectively — this total is Year 1 actuals, "
               "not a flat monthly rate like the Nut.")

    st.markdown("---")
    st.subheader("Projected Performance (Year 1)")
    perf_l, perf_r = st.columns(2)
    with perf_l:
        _c = model.SCENARIOS["Conservative"]
        st.markdown(f"**Conservative** ({_c['truck_slots']} trucks @ "
                    f"{_c['truck_occupancy']:.0%} occ, soft bar)")
        st.metric("Revenue", fmt_dollar(conservative["total_gross"]))
        st.metric("Free Cash Flow (pre-tax)", fmt_dollar(conservative["total_net_cash"]))
        st.metric("After-Tax Cash Flow", fmt_dollar(conservative["after_tax_noi"]))
        st.metric("FCF Yield (pre / after tax)",
                  f"{conservative['fcf_yield']:.0%} / {conservative['after_tax_fcf_yield']:.0%}")
    with perf_r:
        _b = model.SCENARIOS["Base Case"]
        st.markdown(f"**Base Case** ({_b['truck_slots']} trucks @ "
                    f"{_b['truck_occupancy']:.0%} occ, {_b['weekday_customers']} wkday / "
                    f"{_b['weekend_customers']} wkend bar)")
        st.metric("Revenue", fmt_dollar(base["total_gross"]))
        st.metric("Free Cash Flow (pre-tax)", fmt_dollar(base["total_net_cash"]))
        st.metric("After-Tax Cash Flow", fmt_dollar(base["after_tax_noi"]))
        st.metric("FCF Yield (pre / after tax)",
                  f"{base['fcf_yield']:.0%} / {base['after_tax_fcf_yield']:.0%}")
    st.caption(f"After-tax figures apply a {model.EFFECTIVE_INCOME_TAX_RATE:.0%} blended "
               "effective federal + self-employment rate estimate on pass-through "
               "profit (TX has no state income tax). Confirm with a CPA.")
    st.caption(
        f"Free Cash Flow above is net of a management fee "
        f"({model.MANAGEMENT_FEE_RATE:.0%} of EGI) and a replacement reserve "
        f"({model.REPLACEMENT_RESERVE_RATE:.0%} of EGI) — real, market-rate costs "
        f"included whether or not the owner charges themselves one. Conservative: "
        f"\\${conservative['total_management_fee']:,.0f} mgmt fee + "
        f"\\${conservative['total_replacement_reserve']:,.0f} reserve. Base Case: "
        f"\\${base['total_management_fee']:,.0f} mgmt fee + "
        f"\\${base['total_replacement_reserve']:,.0f} reserve."
    )

    st.markdown("---")
    st.subheader("Risk Mitigants")
    mitigants = [
        f"Free cash flow beyond the required payment can be swept to extra "
        f"principal, retiring the \\${model.LOAN_AMOUNT:,.0f} loan faster and "
        f"saving interest vs. the contractual {model.LOAN_TERM_YEARS}-year "
        "schedule (see Loan Amortization Schedule)",
        f"Land owned outright — no rent or mortgage in the monthly nut, and "
        f"\\${model.ALREADY_SPENT:,.0f} of the \\${model.TOTAL_PROJECT_COST:,.0f} "
        "loan is already committed (payoff of the owner's existing LOC), on "
        f"top of \\${model.PHASE_0_5_TOTAL:,.0f} of real buildout already "
        "financed and largely complete outside this loan",
        "Full container bar (draft, canned, shots, cocktails) — a higher "
        "average check and better blended margin than a prepackaged-only "
        "stand, on a $50,000 budgeted buildout",
        "Utilities sub-metered and billed at cost (PURA §39.107) — "
        "no utility margin risk",
        "COTA upside preserved: event parking + bar uplift on race weekends",
        "100% of liquor/beer revenue retained (no rev-share on bar sales)",
        "All-day beverages are staffed by a daytime attendant, separate from "
        "the evening bartender, plus one extra body on COTA event days. "
        "That crew is still light for an 11-hour day. Lodging is provided "
        "and not expensed. Wage rates are estimates, not quotes",
    ]
    for m in mitigants:
        st.markdown(f"- {m}")


# =============================================================================
# TAB 9: TAX STRATEGIES
# =============================================================================
with tabs[9]:
    st.header("Tax Savings Strategies")
    st.caption("Illustrative only — depreciation elections and entity choice "
               "depend on the owner's full tax picture (other income, filing "
               "status, state). Confirm with a CPA before filing. This tab "
               "doesn't change the pre-tax profit used elsewhere in the "
               "model — it only estimates incremental tax savings.")
    st.info(
        "**This tab covers the FEDERAL layer only** — income tax plus "
        "self-employment/payroll tax, applied to profit AFTER the loan's "
        "INTEREST expense only (a deductible business cost — loan principal "
        "is not). Texas has no personal income tax, but the business pays "
        "plenty of other Texas taxes (mixed beverage GRT and sales tax, "
        "sales tax on parking and daytime beverages, property tax, employer "
        "payroll). Those, plus the loan interest itself, are ordinary "
        "operating expenses and are **already deducted inside the profit "
        "figure below** — see the Owner Summary tab's Variable Operating "
        "Costs table for that side."
    )

    st.markdown("---")
    st.subheader("Taxable Profit Basis")
    st.caption("This is NOI after the loan's INTEREST expense only (a "
               "deductible cost) — NOT total_net_cash, which nets out the "
               "loan's full principal + interest payment; principal isn't "
               "tax-deductible. See the CRE Investment Summary tab for the "
               "property-level NOI figure.")
    noi_source = st.radio(
        "Run the analysis on:",
        ["Current Dashboard Inputs", "Base Case", "Conservative", "Custom"],
        horizontal=True,
    )
    if noi_source == "Current Dashboard Inputs":
        tax_noi = annual["total_noi"] - annual["loan_interest_paid"]
        st.metric("Year 1 Taxable Profit (sidebar inputs)", fmt_dollar(tax_noi))
    elif noi_source == "Custom":
        tax_noi = st.slider("Annual Taxable Profit ($)", 0, 400_000,
                            int(annual["total_noi"] - annual["loan_interest_paid"]),
                            step=5_000, format="$%d")
    else:
        _, scen_ann = model.run_scenario_projection(model.SCENARIOS[noi_source])
        tax_noi = scen_ann["total_noi"] - scen_ann["loan_interest_paid"]
        st.metric(f"{noi_source} Year 1 Taxable Profit", fmt_dollar(tax_noi))

    st.markdown("---")
    st.subheader("1. Depreciation & Startup Cost Amortization")
    st.markdown(
        f"The \\${model.TOTAL_DEPRECIABLE_BASIS:,.0f} capital buildout "
        "(excludes inventory and contingency — see Owner Summary for the "
        "full Use of Funds) can be written off against taxable income. It's "
        "a **non-cash deduction**: it lowers the tax bill without reducing "
        "actual cash NOI. Separately, pre-opening costs that aren't "
        f"depreciable property — permits, licensing, cleaning "
        f"(\\${model.STARTUP_COST_BASIS:,.0f}) — are deductible under **IRC "
        "§195**: up to \\$5,000 immediately in the opening year, with the "
        "remainder amortized over 15 years."
    )
    dep_l, dep_r = st.columns(2)
    with dep_l:
        st.metric("5-Year Basis (equipment/fixtures)", fmt_dollar(model.DEPRECIABLE_BASIS_5YR))
        st.metric("Straight-Line Annual Expense", fmt_dollar(model.ANNUAL_STRAIGHT_LINE_DEPRECIATION))
        st.metric("§195 Startup Basis", fmt_dollar(model.STARTUP_COST_BASIS))
    with dep_r:
        st.metric("15-Year Basis (land improvements)", fmt_dollar(model.DEPRECIABLE_BASIS_15YR))
        st.metric("Accelerated (100% Bonus, Year 1)", fmt_dollar(model.YEAR1_ACCELERATED_DEPRECIATION))
        st.metric("§195 Year 1 Deduction", fmt_dollar(model.YEAR1_STARTUP_DEDUCTION))
    accelerated = st.checkbox(
        "Elect 100% bonus depreciation / Section 179 (write off the full basis in "
        "Year 1, vs. spreading it straight-line over 5/15 years)",
        value=True,
    )
    st.caption(
        "100% bonus depreciation was **permanently restored** by the One Big "
        "Beautiful Bill Act for property acquired after Jan 19, 2025 (IRC "
        "§168(k); IRS Notice 2026-11), so the full-basis Year 1 write-off is "
        "available and no longer phasing down. Mechanism differs by asset "
        "class: 5-year equipment qualifies for both §179 and bonus, while "
        "15-year land improvements (gravel, lighting, fencing) are generally "
        "**not** §179-eligible but are bonus-eligible — 100% bonus is what "
        "actually expenses that portion."
    )

    st.markdown("---")
    st.subheader("2. Owner Salary vs. Distributions (S-Corp Election)")
    st.markdown(
        "A sole proprietorship / single-member LLC (today's default "
        "structure elsewhere in this model) owes **self-employment tax "
        "(15.3%)** on 100% of net profit. Electing **S-corp** status lets "
        "the owner split profit into a \"reasonable salary\" (subject to "
        "payroll tax, the SE-tax equivalent) and distributions (income tax "
        "only — no SE/payroll tax on that portion)."
    )
    owner_salary = st.slider(
        "Reasonable Owner Salary ($/yr)", 0, 100_000,
        model.REASONABLE_OWNER_SALARY, step=1_000, format="$%d",
    )
    st.caption(
        "Default reflects a part-time oversight role on top of the on-site "
        f"manager's \\${model.MANAGER_ANNUAL_SALARY:,.0f} cash salary. Lodging "
        "is provided and is not expensed; IRC §119 and FLSA §3(m) are not "
        "treated as established. Floor labor is scheduled wages, not a "
        "beverage-revenue share. A CPA reasonable-compensation study should "
        "confirm the owner-salary figure before an S-corp election."
    )

    st.markdown("---")
    st.subheader("Combined Financial Impact")
    no_strategy = model.run_tax_strategy_analysis(tax_noi, apply_depreciation=False, apply_scorp=False)
    dep_only = model.run_tax_strategy_analysis(tax_noi, accelerated_depreciation=accelerated, apply_scorp=False)
    scorp_only = model.run_tax_strategy_analysis(tax_noi, apply_depreciation=False,
                                                 apply_scorp=True, owner_salary=owner_salary)
    combined = model.run_tax_strategy_analysis(tax_noi, accelerated_depreciation=accelerated,
                                               apply_scorp=True, owner_salary=owner_salary)

    compare_df = pd.DataFrame([
        {"Strategy": "No Strategy (today)", "Total Tax": no_strategy["strategy_total_tax"],
         "After-Tax Cash Flow": no_strategy["strategy_after_tax"]},
        {"Strategy": "+ Depreciation Only", "Total Tax": dep_only["strategy_total_tax"],
         "After-Tax Cash Flow": dep_only["strategy_after_tax"]},
        {"Strategy": "+ S-Corp Election Only", "Total Tax": scorp_only["strategy_total_tax"],
         "After-Tax Cash Flow": scorp_only["strategy_after_tax"]},
        {"Strategy": "+ Both Combined", "Total Tax": combined["strategy_total_tax"],
         "After-Tax Cash Flow": combined["strategy_after_tax"]},
    ])

    fig_tax = go.Figure()
    fig_tax.add_trace(go.Bar(x=compare_df["Strategy"], y=compare_df["Total Tax"],
                             name="Total Tax", marker_color="#E15759"))
    fig_tax.add_trace(go.Bar(x=compare_df["Strategy"], y=compare_df["After-Tax Cash Flow"],
                             name="After-Tax Cash Flow", marker_color="#59A14F"))
    fig_tax.update_layout(
        barmode="group",
        yaxis=dict(title="Dollars ($)", tickformat="$,.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig_tax, use_container_width=True)

    disp_df = compare_df.copy()
    disp_df["Total Tax"] = disp_df["Total Tax"].apply(fmt_dollar)
    disp_df["After-Tax Cash Flow"] = disp_df["After-Tax Cash Flow"].apply(fmt_dollar)
    st.dataframe(disp_df, use_container_width=True, hide_index=True)

    combined_savings = no_strategy["strategy_total_tax"] - combined["strategy_total_tax"]
    cf_uplift = combined["strategy_after_tax"] - no_strategy["strategy_after_tax"]
    sm1, sm2, sm3, sm4 = st.columns(4)
    sm1.metric(
        "Combined Tax Savings", fmt_dollar(combined_savings),
        f"{combined_savings / no_strategy['strategy_total_tax']:.0%} lower tax bill"
        if no_strategy["strategy_total_tax"] else None,
    )
    sm2.metric("Owner Salary", fmt_dollar(combined["owner_salary"]))
    sm3.metric("Distributions", fmt_dollar(combined["distribution"]))
    sm4.metric("After-Tax Cash Flow Uplift", fmt_dollar(cf_uplift))

    st.caption(
        f"Federal income tax is estimated at {model.FEDERAL_INCOME_TAX_RATE_ONLY:.0%} of taxable "
        "profit (NOI after depreciation) in every column above — only the "
        "self-employment/payroll-tax base changes by strategy. For "
        f"reference, the flat blended-rate estimate used elsewhere in the "
        f"model ({model.EFFECTIVE_INCOME_TAX_RATE:.0%}) implies "
        f"{fmt_dollar(no_strategy['blended_baseline_tax'])} of tax on this NOI — close to the "
        "\"No Strategy\" column here, which breaks that same estimate into "
        "its income-tax and self-employment-tax components."
    )


# =============================================================================
# TAB 10: MODEL OVERVIEW
# =============================================================================
with tabs[10]:
    st.header("📊 How The Model Works")
    st.caption("Food truck park + a bar & beverage stand on the Del Valle "
               "land, financed via a $500,000 bank term loan")

    st.markdown(
        f"""
        Four revenue streams stack here: contracted monthly rent from food
        truck tenants forms a stable base, the evening container bar adds
        draft and canned beer, liquor shots, and cocktails, the
        all-day stand adds soda/juice/water/coffee, and COTA event weekends
        layer parking and bar upside on top. The
        \\${model.TOTAL_PROJECT_COST:,.0f} total project cost (the owner's
        real Phase 0.5 buildout tracker plus septic, paving, and the
        remaining construction phase) is financed through a **bank term
        loan** at {model.LOAN_INTEREST_RATE:.1%}, {model.LOAN_TERM_YEARS}-year
        amortization — fixed monthly principal + interest, not the smaller
        interest-only personal line of credit that financed the original
        Phase 0.5 buildout alone. The model tracks the **monthly operating
        nut** (which includes the fixed loan payment) and **FCF yield on
        total cost**, plus a dedicated loan amortization schedule.
        """
    )
    st.warning(
        "**The park is not open yet.** It's still under construction with no "
        "operating history and no signed vendor contracts (six operators have "
        "expressed interest, which isn't the same thing). Every number here is "
        "an estimate, and where a number is uncertain the model deliberately "
        "errs toward **higher expenses and lower revenue** — understating the "
        "business is acceptable, overstating it isn't. Use the **Projection "
        "View** toggle in the sidebar to switch between the ramped Year 1 view "
        "and the steady-state run-rate."
    )

    with st.expander("1. Revenue Streams", expanded=True):
        # Steady-state (no-ramp) run rate, computed live so this table can't
        # drift away from the engine the way hardcoded figures did before.
        _, _ss = get_annual(weekday_customers, weekend_customers, avg_check,
                            truck_slots, truck_rent, truck_share, truck_sales,
                            truck_occupancy, seasonal_pct,
                            daytime_bev_attach, daytime_bev_price,
                            cota_impact_multiplier, yr=2)
        _mo = lambda k: fmt_dollar(_ss[k] / 12) + "/mo"
        _alcohol_margin = 1 - model.VARIABLE_COST_RATE
        _parking_margin = 1 - model.PARKING_UPKEEP_RATE - model.PARKING_SALES_TAX_RATE
        streams = pd.DataFrame([
            ("1. Food Trucks",
             f"{model.TRUCK_SLOTS} hubs being built (no more budgeted), leasing "
             f"up from ~half-full at open to fully leased by month "
             f"{max(model.TRUCK_Y1_FILL_RAMP) + 1} at "
             f"{model.TRUCK_OCCUPANCY:.0%} steady-state occupancy: "
             f"${model.TRUCK_PAD_RENT} pad rent + {model.TRUCK_REV_SHARE_RATE:.0%} "
             f"rev share on ~${model.TRUCK_AVG_MONTHLY_SALES/1000:.0f}K/mo truck sales",
             _mo("total_trucks"), "100% (trucks carry their own OpEx)"),
            ("2. Evening Bar",
             f"6pm-close only, full container bar: ${model.DRAFT_BEER_PRICE:.0f} draft "
             f"/ ${model.BEER_PRICE:.0f} canned beer / ${model.SHOT_PRICE:.0f} shots "
             f"/ ${model.COCKTAIL_PRICE:.0f} cocktails "
             f"({model.DRAFT_BEER_MIX_PCT:.0%}/{model.BEER_MIX_PCT:.0%}/"
             f"{model.SHOT_MIX_PCT:.0%}/{model.COCKTAIL_MIX_PCT:.0%} item mix): "
             f"{model.BAR_WEEKDAY_CUSTOMERS} weekday / {model.BAR_WEEKEND_CUSTOMERS} "
             f"weekend customers/evening averaging {model.DRINKS_PER_VISIT} drinks "
             f"(~${model.BAR_AVG_CHECK:.2f} check)",
             _mo("total_bar"),
             f"~{_alcohol_margin:.0%} after COGS + both mixed beverage taxes"),
            ("3. Daytime Beverages",
             f"All-day (~11am-close) soda/juice/water/coffee, sized off implied "
             f"food-truck customer traffic ({model.DAYTIME_BEVERAGE_ATTACH_RATE:.0%} "
             f"attach rate x ${model.DAYTIME_BEVERAGE_AVG_PRICE:.2f} avg price) - "
             "staffed by a daytime attendant on scheduled wages (the evening "
             "bartender does not cover this window unpaid). The crew is still "
             "light. Requires vendor leases restricting trucks to food-only "
             "(specialty drinks OK); no leases are executed, so percentage "
             "rent is non-contractual",
             _mo("total_daytime_beverage"),
             f"~{1 - model.DAYTIME_BEVERAGE_VARIABLE_COST_RATE:.0%} after COGS + sales tax"),
            ("4. COTA Events",
             f"{model.EVENT_PARKING_SPACES}-space event parking (dedicated 3-acre "
             "lot), day-by-day occupancy building to the marquee day (F1: 45% Fri "
             "/ 75% Sat / 100% Sun) + uplift on the bar and daytime beverages, "
             f"with the bar at premium event pricing "
             f"(${model.COTA_EVENT_DRAFT_BEER_PRICE:.0f} draft / "
             f"${model.COTA_EVENT_BEER_PRICE:.0f} canned / "
             f"${model.COTA_EVENT_SHOT_PRICE:.0f} shot / "
             f"${model.COTA_EVENT_COCKTAIL_PRICE:.0f} cocktail)",
             "Event months only",
             f"Parking ~{_parking_margin:.0%} after upkeep + sales tax, "
             "less per-tier event staffing"),
            ("5. Seasonal Events",
             "Super Bowl / March Madness / NYE watch parties on the big TVs. "
             "Separate from the everyday sports-calendar effect (see Ramps & "
             "Levers)",
             fmt_dollar(_ss["total_seasonal"]) + "/yr",
             f"~{_alcohol_margin:.0%} (same as the bar)"),
            ("6. Utility Pass-Through",
             "Sub-metered truck power/water/waste billed at cost (PURA §39.107)",
             _mo("total_utility_billed"), "0% by law (at-cost resale)"),
        ], columns=["Stream", "Description", "Steady-State Monthly", "Margin"])
        st.dataframe(streams, use_container_width=True, hide_index=True)
        st.caption(
            "Monthly figures are the **steady-state run rate** (Year 2+, no "
            "ramps) at the current sidebar settings, so they won't match the "
            "Year 1 view. Margins are after that stream's own variable costs "
            "but before the fixed monthly nut, credit-card processing, "
            "shrinkage, and scheduled labor (wages are hours, not a share of sales)."
        )

    with st.expander("2. Key Assumptions"):
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("Capital")
            cap_df = pd.DataFrame([
                ("Total Project Cost", fmt_dollar(model.TOTAL_PROJECT_COST)),
                ("Funding", f"Bank term loan @ {model.LOAN_INTEREST_RATE:.1%}, "
                            f"{model.LOAN_TERM_YEARS}yr fully amortizing"),
                ("Already Spent", fmt_dollar(model.ALREADY_SPENT)),
                ("Remaining to Spend", fmt_dollar(model.NEW_CASH_NEEDED)),
                ("Monthly Operating Nut (incl. loan payment)", fmt_dollar(model.MONTHLY_NUT)),
            ], columns=["Parameter", "Value"])
            st.dataframe(cap_df, use_container_width=True, hide_index=True)
        with col_r:
            st.subheader("Ramps & Levers")
            _bar_full = max(model.BAR_Y1_RAMP) + 1
            _fill_full = max(model.TRUCK_Y1_FILL_RAMP) + 1
            ramp_df = pd.DataFrame([
                ("Truck lease-up (Yr 1)",
                 f"{model.TRUCK_Y1_FILL_RAMP[1]:.0%} of {model.TRUCK_SLOTS} hubs at "
                 f"open → fully leased by month {_fill_full} (no contracts signed yet)"),
                ("Truck occupancy",
                 f"{model.TRUCK_OCCUPANCY:.0%} steady-state vacancy haircut, "
                 "applied on top of lease-up"),
                ("Bar / daytime beverages (Yr 1)",
                 f"{model.BAR_Y1_RAMP[1]:.0%} month 1 → 100% by month {_bar_full} "
                 "(cold-start discovery curve)"),
                ("Seasonality (all year)",
                 f"{min(model.SEASONALITY.values()):.2f}–{max(model.SEASONALITY.values()):.2f} "
                 "by month — Austin patio weather, the dominant swing"),
                ("Sports density (all year)",
                 f"{min(model.SPORTS_DENSITY.values()):.2f}–{max(model.SPORTS_DENSITY.values()):.2f} "
                 "by month — evening bar only; averages ~1.00 so it redistributes "
                 "traffic rather than adding revenue"),
            ], columns=["Lever", "Schedule"])
            st.dataframe(ramp_df, use_container_width=True, hide_index=True)

    with st.expander("3. Texas Tax Stack"):
        st.markdown(
            "Texas has no personal income tax, but this business is far from "
            "untaxed — and an MB permittee files **monthly** returns. Every "
            "rate below is a real operating cost already netted out of NOI."
        )
        tax_df = pd.DataFrame([
            ("Mixed Beverage Gross Receipts Tax",
             f"{model.GRT_RATE:.1%} after sales tax is backed out",
             "Permittee's own liability. On tax-inclusive prices, sales tax "
             "comes out of the cash receipt first so GRT is not charged on "
             "the sales tax"),
            ("Mixed Beverage Sales Tax",
             f"{model.MB_SALES_TAX_RATE:.2%} embedded in the cash price",
             "A second, separate tax. Under an MB permit it hits every "
             "alcoholic drink including canned beer. Extracted as "
             "rate / (1 + rate) from the tax-inclusive receipt"),
            ("Sales tax — daytime beverages",
             f"{model.DAYTIME_BEVERAGE_SALES_TAX_RATE:.2%}",
             "Standard Del Valle/Travis County rate — not alcohol, so no GRT"),
            ("Sales tax — event parking",
             f"{model.PARKING_SALES_TAX_RATE:.2%} embedded in the cash price",
             "Motor vehicle parking is an explicitly taxable service in TX "
             "(34 TAC 3.315). Extracted from the tax-inclusive price"),
            ("Property tax — land",
             fmt_dollar(model.FIXED_COSTS['property_tax'] * 12) + "/yr",
             "Actual bill; county assesses the land at "
             f"{fmt_dollar(model.LAND_ASSESSED_VALUE)}"),
            ("Property tax — improvements",
             f"{model.PROPERTY_TAX_IMPROVEMENT_RATE:.1%} of buildout "
             f"({fmt_dollar(model.FIXED_COSTS['property_tax_improvements'] * 12)}/yr)",
             "The buildout joins the tax roll once complete"),
            ("Employer payroll (FICA/FUTA/SUTA)",
             f"~{model.EMPLOYER_PAYROLL_BURDEN_RATE:.0%} of all cash wages",
             "Applies to daytime, evening, event-extra, overtime allowance, "
             "and the manager salary. Lodging is not in the wage base"),
            ("Federal income + self-employment tax",
             f"~{model.EFFECTIVE_INCOME_TAX_RATE:.0%} blended on profit",
             "See the Tax Strategies tab for depreciation and S-corp levers"),
            ("Texas franchise tax",
             "$0 owed",
             "2026 no-tax-due threshold is $2.65M revenue; this projects well "
             "under $1M. A Public Information Report must still be filed"),
        ], columns=["Tax", "Rate", "Notes"])
        st.dataframe(tax_df, use_container_width=True, hide_index=True)
        st.caption(
            "The \\$5,300 TABC Mixed Beverage permit (two years; \\$2,650 at "
            "renewal) is already paid and sits inside the \\$120,000 LOC payoff. "
            f"It is not in the Use of Funds permits line "
            f"(\\${model.HEALTH_LICENSE:,.0f} health permit and business license). "
            "This model records the permit as paid, not as "
            "a permit number and not as transferable collateral. Confirm the "
            "tax stack with a TABC-savvy CPA before filing."
        )

    with st.expander("4. Project Snapshot"):
        st.markdown(
            rf"""
            | | This project |
            |---|---|
            | Capital | \${model.TOTAL_PROJECT_COST:,.0f} bank term loan |
            | Rate / structure | {model.LOAN_INTEREST_RATE:.1%}, {model.LOAN_TERM_YEARS}-yr fully amortizing |
            | Financing cost | \${model.LOAN_MONTHLY_PAYMENT:,.0f}/mo fixed P&I |
            | Monthly nut | \${model.MONTHLY_NUT:,.0f} (\${model.MONTHLY_OPEX_NUT:,.0f} opex + the loan payment) |
            | Land | {model.LAND_ACRES} deeded acres, owned outright (\${model.LAND_PURCHASE_PRICE:,.0f} basis) — no rent or mortgage in the nut |
            | Truck count | {model.TRUCK_SLOTS} hubs, leasing up over Year 1 (no more budgeted) |
            | Cost basis | Itemized from the owner's real Phase 0.5 cost tracker + the actual loan request |
            | Manager | \${model.MANAGER_ANNUAL_SALARY:,.0f} cash salary. Lodging is provided and not expensed |
            | Floor labor | Daytime \${model.DAYTIME_ATTENDANT_WAGE:.0f}/hr, evening \${model.EVENING_BARTENDER_WAGE:.0f}/hr. Weekday hours {model.LABOR_WEEKDAY_DAYTIME_HOURS:.1f}/{model.LABOR_WEEKDAY_EVENING_HOURS:.1f}, weekend {model.LABOR_WEEKEND_DAYTIME_HOURS:.1f}/{model.LABOR_WEEKEND_EVENING_HOURS:.1f}, race-day evening {model.LABOR_RACE_EVENING_HOURS:.1f} plus one extra body. {model.OVERTIME_ALLOWANCE_RATE:.0%} overtime allowance, {model.EMPLOYER_PAYROLL_BURDEN_RATE:.0%} burden. The 5% share is removed. Wages are estimates |
            | Bar offering | Full container bar: \${model.DRAFT_BEER_PRICE:.0f} draft / \${model.BEER_PRICE:.0f} canned / \${model.SHOT_PRICE:.0f} shots / \${model.COCKTAIL_PRICE:.0f} cocktails; premium pricing during COTA events |
            | Coverage metrics | Nut Coverage (plain-language) + real DSCR (CRE Investment Summary tab) |
            | Primary output | Owner summary + FCF yield + loan amortization schedule + CRE underwriting view |
            """
        )
        st.caption(
            "The loan is a real, fixed-payment amortizing bank term loan — "
            "this model no longer uses the smaller interest-only personal "
            "line of credit it started with, which the loan pays off in "
            "full. Analysis toolkit: Monte Carlo, scenarios, sensitivity, "
            "break-even, multi-year, waterfall, and a full CRE underwriting "
            "tab."
        )

    with st.expander("5. Function Reference"):
        st.code(
            """
model.run_annual_projection()       # 12-month projection; year=1 ramped, year=2 steady state
model.run_multi_year_projection()   # Years 1-3 with growth + cost inflation
model.run_monte_carlo()             # 10K randomized Year 1 scenarios
model.run_scenario_comparison()     # 5 named scenarios side by side
model.run_breakeven_analysis()      # zero-bar test + min bar traffic targets
model.run_sensitivity_analysis()    # one-lever-at-a-time sweeps
model.run_cash_reserve_tracker()    # month-by-month cash balance + payback month
model.run_loan_amortization_schedule() # loan balance/interest; optional extra-prepayment sweep
model.run_tax_strategy_analysis()   # depreciation + Sec 195 + S-corp election
model.print_tax_strategy_analysis() # same, printed (CLI)
model.print_owner_summary()         # full owner-facing report (CLI)
model.calc_valuation_and_leverage() # cap-rate value, LTC/LTV, debt yield, DSCR
model.run_returns_analysis()        # unlevered/levered IRR, NPV, equity multiple
model.run_cre_sensitivity_grid()    # revenue x exit-cap-rate IRR grid
model.run_rate_sensitivity_analysis() # DSCR + levered IRR across candidate loan rates
model.run_bank_case_underwriting()  # packaged conservative case for a lender

# Regression tests — run after ANY change to the calculation engine:
#   pytest -q
            """,
            language="python",
        )


# =============================================================================
# TAB 11: CRE INVESTMENT SUMMARY
# =============================================================================
with tabs[11]:
    st.header("CRE Investment Summary")
    st.warning(model.get_cre_review_supersession_banner())
    st.caption(
        "Formal commercial real estate underwriting view of this project — "
        "sources & uses, stabilized NOI, cap-rate valuation, leverage, and "
        "unlevered/levered returns. This tab intentionally uses standard "
        "CRE terminology that differs from the plain-language figures "
        "elsewhere in this dashboard (e.g. NOI here excludes the loan "
        "payment, where 'Free Cash Flow' on other tabs includes it) — each "
        "metric's tooltip gives the exact formula."
    )

    # Stabilized (steady-state, no ramps) figures at current sidebar inputs -
    # CRE valuation is always done off stabilized NOI, not a ramped Year 1.
    _, stab = get_annual(weekday_customers, weekend_customers, avg_check,
                         truck_slots, truck_rent, truck_share, truck_sales,
                         truck_occupancy, seasonal_pct,
                         daytime_bev_attach, daytime_bev_price,
                         cota_impact_multiplier, yr=2)
    st.caption("All figures below are the **stabilized (steady-state) run rate** "
               "at the current sidebar inputs, regardless of the sidebar's "
               "Projection View toggle — CRE valuation is done off stabilized "
               "NOI, not a ramped opening year.")

    # --- 1. Sources & Uses ---
    st.subheader("1. Sources & Uses")
    buildout_capitalized = model.TOTAL_CAPITALIZED_BASIS - model.LAND_PURCHASE_PRICE
    su1, su2, su3, su4 = st.columns(4)
    su1.metric("Land (Contributed, at Basis)", fmt_dollar(model.LAND_PURCHASE_PRICE),
               help="Owner's actual purchase price. Owned outright, not "
                    "financed by this project's bank loan.")
    su2.metric("Buildout (Capitalized)", fmt_dollar(buildout_capitalized),
               help="Phase 0.5 historical buildout ($66,800, already "
                    "financed via the owner's prior personal LOC) plus new "
                    "construction and soft costs (septic, paving, container "
                    "bar, permits, contingency). Excludes the LOC-payoff "
                    "line (refinancing, not a new asset) and Reserve & "
                    "Safety Cash (uncommitted, not yet spent on an asset).")
    su3.metric("Total Capitalized Basis", fmt_dollar(model.TOTAL_CAPITALIZED_BASIS),
               help="Land + capitalized buildout. The correct denominator "
                    "for a yield-on-cost calculation — excluding land, as "
                    "this dashboard's other 'FCF Yield' metrics do, only "
                    "measures return on cash actually spent, not on the "
                    "full capital committed to the project.")
    su4.metric("Bank Loan (Debt)", fmt_dollar(model.LOAN_AMOUNT),
               help="Sized ask. Funds new construction, pays off the prior "
                    "LOC, prepays six months of land carry, and leaves the "
                    "reserve floor. A $500,000 check does not cover these uses.")

    su_df = pd.DataFrame([
        {"Source / Use": "Property equity (capitalized basis − loan)",
         "Amount": model.PROPERTY_EQUITY,
         "% of Basis": model.PROPERTY_EQUITY / model.TOTAL_CAPITALIZED_BASIS},
        {"Source / Use": f"Bank term loan (debt) @ {model.LOAN_INTEREST_RATE:.1%}, {model.LOAN_TERM_YEARS}yr",
         "Amount": model.LOAN_AMOUNT,
         "% of Basis": model.LOAN_AMOUNT / model.TOTAL_CAPITALIZED_BASIS},
        {"Source / Use": "Total Capitalized Basis", "Amount": model.TOTAL_CAPITALIZED_BASIS, "% of Basis": 1.0},
    ])
    su_df["Amount"] = su_df["Amount"].apply(fmt_dollar)
    su_df["% of Basis"] = su_df["% of Basis"].apply(lambda x: f"{x:.1%}")
    st.dataframe(su_df, use_container_width=True, hide_index=True)
    st.markdown("**Equity schedule — every row sums to the next subtotal**")
    eq_df = pd.DataFrame(model.equity_schedule_rows())
    eq_df["Amount"] = eq_df["amount"].apply(fmt_dollar)
    eq_df = eq_df.rename(columns={"line": "Line", "role": "Role"})[["Line", "Amount", "Role"]]
    st.dataframe(eq_df, use_container_width=True, hide_index=True)
    # Read the reserve and payoff straight out of USE_OF_FUNDS so this
    # caption can't drift from the engine (the TABC-permit correction moved
    # $5,300 from the permits line into the reserve).
    _reserve_amt = next(a for l, a, _ in model.USE_OF_FUNDS
                        if l.startswith("Reserve & Safety Cash"))
    _payoff_amt = next(a for l, a, _ in model.USE_OF_FUNDS
                       if l.startswith("Payoff of existing"))
    st.caption(
        f"Property equity is \\${model.PROPERTY_EQUITY:,.0f} "
        "(capitalized basis minus the loan). Total economic equity is "
        f"\\${model.TOTAL_ECONOMIC_EQUITY:,.0f} (property equity plus the "
        f"\\${_reserve_amt:,.0f} reserve). Those are different numbers; the "
        "schedule above is what adds up. Land at "
        f"\\${model.LAND_PURCHASE_PRICE:,.0f} is a related-party transfer "
        "basis, not an appraisal — loan divided by that figure is not LTV. "
        f"\\${_payoff_amt:,.0f} of the loan pays off the prior personal LOC "
        "(cash already spent, not a new asset)."
    )

    uses_df = pd.DataFrame(model.USE_OF_FUNDS, columns=["Use", "Amount", "Status"])
    uses_df["Amount"] = uses_df["Amount"].apply(fmt_dollar)
    st.markdown("**Uses of the sized loan**")
    st.dataframe(uses_df, use_container_width=True, hide_index=True)
    st.caption(
        f"Bank-case contingency at {model.CONTINGENCY_RATE_BANK:.0%} sizes a "
        f"separate ask of \\${model.build_use_of_funds(contingency_rate=model.CONTINGENCY_RATE_BANK)['ask']:,.0f}. "
        "That case does not change the Base uses above."
    )

    st.markdown("**PropCo / OpCo**")
    split = model.run_propco_opco_split(stab)
    pc1, pc2, pc3, pc4 = st.columns(4)
    pc1.metric("Lease payment (OpCo → PropCo)", fmt_dollar(split["lease_payment"]),
               help=split["lease_note"])
    pc2.metric("PropCo NOI", fmt_dollar(split["propco_noi"]),
               help="Truck rent, percentage rent, event parking, and the lease, "
                    "less property opex and the replacement reserve.")
    pc3.metric("OpCo NOI", fmt_dollar(split["opco_noi"]),
               help="Bar and beverage contribution after labor, less operating "
                    "costs and the lease. Negative means the bar does not cover "
                    "its own wages and rent.")
    pc4.metric("Consolidated NOI", fmt_dollar(split["consolidated_noi"]),
               help="Lease eliminates. This matches stabilized NOI.")
    if not split["consolidated_ties"]:
        st.error("PropCo + OpCo does not tie to consolidated NOI.")

    st.markdown("**DSCR by loan product** — Base, Bank Case, and no-COTA. "
                "Proposal math uses Base. Bank Case and no-COTA are stress, not upside.")
    dscr_pkg = model.run_loan_size_dscr()
    dscr_df = pd.DataFrame(dscr_pkg["rows"])
    show = dscr_df[dscr_df["product"].isin(["sba_7a", "sba_504"])].copy()
    show["NOI"] = show["noi"].apply(fmt_dollar)
    show["DSCR"] = show["dscr"].apply(lambda x: f"{x:.2f}x")
    show["Loan"] = show["loan_amount"].apply(lambda x: f"${x:,.0f}")
    show["ADS"] = show["annual_debt_service"].apply(fmt_dollar)
    show = show.rename(columns={
        "case": "Case", "year": "Year", "product_label": "Product",
    })[["Case", "Year", "Loan", "Product", "NOI", "ADS", "DSCR"]]
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.caption(dscr_pkg["note_500k"] + " " + dscr_pkg["note_750k"]
               + " 7(a) is 10% variable / 25 years. 504 is a 50/40 blend "
               "(bank ~7.5%, CDC 6.97%), both 25 years, fees not included. "
               "Both SBA products typically require a personal guarantee.")

    with st.expander("Rate grid — Lender Base vs Bank Case (not mixed)"):
        matrix = model.run_dscr_matrix()
        rate_rows = []
        for case_name, block in (("Lender Base", matrix["lender_base"]),
                                 ("Bank Case", matrix["bank_case"])):
            for year, payload in block.items():
                row = {"Case": case_name, "Year": year,
                       "NOI": payload["noi_gc"]}
                for rate, dscr in payload["going_concern"].items():
                    row[f"{rate:.1%}"] = dscr
                rate_rows.append(row)
        rate_grid = pd.DataFrame(rate_rows)
        rate_grid["NOI"] = rate_grid["NOI"].apply(fmt_dollar)
        for col in rate_grid.columns:
            if col not in ("Case", "Year", "NOI"):
                rate_grid[col] = rate_grid[col].apply(lambda x: f"{x:.2f}x")
        st.dataframe(rate_grid, use_container_width=True, hide_index=True)
        st.caption("Going-concern NOI. Bank Case uses stressed operations and "
                   "the 15% contingency ask. It is not the proposal case.")

    with st.expander("Construction draws and assumptions appendix"):
        schedule = model.build_construction_draw_schedule()
        st.write(schedule["note"])
        draw_df = pd.DataFrame(schedule["months"])
        st.dataframe(draw_df, use_container_width=True, hide_index=True)
        assumptions_df = pd.DataFrame(model.export_assumptions_rows())
        assumptions_df["value"] = assumptions_df["value"].astype(str)
        st.dataframe(assumptions_df, use_container_width=True, hide_index=True)
        st.download_button("Download sources & uses CSV", model.export_su_csv(),
                           file_name="sources_and_uses.csv", mime="text/csv")
        st.download_button("Download DSCR matrix CSV",
                           model.export_dscr_matrix_csv(matrix),
                           file_name="dscr_matrix.csv", mime="text/csv")
        st.download_button("Download draw schedule CSV",
                           model.export_draw_schedule_csv(schedule),
                           file_name="draw_schedule.csv", mime="text/csv")
        st.download_button("Download assumptions CSV", model.export_assumptions_csv(),
                           file_name="assumptions.csv", mime="text/csv")
    st.caption(model.get_entity_guarantor_notes())

    # --- 2. Stabilized Operations ---
    st.markdown("---")
    st.subheader("2. Stabilized Operations")
    op1, op2, op3, op4 = st.columns(4)
    op1.metric("Effective Gross Income", fmt_dollar(stab["total_gross"]),
               help="All revenue streams, including the at-cost utility pass-through.")
    op2.metric("Management Fee", fmt_dollar(stab["total_management_fee"]),
               help=f"{model.MANAGEMENT_FEE_RATE:.0%} of EGI ex. utility "
                    "pass-through — market 3rd-party property management "
                    "cost, charged whether or not this owner collects it.")
    op3.metric("Replacement Reserve", fmt_dollar(stab["total_replacement_reserve"]),
               help=f"{model.REPLACEMENT_RESERVE_RATE:.0%} of EGI ex. "
                    "utility pass-through — capital reserve for FF&E / "
                    "site replacement.")
    op4.metric("Net Operating Income (NOI)", fmt_dollar(stab["total_noi"]),
               help="EGI less all operating expenses (incl. management fee "
                    "and replacement reserve), BEFORE debt service. This is "
                    "the standard CRE NOI figure — it excludes the loan "
                    "payment, unlike the 'Free Cash Flow' figures "
                    "elsewhere in this dashboard.")

    st.caption("**Real Estate vs. Operating Business Contribution** — pre-shared-overhead "
               "(management fee, replacement reserve, and per-event COTA staffing "
               "costs apply to the consolidated property, not to either segment individually)")
    seg1, seg2, seg3 = st.columns(3)
    re_contrib = stab["total_real_estate_contribution"]
    biz_contrib = stab["total_business_contribution"]
    seg1.metric("Real Estate", fmt_dollar(re_contrib),
                help="Pad rent (intended contractual terms; leases not "
                     "executed) + percentage rent (non-contractual) + "
                     "transactional event parking, net of upkeep and tax, "
                     "plus the at-cost utility pass-through.")
    seg2.metric("Operating Business", fmt_dollar(biz_contrib),
                help="Evening bar + daytime beverages + seasonal events + "
                     "COTA bar/beverage uplifts, net of their own COGS, "
                     "tax, and labor. F&B business enterprise value, not "
                     "real property income.")
    seg3.metric("Business Share of Contribution",
                fmt_pct(biz_contrib / (re_contrib + biz_contrib) * 100) if (re_contrib + biz_contrib) else "n/a")
    mix = model.calc_revenue_mix(stab)
    mix_df = pd.DataFrame([
        {"Component": "Contractual pad rent (leases not executed)",
         "Amount": mix["contractual_pad_rent"],
         "Share of gross": mix["contractual_pad_rent_share"]},
        {"Component": mix["percentage_rent_label"],
         "Amount": mix["noncontractual_percentage_rent"],
         "Share of gross": mix["noncontractual_percentage_rent"] / mix["gross"] if mix["gross"] else 0},
        {"Component": mix["event_parking_label"],
         "Amount": mix["transactional_event_parking"],
         "Share of gross": mix["transactional_event_parking"] / mix["gross"] if mix["gross"] else 0},
        {"Component": "Property + parking",
         "Amount": mix["property_and_parking"],
         "Share of gross": mix["property_and_parking_share"]},
    ])
    mix_df["Amount"] = mix_df["Amount"].apply(fmt_dollar)
    mix_df["Share of gross"] = mix_df["Share of gross"].apply(lambda x: f"{x:.1%}")
    st.dataframe(mix_df, use_container_width=True, hide_index=True)
    st.caption(
        "Shares are of total gross revenue, including the utility pass-through. "
        "Property + parking is pad rent, percentage rent, and event parking — "
        "about half of gross at the base case, not a 58% headline. Percentage "
        "rent stays non-contractual until leases are signed."
    )

    # --- 3. Valuation & Leverage ---
    st.markdown("---")
    st.subheader("3. Valuation & Leverage")
    cap_rate_pct = st.slider(
        "Market Cap Rate (%)", 6.0, 14.0, model.MARKET_CAP_RATE * 100, step=0.25,
        help="Used both to value the property today (NOI / cap rate) and "
             "as the default exit assumption in the Returns section below.")
    cap_rate = cap_rate_pct / 100
    val = model.calc_valuation_and_leverage(stab, cap_rate=cap_rate)

    v1, v2, v3 = st.columns(3)
    v1.metric("Implied Value (NOI ÷ Cap Rate)", fmt_dollar(val["implied_value"]))
    v2.metric("Yield on Cost", fmt_pct(val["yield_on_cost"] * 100),
              help="Stabilized NOI ÷ Total Capitalized Basis (land + "
                   "buildout). Compare to the market cap rate — the gap is "
                   "the development spread.")
    v3.metric("Development Spread", f"{val['development_spread'] * 100:+.1f} pts",
              help="Yield on cost minus the market cap rate. Positive means "
                   "the project was built cheaper than it can be sold for "
                   "at a stabilized cap rate.")

    l1, l2, l3, l4, l5 = st.columns(5)
    l1.metric("Loan-to-Cost (LTC)", fmt_pct(val["ltc"] * 100),
              help="Loan amount ÷ Total Capitalized Basis.")
    l2.metric("Cap-rate LTV (indication)", fmt_pct(val["ltv"] * 100),
              help="Loan ÷ (NOI / the cap rate above). An indication, not an "
                   "appraisal, and not loan ÷ the $1.4M related-party land basis.")
    l3.metric("Debt Yield", fmt_pct(val["debt_yield"] * 100),
              help="NOI ÷ loan amount. A value-independent leverage test "
                   "lenders use because it can't be moved by a cap-rate "
                   "assumption. Typical minimums: ~9-11% general CRE, "
                   "11-13% hospitality/F&B.")
    l4.metric("DSCR", f"{val['dscr']:.2f}x" if val["dscr"] is not None else "n/a",
              help=f"NOI ÷ annual debt service (${val['annual_debt_service']:,.0f}/yr "
                   f"at the {val['loan_rate']:.1%} loan rate). The actual lender "
                   "covenant ratio for a real amortizing loan — typical "
                   "minimums 1.20-1.30x general CRE, 1.35-1.50x hospitality/F&B, "
                   "because operating income is less contractual than rent.")
    l5.metric("Fixed Charge Coverage Ratio (FCCR)",
              f"{stab['avg_monthly_nut_coverage']:.2f}x",
              help="Operating income before fixed overhead ÷ total monthly "
                   "nut (opex + debt service) — a broader ratio than DSCR "
                   "since the denominator also includes cash opex, shown "
                   "elsewhere in this dashboard as 'Nut Coverage.' DSCR "
                   "above is the ratio an actual lender covenant would use.")
    if val["leverage_dilutive"]:
        st.warning(
            f"Leverage is dilutive on yield: yield on cost "
            f"({val['yield_on_cost']:.1%}) is below the loan rate "
            f"({val['loan_rate']:.1%}). Debt does not improve the unlevered yield."
        )
    collateral = model.calc_collateral_indications(stab)
    st.markdown("**Collateral indications — not an appraisal**")
    st.caption(
        "None of these is a headline LTV. Loan ÷ the $1.4M land figure is a "
        "related-party basis ratio. Segment value capitalizes real-estate "
        f"contribution at {model.PROPERTY_INCOME_CAP_RATE:.1%} and the operating "
        f"business at {model.GOING_CONCERN_EBITDA_MULTIPLE:.1f}×, with shared "
        "overhead unallocated. An independent appraisal is still required."
    )
    col_df = pd.DataFrame([
        {"Reading": "Loan / related-party land basis (not LTV)",
         "Value": collateral["loan_over_related_party_land_basis"]},
        {"Reading": "Loan / capitalized cost (LTC)",
         "Value": collateral["ltc_on_capitalized_cost"]},
        {"Reading": "Loan / segment indication (unallocated overhead)",
         "Value": collateral["ltv_segment_indication"] or 0},
    ])
    col_df["Value"] = col_df["Value"].apply(lambda x: f"{x:.1%}")
    st.dataframe(col_df, use_container_width=True, hide_index=True)

    st.markdown("**Interest Rate Sensitivity**")
    st.caption(
        f"{model.LOAN_INTEREST_RATE:.1%} is a placeholder pending an actual "
        "bank quote — the rate most likely to move before closing. DSCR and "
        "levered IRR at stabilized NOI across a candidate rate range:"
    )
    rate_sensitivity_years = get_multi_year(
        weekday_customers, weekend_customers, avg_check,
        truck_slots, truck_rent, truck_share, truck_sales,
        truck_occupancy, seasonal_pct,
        daytime_bev_attach, daytime_bev_price,
        cota_impact_multiplier, years=model.HOLD_PERIOD_YEARS + 1)
    rate_rows = model.run_rate_sensitivity_analysis(
        annual=stab, base_years=rate_sensitivity_years, exit_cap_rate=cap_rate)
    rate_df = pd.DataFrame(rate_rows)
    rate_df["rate"] = rate_df["rate"].apply(lambda r: f"{r:.1%}")
    rate_df["annual_debt_service"] = rate_df["annual_debt_service"].apply(fmt_dollar)
    rate_df["dscr"] = rate_df["dscr"].apply(lambda x: f"{x:.2f}x" if x is not None else "n/a")
    rate_df["levered_irr"] = rate_df["levered_irr"].apply(lambda x: f"{x:.1%}" if x is not None else "n/a")
    rate_df["levered_equity_multiple"] = rate_df["levered_equity_multiple"].apply(
        lambda x: f"{x:.2f}x" if x is not None else "n/a")
    rate_df = rate_df.drop(columns=["monthly_payment"]).rename(columns={
        "rate": "Loan Rate", "annual_debt_service": "Annual Debt Service",
        "dscr": "DSCR", "levered_irr": "Levered IRR",
        "levered_equity_multiple": "Levered Eq. Multiple",
    })
    st.dataframe(rate_df, use_container_width=True, hide_index=True)

    # --- 4. Returns ---
    st.markdown("---")
    st.subheader("4. Returns — Unlevered & Levered")
    st.caption(
        f"IRR/NPV delay operating cash flows by {model.RETURNS_DELAY_MONTHS} months "
        f"({model.ENTITLEMENT_PERMIT_LAG_MONTHS} months of entitlement + "
        f"{model.CONSTRUCTION_PERIOD_MONTHS} month of construction). "
        "Land carry is in sources and uses. Pre-open debt service is in the "
        "cash tracker. The draw schedule is in the expander above."
    )
    r1, r2, r3, r4 = st.columns(4)
    hold_years = r1.slider("Hold Period (yrs)", 3, 10, model.HOLD_PERIOD_YEARS, step=1)
    exit_cap_pct = r2.slider("Exit Cap Rate (%)", 6.0, 14.0, model.MARKET_CAP_RATE * 100, step=0.25)
    sale_cost_pct = r3.slider("Sale Costs (%)", 0.0, 6.0, model.SALE_COST_PCT * 100, step=0.5) / 100
    discount_pct = r4.slider("NPV Discount Rate (%)", 4.0, 20.0, model.DISCOUNT_RATE * 100, step=0.5) / 100
    exit_cap_rate = exit_cap_pct / 100

    base_years = get_multi_year(weekday_customers, weekend_customers, avg_check,
                                truck_slots, truck_rent, truck_share, truck_sales,
                                truck_occupancy, seasonal_pct,
                                daytime_bev_attach, daytime_bev_price,
                                cota_impact_multiplier, years=hold_years + 1)
    returns = model.run_returns_analysis(
        hold_years=hold_years, exit_cap_rate=exit_cap_rate,
        sale_cost_pct=sale_cost_pct, discount_rate=discount_pct,
        base_years=base_years)

    ru, rl = st.columns(2)
    with ru:
        st.markdown("**Unlevered (all-cash, no loan)**")
        st.metric("IRR", fmt_pct(returns["unlevered_irr"] * 100) if returns["unlevered_irr"] is not None else "n/a")
        st.metric("Equity Multiple", f"{returns['unlevered_equity_multiple']:.2f}x")
        st.metric("NPV", fmt_dollar(returns["unlevered_npv"]))
    with rl:
        st.markdown("**Levered (with the bank loan)**")
        st.metric("IRR", fmt_pct(returns["levered_irr"] * 100) if returns["levered_irr"] is not None else "n/a")
        st.metric("Equity Multiple",
                  f"{returns['levered_equity_multiple']:.2f}x" if returns["levered_equity_multiple"] is not None else "n/a")
        st.metric("NPV", fmt_dollar(returns["levered_npv"]))
    if returns["leverage_dilutive"] and returns["levered_irr"] is not None and returns["unlevered_irr"] is not None:
        st.warning(
            f"Levered IRR ({returns['levered_irr']:.1%}) is below unlevered IRR "
            f"({returns['unlevered_irr']:.1%}). At these assumptions the loan "
            "dilutes equity returns. Both figures stay on screen."
        )
    st.metric("Cash-on-Cash (Year 1)",
              fmt_pct(returns["cash_on_cash_year1"] * 100) if returns["cash_on_cash_year1"] is not None else "n/a",
              help="Year 1 net cash flow after debt service ÷ equity basis "
                   "(land + cash equity in the deal). The only true "
                   "cash-on-cash figure in this model — the other 'yield' "
                   "metrics elsewhere divide by cost, not equity.")
    st.caption(
        f"Reversion (sale) value: \\${returns['reversion_gross']:,.0f} gross, "
        f"\\${returns['reversion_net']:,.0f} net of {sale_cost_pct:.1%} sale "
        "costs — based on the NOI in the year immediately after the hold ends, "
        "capitalized at the exit cap rate above (standard forward-cap convention)."
    )

    # --- 5. Sensitivity ---
    st.markdown("---")
    st.subheader("5. Sensitivity — Unlevered IRR")
    st.caption("Revenue scenario (bar traffic, avg check, and truck sales "
               "scaled together) × exit cap rate.")
    grid = model.run_cre_sensitivity_grid(
        revenue_deltas=(-0.10, -0.05, 0.0, 0.05, 0.10),
        exit_cap_rates=(0.07, 0.08, 0.09, 0.10, 0.11),
        hold_years=hold_years,
        base_weekday_customers=weekday_customers, base_weekend_customers=weekend_customers,
        base_check=avg_check, base_truck_avg_sales=truck_sales,
        truck_slots=truck_slots, truck_rent=truck_rent, truck_share_rate=truck_share,
        truck_occupancy=truck_occupancy, seasonal_pct=seasonal_pct,
        daytime_beverage_attach_rate=daytime_bev_attach,
        daytime_beverage_avg_price=daytime_bev_price,
        cota_impact_multiplier=cota_impact_multiplier,
    )
    grid_df = pd.DataFrame(grid)
    cap_cols = [c for c in grid_df.columns if c != "revenue_delta"]
    for c in cap_cols:
        grid_df[c] = grid_df[c].apply(lambda x: f"{x:.1%}" if x is not None else "n/a")
    grid_df["revenue_delta"] = grid_df["revenue_delta"].apply(lambda d: f"{d:+.0%}")
    grid_df = grid_df.rename(columns={"revenue_delta": "Revenue Δ",
                                      **{c: f"{c:.0%} cap" for c in cap_cols}})
    st.dataframe(grid_df, use_container_width=True, hide_index=True)

    # --- 6. Bank Case ---
    st.markdown("---")
    st.subheader("6. Bank Case — Conservative Underwriting")
    st.caption(
        "One packaged conservative case, more useful to a loan officer than "
        "the plain-language Scenarios tab's generic Worst Case/Upside: it "
        "stacks the *specific* risks this deal carries — no signed truck "
        "leases yet, a softer bar, no contractual relationship with COTA's "
        "event calendar, a softer season, and a +150bp rate stress over "
        "the point-estimate quote — into one underwriting result."
    )
    bank_case = model.run_bank_case_underwriting()
    bc1, bc2, bc3, bc4 = st.columns(4)
    bc1.metric("Stabilized NOI", fmt_dollar(bank_case["stabilized_noi"]),
               help=f"vs. \\${stab['total_noi']:,.0f} at Base Case assumptions.")
    bc2.metric("DSCR", f"{bank_case['dscr']:.2f}x" if bank_case["dscr"] is not None else "n/a",
               help=f"At a stressed {bank_case['loan_rate']:.1%} loan rate "
                    f"(+150bp over the {model.LOAN_INTEREST_RATE:.1%} point "
                    "estimate). Compare to the 1.35-1.50x typical F&B minimum.")
    bc3.metric("Yield on Cost", fmt_pct(bank_case["yield_on_cost"] * 100))
    bc4.metric("Cap-rate LTV (indication)", fmt_pct(bank_case["ltv"] * 100),
               help=f"Loan ÷ stressed NOI at a {bank_case['cap_rate']:.1%} cap "
                    "rate. Not loan ÷ the related-party land basis, and not an appraisal.")
    bc5, bc6 = st.columns(2)
    bc5.metric("Unlevered IRR", fmt_pct(bank_case["unlevered_irr"] * 100)
               if bank_case["unlevered_irr"] is not None else "n/a")
    bc6.metric("Levered IRR", fmt_pct(bank_case["levered_irr"] * 100)
               if bank_case["levered_irr"] is not None else "n/a")
    if bank_case["levered_irr"] is None or (
        bank_case["unlevered_irr"] is not None
        and bank_case["levered_irr"] < bank_case["unlevered_irr"]
    ):
        st.warning(
            "Bank-case leverage is dilutive. Levered IRR is below unlevered "
            "IRR, or the levered cash flows have no IRR in range. The "
            "unlevered figure stays on screen."
        )
    _stress = model.SCENARIOS["Stress Test"]
    st.caption(
        f"Assumptions: {_stress['weekday_customers']}/"
        f"{_stress['weekend_customers']} weekday/weekend bar customers and a "
        f"\\${_stress['avg_check']:.2f} avg check (both read from the Stress "
        f"Test scenario), 75% truck occupancy, 85% seasonal factor, "
        f"{_stress['daytime_beverage_attach_rate']:.0%} daytime-beverage "
        "attach rate, COTA impact halved (cota_impact_multiplier=0.5). These "
        "stack independently of the sidebar sliders above — this section "
        "always shows the same fixed stress case regardless of sidebar "
        "inputs, so it stays a stable reference point."
    )

    with st.expander("Glossary"):
        st.markdown(
            """
            | Term | Definition |
            |---|---|
            | **NOI** | Effective Gross Income − operating expenses, BEFORE debt service, capex, depreciation, income tax |
            | **Cap rate** | NOI ÷ value — the market's required unlevered yield. Value = NOI ÷ cap rate |
            | **Yield on cost** | Stabilized NOI ÷ total capitalized basis. The gap vs. market cap rate is the **development spread** |
            | **LTC** | Loan ÷ total capitalized cost |
            | **Cap-rate LTV** | Loan ÷ (NOI / cap rate). An indication, not an appraisal |
            | **Related-party land ratio** | Loan ÷ the $1.4M transfer basis. Not LTV |
            | **Dilutive leverage** | Yield on cost below the loan rate, or levered IRR below unlevered IRR |
            | **Debt yield** | NOI ÷ loan amount — a value-independent leverage test |
            | **DSCR** | Debt Service Coverage Ratio — NOI ÷ annual loan P&I. The actual lender covenant ratio. Typical minimums 1.20-1.30x general CRE, 1.35-1.50x hospitality/F&B |
            | **FCCR** | Fixed Charge Coverage Ratio — operating income before overhead ÷ (opex + debt service). Broader than DSCR |
            | **Reversion** | Sale proceeds at end of hold = terminal-year NOI ÷ exit cap rate, less sale costs |
            | **Equity multiple** | Total distributions ÷ equity invested — not time-weighted |
            | **IRR** | Discount rate at which NPV of all cash flows = 0 — time-weighted |
            | **Cash-on-cash** | Annual cash flow after debt service ÷ equity invested |
            """
        )
