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

with open("conversion_factors.json", "r", encoding="utf-8") as f:
    conv = json.load(f)

mj_per_smc = conv["natural_gas"]["conversion_factors"]["MJ_per_Smc"]


#------------------------------------------
st.title("🥛🇮🇹 Glass")
st.caption("Source:elaboration by Wavetransition")

#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------


c1,c2,c3  = st.columns(3)

with c1:
    st.subheader("Annual Production [t/y]")
    annual_production_t=st.number_input(
    "Annual Production [t/y]",
    value=109500,
    min_value=0,
    step=500,
    key="annual_production_t"
)

with c2:
    st.subheader("operating hours [h]")
    chp_hours=st.number_input(
        "operating hours [h]",
        value=7906,
        min_value=0,
        max_value=8760,
        step=10,
        key="operating hours [h]"
    )

with c3:
    st.subheader("electricity need covered by CHP [%]")
    chp_ee_share_pct = st.number_input(
        "CHP electricity share [%]",
        min_value=0,
        max_value=100,
        value=89,
        step=1,
        key="chp_electricity_share_pct"
    )



#annual_production_t = st.session_state["annual_production_t"]

#--------------------------------------------------------------------------------------------
st.divider()
#--------------------------------------------------------------------------------------------
st.header("⚙️ Consumption by process phase")
st.write("")
st.markdown(
    f"""
    <div style="display:flex; justify-content:center; align-items:center; gap:22px; margin:1.5rem 0; flex-wrap:wrap;">
        <div style="background:{palette_blue[0]}; color:#1f1f1f; padding:12px 22px; border-radius:8px; font-weight:600; min-width:120px; text-align:center;">Mixing</div>
        <div style="font-size:28px; font-weight:700; color:white; margin:0 8px;">→</div>
        <div style="background:{palette_blue[2]}; color:#1f1f1f; padding:12px 22px; border-radius:8px; font-weight:600; min-width:120px; text-align:center;">Melting</div>
        <div style="font-size:28px; font-weight:700; color:white; margin:0 8px;">→</div>
        <div style="background:{palette_green[1]}; color:#1f1f1f; padding:12px 22px; border-radius:8px; font-weight:600; min-width:120px; text-align:center;">Forming</div>
        <div style="font-size:28px; font-weight:700; color:white; margin:0 8px;">→</div>
        <div style="background:{palette_other[0]}; color:#1f1f1f; padding:12px 22px; border-radius:8px; font-weight:600; min-width:120px; text-align:center;">Finishing</div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")

h1, h2, h3 = st.columns([1.2, 2, 2])
h1.markdown("**Process Phase**")
h2.markdown("**Specific Thermal Consumption [GJ/t]**")
h3.markdown("**Specific Electrical Consumption [GJ/t]**")

r1c1, r1c2, r1c3 = st.columns([1.2, 2, 2])
r1c1.write("Mixing")
mixing_gas = r1c2.slider("mixing_gas", min_value=0.0, max_value=0.001, value=0.584, step=0.001, format="%.3f", key="mixing_gas")
mixing_ee = r1c3.slider("mixing_ee", min_value=0.0, max_value=0.001, value=0.136, step=0.001, format="%.3f", key="mixing_ee")

r2c1, r2c2, r2c3 = st.columns([1.2, 2, 2])
r2c1.write("Melting")
melting_gas = r2c2.slider("melting_gas", min_value=3.0, max_value=5.000, value=3.790, step=0.001, format="%.3f", key="melting_gas")
melting_ee = r2c3.slider("melting_ee", min_value=0.5, max_value=2.000, value=0.888, step=0.001, format="%.3f", key="melting_ee")

r3c1, r3c2, r3c3 = st.columns([1.2, 2, 2])
r3c1.write("Forming")
forming_gas = r3c2.slider("forming_gas", min_value=0.1, max_value=2.500, value=1.022, step=0.001, format="%.3f", key="forming_gas")
forming_ee = r3c3.slider("forming_ee", min_value=0.0, max_value=2.000, value=0.233, step=0.001, format="%.3f", key="forming_ee")

r4c1, r4c2, r4c3 = st.columns([1.2, 2, 2])
r4c1.write("Finishing")
finishing_gas = r4c2.slider("finishing_gas", min_value=0.0, max_value=2.000, value=0.584, step=0.001, format="%.3f", key="finishing_gas")
finishing_ee = r4c3.slider("finishing_ee", min_value=0.0, max_value=2.000, value=0.13, step=0.001, format="%.3f", key="finishing_ee")


#----------OVERRAIDING TEMP
#mixing_ee=0.594

# Summary table
st.write("")
summary_table = pd.DataFrame({
    "Process Phase": [
        "Mixing",
        "Melting",
        "Forming",
        "Finishing",
       
    ],
    "Total Gas [GJ/y]": [
        mixing_gas * annual_production_t,
        melting_gas * annual_production_t,
        forming_gas * annual_production_t,
        finishing_gas * annual_production_t,
        
    ],
    "Total Electricity [GJ/y]": [
        mixing_ee * annual_production_t,
        melting_ee * annual_production_t,
        forming_ee * annual_production_t,
        finishing_ee * annual_production_t,
       
    ]
})

total_gas_gj = summary_table["Total Gas [GJ/y]"].sum()
total_electricity_gj = summary_table["Total Electricity [GJ/y]"].sum()
total_energy_gj=total_gas_gj+total_electricity_gj
specific_energy_GJ_t=total_energy_gj/annual_production_t
#st.text(f"specific product energy is {specific_energy_GJ_t} GJ/t")
#st.metric("Specific product energy", f"{specific_energy_GJ_t:,.2f} GJ/t")
#st.markdown(f"**Specific product energy:** {specific_energy_GJ_t:,.2f} GJ/t")
st.info(f"Specific product energy: {specific_energy_GJ_t:,.2f} GJ/t")

# Add total row
total_row = pd.DataFrame({
    "Process Phase": ["Total"],
    "Total Gas [GJ/y]": [total_gas_gj],
    "Total Electricity [GJ/y]": [total_electricity_gj]
})

summary_table = pd.concat([summary_table, total_row], ignore_index=True)

st.subheader("Annual Energy Consumption by Process Phase")
st.dataframe(
    summary_table.style.format({
        "Total Gas [GJ/y]": "{:,.0f}",
        "Total Electricity [GJ/y]": "{:,.0f}"
    }),
    use_container_width=True
)

#-------------------------------------------------------

gj_per_mwh = conv["universal"]["energy"]["GJ_per_MWh"]
mwh_per_gj = conv["universal"]["energy"]["MWh_per_GJ"]
mj_per_smc = conv["natural_gas"]["conversion_factors"]["MJ_per_Smc"]
mwh_per_smc = conv["natural_gas"]["conversion_factors"]["MWh_per_Smc"]
smc_per_mwh = conv["natural_gas"]["reference_basis"]["Smc_per_MWh"]

# ---- Elaborations only in MWh ----
total_gas_mwh = total_gas_gj * mwh_per_gj
total_electricity_mwh = total_electricity_gj * mwh_per_gj

# ---- CHP assumptions ----
chp_ee_share = chp_ee_share_pct / 100
chp_electricity_mwh = total_electricity_mwh * chp_ee_share
# once defined the part of electricity autogenerated I can calucate the gas for the chp

chp_eff = 0.28
process_gas_displaced_by_chp_mwh=chp_electricity_mwh/chp_eff  # MWh

#chp_gas_share = chp_gas_share_pct / 100

# ---- CHP electricity and size ----
if chp_hours > 0:
    chp_size_mw = chp_electricity_mwh / chp_hours
else:
    chp_size_mw = 0.0

# ---- Gas split from grid ----
#process_gas_displaced_by_chp_mwh = total_gas_mwh * chp_gas_share
gas_from_gas_grid_for_process_mwh = total_gas_mwh - process_gas_displaced_by_chp_mwh
# ---- CHP gas requirement ----
gas_needed_mwh = chp_electricity_mwh / chp_eff if chp_eff > 0 else 0.0
gas_needed_gj = gas_needed_mwh * gj_per_mwh
gas_needed_smc = gas_needed_mwh * smc_per_mwh

total_gas_smc = total_gas_mwh * smc_per_mwh
chp_gas_vs_total_pct = (gas_needed_gj / total_gas_gj * 100) if total_gas_gj > 0 else 0.0
# Residual electricity from grid
grid_electricity_mwh = total_electricity_mwh - chp_electricity_mwh
# ---- Nice summary table ----
df_energy_summary = pd.DataFrame({
    "Item": [
        "Total electricity demand",
        "Electricity covered by CHP",
        "Electricity from grid",
        "Total gas demand",
        "Gas to CHP",
        "Gas to process"
    ],
    "Electricity [MWh/y]": [
        total_electricity_mwh,
        chp_electricity_mwh,
        grid_electricity_mwh,
        None,
        None,
        None
    ],
    "Gas [MWh/y]": [
        None,
        None,
        None,
        total_gas_mwh,
        gas_needed_mwh,
        gas_from_gas_grid_for_process_mwh
    ],
    "Gas [GJ/y]": [
        None,
        None,
        None,
        total_gas_mwh * gj_per_mwh,
        gas_needed_mwh * gj_per_mwh,
        gas_from_gas_grid_for_process_mwh * gj_per_mwh
    ],
    "Gas [Smc/y]": [
        None,
        None,
        None,
        total_gas_mwh * smc_per_mwh,
        gas_needed_mwh * smc_per_mwh,
        gas_from_gas_grid_for_process_mwh * smc_per_mwh
    ]
})

st.subheader("Energy summary")
st.dataframe(
    df_energy_summary.style.format({
        "Electricity [MWh/y]": "{:,.0f}",
        "Gas [MWh/y]": "{:,.0f}",
        "Gas [GJ/y]": "{:,.0f}",
        "Gas [Smc/y]": "{:,.0f}"
    }),
    use_container_width=True
)

# ------------------------Sankey nodes----------------------
labels = [
    "Gas grid",
    "CHP",
    "Process gas demand",
    "Electricity demand",
    "Grid electricity"
]

# Sankey links
source = [
    0,  # Gas grid -> CHP
    0,  # Gas grid -> Process gas demand
    1,  # CHP -> Electricity demand
    4   # Grid electricity -> Electricity demand
]

target = [
    1,
    2,
    3,
    3
]

value = [
    gas_needed_mwh,
    gas_from_gas_grid_for_process_mwh,
    chp_electricity_mwh,
    grid_electricity_mwh
]

fig = go.Figure(go.Sankey(
    arrangement="snap",
    node=dict(
        pad=20,
        thickness=20,
        line=dict(width=0.5),
        label=labels
    ),
    link=dict(
        source=source,
        target=target,
        value=value
    )
))

fig.update_layout(
    title_text="Energy flow with CHP",
    font_size=12
)

st.plotly_chart(fig, use_container_width=True)


# =========================
# Energy bill
# =========================

#--------------------------------------------------------------------------------------------
st.divider()
#--------------------------------------------------------------------------------------------
st.header("💶 Energy Bill")

c1,c2  = st.columns(2)
# ETS cost impact
with c1:
    gas_price= st.slider(
    "gas price [EUR/MWh]",
    min_value=0,
    max_value=400,
    value=75,
    step=1,
    key="gas_price"
)

with c2:
    ele_price= st.slider(
    "electricity price [EUR/MWh]",
    min_value=0,
    max_value=400,
    value=125,
    step=1,
    key="ele_price"
)

gas_bill=gas_price*gas_needed_mwh
ele_bill=ele_price*grid_electricity_mwh
total_energy_bill = gas_bill + ele_bill

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total energy bill [EUR/y]", f"{total_energy_bill:,.0f}")

with c2:
    st.metric("Gas bill [EUR/y]", f"{gas_bill:,.0f}")

with c3:
    st.metric("Electricity bill [EUR/y]", f"{ele_bill:,.0f}")


fig = go.Figure(
    data=[
        go.Pie(
            labels=["Gas", "Electricity"],
            values=[gas_bill, ele_bill],
            hole=0.35,
            textinfo="label+percent",
            hovertemplate="%{label}<br>Cost: %{value:,.0f} EUR/y<extra></extra>"
        )
    ]
)

fig.update_layout(
    title="Annual Energy Bill Breakdown"
)

st.plotly_chart(fig, use_container_width=True)


# =========================
# CO2 emissions assessment
# =========================
#--------------------------------------------------------------------------------------------
st.divider()
#--------------------------------------------------------------------------------------------
st.header("🏭 CO₂ emissions assessment")

st.markdown(
    """
    This section estimates CO₂ emissions in line with the EU ETS and GHG accounting approach,
    distinguishing between:

    - **Scope 1 emissions** from the direct combustion of natural gas on site
    - **Scope 2 emissions** from electricity imported from the grid

    For **Scope 1**, emissions are calculated using an inventory-based methodology:
    the amount of natural gas burned is multiplied by the applicable emission factor.

    For natural gas, a simplified emission factor is used:
    - **0.0561 tCO₂/GJ**
    - equivalent to **0.20196 tCO₂/MWh_gas**

    In the CHP configuration, it is good practice to keep the gas flows separated in order
    to clearly identify the sources of direct emissions:
    - **gas burned in the CHP** for on-site electricity generation
    - **residual process gas** burned in conventional thermal equipment

    Therefore, direct CO₂ emissions are calculated as:

    - **Scope 1 CO₂ from CHP = Gas to CHP × emission factor**
    - **Scope 1 CO₂ from burners = Residual process gas × emission factor**
    - **Total Scope 1 CO₂ = CO₂ from CHP + CO₂ from burners**

    Separately, **Scope 2 emissions** account for indirect emissions associated with
    **electricity imported from the grid**. These emissions are not generated physically
    at the plant, but arise from the off-site production of purchased electricity.

    This distinction ensures that on-site fuel combustion is properly captured under
    **Scope 1 / EU ETS-relevant direct emissions**, while grid electricity is reported
    under **Scope 2** as indirect energy-related emissions.
    """
)
# ---- CO2 assumptions ----
 #---- Emission factors from JSON ----
co2_factor_gas_t_per_mwh = conv["emissions"]["natural_gas"]["co2_factor_t_per_mwh"]
co2_factor_gas_t_per_gj = conv["emissions"]["natural_gas"]["co2_factor_t_per_gj"]
co2_factor_grid_t_per_mwh = conv["emissions"]["grid_it"]["co2_factor_t_per_mwh"]

# ---- Scope 1 emissions: direct natural gas combustion ----
scope1_chp_t = gas_needed_mwh * co2_factor_gas_t_per_mwh
scope1_process_t = gas_from_gas_grid_for_process_mwh * co2_factor_gas_t_per_mwh
scope1_total_t = scope1_chp_t + scope1_process_t

# ---- Scope 2 emissions: purchased electricity from grid ----
scope2_grid_t = grid_electricity_mwh * co2_factor_grid_t_per_mwh
# ---- Total Scope 1 + Scope 2 ----
scope1_scope2_total_t = scope1_total_t + scope2_grid_t

# ---- CO2 summary table ----
df_co2_summary = pd.DataFrame({
    "Emission source": [
        "Scope 1 - CHP gas combustion",
        "Scope 1 - Process gas combustion",
        "Scope 1 - Total",
        "Scope 2 - Grid electricity",
        "Scope 1 + Scope 2 - Total"
    ],
    "Activity": [
        gas_needed_mwh,
        gas_from_gas_grid_for_process_mwh,
        gas_needed_mwh + gas_from_gas_grid_for_process_mwh,
        grid_electricity_mwh,
        None
    ],
    "Unit": [
        "MWh/y",
        "MWh/y",
        "MWh/y",
        "MWh/y",
        "-"
    ],
    "Emission factor": [
        co2_factor_gas_t_per_mwh,
        co2_factor_gas_t_per_mwh,
        co2_factor_gas_t_per_mwh,
        co2_factor_grid_t_per_mwh,
        None
    ],
    "Emission factor unit": [
        "tCO2/MWh",
        "tCO2/MWh",
        "tCO2/MWh",
        "tCO2/MWh",
        "-"
    ],
    "CO2 emissions [tCO2/y]": [
        scope1_chp_t,
        scope1_process_t,
        scope1_total_t,
        scope2_grid_t,
        scope1_scope2_total_t
    ]
})

st.markdown("### Scope 1 and Scope 2 CO₂ emissions")
st.dataframe(
    df_co2_summary.style.format({
        "Activity": "{:,.0f}",
        "Emission factor": "{:,.5f}",
        "CO2 emissions [tCO2/y]": "{:,.0f}"
    }),
    use_container_width=True
)

c1,c2  = st.columns(2)
# ETS cost impact
with c1:
    co2_free_allowance= st.slider(
    "CO2 free allownce [%]",
    min_value=0,
    max_value=100,
    value=50,
    step=1,
    key="co2_free_allowance"
)

with c2:
    co2_EUA_price= st.slider(
    "EUA CO2 price [EUR/tCO2]",
    min_value=0,
    max_value=300,
    value=70,
    step=1,
    key="EUA CO2 price"
)
    
co2_emissions_under_co2_price=scope1_total_t*(1-co2_free_allowance/100)
co2_ETS1_burden=co2_emissions_under_co2_price*co2_EUA_price
st.info(f"ETS 1 cost : {co2_ETS1_burden/1000000:,.2f} MEUR/y")
# =========================
# H2 blending assessment
# =========================
#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------

st.header("Hydrogen blending assessment")

# Assumptions
h2_blend_vol_pct = st.slider(
    "Hydrogen blending [% vol.]",
    min_value=0,
    max_value=100,
    value=20,
    step=1,
    key="h2_blend_vol_pct"
)

h2_density_kg_per_smc = conv["hydrogen"]["reference_basis"]["density_kg_per_Smc"]
h2_mwh_per_smc = conv["hydrogen"]["conversion_factors"]["MWh_per_Smc"]
h2_kwh_per_kg = conv["hydrogen"]["conversion_factors"]["kWh_per_kg"]

# Baseline natural gas demand from your existing variables
total_energy_mwh = total_gas_mwh
natural_gas_smc_base = total_gas_smc

# Baseline NG energy content
ng_mwh_per_smc = (
    total_energy_mwh / natural_gas_smc_base
    if natural_gas_smc_base > 0 else 0.0
)

# Blend fraction
x = h2_blend_vol_pct / 100

# Energy content of blended fuel
blend_mwh_per_smc = (1 - x) * ng_mwh_per_smc + x * h2_mwh_per_smc

# Total blended fuel needed to keep annual energy constant
total_blend_smc = (
    total_energy_mwh / blend_mwh_per_smc
    if blend_mwh_per_smc > 0 else 0.0
)

# Split by volume
h2_needed_smc = total_blend_smc * x
ng_needed_smc = total_blend_smc * (1 - x)

# H2 mass
h2_needed_kg = h2_needed_smc * h2_density_kg_per_smc
h2_needed_t = h2_needed_kg / 1000

# Energy shares
h2_energy_mwh = h2_needed_smc * h2_mwh_per_smc
ng_energy_mwh = ng_needed_smc * ng_mwh_per_smc
h2_energy_share_pct = (
    100 * h2_energy_mwh / total_energy_mwh
    if total_energy_mwh > 0 else 0.0
)

# Summary table
df_h2_blend = pd.DataFrame({
    "Metric": [
        "Baseline NG energy content",
        "Blend energy content",
        "Total blended fuel needed",
        "Natural gas in blend",
        "Hydrogen needed",
        "Hydrogen needed",
        "Hydrogen energy supplied",
        "Hydrogen energy share"
    ],
    "Unit": [
        "MWh/Smc",
        "MWh/Smc",
        "Smc/y",
        "Smc/y",
        "Smc/y",
        "t/y",
        "MWh/y",
        "%"
    ],
    "Value": [
        ng_mwh_per_smc,
        blend_mwh_per_smc,
        total_blend_smc,
        ng_needed_smc,
        h2_needed_smc,
        h2_needed_t,
        h2_energy_mwh,
        h2_energy_share_pct
    ]
})

st.dataframe(
    df_h2_blend.style.format({
        "Value": "{:,.3f}"
    }),
    use_container_width=True
)

st.subheader("Energy comparison: without and with H₂ blending")

fig = go.Figure()

# Baseline: only natural gas
fig.add_trace(go.Bar(
    name="Natural gas",
    x=["Without H₂ blending", "With H₂ blending"],
    y=[total_gas_mwh, ng_energy_mwh]
))

# With H2: add hydrogen only in the blended case
fig.add_trace(go.Bar(
    name="Hydrogen",
    x=["Without H₂ blending", "With H₂ blending"],
    y=[0, h2_energy_mwh]
))

fig.update_layout(
    barmode="stack",
    title="Annual energy demand comparison",
    xaxis_title="Scenario",
    yaxis_title="Energy [MWh/y]",
    legend_title="Energy carrier"
)

st.plotly_chart(fig, use_container_width=True)