import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Did I Like It?", layout="wide")

# --- 2. GOOGLE OAUTH CONFIG ---
# This pulls from the Secrets you set up earlier
CLIENT_CONFIG = {
    "web": {
        "client_id": st.secrets["google_oauth"]["client_id"],
        "client_secret": st.secrets["google_oauth"]["client_secret"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]],
    }
}

def login():
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=["https://www.googleapis.com/auth/userinfo.email", "openid"],
        redirect_uri=st.secrets["google_oauth"]["redirect_uri"]
    )
    auth_url, _ = flow.authorization_url(prompt='select_account')
    st.markdown(f'<a href="{auth_url}" target="_self" style="background-color: #4285F4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Sign in with Google</a>', unsafe_allow_html=True)

# --- 3. CHECK AUTHENTICATION ---
if "user_email" not in st.session_state:
    # Check if returning from Google login
    query_params = st.query_params
    if "code" in query_params:
        flow = Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=["https://www.googleapis.com/auth/userinfo.email", "openid"],
            redirect_uri=st.secrets["google_oauth"]["redirect_uri"]
        )
        flow.fetch_token(code=query_params["code"])
        session = flow.authorized_session()
        user_info = session.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
        st.session_state["user_email"] = user_info["email"]
        st.query_params.clear()
        st.rerun()
    else:
        st.title("🤔 Did I Like It?")
        st.write("Please sign in to access your private vault.")
        login()
        st.stop()

# --- 4. LOGGED IN CONTENT ---
user_email = st.session_state["user_email"]

# ... (Everything from the previous Database Connection section goes here) ...
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0s")
user_data = df[df["User"] == user_email].copy()

st.title(f"🤔 {user_email.split('@')[0]}'s Log")
with st.sidebar:
    st.write(f"Securely logged in: **{user_email}**")
    if st.button("Log Out"):
        del st.session_state["user_email"]
        st.rerun()
    
    # ... (Rest of your form code) ...
