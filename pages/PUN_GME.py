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

#import supporting_functions.lxml_read_functions as lxml_funcs

# Force reload (development only)
#importlib.reload(lxml_funcs)


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



#LOAD DATA
HISTORY_DIR = Path("pun_parquet/history")
LIVE_2026 = Path("pun_parquet/live/pun_2026.parquet")

def dir_mtime_key(folder: Path, pattern: str) -> float:
    files = list(folder.glob(pattern))
    if not files:
        return 0.0
    return max(f.stat().st_mtime for f in files)

def file_mtime_key(path: Path) -> float:
    return path.stat().st_mtime if path.exists() else 0.0

@st.cache_data(show_spinner=False)
def load_history(_key: float) -> pd.Series:
    files = sorted(HISTORY_DIR.glob("pun_*.parquet"))
    dfs = [pd.read_parquet(p) for p in files]
    df = pd.concat(dfs, ignore_index=True)
    # Make absolutely sure datetime is datetime64
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"]).sort_values("datetime")
    ts = pd.Series(df["pun"].to_numpy(), index=df["datetime"], name="pun").sort_index()
    if not ts.index.is_unique:
        ts = ts.groupby(level=0).mean().sort_index()
    return ts

@st.cache_data(show_spinner=False)
def load_live_2026(_key: float) -> pd.Series:
    if not LIVE_2026.exists():
        return pd.Series(dtype="float64", name="pun")

    df = pd.read_parquet(LIVE_2026)

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.dropna(subset=["datetime"]).sort_values("datetime")
        ts = pd.Series(df["pun"].to_numpy(), index=df["datetime"], name="pun")
    else:
        ts = df["pun"]
        ts.name = "pun"
        ts = ts.sort_index()

    if not ts.index.is_unique:
        ts = ts.groupby(level=0).mean().sort_index()

    return ts

history_ts = load_history(dir_mtime_key(HISTORY_DIR, "pun_*.parquet"))
live_ts = load_live_2026(file_mtime_key(LIVE_2026))

pun_hourly_ts = pd.concat([history_ts, live_ts]).sort_index()
pun_hourly_ts.to_csv("pun_hourly_data.csv")


pun_monthly_ts=pun_hourly_ts.resample("MS").mean()

#------------------------------------------
st.title("⚡ PUN – 🇮🇹 Italian Day-Ahead Electricity Market")
st.caption("Source: GME , elaboration by Wavetransition")

#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------
# --- Narrative at the top of the page ---

md_text = open("narratives/PUN.md", "r", encoding="utf-8").read()
styled_scrollable_markdown(md_text, height_rem=15)

#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------
st.subheader("📈 Dynamic Hystorical Trend Visualization")

# ---- Date limits from your TS ----
min_dt = pun_hourly_ts.index.min()
max_dt = pun_hourly_ts.index.max()

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
ts_sel = pun_hourly_ts.loc[start:end]


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


narrative_dynamic_explanation=f"""
The PUN [EUR/MWh] for the selection has been
- {start} 
- {end}

"""
# ---- Build Plotly Figure directly ----
fig = go.Figure()

fig.add_trace(
        go.Scatter(
            x=ts_plot.index,
            y=ts_plot.values,
            mode="lines",
            name="PUN [EUR/MWh]",
            line=dict(color=palette_blue[3], width=4),
            fill="tozeroy",                     # 👈 fills area to x-axis
            fillcolor="rgba(31,119,180,0.25)"  , 
            opacity=0.1,# 👈 area color
            hovertemplate="%{x|%Y-%m-%d %H:%M}<br>PUN=%{y:.2f}<extra></extra>",
        )
    )

fig.update_layout(
            title="PUN Electricity Price [EUR/MWh]",
            xaxis_title="Time",
            yaxis_title="Price",
            hovermode="x unified",
            margin=dict(l=10, r=10, t=40, b=10),
)

fig.update_xaxes(
            rangeslider=dict(visible=True),
            type="date"
)

st.plotly_chart(fig, use_container_width=True)

st.caption(f"Aggregation shown: {freq_label} | Raw points: {len(ts_sel):,} | Displayed: {len(ts_plot):,}")


#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------
st.subheader("📊 Monthly Day-Ahead Electricity Prices Trend")


#pun_monthly_ts

fig3 = go.Figure()

fig3.add_trace(
        go.Scatter(
            x=pun_monthly_ts.index,
            y=pun_monthly_ts.values,
            mode="lines",
            name="MG-GAS [EUR/MWh]",
            line=dict(color=palette_blue[3], width=4),
            fill="tozeroy",                     # 👈 fills area to x-axis
            fillcolor="rgba(31,119,180,0.25)"  , 
            opacity=0.1,# 👈 area color
            hovertemplate="%{x|%Y-%m-%d %H:%M}<br>GAS=%{y:.2f}<extra></extra>",
        )
    )

fig3.update_layout(
    title="GAS Price [EUR/MWh]",
    xaxis_title="Time",
    yaxis_title="Price",
    hovermode="x unified",
    margin=dict(l=10, r=10, t=40, b=10),
    yaxis=dict(
        autorange=True,
        fixedrange=False
    )
)

fig3.update_xaxes(
    rangeslider=dict(visible=True),
    type="date"
)
fig3.update_xaxes(rangeslider_visible=True)
st.plotly_chart(fig3, use_container_width=True)








#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------
st.subheader("📊 Boxplot of Monthly Day-Ahead Electricity Prices by Year")

monthly_pun_hourly_ts = pun_hourly_ts.resample("MS").mean()
df_plot = monthly_pun_hourly_ts.to_frame("pun").loc["2008":"2025"].copy()
df_plot["Year"] = df_plot.index.year

years = sorted(df_plot["Year"].unique())

# --- build figure ---
fig2 = go.Figure()

for i, y in enumerate(years):
    vals = df_plot.loc[df_plot["Year"] == y, "pun"].dropna()
    color = palette_other[i % len(palette_other)]

    fig2.add_trace(
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


st.plotly_chart(fig2, use_container_width=True)

#styled_scrollable_markdown(narrative_graph1, height_rem=20)
pun_box_text = open("narratives/PRICE_BOX_PLOT.md", "r", encoding="utf-8").read()
styled_scrollable_markdown(pun_box_text, height_rem=20)
