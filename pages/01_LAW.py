import json
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from pathlib import Path
import importlib

st.set_page_config(page_title="Dashboard", layout="wide")
from utils import apply_style_and_logo

apply_style_and_logo()

import supporting_functions.lxml_read_functions as lxml_funcs

# Force reload (development only)
importlib.reload(lxml_funcs)


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


def styled_scrollable_markdown(md: str, height: int = 500):
            st.markdown(
    f"""
    <div style="
        height: 35rem;
        overflow-y: auto;
        padding: 1.5rem;
        border: 0.0625rem solid #dcdcdc;
        border-radius: 0.5rem;
        background-color: #005680;
        font-size: 1.0625rem;
        line-height: 1.8;
        font-family: Georgia, serif;
    ">
        {md.replace('\n', '<br>')}
    </div>
    """,
    unsafe_allow_html=True
)

#------------------------------------------
st.title(f"⚖️  ITALIAN LAW DECODER")
st.caption("Source: WaveTransition")

#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------
st.subheader("📖 Law Description")
#from supporting_functions.lxml_read_functions import get_law_title
# 1) Folder where XML laws are stored
LAWS_DIR = Path("laws")
NS = {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"}
# 2) Display name -> filename mappings

CONFIG_PATH = LAWS_DIR / "law_list_dict.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    law_list_dict = json.load(f)

selected_law_name = st.selectbox(
    "Select a law",
    options=list(law_list_dict.keys())
)

selected_filename = law_list_dict[selected_law_name]
selected_law_path = LAWS_DIR / selected_filename

#law_info=lxml_funcs.get_law_title(selected_law_path,NS)
meta = lxml_funcs.get_law_metadata(selected_law_path)

st.subheader("⚖️ Law metadata")
st.write("Title:", meta.get("doc_title"))
st.write("Date:", meta.get("frbr_date"))
st.write("Official code:", meta.get("eli_id_local"))
st.write("ELI alias:", meta.get("eli_alias"))
    # law_info is a dict like:
    # {"title": "...", "date": "2026-02-20"}


#--------------------------------------------------------------------------------------------
st.divider()  # <--- Streamlit's built-in separator
#-------------------------------------------------------
col1, col2 = st.columns([1, 2], gap="large")

# --- Build articles once (outside columns)
articles = lxml_funcs.list_articles_with_titles(selected_law_path)
article_ids = [a.eId for a in articles if a.eId]

md_lines = []
for a in articles:
    num = (a.article_number or "").replace("\n", " ").strip()
    title = (a.title or "").replace("\n", " ").strip()
    md_lines.append(f"- **{num}** {title}" if title else f"- **{num}**")
md_content = "\n".join(md_lines)

# --- Row 1: headers / controls
h1, h2 = st.columns([1, 2], gap="large")
with h1:
    st.subheader("📜 Articles list")
    #st.text(law_info.get("title"))
with h2:
    st.subheader("🧩 Article")
    selected_article = st.selectbox("Select an article", options=article_ids, label_visibility="collapsed")

# --- Row 2: the two aligned boxes
b1, b2 = st.columns([1, 2], gap="large")
with b1:
    styled_scrollable_markdown(md_content, height=500)  # same height as right
with b2:
    art = lxml_funcs.extract_article_content(selected_law_path, selected_article)
    md = lxml_funcs.render_article_markdown(art)
    styled_scrollable_markdown(md, height=500)
    
    st.divider()  
    st.download_button(
    label="⬇️ Download article as TXT (.txt)",
    data=md,
    file_name=f"{selected_article}.txt",
    mime="text/plain"
)