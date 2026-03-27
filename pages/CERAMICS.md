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
st.title("🏺🇮🇹 Ceramics")
st.caption("Source: GME , elaboration by Wavetransition")

#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------


c1,c2  = st.columns(2)

with c1:
    st.subheader("Annual Production [t/y]")
    annual_production_t=st.number_input(
    "Annual Production [t/y]",
    value=85000,
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

#annual_production_t = st.session_state["annual_production_t"]

st.subheader("Consumption by process phase")

h1, h2, h3 = st.columns([1.2, 2, 2])
h1.markdown("**Process Phase**")
h2.markdown("**Specific Thermal Consumption [GJ/t]**")
h3.markdown("**Specific Electrical Consumption [GJ/t]**")

r1c1, r1c2, r1c3 = st.columns([1.2, 2, 2])
r1c1.write("Wet grinding")
wet_grinding_gas = r1c2.slider("wet_grinding_gas", 0.0, 0.001, 0.0, 0.001, format="%.3f", key="wet_grinding_gas")
wet_grinding_ee = r1c3.slider("wet_grinding_ee", 0.05, 0.35, 0.25, 0.005, format="%.3f", key="wet_grinding_ee")

r2c1, r2c2, r2c3 = st.columns([1.2, 2, 2])
r2c1.write("Spray drying")
spray_drying_gas = r2c2.slider("spray_drying_gas", 1.1, 2.2, 1.8, 0.005, format="%.3f", key="spray_drying_gas")
spray_drying_ee = r2c3.slider("spray_drying_ee", 0.01, 0.07, 0.03, 0.005, format="%.3f", key="spray_drying_ee")

r3c1, r3c2, r3c3 = st.columns([1.2, 2, 2])
r3c1.write("Pressing")
pressing_gas = r3c2.slider("pressing_gas", 0.0, 0.001, 0.0, 0.001, format="%.3f", key="pressing_gas")
pressing_ee = r3c3.slider("pressing_ee", 0.005, 0.15, 0.02, 0.005, format="%.3f", key="pressing_ee")

r4c1, r4c2, r4c3 = st.columns([1.2, 2, 2])
r4c1.write("Drying")
drying_gas = r4c2.slider("drying_gas", 0.3, 0.8, 0.5, 0.005, format="%.3f", key="drying_gas")
drying_ee = r4c3.slider("drying_ee", 0.01, 0.04, 0.02, 0.005, format="%.3f", key="drying_ee")

r5c1, r5c2, r5c3 = st.columns([1.2, 2, 2])
r5c1.write("Firing")
firing_gas = r5c2.slider("firing_gas", 1.9, 4.8, value=2.685, step=0.005, format="%.3f", key="firing_gas")
firing_ee = r5c3.slider("firing_ee", 0.02, 0.15, 0.1, 0.005, format="%.3f", key="firing_ee")

#----------OVERRAIDING TEMP
#wet_grinding_ee=0.594


# Summary table
summary_table = pd.DataFrame({
    "Process Phase": [
        "Wet grinding",
        "Spray drying",
        "Pressing",
        "Drying",
        "Firing"
    ],
    "Total Gas [GJ/y]": [
        wet_grinding_gas * annual_production_t,
        spray_drying_gas * annual_production_t,
        pressing_gas * annual_production_t,
        drying_gas * annual_production_t,
        firing_gas * annual_production_t
    ],
    "Total Electricity [GJ/y]": [
        wet_grinding_ee * annual_production_t,
        spray_drying_ee * annual_production_t,
        pressing_ee * annual_production_t,
        drying_ee * annual_production_t,
        firing_ee * annual_production_t
    ]
})

total_gas_gj = summary_table["Total Gas [GJ/y]"].sum()
total_electricity_gj = summary_table["Total Electricity [GJ/y]"].sum()

# Add total row
total_row = pd.DataFrame({
    "Process Phase": ["Total"],
    "Total Gas [GJ/y]": [total_gas_gj],
    "Total Electricity [GJ/y]": [total_electricity_gj]
})

summary_table = pd.concat([summary_table, total_row], ignore_index=True)

st.subheader("Annual Energy Consumption by Process Phase")
st.dataframe(summary_table, use_container_width=True)


#---------------------------
c1,c2  = st.columns(2)

with c1:
    chp_gas_share_pct = st.slider(
        "CHP gas share [%]",
        min_value=0,
        max_value=100,
        value=25,
        step=1,
        key="chp_gas_share_pct"
    )


with c2:
    chp_ee_share_pct = st.slider(
        "CHP electricity share [%]",
        min_value=0,
        max_value=100,
        value=89,
        step=1,
        key="chp_electricity_share_pct"
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



# Sankey nodes
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

#--------------------------------------------------------------------------------------------
st.divider()

st.subheader("Energy Bill")

# =========================
# CO2 emissions assessment
# =========================

st.markdown("## CO₂ emissions assessment")

st.markdown(
    """
    This section estimates direct CO₂ emissions from natural gas combustion in the plant.
    The inventory-based methodology is straightforward: emissions are calculated as the
    amount of fuel consumed multiplied by a fuel-specific emission factor.

    For natural gas, a simplified emission factor is used:
    - **0.0561 tCO₂/GJ**
    - equivalent to **0.20196 tCO₂/MWh_gas**

    In the CHP configuration, it is good practice to keep the energy flows separated:
    - **gas burned in the CHP** to generate electricity,
    - **residual process gas** still burned in conventional thermal equipment.

    Therefore, CO₂ emissions are calculated as:

    - **CO₂ from CHP = Gas to CHP × emission factor**
    - **CO₂ from burners = Residual process gas × emission factor**
    - **Total CO₂ = CO₂ from CHP + CO₂ from burners**

    This approach is consistent with an inventory perspective, where fuel input,
    electricity output, and useful thermal output are accounted for as distinct flows.
    """
)

# ---- CO2 assumptions ----
#co2_factor_t_per_mwh = 0.20196
#co2_factor_t_per_gj = 0.0561


#with open("conversion_factors.json", "r", encoding="utf-8") as f:
 #   conv = json.load(f)

co2_factor_t_per_mwh = conv["emissions"]["natural_gas"]["co2_factor_t_per_mwh"]
co2_factor_t_per_gj = conv["emissions"]["natural_gas"]["co2_factor_t_per_gj"]
# ---- CO2 from CHP and residual burners ----
residual_process_gas_mwh = gas_from_gas_grid_for_process_mwh

co2_chp_t = gas_needed_mwh * co2_factor_t_per_mwh
co2_burners_t = residual_process_gas_mwh * co2_factor_t_per_mwh
co2_total_t = co2_chp_t + co2_burners_t

# ---- CO2 by process from residual gas burners ----
co2_by_process_df = pd.DataFrame({
    "Process Phase": [
        "Wet grinding",
        "Spray drying",
        "Pressing",
        "Drying",
        "Firing"
    ],
    "Residual Gas for Process [MWh/y]": [
        wet_grinding_gas / (3.6 * residual_process_gas_mwh),
        spray_drying_gas / (3.6 * residual_process_gas_mwh),
        pressing_gas / (3.6 * residual_process_gas_mwh),
        drying_gas / (3.6 * residual_process_gas_mwh),
        firing_gas /(3.6 * residual_process_gas_mwh),
    ]
})

co2_by_process_df["CO2 from Burners [tCO2/y]"] = (
    co2_by_process_df["Residual Gas for Process [MWh/y]"] * co2_factor_t_per_mwh
)

total_row_co2 = pd.DataFrame({
    "Process Phase": ["Total burners"],
    "Residual Gas for Process [MWh/y]": [co2_by_process_df["Residual Gas for Process [MWh/y]"].sum()],
    "CO2 from Burners [tCO2/y]": [co2_by_process_df["CO2 from Burners [tCO2/y]"].sum()]
})

co2_by_process_df = pd.concat([co2_by_process_df, total_row_co2], ignore_index=True)

# ---- Global CO2 summary ----
df_co2_summary = pd.DataFrame({
    "Source": [
        "CHP",
        "Process burners",
        "Total"
    ],
    "Gas consumption [MWh/y]": [
        gas_needed_mwh,
        residual_process_gas_mwh,
        gas_needed_mwh + residual_process_gas_mwh
    ],
    "Emission factor [tCO2/MWh]": [
        co2_factor_t_per_mwh,
        co2_factor_t_per_mwh,
        co2_factor_t_per_mwh
    ],
    "CO2 emissions [tCO2/y]": [
        co2_chp_t,
        co2_burners_t,
        co2_total_t
    ]
})

st.markdown("### CO₂ summary by energy system")
st.dataframe(
    df_co2_summary.style.format({
        "Gas consumption [MWh/y]": "{:,.2f}",
        "Emission factor [tCO2/MWh]": "{:,.5f}",
        "CO2 emissions [tCO2/y]": "{:,.2f}"
    }),
    use_container_width=True
)

st.markdown("### CO₂ from residual process gas by process phase")
st.dataframe(
    co2_by_process_df.style.format({
        "Residual Gas for Process [MWh/y]": "{:,.2f}",
        "CO2 from Burners [tCO2/y]": "{:,.2f}"
    }),
    use_container_width=True
)


# TARFI BILL STRUCTURE

with open("italy_gas_distribution_tariff_q4_2025_ambito2.json", "r", encoding="utf-8") as f:
    tariff = json.load(f)

fixed_components = tariff["fixed_components_eur_per_year"]
meter_class = "C_gt_G40"

fixed_g40_plus_eur_per_year = sum(
    component[meter_class]
    for component in fixed_components.values()
)

st.text(fixed_g40_plus_eur_per_year)

st.text(total_gas_smc)

def get_consumption_bracket(total_gas_smc: float, tariff: dict) -> dict:
    brackets = tariff["variable_distribution_t3_dis_ceur_per_smc_by_consumption"]

    for bracket in brackets:
        lower = bracket["from_smc"]
        upper = bracket["to_smc"]

        if upper is None:
            if total_gas_smc >= lower:
                return bracket
        elif lower <= total_gas_smc <= upper:
            return bracket

    raise ValueError(f"No tariff bracket found for total_gas_smc={total_gas_smc}")


def get_variable_transport_components(total_gas_smc: float, tariff: dict) -> dict:
    bracket = get_consumption_bracket(total_gas_smc, tariff)

    return {
        "from_smc": bracket["from_smc"],
        "to_smc": bracket["to_smc"],
        "t3_dis": bracket.get("t3_dis", 0.0),
        "ug1": bracket.get("ug1", 0.0),
        "ug2c": bracket.get("ug2c", 0.0),
        "ug3int": bracket.get("ug3int", 0.0),
        "ug3ui": bracket.get("ug3ui", 0.0),
        "ug3ft": bracket.get("ug3ft", 0.0),
        "gs": bracket.get("gs", 0.0),
        "re_pre2023": bracket.get("re_pre2023", 0.0),
        "rs": bracket.get("rs", 0.0),
        "vr": bracket.get("vr", 0.0),
        "st": bracket.get("st", 0.0),
    }
    
with open("italy_gas_distribution_tariff_q4_2025_ambito2.json", "r", encoding="utf-8") as f:
    tariff = json.load(f)

components = get_variable_transport_components(total_gas_smc, tariff)

t3_dis = components.get("t3_dis", 0.0)
st.text(t3_dis)
t3_dis_part=t3_dis*total_gas_smc/100  # in cEUR shall be divided


# =========================
# H2 blending assessment
# =========================
st.subheader("Hydrogen blending assessment")

# Assumptions
h2_blend_vol_pct = st.slider(
    "Hydrogen blending [% vol.]",
    min_value=0,
    max_value=100,
    value=20,
    step=1,
    key="h2_blend_vol_pct"
)

h2_density_kg_per_smc = 0.0899
h2_mwh_per_smc = 10.8 / 3600  # H2 LHV: 10.8 MJ/Smc

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