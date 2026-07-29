"""
Food Truck Park + Bar & Beverage Stand | Del Valle
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

st.sidebar.subheader("Evening Bar (6pm-close, beer + shots only)")
weekday_customers = st.sidebar.slider("Weekday Customers/Evening (Mon-Thu)", 5, 50,
                                      model.BAR_WEEKDAY_CUSTOMERS, step=1)
weekend_customers = st.sidebar.slider("Weekend Customers/Evening (Fri-Sun)", 15, 100,
                                      model.BAR_WEEKEND_CUSTOMERS, step=2)
avg_check = st.sidebar.slider("Avg Check ($)", 5.0, 15.0, model.BAR_AVG_CHECK,
                              step=0.25, format="$%.2f")

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
               dbev_attach, dbev_price, yr=1):
    return model.run_annual_projection(
        wd_custs, we_custs, year=yr, avg_check=check,
        truck_slots=slots, truck_rent=t_rent,
        truck_share_rate=t_share, truck_avg_sales=t_sales,
        truck_occupancy=t_occ, seasonal_pct=seasonal,
        daytime_beverage_attach_rate=dbev_attach,
        daytime_beverage_avg_price=dbev_price,
    )


@st.cache_data
def get_multi_year(wd_custs, we_custs, check, slots, t_rent, t_share, t_sales, t_occ, seasonal,
                   dbev_attach, dbev_price, years=3):
    return model.run_multi_year_projection(
        wd_custs, we_custs, years=years, base_check=check,
        truck_slots=slots, truck_rent=t_rent,
        truck_share_rate=t_share, truck_avg_sales=t_sales,
        truck_occupancy=t_occ, seasonal_pct=seasonal,
        daytime_beverage_attach_rate=dbev_attach,
        daytime_beverage_avg_price=dbev_price,
    )


@st.cache_data
def get_monte_carlo(n_sims, seed, wd_custs, we_custs, check, t_rent, t_share, t_occ, seasonal,
                    slots, t_sales, dbev_attach, dbev_price):
    return model.run_monte_carlo(
        n_sims, seed,
        base_weekday_customers=wd_custs, base_weekend_customers=we_custs,
        base_check=check, base_truck_rent=t_rent, base_truck_share=t_share,
        base_truck_occupancy=t_occ, base_seasonal_pct=seasonal,
        base_truck_slots=slots, base_truck_avg_sales=t_sales,
        base_daytime_beverage_attach_rate=dbev_attach,
        base_daytime_beverage_avg_price=dbev_price,
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
                            yr=projection_year)
df = months_to_df(months)


# =============================================================================
# MAIN CONTENT — TABS
# =============================================================================
st.title("Food Truck Park + Bar & Beverage Stand")
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
    "Tax Strategies",
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
    c4.metric("Bartender Share (5%)", fmt_dollar(annual["total_bartender_share"]))

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
                                 seasonal_pct, truck_slots, truck_sales,
                                 daytime_bev_attach, daytime_bev_price)

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
        "customers/evening, avg check (\\$5-\\$13), COTA event mix (big 4 fixed; "
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
                               daytime_bev_attach, daytime_bev_price)

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
    bartender_share = annual["total_bartender_share"]
    payroll_burden = annual["total_payroll_burden"]
    fixed_ex = model.ANNUAL_NUT
    pre_tax_cf = (gross - cogs - grt - mb_sales_tax
                  - daytime_bev_cogs - daytime_bev_tax - cc
                  - shrinkage - utility_cost - parking_cost - parking_tax
                  - cota_cost - bartender_share - payroll_burden - fixed_ex)
    income_tax = max(0.0, pre_tax_cf) * model.EFFECTIVE_INCOME_TAX_RATE
    free_cf = pre_tax_cf - income_tax

    labels = ["Gross Revenue", f"COGS ({model.COGS_RATE:.0%})",
              f"TX Mixed Bev GRT ({model.GRT_RATE:.1%})",
              f"TX Mixed Bev Sales Tax ({model.MB_SALES_TAX_RATE:.2%})",
              f"Daytime Bev COGS ({model.DAYTIME_BEVERAGE_COGS_RATE:.0%})",
              f"Daytime Bev Sales Tax ({model.DAYTIME_BEVERAGE_SALES_TAX_RATE:.2%})",
              "CC Processing", "Shrinkage", "Utility Pass-Thru", "Parking Upkeep",
              f"Parking Sales Tax ({model.PARKING_SALES_TAX_RATE:.2%})",
              "COTA Costs", "Bartender Share", "Employer Payroll Burden",
              "Fixed Costs (Nut)",
              f"Income Tax ({model.EFFECTIVE_INCOME_TAX_RATE:.0%})",
              "After-Tax Cash Flow"]
    values = [gross, -cogs, -grt, -mb_sales_tax,
              -daytime_bev_cogs, -daytime_bev_tax, -cc, -shrinkage,
              -utility_cost, -parking_cost, -parking_tax,
              -cota_cost, -bartender_share, -payroll_burden,
              -fixed_ex, -income_tax, 0]
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
               "cash flow pays the balance down. This is FIXED costs only — "
               "see Variable Operating Costs below for COGS, taxes, and "
               "everything else that scales with revenue.")

    st.markdown("---")
    st.subheader("Variable Operating Costs (Scale with Revenue)")
    st.caption("Not part of \"The Nut\" above — these move with sales volume "
               "rather than being fixed monthly bills, so they're netted "
               "against revenue in NOI instead of sitting in FIXED_COSTS. "
               "Dollar figures below are Base Case Year 1.")
    _, conservative = model.run_scenario_projection(model.SCENARIOS["Conservative"])
    _, base = model.run_scenario_projection(model.SCENARIOS["Base Case"])
    var_cost_rows = [
        {"Expense": "COGS — Evening Bar (beer/shots)",
         "Rate": f"{model.COGS_RATE:.1%} of alcohol revenue",
         "Annual (Base Case)": base["total_cogs"]},
        {"Expense": "TX Mixed Beverage GRT",
         "Rate": f"{model.GRT_RATE:.1%} of alcohol revenue",
         "Annual (Base Case)": base["total_grt"]},
        {"Expense": "TX Mixed Beverage Sales Tax",
         "Rate": f"{model.MB_SALES_TAX_RATE:.2%} of alcohol revenue (tax-inclusive pricing)",
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
        {"Expense": "Bartender Share (variable comp, not a salary)",
         "Rate": f"{model.BARTENDER_SHARE_RATE:.0%} of all beverage revenue",
         "Annual (Base Case)": base["total_bartender_share"]},
        {"Expense": "Employer Payroll Burden (FICA/FUTA/SUTA)",
         "Rate": f"{model.EMPLOYER_PAYROLL_BURDEN_RATE:.0%} on top of bartender comp",
         "Annual (Base Case)": base["total_payroll_burden"]},
        {"Expense": "COTA Parking Lot Upkeep",
         "Rate": f"{model.PARKING_UPKEEP_RATE:.0%} of event parking revenue",
         "Annual (Base Case)": base["total_cota_parking_upkeep"]},
        {"Expense": "TX Sales Tax — Event Parking",
         "Rate": f"{model.PARKING_SALES_TAX_RATE:.2%} of event parking revenue",
         "Annual (Base Case)": base["total_cota_parking_sales_tax"]},
        {"Expense": "COTA Incremental Costs (event staffing/porta-potty)",
         "Rate": "flat per event tier",
         "Annual (Base Case)": base["total_cota_cost"]},
        {"Expense": "Utility Pass-Through Cost (at cost, net-zero)",
         "Rate": "billed at cost, no markup",
         "Annual (Base Case)": base["total_utility_cost"]},
    ]
    var_df = pd.DataFrame(var_cost_rows)
    total_variable = var_df["Annual (Base Case)"].sum()
    var_df["Annual (Base Case)"] = var_df["Annual (Base Case)"].apply(fmt_dollar)
    st.dataframe(var_df, use_container_width=True, hide_index=True)
    st.markdown(f"**Total Variable Costs (Base Case, Year 1): {fmt_dollar(total_variable)}**")
    st.caption("Utility pass-through nets to $0 NOI impact (revenue and cost "
               "offset exactly — PURA §39.107) but is listed here for a "
               "complete expense picture. COTA incremental costs and "
               "bartender share only apply in months with COTA events / "
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

    st.markdown("---")
    st.subheader("Risk Mitigants")
    mitigants = [
        f"LOC is revolving/interest-only — \\${model.LOC_AMOUNT:,.0f} draw at "
        f"{model.LOC_INTEREST_RATE:.1%} with no fixed amortization, so free cash "
        "flow can sweep the balance down faster than the conservative flat-"
        "interest nut assumes (see LOC Payoff Schedule)",
        f"Land owned outright — no rent or mortgage in the monthly nut, and "
        f"{model.ALREADY_SPENT / model.TOTAL_PROJECT_COST:.0%} of the buildout "
        "is already paid for",
        "Simple beer + sealed-shot offering = minimal labor skill/speed "
        "requirements, low equipment cost",
        "Utilities sub-metered and billed at cost (PURA §39.107) — "
        "no utility margin risk",
        "COTA upside preserved: event parking + bar uplift on race weekends",
        "100% of liquor/beer revenue retained (no rev-share on bar sales)",
        "All-day beverage sales (soda/juice/water/coffee) diversify revenue "
        "beyond evening-only alcohol hours at no new fixed labor cost — "
        "same on-site bartender covers both windows",
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
               "doesn't change the pre-tax NOI used elsewhere in the model — "
               "it only estimates incremental tax savings.")
    st.info(
        "**This tab covers the FEDERAL layer only** — income tax plus "
        "self-employment/payroll tax. Texas has no personal income tax, but "
        "the business pays plenty of other Texas taxes (mixed beverage GRT "
        "and sales tax, sales tax on parking and daytime beverages, property "
        "tax, employer payroll). Those are ordinary operating expenses and "
        "are **already deducted inside the NOI figure below** — see the "
        "Owner Summary tab's Variable Operating Costs table for that side."
    )

    st.markdown("---")
    st.subheader("NOI Basis")
    noi_source = st.radio(
        "Run the analysis on:",
        ["Current Dashboard Inputs", "Base Case", "Conservative", "Custom"],
        horizontal=True,
    )
    if noi_source == "Current Dashboard Inputs":
        tax_noi = annual["total_noi"]
        st.metric("Year 1 NOI (pre-tax, sidebar inputs)", fmt_dollar(tax_noi))
    elif noi_source == "Custom":
        tax_noi = st.slider("Annual NOI (pre-tax, $)", 0, 400_000,
                            int(annual["total_noi"]), step=5_000, format="$%d")
    else:
        _, scen_ann = model.run_scenario_projection(model.SCENARIOS[noi_source])
        tax_noi = scen_ann["total_noi"]
        st.metric(f"{noi_source} Year 1 NOI (pre-tax)", fmt_dollar(tax_noi))

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
    st.caption("Default reflects a part-time oversight role — the on-site "
               "manager (free housing in exchange for day-to-day ops) and "
               "bartender (see Owner Summary) handle the actual labor. A "
               "CPA reasonable-compensation study should confirm this "
               "number before electing S-corp status.")

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
    st.caption("Leanest concept on the Del Valle land: food truck park + a "
               "bar & beverage stand, financed via a personal line of "
               "credit — no RV park, no bank term loan")

    st.markdown(
        f"""
        This model strips the food-truck-+-RV-park concept down further:
        contracted monthly rent from food truck tenants forms a stable base,
        the evening bar adds beer and single-serve liquor shot sales, the
        all-day stand adds soda/juice/water/coffee, and COTA event weekends
        layer parking and bar upside on top. The
        \\${model.TOTAL_PROJECT_COST:,.0f} buildout (itemized from the owner's
        real Phase 0.5 cost tracker) is financed through a personal line of
        credit at {model.LOC_INTEREST_RATE:.1%} rather than a bank term loan — revolving,
        interest-only, no fixed amortization schedule. The model tracks the
        **monthly operating nut** (which includes the LOC's interest-only
        carrying cost) and **FCF yield on total cost** instead of a lender's
        DSCR covenant, plus a dedicated LOC payoff schedule.
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
                            yr=2)
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
             f"6pm-close only, ${model.BEER_PRICE:.0f} beer + ${model.SHOT_PRICE:.0f} "
             f"shots in plastic shot glasses (no cocktails, no mixed drinks): "
             f"{model.BAR_WEEKDAY_CUSTOMERS} weekday / {model.BAR_WEEKEND_CUSTOMERS} "
             f"weekend customers/evening averaging {model.DRINKS_PER_VISIT} drinks "
             f"(~${model.BAR_AVG_CHECK:.2f} check)",
             _mo("total_bar"),
             f"~{_alcohol_margin:.0%} after COGS + both mixed beverage taxes"),
            ("3. Daytime Beverages",
             f"All-day (~11am-close) soda/juice/water/coffee, sized off implied "
             f"food-truck customer traffic ({model.DAYTIME_BEVERAGE_ATTACH_RATE:.0%} "
             f"attach rate x ${model.DAYTIME_BEVERAGE_AVG_PRICE:.2f} avg price) - "
             "same on-site bartender, no new fixed labor. Requires vendor leases "
             "restricting trucks to food-only (specialty drinks OK) so demand "
             "doesn't leak to truck-sold drinks",
             _mo("total_daytime_beverage"),
             f"~{1 - model.DAYTIME_BEVERAGE_VARIABLE_COST_RATE:.0%} after COGS + sales tax"),
            ("4. COTA Events",
             f"{model.EVENT_PARKING_SPACES}-space event parking (dedicated 3-acre "
             "lot), day-by-day occupancy building to the marquee day (F1: 45% Fri "
             "/ 75% Sat / 100% Sun) + uplift on the bar and daytime beverages, "
             f"with the bar at premium event pricing "
             f"(${model.COTA_EVENT_BEER_PRICE:.0f} beer / "
             f"${model.COTA_EVENT_SHOT_PRICE:.0f} shot)",
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
            "shrinkage, and the bartender's revenue share."
        )

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
             f"{model.GRT_RATE:.1%} of alcohol sales",
             "Permittee's own liability — cannot be added to the menu price"),
            ("Mixed Beverage Sales Tax",
             f"{model.MB_SALES_TAX_RATE:.2%} of alcohol sales",
             "A second, separate tax. Under an MB permit it hits every "
             "alcoholic drink including canned beer. Model assumes "
             "tax-inclusive menu pricing (the conservative read)"),
            ("Sales tax — daytime beverages",
             f"{model.DAYTIME_BEVERAGE_SALES_TAX_RATE:.2%}",
             "Standard Del Valle/Travis County rate — not alcohol, so no GRT"),
            ("Sales tax — event parking",
             f"{model.PARKING_SALES_TAX_RATE:.2%}",
             "Motor vehicle parking is an explicitly taxable service in TX "
             "(34 TAC 3.315)"),
            ("Property tax — land",
             fmt_dollar(model.FIXED_COSTS['property_tax'] * 12) + "/yr",
             "Actual bill; county assesses the land at "
             f"{fmt_dollar(model.LAND_ASSESSED_VALUE)}"),
            ("Property tax — improvements",
             f"{model.PROPERTY_TAX_IMPROVEMENT_RATE:.1%} of buildout "
             f"({fmt_dollar(model.FIXED_COSTS['property_tax_improvements'] * 12)}/yr)",
             "The buildout joins the tax roll once complete"),
            ("Employer payroll (FICA/FUTA/SUTA)",
             f"~{model.EMPLOYER_PAYROLL_BURDEN_RATE:.0%} of bartender comp",
             "Revenue-share pay doesn't avoid employer payroll tax for a "
             "W-2 employee"),
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
            "Permits are real money and were badly understated in earlier "
            "versions: a TABC **Mixed Beverage Permit is \\$5,300 for the first "
            "two years** (\\$2,650 at renewal), which is most of the permits "
            "line in Use of Funds. Confirm all of the above with a "
            "TABC-savvy CPA before filing."
        )

    with st.expander("4. What Changed vs. the Food Truck + RV Park Model"):
        st.markdown(
            r"""
            | | Food Truck + RV Park | Food Truck Park (this model) |
            |---|---|---|
            | Capital | \$300,000 SBA 7(a) term loan | \$81,600 personal LOC |
            | Rate / structure | 10.5%, 10-yr amortizing | 12.5%, revolving interest-only |
            | Financing cost | ~\$4,050/mo fixed P&I | ~\$850/mo interest (conservative; declines as paid down) |
            | Monthly nut | ~\$15,200 | ~\$5,200 |
            | RV pad rent | ~\$16-18K/mo | Removed entirely |
            | Truck count | 6 slots, ramps up | 4 hubs, leasing up over Year 1 (no more budgeted) |
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
model.run_loc_payoff_schedule()     # declining-balance LOC payoff vs. the flat nut
model.run_tax_strategy_analysis()   # depreciation + Sec 195 + S-corp election
model.print_tax_strategy_analysis() # same, printed (CLI)
model.print_owner_summary()         # full owner-facing report (CLI)

# Regression tests — run after ANY change to the calculation engine:
#   pytest -q
            """,
            language="python",
        )
