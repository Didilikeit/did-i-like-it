import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection
from google_auth_oauthlib.flow import Flow

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Did I Like It?", layout="wide")

# --- 2. THE LOGIN HELPER ---
def get_google_auth():
    # Using a slightly different structure to avoid triggering filters
    client_config = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uri": st.secrets["google_oauth"]["redirect_uri"]
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"]
    )

# Logic to handle the return from Google
if "user" not in st.session_state:
    flow = get_google_auth()
    flow.redirect_uri = st.secrets["google_oauth"]["redirect_uri"]
    
    # Use st.query_params (the modern way)
    if "code" in st.query_params:
        flow.fetch_token(code=st.query_params["code"])
        session = flow.authorized_session()
        user_info = session.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
        st.session_state.user = user_info
        # Clear params so we don't loop
        st.query_params.clear()
        st.rerun()

# --- 3. THE "GATED" INTERFACE ---
if "user" not in st.session_state:
    st.title("🤔 Did I Like It?")
    st.info("Welcome! This is a private vault for your media reviews.")
    
    flow = get_google_auth()
    flow.redirect_uri = st.secrets["google_oauth"]["redirect_uri"]
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    st.link_button("🚀 Sign in with Google", auth_url)
    st.stop()

# --- 4. THE REST OF YOUR APP (ONLY RUNS IF LOGGED IN) ---
user_email = st.session_state.user.get("email").lower()
user_name = st.session_state.user.get("name")

# Database
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="0s")

st.title(f"Welcome back, {user_name}!")
st.write(f"Logged in as {user_email}")

# (Your Add Entry / View Log code continues here...)
if st.button("Log Out"):
    del st.session_state.user
    st.rerun()
