import streamlit as st
import json
from data_store import _get_backend

def render():
    st.title("Cloud Storage Status")
    
    # SAFE: Just calling the function, not printing the result yet
    backend = _get_backend()

    if backend:
        st.success("✅ Connected to Google Drive")
        
        # SAFE: Hardcoded strings, not the object itself
        st.write(f"Connected to project: **{st.secrets['SERVICE_ACCOUNT_JSON'].split('project_id\": \"')[1].split('\"')[0]}**")
        
        # SAFE: Only printing the ID string, not the whole folder object
        st.info(f"Root Archive Folder ID: `{backend.root_id}`")
        
        st.divider()
        st.write("### Active Folders")
        st.write(f"- **Scans:** `{backend.uploads_id}`")
        st.write(f"- **Transcriptions:** `{backend.transcriptions_id}`")
    else:
        st.error("❌ Not Connected")
        st.info("Check your Streamlit Secrets and ensure the JSON is valid.")

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
