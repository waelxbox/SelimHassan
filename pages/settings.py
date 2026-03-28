# pages/settings.py

import streamlit as st

def render():
    st.title("Settings")
    st.caption("Configure your AI model and API credentials.")

    with st.form("settings_form"):
        api_key = st.text_input(
            "Gemini API Key", 
            value=st.session_state.get("api_key", ""), 
            type="password"
        )
        base_url = st.text_input(
            "Base URL", 
            value=st.session_state.get("base_url", "https://generativelanguage.googleapis.com/v1beta/openai/")
        )
        model = st.text_input(
            "Model", 
            value=st.session_state.get("model", "gemini-3.0-pro"),
            help="gemini-3.0-pro is recommended for complex multilingual handwriting."
        )

        if st.form_submit_button("Save Settings", type="primary"):
            st.session_state["api_key"] = api_key
            st.session_state["base_url"] = base_url
            st.session_state["model"] = model
            st.success("Settings saved successfully. You can now use the Upload & Transcribe pipeline.")
