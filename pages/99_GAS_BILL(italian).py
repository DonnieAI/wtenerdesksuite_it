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


st.set_page_config(page_title="Bolletta gas – trasporto e gestione contatore", layout="wide")
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

# =========================================================
# Helpers
# =========================================================
def read_tariff_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_meter_class_label(total_gas_smc: float) -> str:
    # adattalo se vuoi usare una vera classe contatore e non la soglia consumo
    if total_gas_smc <= 6:
        return "A_leq_G6"
    elif total_gas_smc <= 40:
        return "B_G6_to_G40"
    return "C_gt_G40"


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

    raise ValueError(f"Nessuna fascia trovata per total_gas_smc={total_gas_smc}")


def get_defaults_from_json(tariff: dict, total_gas_smc: float) -> dict:
    meter_class = get_meter_class_label(total_gas_smc)
    bracket = get_consumption_bracket(total_gas_smc, tariff)
    fixed = tariff["fixed_components_eur_per_year"]

    return {
        "classe_misuratore": meter_class,
        "ambito": tariff["metadata"]["ambito"]["name"],
        "qf_dis_eur_year": fixed["distribution_qf_dis_t1"][meter_class],
        "qf_mis_eur_year": fixed["measurement_qf_mis_t1"][meter_class],
        "qf_cot_eur_year": fixed["commercialization_qf_cot_t1"][meter_class],
        "t3_dis_ceur_smc": bracket.get("t3_dis", 0.0),
        "ug1_ceur_smc": bracket.get("ug1", 0.0),
        "ug2c_ceur_smc": bracket.get("ug2c", 0.0),
        "ug3int_ceur_smc": bracket.get("ug3int", 0.0),
        "ug3ui_ceur_smc": bracket.get("ug3ui", 0.0),
        "ug3ft_ceur_smc": bracket.get("ug3ft", 0.0),
        "gs_ceur_smc": bracket.get("gs", 0.0),
        "re_pre2023_ceur_smc": bracket.get("re_pre2023", 0.0),
        "rs_ceur_smc": bracket.get("rs", 0.0),
        "vr_ceur_smc": bracket.get("vr", 0.0),
        "st_ceur_smc": bracket.get("st", 0.0),
        "fascia_da_smc": bracket.get("from_smc"),
        "fascia_a_smc": bracket.get("to_smc"),
    }


def init_state(tariff: dict) -> None:
    if "gas_bill_initialized" not in st.session_state:
        st.session_state["provider"] = "ARERA"
        st.session_state["offer"] = "Tariffa distribuzione gas"
        st.session_state["months"] = 12.0
        st.session_state["total_gas_smc"] = 250000.0

        defaults = get_defaults_from_json(tariff, st.session_state["total_gas_smc"])
        for k, v in defaults.items():
            st.session_state[k] = v

        st.session_state["gas_bill_initialized"] = True


def reload_defaults_from_consumption(tariff: dict) -> None:
    total_gas_smc = float(st.session_state["total_gas_smc"])
    defaults = get_defaults_from_json(tariff, total_gas_smc)

    for k, v in defaults.items():
        st.session_state[k] = v


def on_total_gas_change() -> None:
    reload_defaults_from_consumption(st.session_state["tariff_data"])


@dataclass
class Inputs:
    provider: str
    offer: str
    months: float
    total_gas_smc: float
    classe_misuratore: str
    ambito: str

    qf_dis_eur_year: float
    qf_mis_eur_year: float
    qf_cot_eur_year: float

    t3_dis_ceur_smc: float
    ug1_ceur_smc: float
    ug2c_ceur_smc: float
    ug3int_ceur_smc: float
    ug3ui_ceur_smc: float
    ug3ft_ceur_smc: float
    gs_ceur_smc: float
    re_pre2023_ceur_smc: float
    rs_ceur_smc: float
    vr_ceur_smc: float
    st_ceur_smc: float


def compute_gas_distribution_bill(i: Inputs) -> Dict[str, Any]:
    # quote fisse annuali riproporzionate ai mesi
    quota_fissa_distribuzione = i.qf_dis_eur_year * i.months / 12.0
    quota_fissa_misura = i.qf_mis_eur_year * i.months / 12.0
    quota_fissa_commercializzazione = i.qf_cot_eur_year * i.months / 12.0

    quota_fissa_totale = (
        quota_fissa_distribuzione
        + quota_fissa_misura
        + quota_fissa_commercializzazione
    )

    # componenti variabili: il JSON è in c€/Smc -> converto in €/Smc dividendo per 100
    t3_dis_eur = i.total_gas_smc * i.t3_dis_ceur_smc / 100.0
    ug1_eur = i.total_gas_smc * i.ug1_ceur_smc / 100.0
    ug2c_eur = i.total_gas_smc * i.ug2c_ceur_smc / 100.0
    ug3int_eur = i.total_gas_smc * i.ug3int_ceur_smc / 100.0
    ug3ui_eur = i.total_gas_smc * i.ug3ui_ceur_smc / 100.0
    ug3ft_eur = i.total_gas_smc * i.ug3ft_ceur_smc / 100.0
    gs_eur = i.total_gas_smc * i.gs_ceur_smc / 100.0
    re_pre2023_eur = i.total_gas_smc * i.re_pre2023_ceur_smc / 100.0
    rs_eur = i.total_gas_smc * i.rs_ceur_smc / 100.0
    vr_eur = i.total_gas_smc * i.vr_ceur_smc / 100.0
    st_eur = i.total_gas_smc * i.st_ceur_smc / 100.0

    quota_variabile_totale = (
        t3_dis_eur
        + ug1_eur
        + ug2c_eur
        + ug3int_eur
        + ug3ui_eur
        + ug3ft_eur
        + gs_eur
        + re_pre2023_eur
        + rs_eur
        + vr_eur
        + st_eur
    )

    totale_trasporto_gestione_contatore = quota_fissa_totale + quota_variabile_totale

    breakdown_fisso = {
        "Quota fissa distribuzione": quota_fissa_distribuzione,
        "Quota fissa misura": quota_fissa_misura,
        "Quota fissa commercializzazione": quota_fissa_commercializzazione,
        "Totale quota fissa": quota_fissa_totale,
    }

    breakdown_variabile = {
        "T3 distribuzione": t3_dis_eur,
        "UG1": ug1_eur,
        "UG2c": ug2c_eur,
        "UG3INT": ug3int_eur,
        "UG3UI": ug3ui_eur,
        "UG3FT": ug3ft_eur,
        "GS": gs_eur,
        "RE pre 2023": re_pre2023_eur,
        "RS": rs_eur,
        "VR": vr_eur,
        "ST": st_eur,
        "Totale quota variabile": quota_variabile_totale,
    }

    riepilogo = {
        "Totale quota fissa": quota_fissa_totale,
        "Totale quota variabile": quota_variabile_totale,
        "Totale trasporto e gestione contatore": totale_trasporto_gestione_contatore,
    }

    return {
        "breakdown_fisso": breakdown_fisso,
        "breakdown_variabile": breakdown_variabile,
        "riepilogo": riepilogo,
        "inputs": asdict(i),
    }


# =========================================================
# Load JSON
# =========================================================
JSON_PATH = Path("italy_gas_distribution_tariff_q4_2025_ambito2.json")

if not JSON_PATH.exists():
    st.error("File JSON non trovato nella stessa cartella della pagina.")
    st.stop()

tariff = read_tariff_json(JSON_PATH)
st.session_state["tariff_data"] = tariff

init_state(tariff)


# =========================================================
# Sidebar
# =========================================================
with st.sidebar:
    st.header("Tariffa caricata")
    st.success(JSON_PATH.name)
    st.write("Ambito:", tariff["metadata"]["ambito"]["name"])
    st.write("Validità:", f"{tariff['metadata']['valid_from']} → {tariff['metadata']['valid_to']}")

    if st.button("Ricarica valori default dal JSON"):
        reload_defaults_from_consumption(tariff)
        st.rerun()


# =========================================================
# Title
# =========================================================
st.title("Bolletta gas – Trasporto e gestione del contatore")
st.caption("Pagina parametrica alimentata da file JSON tariffario")


# =========================================================
# Dati generali
# =========================================================
st.subheader("Dati generali")

g1, g2, g3, g4 = st.columns(4)
with g1:
    provider = st.text_input("Provider", key="provider")
with g2:
    offer = st.text_input("Offerta", key="offer")
with g3:
    ambito = st.text_input("Ambito", value=st.session_state["ambito"], disabled=True)
with g4:
    classe_misuratore = st.text_input(
        "Classe misuratore",
        value=st.session_state["classe_misuratore"],
        disabled=True
    )

g5, g6 = st.columns(2)
with g5:
    total_gas_smc = st.number_input(
        "Consumo annuo [Smc]",
        min_value=0.0,
        step=100.0,
        key="total_gas_smc",
        on_change=on_total_gas_change
    )
with g6:
    months = st.number_input(
        "Mesi fatturati",
        min_value=0.0,
        step=1.0,
        key="months"
    )

f1, f2 = st.columns(2)
with f1:
    st.text_input(
        "Fascia consumo da [Smc]",
        value=str(st.session_state["fascia_da_smc"]),
        disabled=True
    )
with f2:
    fascia_a = st.session_state["fascia_a_smc"]
    st.text_input(
        "Fascia consumo a [Smc]",
        value="oltre" if fascia_a is None else str(fascia_a),
        disabled=True
    )

st.divider()


# =========================================================
# Parametri tariffari
# =========================================================
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("Quote fisse [€/anno]")
    qf_dis_eur_year = st.number_input(
        "QF distribuzione",
        step=0.01,
        format="%.2f",
        key="qf_dis_eur_year"
    )
    qf_mis_eur_year = st.number_input(
        "QF misura",
        step=0.01,
        format="%.2f",
        key="qf_mis_eur_year"
    )
    qf_cot_eur_year = st.number_input(
        "QF commercializzazione",
        step=0.01,
        format="%.2f",
        key="qf_cot_eur_year"
    )

with c2:
    st.subheader("Componenti variabili [c€/Smc]")
    t3_dis_ceur_smc = st.number_input(
        "T3 distribuzione",
        step=0.0001,
        format="%.4f",
        key="t3_dis_ceur_smc"
    )
    ug1_ceur_smc = st.number_input(
        "UG1",
        step=0.0001,
        format="%.4f",
        key="ug1_ceur_smc"
    )
    ug2c_ceur_smc = st.number_input(
        "UG2c",
        step=0.0001,
        format="%.4f",
        key="ug2c_ceur_smc"
    )
    ug3int_ceur_smc = st.number_input(
        "UG3INT",
        step=0.0001,
        format="%.4f",
        key="ug3int_ceur_smc"
    )
    ug3ui_ceur_smc = st.number_input(
        "UG3UI",
        step=0.0001,
        format="%.4f",
        key="ug3ui_ceur_smc"
    )
    ug3ft_ceur_smc = st.number_input(
        "UG3FT",
        step=0.0001,
        format="%.4f",
        key="ug3ft_ceur_smc"
    )

with c3:
    st.subheader("Altre componenti variabili [c€/Smc]")
    gs_ceur_smc = st.number_input(
        "GS",
        step=0.0001,
        format="%.4f",
        key="gs_ceur_smc"
    )
    re_pre2023_ceur_smc = st.number_input(
        "RE pre 2023",
        step=0.0001,
        format="%.4f",
        key="re_pre2023_ceur_smc"
    )
    rs_ceur_smc = st.number_input(
        "RS",
        step=0.0001,
        format="%.4f",
        key="rs_ceur_smc"
    )
    vr_ceur_smc = st.number_input(
        "VR",
        step=0.0001,
        format="%.4f",
        key="vr_ceur_smc"
    )
    st_ceur_smc = st.number_input(
        "ST",
        step=0.0001,
        format="%.4f",
        key="st_ceur_smc"
    )


# =========================================================
# Inputs object
# =========================================================
inputs = Inputs(
    provider=provider,
    offer=offer,
    months=float(months),
    total_gas_smc=float(total_gas_smc),
    classe_misuratore=st.session_state["classe_misuratore"],
    ambito=st.session_state["ambito"],

    qf_dis_eur_year=float(qf_dis_eur_year),
    qf_mis_eur_year=float(qf_mis_eur_year),
    qf_cot_eur_year=float(qf_cot_eur_year),

    t3_dis_ceur_smc=float(t3_dis_ceur_smc),
    ug1_ceur_smc=float(ug1_ceur_smc),
    ug2c_ceur_smc=float(ug2c_ceur_smc),
    ug3int_ceur_smc=float(ug3int_ceur_smc),
    ug3ui_ceur_smc=float(ug3ui_ceur_smc),
    ug3ft_ceur_smc=float(ug3ft_ceur_smc),
    gs_ceur_smc=float(gs_ceur_smc),
    re_pre2023_ceur_smc=float(re_pre2023_ceur_smc),
    rs_ceur_smc=float(rs_ceur_smc),
    vr_ceur_smc=float(vr_ceur_smc),
    st_ceur_smc=float(st_ceur_smc),
)

result = compute_gas_distribution_bill(inputs)


# =========================================================
# Results
# =========================================================
st.divider()
st.subheader("Risultati")

r1, r2, r3 = st.columns(3)
r1.metric("Totale quota fissa", f"{result['riepilogo']['Totale quota fissa']:,.2f} €")
r2.metric("Totale quota variabile", f"{result['riepilogo']['Totale quota variabile']:,.2f} €")
r3.metric(
    "Totale trasporto e gestione contatore",
    f"{result['riepilogo']['Totale trasporto e gestione contatore']:,.2f} €"
)

st.markdown("### Quota fissa")
df_fisso = pd.DataFrame(
    [{"Voce": k, "Importo [€]": v} for k, v in result["breakdown_fisso"].items()]
)
st.dataframe(
    df_fisso.style.format({"Importo [€]": "{:,.2f}"}),
    use_container_width=True,
    hide_index=True
)

st.markdown("### Quota variabile")
df_variabile = pd.DataFrame(
    [{"Voce": k, "Importo [€]": v} for k, v in result["breakdown_variabile"].items()]
)
st.dataframe(
    df_variabile.style.format({"Importo [€]": "{:,.2f}"}),
    use_container_width=True,
    hide_index=True
)

st.markdown("### Riepilogo")
df_riepilogo = pd.DataFrame(
    [{"Voce": k, "Importo [€]": v} for k, v in result["riepilogo"].items()]
)
st.dataframe(
    df_riepilogo.style.format({"Importo [€]": "{:,.2f}"}),
    use_container_width=True,
    hide_index=True
)

with st.expander("Mostra input attivi"):
    st.json(result["inputs"])