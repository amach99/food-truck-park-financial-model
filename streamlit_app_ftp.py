"""
Food Truck Park + Limited Bar | Del Valle
Streamlit Financial Model Dashboard (financed via a 12.5% personal line of credit)

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
    page_title="Food Truck Park + Limited Bar | Financial Model",
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
st.sidebar.caption("Food Trucks + Limited Bar (beer & shots) — Del Valle")
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

st.sidebar.subheader("Limited Bar (6pm-close, beer + shots only)")
weekday_customers = st.sidebar.slider("Weekday Customers/Evening (Mon-Thu)", 5, 50,
                                      model.BAR_WEEKDAY_CUSTOMERS, step=1)
weekend_customers = st.sidebar.slider("Weekend Customers/Evening (Fri-Sun)", 15, 100,
                                      model.BAR_WEEKEND_CUSTOMERS, step=2)
avg_check = st.sidebar.slider("Avg Check ($)", 5.0, 15.0, model.BAR_AVG_CHECK,
                              step=0.25, format="$%.2f")

st.sidebar.subheader("Other")
seasonal_pct = st.sidebar.slider("Seasonal Event Strength", 0.0, 2.0, 1.0, step=0.25)

st.sidebar.markdown("---")
st.sidebar.subheader("Monte Carlo")
mc_seed = st.sidebar.number_input("Random Seed", value=42, step=1)
mc_sims = st.sidebar.selectbox("Simulations", [1000, 5000, 10000], index=1)


# =============================================================================
# CACHED COMPUTATIONS
# =============================================================================
@st.cache_data
def get_annual(wd_custs, we_custs, check, slots, t_rent, t_share, t_sales, t_occ, seasonal, yr=1):
    return model.run_annual_projection(
        wd_custs, we_custs, year=yr, avg_check=check,
        truck_slots=slots, truck_rent=t_rent,
        truck_share_rate=t_share, truck_avg_sales=t_sales,
        truck_occupancy=t_occ, seasonal_pct=seasonal,
    )


@st.cache_data
def get_multi_year(wd_custs, we_custs, check, slots, t_rent, t_share, t_sales, t_occ, seasonal, years=3):
    return model.run_multi_year_projection(
        wd_custs, we_custs, years=years, base_check=check,
        truck_slots=slots, truck_rent=t_rent,
        truck_share_rate=t_share, truck_avg_sales=t_sales,
        truck_occupancy=t_occ, seasonal_pct=seasonal,
    )


@st.cache_data
def get_monte_carlo(n_sims, seed, wd_custs, we_custs, check, t_rent, t_share, t_occ, seasonal):
    return model.run_monte_carlo(
        n_sims, seed,
        base_weekday_customers=wd_custs, base_weekend_customers=we_custs,
        base_check=check, base_truck_rent=t_rent, base_truck_share=t_share,
        base_truck_occupancy=t_occ, base_seasonal_pct=seasonal,
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
        cota = m["cota_parking"] + m["cota_bar_uplift"]
        rows.append({
            "Month": MONTH_NAMES[m["month"] - 1],
            "Gross Revenue": m["total_gross_revenue"],
            "Food Trucks": m["truck_gross"],
            "Limited Bar": m["bar_revenue"],
            "COTA": cota,
            "Seasonal": m["seasonal_revenue"],
            "Utilities (pass-thru)": m["utility_billed"],
            "Trucks Active": m["trucks_active"],
            "NOI": m["noi"],
            "Nut Coverage": m["monthly_nut_coverage"],
            "Cash Flow": m["net_cash_flow"],
        })
    return pd.DataFrame(rows)


# Shared computation for current sidebar inputs
months, annual = get_annual(weekday_customers, weekend_customers, avg_check,
                            truck_slots, truck_rent, truck_share, truck_sales,
                            truck_occupancy, seasonal_pct)
df = months_to_df(months)


# =============================================================================
# MAIN CONTENT — TABS
# =============================================================================
st.title("Food Truck Park + Limited Bar")
st.caption(f"13901 FM 812, Del Valle, TX 78617  •  "
           f"Startup Cost: \\${model.TOTAL_PROJECT_COST:,.0f} "
           f"(LOC @ {model.LOC_INTEREST_RATE:.1%})  •  "
           f"Monthly Nut: \\${model.MONTHLY_NUT:,.0f}")

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
    "📖 Model Overview",
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
        st.subheader("Revenue Breakdown (Year 1)")
        cota_total = annual["total_cota_parking"] + annual["total_cota_bar"]
        rev_data = {
            "Stream": ["Food Trucks", "Limited Bar", "COTA Events",
                       "Seasonal", "Utilities (at cost)"],
            "Revenue": [annual["total_trucks"], annual["total_bar"],
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

    st.subheader("Year 1 Fill Trajectory")
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
    st.header("Year 1 Annual Projection")

    stream_cols = ["Food Trucks", "Limited Bar", "COTA", "Seasonal"]
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
    c4.metric("Bartender Share (5%)", fmt_dollar(annual["total_bartender_share"]))

    st.subheader("Revenue Streams")
    stream_data = {
        "Stream": ["Food Truck Rent", "Food Truck Rev Share",
                   "Limited Bar", "COTA Parking", "COTA Bar Uplift",
                   "Seasonal Events", "Utility Pass-Through (at cost)"],
        "Annual": [annual["total_truck_rent"], annual["total_truck_share"],
                   annual["total_bar"], annual["total_cota_parking"],
                   annual["total_cota_bar"], annual["total_seasonal"],
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
    display_df = df[["Month", "Gross Revenue", "Food Trucks", "Limited Bar",
                     "COTA", "NOI", "Cash Flow", "Nut Coverage"]].copy()
    for col in ["Gross Revenue", "Food Trucks", "Limited Bar", "COTA", "NOI", "Cash Flow"]:
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
    c3.metric("Startup Cost (LOC)", fmt_dollar(model.TOTAL_PROJECT_COST))

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
    st.caption("Assumes a weak truck base (4 trucks @ \\$600 + 5%, no COTA) — "
               "worst-case support from the truck-rent stream")
    be_rows = []
    for label, target, wd, we in be["bar_traffic_targets"]:
        be_rows.append({
            "Nut Coverage Target": f"{label} ({target:.2f}x)",
            "Min Weekday/Weekend Customers": f"~{wd} / ~{we}",
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

    mc_results = get_monte_carlo(mc_sims, mc_seed, weekday_customers, weekend_customers,
                                 avg_check, truck_rent, truck_share, truck_occupancy,
                                 seasonal_pct)

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
        "Randomized: truck slots (base -2 to base), truck sales (\\$10K-\\$35K/mo), "
        "bar customers/evening (10-70), avg check (\\$5-\\$13), COTA events "
        "(8-15/yr), seasonal strength (40%-150%). Truck rent and revenue "
        "share are held fixed across every simulation at the sidebar slider "
        "values (they're actual contracted terms, not something to randomize)."
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
                               truck_occupancy, seasonal_pct)

    my_rows = []
    for yr, months_data, ann in all_years:
        cota_total = ann["total_cota_parking"] + ann["total_cota_bar"]
        my_rows.append({
            "Year": f"Year {yr}",
            "Annual Revenue": ann["total_gross"],
            "Food Trucks": ann["total_trucks"],
            "Limited Bar": ann["total_bar"],
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
    for col in ["Annual Revenue", "Food Trucks", "Limited Bar", "COTA",
                "Cost Inflation", "Free Cash Flow"]:
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
    k1.metric("Opening Operating Reserve", fmt_dollar(model.OPENING_CASH_RESERVE))
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

    # LOC payoff schedule
    st.subheader("LOC Payoff Schedule")
    st.caption(f"Simulates the \\${model.LOC_AMOUNT:,.0f} LOC balance actually "
               "declining as free cash flow sweeps against principal — more "
               "realistic than the flat interest-only assumption baked into "
               "the monthly nut.")
    loc_sched = model.run_loc_payoff_schedule(all_years, verbose=False)
    loc_rows = [{
        "Period": f"Y{s['year']} {MONTH_NAMES[s['month'] - 1]}",
        "Balance": s["balance"], "Interest": s["interest"],
    } for s in loc_sched["series"]]
    loc_df = pd.DataFrame(loc_rows)

    l1, l2, l3 = st.columns(3)
    payoff = loc_sched["payoff_month"]
    l1.metric("LOC Payoff Month", f"Y{payoff[0]} {MONTH_NAMES[payoff[1]-1]}"
              if payoff else "Not within window")
    l2.metric("Total Interest Paid (actual)", fmt_dollar(loc_sched["total_interest_paid"]))
    l3.metric("vs. Flat-Assumption Interest",
              fmt_dollar(model.LOC_MONTHLY_INTEREST * len(loc_sched["series"])))

    fig_loc = go.Figure()
    fig_loc.add_trace(go.Scatter(
        x=loc_df["Period"], y=loc_df["Balance"],
        name="LOC Balance", fill="tozeroy",
        line=dict(color="#E15759", width=2),
        fillcolor="rgba(225, 87, 89, 0.2)"
    ))
    fig_loc.update_layout(
        yaxis=dict(title="LOC Balance ($)", tickformat="$,.0f"),
        margin=dict(t=40, b=40), xaxis=dict(tickangle=-45),
    )
    st.plotly_chart(fig_loc, use_container_width=True)


# =============================================================================
# TAB 7: WATERFALL
# =============================================================================
with tabs[7]:
    st.header("Year 1 Cash Flow Waterfall")

    gross = annual["total_gross"]
    bar_like = annual["total_bar"] + annual["total_cota_bar"] + annual["total_seasonal"]
    cogs = bar_like * model.COGS_RATE
    grt = bar_like * model.GRT_RATE
    cc = annual["total_cc_processing"]
    shrinkage = annual["total_shrinkage"]
    utility_cost = annual["total_utility_billed"]  # pass-through at cost
    parking_cost = annual["total_cota_parking"] * 0.05
    cota_cost = annual["total_cota_cost"]
    bartender_share = annual["total_bartender_share"]
    fixed_ex = model.ANNUAL_NUT
    pre_tax_cf = (gross - cogs - grt - cc - shrinkage - utility_cost - parking_cost
                  - cota_cost - bartender_share - fixed_ex)
    income_tax = max(0.0, pre_tax_cf) * model.EFFECTIVE_INCOME_TAX_RATE
    free_cf = pre_tax_cf - income_tax

    labels = ["Gross Revenue", f"COGS ({model.COGS_RATE:.0%})", "TX GRT (6.7%)",
              "CC Processing", "Shrinkage", "Utility Pass-Thru", "Parking Upkeep",
              "COTA Costs", "Bartender Share", "Fixed Costs (Nut)",
              f"Income Tax ({model.EFFECTIVE_INCOME_TAX_RATE:.0%})",
              "After-Tax Cash Flow"]
    values = [gross, -cogs, -grt, -cc, -shrinkage, -utility_cost, -parking_cost,
              -cota_cost, -bartender_share, -fixed_ex, -income_tax, 0]
    measures = ["absolute"] + ["relative"] * 10 + ["total"]

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
    st.subheader("Food Truck Park + Limited Bar (Beer & Shots) | Del Valle, TX")

    st.markdown("---")
    st.subheader("Startup Cost — Financed via Personal Line of Credit")
    lt1, lt2, lt3, lt4 = st.columns(4)
    lt1.metric("Total Startup Cost", fmt_dollar(model.TOTAL_PROJECT_COST))
    lt2.metric("LOC Rate", f"{model.LOC_INTEREST_RATE:.1%}")
    lt3.metric("Already Spent (Phase 0.5)", fmt_dollar(model.ALREADY_SPENT))
    lt4.metric("New Draw Needed", fmt_dollar(model.NEW_CASH_NEEDED))

    st.markdown("---")
    st.subheader("Use of Funds")
    status_labels = {"done": "✅ Done", "in_progress": "🔧 In Progress", "not_started": "⬜ Not Started"}
    use_df = pd.DataFrame(model.USE_OF_FUNDS, columns=["Item", "Amount", "Status"])
    use_df["Status"] = use_df["Status"].map(status_labels)
    use_df["Amount"] = use_df["Amount"].apply(fmt_dollar)
    st.dataframe(use_df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total: {fmt_dollar(model.TOTAL_PROJECT_COST)}**")
    st.caption("Sourced from the owner's real Phase 0.5 cost tracker — "
               "itemized at actual vendor-quoted prices, not estimated "
               "buckets. Planning-only line items that were never actually "
               "implemented (generator, grease removal, propane tank "
               "service) are excluded rather than estimated.")

    st.markdown("---")
    st.subheader("Monthly Operating Costs (The Nut)")
    nut_rows = [{"Expense": k.replace("_", " ").title(), "Monthly": fmt_dollar(v)}
                for k, v in model.FIXED_COSTS.items()]
    st.dataframe(pd.DataFrame(nut_rows), use_container_width=True, hide_index=True)
    st.markdown(f"**Total Monthly Nut: \\${model.MONTHLY_NUT:,.0f}** | "
                f"**Annual: \\${model.ANNUAL_NUT:,.0f}**")
    st.caption(f"Includes \\${model.LOC_MONTHLY_INTEREST:,.0f}/mo interest-only "
               f"carrying cost on the \\${model.LOC_AMOUNT:,.0f} LOC draw, "
               "conservatively assuming the full balance stays outstanding — "
               "see the Multi-Year tab for the LOC payoff schedule as free "
               "cash flow pays the balance down.")

    st.markdown("---")
    st.subheader("Projected Performance (Year 1)")
    _, conservative = model.run_scenario_projection(model.SCENARIOS["Conservative"])
    _, base = model.run_scenario_projection(model.SCENARIOS["Base Case"])
    perf_l, perf_r = st.columns(2)
    with perf_l:
        st.markdown("**Conservative** (4 trucks @ 88% occ, soft bar)")
        st.metric("Revenue", fmt_dollar(conservative["total_gross"]))
        st.metric("Free Cash Flow (pre-tax)", fmt_dollar(conservative["total_net_cash"]))
        st.metric("After-Tax Cash Flow", fmt_dollar(conservative["after_tax_noi"]))
        st.metric("FCF Yield (pre / after tax)",
                  f"{conservative['fcf_yield']:.0%} / {conservative['after_tax_fcf_yield']:.0%}")
    with perf_r:
        st.markdown("**Base Case** (4 trucks @ 90% occ, 20 wkday / 58 wkend bar)")
        st.metric("Revenue", fmt_dollar(base["total_gross"]))
        st.metric("Free Cash Flow (pre-tax)", fmt_dollar(base["total_net_cash"]))
        st.metric("After-Tax Cash Flow", fmt_dollar(base["after_tax_noi"]))
        st.metric("FCF Yield (pre / after tax)",
                  f"{base['fcf_yield']:.0%} / {base['after_tax_fcf_yield']:.0%}")
    st.caption(f"After-tax figures apply a {model.EFFECTIVE_INCOME_TAX_RATE:.0%} blended "
               "effective federal + self-employment rate estimate on pass-through "
               "profit (TX has no state income tax). Confirm with a CPA.")

    st.markdown("---")
    st.subheader("Risk Mitigants")
    mitigants = [
        f"LOC is revolving/interest-only — \\${model.LOC_AMOUNT:,.0f} draw at "
        f"{model.LOC_INTEREST_RATE:.1%} with no fixed amortization, so free cash "
        "flow can sweep the balance down faster than the conservative flat-"
        "interest nut assumes (see LOC Payoff Schedule)",
        "Phase 0.5 food truck park already operating (opened June 2026) — "
        "not a cold start",
        "Simple beer + sealed-shot offering = minimal labor skill/speed "
        "requirements, low equipment cost",
        "Utilities sub-metered and billed at cost (PURA §39.107) — "
        "no utility margin risk",
        "COTA upside preserved: event parking + bar uplift on race weekends",
        "100% of liquor/beer revenue retained (no rev-share on bar sales)",
    ]
    for m in mitigants:
        st.markdown(f"- {m}")


# =============================================================================
# TAB 9: MODEL OVERVIEW
# =============================================================================
with tabs[9]:
    st.header("📊 How The Model Works")
    st.caption("Leanest concept on the Del Valle land: food truck park + a "
               "limited beer/shots bar, financed via a personal line of "
               "credit — no RV park, no bank term loan")

    st.markdown(
        f"""
        This model strips the food-truck-+-RV-park concept down further:
        contracted monthly rent from food truck tenants forms a stable base,
        the limited bar adds beer and single-serve liquor shot sales, and
        COTA event weekends layer parking and bar upside on top. The
        \\${model.TOTAL_PROJECT_COST:,.0f} buildout (itemized from the owner's
        real Phase 0.5 cost tracker) is financed through a personal line of
        credit at {model.LOC_INTEREST_RATE:.1%} rather than a bank term loan — revolving,
        interest-only, no fixed amortization schedule. The model tracks the
        **monthly operating nut** (which includes the LOC's interest-only
        carrying cost) and **FCF yield on total cost** instead of a lender's
        DSCR covenant, plus a dedicated LOC payoff schedule.
        """
    )

    with st.expander("1. Revenue Streams", expanded=True):
        streams = pd.DataFrame([
            ("1. Food Trucks", "4 trucks (fixed for Year 1, no more hubs "
             "budgeted) at 90% occupancy: $500 pad rent + 10% rev share on "
             "~$20K/mo truck sales", "~$12-13K/mo", "100%"),
            ("2. Limited Bar", "6pm-close only, $7 beer + $3 shots in plastic "
             "shot glasses (no cocktails, no mixed drinks): 20 weekday / 58 "
             "weekend customers/evening averaging 1.5 drinks (~$9.00 check)",
             "~$7-9K/mo", "~58% after COGS + GRT"),
            ("3. COTA Events", "270-space event parking (dedicated 3-acre "
             "lot), day-by-day occupancy building to the marquee day (F1: "
             "45% Fri / 75% Sat / 100% Sun) + bar uplift at premium event "
             "pricing ($12 beer / $5 shot)", "Event months", "~90-95%"),
            ("4. Seasonal Events", "Super Bowl / March Madness / NYE watch "
             "parties on the big TVs", "~$2.7K/yr", "~58%"),
            ("5. Utility Pass-Through", "Sub-metered truck power/water/waste "
             "billed at cost (PURA §39.107)", "~$1.8K/mo", "0% (at-cost by law)"),
        ], columns=["Stream", "Description", "Steady-State Monthly", "Margin"])
        st.dataframe(streams, use_container_width=True, hide_index=True)

    with st.expander("2. Key Assumptions"):
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("Capital")
            cap_df = pd.DataFrame([
                ("Total Startup Cost", fmt_dollar(model.TOTAL_PROJECT_COST)),
                ("Funding", f"Personal LOC @ {model.LOC_INTEREST_RATE:.1%}, revolving/interest-only"),
                ("Already Spent (Phase 0.5)", fmt_dollar(model.ALREADY_SPENT)),
                ("New Draw Needed", fmt_dollar(model.NEW_CASH_NEEDED)),
                ("Monthly Operating Nut (incl. LOC interest)", fmt_dollar(model.MONTHLY_NUT)),
            ], columns=["Parameter", "Value"])
            st.dataframe(cap_df, use_container_width=True, hide_index=True)
        with col_r:
            st.subheader("Ramps & Levers (Year 1)")
            ramp_df = pd.DataFrame([
                ("Food trucks", "Flat at 4 (already built/running, no ramp)"),
                ("Truck occupancy", f"{model.TRUCK_OCCUPANCY:.0%} (vacancy factor; 6-mo contracts)"),
                ("Limited bar", "50% month 1 → 100% by month 8"),
            ], columns=["Stream", "Schedule"])
            st.dataframe(ramp_df, use_container_width=True, hide_index=True)

    with st.expander("3. What Changed vs. the Food Truck + RV Park Model"):
        st.markdown(
            r"""
            | | Food Truck + RV Park | Food Truck Park (this model) |
            |---|---|---|
            | Capital | \$300,000 SBA 7(a) term loan | \$75,000 personal LOC |
            | Rate / structure | 10.5%, 10-yr amortizing | 12.5%, revolving interest-only |
            | Financing cost | ~\$4,050/mo fixed P&I | ~\$781/mo interest (conservative; declines as paid down) |
            | Monthly nut | ~\$15,200 | ~\$7,000 |
            | RV pad rent | ~\$16-18K/mo | Removed entirely |
            | Truck count | 6 slots, ramps up | 4 trucks, fixed for Year 1 (no more hubs budgeted) |
            | Cost basis | Estimated buckets | Itemized from real Phase 0.5 cost tracker |
            | Cleaning/maintenance labor | Part-time paid cleaner | Park manager lives on-site free, no labor cost |
            | Event staffing | Extra bartender for big events | One bartender always, no extra hire |
            | Bar offering | Beer, prepackaged cocktails, shots | $7 beer + $3 shots (no cocktails); $12/$5 during COTA events |
            | Coverage metric | DSCR (vs. debt service) | Nut Coverage (vs. fixed opex incl. LOC interest) |
            | Primary output | Lender summary | Owner summary + FCF yield + LOC payoff schedule |
            """
        )
        st.caption(
            "Both models share the same land, the same COTA calendar, and the "
            "same analysis toolkit (Monte Carlo, scenarios, sensitivity, "
            "break-even, multi-year, waterfall)."
        )

    with st.expander("4. Function Reference"):
        st.code(
            """
model.run_annual_projection()      # 12-month projection, Year 1 or steady state
model.run_multi_year_projection()  # Years 1-3 with growth + cost inflation
model.run_monte_carlo()            # 10K randomized Year 1 scenarios
model.run_scenario_comparison()    # 5 named scenarios side by side
model.run_breakeven_analysis()     # zero-bar test + min bar traffic targets
model.run_sensitivity_analysis()   # one-lever-at-a-time sweeps
model.run_cash_reserve_tracker()   # month-by-month cash balance + payback month
model.print_owner_summary()        # full owner-facing report (CLI)
            """,
            language="python",
        )
