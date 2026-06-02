import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import mimetypes
import os

try:
    from utils import apply_style_and_logo
except Exception:
    apply_style_and_logo = None

try:
    from supporting_functions.editing_function import styled_scrollable_markdown
except Exception:
    styled_scrollable_markdown = None


# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------
st.set_page_config(page_title="Sources Repository", layout="wide")

if apply_style_and_logo:
    apply_style_and_logo()


# ------------------------------------------------------------
# Constants and styling
# ------------------------------------------------------------
APP_ROOT = Path.cwd()
SOURCES_DIR = APP_ROOT / "sources"

SUPPORTED_EXTENSIONS = {
    ".pdf": "PDF",
    ".docx": "Word",
    ".doc": "Word",
    ".xlsx": "Excel",
    ".xls": "Excel",
    ".csv": "CSV",
    ".pptx": "PowerPoint",
    ".ppt": "PowerPoint",
    ".txt": "Text",
    ".md": "Markdown",
    ".json": "JSON",
    ".zip": "ZIP",
}

palette_blue = [
    "#A7D5F2",
    "#94CCE8",
    "#81C3DD",
    "#6FBBD3",
    "#5DB2C8",
    "#A9DEF9",
]

palette_green = [
    "#6DC0B8",
    "#7DCFA8",
    "#8DDC99",
    "#9CE98A",
    "#ABF67B",
    "#C9F9D3",
    "#C4E17F",
]

palette_other = [
    "#FFD7BA",
    "#FFE29A",
    "#FFB6C1",
    "#D7BDE2",
    "#F6C6EA",
    "#F7D794",
    "#E4C1F9",
]

st.markdown(
    """
    <style>
    .repo-card {
        border: 1px solid rgba(49, 51, 63, 0.16);
        border-radius: 16px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.8rem;
        background: rgba(255, 255, 255, 0.72);
        box-shadow: 0 1px 8px rgba(0,0,0,0.035);
    }
    .repo-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .repo-meta {
        color: #5f6368;
        font-size: 0.86rem;
        line-height: 1.45;
    }
    .small-muted {
        color: #70757a;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def human_size(num_bytes: int) -> str:
    """Return a human-readable file size."""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    value = float(num_bytes)
    for unit in ["KB", "MB", "GB", "TB"]:
        value /= 1024.0
        if value < 1024:
            return f"{value:,.1f} {unit}"
    return f"{value:,.1f} PB"


def safe_stat(path: Path) -> Optional[os.stat_result]:
    """Return file stat or None when the file is not accessible."""
    try:
        return path.stat()
    except OSError:
        return None


def infer_issuer(path: Path, sources_dir: Path) -> str:
    """Infer issuer from the first subfolder under sources/."""
    try:
        relative = path.relative_to(sources_dir)
    except ValueError:
        return "unknown"

    if len(relative.parts) > 1:
        return relative.parts[0]
    return "_root"


def prettify_name(name: str) -> str:
    """Create a clean display label from filenames and folder names."""
    cleaned = name.replace("_", " ").replace("-", " ").strip()
    return " ".join(cleaned.split())


def get_file_type(path: Path) -> str:
    """Return a friendly file type label."""
    return SUPPORTED_EXTENSIONS.get(path.suffix.lower(), path.suffix.lower().replace(".", "").upper() or "File")


@st.cache_data(show_spinner=False)
def scan_sources_folder(sources_dir_str: str) -> pd.DataFrame:
    """
    Scan the sources repository and return one row per document.

    Expected structure:
        sources/
            arera/
                report_1.pdf
            terna/
                report_2.pdf
            ...
    """
    sources_dir = Path(sources_dir_str)
    rows: List[Dict[str, object]] = []

    if not sources_dir.exists():
        return pd.DataFrame(columns=[
            "issuer",
            "title",
            "file_name",
            "file_type",
            "extension",
            "relative_path",
            "absolute_path",
            "size_bytes",
            "size",
            "modified_at",
            "folder",
        ])

    for path in sorted(sources_dir.rglob("*")):
        if not path.is_file():
            continue

        # Ignore hidden/system files.
        if any(part.startswith(".") for part in path.parts):
            continue

        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            continue

        stat = safe_stat(path)
        if stat is None:
            continue

        issuer = infer_issuer(path, sources_dir)
        relative_path = path.relative_to(sources_dir)
        modified_at = datetime.fromtimestamp(stat.st_mtime)

        rows.append(
            {
                "issuer": issuer,
                "issuer_label": prettify_name(issuer).upper() if issuer != "_root" else "ROOT",
                "title": prettify_name(path.stem),
                "file_name": path.name,
                "file_type": get_file_type(path),
                "extension": extension,
                "relative_path": str(relative_path),
                "absolute_path": str(path.resolve()),
                "size_bytes": int(stat.st_size),
                "size": human_size(int(stat.st_size)),
                "modified_at": modified_at,
                "folder": str(path.parent.relative_to(sources_dir)),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["issuer_label", "file_type", "title"], ascending=True).reset_index(drop=True)
    return df


def filter_documents(
    df: pd.DataFrame,
    issuer: str,
    file_types: List[str],
    search_text: str,
) -> pd.DataFrame:
    """Apply issuer, file-type and text filters."""
    filtered = df.copy()

    if issuer != "All issuers":
        filtered = filtered[filtered["issuer_label"] == issuer]

    if file_types:
        filtered = filtered[filtered["file_type"].isin(file_types)]

    if search_text.strip():
        q = search_text.strip().lower()
        searchable = (
            filtered["title"].fillna("").str.lower()
            + " "
            + filtered["file_name"].fillna("").str.lower()
            + " "
            + filtered["issuer_label"].fillna("").str.lower()
            + " "
            + filtered["relative_path"].fillna("").str.lower()
        )
        filtered = filtered[searchable.str.contains(q, regex=False)]

    return filtered.reset_index(drop=True)


def read_file_bytes(path: Path) -> Optional[bytes]:
    """Read file bytes for Streamlit download button."""
    try:
        return path.read_bytes()
    except OSError:
        return None


def mime_type_for(path: Path) -> str:
    """Infer MIME type for download button."""
    mime_type, _ = mimetypes.guess_type(str(path))
    return mime_type or "application/octet-stream"


# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("📚 Sources Repository")
st.caption("Browse reports and documents organised by issuer folder, for example `sources/arera`, `sources/terna`, etc.")

with st.expander("Repository folder structure expected by this page", expanded=False):
    example = """sources/
├── arera/
│   ├── report_1.pdf
│   └── dataset.xlsx
├── terna/
│   └── scenario_document.pdf
└── gse/
    └── policy_note.docx"""
    st.code(example, language="text")

df_docs = scan_sources_folder(str(SOURCES_DIR))

if df_docs.empty:
    st.warning(
        "No documents found. Create a `sources/` folder in the app root and add issuer subfolders such as "
        "`sources/arera` or `sources/terna` with PDF, Word, Excel, CSV, PowerPoint, text, JSON or ZIP files."
    )
    st.stop()

# Top metrics
total_docs = len(df_docs)
total_issuers = df_docs["issuer_label"].nunique()
total_size = human_size(int(df_docs["size_bytes"].sum()))

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Documents", f"{total_docs:,}")
metric_col2.metric("Issuers", f"{total_issuers:,}")
metric_col3.metric("Repository size", total_size)

st.divider()

# Filters
left, middle, right = st.columns([1.2, 1.2, 2.0])

issuer_options = ["All issuers"] + sorted(df_docs["issuer_label"].dropna().unique().tolist())
with left:
    selected_issuer = st.selectbox("Issuer folder", issuer_options)

with middle:
    file_type_options = sorted(df_docs["file_type"].dropna().unique().tolist())
    selected_file_types = st.multiselect("Document type", file_type_options, default=[])

with right:
    search_text = st.text_input(
        "Search documents",
        placeholder="Search by title, issuer, filename or path...",
    )

filtered_docs = filter_documents(df_docs, selected_issuer, selected_file_types, search_text)

st.markdown(f"**{len(filtered_docs):,}** document(s) shown")

# Main layout
list_col, detail_col = st.columns([1.2, 1.0], gap="large")

with list_col:
    st.subheader("Repository documents")

    if filtered_docs.empty:
        st.info("No documents match the current filters.")
    else:
        display_mode = st.radio(
            "View mode",
            ["Cards", "Table"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if display_mode == "Table":
            table_df = filtered_docs[
                ["issuer_label", "title", "file_type", "size", "modified_at", "relative_path"]
            ].rename(
                columns={
                    "issuer_label": "Issuer",
                    "title": "Title",
                    "file_type": "Type",
                    "size": "Size",
                    "modified_at": "Modified",
                    "relative_path": "Path",
                }
            )
            st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            for idx, row in filtered_docs.iterrows():
                st.markdown(
                    f"""
                    <div class="repo-card">
                        <div class="repo-title">📄 {row['title']}</div>
                        <div class="repo-meta">
                            <b>Issuer:</b> {row['issuer_label']} &nbsp; | &nbsp;
                            <b>Type:</b> {row['file_type']} &nbsp; | &nbsp;
                            <b>Size:</b> {row['size']}<br>
                            <b>Path:</b> {row['relative_path']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

with detail_col:
    st.subheader("Open and download")

    if filtered_docs.empty:
        st.info("Select filters to show documents.")
    else:
        labels = [
            f"{row.issuer_label} · {row.title} · {row.file_type}"
            for row in filtered_docs.itertuples(index=False)
        ]

        selected_label = st.selectbox("Select a document", labels)
        selected_idx = labels.index(selected_label)
        selected = filtered_docs.iloc[selected_idx]
        selected_path = Path(selected["absolute_path"])

        st.markdown(
            f"""
            <div class="repo-card">
                <div class="repo-title">{selected['title']}</div>
                <div class="repo-meta">
                    <b>Issuer:</b> {selected['issuer_label']}<br>
                    <b>File name:</b> {selected['file_name']}<br>
                    <b>Type:</b> {selected['file_type']}<br>
                    <b>Size:</b> {selected['size']}<br>
                    <b>Modified:</b> {selected['modified_at'].strftime('%Y-%m-%d %H:%M')}<br>
                    <b>Relative path:</b> {selected['relative_path']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        data = read_file_bytes(selected_path)
        if data is None:
            st.error("The selected file could not be read.")
        else:
            st.download_button(
                label="⬇️ Download selected document",
                data=data,
                file_name=selected["file_name"],
                mime=mime_type_for(selected_path),
                use_container_width=True,
            )

            if selected_path.suffix.lower() == ".pdf":
                st.info("PDF preview is available when the browser supports embedded PDF rendering.")
                try:
                    import base64

                    b64 = base64.b64encode(data).decode("utf-8")
                    st.markdown(
                        f"""
                        <iframe
                            src="data:application/pdf;base64,{b64}"
                            width="100%"
                            height="640"
                            type="application/pdf">
                        </iframe>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception:
                    st.warning("PDF preview could not be created, but the document can still be downloaded.")

st.divider()

# Issuer summary
st.subheader("Issuer summary")
summary = (
    df_docs.groupby(["issuer_label", "file_type"], as_index=False)
    .agg(
        documents=("file_name", "count"),
        size_bytes=("size_bytes", "sum"),
    )
    .sort_values(["issuer_label", "file_type"])
)
summary["size"] = summary["size_bytes"].apply(human_size)

st.dataframe(
    summary.rename(
        columns={
            "issuer_label": "Issuer",
            "file_type": "Type",
            "documents": "Documents",
            "size": "Size",
        }
    )[["Issuer", "Type", "Documents", "Size"]],
    use_container_width=True,
    hide_index=True,
)

csv_export = filtered_docs.drop(columns=["absolute_path"], errors="ignore").to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download filtered repository index as CSV",
    data=csv_export,
    file_name="sources_repository_index.csv",
    mime="text/csv",
)