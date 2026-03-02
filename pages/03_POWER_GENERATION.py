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

color_map = {
    "Hydro": palette_blue[3],            # medium blue
    "Wind": palette_green[0],            # pastel teal
    "Photovoltaic": palette_other[1],    # pastel yellow
    "Thermal": palette_other[0],         # pastel orange
    "Geothermal": palette_other[3],      # pastel purple
    "Self-consumption": palette_green[5] # mint green
}

#DATA ELEBORATION
# upload historical data 2021-2025
df_hist=pd.read_parquet(r"terna_data\historical\terna_all.parquet")

#upload the recent 2026 data
df_2026 = pd.read_csv(r"terna_data\live\terna_gen_2026.csv")
df_2026["Date"] = pd.to_datetime(
                            df_2026["Date"],
                            dayfirst=True,
                            errors="coerce"
                        )
df_2026 = df_2026[df_2026["Date"].notna()]   # remove bad rows
df_2026 = df_2026.set_index("Date")
df_2026 = df_2026.sort_index()

# this is in the long format
df_long=pd.concat([df_hist,df_2026])
df_wide=df_long.pivot_table(
            values="Actual Generation",
            index=df_long.index,
            columns="Primary Source",
            aggfunc="sum"
        ).sort_index()   

# monthly 
df_monthly = df_wide.resample("MS").mean()
    # Hours in each month (difference between month start and next month start)
hours_in_month = (
        df_monthly.index.to_series()
        .apply(lambda d: (d + pd.offsets.MonthBegin(1)) - d)  # next month start - this month start
        .dt.total_seconds()
        .div(3600.0)
    )

# Multiply each row by that month's hours
df_monthly_gwh = df_monthly.mul(hours_in_month, axis=0).astype(int)

#------------------------------------------
st.title("⚡ – 🇮🇹 Power Generation by Source (excl Import)")
st.caption("Source: TERNA , elaboration by Wavetransition")

#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------
st.subheader("📈 Dynamic Hystorical Trend Visualization")

energy_cols = [col for col in df_monthly.columns if col != "Total"]
# Mean monthly value per source
avg_values = df_monthly[energy_cols].mean()

# Sort descending (largest first)
sorted_cols = avg_values.sort_values(ascending=False).index.tolist()
fig1 = go.Figure()
for col in sorted_cols:
        fig1.add_trace(
            go.Bar(
                x=df_monthly.index,
                y=df_monthly[col],
                name=col,
                marker_color=color_map.get(col, "#CCCCCC")
            )
        )
fig1.update_layout(
        barmode="stack",
        title="Monthly Energy Generation by Source",
        xaxis_title="Month",
        yaxis_title="Energy (GWh)",
        template="plotly_white",
        legend_title="Source"
    )
st.plotly_chart(fig1, use_container_width=True)