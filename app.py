import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_google_auth import Authenticate
import pandas as pd
from datetime import date

# --- 1. CONFIG ---
st.set_page_config(page_title="Did I Like It?", layout="wide")

# --- 2. GOOGLE AUTH ---
# cookie_expiry_days is required to prevent the TypeError
auth = Authenticate(
    secret_token="personal_vault_token", 
    client_id=st.secrets["google_oauth"]["client_id"],
    client_secret=st.secrets["google_oauth"]["client_secret"],
    redirect_uri=st.secrets["google_oauth"]["redirect_uri"],
    cookie_name="google_auth_cookie",
    cookie_expiry_days=30 
)

# Pulls the admin email from your hidden Secrets
ADMIN_EMAIL = st.secrets.get("admin_user", "").lower()

auth.check_authenticity()

if not st.session_state.get("connected"):
    st.title("🤔 Did I Like It?")
    st.write("Please sign in with Google to access your private log.")
    auth.login()
    st.stop()

user_email = st.session_state["user_info"].get("email").lower()
user_name = st.session_state["user_info"].get("name")

# --- 3. DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        df = conn.read(ttl="0s")
        if "User" not in df.columns:
            # Create the column if it's a brand new sheet
            df["User"] = ""
        return df
    except:
        return pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])

all_data = get_data()
# Filter for only THIS user's data
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
                # Append new data to the master sheet
                new_row = pd.DataFrame([[user_email, t, c, m, g, y, d.strftime('%Y-%m-%d'), l, th]], 
                                       columns=all_data.columns)
                updated_df = pd.concat([all_data, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("Saved! Check 'My Log' to see it.")
                st.rerun()
            else:
                st.warning("Please provide a Title.")

# --- 6. PAGE: MY LOG ---
elif choice == "My Log":
    st.title(f"🤔 {user_name}'s Private Log")
    
    if user_data.empty:
        st.info("Your log is empty. Go to 'Add Entry' to start your collection!")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Your Total", len(user_data))
        m2.metric("Movies", len(user_data[user_data['Type'] == "Movie"]))
        m3.metric("Books", len(user_data[user_data['Type'] == "Book"]))
        m4.metric("Albums", len(user_data[user_data['Type'] == "Album"]))

        st.divider()
        search = st.text_input("🔍 Search my entries...")
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
                    # Drop by the original index in all_data
                    updated_all = all_data.drop(i)
                    conn.update(data=updated_all)
                    st.rerun()

# --- 7. PAGE: ADMIN ---
elif choice == "Admin Dashboard":
    st.title("🛡️ Admin Overview")
    st.info("Only you can see this page. Other users' specific logs remain hidden.")
    
    col1, col2 = st.columns(2)
    col1.metric("Unique Users", all_data['User'].nunique())
    col2.metric("Total Database Rows", len(all_data))
    
    st.subheader("Usage by User")
    if not all_data.empty:
        user_counts = all_data['User'].value_counts()
        st.bar_chart(user_counts)
    else:
        st.write("No data available yet.")
