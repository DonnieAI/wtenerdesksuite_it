import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go

# Optional project styling: keeps the page working even if utils are not available.
try:
    from utils import apply_style_and_logo
except Exception:
    apply_style_and_logo = None

try:
    from supporting_functions.editing_function import styled_scrollable_markdown
except Exception:
    styled_scrollable_markdown = None


st.set_page_config(page_title="ATECO 2025 Code Explorer", layout="wide")

if apply_style_and_logo:
    apply_style_and_logo()

palette_blue = [
    "#A7D5F2", "#94CCE8", "#81C3DD", "#6FBBD3", "#5DB2C8", "#A9DEF9",
]

palette_green = [
    "#6DC0B8", "#7DCFA8", "#8DDC99", "#9CE98A", "#ABF67B", "#C9F9D3", "#C4E17F",
]

palette_other = [
    "#FFD7BA", "#FFE29A", "#FFB6C1", "#D7BDE2", "#F6C6EA", "#F7D794", "#E4C1F9",
]


# ---------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_ateco_data(csv_path: str | Path) -> pd.DataFrame:
    """Load and normalize the official ATECO 2025 structure CSV."""
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV not found: {csv_path}. Put the file in ateco_codes/ or update CSV_PATH."
        )

    df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]

    required_cols = [
        "ORDINE_CODICE_ATECO_2025",
        "CODICE_ATECO_2025",
        "TITOLO_ITALIANO_ATECO_2025",
        "TITOLO_INGLESE_ATECO_2025",
        "TITOLO_TEDESCO_ATECO_2025",
        "GERARCHIA_ATECO_2025",
        "CODICE_PADRE_ATECO_2025",
        "GERARCHIA_PADRE_ATECO_2025",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in ATECO CSV: {missing}")

    # Clean strings and numeric sort keys.
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["GERARCHIA_ATECO_2025"] = pd.to_numeric(
        df["GERARCHIA_ATECO_2025"], errors="coerce"
    ).astype("Int64")
    df["GERARCHIA_PADRE_ATECO_2025"] = pd.to_numeric(
        df["GERARCHIA_PADRE_ATECO_2025"], errors="coerce"
    ).astype("Int64")
    df["ORDINE_CODICE_ATECO_2025"] = pd.to_numeric(
        df["ORDINE_CODICE_ATECO_2025"], errors="coerce"
    ).astype("Int64")

    df = df.sort_values("ORDINE_CODICE_ATECO_2025").reset_index(drop=True)

    # User-friendly labels for dropdown/search.
    df["LABEL_IT"] = (
        df["CODICE_ATECO_2025"].astype(str)
        + " — "
        + df["TITOLO_ITALIANO_ATECO_2025"].astype(str)
    )
    df["LABEL_EN"] = (
        df["CODICE_ATECO_2025"].astype(str)
        + " — "
        + df["TITOLO_INGLESE_ATECO_2025"].astype(str)
    )
    df["SEARCH_TEXT"] = (
        df["CODICE_ATECO_2025"].astype(str)
        + " "
        + df["TITOLO_ITALIANO_ATECO_2025"].astype(str)
        + " "
        + df["TITOLO_INGLESE_ATECO_2025"].astype(str)
        + " "
        + df["TITOLO_TEDESCO_ATECO_2025"].astype(str)
    ).str.lower()

    return df


def label_for(row: pd.Series, language: str) -> str:
    """Return a readable label for one ATECO row."""
    title_col = {
        "Italiano": "TITOLO_ITALIANO_ATECO_2025",
        "English": "TITOLO_INGLESE_ATECO_2025",
        "Deutsch": "TITOLO_TEDESCO_ATECO_2025",
    }[language]
    return f"{row['CODICE_ATECO_2025']} — {row[title_col]}"


def make_option_map(df: pd.DataFrame, language: str) -> dict[str, str]:
    """Map dropdown label -> ATECO code."""
    labels = {}
    for _, row in df.iterrows():
        label = label_for(row, language)
        labels[label] = row["CODICE_ATECO_2025"]
    return labels


def get_children(df: pd.DataFrame, parent_code: str | None, level: int) -> pd.DataFrame:
    """Return direct children for parent_code at the requested hierarchy level."""
    if parent_code is None:
        out = df[df["GERARCHIA_ATECO_2025"] == level]
    else:
        out = df[
            (df["CODICE_PADRE_ATECO_2025"] == parent_code)
            & (df["GERARCHIA_ATECO_2025"] == level)
        ]
    return out.sort_values("ORDINE_CODICE_ATECO_2025")


def get_ancestors(df: pd.DataFrame, code: str) -> pd.DataFrame:
    """Return root-to-selected hierarchy path for a selected ATECO code."""
    by_code = df.set_index("CODICE_ATECO_2025", drop=False)
    if code not in by_code.index:
        return pd.DataFrame(columns=df.columns)

    path_rows = []
    current = by_code.loc[code]

    # Limit loop to protect against malformed circular parent relationships.
    for _ in range(10):
        path_rows.append(current)
        parent_code = str(current.get("CODICE_PADRE_ATECO_2025", "")).strip()
        if not parent_code or parent_code not in by_code.index:
            break
        current = by_code.loc[parent_code]

    return pd.DataFrame(path_rows[::-1]).reset_index(drop=True)


def filter_results(df: pd.DataFrame, query: str, level: int | None = None) -> pd.DataFrame:
    """Filter ATECO table by code/title query and optional hierarchy level."""
    out = df.copy()
    if level is not None:
        out = out[out["GERARCHIA_ATECO_2025"] == level]
    if query:
        terms = query.lower().strip().split()
        mask = pd.Series(True, index=out.index)
        for term in terms:
            mask &= out["SEARCH_TEXT"].str.contains(term, regex=False, na=False)
        out = out[mask]
    return out.sort_values("ORDINE_CODICE_ATECO_2025")


def build_sunburst(df: pd.DataFrame, selected_code: str | None = None) -> go.Figure:
    """Build a compact Plotly sunburst chart for the selected branch or full level 1-3 tree."""
    if selected_code:
        selected_path = get_ancestors(df, selected_code)
        if selected_path.empty:
            chart_df = df[df["GERARCHIA_ATECO_2025"].isin([1, 2, 3])]
        else:
            root_code = selected_path.iloc[0]["CODICE_ATECO_2025"]
            chart_df = df[
                (
                    (df["CODICE_ATECO_2025"] == root_code)
                    | (df["CODICE_PADRE_ATECO_2025"] == root_code)
                    | (df["CODICE_ATECO_2025"].str.startswith(str(root_code), na=False))
                )
                & (df["GERARCHIA_ATECO_2025"].isin([1, 2, 3, 4]))
            ].copy()
    else:
        chart_df = df[df["GERARCHIA_ATECO_2025"].isin([1, 2, 3])].copy()

    chart_df["PARENT_FOR_CHART"] = chart_df["CODICE_PADRE_ATECO_2025"].fillna("")
    chart_df.loc[chart_df["GERARCHIA_ATECO_2025"] == 1, "PARENT_FOR_CHART"] = ""

    fig = go.Figure(
        go.Sunburst(
            ids=chart_df["CODICE_ATECO_2025"],
            labels=chart_df["CODICE_ATECO_2025"],
            parents=chart_df["PARENT_FOR_CHART"],
            hovertext=chart_df["TITOLO_ITALIANO_ATECO_2025"],
            hovertemplate="<b>%{label}</b><br>%{hovertext}<extra></extra>",
            maxdepth=4,
        )
    )
    fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=520)
    return fig


# Change this only if your folder/file name is different.
CSV_PATH = Path("ateco_codes") / "StrutturaATECO-2025-IT-EN-DE_ISPRA.csv"

st.title("🏭 ATECO 2025 Code Explorer")
st.caption("Interactive query page for the ATECO 2025 code structure.")

try:
    ateco = load_ateco_data(CSV_PATH)
except Exception as exc:
    st.error(str(exc))
    st.info(
        "Expected path: `ateco_codes/StrutturaATECO-2025-IT-EN-DE_ISPRA.csv` "
        "relative to the Streamlit app root."
    )
    st.stop()


# ---------------------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Controls")
    language = st.radio("Dropdown language", ["Italiano", "English", "Deutsch"], horizontal=False)
    mode = st.radio(
        "Selection mode",
        ["Cascading hierarchy", "Search all codes"],
        index=0,
    )

    st.divider()
    st.metric("Codes loaded", f"{len(ateco):,}".replace(",", "."))
    st.metric("Hierarchy levels", int(ateco["GERARCHIA_ATECO_2025"].max()))


selected_code = None

# ---------------------------------------------------------------------
# MAIN SELECTION AREA
# ---------------------------------------------------------------------
if mode == "Cascading hierarchy":
    st.subheader("Select by hierarchy")

    levels = sorted([int(x) for x in ateco["GERARCHIA_ATECO_2025"].dropna().unique()])
    current_parent = None
    selected_by_level: dict[int, str] = {}

    cols = st.columns(3)
    for i, level in enumerate(levels):
        children = get_children(ateco, current_parent, level)

        if children.empty:
            break

        options = make_option_map(children, language)
        col = cols[i % 3]

        with col:
            choice = st.selectbox(
                f"Level {level}",
                options=["—"] + list(options.keys()),
                key=f"ateco_level_{level}",
            )

        if choice == "—":
            break

        selected_by_level[level] = options[choice]
        current_parent = selected_by_level[level]
        selected_code = current_parent

else:
    st.subheader("Search all codes")

    c1, c2 = st.columns([2, 1])
    with c1:
        query = st.text_input(
            "Search by code, Italian title, English title or German title",
            placeholder="Example: 49 transport, 01.11 cereali, software...",
        )
    with c2:
        level_filter_choice = st.selectbox(
            "Hierarchy level",
            ["All"] + [str(i) for i in sorted(ateco["GERARCHIA_ATECO_2025"].dropna().unique())],
        )

    level_filter = None if level_filter_choice == "All" else int(level_filter_choice)
    results = filter_results(ateco, query, level_filter).head(250)

    if results.empty:
        st.warning("No matching ATECO code found.")
    else:
        options = make_option_map(results, language)
        choice = st.selectbox(
            f"Matching codes ({len(results)} shown, max 250)",
            options=list(options.keys()),
        )
        selected_code = options[choice]


# ---------------------------------------------------------------------
# SELECTED CODE DETAILS
# ---------------------------------------------------------------------
st.divider()

if selected_code:
    selected = ateco.loc[ateco["CODICE_ATECO_2025"] == selected_code].iloc[0]
    path = get_ancestors(ateco, selected_code)

    left, right = st.columns([1.15, 0.85])

    with left:
        st.subheader("Selected ATECO code")
        st.markdown(f"### `{selected['CODICE_ATECO_2025']}`")
        st.write(f"**Italiano:** {selected['TITOLO_ITALIANO_ATECO_2025']}")
        st.write(f"**English:** {selected['TITOLO_INGLESE_ATECO_2025']}")
        st.write(f"**Deutsch:** {selected['TITOLO_TEDESCO_ATECO_2025']}")

        meta = pd.DataFrame(
            {
                "Field": [
                    "Hierarchy level",
                    "Parent code",
                    "Parent hierarchy level",
                    "Official order",
                ],
                "Value": [
                    selected["GERARCHIA_ATECO_2025"],
                    selected["CODICE_PADRE_ATECO_2025"] or "—",
                    selected["GERARCHIA_PADRE_ATECO_2025"] if pd.notna(selected["GERARCHIA_PADRE_ATECO_2025"]) else "—",
                    selected["ORDINE_CODICE_ATECO_2025"],
                ],
            }
        )
        st.dataframe(meta, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Hierarchy path")
        path_view = path[
            [
                "GERARCHIA_ATECO_2025",
                "CODICE_ATECO_2025",
                "TITOLO_ITALIANO_ATECO_2025",
                "TITOLO_INGLESE_ATECO_2025",
            ]
        ].rename(
            columns={
                "GERARCHIA_ATECO_2025": "Level",
                "CODICE_ATECO_2025": "Code",
                "TITOLO_ITALIANO_ATECO_2025": "Italian title",
                "TITOLO_INGLESE_ATECO_2025": "English title",
            }
        )
        st.dataframe(path_view, use_container_width=True, hide_index=True)

    children = ateco[ateco["CODICE_PADRE_ATECO_2025"] == selected_code].copy()
    if not children.empty:
        st.subheader("Direct child codes")
        child_view = children[
            [
                "CODICE_ATECO_2025",
                "TITOLO_ITALIANO_ATECO_2025",
                "TITOLO_INGLESE_ATECO_2025",
                "GERARCHIA_ATECO_2025",
            ]
        ].rename(
            columns={
                "CODICE_ATECO_2025": "Code",
                "TITOLO_ITALIANO_ATECO_2025": "Italian title",
                "TITOLO_INGLESE_ATECO_2025": "English title",
                "GERARCHIA_ATECO_2025": "Level",
            }
        )
        st.dataframe(child_view, use_container_width=True, hide_index=True)
    else:
        st.info("This code has no direct child codes in the CSV.")

    with st.expander("Plotly hierarchy visualisation", expanded=False):
        st.plotly_chart(build_sunburst(ateco, selected_code), use_container_width=True)

else:
    st.info("Select an ATECO code from the dropdowns or search box to see details.")
    with st.expander("Full high-level structure", expanded=True):
        st.plotly_chart(build_sunburst(ateco), use_container_width=True)


# ---------------------------------------------------------------------
# FULL TABLE / DOWNLOAD
# ---------------------------------------------------------------------
with st.expander("Browse full ATECO table"):
    table = ateco[
        [
            "ORDINE_CODICE_ATECO_2025",
            "GERARCHIA_ATECO_2025",
            "CODICE_ATECO_2025",
            "TITOLO_ITALIANO_ATECO_2025",
            "TITOLO_INGLESE_ATECO_2025",
            "TITOLO_TEDESCO_ATECO_2025",
            "CODICE_PADRE_ATECO_2025",
        ]
    ].rename(
        columns={
            "ORDINE_CODICE_ATECO_2025": "Order",
            "GERARCHIA_ATECO_2025": "Level",
            "CODICE_ATECO_2025": "Code",
            "TITOLO_ITALIANO_ATECO_2025": "Italian title",
            "TITOLO_INGLESE_ATECO_2025": "English title",
            "TITOLO_TEDESCO_ATECO_2025": "German title",
            "CODICE_PADRE_ATECO_2025": "Parent code",
        }
    )
    st.dataframe(table, use_container_width=True, hide_index=True)

    csv_bytes = table.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download filtered/display table as CSV",
        data=csv_bytes,
        file_name="ateco_2025_structure_export.csv",
        mime="text/csv",
    )