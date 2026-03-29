import streamlit as st
from google_auth_oauthlib.flow import Flow
import json

SCOPES = ["https://www.googleapis.com/auth/drive"]

def render():
    st.title("Connect to Google Drive")
    st.caption("Log in with your Google account to use your personal storage quota.")

    # 1. Check if already logged in
    if "oauth_gdrive_creds" in st.session_state:
        st.success("✅ Google Drive is connected as YOU!")
        st.info("Your uploads will now successfully bypass the 0-byte Service Account quota.")
        if st.button("Disconnect"):
            del st.session_state["oauth_gdrive_creds"]
            st.rerun()
        return

    # 2. Check for the Client Secrets in Streamlit Secrets
    if "OAUTH_CLIENT_SECRETS" not in st.secrets:
        st.error("Missing Client Secrets.")
        st.info("Please paste your OAuth 2.0 Client ID JSON into Streamlit Secrets as OAUTH_CLIENT_SECRETS.")
        return

    # 3. Generate the Login Link
    try:
        client_secrets = json.loads(st.secrets["OAUTH_CLIENT_SECRETS"])
        flow = Flow.from_client_config(
            client_secrets,
            scopes=SCOPES,
            redirect_uri="urn:ietf:wg:oauth:2.0:oob"
        )
        auth_url, _ = flow.authorization_url(prompt="consent")
        
        st.markdown(f"### Step 1: [Click here to authorize access]({auth_url})", unsafe_allow_html=True)
        st.markdown("### Step 2: Paste the code below")
        
        auth_code = st.text_input("Enter authorization code from Google:")
        
        if st.button("Connect"):
            if not auth_code:
                st.warning("Please enter the code first.")
                return
            
            flow.fetch_token(code=auth_code)
            # Save the active login session!
            st.session_state["oauth_gdrive_creds"] = flow.credentials.to_json()
            st.rerun()
            
    except Exception as e:
        st.error(f"Authentication setup failed: {e}")
