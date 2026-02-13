import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_google_auth import Authenticate
import pandas as pd
from datetime import date

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Did I Like It?", layout="wide")

# --- 2. GOOGLE AUTH ---
# Changed 'secret_token' to 'secret_key' to fix the TypeError
auth = Authenticate(
    secret_key="personal_vault_token", 
    client_id=st.secrets["google_oauth"]["client_id"],
    client_secret=st.secrets["google_oauth"]["client_secret"],
    redirect_uri=st.secrets["google_oauth"]["redirect_uri"],
    cookie_name=st.secrets["google_oauth"]["cookie_name"],
    cookie_expiry_days=30 
)

# Identify the Admin from Secrets
ADMIN_EMAIL = st.secrets.get("admin_user", "").lower()

# Check if user is already logged in
auth.check_authenticity()

if not st.session_state.get("connected"):
    st.title("🤔 Did I Like It?")
    st.write("Please sign in with Google to access your private vault.")
    auth.login()
    st.stop()

# Get current user info
user_email = st.session_state["user_info"].get("email").lower()
user_name = st.session_state["user_info"].get("name")

# --- 3. DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df = conn.read(ttl="0s")
        if df is None:
            return pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])
        if "User" not in df.columns:
            df["User"] = ""
        return df
    except:
        return pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])

all_data = get_data()
# Privacy Filter: Only shows rows belonging to the logged-in user
user_data = all_data[all_data["User"] == user_email].copy()

# --- 4. NAVIGATION ---
menu = ["My Log", "Add Entry"]
if user_email == ADMIN_EMAIL:
    menu.append("Admin Dashboard")

choice = st.sidebar.selectbox("Menu", menu)
st.sidebar.divider()
st.sidebar.write(f"Logged in: **{user_email}**")
if st.sidebar.button("Log Out"):
    auth.logout()
    st.rerun()

# --- 5. PAGE: ADD ENTRY ---
if choice == "Add Entry":
    st.title("➕ Add to my Log")
    with st.form("add_form", clear_on_submit=True):
        t = st.text_input("Title")
        m = st.selectbox("Type", ["Movie", "Book", "Album"])
        c = st.text_input("Director / Author / Artist")
        g = st.text_input("Genre")
        y = st.number_input("Year Released", 1800, 2100, 2026)
        d = st.date_input("Date Logged", date.today())
        l = st.selectbox("Did I like it?", ["Yes", "No", "Kind of"])
        th = st.text_area("Final Thoughts")
        
        if st.form_submit_button("Save to Vault"):
            if t:
                new_row = pd.DataFrame([[user_email, t, c, m, g, y, d.strftime('%Y-%m-%d'), l, th]], 
                                       columns=all_data.columns)
                updated_df = pd.concat([all_data, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("Successfully saved!")
                st.rerun()
            else:
                st.error("Please enter a Title.")

# --- 6. PAGE: MY LOG ---
elif choice == "My Log":
    st.title(f"🤔 {user_name}'s Private Log")
    
    if user_data.empty:
        st.info("Your log is empty. Use 'Add Entry' in the menu to start!")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Entries", len(user_data))
        m2.metric("Movies", len(user_data[user_data['Type'] == "Movie"]))
        m3.metric("Books", len(user_data[user_data['Type'] == "Book"]))
        m4.metric("Albums", len(user_data[user_data['Type'] == "Album"]))

        st.divider()
        search = st.text_input("🔍 Search your collection...")
        display_df = user_data.iloc[::-1]
        
        if search:
            display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        for i, row in display_df.iterrows():
            with st.container(border=True):
                h, del_col = st.columns([8, 1])
                icon = "🎬" if row['Type'] == "Movie" else "📖" if row['Type'] == "Book" else "🎵"
                h.subheader(f"{icon} {row['Title']} ({row['Year Released']})")
                st.write(f"**By:** {row['Creator']} | **Genre:** {row['Genre']} | **Liked?** {row['Did I Like It?']}")
                st.write(f"*{row['Thoughts']}*")
                
                if del_col.button("🗑️", key=f"del_{i}"):
                    master_updated = all_data.drop(i)
                    conn.update(data=master_updated)
                    st.rerun()

# --- 7. PAGE: ADMIN DASHBOARD ---
elif choice == "Admin Dashboard":
    st.title("🛡️ Admin Overview")
    col1, col2 = st.columns(2)
    col1.metric("Unique Users", all_data['User'].nunique() if not all_data.empty else 0)
    col2.metric("Total Rows", len(all_data))
    
    if not all_data.empty:
        st.subheader("Entry Count per User")
        st.bar_chart(all_data['User'].value_counts())
