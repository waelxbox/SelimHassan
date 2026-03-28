# pages/dashboard.py

import streamlit as st
from data_store import count_by_status

def render():
    st.title("Archive Dashboard")
    st.caption("Overview of the Antiquities Service transcription and translation pipeline.")

    # Fetch real-time metrics from the local directory or Google Drive
    counts = count_by_status()
    total = counts.get("total", 0)
    reviewed = counts.get("reviewed", 0)
    flagged = counts.get("flagged", 0)
    pending = counts.get("pending", 0)
    errors = counts.get("error", 0)

    # Calculate overall progress
    completed = reviewed + flagged
    progress = (completed / total) if total > 0 else 0.0

    st.subheader("Current Progress")
    st.progress(progress)
    st.write(f"**{completed}** of **{total}** documents verified ({progress:.1%})")

    st.divider()

    # Key Metrics View
    st.subheader("Pipeline Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Pending Review", value=pending)
    with col2:
        st.metric(label="Reviewed", value=reviewed)
    with col3:
        st.metric(label="Flagged for Expert", value=flagged)
    with col4:
        st.metric(label="Transcription Errors", value=errors)

    st.divider()

    # Navigation Shortcuts
    st.subheader("Quick Actions")
    col_act1, col_act2 = st.columns(2, gap="large")

    with col_act1:
        st.info("Upload new high-resolution scans and run them through the Gemini 3.0 Pro translation pipeline.")
        if st.button("Go to Upload & Transcribe", use_container_width=True):
            st.session_state["active_page"] = "Upload & Transcribe"
            st.rerun()

    with col_act2:
        st.info("Verify AI transcriptions, correct English translations, and confirm extracted stamps/marginalia.")
        if st.button("Continue Reviewing", type="primary", use_container_width=True):
            st.session_state["active_page"] = "Review Documents"
            st.session_state["review_filter"] = "Pending only"
            st.rerun()
