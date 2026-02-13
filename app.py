import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_google_oauth import login
import pandas as pd
from datetime import date

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Did I Like It?", layout="wide")

# --- 2. GOOGLE LOGIN ---
# This looks at your Secrets for client_id and client_secret
user_info = login(
    client_id=st.secrets["google_oauth"]["client_id"],
    client_secret=st.secrets["google_oauth"]["client_secret"],
    redirect_uri=st.secrets["google_oauth"]["redirect_uri"],
)

if not user_info:
    st.title("🤔 Did I Like It?")
    st.write("Welcome! Please sign in with Google to view your private list.")
else:
    user_email = user_info.get("email")
    user_name = user_info.get("name")

    # --- 3. DATABASE CONNECTION ---
    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        try:
            df = conn.read(ttl="0s")
            return df if "User" in df.columns else pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])
        except:
            return pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])

    all_data = load_data()
    # Filter for the logged-in Gmail
    user_data = all_data[all_data["User"] == user_email].copy()

    # --- 4. HEADER & INTERFACE ---
    st.title(f"🤔 {user_name}'s Log")
    st.sidebar.write(f"Logged in as: {user_email}")
    
    if not user_data.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Logged", len(user_data))
        m2.metric("Movies", len(user_data[user_data['Type'] == "Movie"]))
        m3.metric("Books", len(user_data[user_data['Type'] == "Book"]))
        m4.metric("Albums", len(user_data[user_data['Type'] == "Album"]))
    
    st.divider()

    # --- 5. SIDEBAR: ADD ENTRY ---
    with st.sidebar:
        st.header("➕ Add New Entry")
        with st.form("add_form", clear_on_submit=True):
            t = st.text_input("Title")
            m = st.selectbox("Type", ["Movie", "Book", "Album"])
            c = st.text_input("Director / Author / Artist")
            g = st.text_input("Genre")
            y = st.number_input("Year Released", 1800, 2100, 2026)
            d = st.date_input("Date Logged", date.today())
            l = st.selectbox("Did I like it?", ["Yes", "No", "Kind of"])
            th = st.text_area("Final Thoughts")
            
            if st.form_submit_button("Save to Cloud"):
                if t:
                    new_row = pd.DataFrame([[user_email, t, c, m, g, y, d.strftime('%Y-%m-%d'), l, th]], 
                                           columns=all_data.columns)
                    updated_df = pd.concat([all_data, new_row], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("Saved!")
                    st.rerun()

    # --- 6. DISPLAY CARDS ---
    if not user_data.empty:
        search = st.text_input("🔍 Search entries...")
        display_df = user_data.iloc[::-1]
        
        if search:
            display_df = display_df[display_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

        for i, row in display_df.iterrows():
            with st.container(border=True):
                h, del_col = st.columns([8, 1])
                icon = "🎬" if row['Type'] == "Movie" else "📖" if row['Type'] == "Book" else "🎵"
                h.subheader(f"{icon} {row['Title']} ({row['Year Released']})")
                
                ca, cb, cc = st.columns(3)
                ca.write(f"**By:** {row['Creator']}")
                cb.write(f"**Genre:** {row['Genre']}")
                rating = row['Did I Like It?']
                cc.write(f"**Liked?** {'🟢' if rating=='Yes' else '🔴' if rating=='No' else '🟡'} {rating}")
                
                st.write(f"*{row['Thoughts']}*")

                if del_col.button("🗑️", key=f"del_{i}"):
                    all_data = all_data.drop(i)
                    conn.update(data=all_data)
                    st.rerun()
