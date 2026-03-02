import streamlit as st
from markdown import markdown

def styled_scrollable_markdown(md: str, height_rem: float = 35):
    html_body = markdown(
        md,
        extensions=["extra", "sane_lists"]  # better lists, headings, etc.
    )
    st.markdown(
        f"""
        <div style="
            height: {height_rem}rem;
            overflow-y: auto;
            padding: 1.5rem;
            border: 0.0625rem solid #dcdcdc;
            border-radius: 0.5rem;
            background-color: #005680;
            font-size: 1.2rem;
            line-height: 1.2;
            font-family: Georgia, serif;
            color: white;
        ">
            {html_body}
        </div>

 
        """,
        unsafe_allow_html=True
    )
