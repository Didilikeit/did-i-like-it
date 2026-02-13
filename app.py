import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Did I Like It?", layout="wide")

# --- 2. SIMPLE LOGIN (The backup plan while we fix OAuth) ---
# Since OAuth libraries are being difficult, let's use a simple email entry 
# for a moment to ensure your database connection is actually working.
# WE WILL UPGRADE THIS TO THE GOOGLE BUTTON ONCE THE SERVER STABILIZES.

if 'user_email' not in st.session_state:
    st.title("🤔 Did I Like It?")
    email_input = st.text_input("Enter your Gmail address to log in:")
    if st.button("Log In"):
        if "@gmail.com" in email_input:
            st.session_state['user_email'] = email_input
            st.rerun()
        else:
            st.error("Please enter a valid Gmail address.")
else:
    user_email = st.session_state['user_email']
    
    # --- 3. DATABASE CONNECTION ---
    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        try:
            df = conn.read(ttl="0s")
            return df if "User" in df.columns else pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])
        except:
            return pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])

    all_data = load_data()
    user_data = all_data[all_data["User"] == user_email].copy()

    # --- 4. INTERFACE ---
    st.title(f"🤔 {user_email.split('@')[0]}'s Log")
    st.sidebar.write(f"Logged in as: {user_email}")
    if st.sidebar.button("Log Out"):
        del st.session_state['user_email']
        st.rerun()
    
    # ... (The rest of the Add/View code is the same as before)
    # [Rest of code omitted for brevity but should remain in your app.py]
