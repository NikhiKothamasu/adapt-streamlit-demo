from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Northstar Analytics",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

COLORS = {
    "ink": "#172121",
    "muted": "#66706f",
    "paper": "#f5f1e8",
    "surface": "#fffdf8",
    "teal": "#087f7a",
    "coral": "#e8664a",
    "gold": "#d4a72c",
    "blue": "#3c6e9f",
}

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,600&display=swap');
    :root { --paper: #f5f1e8; --ink: #172121; --teal: #087f7a; --coral: #e8664a; }
    .stApp { background: var(--paper); color: var(--ink); font-family: 'DM Sans', sans-serif; }
    h1, h2, h3 { font-family: 'Newsreader', serif !important; letter-spacing: 0 !important; }
    h1 { font-size: clamp(2.2rem, 5vw, 4.8rem) !important; line-height: .95 !important; }
    [data-testid="stHeader"] { background: rgba(245, 241, 232, .88); }
    [data-testid="stMetric"] { background: #fffdf8; border: 1px solid #ded8cc; border-radius: 6px; padding: 1rem; }
    [data-testid="stMetricValue"] { font-family: 'Newsreader', serif; color: var(--ink); }
    [data-testid="stMetricDelta"] svg { display: none; }
    .stPlotlyChart { background: #fffdf8; border: 1px solid #ded8cc; border-radius: 6px; padding: .4rem; }
    div[data-testid="stDataFrame"] { border: 1px solid #ded8cc; border-radius: 6px; overflow: hidden; }
    .eyebrow { color: var(--teal); font-size: .75rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
    .hero-copy { color: #586261; font-size: 1.05rem; max-width: 45rem; margin: -.5rem 0 1.5rem; }
    .section-rule { border: 0; border-top: 1px solid #d7d0c4; margin: 1.5rem 0; }
    .signal { background: #172121; color: #fffdf8; padding: 1rem 1.2rem; border-radius: 6px; min-height: 6.5rem; }
    .signal strong { color: #e9b949; }
    button[kind="pillsActive"] { background: var(--teal) !important; }
    @media (max-width: 700px) {
      h1 { font-size: 2.7rem !important; }
      .block-container { padding-left: 1rem; padding-right: 1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def build_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(27)
    dates = pd.date_range("2024-01-01", date.today(), freq="D")
    regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
    channels = ["Enterprise", "Self-serve", "Partners"]
    products = ["Core", "Flow", "Pulse"]
    rows: list[dict[str, object]] = []

    for index, day in enumerate(dates):
        seasonal = 1 + 0.14 * np.sin(index * 2 * np.pi / 30) + 0.08 * np.sin(index * 2 * np.pi / 365)
        trend = 1 + index / max(len(dates), 1) * 0.34
        for region_index, region in enumerate(regions):
            orders = max(12, int(rng.normal(72 + region_index * 9, 11) * seasonal * trend))
            average_order = rng.normal(168 - region_index * 7, 15)
            revenue = orders * average_order
            if rng.random() < 0.012:
                revenue *= rng.choice([0.52, 1.65])
            rows.append(
                {
                    "date": day,
                    "region": region,
                    "channel": rng.choice(channels, p=[0.38, 0.42, 0.20]),
                    "product": rng.choice(products, p=[0.48, 0.30, 0.22]),
                    "orders": orders,
                    "revenue": round(revenue, 2),
                    "customers": max(8, int(orders * rng.uniform(0.68, 0.92))),
                    "conversion": rng.uniform(0.021, 0.067),
                    "satisfaction": np.clip(rng.normal(4.28, 0.24), 3.2, 4.9),
                }
            )

    frame = pd.DataFrame(rows)
    frame["margin"] = frame["revenue"] * rng.uniform(0.54, 0.72, len(frame))
    return frame


def chart_style(figure: go.Figure, height: int = 390) -> go.Figure:
    figure.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=48, b=18),
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font=dict(family="DM Sans", color=COLORS["ink"]),
        title_font=dict(family="Newsreader", size=22),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor=COLORS["ink"], font_color="white"),
    )
    figure.update_xaxes(showgrid=False, linecolor="#d8d1c5")
    figure.update_yaxes(gridcolor="#e7e1d7", zeroline=False)
    return figure


def page_header(kicker: str, title: str, summary: str) -> None:
    st.markdown(f'<div class="eyebrow">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="hero-copy">{summary}</p>', unsafe_allow_html=True)


DATA = build_dataset()


def global_filters(frame: pd.DataFrame) -> pd.DataFrame:
    with st.popover("Filters", width="content"):
        minimum = frame["date"].min().date()
        maximum = frame["date"].max().date()
        selected_dates = st.date_input("Date range", (maximum - pd.Timedelta(days=179), maximum), minimum, maximum)
        selected_regions = st.multiselect("Regions", sorted(frame["region"].unique()), default=sorted(frame["region"].unique()))
        selected_channels = st.multiselect("Channels", sorted(frame["channel"].unique()), default=sorted(frame["channel"].unique()))

    if len(selected_dates) != 2:
        return frame.iloc[0:0]
    start, end = pd.Timestamp(selected_dates[0]), pd.Timestamp(selected_dates[1])
    return frame[
        frame["date"].between(start, end)
        & frame["region"].isin(selected_regions)
        & frame["channel"].isin(selected_channels)
    ]


def overview() -> None:
    page_header("Executive intelligence", "The whole business, at a glance.", "Live performance signals across revenue, customers, margin, and conversion.")
    filtered = global_filters(DATA)
    if filtered.empty:
        st.warning("Select at least one region and channel, plus a complete date range.")
        return

    current_end = filtered["date"].max()
    split = current_end - pd.Timedelta(days=29)
    current = filtered[filtered["date"] > split]
    previous = filtered[(filtered["date"] <= split) & (filtered["date"] > split - pd.Timedelta(days=30))]

    def change(column: str) -> float:
        old = previous[column].sum()
        return 0.0 if old == 0 else (current[column].sum() / old - 1) * 100

    metrics = st.columns(4)
    metrics[0].metric("Revenue", f"${filtered['revenue'].sum() / 1_000_000:.2f}M", f"{change('revenue'):+.1f}% vs prior 30d", border=True)
    metrics[1].metric("Gross margin", f"{filtered['margin'].sum() / filtered['revenue'].sum():.1%}", "Portfolio weighted", border=True)
    metrics[2].metric("Customers", f"{filtered['customers'].sum():,.0f}", f"{change('customers'):+.1f}% vs prior 30d", border=True)
    metrics[3].metric("Conversion", f"{filtered['conversion'].mean():.2%}", f"CSAT {filtered['satisfaction'].mean():.2f} / 5", border=True)

    daily = filtered.groupby("date", as_index=False).agg(revenue=("revenue", "sum"), margin=("margin", "sum"))
    daily["Revenue · 14d average"] = daily["revenue"].rolling(14, min_periods=1).mean()
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=daily["date"], y=daily["revenue"], name="Daily revenue", line=dict(color="#a9b9b6", width=1)))
    figure.add_trace(go.Scatter(x=daily["date"], y=daily["Revenue · 14d average"], name="14-day signal", line=dict(color=COLORS["teal"], width=3)))
    figure.update_layout(title="Revenue velocity")
    figure.update_yaxes(tickprefix="$", tickformat="~s")
    st.plotly_chart(chart_style(figure, 420), alt="Daily revenue with a smoothed 14-day trend")

    left, right = st.columns([1.55, 1])
    regional = filtered.groupby("region", as_index=False)[["revenue", "margin"]].sum().sort_values("revenue")
    regional_figure = px.bar(regional, x="revenue", y="region", orientation="h", color="region", color_discrete_sequence=[COLORS["teal"], COLORS["coral"], COLORS["gold"], COLORS["blue"]], title="Regional contribution")
    regional_figure.update_layout(showlegend=False)
    regional_figure.update_xaxes(tickprefix="$", tickformat="~s")
    left.plotly_chart(chart_style(regional_figure, 350), alt="Revenue contribution by region")

    best = regional.iloc[-1]
    margin_rate = filtered["margin"].sum() / filtered["revenue"].sum()
    right.markdown(
        f"""<div class="signal"><span class="eyebrow" style="color:#8fd0c9">Decision signal</span><br>
        <strong>{best['region']}</strong> leads revenue contribution. Portfolio margin is <strong>{margin_rate:.1%}</strong>; prioritize channels above that threshold.</div>""",
        unsafe_allow_html=True,
    )
    mix = filtered.groupby("channel", as_index=False)["revenue"].sum()
    mix_figure = px.pie(mix, values="revenue", names="channel", hole=.68, color_discrete_sequence=[COLORS["teal"], COLORS["coral"], COLORS["gold"]], title="Channel mix")
    right.plotly_chart(chart_style(mix_figure, 235), alt="Revenue share across sales channels")


def trends() -> None:
    page_header("Predictive view", "Momentum, forecast, and exceptions.", "Separate structural growth from noise and surface days that deserve investigation.")
    filtered = global_filters(DATA)
    if filtered.empty:
        st.warning("Adjust the filters to include data.")
        return

    daily = filtered.groupby("date", as_index=False)["revenue"].sum().sort_values("date")
    daily["baseline"] = daily["revenue"].rolling(21, center=True, min_periods=7).median()
    residual = daily["revenue"] - daily["baseline"]
    deviation = residual.std() or 1
    daily["z_score"] = residual / deviation
    daily["anomaly"] = daily["z_score"].abs() >= 2.25

    horizon = st.segmented_control("Forecast horizon", ["30 days", "60 days", "90 days"], default="60 days")
    forecast_days = int((horizon or "60 days").split()[0])
    training = daily.tail(min(180, len(daily))).copy()
    x_values = np.arange(len(training))
    slope, intercept = np.polyfit(x_values, training["revenue"], 1)
    future_dates = pd.date_range(daily["date"].max() + pd.Timedelta(days=1), periods=forecast_days)
    future_x = np.arange(len(training), len(training) + forecast_days)
    prediction = intercept + slope * future_x
    uncertainty = residual.tail(180).std() * np.sqrt(1 + future_x / max(len(training), 1))

    figure = go.Figure()
    figure.add_trace(go.Scatter(x=daily["date"], y=daily["revenue"], name="Actual", line=dict(color=COLORS["ink"], width=1.5)))
    figure.add_trace(go.Scatter(x=future_dates, y=prediction + 1.64 * uncertainty, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    figure.add_trace(go.Scatter(x=future_dates, y=prediction - 1.64 * uncertainty, fill="tonexty", fillcolor="rgba(8,127,122,.16)", line=dict(width=0), name="90% interval"))
    figure.add_trace(go.Scatter(x=future_dates, y=prediction, name="Trend forecast", line=dict(color=COLORS["teal"], width=3, dash="dash")))
    anomalies = daily[daily["anomaly"]]
    figure.add_trace(go.Scatter(x=anomalies["date"], y=anomalies["revenue"], mode="markers", name="Anomaly", marker=dict(color=COLORS["coral"], size=10, symbol="diamond")))
    figure.update_layout(title="Revenue outlook and detected anomalies")
    figure.update_yaxes(tickprefix="$", tickformat="~s")
    st.plotly_chart(chart_style(figure, 470), alt="Revenue forecast, uncertainty interval, and anomalous days")

    col1, col2, col3 = st.columns(3)
    col1.metric("Daily forecast", f"${prediction[-1]:,.0f}", f"{slope:+,.0f} / day trend")
    col2.metric("Exceptions", f"{len(anomalies)}", f"{len(anomalies) / len(daily):.1%} of observed days")
    col3.metric("Forecast range", f"±${1.64 * uncertainty[-1]:,.0f}", "90% model interval")


def segments() -> None:
    page_header("Portfolio lens", "Find the growth pockets.", "Compare product, region, and channel combinations by scale, efficiency, and customer quality.")
    filtered = global_filters(DATA)
    if filtered.empty:
        st.warning("Adjust the filters to include data.")
        return

    grouped = filtered.groupby(["region", "channel", "product"], as_index=False).agg(
        revenue=("revenue", "sum"), margin=("margin", "sum"), customers=("customers", "sum"), satisfaction=("satisfaction", "mean")
    )
    grouped["margin_rate"] = grouped["margin"] / grouped["revenue"]
    grouped["revenue_per_customer"] = grouped["revenue"] / grouped["customers"]
    figure = px.scatter(
        grouped, x="revenue_per_customer", y="margin_rate", size="revenue", color="region", symbol="product",
        hover_data=["channel", "product", "revenue"], size_max=52,
        color_discrete_sequence=[COLORS["teal"], COLORS["coral"], COLORS["gold"], COLORS["blue"]],
        title="Segment opportunity map",
    )
    figure.update_xaxes(title="Revenue per customer", tickprefix="$", tickformat=",.0f")
    figure.update_yaxes(title="Margin rate", tickformat=".0%")
    st.plotly_chart(chart_style(figure, 490), alt="Business segments compared by revenue per customer and margin rate")

    dimension = st.segmented_control("Rank by", ["Region", "Channel", "Product"], default="Product") or "Product"
    summary = filtered.groupby(dimension.lower(), as_index=False).agg(revenue=("revenue", "sum"), margin=("margin", "sum"), customers=("customers", "sum"))
    summary["margin rate"] = summary["margin"] / summary["revenue"]
    summary["revenue / customer"] = summary["revenue"] / summary["customers"]
    st.dataframe(summary.sort_values("revenue", ascending=False), hide_index=True, alt=f"Performance ranked by {dimension.lower()}", column_config={"revenue": st.column_config.NumberColumn(format="$%.0f"), "margin": st.column_config.NumberColumn(format="$%.0f"), "margin rate": st.column_config.NumberColumn(format="percent"), "revenue / customer": st.column_config.NumberColumn(format="$%.2f")})


def data_lab() -> None:
    page_header("Analyst workspace", "Explore the evidence.", "Slice the underlying observations, inspect distributions, and export the exact working set.")
    filtered = global_filters(DATA)
    if filtered.empty:
        st.warning("Adjust the filters to include data.")
        return

    metric = st.selectbox("Distribution metric", ["revenue", "orders", "conversion", "satisfaction", "margin"], index=0)
    left, right = st.columns([1.45, 1])
    histogram = px.histogram(filtered, x=metric, color="channel", marginal="box", nbins=42, color_discrete_sequence=[COLORS["teal"], COLORS["coral"], COLORS["gold"]], title=f"{metric.title()} distribution")
    left.plotly_chart(chart_style(histogram, 390), alt=f"Distribution of {metric} split by sales channel")
    correlation_columns = ["revenue", "orders", "customers", "conversion", "satisfaction", "margin"]
    correlation = filtered[correlation_columns].corr()
    heatmap = px.imshow(correlation, text_auto=".2f", color_continuous_scale=[[0, COLORS["coral"]], [.5, COLORS["paper"]], [1, COLORS["teal"]]], zmin=-1, zmax=1, title="Signal correlation")
    right.plotly_chart(chart_style(heatmap, 390), alt="Correlation among revenue, orders, customers, conversion, satisfaction, and margin")

    st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
    st.subheader("Working dataset")
    st.dataframe(filtered.sort_values("date", ascending=False), hide_index=True, alt="Filtered business observations available for export")
    st.download_button("Download filtered CSV", filtered.to_csv(index=False).encode("utf-8"), "northstar_filtered.csv", "text/csv", width="stretch")


pages = [
    st.Page(overview, title="Overview", icon=":material/space_dashboard:", default=True),
    st.Page(trends, title="Trends & Forecast", icon=":material/query_stats:"),
    st.Page(segments, title="Segments", icon=":material/hub:"),
    st.Page(data_lab, title="Data Lab", icon=":material/science:"),
]

navigation = st.navigation(pages, position="top")
navigation.run()