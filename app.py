import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Did I Like It?", layout="wide")

# --- 1. NEW BUILT-IN AUTH ---
if not st.experimental_user.is_logged_in:
    st.title("🤔 Did I Like It?")
    st.info("Log in to access your private media vault.")
    if st.button("Log in with Google"):
        st.login("google")
    st.stop()

# --- 2. LOGGED IN DATA ---
user_email = st.experimental_user.email
user_name = st.experimental_user.name

st.title(f"🎬 {user_name}'s Log")

# Database Connection
conn = st.connection("gsheets", type=GSheetsConnection)
all_data = conn.read(ttl="0s")
if all_data is None:
    all_data = pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])

# (The rest of your app code here...)

if st.sidebar.button("Log out"):
    st.logout()
