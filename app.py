import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Did I Like It?", layout="wide", page_icon="🤔")

# --- 2. AUTHENTICATION ---
# st.login looks for the [auth] section in your secrets automatically
if not st.experimental_user.is_logged_in:
    st.title("🤔 Did I Like It?")
    st.write("Welcome! Log in with your Google account to access your private reviews.")
    if st.button("Log in with Google"):
        st.login("google")
    st.stop()

# User details from the Google session
user_email = st.experimental_user.email
user_name = st.experimental_user.name
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
# Filter so user only sees their own rows
user_data = all_data[all_data["User"] == user_email.lower()].copy()

# --- 4. NAVIGATION ---
st.sidebar.title(f"Hello, {user_name}!")
menu = ["My Log", "Add New Entry"]
if user_email.lower() == ADMIN_EMAIL.lower():
    menu.append("Admin Dashboard")

choice = st.sidebar.radio("Navigate", menu)

if st.sidebar.button("Log Out"):
    st.logout()

# --- 5. PAGES ---
if choice == "Add New Entry":
    st.header("➕ Add New Review")
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
        
        thoughts = st.text_area("Thoughts")
        
        if st.form_submit_button("Save Entry"):
            if title:
                new_row = pd.DataFrame([[
                    user_email.lower(), title, creator, category, 
                    genre, year, date.today().strftime("%Y-%m-%d"), 
                    rating, thoughts
                ]], columns=all_data.columns)
                
                updated_df = pd.concat([all_data, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("Saved!")
                st.rerun()

elif choice == "My Log":
    st.header("📖 Your Personal Log")
    if user_data.empty:
        st.info("No entries yet.")
    else:
        search = st.text_input("🔍 Search...")
        display_df = user_data.iloc[::-1]
        
        if search:
            display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        for i, row in display_df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([0.9, 0.1])
                c1.subheader(f"{row['Title']} ({row['Year Released']})")
                c1.write(f"**{row['Type']}** | **Liked?** {row['Did I Like It?']}")
                c1.write(f"*{row['Thoughts']}*")
                if c2.button("🗑️", key=f"del_{i}"):
                    conn.update(data=all_data.drop(i))
                    st.rerun()

elif choice == "Admin Dashboard":
    st.header("📊 Admin Statistics")
    st.write(f"Total Entries: {len(all_data)}")
    st.dataframe(all_data)
