import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import hashlib
import json
import os

# --- 1. FIREBASE SETUP ---
FIREBASE_DB_URL = "https://my-home-a6d27-default-rtdb.firebaseio.com/"

@st.cache_resource
def init_firebase():
    try:
        if not firebase_admin._apps:
            # Check for Streamlit Cloud Secrets
            if "firebase" in st.secrets:
                fb_credentials = dict(st.secrets["firebase"])
                
                # --- THE FIX ---
                # This ensures any literal "\n" strings are converted to actual newlines
                # and removes any accidental double-backslashes.
                if "private_key" in fb_credentials:
                    fb_credentials["private_key"] = "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDefCEIbJRhBf2L\nv7sUKjspSLhG9oWR79AwDhrAJ1Ew8qRJh8WMWHJpOejPNtnla0M1OJHEGFPMPcsB\nrOPmU8HOUqcxmj/rTz3SU51/QH9ubUU/ZFYe3sab4v5F2FdKzkcNRkAA9F7/dWAR\nIgVWyPH166AdIRsU/klnUs/EjU8D4FUHRHFV32blSF7bMv90O2oCTKhl8kU0UGO2\np262Kwsb0EhDv/gifAH0q9lc9pg5EOZ/2W10ZT8bBhUuMmzOUEdyv2TO9z35azv+\n9PrQwa++oZuPYPwFy3MSFZ/uvgweAQx0+2vdEFKD9Q80a6HgsAl7N2b1vpo7UTy1\noO+Sy7uZAgMBAAECggEAU8DIsqIlTUzzAIvBwjqPoN/2NwiQibqMVbrJiTKD1vhQ\nrjmFPWsCTuh04qSUbE/vsfZEsVwzF3zfkhbiiA9ZsvDcbcjSbSOcczP04zWFgy1x\nVwbPgLl+bKqL7AEgA1IZ3z5l07YqmOI3sttqxRvKMjhsQur2hfWf7lx3SFeluiAi\nUuRh4SytKw5HZJroDC7Qtz6tlF2qoJTGX9/m6Co2aseY9tBxgokfaeJILqIuhZWv\nSDCD4wX1WEA2hKjpytKIVwP7eo7hhIfWtcMqJnOuhXdT6nteEUs9uoqeycuptvey\nh9OzQxvDzCoHqdpjCB1DHYBCe8pkCW6682dEhglHXQKBgQDvplpUJJL6A7iHmR3i\nXAP207c2YQ22S/itbXYvq1NRRvUvC4N+cZxKNkAyRYQ1Rk4YoVybuRaueJfhJjqj\njujVgY5ucQiwEM/PgQsKhQpA+5wA3ano5dhF0Gv59ivRN4NOizNjeGcXmpxSKQg9\nr0VMA8qLRALboWekE25BKLQYiwKBgQDtqfqYKMtbsJ8UUKM+tA2aMns0dF2XJ4Vz\nzpSCulm6TGoUaTrntrg+8J11oJ8BDEOusFha8hYaMb7kzAyYyBIAum5LBgyQAsNB\nw+z9glSAu4LFz44fhJbDUGoeoBCceZW/ftFEWdaI/u6BTCh+yG8ty5CYXuNlKDq3\nViALt54c6wKBgQDA6dTE7zwxblVZMnTQBupaA0v0xmPXX4ircvY0oWHMh6ZPXKFZ\nY/M/+jPrQ/KNQC8VvK9j27bac9EvOSrzBtN/K2+QkAVCVgYzL9nHehkq/mAygj2I\ncZ2LdZ+18+iJ3nog/AU+CWpToe48ZTNxFGpgKp0dRn5WdrOLbOjQIwf2yQKBgQCi\nGbnOZqStmT4ngQiXD//nGF9oW6YqHs6rOk+ZCrmAk/YWjd+bg8kPRNZhEHjjIhZX\n4/efsFba7usg6vv8iRmeXYo0qZ+P6hJ7nMLb9jTkyQBdIz/wx2J9PS/kS5CI6XT1\n8+2QDSaCsj7C+cr1DoimV538D1xR9qp1ucyJsWeqmQKBgQC231jIrQ0vayrdB5XR\nOP+GbnLdT7j5OjHC+1Qc1+ggk0giB817j4MAyLCvO5LBRRfpDeqDo/LnIaL2qce2\nKb0myybb5AIgbIZWK3p3flfXqkV0SII9h2UKpzXU5GoXTyg2tm7VAh87HDAHNA5p\n6WnDBOc0VIMLgdJocKUptby4Ag==\n-----END PRIVATE KEY-----\n"
                
                cred = credentials.Certificate(fb_credentials)
                firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
                return True
            else:
                # Local development fallback
                CERT_FILE = "my-home-a6d27-firebase-adminsdk-fbsvc-795dff0005.json"
                if os.path.exists(CERT_FILE):
                    cred = credentials.Certificate(CERT_FILE)
                    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
                    return True
                else:
                    st.error("❌ Firebase Secrets missing in Streamlit Cloud. Please add them in Settings > Secrets.")
                    return False
        return True
    except Exception as e:
        st.error(f"⚠️ Firebase Connection Failed: {e}")
        return False

firebase_ready = init_firebase()

# --- 2. SECURITY & DATA UTILITIES ---
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            try: return json.load(f)
            except: return {}
    # Initial default user if file doesn't exist
    if file == "users.json":
        return {"admin": {"password": hash_password("1234"), "Description": "Main Admin"}}
    return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# --- 3. FIREBASE SYNC FUNCTIONS ---
def sync_to_firebase(node_name, value):
    if not firebase_ready: return
    try:
        # Sending as 1/0 for hardware (ESP32/Arduino) compatibility
        ref = db.reference(f"users/Reciption/{node_name}")
        ref.set(int(value))
    except Exception as e:
        st.error(f"📡 Sync Error: {node_name} failed.")

def fetch_initial_state():
    if not firebase_ready: return
    try:
        ref = db.reference("users/Reciption")
        data = ref.get()
        if data:
            for key in light_keys:
                if key in data:
                    st.session_state[key] = bool(data[key])
    except Exception as e:
        st.warning("⚠️ Cloud unreachable. Using local states.")

# --- 4. SESSION STATE INITIALIZATION ---
light_keys = ["LedSide_State", "Magnetic_State", "Spots_State", "LED_State"]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.show_settings = False
    st.session_state.change_pwd_mode = False
    st.session_state.customize_mode = False
    st.session_state.edit_mode_selection = None
    fetch_initial_state()

for key in light_keys:
    if key not in st.session_state:
        st.session_state[key] = False

DB_FILE = "users.json"
SCENE_FILE = "scenes.json"
usr_dict = load_data(DB_FILE)
all_scenes = load_data(SCENE_FILE)

# --- 5. CALLBACK FUNCTIONS ---
def handle_toggle(key):
    sync_to_firebase(key, st.session_state[key])

def turn_all(state: bool):
    for key in light_keys:
        st.session_state[key] = state
        sync_to_firebase(key, state)

def apply_scene(scene_name, user_scenes):
    scene_config = user_scenes.get(scene_name, {})
    for key in light_keys:
        val = scene_config.get(key, False)
        st.session_state[key] = val
        sync_to_firebase(key, val)

def logout():
    for key in ["logged_in", "user_name", "show_settings", "change_pwd_mode", "customize_mode"]:
        st.session_state[key] = False

# --- 6. APP LOGIC FLOW ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🏡 My Home Control</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        st.subheader("Authentication Required")
        input_user = st.text_input("Username")
        input_pass = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        if submit:
            if input_user in usr_dict:
                if verify_password(usr_dict[input_user]["password"], input_pass):
                    st.session_state.logged_in = True
                    st.session_state.user_name = input_user
                    st.rerun()
                else: st.error("Incorrect password.")
            else: st.error("Username not found.")
else:
    user_id = st.session_state.user_name
    user_scenes = all_scenes.get(user_id, {})

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown('<div style="background-color: #2e7d32; padding: 15px; border-radius: 10px; margin-bottom: 20px;"><h1 style="color: white; text-align: center; font-size: 22px; margin: 0;">🏡 MY HOME</h1></div>', unsafe_allow_html=True)
        st.button("⚙️ Settings", use_container_width=True, on_click=lambda: st.session_state.update({"show_settings": not st.session_state.show_settings}))
        st.button("🚪 Logout", use_container_width=True, on_click=logout)
        st.divider()
        st.caption(f"User: {user_id}")

    st.title(f"Welcome back, {user_id}!")

    # --- SETTINGS CONTAINER ---
    if st.session_state.show_settings:
        with st.container(border=True):
            st.markdown("### 🛠️ Control Panel")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔑 Password", use_container_width=True):
                    st.session_state.change_pwd_mode = not st.session_state.change_pwd_mode
                    st.session_state.customize_mode = False
            with col2:
                if st.button("🎨 Add Mode", use_container_width=True):
                    st.session_state.customize_mode = True
                    st.session_state.edit_mode_selection = None
                    st.session_state.change_pwd_mode = False
            with col3:
                if st.button("📝 Edit Mode", use_container_width=True):
                    st.session_state.customize_mode = False
                    st.session_state.change_pwd_mode = False
                    if user_scenes: st.session_state.edit_mode_selection = "Select"
                    else: st.toast("No modes found.")

            if st.session_state.edit_mode_selection:
                st.write("---")
                options = ["Select"] + list(user_scenes.keys())
                sel = st.selectbox("Select mode to edit:", options)
                if sel != "Select":
                    st.session_state.edit_mode_selection = sel
                    st.session_state.customize_mode = True

            if st.session_state.customize_mode:
                is_edit = st.session_state.edit_mode_selection and st.session_state.edit_mode_selection != "Select"
                curr_name = st.session_state.edit_mode_selection if is_edit else ""
                curr_vals = user_scenes.get(curr_name, {k: False for k in light_keys})
                
                st.write("---")
                st.subheader(f"{'Edit' if is_edit else 'Add New'} Mode")
                with st.form("mode_form"):
                    new_name = st.text_input("Mode Name", value=curr_name)
                    c1, c2 = st.columns(2)
                    new_conf = {
                        "LedSide_State": c1.checkbox("Led Side", value=curr_vals.get("LedSide_State", False)),
                        "Magnetic_State": c1.checkbox("Magnetic", value=curr_vals.get("Magnetic_State", False)),
                        "Spots_State": c2.checkbox("Spots", value=curr_vals.get("Spots_State", False)),
                        "LED_State": c2.checkbox("Led Profile", value=curr_vals.get("LED_State", False))
                    }
                    if st.form_submit_button("Save Mode"):
                        if new_name:
                            if user_id not in all_scenes: all_scenes[user_id] = {}
                            if is_edit and new_name != curr_name: del all_scenes[user_id][curr_name]
                            all_scenes[user_id][new_name] = new_conf
                            save_data(SCENE_FILE, all_scenes)
                            st.success(f"Mode '{new_name}' saved!")
                            st.rerun()
                        else: st.error("Mode name is required.")

            if st.session_state.change_pwd_mode:
                st.write("---")
                with st.form("pwd_f"):
                    new_p = st.text_input("New Password", type="password")
                    if st.form_submit_button("Update Password"):
                        if new_p:
                            usr_dict[user_id]["password"] = hash_password(new_p)
                            save_data(DB_FILE, usr_dict)
                            st.success("Password updated!")
                            st.session_state.change_pwd_mode = False
                            st.rerun()

            if st.button("✖️ Close Settings", use_container_width=True):
                st.session_state.show_settings = False
                st.rerun()

    st.write("---")
    
    # --- LIGHTING CONTROLS ---
    st.subheader("💡 Lighting Control")
    if not firebase_ready: st.warning("Offline Mode: Cloud sync disabled.")

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.toggle("LED Side", key="LedSide_State", on_change=handle_toggle, args=("LedSide_State",))
        st.toggle("Magnetic Lights", key="Magnetic_State", on_change=handle_toggle, args=("Magnetic_State",))
    with t_col2:
        st.toggle("Spots", key="Spots_State", on_change=handle_toggle, args=("Spots_State",))
        st.toggle("Led Profile", key="LED_State", on_change=handle_toggle, args=("LED_State",))

    # --- DYNAMIC MODE BUTTONS ---
    if user_scenes:
        st.subheader("🎭 Your Modes")
        cols = st.columns(3)
        for i, name in enumerate(user_scenes.keys()):
            cols[i % 3].button(name, key=f"btn_{name}", use_container_width=True, on_click=apply_scene, args=(name, user_scenes))

    st.write("")
    m_col1, m_col2 = st.columns(2)
    m_col1.button("🟢 All On", use_container_width=True, on_click=turn_all, args=(True,))
    m_col2.button("🔴 All Off", use_container_width=True, on_click=turn_all, args=(False,))