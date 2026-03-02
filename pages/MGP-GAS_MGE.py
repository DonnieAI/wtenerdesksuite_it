import streamlit as st
import pandas as pd
from pathlib import Path
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import importlib
from markdown import markdown

st.set_page_config(page_title="Dashboard", layout="wide")
from utils import apply_style_and_logo
from supporting_functions.editing_function import styled_scrollable_markdown
#import supporting_functions.lxml_read_functions as lxml_funcs

apply_style_and_logo()

palette_blue = [
    "#A7D5F2",  # light blue
    "#94CCE8",
    "#81C3DD",
    "#6FBBD3",
    "#5DB2C8",
    "#A9DEF9",  # baby blue
]

palette_green = [
    "#6DC0B8",  # pastel teal
    "#7DCFA8",
    "#8DDC99",
    "#9CE98A",
    "#ABF67B",
    "#C9F9D3",  # mint green
    "#C4E17F",  # lime green
]

palette_other = [
    "#FFD7BA",  # pastel orange
    "#FFE29A",  # pastel yellow
    "#FFB6C1",  # pastel pink
    "#D7BDE2",  # pastel purple
    "#F6C6EA",  # light rose
    "#F7D794",  # peach
    "#E4C1F9",  # lavender
]


#----LOAD DATA
#return time sereies from 2027 to Sept 2025
# these are gas price from GSE related to MG market EUR/MWh
df_at_hist = pd.read_parquet(r"mgp_gas_data\history\gse_gas_mg.parquet")
# ensure it's a DatetimeIndex
df_at_hist.index = pd.to_datetime(df_at_hist.index)
# make it a Series (optional, but convenient)
ts_at_hist = df_at_hist["MG_PRICE"].sort_index()


df_at_2025_2026 = pd.read_csv(
    r"mgp_gas_data\live\Annotermico_2025-2026.csv",
    usecols=["DAY", "MG_PRICE"],   # ignore those trailing empty columns
    dtype={"DAY": "string"}
)
df_at_2025_2026["DAY"] = pd.to_datetime(
    df_at_2025_2026["DAY"].str.strip(),
    format="%Y%m%d",
    errors="coerce"
)

ts_at_2025_2026 = (
    df_at_2025_2026
    .dropna(subset=["DAY"])
    .set_index("DAY")["MG_PRICE"]
    .sort_index()
)

#ts_all = pd.concat([ts_at_hist, ts_at_2025_2026]).sort_index()
mpg_gas_daily_ts=pd.concat([ts_at_hist, ts_at_2025_2026]).sort_index()


#------DATA FOR THE FIG2
mpg_gas_monthly_ts = mpg_gas_daily_ts.resample("MS").mean()
mpg_gas_monthly_mom_ts = mpg_gas_monthly_ts.pct_change(1, fill_method=None) * 100



#----DATA FOR FIG BOXPLOT
#monthly_pun_hourly_ts = pun_hourly_ts.resample("MS").mean()
df_plot_3 = mpg_gas_monthly_ts.to_frame("pun").loc["2008":"2025"].copy()
df_plot_3["Year"] = df_plot_3.index.year
years = sorted(df_plot_3["Year"].unique())



#------------------------------------------
st.title("🔥MGP-GAS GME – 🇮🇹 Italian day gas price")
st.caption("Source: GME , elaboration by Wavetransition")


# --- Narrative at the top of the page ---

md_text = open("narratives/MGP-GAS_GME.md", "r", encoding="utf-8").read()
styled_scrollable_markdown(md_text, height_rem=15)

#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------
st.subheader("📈 Dynamic Hystorical Trend Visualization")

# ---- Date limits from your TS ----
min_dt = mpg_gas_daily_ts.index.min()
max_dt = mpg_gas_daily_ts.index.max()

if st.button("Reload data"):
    st.cache_data.clear()
    st.rerun()
preset = st.selectbox(
            "Quick range",
            ["Past Day", "Past Week", "Past Month","Past Year", "All", "Custom"],
            index=2,  # default Past Year
        )

if preset == "Past Day":
    start = max_dt - pd.Timedelta(days=1)
    end = max_dt

elif preset == "Past Week":
    start = max_dt - pd.Timedelta(days=7)
    end = max_dt

elif preset == "Past Month":
    start = max_dt - pd.Timedelta(days=30)
    end = max_dt

elif preset == "Past Year":
    start = max_dt - pd.Timedelta(days=365)
    end = max_dt

elif preset == "All":
    start, end = min_dt, max_dt
    
else:  # Custom
    default_start = max_dt - pd.Timedelta(days=365)
    if default_start < min_dt:
        default_start = min_dt

    start_date, end_date = st.date_input(
        "Select period",
        value=(default_start.date(), max_dt.date()),
        min_value=min_dt.date(),
        max_value=max_dt.date(),
    )

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    if end < start:
        st.warning("End date is earlier than start date. Swapping them.")
        start, end = end, start

# clamp to data availability (important for presets)
start = max(start, min_dt)
end = min(end, max_dt)

# ---- Slice once (only once) ----
ts_sel = mpg_gas_daily_ts.loc[start:end]

# ---- Optional auto-resample (for performance) ----
days = (end - start) / pd.Timedelta(days=1)

if days <= 3:
    ts_plot = ts_sel
elif days <= 90:
    ts_plot = ts_sel.resample("D").mean()
elif days <= 365 * 3:
    ts_plot = ts_sel.resample("W").mean()
else:
    ts_plot = ts_sel.resample("MS").mean()
    
if days <= 3:
    freq_label = "Hourly (raw)"
elif days <= 90:
    freq_label = "Daily mean"
elif days <= 365 * 3:
    freq_label = "Weekly mean"
else:
    freq_label = "Monthly mean"



# ---- Build Plotly Figure directly ----
fig1 = go.Figure()

fig1.add_trace(
        go.Scatter(
            x=ts_plot.index,
            y=ts_plot.values,
            mode="lines",
            name="MGP-GAS GME [EUR/MWh]",
            line=dict(color=palette_blue[3], width=4),
            fill="tozeroy",                     # 👈 fills area to x-axis
            fillcolor="rgba(31,119,180,0.25)"  , 
            opacity=0.1,# 👈 area color
            hovertemplate="%{x|%Y-%m-%d %H:%M}<br>PUN=%{y:.2f}<extra></extra>",
        )
    )

fig1.update_layout(
            title="PMGP-GAS GME  [EUR/MWh]",
            xaxis_title="Time",
            yaxis_title="Price",
            hovermode="x unified",
            margin=dict(l=10, r=10, t=40, b=10),
)

fig1.update_xaxes(
            rangeslider=dict(visible=True),
            type="date"
)

st.plotly_chart(fig1, use_container_width=True)

st.caption(f"Aggregation shown: {freq_label} | Raw points: {len(ts_sel):,} | Displayed: {len(ts_plot):,}")



#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------
st.subheader("📈 Static Hystorical Trend Visualization - Monthly")

fig2 = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.12,
    row_heights=[0.7, 0.3],
    subplot_titles=(
        "Gas Price [EUR/MWh]",
        "YoY variation [%]"
    )
)

# --- Row 1: Price bars
fig2.add_trace(
    go.Bar(
        x=mpg_gas_monthly_ts.index,
        y=mpg_gas_monthly_ts.values,
        name="MGP-GAS [EUR/MWh]",
        marker=dict(color=palette_blue[3]),
        opacity=0.85,
        #hovertemplate="%{x|%b %Y}<br>GAS=%{y:.2f} EUR/MWh<extra></extra>",
    ),
    row=1,
    col=1
)

# --- Row 2: YoY bars (green up, red down)
yoy_vals = mpg_gas_monthly_mom_ts.values
fig2.add_trace(
    go.Bar(
        x=mpg_gas_monthly_mom_ts.index,
        y=yoy_vals,
        name="YoY Change [%]",
        marker_color=[
            "#F5B7B1" if (v is not None and v < 0) else "#A9DFBF"
            for v in yoy_vals
        ],
        hovertemplate="%{x|%b %Y}<br>YoY=%{y:.2f}%<extra></extra>",
    ),
    row=2,
    col=1
)

fig2.update_layout(
    title="MGP-GAS GME [EUR/MWh]",
   # hovermode="x unified",
    margin=dict(l=10, r=10, t=40, b=10),
    bargap=0.15,
)

fig2.update_yaxes(title_text="Price", row=1, col=1, autorange=True, fixedrange=False)
fig2.update_yaxes(title_text="YoY [%]", row=2, col=1, autorange=True, fixedrange=False)

fig2.update_xaxes(
    type="date",
    #rangeslider=dict(visible=True),
    tickformat="%b %Y",
)

st.plotly_chart(fig2, use_container_width=True)


#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------
st.subheader("📊 Boxplot of Monthly MGP-GAS Prices by Year")

# --- build figure ---
fig3 = go.Figure()

for i, y in enumerate(years):
    vals = df_plot_3.loc[df_plot_3["Year"] == y, "pun"].dropna()
    color = palette_other[i % len(palette_other)]

    fig3.add_trace(
        go.Box(
            y=vals,
            name=str(y),
            boxpoints=False,     
            width=0.6,                 # 👈 wider boxes
            line=dict(width=1.5),
            marker=dict(size=4),# no points (clean)
            marker_color=color,          # 👈 fill color
            # IMPORTANT: Plotly whiskers are not percentile-based like matplotlib.
            # We'll mimic 0.5%–99.5% by hiding points and relying on box spread,
            # OR use custom stats (see note below).
        )
    )

fig2.update_layout(
            title="Monthly Day-Ahead Electricity Prices (2015–2025)",
            yaxis_title="Price (PUN)",
            xaxis_title="Year",
            template="plotly_white",
            boxmode="group",
            height=450,
            margin=dict(l=40, r=20, t=60, b=40),
)


st.plotly_chart(fig3, use_container_width=True)

#styled_scrollable_markdown(narrative_graph1, height_rem=20)

pun_box_text = open("narratives/PRICE_BOX_PLOT.md", "r", encoding="utf-8").read()
styled_scrollable_markdown(pun_box_text, height_rem=20)