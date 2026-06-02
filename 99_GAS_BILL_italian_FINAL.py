from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    from utils import apply_style_and_logo
except Exception:
    def apply_style_and_logo() -> None:
        return None


st.set_page_config(page_title="Gas Bill Analyzer", layout="wide")
apply_style_and_logo()


# =========================================================
# Folders
# =========================================================
COMMERCIAL_DIRS = [
    Path("bollette") / "gas" / "offerte",
    Path("bollette") / "gas",
    Path("."),
]

REGULATED_DIRS = [
    Path("bollette") / "gas" / "arera",
    Path("bollette") / "gas",
    Path("."),
]

SYSTEM_CHARGES_DIRS = [
    Path("bollette") / "gas" / "oneri",
    Path("bollette") / "gas" / "arera_oneri",
    Path("bollette") / "gas",
    Path("."),
]


# =========================================================
# Basic helpers
# =========================================================
def read_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return default if value is None else float(value)
    except Exception:
        return default


def discover_json_files(folders: list[Path]) -> list[Path]:
    files: list[Path] = []
    seen: set[str] = set()

    for folder in folders:
        if folder.exists() and folder.is_dir():
            for file in sorted(folder.glob("*.json")):
                key = str(file.resolve())
                if key not in seen:
                    seen.add(key)
                    files.append(file)

    return files


def format_eur(value: Any) -> str:
    """Euro values without decimals and without thousands separator."""
    return f"{safe_float(value):.0f} €"


def format_eur_table(value: Any) -> str:
    """Table values without decimals and without thousands separator."""
    return f"{safe_float(value):.0f}"


def format_smc(value: Any) -> str:
    """Smc values without thousands separator. Dot is reserved for decimals."""
    if value is None:
        return "oltre"
    return f"{safe_float(value):.0f}"


def format_rate(value: Any, decimals: int = 6) -> str:
    """Unit rates with decimal point."""
    return f"{safe_float(value):.{decimals}f}"


def money_df(items: dict[str, float]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"Voce": key, "Importo [€]": value} for key, value in items.items()]
    )


def in_consumption_range(row: dict[str, Any], annual_consumption_smc: float) -> bool:
    lower = safe_float(row.get("from_smc"), 0.0)
    upper = row.get("to_smc")

    if upper is None:
        return annual_consumption_smc >= lower

    return lower <= annual_consumption_smc <= safe_float(upper)


# =========================================================
# JSON classification
# =========================================================
def classify_json(path: Path) -> str:
    try:
        data = read_json(path)
    except Exception:
        return "unknown"

    metadata = data.get("metadata", {}) or {}
    json_type = str(metadata.get("json_type", "")).lower()

    if json_type == "gas_commercial_offer":
        return "commercial"

    if json_type == "gas_regulated_charges":
        return "regulated"

    if json_type == "gas_system_charges":
        return "system"

    if "system_variable_charges_ceur_per_smc_by_annual_consumption" in data:
        return "system"

    if "commercial_components" in data and "offer" in data and "seller" in data:
        return "commercial"

    if "fixed_charges_eur_per_year_by_meter_class" in data:
        return "regulated"

    return "unknown"


# =========================================================
# Commercial offer helpers
# =========================================================
def offer_identity(data: dict[str, Any]) -> dict[str, Any]:
    seller = data.get("seller", {}) or {}
    offer = data.get("offer", {}) or {}
    metadata = data.get("metadata", {}) or {}

    return {
        "seller_name": seller.get("name", "N/D"),
        "offer_name": offer.get("name") or metadata.get("service", "N/D"),
        "offer_code": offer.get("code", "N/D"),
        "valid_from": offer.get("valid_from") or metadata.get("valid_from", "N/D"),
        "valid_to": offer.get("valid_to") or metadata.get("valid_to", "N/D"),
    }


def commercial_components(data: dict[str, Any]) -> dict[str, Any]:
    components = data.get("commercial_components", {}) or {}
    commodity = components.get("commodity_price", {}) or {}
    spread = commodity.get("spread", {}) or {}
    fixed_fee = components.get("fixed_fee", {}) or {}

    return {
        "formula": commodity.get("formula", "PSV-DA + spread"),
        "spread_eur_smc": safe_float(spread.get("value"), 0.0),
        "fixed_fee_eur_year": safe_float(fixed_fee.get("value"), 0.0),
    }


def offer_limit(data: dict[str, Any]) -> float | None:
    offer = data.get("offer", {}) or {}
    eligibility = offer.get("eligibility", {}) or {}
    value = eligibility.get("annual_consumption_limit_smc")
    return None if value is None else safe_float(value)


def evaluate_offer_limit(data: dict[str, Any], annual_consumption_smc: float) -> tuple[str, str]:
    max_smc = offer_limit(data)

    if max_smc is None:
        return "info", "Nessun limite massimo di consumo indicato nel JSON commerciale."

    if annual_consumption_smc <= max_smc:
        return (
            "success",
            f"Consumo entro limite offerta: {format_smc(annual_consumption_smc)} ≤ {format_smc(max_smc)} Smc/anno.",
        )

    return (
        "error",
        f"ATTENZIONE: consumo superiore al limite offerta: {format_smc(annual_consumption_smc)} > {format_smc(max_smc)} Smc/anno.",
    )


# =========================================================
# Regulated ARERA distribution/metering helpers
# =========================================================
def zone_name(data: dict[str, Any]) -> str:
    metadata = data.get("metadata", {}) or {}
    zone = metadata.get("tariff_zone") or metadata.get("ambito") or {}

    if isinstance(zone, dict):
        code = zone.get("code", "")
        name = zone.get("name", "N/D")
        return f"Ambito {code} - {name}" if code != "" else name

    return str(zone) if zone else "N/D"


def zone_regions(data: dict[str, Any]) -> list[str]:
    metadata = data.get("metadata", {}) or {}
    zone = metadata.get("tariff_zone") or metadata.get("ambito") or {}

    if isinstance(zone, dict):
        return zone.get("regions", []) or []

    return []


def meter_classes(data: dict[str, Any]) -> dict[str, str]:
    return data.get("meter_classes", {}) or {
        "A_leq_G6": "GdM ≤ G6",
        "B_G6_to_G40": "G6 < GdM ≤ G40",
        "C_gt_G40": "GdM > G40",
    }


def fixed_block(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("fixed_charges_eur_per_year_by_meter_class", {}) or {}


def fixed_value(data: dict[str, Any], component: str, meter_class: str) -> float:
    values = fixed_block(data).get(component, 0.0)
    if isinstance(values, dict):
        return safe_float(values.get(meter_class), 0.0)
    return safe_float(values, 0.0)


def variable_brackets(data: dict[str, Any]) -> list[dict[str, Any]]:
    return data.get("variable_charges_ceur_per_smc_by_annual_consumption", []) or []


def selected_bracket(data: dict[str, Any], annual_consumption_smc: float) -> dict[str, Any]:
    for bracket in variable_brackets(data):
        if in_consumption_range(bracket, annual_consumption_smc):
            return bracket

    return {}


def default_vat_rate(regulated: dict[str, Any]) -> float:
    taxes = regulated.get("taxes", {}) or {}
    vat = taxes.get("vat", {}) or {}
    return safe_float(vat.get("default_rate"), 0.22)


# =========================================================
# System charges helpers
# =========================================================
def system_bracket(data: dict[str, Any], annual_consumption_smc: float) -> dict[str, Any]:
    brackets = data.get("system_variable_charges_ceur_per_smc_by_annual_consumption", []) or []

    for bracket in brackets:
        if in_consumption_range(bracket, annual_consumption_smc):
            return bracket

    return {}


def system_value(data: dict[str, Any], annual_consumption_smc: float, key: str) -> float:
    bracket = system_bracket(data, annual_consumption_smc)
    return safe_float(bracket.get(key), 0.0)


def system_fixed_value(data: dict[str, Any], key: str) -> float:
    fixed = data.get("system_fixed_charges_eur_per_year", {}) or {}
    return safe_float(fixed.get(key), 0.0)


def re_classes(data: dict[str, Any]) -> dict[str, Any]:
    re_block = data.get("re_component_281_2025_r_com", {}) or {}
    return re_block.get("classes", {}) or {}


def default_re_class(data: dict[str, Any]) -> str:
    re_block = data.get("re_component_281_2025_r_com", {}) or {}
    return str(re_block.get("default_class") or "CLASSE 0")


def re_value(data: dict[str, Any], re_class: str, annual_consumption_smc: float) -> float:
    classes = re_classes(data)
    class_data = classes.get(re_class, {}) or {}

    for bracket in class_data.get("brackets", []) or []:
        if in_consumption_range(bracket, annual_consumption_smc):
            return safe_float(bracket.get("re_overall_ceur_smc"), 0.0)

    return 0.0


def re_active_bracket(data: dict[str, Any], re_class: str, annual_consumption_smc: float) -> dict[str, Any]:
    classes = re_classes(data)
    class_data = classes.get(re_class, {}) or {}

    for bracket in class_data.get("brackets", []) or []:
        if in_consumption_range(bracket, annual_consumption_smc):
            return bracket

    return {}


# =========================================================
# Labels
# =========================================================
def label_for(path: Path) -> str:
    try:
        data = read_json(path)
        kind = classify_json(path)

        if kind == "commercial":
            identity = offer_identity(data)
            return " | ".join(
                x for x in [
                    identity["seller_name"],
                    identity["offer_name"],
                    identity["offer_code"],
                ]
                if x and x != "N/D"
            )

        if kind == "regulated":
            metadata = data.get("metadata", {}) or {}
            valid_from = metadata.get("valid_from", "")
            valid_to = metadata.get("valid_to", "")
            return " | ".join(
                x for x in [zone_name(data), f"{valid_from} → {valid_to}"]
                if x.strip(" →")
            )

        if kind == "system":
            metadata = data.get("metadata", {}) or {}
            service = metadata.get("service", "Oneri generali gas")
            valid_from = metadata.get("valid_from", "")
            valid_to = metadata.get("valid_to", "")
            return " | ".join(
                x for x in [service, f"{valid_from} → {valid_to}"]
                if x.strip(" →")
            )

    except Exception:
        pass

    return path.name


# =========================================================
# Calculation
# =========================================================
def compute_bill(i: dict[str, float | bool]) -> dict[str, Any]:
    smc = safe_float(i["annual_consumption_smc"])

    materia = {
        "PSV-DA": smc * safe_float(i["psv_da_eur_smc"]),
        "Spread commerciale": smc * safe_float(i["spread_eur_smc"]),
        "Quota fissa commerciale": safe_float(i["commercial_fixed_fee_eur_year"]),
    }
    materia["Totale materia gas naturale"] = sum(materia.values())

    trasporto = {
        "Distribuzione T1": safe_float(i["qf_distribution_t1_eur_year"]),
        "Misura T1": safe_float(i["qf_measurement_t1_eur_year"]),
        "Commercializzazione T1": safe_float(i["qf_commercialization_cot_t1_eur_year"]),
        "ST fisso": safe_float(i["st_fixed_eur_year"]),
        "VR fisso": safe_float(i["vr_fixed_eur_year"]),
        "CE fisso": safe_float(i["ce_fixed_eur_year"]),
        "T3 distribuzione": smc * safe_float(i["t3_dis_ceur_smc"]) / 100.0,
    }
    trasporto["Totale trasporto e gestione contatore"] = sum(trasporto.values())

    oneri = {
        "UG1": smc * safe_float(i["ug1_ceur_smc"]) / 100.0,
        "RS": smc * safe_float(i["rs_ceur_smc"]) / 100.0,
        "UG2 fisso": safe_float(i["ug2_fixed_eur_year"]),
        "UG2c": smc * safe_float(i["ug2c_ceur_smc"]) / 100.0,
        "UG3INT": smc * safe_float(i["ug3int_ceur_smc"]) / 100.0,
        "UG3UI": smc * safe_float(i["ug3ui_ceur_smc"]) / 100.0,
        "UG3FT": smc * safe_float(i["ug3ft_ceur_smc"]) / 100.0,
        "GS": smc * safe_float(i["gs_ceur_smc"]) / 100.0,
        "RE": smc * safe_float(i["re_ceur_smc"]) / 100.0,
    }
    oneri["Totale oneri di sistema"] = sum(oneri.values())

    accisa = smc * safe_float(i["accisa_eur_smc"])
    addizionale = smc * safe_float(i["addizionale_regionale_eur_smc"])

    imponibile = (
        materia["Totale materia gas naturale"]
        + trasporto["Totale trasporto e gestione contatore"]
        + oneri["Totale oneri di sistema"]
        + accisa
        + addizionale
    )

    iva = imponibile * safe_float(i["vat_rate"]) if bool(i["include_vat"]) else 0.0

    imposte = {
        "Accisa": accisa,
        "Addizionale regionale": addizionale,
        "IVA": iva,
    }
    imposte["Totale imposte e IVA"] = sum(imposte.values())

    totale = imponibile + iva

    return {
        "sections": {
            "Spesa per la materia gas naturale": materia,
            "Spesa per il trasporto e la gestione del contatore": trasporto,
            "Spesa oneri di sistema": oneri,
            "Imposte e IVA": imposte,
        },
        "summary": {
            "Totale materia gas naturale": materia["Totale materia gas naturale"],
            "Totale trasporto e gestione contatore": trasporto["Totale trasporto e gestione contatore"],
            "Totale oneri di sistema": oneri["Totale oneri di sistema"],
            "Totale accise/addizionale prima IVA": accisa + addizionale,
            "IVA": iva,
            "Totale annuo stimato": totale,
            "Prezzo medio all-in EUR/Smc": totale / smc if smc else 0.0,
            "Prezzo materia gas EUR/Smc": safe_float(i["psv_da_eur_smc"]) + safe_float(i["spread_eur_smc"]),
        },
        "inputs": i,
    }


# =========================================================
# Load JSON files
# =========================================================
commercial_files = [p for p in discover_json_files(COMMERCIAL_DIRS) if classify_json(p) == "commercial"]
regulated_files = [p for p in discover_json_files(REGULATED_DIRS) if classify_json(p) == "regulated"]
system_files = [p for p in discover_json_files(SYSTEM_CHARGES_DIRS) if classify_json(p) == "system"]

if not commercial_files:
    st.error("Nessun JSON commerciale trovato.")
    st.stop()

if not regulated_files:
    st.error("Nessun JSON ARERA distribuzione/misura trovato.")
    st.stop()

if not system_files:
    st.error("Nessun JSON oneri generali trovato.")
    st.info("Inserisci il file `arera_gas_oneri_generali_variabili_2026_q1_FINAL.json` in `bollette/gas/oneri/`.")
    st.stop()

regulated_registry: list[dict[str, Any]] = []
for file in regulated_files:
    data = read_json(file)
    regulated_registry.append(
        {
            "path": file,
            "data": data,
            "zone": zone_name(data),
            "regions": zone_regions(data),
        }
    )

all_regions = sorted({region for item in regulated_registry for region in item["regions"]})

with st.sidebar:
    st.header("📂 File di input")

    commercial_options = {label_for(path): path for path in commercial_files}
    commercial_path = commercial_options[
        st.selectbox("1) JSON offerta commerciale", list(commercial_options.keys()))
    ]
    commercial_json = read_json(commercial_path)

    st.markdown("### 2) Zona tariffaria ARERA")
    region_choice = st.selectbox("Regione fornitura", ["Selezione manuale"] + all_regions)

    if region_choice == "Selezione manuale":
        matching_regulated = regulated_registry
    else:
        matching_regulated = [
            item for item in regulated_registry
            if region_choice in item["regions"]
        ]

    if not matching_regulated:
        st.error(f"Nessun JSON ARERA trovato per la regione: {region_choice}")
        st.stop()

    regulated_options = {
        f"{item['zone']} | {item['path'].name}": item
        for item in matching_regulated
    }
    regulated_item = regulated_options[
        st.selectbox("JSON ARERA distribuzione/misura", list(regulated_options.keys()))
    ]

    regulated_path = regulated_item["path"]
    regulated_json = regulated_item["data"]

    st.markdown("### 3) Oneri generali gas")
    system_options = {label_for(path): path for path in system_files}
    system_path = system_options[
        st.selectbox("JSON oneri generali", list(system_options.keys()))
    ]
    system_json = read_json(system_path)

    st.caption("La simulazione combina i tre JSON selezionati.")


# =========================================================
# Defaults
# =========================================================
identity = offer_identity(commercial_json)
commercial = commercial_components(commercial_json)
max_offer_smc = offer_limit(commercial_json)

defaults = commercial_json.get("calculator_defaults", {}) or {}
default_consumption = safe_float(
    defaults.get("annual_consumption_smc"),
    safe_float(max_offer_smc, 100000.0),
)
default_psv = safe_float(defaults.get("psv_da_eur_smc"), 0.493117)
default_meter = defaults.get("meter_class", "C_gt_G40")

classes = meter_classes(regulated_json)
class_keys = list(classes.keys())
default_meter_index = class_keys.index(default_meter) if default_meter in class_keys else len(class_keys) - 1

available_re_classes = re_classes(system_json)
available_re_class_keys = list(available_re_classes.keys())
default_re = default_re_class(system_json)
default_re_index = (
    available_re_class_keys.index(default_re)
    if default_re in available_re_class_keys
    else 0
)


# =========================================================
# Header
# =========================================================
st.title("🔥🧾 Gas Italian Bill Analyzer")
st.markdown(
    "[🔗 Fonte ARERA – Tariffe di distribuzione, misura e oneri generali]"
    "(https://www.arera.it/area-operatori/prezzi-e-tariffe/tariffe-di-distribuzione-misura-oneri-generali)"
)
st.caption("Calcolo annuo con JSON separati: offerta commerciale, tariffe ARERA per ambito e oneri generali.")

h1, h2, h3, h4 = st.columns(4)
with h1:
    st.caption("Venditore")
    st.write(identity["seller_name"])
with h2:
    st.caption("Offerta")
    st.write(identity["offer_name"])
with h3:
    st.caption("Validità")
    st.write(f"{identity['valid_from']} → {identity['valid_to']}")
with h4:
    st.caption("Limite offerta")
    if max_offer_smc is None:
        st.write("N/D")
    else:
        st.write(f"≤ {format_smc(max_offer_smc)} Smc/anno")

f1, f2, f3 = st.columns(3)
f1.info(f"**Commerciale:** `{commercial_path.name}`")
f2.info(f"**ARERA distribuzione/misura:** `{regulated_path.name}`")
f3.info(f"**Oneri generali:** `{system_path.name}`")
st.info(f"**Zona tariffaria:** {zone_name(regulated_json)}")

st.divider()


# =========================================================
# 1) Commercial and consumption profile
# =========================================================
st.markdown("## 📄 Offerta commerciale")
st.caption("Formula commerciale caricata")
st.write(commercial["formula"])

oc1, oc2 = st.columns(2)
with oc1:
    st.caption("Spread commerciale da offerta")
    st.write(f"{format_rate(commercial['spread_eur_smc'])} €/Smc")
with oc2:
    st.caption("Quota fissa commerciale da offerta")
    st.write(format_eur(commercial["fixed_fee_eur_year"]))

p1, p2, p3 = st.columns(3)
with p1:
    annual_consumption_smc = st.number_input(
        "Consumo annuo [Smc]",
        min_value=0.0,
        value=float(default_consumption),
        step=1000.0,
        format="%.0f",
    )
with p2:
    meter_class = st.selectbox(
        "Classe misuratore",
        class_keys,
        index=max(default_meter_index, 0),
        format_func=lambda key: f"{key} – {classes.get(key, key)}",
    )
with p3:
    include_vat = st.checkbox("Includi IVA", value=True)

severity, message = evaluate_offer_limit(commercial_json, annual_consumption_smc)
if severity == "success":
    st.success(message)
elif severity == "error":
    st.error(message)
else:
    st.info(message)

st.markdown("### Parametri materia gas naturale")

m1, m2, m3 = st.columns(3)
with m1:
    psv_da_eur_smc = st.number_input(
        "PSV-DA [€/Smc]",
        min_value=0.0,
        max_value=2.0,
        value=float(default_psv),
        step=0.001,
        format="%.6f",
    )
with m2:
    spread_eur_smc = st.number_input(
        "Spread commerciale [€/Smc]",
        value=float(commercial["spread_eur_smc"]),
        step=0.001,
        format="%.6f",
    )
with m3:
    commercial_fixed_fee_eur_year = st.number_input(
        "Quota fissa commerciale [€/anno]",
        value=float(commercial["fixed_fee_eur_year"]),
        step=1.0,
        format="%.0f",
    )

unit_price = psv_da_eur_smc + spread_eur_smc

u1, u2, u3 = st.columns(3)
with u1:
    st.caption("PSV-DA")
    st.write(f"{format_rate(psv_da_eur_smc)} €/Smc")
with u2:
    st.caption("Spread")
    st.write(f"{format_rate(spread_eur_smc)} €/Smc")
with u3:
    st.caption("Prezzo materia gas")
    st.write(f"{format_rate(unit_price)} €/Smc")

st.divider()


# =========================================================
# 2) Regulated components
# =========================================================
regulated_bracket = selected_bracket(regulated_json, annual_consumption_smc)
active_system_bracket = system_bracket(system_json, annual_consumption_smc)

st.markdown("## 🏛️ Componenti regolate ARERA")

b1, b2 = st.columns(2)
with b1:
    st.text_input(
        "Scaglione distribuzione ARERA da [Smc]",
        value=format_smc(regulated_bracket.get("from_smc")),
        disabled=True,
    )
with b2:
    st.text_input(
        "Scaglione distribuzione ARERA a [Smc]",
        value=format_smc(regulated_bracket.get("to_smc")),
        disabled=True,
    )

if active_system_bracket:
    st.caption(
        "Oneri generali caricati dal JSON oneri: GS, RS, UG1, UG2 fisso, UG2c, UG3INT, UG3UI, UG3FT e RE."
    )
else:
    st.warning("Nessuno scaglione oneri trovato nel JSON selezionato.")

q1, q2, q3 = st.columns(3)

with q1:
    st.markdown("### Quote fisse trasporto/contatore [€/anno]")
    qf_distribution_t1 = st.number_input(
        "Distribuzione T1 [€/PDR]",
        value=fixed_value(regulated_json, "qf_distribution_t1", meter_class),
        step=0.01,
        format="%.2f",
    )
    qf_measurement_t1 = st.number_input(
        "Misura T1 [€/PDR]",
        value=fixed_value(regulated_json, "qf_measurement_t1", meter_class),
        step=0.01,
        format="%.2f",
    )
    qf_commercialization_cot_t1 = st.number_input(
        "Commercializzazione T1 [€/PDR]",
        value=fixed_value(regulated_json, "qf_commercialization_cot_t1", meter_class),
        step=0.01,
        format="%.2f",
    )
    st_fixed = st.number_input(
        "ST fisso [€/PDR]",
        value=fixed_value(regulated_json, "st_fixed", meter_class),
        step=0.01,
        format="%.2f",
    )
    vr_fixed = st.number_input(
        "VR fisso [€/PDR]",
        value=fixed_value(regulated_json, "vr_fixed", meter_class),
        step=0.01,
        format="%.2f",
    )
    ce_fixed = st.number_input(
        "CE fisso [€/PDR]",
        value=fixed_value(regulated_json, "ce_fixed", meter_class),
        step=0.01,
        format="%.2f",
    )

with q2:
    st.markdown("### Quote energia trasporto [c€/Smc]")
    t3_dis = st.number_input(
        "T3 distribuzione",
        value=safe_float(regulated_bracket.get("t3_dis")),
        step=0.0001,
        format="%.4f",
    )

    st.markdown("### Oneri principali [c€/Smc]")
    ug1 = st.number_input(
        "UG1",
        value=system_value(system_json, annual_consumption_smc, "ug1_ceur_smc"),
        step=0.0001,
        format="%.4f",
    )
    rs = st.number_input(
        "RS",
        value=system_value(system_json, annual_consumption_smc, "rs_ceur_smc"),
        step=0.0001,
        format="%.4f",
    )
    gs = st.number_input(
        "GS",
        value=system_value(system_json, annual_consumption_smc, "gs_ceur_smc"),
        step=0.0001,
        format="%.4f",
    )

with q3:
    st.markdown("### Oneri UG2 / UG3 / RE")
    ug2_fixed = st.number_input(
        "UG2 fisso [€/anno]",
        value=system_fixed_value(system_json, "ug2_fixed_eur_year"),
        step=0.01,
        format="%.2f",
    )
    ug2c = st.number_input(
        "UG2c [c€/Smc]",
        value=system_value(system_json, annual_consumption_smc, "ug2c_ceur_smc"),
        step=0.0001,
        format="%.4f",
    )
    ug3int = st.number_input(
        "UG3INT [c€/Smc]",
        value=system_value(system_json, annual_consumption_smc, "ug3int_ceur_smc"),
        step=0.0001,
        format="%.4f",
    )
    ug3ui = st.number_input(
        "UG3UI [c€/Smc]",
        value=system_value(system_json, annual_consumption_smc, "ug3ui_ceur_smc"),
        step=0.0001,
        format="%.4f",
    )
    ug3ft = st.number_input(
        "UG3FT [c€/Smc]",
        value=system_value(system_json, annual_consumption_smc, "ug3ft_ceur_smc"),
        step=0.0001,
        format="%.4f",
    )

    if available_re_class_keys:
        re_class = st.selectbox(
            "Classe RE",
            available_re_class_keys,
            index=max(default_re_index, 0),
            format_func=lambda key: f"{key} – {(available_re_classes.get(key, {}) or {}).get('description_it', key)}",
        )
        re_default_value = re_value(system_json, re_class, annual_consumption_smc)
    else:
        re_class = "N/D"
        re_default_value = system_value(system_json, annual_consumption_smc, "re_pre2023_ceur_smc")

    re_ceur_smc = st.number_input(
        "RE [c€/Smc]",
        value=re_default_value,
        step=0.0001,
        format="%.4f",
        help="Valore caricato dal blocco RE del JSON oneri in base alla classe RE selezionata.",
    )

st.divider()


# =========================================================
# 3) Taxes
# =========================================================
st.markdown("## 🧾 Accise e imposte")

tax1, tax2, tax3 = st.columns(3)
with tax1:
    accisa_eur_smc = st.number_input(
        "Accisa uso non domestico [€/Smc]",
        value=0.012498,
        step=0.001,
        format="%.6f",
    )
with tax2:
    addizionale_regionale_eur_smc = st.number_input(
        "Addizionale regionale [€/Smc]",
        value=0.0,
        step=0.001,
        format="%.6f",
    )
with tax3:
    vat_rate = st.number_input(
        "IVA",
        min_value=0.0,
        max_value=1.0,
        value=default_vat_rate(regulated_json),
        step=0.01,
        format="%.2f",
        disabled=not include_vat,
    )

st.divider()


# =========================================================
# Compute
# =========================================================
inputs = {
    "annual_consumption_smc": float(annual_consumption_smc),
    "meter_class": meter_class,
    "re_class": re_class,
    "psv_da_eur_smc": float(psv_da_eur_smc),
    "spread_eur_smc": float(spread_eur_smc),
    "commercial_fixed_fee_eur_year": float(commercial_fixed_fee_eur_year),
    "qf_distribution_t1_eur_year": float(qf_distribution_t1),
    "qf_measurement_t1_eur_year": float(qf_measurement_t1),
    "qf_commercialization_cot_t1_eur_year": float(qf_commercialization_cot_t1),
    "st_fixed_eur_year": float(st_fixed),
    "vr_fixed_eur_year": float(vr_fixed),
    "ce_fixed_eur_year": float(ce_fixed),
    "t3_dis_ceur_smc": float(t3_dis),
    "ug1_ceur_smc": float(ug1),
    "rs_ceur_smc": float(rs),
    "ug2_fixed_eur_year": float(ug2_fixed),
    "ug2c_ceur_smc": float(ug2c),
    "ug3int_ceur_smc": float(ug3int),
    "ug3ui_ceur_smc": float(ug3ui),
    "ug3ft_ceur_smc": float(ug3ft),
    "gs_ceur_smc": float(gs),
    "re_ceur_smc": float(re_ceur_smc),
    "accisa_eur_smc": float(accisa_eur_smc),
    "addizionale_regionale_eur_smc": float(addizionale_regionale_eur_smc),
    "vat_rate": float(vat_rate),
    "include_vat": bool(include_vat),
}

result = compute_bill(inputs)


# =========================================================
# Results
# =========================================================
st.markdown("## 💶 Totale spesa annua")

s1, s2, s3, s4 = st.columns(4)
s1.metric("Totale annuo stimato", format_eur(result["summary"]["Totale annuo stimato"]))
s2.metric("Prezzo medio all-in", f"{format_rate(result['summary']['Prezzo medio all-in EUR/Smc'], 4)} €/Smc")
s3.metric("Prezzo materia gas", f"{format_rate(result['summary']['Prezzo materia gas EUR/Smc'], 4)} €/Smc")
s4.metric("Consumo annuo", f"{format_smc(annual_consumption_smc)} Smc")


# =========================================================
# Waterfall chart
# =========================================================
waterfall_items = [
    ("Materia gas naturale", result["summary"]["Totale materia gas naturale"]),
    ("Trasporto e gestione contatore", result["summary"]["Totale trasporto e gestione contatore"]),
    ("Oneri di sistema", result["summary"]["Totale oneri di sistema"]),
    ("Accise / addizionale", result["summary"]["Totale accise/addizionale prima IVA"]),
    ("IVA", result["summary"]["IVA"]),
]

waterfall_labels = [item[0] for item in waterfall_items] + ["Totale annuo"]
waterfall_values = [float(item[1]) for item in waterfall_items] + [float(result["summary"]["Totale annuo stimato"])]
waterfall_measures = ["relative"] * len(waterfall_items) + ["total"]

fig_waterfall = go.Figure(
    go.Waterfall(
        name="Bolletta gas annua",
        orientation="v",
        measure=waterfall_measures,
        x=waterfall_labels,
        y=waterfall_values,
        text=[f"{value:.0f} €" for value in waterfall_values],
        textposition="outside",
        connector={"line": {"width": 1}},
    )
)

fig_waterfall.update_layout(
    title="Composizione della bolletta annua",
    yaxis_title="Importo [€]",
    showlegend=False,
    height=520,
)

st.plotly_chart(fig_waterfall, use_container_width=True)


summary_df = pd.DataFrame(
    [
        {"Sezione": key, "Importo [€]": value}
        for key, value in result["summary"].items()
        if "EUR/Smc" not in key
    ]
)
st.dataframe(
    summary_df.style.format({"Importo [€]": format_eur_table}),
    use_container_width=True,
    hide_index=True,
)

for section_name, section in result["sections"].items():
    st.markdown(f"### {section_name}")
    df = money_df(section)
    st.dataframe(
        df.style.format({"Importo [€]": format_eur_table}),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("JSON/calcolo attivo"):
    st.json(
        {
            "commercial_json": str(commercial_path),
            "regulated_json": str(regulated_path),
            "system_charges_json": str(system_path),
            "active_regulated_bracket": regulated_bracket,
            "active_system_bracket": active_system_bracket,
            "active_re_bracket": re_active_bracket(system_json, re_class, annual_consumption_smc),
            "offer": identity,
            "inputs": inputs,
            "summary": result["summary"],
        }
    )

st.caption(
    "Nota: simulazione tecnico-economica. Per uso fiscale/fatturazione validare sempre valori ARERA, accise, addizionali e IVA applicabili."
)
