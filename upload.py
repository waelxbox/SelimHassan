# pages/upload.py

import time
import streamlit as st
from pathlib import Path

from data_store import (
    list_cards, 
    save_uploaded_file, 
    save_json, 
    UPLOADS_DIR
)
from transcribe_engine import transcribe_image, build_client

def render():
    st.title("Upload & Transcribe")
    st.caption("Upload high-resolution scans of archival documents. The system will process French/Arabic text and generate an English translation.")

    if not st.session_state.get("api_key"):
        st.warning("No API key configured. Please go to Settings to enter your credentials.")
        return

    # Upload Interface
    uploaded_files = st.file_uploader(
        "Drop archival scans here (JPG, PNG, TIFF)", 
        accept_multiple_files=True, 
        type=["jpg", "jpeg", "png", "tif", "tiff"]
    )

    if uploaded_files:
        st.subheader(f"Ready to process {len(uploaded_files)} document(s)")
        
        if st.button("Start Transcription Pipeline", type="primary"):
            client = build_client(
                api_key=st.session_state["api_key"], 
                base_url=st.session_state.get("base_url")
            )
            model = st.session_state.get("model", "gemini-3.0-pro")

            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            error_count = 0

            for i, uf in enumerate(uploaded_files):
                status_text.text(f"Processing: {uf.name} ({i+1}/{len(uploaded_files)})")
                
                # 1. Save the raw image
                save_uploaded_file(uf)
                
                # 2. Check if it's already transcribed to avoid redundant API calls
                stem = Path(uf.name).stem
                existing_cards = list_cards()
                already_done = any(c["stem"] == stem and c["has_json"] for c in existing_cards)
                
                if already_done:
                    success_count += 1
                else:
                    # 3. Send to Gemini 3.0 Pro
                    result = transcribe_image(
                        image_input=uf.getvalue(), 
                        client=client, 
                        model=model, 
                        filename=uf.name
                    )
                    
                    # 4. Save the JSON output
                    save_json(stem, result)
                    
                    if "error" in result:
                        error_count += 1
                    else:
                        success_count += 1
                        
                progress_bar.progress((i + 1) / len(uploaded_files))
                time.sleep(0.5) # Brief pause for UI refresh

            status_text.text("Processing complete.")
            
            if error_count == 0:
                st.success(f"Successfully processed {success_count} document(s).")
            else:
                st.warning(f"Processed {success_count} document(s), but encountered {error_count} error(s).")
                
            if st.button("Proceed to Review"):
                st.session_state["active_page"] = "Review Documents"
                st.rerun()

    st.divider()
    
    # Simple queue status
    existing = list_cards()
    pending = [c for c in existing if c["status"] == "pending"]
    st.info(f"Current Queue: {len(pending)} document(s) awaiting human review.")
