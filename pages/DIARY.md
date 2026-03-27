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
st.title("🧀🇮🇹 Dairy")
st.caption("Source: elaboration by Wavetransition")

#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------


c1,c2,c3,c4,c5  = st.columns(5)

with c1:
    st.subheader("Annual Production [t/y]")
    annual_production_t=st.number_input(
    "Annual Production [t/y]",
    min_value=0,
    value=10000,
    step=5,
    key="annual_production_t"
)

with c2:
    st.subheader("operating hours [h]")
    chp_operating_hours=st.number_input(
        "operating hours [h]",
        min_value=0,
        max_value=8760,
        value=5764,
        step=10,
        key="operating hours [h]"
    )

with c3:
    st.subheader("electricity by CHP [%]")
    chp_ee_share_pct = st.number_input(
        "CHP electricity share [%]",
        min_value=0,
        max_value=100,
        value=83,
        step=1,
        key="chp_electricity_share_pct"
    )

with c4:
    st.subheader("electricity by PV [MWh]")
    ee_pv_mwh = st.number_input(
        "Ele PV [MWh]",
        min_value=0,
        max_value=100000,
        value=870,
        step=1,
        key="Ele PV"
    )


with c5:
    st.subheader("diesel fleet [liters]")
    diesel_fleet_liter = st.number_input(
        "diesel fleet [liters]",
        min_value=0,
        max_value=150000,
        value=9150,
        step=500,
        key="diesel_fleet"
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
        <div style="background:{palette_blue[0]}; color:#1f1f1f; padding:12px 22px; border-radius:8px; font-weight:600; min-width:120px; text-align:center;">Reception</div>
        <div style="font-size:28px; font-weight:700; color:white; margin:0 8px;">→</div>
        <div style="background:{palette_blue[2]}; color:#1f1f1f; padding:12px 22px; border-radius:8px; font-weight:600; min-width:120px; text-align:center;">Processing</div>
        <div style="font-size:28px; font-weight:700; color:white; margin:0 8px;">→</div>
        <div style="background:{palette_green[1]}; color:#1f1f1f; padding:12px 22px; border-radius:8px; font-weight:600; min-width:120px; text-align:center;">Packaging & Cooling</div>
        <div style="font-size:28px; font-weight:700; color:white; margin:0 8px;">→</div>
        <div style="background:{palette_other[0]}; color:#1f1f1f; padding:12px 22px; border-radius:8px; font-weight:600; min-width:120px; text-align:center;">Distribution</div>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("")
h1, h2, h3 = st.columns([1.2, 2, 2])
h1.markdown("**Process Phase [MJ/t**")
h2.markdown("**Specific Thermal Consumption [GJ/t]**")
h3.markdown("**Specific Electrical Consumption [GJ/t]**")
st.write("")
r1c1, r1c2, r1c3 = st.columns([1.2, 2, 2])
r1c1.write("reception")
reception_th = r1c2.slider("reception_gas", min_value=0.0, max_value=0.001, value=0.0, step=0.001, format="%.3f", key="reception_gas")
reception_ee = r1c3.slider("reception_ee", min_value=0.0, max_value=0.001, value=0.0, step=0.001, format="%.3f", key="reception_ee")

r2c1, r2c2, r2c3 = st.columns([1.2, 2, 2])
r2c1.write("processing")
processing_th = r2c2.slider("processing_gas", min_value=0.0, max_value=1.000, value=0.0, step=0.001, format="%.3f", key="processing_gas")
processing_ee = r2c3.slider("processing_ee", min_value=0.0, max_value=1.000, value=0.0, step=0.001, format="%.3f", key="processing_ee")

r3c1, r3c2, r3c3 = st.columns([1.2, 2, 2])
r3c1.write("pack")
pack_th = r3c2.slider("pack_gas", min_value=0.1, max_value=10.500, value=6.00, step=0.001, format="%.3f", key="pack_gas")
pack_ee = r3c3.slider("pack_ee", min_value=0.0, max_value=10.000, value=2.50, step=0.001, format="%.3f", key="pack_ee")

r4c1, r4c2, r4c3 = st.columns([1.2, 2, 2])
r4c1.write("distribution")
distribution_th = r4c2.slider("distribution_gas", min_value=0.0, max_value=1.000, value=0.0, step=0.001, format="%.3f", key="distribution_gas")
distribution_ee = r4c3.slider("distribution_ee", min_value=0.0, max_value=1.000, value=0.0, step=0.001, format="%.3f", key="distribution_ee")


# Summary table
st.write("")
summary_table = pd.DataFrame({
    "Process Phase": [
    "Reception",
    "Processing",
    "Packaging & Cooling",
    "Distribution",
        ],
    "Total Thermal [GJ/y]": [
        reception_th * annual_production_t,
        processing_th * annual_production_t,
        pack_th * annual_production_t,
        distribution_th * annual_production_t,
        
    ],
    "Total Electricity [GJ/y]": [
        reception_ee * annual_production_t,
        processing_ee * annual_production_t,
        pack_ee * annual_production_t,
        distribution_ee * annual_production_t,
       
    ]
})

# =========================
# Total process energy requirements (expressed in GJ/year)
# =========================
ee_total_demand_gj = summary_table["Total Electricity [GJ/y]"].sum()
th_total_demand_gj = summary_table["Total Thermal [GJ/y]"].sum()
total_final_energy_demand_gj = ee_total_demand_gj + th_total_demand_gj

specific_final_energy_gj_per_t = total_final_energy_demand_gj / annual_production_t
st.info(f"Specific product energy: {specific_final_energy_gj_per_t:,.2f} GJ/t")


# Add total row
total_row = pd.DataFrame({
    "Process Phase": ["Total"],
    "Total Thermal [GJ/y]": [th_total_demand_gj],
    "Total Electricity [GJ/y]": [ee_total_demand_gj]
})

summary_table = pd.concat([summary_table, total_row], ignore_index=True)

st.subheader("Annual Energy Consumption by Process Phase")
st.dataframe(
    summary_table.style.format({
        "Total Thermal [GJ/y]": "{:,.0f}",
        "Total Electricity [GJ/y]": "{:,.0f}"
    }),
    use_container_width=True
)

# -------------------------------------------------------
#ENERGY BREAKDOWN ANALYSIS
# -------------------------------------------------------
# Conversions
gj_per_mwh = conv["universal"]["energy"]["GJ_per_MWh"]
mwh_per_gj = conv["universal"]["energy"]["MWh_per_GJ"]
mwh_per_smc = conv["natural_gas"]["conversion_factors"]["MWh_per_Smc"]
smc_per_mwh = conv["natural_gas"]["reference_basis"]["Smc_per_MWh"]
mj_per_liter = conv["diesel"]["conversion_factors"]["MJ_per_liter"]

# -------------------------------------------------------
# CHP assumptions
# -------------------------------------------------------
chp_electricity_share = chp_ee_share_pct / 100
chp_el_efficiency = 0.41
chp_th_efficiency = 0.45
boiler_efficiency = 0.90

# -------------------------------------------------------
# EE calculations and balance 
# -------------------------------------------------------
ee_total_demand_mwh = ee_total_demand_gj * mwh_per_gj
ee_chp_mwh = ee_total_demand_mwh * chp_electricity_share
ee_grid_mwh = max(0, ee_total_demand_mwh - ee_chp_mwh - ee_pv_mwh)
chp_electricity_coverage = ee_chp_mwh / ee_total_demand_mwh

# SIZING OF THE CHP
chp_capacity_mwe = ee_chp_mwh / chp_operating_hours
st.info(f"Estimated CHP electrical capacity: {chp_capacity_mwe:,.2f} MWe")

# -------------------------------------------------------
# therma the mix of gas used for cogeneration electricity and thermical loads l energy 
# -------------------------------------------------------
th_total_demand_mwh = th_total_demand_gj * mwh_per_gj

fuel_chp_input_mwh = ee_chp_mwh / chp_el_efficiency  #fuel into CHP
th_chp_useful_mwh = fuel_chp_input_mwh * chp_th_efficiency #useful thermal output from CHP
chp_thermal_coverage = th_chp_useful_mwh / th_total_demand_mwh  #th_boiler_useful_mwh

th_boiler_useful_mwh = th_total_demand_mwh - th_chp_useful_mwh  #fuel_boiler_input_mwh
fuel_boiler_input_mwh = th_boiler_useful_mwh / boiler_efficiency
total_fuel_purchased_mwh = fuel_chp_input_mwh + fuel_boiler_input_mwh #total_fuel_purchased_mwh

# -------------------------------------------------------
# energy vectors and source
# -------------------------------------------------------
# the first assumption her is that the natrual gas is used BUT LNG or LPG or Diesel
# ng= natual gas


# Natural gas purchase assumption
ng_purchased_mwh = total_fuel_purchased_mwh
ng_purchased_smc = ng_purchased_mwh * smc_per_mwh

# electricity from the grid
electricity_purchased_mwh = ee_grid_mwh


#diesel
diesel_energy_mj_per_year = diesel_fleet_liter * mj_per_liter
diesel_energy_gj_per_year = diesel_energy_mj_per_year / 1000
diesel_purchased_mwh = diesel_energy_gj_per_year / gj_per_mwh



# -------------------------------------------------------
# Energy summary table
df_energy_summary = pd.DataFrame({
    "Item": [
        "Total electricity demand",
        "Electricity from PV",
        "Electricity from CHP",
        "Electricity from grid",
        "Process thermal demand",
        "Useful heat from CHP",
        "Residual process gas",
        "Gas to CHP",
        "Gas from grid",
        "Diesel fleet"
    ],
    "Electricity [MWh/y]": [
        total_electricity_mwh,
        electricity_from_PV_mwh,
        chp_electricity_mwh,
        grid_electricity_mwh,
        None,
        None,
        None,
        None,
        None,
        None
    ],
    "Gas [MWh/y]": [
        None,
        None,
        None,
        None,
        process_thermal_demand_mwh,
        chp_useful_heat_mwh,
        residual_process_gas_mwh,
        gas_to_chp_mwh,
        gas_from_grid_mwh,
        None
    ],
    "Gas [GJ/y]": [
        None,
        None,
        None,
        None,
        process_thermal_demand_gj,
        chp_useful_heat_gj,
        residual_process_gas_gj,
        gas_to_chp_gj,
        gas_from_grid_gj,
        None
    ],
    "Gas [Smc/y]": [
        None,
        None,
        None,
        None,
        process_thermal_demand_smc,
        chp_useful_heat_mwh * smc_per_mwh,
        residual_process_gas_smc,
        gas_to_chp_smc,
        gas_from_grid_smc,
        None
    ],
    "Diesel [MJ/y]": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        diesel_mj_y
    ],
    "Diesel [GJ/y]": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        diesel_gj_y
    ],
    "Diesel [MWh/y]": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        diesel_mwh_y
    ]
})


df_energy_summary = pd.concat([df_energy_summary], ignore_index=True)

st.subheader("Energy summary")
st.dataframe(
    df_energy_summary.style.format({
        "Electricity [MWh/y]": "{:,.0f}",
        "Gas [MWh/y]": "{:,.0f}",
        "Gas [GJ/y]": "{:,.0f}",
        "Gas [Smc/y]": "{:,.0f}",
        "Diesel [MJ/y]": "{:,.0f}",
        "Diesel [GJ/y]": "{:,.0f}",
        "Diesel [MWh/y]": "{:,.0f}"
    }),
    use_container_width=True
)

# -------------------------------------------------------
# Sankey in MWh only
#------------------------------------------------
labels = [
    "Gas grid",
    "CHP",
    "Process thermal demand",
    "Useful heat from CHP",
    "Residual process gas",
    "PV electricity",
    "Grid electricity",
    "Electricity demand"
]

source = [
    0,  # Gas grid -> CHP
    0,  # Gas grid -> Residual process gas
    1,  # CHP -> Useful heat from CHP
    3,  # Useful heat from CHP -> Process thermal demand
    4,  # Residual process gas -> Process thermal demand
    5,  # PV electricity -> Electricity demand
    1,  # CHP -> Electricity demand
    6   # Grid electricity -> Electricity demand
]

target = [
    1,
    4,
    3,
    2,
    2,
    7,
    7,
    7
]

value = [
    gas_to_chp_mwh,
    residual_process_gas_mwh,
    chp_useful_heat_mwh,
    chp_useful_heat_mwh,
    residual_process_gas_mwh,
    electricity_from_PV_mwh,
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
    title_text="Energy flow (MWh/y)",
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
gas_needed_mwh=0

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

    """
)
# ---- CO2 assumptions ----
 #---- Emission factors from JSON ----
co2_factor_gas_t_per_mwh = conv["emissions"]["natural_gas"]["co2_factor_t_per_mwh"]
co2_factor_gas_t_per_gj = conv["emissions"]["natural_gas"]["co2_factor_t_per_gj"]
co2_factor_grid_t_per_mwh = conv["emissions"]["grid_it"]["co2_factor_t_per_mwh"]
gas_from_gas_grid_for_process_mwh=0
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
total_gas_smc=0
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

# =========================
# Fuel switching + electrification optimization (SciPy add-in)
# =========================
from scipy.optimize import linprog

st.divider()
st.header("🧮 Fuel mix optimization")

# -------------------------
# User inputs
# -------------------------
st.subheader("Energy and CO₂ price assumptions")

gas_price = st.slider(
    "Natural gas price [EUR/MWh]",
    min_value=0,
    max_value=400,
    value=75,
    step=1,
    key="opt_gas_price"
)

h2_price = st.slider(
    "Hydrogen price [EUR/MWh]",
    min_value=0,
    max_value=400,
    value=180,
    step=1,
    key="h2_price"
)

biomethane_price = st.slider(
    "Biomethane price [EUR/MWh]",
    min_value=0,
    max_value=400,
    value=110,
    step=1,
    key="biomethane_price"
)

ele_price = st.slider(
    "Electricity price [EUR/MWh]",
    min_value=0,
    max_value=400,
    value=125,
    step=1,
    key="opt_ele_price"
)

co2_EUA_price = st.slider(
    "CO₂ price [EUR/tCO₂]",
    min_value=0,
    max_value=200,
    value=70,
    step=1,
    key="co2_EUA_price"
)

c6, c7, c8, c9 = st.columns(4)

with c6:
    max_h2_share_pct = st.slider(
        "Maximum H₂ share in fuel mix [%]",
        min_value=0,
        max_value=100,
        value=20,
        step=1,
        key="max_h2_share_pct"
    )

with c7:
    max_electrification_share_pct = st.slider(
        "Maximum electrification share [%]",
        min_value=0,
        max_value=20,
        value=20,
        step=1,
        key="max_electrification_share_pct"
    )

with c8:
    max_h2_mwh = st.number_input(
        "Max hydrogen availability [MWh/y]",
        min_value=0.0,
        value=float(total_gas_mwh),
        step=100.0,
        key="max_h2_mwh"
    )

with c9:
    max_biomethane_mwh = st.number_input(
        "Max biomethane availability [MWh/y]",
        min_value=0.0,
        value=float(total_gas_mwh),
        step=100.0,
        key="max_biomethane_mwh"
    )

# -------------------------
# Demand and emission factors
# -------------------------
fuel_demand_mwh = total_gas_mwh

# Assumption: H2 and biomethane have no CO2 cost
co2_factor_h2_t_per_mwh = 0.0
co2_factor_biomethane_t_per_mwh = 0.0

# Electricity Scope 2 factor, if already loaded from JSON keep this variable name
# co2_factor_grid_t_per_mwh must already exist in your file
# If not, define it before this block.

# Total unit costs including ETS
gas_total_cost_eur_per_mwh = gas_price + co2_factor_gas_t_per_mwh * co2_EUA_price
h2_total_cost_eur_per_mwh = h2_price
biomethane_total_cost_eur_per_mwh = biomethane_price
electricity_total_cost_eur_per_mwh = ele_price

# -------------------------
# Linear programming problem
# Decision variables:
# x[0] = natural gas [MWh/y]
# x[1] = hydrogen [MWh/y]
# x[2] = biomethane [MWh/y]
# x[3] = electrified energy [MWh/y]
# -------------------------
c = [
    gas_total_cost_eur_per_mwh,
    h2_total_cost_eur_per_mwh,
    biomethane_total_cost_eur_per_mwh,
    electricity_total_cost_eur_per_mwh
]
ele_replacement_factor = 1.5
# Demand coverage
A_eq = [[1, 1, 1, ele_replacement_factor]]
b_eq = [fuel_demand_mwh]

A_ub = []
b_ub = []

# Availability constraints
A_ub.append([0, 1, 0, 0])
b_ub.append(max_h2_mwh)

A_ub.append([0, 0, 1, 0])
b_ub.append(max_biomethane_mwh)

# H2 share limit over total supplied energy
max_h2_share = max_h2_share_pct / 100
A_ub.append([
    -max_h2_share,
    1 - max_h2_share,
    -max_h2_share,
    -max_h2_share
])
b_ub.append(0)

# Electrification share limit over total supplied energy
max_electrification_share = max_electrification_share_pct / 100
A_ub.append([
    -max_electrification_share,
    -max_electrification_share,
    -max_electrification_share,
    1 - max_electrification_share
])
b_ub.append(0)

# Variable bounds
bounds = [
    (0, None),  # x_gas
    (0, None),  # x_h2
    (0, None),  # x_biomethane
    (0, None)   # x_electricity
]

# -------------------------
# Solve
# -------------------------
result_lp = linprog(
    c=c,
    A_ub=A_ub,
    b_ub=b_ub,
    A_eq=A_eq,
    b_eq=b_eq,
    bounds=bounds,
    method="highs"
)

# -------------------------
# Results
# -------------------------
if result_lp.success:
    opt_gas_mwh = result_lp.x[0]
    opt_h2_mwh = result_lp.x[1]
    opt_biomethane_mwh = result_lp.x[2]
    opt_electricity_mwh = result_lp.x[3]

    opt_total_cost_eur = result_lp.fun

    opt_scope1_t = co2_factor_gas_t_per_mwh * opt_gas_mwh
    opt_scope2_t = co2_factor_grid_t_per_mwh * opt_electricity_mwh
    opt_total_co2_t = opt_scope1_t + opt_scope2_t

    df_fuel_optimization = pd.DataFrame({
        "Energy carrier": ["Natural gas", "Hydrogen", "Biomethane", "Electricity", "Total"],
        "Optimized energy [MWh/y]": [
            opt_gas_mwh,
            opt_h2_mwh,
            opt_biomethane_mwh,
            opt_electricity_mwh,
            opt_gas_mwh + opt_h2_mwh + opt_biomethane_mwh + opt_electricity_mwh
        ],
        "Unit cost incl. ETS [EUR/MWh]": [
            gas_total_cost_eur_per_mwh,
            h2_total_cost_eur_per_mwh,
            biomethane_total_cost_eur_per_mwh,
            electricity_total_cost_eur_per_mwh,
            None
        ],
        "Annual cost [EUR/y]": [
            opt_gas_mwh * gas_total_cost_eur_per_mwh,
            opt_h2_mwh * h2_total_cost_eur_per_mwh,
            opt_biomethane_mwh * biomethane_total_cost_eur_per_mwh,
            opt_electricity_mwh * electricity_total_cost_eur_per_mwh,
            opt_total_cost_eur
        ],
        "CO2 emissions [tCO2/y]": [
            opt_scope1_t,
            0.0,
            0.0,
            opt_scope2_t,
            opt_total_co2_t
        ]
    })

    st.dataframe(
        df_fuel_optimization.style.format({
            "Optimized energy [MWh/y]": "{:,.0f}",
            "Unit cost incl. ETS [EUR/MWh]": "{:,.2f}",
            "Annual cost [EUR/y]": "{:,.0f}",
            "CO2 emissions [tCO2/y]": "{:,.0f}"
        }),
        use_container_width=True
    )

else:
    st.error(f"Optimization failed: {result_lp.message}")
    

#pie graph
c1, c2 = st.columns(2)

with c1:
    st.metric("Baseline total bill [EUR/y]", f"{fuel_demand_mwh * gas_total_cost_eur_per_mwh:,.0f}")

    fig_base = go.Figure(
        data=[
            go.Pie(
                labels=["Natural gas"],
                values=[fuel_demand_mwh * gas_total_cost_eur_per_mwh],
                hole=0.35,
                textinfo="label+percent",
                hovertemplate="%{label}<br>Cost: %{value:,.0f} EUR/y<extra></extra>",
                marker=dict(
                    colors=[palette_blue[2]]
                )
            )
        ]
    )
    fig_base.update_layout(title="Baseline energy bill")
    st.plotly_chart(fig_base, use_container_width=True)

with c2:
    st.metric("Optimized total bill [EUR/y]", f"{opt_total_cost_eur:,.0f}")

    fig_opt = go.Figure(
        data=[
            go.Pie(
                labels=["Natural gas", "Hydrogen", "Biomethane", "Electricity"],
                values=[
                    opt_gas_mwh * gas_total_cost_eur_per_mwh,
                    opt_h2_mwh * h2_total_cost_eur_per_mwh,
                    opt_biomethane_mwh * biomethane_total_cost_eur_per_mwh,
                    opt_electricity_mwh * electricity_total_cost_eur_per_mwh
                ],
                hole=0.35,
                textinfo="label+percent",
                hovertemplate="%{label}<br>Cost: %{value:,.0f} EUR/y<extra></extra>",
                marker=dict(
                    colors=[
                        palette_blue[2],
                        palette_green[1],
                        palette_other[0],
                        palette_other[3]
                    ]
                )
            )
        ]
    )
    fig_opt.update_layout(title="Optimized energy bill")
    st.plotly_chart(fig_opt, use_container_width=True)