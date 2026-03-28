"""
app.py  –  Antiquities Service Archive: AI Translation & Review Platform
Main entry point for the multi-page Streamlit application.

Run with:
    streamlit run app.py
"""

import os
import streamlit as st

st.set_page_config(
    page_title="Antiquities Service Archive",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Clean, modern, and minimal styling
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #f7f7f9;
    border-right: 1px solid #e0e0e0;
}
[data-testid="stSidebar"] * { 
    color: #333333 !important; 
}
[data-testid="stSidebar"] .stRadio label { 
    font-size: 0.95rem; 
    font-weight: 500;
}
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 12px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)


def _init_state():
    # Structural defaults for the Antiquities Service pipeline
    defaults = {
        "api_key": "",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3.0-pro",
        "review_index": 0,
        "review_filter": "Pending only",
        "active_page": "Dashboard",
        "_secrets_loaded": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Auto-load API credentials from Streamlit secrets / env vars on first render.
    if not st.session_state["_secrets_loaded"]:
        def _get(key, fallback=""):
            try:
                return st.secrets.get(key, os.environ.get(key, fallback))
            except Exception:
                return os.environ.get(key, fallback)

        api_key  = _get("OPENAI_API_KEY")
        base_url = _get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        model    = _get("GEMINI_MODEL", "gemini-3.0-pro")

        if api_key:
            st.session_state["api_key"]  = api_key
        if base_url:
            st.session_state["base_url"] = base_url
        if model:
            st.session_state["model"]    = model

        st.session_state["_secrets_loaded"] = True

_init_state()

PAGES = ["Dashboard", "Upload & Transcribe", "Review Documents", "Export Data", "Settings", "Google Drive"]

with st.sidebar:
    st.markdown("## Antiquities Service Archive")
    st.markdown("*AI Translation & Review Platform*")
    st.divider()

    page = st.radio(
        "Navigation",
        PAGES,
        index=PAGES.index(st.session_state.get("active_page", "Dashboard")),
        label_visibility="collapsed",
    )
    st.session_state["active_page"] = page

    st.divider()

    # Mocked data store import - replace with your actual data store logic
    try:
        from data_store import count_by_status
        counts = count_by_status()
        total = counts["total"]
        done = counts["reviewed"] + counts["flagged"]
    except ImportError:
        # Fallback if data_store isn't implemented yet
        total = 0
        done = 0

    st.caption(f"**{done}** / **{total}** documents reviewed")
    if total > 0:
        st.progress(done / total)

    st.divider()

    # Google Drive status indicator
    if st.session_state.get("gdrive_creds"):
        st.success("Google Drive connected")
    else:
        st.info("Storage: Local (temporary)")
        if st.button("Connect Google Drive", use_container_width=True):
            st.session_state["active_page"] = "Google Drive"
            st.rerun()

    st.divider()
    if st.session_state.get("api_key"):
        st.success("API key configured")
    else:
        st.warning("No API key set")
        if st.button("Go to Settings", use_container_width=True):
            st.session_state["active_page"] = "Settings"
            st.rerun()


# Page Routing
if page == "Dashboard":
    from pages.dashboard import render
    render()
elif page == "Upload & Transcribe":
    from pages.upload import render
    render()
elif page == "Review Documents":
    from pages.review import render
    render()
elif page == "Export Data":
    from pages.export import render
    render()
elif page == "Settings":
    from pages.settings import render
    render()
elif page == "Google Drive":
    from pages.gdrive_auth import render
    render()
