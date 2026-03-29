import streamlit as st
import json
from data_store import _get_backend

def render():
    st.title("Cloud Storage Status")
    st.caption("Verifying the connection between this app and your Google Drive via the Service Account.")

    # Try to initialize the backend using the Service Account from Secrets
    backend = _get_backend()

    if backend:
        st.success("✅ Connected to Google Drive")
        st.info("The app is using the Service Account: \n" 
                f"`{st.secrets['SERVICE_ACCOUNT_JSON'][:50]}...`")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Root Archive Folder", "Found" if backend.root_id else "Error")
        with col2:
            st.metric("Transcriptions Folder", "Found" if backend.transcriptions_id else "Error")
            
        st.markdown("---")
        st.markdown("### Troubleshooting")
        st.write("If the app cannot see files, ensure you have **shared** your target Google Drive folder with the service account email:")
        
        # Pull the email from the secret so you can easily copy it
        try:
            creds = json.loads(st.secrets["SERVICE_ACCOUNT_JSON"])
            email = creds.get("client_email", "Email not found")
            st.code(email, language="text")
        except:
            st.error("Could not parse service account email from secrets.")

    else:
        st.error("❌ Not Connected")
        st.warning("The Service Account key in your Streamlit Secrets is either missing or malformed.")
        
        st.markdown("""
        **To fix this:**
        1. Go to your Streamlit Cloud Dashboard.
        2. Open **Settings > Secrets**.
        3. Ensure `SERVICE_ACCOUNT_JSON` is formatted correctly with triple quotes.
        """)
