import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Did I Like It?", layout="wide")

# --- 2. OFFICIAL GOOGLE LOGIN LOGIC ---
def login_user():
    # Configure the Google Flow using your Secrets
    client_config = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
        redirect_uri=st.secrets["google_oauth"]["redirect_uri"]
    )

    # Check if we are returning from Google Login
    query_params = st.query_params
    if "code" in query_params:
        flow.fetch_token(code=query_params["code"])
        session = flow.authorized_session()
        user_info = session.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
        st.session_state.user = user_info
        st.query_params.clear()
        st.rerun()

    # If not logged in, show login button
    if "user" not in st.session_state:
        st.title("🤔 Did I Like It?")
        auth_url, _ = flow.authorization_url(prompt="consent")
        st.link_button("Login with Google", auth_url)
        st.stop()

login_user()

# --- 3. LOGGED IN DATA ---
user_email = st.session_state.user.get("email").lower()
user_name = st.session_state.user.get("name")
ADMIN_EMAIL = st.secrets.get("admin_user", "").lower()

# Database Connection
conn = st.connection("gsheets", type=GSheetsConnection)
all_data = conn.read(ttl="0s")

if all_data is None:
    all_data = pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])

user_data = all_data[all_data["User"] == user_email].copy()

# --- 4. NAVIGATION ---
menu = ["My Log", "Add Entry"]
if user_email == ADMIN_EMAIL:
    menu.append("Admin Dashboard")

choice = st.sidebar.selectbox("Menu", menu)
st.sidebar.write(f"Logged in as: **{user_email}**")
if st.sidebar.button("Log Out"):
    del st.session_state.user
    st.rerun()

# --- 5. INTERFACE ---
if choice == "Add Entry":
    st.header("➕ Add New Entry")
    with st.form("add_form", clear_on_submit=True):
        t = st.text_input("Title")
        m = st.selectbox("Type", ["Movie", "Book", "Album"])
        c = st.text_input("Director / Artist")
        g = st.text_input("Genre")
        y = st.number_input("Year", 1800, 2026, 2026)
        l = st.selectbox("Did I like it?", ["Yes", "No", "Kind of"])
        th = st.text_area("Thoughts")
        
        if st.form_submit_button("Save"):
            if t:
                new_row = pd.DataFrame([[user_email, t, c, m, g, y, date.today(), l, th]], columns=all_data.columns)
                updated_df = pd.concat([all_data, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("Saved!")
                st.rerun()

elif choice == "My Log":
    st.header(f"🎬 {user_name}'s Private Log")
    if user_data.empty:
        st.info("Empty! Add something in the sidebar.")
    else:
        for i, row in user_data.iloc[::-1].iterrows():
            with st.container(border=True):
                colA, colB = st.columns([7, 1])
                colA.subheader(f"{row['Title']} ({row['Year Released']})")
                colA.write(f"**By:** {row['Creator']} | **Liked?** {row['Did I Like It?']}")
                colA.write(f"*{row['Thoughts']}*")
                if colB.button("🗑️", key=f"del_{i}"):
                    conn.update(data=all_data.drop(i))
                    st.rerun()

elif choice == "Admin Dashboard":
    st.header("📊 Admin Overview")
    st.write(f"Unique Users: {all_data['User'].nunique()}")
    st.bar_chart(all_data['User'].value_counts())
