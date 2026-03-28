# pages/review.py
import io
from PIL import Image, ImageOps
from datetime import datetime, timezone
import streamlit as st
from data_store import (
    list_cards, load_json, save_json, append_to_csv, get_image_bytes,
    list_to_str, str_to_list,
    STATUS_PENDING, STATUS_REVIEWED, STATUS_FLAGGED, STATUS_ERROR
)

# Updated filters for the Antiquities Service schema
FILTER_OPTIONS = [
    "Pending only", 
    "All", 
    "Reviewed only", 
    "Flagged only", 
    "With annotations/stamps", 
    "Errors only"
]

def _apply_filter(cards, filter_opt):
    if filter_opt == "Pending only": return [c for c in cards if c["status"] == STATUS_PENDING]
    if filter_opt == "Reviewed only": return [c for c in cards if c["status"] == STATUS_REVIEWED]
    if filter_opt == "Flagged only": return [c for c in cards if c["status"] == STATUS_FLAGGED]
    if filter_opt == "With annotations/stamps": 
        # Safely check if the JSON has stamps/annotations recorded
        return [c for c in cards if c.get("has_annotations", False)] 
    if filter_opt == "Errors only": return [c for c in cards if c["status"] == STATUS_ERROR]
    return cards

def render():
    st.title("Review Documents")
    st.caption("Compare the original archival scan with the AI transcription and translation. Correct any errors and save to advance.")

    all_cards = list_cards()
    transcribed = [c for c in all_cards if c["has_json"]]

    if not transcribed:
        st.info("No transcribed documents found. Go to Upload & Transcribe to process your scanned images first.")
        if st.button("Go to Upload & Transcribe"):
            st.session_state["active_page"] = "Upload & Transcribe"
            st.rerun()
        return

    filter_col, jump_col = st.columns([2, 3])
    with filter_col:
        filter_opt = st.selectbox(
            "Show documents", 
            FILTER_OPTIONS, 
            index=FILTER_OPTIONS.index(st.session_state.get("review_filter", "Pending only"))
        )
        st.session_state["review_filter"] = filter_opt

    filtered = _apply_filter(transcribed, filter_opt)
    if not filtered:
        st.info(f"No documents match the filter: {filter_opt}.")
        return

    if "review_index" not in st.session_state:
        st.session_state["review_index"] = 0
    idx = max(0, min(st.session_state["review_index"], len(filtered) - 1))
    card_names = [c["name"] for c in filtered]

    with jump_col:
        selected_name = st.selectbox(f"Jump to document ({len(filtered)} in view)", card_names, index=idx)
        idx = card_names.index(selected_name)
        st.session_state["review_index"] = idx

    st.divider()

    card = filtered[idx]
    data = load_json(card)
    status = data.get("_review_status", STATUS_PENDING)

    # Clean, text-based status indicators
    badge_map = {
        STATUS_PENDING: "[Pending]", 
        STATUS_REVIEWED: "[Reviewed]", 
        STATUS_FLAGGED: "[Flagged for expert]", 
        STATUS_ERROR: "[Transcription error]"
    }
    
    st.markdown(f"**Document {idx + 1} of {len(filtered)}** &nbsp;|&nbsp; {badge_map.get(status, '[Pending]')} &nbsp;|&nbsp; Model: `{data.get('_model', 'unknown')}`")

    if data.get("Stamps_and_Annotations"):
        st.info("Annotations Detected — This document contains extracted stamps or marginalia.")
        
    if "error" in data:
        st.error(f"Transcription Error: {data['error']}\n\nYou can manually enter the transcription below, or go to Upload & Transcribe to retry.")

    st.divider()

    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.subheader("Original Scan")
        try:
            raw_bytes = get_image_bytes(card)
            img = Image.open(io.BytesIO(raw_bytes))
            # Automatically rotate the image upright based on phone camera EXIF data
            img = ImageOps.exif_transpose(img)
            st.image(img, use_container_width=True)
        except Exception as e:
            st.error(f"Cannot display image: {e}")
            
        with st.expander("Raw JSON output"):
            st.json(data)

    with right_col:
        st.subheader("Transcription & Translation")
        edited = {}
        
        # Metadata Section
        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            edited["Document_Date"] = st.text_input("Date (YYYY-MM-DD)", value=data.get("Document_Date") or "")
        with col_meta2:
            edited["Sender"] = st.text_input("Sender", value=data.get("Sender") or "")
            
        edited["Recipient"] = st.text_input("Recipient", value=data.get("Recipient") or "")
        edited["Brief_Summary"] = st.text_area("Brief Summary", value=data.get("Brief_Summary") or "", height=68)
        
        # Annotations
        edited["Stamps_and_Annotations"] = str_to_list(
            st.text_area("Stamps & Marginalia", value=list_to_str(data.get("Stamps_and_Annotations")), height=68, help="One entry per line.")
        )

        # Main Text Areas
        _orig_value = data.get("Original_Transcription") or ""
        _orig_lines = max(_orig_value.count("\n") + 1, 1)
        _orig_height = max(200, min(500, _orig_lines * 24 + 40))
        edited["Original_Transcription"] = st.text_area("Original Transcription (French/Arabic)", value=_orig_value, height=_orig_height)

        _trans_value = data.get("English_Translation") or ""
        _trans_lines = max(_trans_value.count("\n") + 1, 1)
        _trans_height = max(200, min(500, _trans_lines * 24 + 40))
        edited["English_Translation"] = st.text_area("English Translation", value=_trans_value, height=_trans_height)

        edited["Confidence_Notes"] = st.text_area("Confidence Notes", value=data.get("Confidence_Notes") or "", height=68)

        st.divider()
        b1, b2, b3, b4 = st.columns(4)
        save_clicked = b1.button("Save & Next", type="primary", use_container_width=True)
        flag_clicked = b2.button("Flag for Expert", use_container_width=True)
        prev_clicked = b3.button("Previous", use_container_width=True, disabled=(idx == 0))
        skip_clicked = b4.button("Skip", use_container_width=True, disabled=(idx >= len(filtered) - 1))

        if save_clicked or flag_clicked:
            new_status = STATUS_FLAGGED if flag_clicked else STATUS_REVIEWED
            updated = {**data, **edited, "_review_status": new_status, "_reviewed_at": datetime.now(timezone.utc).isoformat()}
            save_json(card["stem"], updated)
            append_to_csv(card["name"], updated)
            
            action_word = "Flagged" if flag_clicked else "Saved"
            st.success(f"{action_word}! Document {idx + 1} of {len(filtered)}.")
            
            if idx < len(filtered) - 1:
                st.session_state["review_index"] = idx + 1
                st.rerun()
            else:
                st.info("You have reached the last document in this filter.")

        if prev_clicked and idx > 0:
            st.session_state["review_index"] = idx - 1
            st.rerun()
        if skip_clicked and idx < len(filtered) - 1:
            st.session_state["review_index"] = idx + 1
            st.rerun()

    st.divider()
    
    # Clean text-based bottom navigation
    nav_cols = st.columns(min(len(filtered), 20))
    for i, col in enumerate(nav_cols):
        c = filtered[i]
        icon = {
            STATUS_PENDING: "[P]", 
            STATUS_REVIEWED: "[R]", 
            STATUS_FLAGGED: "[F]", 
            STATUS_ERROR: "[E]"
        }.get(c["status"], "[-]")
        
        if col.button(icon, key=f"nav_{i}", help=c["name"]):
            st.session_state["review_index"] = i
            st.rerun()
