from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
import json
#import plotly.graph_objects as go
#from plotly.subplots import make_subplots
import importlib
import re
from dataclasses import dataclass, asdict
from typing import Any, Callable, Optional, Dict
from typing import TypedDict


st.set_page_config(page_title="Dashboard", layout="wide")
from utils import apply_style_and_logo
#from supporting_functions.editing_function import styled_scrollable_markdown
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

class Defaults(TypedDict):
    provider: str
    offer: str
    consumption_kwh: float
    power_kw: float
    months: float
    pun_eur_per_kwh: float
    losses_lambda: float
    spread_eur_per_kwh: float
    dispacciamento_pd_eur_per_kwh: float
    disp_bt_eur_per_pdp: float
    ccv_eur_per_pdp: float
    t3_eur_per_kwh: float
    uc3_eur_per_kwh: float
    uc6_var_eur_per_kwh: float
    t1_eur_per_pdp_month: float
    t2_eur_per_kw_month: float
    uc6_pow_eur_per_kw_month: float
    arim_eur_per_kwh: float
    asos_eur_per_kwh: float
    excise_eur_per_kwh: float
    vat_rate: float

#Block 1 — Base defaults (hardcoded)
def base_defaults() ->  Defaults:
    """
    Hardcoded defaults used when no offer is loaded.
    These keys MUST include everything your UI will edit.
    """
    return {
        # Text
        "provider": "dummy",
        "offer": "dummy",

        # Usage
        "consumption_kwh": 1200.0,
        "power_kw": 3.0,
        "months": 1.0,

        # Market / offer
        "pun_eur_per_kwh": 0.01,
        "losses_lambda": 0.2,
        "spread_eur_per_kwh": 0.02,
        "dispacciamento_pd_eur_per_kwh": 0.00,

        # Sale fixed
        "disp_bt_eur_per_pdp": 0.0,
        "ccv_eur_per_pdp": 0.0,

        # Network variable
        "t3_eur_per_kwh": 0.0,
        "uc3_eur_per_kwh": 0.0,
        "uc6_var_eur_per_kwh": 0.0,

        # Network fixed / power
        "t1_eur_per_pdp_month": 0.0,
        "t2_eur_per_kw_month": 0.0,
        "uc6_pow_eur_per_kw_month": 0.0,

        # System charges
        "arim_eur_per_kwh": 0.0,
        "asos_eur_per_kwh": 0.0,

        # Taxes
        "excise_eur_per_kwh": 0.0,
        "vat_rate": 0.10,
    }

#Block 2 — Parsing helpers (numbers and %)
def parse_number(value: Any) -> Optional[float]:
    """
    Robust parsing:
    - handles "0,115"
    - handles "1.234,56"
    - handles "€ 12,34"
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    # remove currency and spaces
    s = s.replace("€", "").replace("\u00a0", " ").replace(" ", "")

    # extract number-like token
    m = re.search(r"[-+]?\d[\d.,]*", s)
    if not m:
        return None

    token = m.group(0)

    # both separators -> assume thousands '.' and decimal ','
    if "." in token and "," in token:
        token = token.replace(".", "").replace(",", ".")
    # only comma -> decimal comma
    elif "," in token and "." not in token:
        token = token.replace(",", ".")

    try:
        return float(token)
    except ValueError:
        return None



def parse_percent(value: Any) -> Optional[float]:
    """
    If input has % then convert to fraction.
    "10%" -> 0.10
    "0,10" -> 0.10
    """
    if value is None:
        return None
    s = str(value)
    n = parse_number(value)
    if n is None:
        return None
    if "%" in s:
        return n / 100.0
    return n


#Block 3 — Read an uploaded offer CSV (ITEM/VALUE)
def read_offer_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=",", engine="python", dtype=str, keep_default_na=False)

    # Keep only first two columns (ITEM and VALUE)
    df = df.iloc[:, :2]
    df.columns = ["ITEM", "VALUE"]

    return df


#Block 4 — Get one item value from the offer table
def get_item_value(
                    df: pd.DataFrame,
                    key: str,
                    *,
                    fallback: Any,
                    as_percent: bool = False,
                    cast: Optional[Callable[[Any], Any]] = float,
                ) -> Any:
    """
    Reads df rows where ITEM == key, returns VALUE.
    - cast=str for provider/offer
    - cast=float for numeric values
    """
    if df is None or df.empty or "ITEM" not in df.columns or "VALUE" not in df.columns:
        return fallback if cast is None else cast(fallback)

    mask = df["ITEM"].astype(str).str.strip().str.lower() == str(key).strip().lower()
    row = df.loc[mask]
    if row.empty:
        return fallback if cast is None else cast(fallback)
    raw = row.iloc[0]["VALUE"]
    if raw is None or str(raw).strip() == "":
        return fallback if cast is None else cast(fallback)
    # text
    if cast is str:
        return str(raw).strip()
    # numeric
    val = parse_percent(raw) if as_percent else parse_number(raw)
    if val is None:
        return fallback if cast is None else cast(fallback)
    return val if cast is None else cast(val)

#Block 5 — Convert an offer df → defaults dict
def defaults_from_offer_df(base: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Takes base defaults and overwrites with values found in the offer CSV.
    If a key is missing in CSV, base value is kept.
    """
    d = dict(base)
    d.update({
        "provider": get_item_value(df, "provider", fallback=d["provider"], cast=str),
        "offer": get_item_value(df, "offer", fallback=d["offer"], cast=str),
        "consumption_kwh":get_item_value(df, "QE_kWh", fallback=d["consumption_kwh"]),
        "power_kw": get_item_value(df, "Potenza_kW", fallback=d["power_kw"]),
        #energy 
        "losses_lambda": get_item_value(df, "Lambda", fallback=d["losses_lambda"], as_percent=True),
        "pun_eur_per_kwh": get_item_value(df, "PUN", fallback=d["pun_eur_per_kwh"]),
        "spread_eur_per_kwh": get_item_value(df, "SPREAD", fallback=d["spread_eur_per_kwh"]),
        "disp_bt_eur_per_pdp": get_item_value(df, "DISP_BT_Quota_fissa", fallback=d["disp_bt_eur_per_pdp"]),
        "ccv_eur_per_pdp": get_item_value(df, "CCV_Quota_fissa", fallback=d["ccv_eur_per_pdp"]),
        "dispacciamento_pd_eur_per_kwh": get_item_value(df, "PD", fallback=d["dispacciamento_pd_eur_per_kwh"]),
         # spese contatore
        "t3_eur_per_kwh": get_item_value(df, "T3 DIS - Variabile", fallback=d["t3_eur_per_kwh"]),
        "uc3_eur_per_kwh": get_item_value(df, "UC3 - Variabile", fallback=d["uc3_eur_per_kwh"]),
        "uc6_var_eur_per_kwh": get_item_value(df, "UC6 - Variabile", fallback=d["uc6_var_eur_per_kwh"]),
        "t1_eur_per_pdp_month": get_item_value(df, "T1 DIS- Fissa", fallback=d["t1_eur_per_pdp_month"]),
        "t2_eur_per_kw_month": get_item_value(df, "T2 DIS- Potenza", fallback=d["t2_eur_per_kw_month"]),
         "uc6_pow_eur_per_kw_month": get_item_value(df, "UC6 - Potenza", fallback=d["uc6_pow_eur_per_kw_month"]),
       
        #oneri di sistema           
        "arim_eur_per_kwh": get_item_value(df, "ARIM - Variabile", fallback=d["arim_eur_per_kwh"]),
        "asos_eur_per_kwh": get_item_value(df, "ASOS - Variabile", fallback=d["asos_eur_per_kwh"]),
       
        "excise_eur_per_kwh": get_item_value(df, "Accise", fallback=d["excise_eur_per_kwh"]),
        "vat_rate": get_item_value(df, "VAT", fallback=d["vat_rate"], as_percent=True),
    })

    return d

#Block 6 — Session state + offer upload + dropdown + “Load offer” button
# -----------------------------
# Block 6 — Streamlit setup + Offer selection logic
# -----------------------------
st.set_page_config(page_title="Bolletta – Offer selector", layout="wide")
st.title("Bolletta elettrica – confronto offerte")
st.caption("Seleziona un CSV offerta dalla cartella 'bollette', modifica i parametri e calcola.")

BASE = base_defaults()

# 1) Initialize session_state once
if "initialized" not in st.session_state:
    for k, v in BASE.items():
        st.session_state[k] = v
    st.session_state["initialized"] = True
    st.session_state["active_offer_label"] = "Base defaults"

# 2) Discover offer files from local folder
OFFERS_DIR = Path("bollette")
offer_files = sorted(OFFERS_DIR.glob("*.csv"))

with st.sidebar:
    st.header("Offerte (da cartella)")

    if not OFFERS_DIR.exists():
        st.error("Cartella 'bollette' non trovata. Creala accanto al file dell'app.")
        st.stop()

    if not offer_files:
        st.warning("Nessun file CSV trovato in 'bollette/'.")
        st.stop()

    # dropdown shows filenames
    selected_file = st.selectbox(
        "Seleziona offerta (file)",
        offer_files,
        format_func=lambda p: p.name,
        key="selected_offer_file",
    )

    if st.button("Carica offerta selezionata"):
        df_offer = read_offer_csv(selected_file)
        offer_defaults = defaults_from_offer_df(BASE, df_offer)
        # overwrite state with offer defaults
        for k, v in offer_defaults.items():
            st.session_state[k] = v
        st.session_state["active_offer_label"] = selected_file.name
        st.rerun()  # ensure UI updates immediately

st.success(f"Offerta attiva: {st.session_state.get('active_offer_label', 'N/A')}")

#Block 7 — Inputs dataclass + compute_bill
# -----------------------------
# Block 7 — Domain model + computation
# -----------------------------
@dataclass
class Inputs:
    consumption_kwh: float
    power_kw: float
    months: float

    pun_eur_per_kwh: float
    losses_lambda: float
    spread_eur_per_kwh: float
    dispacciamento_pd_eur_per_kwh: float

    disp_bt_eur_per_pdp: float
    ccv_eur_per_pdp: float

    t3_eur_per_kwh: float
    uc3_eur_per_kwh: float
    uc6_var_eur_per_kwh: float

    t1_eur_per_pdp_month: float
    t2_eur_per_kw_month: float
    uc6_pow_eur_per_kw_month: float

    arim_eur_per_kwh: float
    asos_eur_per_kwh: float

    excise_eur_per_kwh: float
    vat_rate: float  # fraction (0.10 means 10%)


def compute_bill(i: Inputs) -> Dict[str, Any]:
    """
    Simplified transparent bill model.
    """
    # Energy sale (variable)
    effective_kwh = i.consumption_kwh * (1.0 + i.losses_lambda)
    #energy_component = effective_kwh * i.pun_eur_per_kwh
    spread_component = i.consumption_kwh * i.spread_eur_per_kwh
    PUN_component=effective_kwh*(i.pun_eur_per_kwh+i.spread_eur_per_kwh)
    CCV_component=i.disp_bt_eur_per_pdp
    PD_component_var = i.consumption_kwh * i.dispacciamento_pd_eur_per_kwh
    DispBT_component=i.disp_bt_eur_per_pdp
    
    sale_var_total = PUN_component + PD_component_var
    sale_fix_total=CCV_component+DispBT_component

    # Sale fixed (assume 1 POD)
    sale_fix_total = i.months * (i.disp_bt_eur_per_pdp + i.ccv_eur_per_pdp)
    sale_total = sale_var_total + sale_fix_total

    # Network components
    network_var_total = i.consumption_kwh * (i.t3_eur_per_kwh + i.uc3_eur_per_kwh + i.uc6_var_eur_per_kwh)
    network_fix_total = i.months * i.t1_eur_per_pdp_month
    network_pow_total = i.months * i.power_kw * (i.t2_eur_per_kw_month + i.uc6_pow_eur_per_kw_month)
    network_total = network_var_total + network_fix_total + network_pow_total

    # System charges
    system_total = i.consumption_kwh * (i.arim_eur_per_kwh + i.asos_eur_per_kwh)

    # Taxes
    excise_total = i.consumption_kwh * i.excise_eur_per_kwh
    taxable_base = sale_total + network_total + system_total + excise_total
    vat_total = taxable_base * i.vat_rate

    grand_total = taxable_base + vat_total

    return {
        "breakdown": {
            "Componente materia prima  (variabile)": sale_var_total,
            "Vendita energia (fissa)": sale_fix_total,
            "Vendita energia (totale)": sale_total,
            "Rete (variabile)": network_var_total,
            "Rete (fissa)": network_fix_total,
            "Rete (potenza)": network_pow_total,
            "Rete (totale)": network_total,
            "Oneri di sistema": system_total,
            "Accise": excise_total,
            "IVA": vat_total,
            "TOTALE": grand_total,
        },
        "intermediate": {
            "effective_kwh_with_losses": effective_kwh,
            "taxable_base": taxable_base,
        },
        "inputs": asdict(i),
    }

#Block 8 — Editable input widgets bound to session_state
# -----------------------------
# Block 8 — UI Inputs (editable, persistent)
# -----------------------------
st.subheader("Dati offerta e parametri")

# Text fields
cA, cB = st.columns(2)
with cA:
    st.text_input("Provider", key="provider")
with cB:
    st.text_input("Offer", key="offer")

st.divider()
with st.expander("Mostra parametri offerta attiva (debug)"):
    st.json({k: st.session_state[k] for k in BASE.keys()})
# Numeric inputs arranged in columns (like your previous UI)
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("Consumi")
    st.number_input("Consumo (kWh)", min_value=0.0, step=10.0, key="consumption_kwh")
    st.number_input("Potenza impegnata (kW)", min_value=0.0, step=0.5, key="power_kw")
    st.number_input("Mesi fatturati", min_value=0.0, step=1.0, key="months")

with c2:
    st.subheader("Mercato e vendita energia")
    st.number_input("PUN (€/kWh)", min_value=0.0, step=0.001, format="%.5f", key="pun_eur_per_kwh")
    st.slider("Perdite di rete (Lambda)", min_value=0.0, max_value=0.30, step=0.005, format="%.3f", key="losses_lambda")
    st.number_input("Spread commerciale (€/kWh)", min_value=0.0, step=0.001, format="%.5f", key="spread_eur_per_kwh")
    st.number_input("Dispacciamento (PD) (€/kWh)", min_value=0.0, step=0.0001, format="%.6f", key="dispacciamento_pd_eur_per_kwh")

with c3:
    st.subheader("Vendita – quota fissa (€/POD/anno)")
    st.number_input("DISP BT quota fissa", min_value=0.0, step=0.10, format="%.4f", key="disp_bt_eur_per_pdp")
    st.number_input("CCV / CSV (quota fissa)", min_value=0.0, step=0.10, format="%.4f", key="ccv_eur_per_pdp")

st.divider()

c4, c5, c6 = st.columns(3)

with c4:
    st.subheader("Rete – variabile (€/kWh)")
    st.number_input("T3 variabile", min_value=0.0, step=0.0001, format="%.6f", key="t3_eur_per_kwh")
    st.number_input("UC3 variabile", min_value=0.0, step=0.0001, format="%.6f", key="uc3_eur_per_kwh")
    st.number_input("UC6 variabile", min_value=0.0, step=0.0001, format="%.6f", key="uc6_var_eur_per_kwh")

with c5:
    st.subheader("Rete – fissa e potenza")
    st.number_input("T1 fissa (€/POD/mese)", min_value=0.0, step=0.10, format="%.4f", key="t1_eur_per_pdp_month")
    st.number_input("T2 potenza (€/kW/mese)", min_value=0.0, step=0.01, format="%.4f", key="t2_eur_per_kw_month")
    st.number_input("UC6 potenza (€/kW/mese)", min_value=0.0, step=0.0001, format="%.6f", key="uc6_pow_eur_per_kw_month")

with c6:
    st.subheader("Oneri e imposte")
    st.number_input("ARIM (€/kWh)", min_value=0.0, step=0.0001, format="%.6f", key="arim_eur_per_kwh")
    st.number_input("ASOS (€/kWh)", min_value=0.0, step=0.0001, format="%.6f", key="asos_eur_per_kwh")
    st.number_input("Accise (€/kWh)", min_value=0.0, step=0.0001, format="%.6f", key="excise_eur_per_kwh")
    st.slider("IVA (aliquota)", min_value=0.0, max_value=0.30, step=0.01, format="%.2f", key="vat_rate")

#Block 9 — Build Inputs → compute → show results
# -----------------------------
# Block 9 — Compute and show results
# -----------------------------
inputs = Inputs(
    consumption_kwh=float(st.session_state["consumption_kwh"]),
    power_kw=float(st.session_state["power_kw"]),
    months=float(st.session_state["months"]),
    pun_eur_per_kwh=float(st.session_state["pun_eur_per_kwh"]),
    losses_lambda=float(st.session_state["losses_lambda"]),
    spread_eur_per_kwh=float(st.session_state["spread_eur_per_kwh"]),
    dispacciamento_pd_eur_per_kwh=float(st.session_state["dispacciamento_pd_eur_per_kwh"]),
    disp_bt_eur_per_pdp=float(st.session_state["disp_bt_eur_per_pdp"]),
    ccv_eur_per_pdp=float(st.session_state["ccv_eur_per_pdp"]),
    t3_eur_per_kwh=float(st.session_state["t3_eur_per_kwh"]),
    uc3_eur_per_kwh=float(st.session_state["uc3_eur_per_kwh"]),
    uc6_var_eur_per_kwh=float(st.session_state["uc6_var_eur_per_kwh"]),
    t1_eur_per_pdp_month=float(st.session_state["t1_eur_per_pdp_month"]),
    t2_eur_per_kw_month=float(st.session_state["t2_eur_per_kw_month"]),
    uc6_pow_eur_per_kw_month=float(st.session_state["uc6_pow_eur_per_kw_month"]),
    arim_eur_per_kwh=float(st.session_state["arim_eur_per_kwh"]),
    asos_eur_per_kwh=float(st.session_state["asos_eur_per_kwh"]),
    excise_eur_per_kwh=float(st.session_state["excise_eur_per_kwh"]),
    vat_rate=float(st.session_state["vat_rate"]),
)

result = compute_bill(inputs)
b = result["breakdown"]

st.subheader("Risultati")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Vendita energia", f"{b['Vendita energia (totale)']:.2f} €")
k2.metric("Rete", f"{b['Rete (totale)']:.2f} €")
k3.metric("Oneri di sistema", f"{b['Oneri di sistema']:.2f} €")
k4.metric("Totale bolletta", f"{b['TOTALE']:.2f} €")

breakdown_df = pd.DataFrame([{"Voce": k, "Importo (€)": v} for k, v in b.items()])
st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
breakdown_df.to_csv("check.csv")

with st.expander("Dettagli / Debug"):
    st.write("kWh effettivi (incluse perdite):", f"{result['intermediate']['effective_kwh_with_losses']:.2f}")
    st.write("Imponibile (prima IVA):", f"{result['intermediate']['taxable_base']:.2f} €")
    st.json(result["inputs"])


#Block 10 — Download edited offer CSV
# -----------------------------
# Block 10 — Export edited offer to CSV
# -----------------------------
def export_offer_df() -> pd.DataFrame:
    rows = []
    # Standard structure ITEM/VALUE
    rows.append({"ITEM": "provider", "VALUE": st.session_state["provider"]})
    rows.append({"ITEM": "offer", "VALUE": st.session_state["offer"]})

    # Save ALL keys (same ones you edit)
    for item in [
        "consumption_kwh","power_kw","months",
        "pun_eur_per_kwh","losses_lambda","spread_eur_per_kwh","dispacciamento_pd_eur_per_kwh",
        "disp_bt_eur_per_pdp","ccv_eur_per_pdp",
        "t3_eur_per_kwh","uc3_eur_per_kwh","uc6_var_eur_per_kwh",
        "t1_eur_per_pdp_month","t2_eur_per_kw_month","uc6_pow_eur_per_kw_month",
        "arim_eur_per_kwh","asos_eur_per_kwh","excise_eur_per_kwh","vat_rate"
    ]:
        rows.append({"ITEM": item, "VALUE": str(st.session_state[item])})

    return pd.DataFrame(rows)

export_name = f"{st.session_state['provider']}_{st.session_state['offer']}_edited.csv".replace(" ", "_")
csv_bytes = export_offer_df().to_csv(sep=";", index=False).encode("utf-8")

st.download_button(
    "Scarica offerta modificata (CSV)",
    data=csv_bytes,
    file_name=export_name,
    mime="text/csv",
)