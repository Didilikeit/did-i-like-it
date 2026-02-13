import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Did I Like It?", layout="wide")

# --- 2. LOGIN LOGIC ---
if 'user_email' not in st.session_state:
    st.title("🤔 Did I Like It?")
    st.write("Enter your email to access your private log.")
    email_input = st.text_input("Gmail Address:")
    if st.button("Log In"):
        if "@" in email_input:
            st.session_state['user_email'] = email_input.lower()
            st.rerun()
        else:
            st.error("Please enter a valid email address.")
else:
    user_email = st.session_state['user_email']
    
    # --- 3. DATABASE CONNECTION ---
    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        try:
            df = conn.read(ttl="0s")
            # If the sheet is brand new, ensure the 'User' column exists
            if "User" not in df.columns:
                df["User"] = ""
            return df
        except:
            return pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])

    all_data = load_data()
    # Filter only for THIS user
    user_data = all_data[all_data["User"] == user_email].copy()

    # --- 4. HEADER & LOGOUT ---
    st.title(f"🤔 {user_email.split('@')[0]}'s Log")
    
    with st.sidebar:
        st.write(f"Logged in as: **{user_email}**")
        if st.button("Log Out"):
            del st.session_state['user_email']
            st.rerun()
        
        st.divider()
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

    # --- 5. STATS ---
    if not user_data.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", len(user_data))
        m2.metric("Movies", len(user_data[user_data['Type'] == "Movie"]))
        m3.metric("Books", len(user_data[user_data['Type'] == "Book"]))
        m4.metric("Albums", len(user_data[user_data['Type'] == "Album"]))

        st.divider()

        # --- 6. DISPLAY CARDS ---
        search = st.text_input("🔍 Search your entries...")
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
    else:
        st.info("Your log is empty. Add your first entry in the sidebar!")
