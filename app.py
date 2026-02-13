import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import streamlit_authenticator as stauth

# --- 1. PAGE CONFIG & STYLE ---
st.set_page_config(page_title="Did I Like It?", layout="wide")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0e1117; color: #ffffff; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    [data-testid="stMetricLabel"] { color: #ffffff !important; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION SETUP ---
if "credentials" in st.secrets:
    config = st.secrets["credentials"]
else:
    # Fallback for local testing
    config = {
        "usernames": {
            "amarindercooner@gmail.com": {"name": "Amarinder", "password": "temp_password_123"}
        }
    }

# Convert nested dictionary to dots/attribute access as required by the library
authenticator = stauth.Authenticate(
    dict(config),
    "did_i_like_it_cookie",
    "signature_key",
    cookie_expiry_days=30
)

# --- 3. LOGIN LOGIC ---
authenticator.login(location="main")

if st.session_state["authentication_status"] == False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] == None:
    st.warning("Please enter your username and password")
elif st.session_state["authentication_status"]:
    
    # Get user info from session state
    name = st.session_state["name"]
    username = st.session_state["username"]

    # --- LOGOUT BUTTON ---
    authenticator.logout("Logout", "sidebar")
    st.sidebar.write(f"Welcome, **{name}**!")

    # --- 4. DATABASE CONNECTION ---
    conn = st.connection("gsheets", type=GSheetsConnection)

    def load_data():
        try:
            df = conn.read(ttl="0s")
            if "User" not in df.columns:
                df["User"] = ""
            return df
        except:
            return pd.DataFrame(columns=["User", "Title", "Creator", "Type", "Genre", "Year Released", "Date Finished", "Did I Like It?", "Thoughts"])

    all_data = load_data()
    # Filter for the logged-in user
    user_data = all_data[all_data["User"] == username].copy()

    # --- 5. HEADER & STATS ---
    st.title(f"🤔 {name}'s Log")
    
    if not user_data.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Logged", len(user_data))
        m2.metric("Movies", len(user_data[user_data['Type'] == "Movie"]))
        m3.metric("Books", len(user_data[user_data['Type'] == "Book"]))
        m4.metric("Albums", len(user_data[user_data['Type'] == "Album"]))
    else:
        st.info("Your log is empty. Add your first entry in the sidebar!")

    st.divider()

    # --- 6. SIDEBAR: ADD ENTRY ---
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
                    new_row = pd.DataFrame([[username, t, c, m, g, y, d.strftime('%Y-%m-%d'), l, th]], 
                                           columns=all_data.columns)
                    updated_df = pd.concat([all_data, new_row], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("Saved!")
                    st.rerun()

    # --- 7. DISPLAY CARDS ---
    if not user_data.empty:
        search = st.text_input("🔍 Search entries...")
        display_df = user_data.iloc[::-1] # Show newest first
        
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
                    # Drop from the main master dataframe
                    all_data = all_data.drop(i)
                    conn.update(data=all_data)
                    st.rerun()
