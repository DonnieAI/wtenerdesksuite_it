import streamlit as st
import pandas as pd

def apply_style_and_logo():
    # Apply custom font style
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat&display=swap');
        html, body, [class*="css"] {
            font-family: 'Montserrat', sans-serif;
        }
        </style>
        """, unsafe_allow_html=True)

    # Sidebar content
    with st.sidebar:
        # App name at top
        st.markdown("<h2 style='text-align: center;'>WT APPLICATIONS HUB", unsafe_allow_html=True)
        st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
        st.image("logo-wavetransition_long.png", use_container_width=True)
        
def tco_capex_vehicle_calculator(df_in: pd.DataFrame, category: str, year: int) -> pd.DataFrame:
    """
    Compute CAPEX breakdown and total for a given vehicle Category and Year.

    Returns a DataFrame with one row per Technology:
    Category, Year, Technology, capex_energy, capex_power, capex_fixed, capex_total
    """
    df = df_in.copy()

    # Filter
    df = df[(df["Category"] == category) & (df["Year"] == year)].copy()

    if df.empty:
        return pd.DataFrame(columns=[
            "Category", "Year", "Technology",
            "capex_energy", "capex_power", "capex_fixed", "capex_total"
        ])

    # Ensure numeric columns are numeric
    numeric_cols = [
        "Energy_Storage_Cost", "Powertrain_Cost", "Other_cost", "Rest_of_Truck_Cost",
        "Energy", "Power"
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # CAPEX components
    df["capex_energy"] = df["Energy_Storage_Cost"] * df["Energy"]
    df["capex_power"]  = df["Powertrain_Cost"] * df["Power"]
    df["capex_fixed"]  = df["Rest_of_Truck_Cost"] + df["Other_cost"]
    df["capex_total"]  = df["capex_energy"] + df["capex_power"] + df["capex_fixed"]

    # Output
    out = df[[
        "Category", "Year", "Technology",
        "capex_energy", "capex_power", "capex_fixed", "capex_total"
    ]].copy()

    return out


def tco_fuel_consumption_manually_calculator(
    df_vehicles: pd.DataFrame,
    df_params: pd.DataFrame,
    category: str,
    year: int
) -> pd.DataFrame:
    """
    Computes annual fuel/energy consumption based on:
      - df_vehicles: contains Annual_km and Technology (plus Category/Year)
      - df_params: contains per-100km consumption by Technology (Value) + Unit

    Annual_consumption = Annual_km * Value / 100

    Returns columns:
      Category, Technology, Year, Annual_km, Weight, Unit, Value, Annual_consumption
    """
    # Filter vehicles for category/year
    v = df_vehicles.copy()
    v = v[(v["Year"] == year) & (v["Category"] == category)].copy()
    v = v.loc[:, ["Category", "Technology", "Year", "Annual_km", "Weight"]].copy()

    # Prepare params
    p = df_params.copy()
    v["Technology"] = v["Technology"].astype(str).str.strip()
    p["Technology"] = p["Technology"].astype(str).str.strip()

    # Ensure Value is numeric
    p["Value"] = pd.to_numeric(p["Value"], errors="coerce")

    # Drop duplicates in params (first occurrence kept)
    p = p.drop_duplicates(subset=["Technology"], keep="first")

    # Merge
    out = v.merge(p[["Technology", "Unit", "Value"]], on="Technology", how="left")

    # Annual consumption (Value is per 100km)
    out["Annual_consumption"] = pd.to_numeric(out["Annual_km"], errors="coerce") * out["Value"] / 100.0

    return out

def yearly_fuel_cost(
    df_consumption,
    diesel_price,
    lng_price,
    electricity_price,
    h2_price,
    yearly_mileage
):
    df = df_consumption.copy()

    # Scale consumption to user mileage
    df["consumption_per_km"] = df["Value"] / 100.0
    df["Annual_consumption_user"] = df["consumption_per_km"] * yearly_mileage

    # Direct multiplication based on Technology
    df["annual_fuel_cost"] = 0.0

    df.loc[df["Technology"] == "ICE-D", "annual_fuel_cost"] = \
        df["Annual_consumption_user"] * diesel_price

    df.loc[df["Technology"] == "ICE-NG", "annual_fuel_cost"] = \
        df["Annual_consumption_user"] * lng_price

    df.loc[df["Technology"] == "BET", "annual_fuel_cost"] = \
        df["Annual_consumption_user"] * electricity_price

    df.loc[df["Technology"] == "FCET", "annual_fuel_cost"] = \
        df["Annual_consumption_user"] * h2_price

    return df

def create_tco_template_from_data(
    df_vehicle: pd.DataFrame,
    country: str,
    category: str,
    year: int,
    annual_km_user: int
) -> pd.DataFrame:
    """
    Build the master TCO dataframe including Country and user annual mileage.
    One row per Technology for selected Category and Year.
    """

    df_filtered = df_vehicle[
        (df_vehicle["Category"] == category) &
        (df_vehicle["Year"] == year)
    ].copy()

    technologies = sorted(df_filtered["Technology"].dropna().unique().tolist())

    df_template = pd.DataFrame({
        "Country": [country] * len(technologies),
        "Category": [category] * len(technologies),
        "Technology": technologies,
        "Year": [year] * len(technologies),
        "annual_km_user": [annual_km_user] * len(technologies),
    })

    # Initialize calculation columns (filled later)
    df_template["capex_total"] = pd.NA
    df_template["Unit"] = pd.NA
    df_template["consumption_per_100km"] = pd.NA
    df_template["annual_consumption_user"] = pd.NA
    df_template["annual_fuel_cost"] = pd.NA
    df_template["annual_toll_cost"]=pd.NA
    df_template["annual_wages_cost"]=pd.NA

    return df_template

def apply_driver_wages(df_master: pd.DataFrame, df_wages: pd.DataFrame):

    df = df_master.copy()

    # Merge on Country + Year
    df = df.merge(
        df_wages[["Country", "Year", "Unitary_Wage_km"]],
        on=["Country", "Year"],
        how="left"
    )

    # Compute annual driver cost
    df["annual_driver_cost"] = df["Unitary_Wage_km"] * df["annual_km_user"]

    return df