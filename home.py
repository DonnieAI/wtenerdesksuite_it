"""
EnerDeskSuite_IT

"""
#cdm
#     projenv\Scripts\activate
#     streamlit run home.py

import streamlit as st
import pandas as pd


# ✅ Must be the first Streamlit call
st.set_page_config(
    page_title="ENERDESK SUITE IT",   # Browser tab title
    page_icon="🏠",      # Optional favicon (emoji or path to .png/.ico)
    layout="wide"        # "centered" or "wide"
)

# ── Load user credentials and profiles ────────────────────────
CREDENTIALS = dict(st.secrets["auth"])
PROFILES = st.secrets.get("profile", {})

# ── Login form ────────────────────────────────────────────────
def login():
    st.title("🔐 Login Required")

    user = st.text_input("Username", key="username_input")
    password = st.text_input("Password", type="password", key="password_input")

    if st.button("Login", key="login_button"):
        if user in CREDENTIALS and password == CREDENTIALS[user]:
            st.session_state["authenticated"] = True
            st.session_state["username"] = user
            st.session_state["first_name"] = PROFILES.get(user, {}).get("first_name", user)
        else:
            st.error("❌ Invalid username or password")

# ── Auth state setup ──────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# ── Login gate ────────────────────────────────────────────────
if not st.session_state["authenticated"]:
    login()
    st.stop()

# ── App begins after login ────────────────────────────────────

# ---------------Sidebar
from utils import apply_style_and_logo

st.sidebar.success(f"Welcome {st.session_state['first_name']}!")
st.sidebar.button("Logout", on_click=lambda: st.session_state.update(authenticated=False))

# Spacer to push the link to the bottom (optional tweak for better placement)
st.sidebar.markdown("<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

# Company website link
st.sidebar.markdown(
    '<p style="text-align:center;">'
    '<a href="https://www.wavetransition.com" target="_blank">🌐 Visit WaveTransition</a>'
    '</p>',
    unsafe_allow_html=True
)
# ---------Main content
st.title("**ENERDESK SUITE IT**")

# --- Centered cover image ---
from PIL import Image
cover_img = Image.open("cover.png")
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.image(cover_img, use_container_width=False, width=800)  # updated
#st.image(cover_img, use_container_width=True)  # auto fit


st.markdown(
    """
    ## 🇮🇹 Italian Energy System Dashboard

    ### 📊 Key Features
    - Comprehensive overview of the **Italian energy system**
    - Coverage of **electricity, natural gas, oil products, and renewables**
    - Insights on **production, consumption, imports, and capacity**
    - Monitoring of **prices, costs, and taxation components**
    - Environmental indicators including **emissions and energy mix composition**
    - Clear and intuitive **data visualizations** for fast analytical assessment

    ### ⚡ What You Can Explore
    - Structure of the national **generation mix**
    - Role of **renewable energy sources**
    - Evolution of **demand and supply balance**
    - Infrastructure capacity and cross-border exchanges
    - Key performance indicators of the Italian energy market

    ### 🌍 Scope
    This application consolidates the main datasets and analytical views 
    required to understand the structure and performance of Italy’s energy system,
    providing a unified national perspective.

    ### ⚠️ Note
    The dashboard focuses on **structural and system-level analysis**.
    Detailed market simulations, forecasting tools, and high-frequency 
    trading dynamics are addressed in dedicated applications.
    """
)


