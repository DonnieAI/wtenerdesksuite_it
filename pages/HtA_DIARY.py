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
st.title("HARD TO ABATE : 🧀🇮🇹 Dairy")
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


# CHP losses
chp_losses_mwh = fuel_chp_input_mwh - ee_chp_mwh - th_chp_useful_mwh

# Boiler losses
boiler_losses_mwh = fuel_boiler_input_mwh - th_boiler_useful_mwh


# -------------------------------------------------------
# energy vectors and source
# -------------------------------------------------------
# the first assumption her is that the natrual gas is used BUT LNG or LPG or Diesel
# ng= natual gas


# Natural gas purchase assumption
ng_purchased_mwh = total_fuel_purchased_mwh
ng_purchased_smc = ng_purchased_mwh * smc_per_mwh

# electricity from the grid
ee_purchased_mwh = ee_grid_mwh


#diesel
diesel_energy_mj_per_year = diesel_fleet_liter * mj_per_liter
diesel_energy_gj_per_year = diesel_energy_mj_per_year / 1000
diesel_purchased_mwh = diesel_energy_gj_per_year / gj_per_mwh


# -------------------------------------------------------
# Sankey diagram in MWh/year
# -------------------------------------------------------

# Losses
chp_losses_mwh = fuel_chp_input_mwh - ee_chp_mwh - th_chp_useful_mwh
boiler_losses_mwh = fuel_boiler_input_mwh - th_boiler_useful_mwh

labels = [
    "Natural gas grid",   # 0
    "CHP",                # 1
    "Boiler",             # 2
    "CHP electricity",    # 3
    "CHP useful heat",    # 4
    "CHP losses",         # 5
    "Boiler useful heat", # 6
    "Boiler losses",      # 7
    "PV electricity",     # 8
    "Grid electricity",   # 9
    "Electricity demand", # 10
    "Thermal demand"      # 11
]

source = [
    0,  # Natural gas grid -> CHP
    0,  # Natural gas grid -> Boiler

    1,  # CHP -> CHP electricity
    1,  # CHP -> CHP useful heat
    1,  # CHP -> CHP losses

    2,  # Boiler -> Boiler useful heat
    2,  # Boiler -> Boiler losses

    3,  # CHP electricity -> Electricity demand
    8,  # PV electricity -> Electricity demand
    9,  # Grid electricity -> Electricity demand

    4,  # CHP useful heat -> Thermal demand
    6   # Boiler useful heat -> Thermal demand
]

target = [
    1,  # Natural gas grid -> CHP
    2,  # Natural gas grid -> Boiler

    3,  # CHP -> CHP electricity
    4,  # CHP -> CHP useful heat
    5,  # CHP -> CHP losses

    6,  # Boiler -> Boiler useful heat
    7,  # Boiler -> Boiler losses

    10, # CHP electricity -> Electricity demand
    10, # PV electricity -> Electricity demand
    10, # Grid electricity -> Electricity demand

    11, # CHP useful heat -> Thermal demand
    11  # Boiler useful heat -> Thermal demand
]

value = [
    fuel_chp_input_mwh,
    fuel_boiler_input_mwh,

    ee_chp_mwh,
    th_chp_useful_mwh,
    chp_losses_mwh,

    th_boiler_useful_mwh,
    boiler_losses_mwh,

    ee_chp_mwh,
    ee_pv_mwh,
    ee_purchased_mwh,

    th_chp_useful_mwh,
    th_boiler_useful_mwh
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
    title_text="Annual energy flows (MWh/year)",
    font_size=12
)

st.plotly_chart(fig, use_container_width=True)


# =========================
# Energy bill
# =========================

# =========================
# Energy bill
# =========================

# --------------------------------------------------------------------------------------------
st.divider()
# --------------------------------------------------------------------------------------------
st.header("💶 Energy Bill")

c1, c2, c3 = st.columns(3)

with c1:
    gas_price = st.slider(
        "Natural gas price [EUR/MWh]",
        min_value=0,
        max_value=400,
        value=75,
        step=1,
        key="gas_price"
    )

with c2:
    electricity_price = st.slider(
        "Electricity price [EUR/MWh]",
        min_value=0,
        max_value=400,
        value=125,
        step=1,
        key="electricity_price"
    )

with c3:
    diesel_price = st.slider(
        "Diesel price [EUR/MWh]",
        min_value=0,
        max_value=400,
        value=150,
        step=1,
        key="diesel_price"
    )

# Annual energy costs
gas_bill = gas_price * ng_purchased_mwh
electricity_bill = electricity_price * ee_purchased_mwh
diesel_bill = diesel_price * diesel_purchased_mwh

total_energy_bill = gas_bill + electricity_bill + diesel_bill

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total energy bill [EUR/y]", f"{total_energy_bill:,.0f}")

with c2:
    st.metric("Gas bill [EUR/y]", f"{gas_bill:,.0f}")

with c3:
    st.metric("Electricity bill [EUR/y]", f"{electricity_bill:,.0f}")

with c4:
    st.metric("Diesel bill [EUR/y]", f"{diesel_bill:,.0f}")

fig = go.Figure(
    data=[
        go.Pie(
            labels=["Natural gas", "Electricity", "Diesel"],
            values=[gas_bill, electricity_bill, diesel_bill],
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
# --------------------------------------------------------------------------------------------
st.divider()
# --------------------------------------------------------------------------------------------
st.header("🏭 CO₂ emissions assessment")

st.markdown(
    """
    This section estimates CO₂ emissions in line with the EU ETS and GHG accounting approach,
    distinguishing between:

    - **Scope 1 emissions** from the direct combustion of fuels on site
    - **Scope 2 emissions** from electricity imported from the grid
    """
)

# ---- Emission factors from JSON ----
co2_factor_ng_t_per_mwh = conv["emissions"]["natural_gas"]["co2_factor_t_per_mwh"]
co2_factor_ng_t_per_gj = conv["emissions"]["natural_gas"]["co2_factor_t_per_gj"]
co2_factor_grid_t_per_mwh = conv["emissions"]["grid_it"]["co2_factor_t_per_mwh"]
co2_factor_diesel_t_per_mwh = conv["emissions"]["diesel"]["co2_factor_t_per_mwh"]

# ---- Scope 1 emissions: direct fuel combustion ----
scope1_chp_ng_t = fuel_chp_input_mwh * co2_factor_ng_t_per_mwh
scope1_boiler_ng_t = fuel_boiler_input_mwh * co2_factor_ng_t_per_mwh
scope1_diesel_t = diesel_purchased_mwh * co2_factor_diesel_t_per_mwh

scope1_total_t = scope1_chp_ng_t + scope1_boiler_ng_t + scope1_diesel_t

# ---- Scope 2 emissions: purchased electricity from grid ----
scope2_grid_t = ee_purchased_mwh * co2_factor_grid_t_per_mwh

# ---- Total Scope 1 + Scope 2 ----
scope1_scope2_total_t = scope1_total_t + scope2_grid_t

# ---- CO2 summary table ----
df_co2_summary = pd.DataFrame({
    "Emission source": [
        "Scope 1 - CHP natural gas combustion",
        "Scope 1 - Boiler natural gas combustion",
        "Scope 1 - Diesel combustion",
        "Scope 1 - Total",
        "Scope 2 - Grid electricity",
        "Scope 1 + Scope 2 - Total"
    ],
    "Activity": [
        fuel_chp_input_mwh,
        fuel_boiler_input_mwh,
        diesel_purchased_mwh,
        fuel_chp_input_mwh + fuel_boiler_input_mwh + diesel_purchased_mwh,
        ee_purchased_mwh,
        None
    ],
    "Unit": [
        "MWh/y",
        "MWh/y",
        "MWh/y",
        "MWh/y",
        "MWh/y",
        "-"
    ],
    "Emission factor": [
        co2_factor_ng_t_per_mwh,
        co2_factor_ng_t_per_mwh,
        co2_factor_diesel_t_per_mwh,
        None,
        co2_factor_grid_t_per_mwh,
        None
    ],
    "Emission factor unit": [
        "tCO2/MWh",
        "tCO2/MWh",
        "tCO2/MWh",
        "-",
        "tCO2/MWh",
        "-"
    ],
    "CO2 emissions [tCO2/y]": [
        scope1_chp_ng_t,
        scope1_boiler_ng_t,
        scope1_diesel_t,
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

c1, c2 = st.columns(2)

with c1:
    co2_free_allowance_pct = st.slider(
        "CO₂ free allowance [%]",
        min_value=0,
        max_value=100,
        value=50,
        step=1,
        key="co2_free_allowance_pct"
    )

with c2:
    co2_eua_price = st.slider(
        "EUA CO₂ price [EUR/tCO2]",
        min_value=0,
        max_value=300,
        value=70,
        step=1,
        key="co2_eua_price"
    )

# ETS cost impact: typically applied to ETS-covered Scope 1 stationary combustion
scope1_ets_eligible_t = scope1_chp_ng_t + scope1_boiler_ng_t
co2_emissions_under_eua_t = scope1_ets_eligible_t * (1 - co2_free_allowance_pct / 100)
co2_ets1_burden_eur = co2_emissions_under_eua_t * co2_eua_price

#st.info(f"ETS 1 cost: {co2_ets1_burden_eur / 1_000_000:,.2f} MEUR/y")
st.metric("ETS 1 cost [EUR/y]", f"{co2_ets1_burden_eur / 1_000_000:,.2f} MEUR/y")