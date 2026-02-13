import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Did I Like It?", layout="wide", page_icon="🤔")

# --- 2. AUTHENTICATION ---
# This uses Streamlit's built-in auth system
if not st.experimental_user.is_logged_in:
    st.title("🤔 Did I Like It?")
    st.write("Welcome! Log in to view or manage your personal media vault.")
    if st.button("Log in with Google"):
        st.login("google")
    st.stop()

# Get user info from the session
user_email = st.experimental_user.email
user_name = st.experimental_user.name
# Hardcoded admin check
ADMIN_EMAIL = "amarindercooner@gmail.com"

# --- 3. DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df = conn.read(ttl="0s")
        if df is None or df.empty:
            return pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])
        return df
    except Exception:
        return pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])

all_data = get_data()
# Filter data so users only see their own entries
user_data = all_data[all_data["User"] == user_email.lower()].copy()

# --- 4. SIDEBAR & NAVIGATION ---
st.sidebar.title(f"Hi, {user_name}!")
st.sidebar.write(f"📧 {user_email}")

menu = ["My Log", "Add New Entry"]
if user_email.lower() == ADMIN_EMAIL.lower():
    menu.append("Admin Dashboard")

choice = st.sidebar.radio("Navigate to:", menu)

if st.sidebar.button("Log Out"):
    st.logout()

# --- 5. APP PAGES ---

if choice == "Add New Entry":
    st.header("➕ Add to your Vault")
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Title")
            creator = st.text_input("Director / Author / Artist")
            category = st.selectbox("Type", ["Movie", "Book", "Album", "TV Show", "Game"])
        with col2:
            genre = st.text_input("Genre")
            year = st.number_input("Year Released", 1800, 2026, 2026)
            rating = st.selectbox("Did I Like It?", ["Yes", "No", "Kind of", "Masterpiece"])
        
        thoughts = st.text_area("Final Thoughts / Notes")
        
        if st.form_submit_button("Save Entry"):
            if title:
                new_row = pd.DataFrame([[
                    user_email.lower(), title, creator, category, 
                    genre, year, date.today().strftime("%Y-%m-%d"), 
                    rating, thoughts
                ]], columns=all_data.columns)
                
                updated_df = pd.concat([all_data, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"Added '{title}' to your log!")
                st.rerun()
            else:
                st.error("Please at least provide a Title.")

elif choice == "My Log":
    st.header("📖 Your Personal Log")
    if user_data.empty:
        st.info("Your log is empty. Head to 'Add New Entry' to start!")
    else:
        search = st.text_input("🔍 Search your vault...")
        display_df = user_data.iloc[::-1] # Newest first
        
        if search:
            display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        for i, row in display_df.iterrows():
            with st.container(border=True):
                col_main, col_del = st.columns([0.9, 0.1])
                with col_main:
                    st.subheader(f"{row['Title']} ({row['Year Released']})")
                    st.write(f"**{row['Type']}** by **{row['Creator']}** — *{row['Genre']}*")
                    st.write(f"**Liked?** {row['Did I Like It?']}")
                    st.write(f"💬 {row['Thoughts']}")
                with col_del:
                    if st.button("🗑️", key=f"del_{i}"):
                        # Find the index in the original full dataframe to delete correctly
                        new_all_data = all_data.drop(i)
                        conn.update(data=new_all_data)
                        st.rerun()

elif choice == "Admin Dashboard":
    st.header("📊 Global Analytics")
    st.write(f"Total entries in database: {len(all_data)}")
    st.write(f"Total unique users: {all_data['User'].nunique()}")
    st.dataframe(all_data)
