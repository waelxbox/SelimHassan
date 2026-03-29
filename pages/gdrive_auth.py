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

    if "OAUTH_CLIENT_SECRETS" not in st.secrets:
        st.error("Missing Client Secrets.")
        return

    try:
        # 2. Setup the Flow ONCE and lock it into session state
        if "oauth_flow" not in st.session_state:
            client_secrets = json.loads(st.secrets["OAUTH_CLIENT_SECRETS"])
            flow = Flow.from_client_config(
                client_secrets,
                scopes=SCOPES,
                redirect_uri="urn:ietf:wg:oauth:2.0:oob"
            )
            auth_url, _ = flow.authorization_url(prompt="consent")
            
            # Save the handshake and URL to memory so they survive the button click!
            st.session_state["oauth_flow"] = flow
            st.session_state["auth_url"] = auth_url

        st.markdown(f"### Step 1: [Click here to authorize access]({st.session_state['auth_url']})", unsafe_allow_html=True)
        st.markdown("### Step 2: Paste the code below")
        
        auth_code = st.text_input("Enter authorization code from Google:")
        
        if st.button("Connect"):
            if not auth_code:
                st.warning("Please enter the code first.")
                return
            
            # Retrieve the exact same handshake flow from memory
            flow = st.session_state["oauth_flow"]
            flow.fetch_token(code=auth_code)
            
            # Save the active login session
            st.session_state["oauth_gdrive_creds"] = flow.credentials.to_json()
            
            # Clean up memory
            del st.session_state["oauth_flow"]
            del st.session_state["auth_url"]
            
            st.rerun()
            
    except Exception as e:
        st.error(f"Authentication setup failed: {e}")
