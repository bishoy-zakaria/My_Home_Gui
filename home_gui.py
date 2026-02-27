import streamlit as st
from streamlit_echarts import st_echarts
import firebase_admin
from firebase_admin import credentials, db
import hashlib
import json
import os
import time

# --- CONFIGURATION & DATA ---
light_keys = ["LedSide_State", "Magnetic_State", "Spots_State", "LED_State"]

power_dict = {
    "LedSide_State": {"current_value": 0, "fixed_value": 200},
    "Magnetic_State": {"current_value": 0, "fixed_value": 180},
    "Spots_State": {"current_value": 0, "fixed_value": 150},
    "LED_State": {"current_value": 0, "fixed_value": 200},
}

FIREBASE_DB_URL = "https://my-home-a6d27-default-rtdb.firebaseio.com/"

# --- 1. FIREBASE SETUP ---
@st.cache_resource
def init_firebase():
    try:
        if "firebase" in st.secrets:
            fb_credentials = dict(st.secrets["firebase"])
            if "private_key" in fb_credentials:
                # Use a unique name for the temp file to avoid collisions
                with open("temp_firebase.json", "w") as f:
                    json.dump(fb_credentials, f, indent=4)
                
                cred = credentials.Certificate("temp_firebase.json")
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
                return True
        st.error("⚠️ Firebase credentials missing in secrets.")
        return False
    except Exception as e:
        st.error(f"⚠️ Firebase Connection Failed: {e}")
        return False

firebase_ready = init_firebase()

# --- 2. UTILITIES ---
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

def load_cred_data(db_node):
    if not firebase_ready: return {}
    try:
        ref = db.reference(db_node)
        return ref.get() or {}
    except:
        return {}

def user_data(data_dict, db_node):
    if not firebase_ready: return
    db.reference(db_node).set(data_dict)

def sync_to_firebase(node_name, value):
    if not firebase_ready: return
    try:
        ref = db.reference(f"users/Reciption/{node_name}")
        ref.set(int(value))
    except:
        st.error(f"📡 Sync Error: {node_name} failed.")

# --- 3. CALLBACKS ---
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

# --- 4. FRAGMENTS (REAL-TIME UI) ---

@st.fragment(run_every=1)
def power_priodic_calc():
    if not firebase_ready: return
    total = 0
    try: 
        for key in light_keys:
            ref = db.reference(f"users/Reciption/{key}")
            data = ref.get()
            power = bool(data) * power_dict[key]["fixed_value"]
            total += power
        st.session_state.Sum_power = total
    except:
        pass

@st.fragment(run_every=2)
def fetch_priodic_state():
    if not firebase_ready: return
    try: 
        # Update session states from DB
        for key in light_keys:
            ref = db.reference(f"users/Reciption/{key}")
            st.session_state[key] = bool(ref.get())

        # --- LAYOUT: SIDE BY SIDE ---
        col_left, col_right = st.columns([1, 1], gap="medium")

        with col_left:
            st.markdown("#### ⚡ Device Switches")
            # Inner columns for a nice 2x2 toggle grid
            i_col1, i_col2 = st.columns(2)
            with i_col1:
                st.toggle("LED Side", key="LedSide_State", on_change=handle_toggle, args=("LedSide_State",))
                st.toggle("Magnetic", key="Magnetic_State", on_change=handle_toggle, args=("Magnetic_State",))
            with i_col2:
                st.toggle("Spots", key="Spots_State", on_change=handle_toggle, args=("Spots_State",))
                st.toggle("Profile", key="LED_State", on_change=handle_toggle, args=("LED_State",))

        with col_right:
            current_power = st.session_state.get("Sum_power", 0)
            gauge_options = {
                "series": [{
                    "type": "gauge",
                    "min": 0,
                    "max": 1000,
                    "detail": {"formatter": "{value} W", "fontSize": 18, "offsetCenter": [0, "70%"]},
                    "data": [{"value": int(current_power), "name": "Usage"}],
                    "axisLine": {
                        "lineStyle": {
                            "width": 8,
                            "color": [[0.2, "#8AE01F"], [0.4, "#DEDA0D"], [0.6, "#C9920C"],[0.8, "#A14213"],[1, "#ED0909"]]
                        }
                    },
                    "pointer": {"width": 4},
                    "title": {"offsetCenter": [0, "90%"], "fontSize": 14}
                }]
            }
            st_echarts(options=gauge_options, height="280px")
        
        st.divider()
    except Exception as e:
        st.warning("🔄 Syncing UI...")

# --- 5. APP INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.update({
        "logged_in": False, "user_name": "", "show_settings": False,
        "change_pwd_mode": False, "customize_mode": False, 
        "edit_mode_selection": None, "Sum_power": 0
    })

for key in light_keys:
    if key not in st.session_state:
        st.session_state[key] = False

usr_dict = load_cred_data("users/Cred")
all_scenes = load_cred_data("users/Scenes")

# --- 6. MAIN ROUTING ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🏡 My Home Control</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        st.subheader("Authentication")
        input_user = st.text_input("Username")
        input_pass = st.text_input("Password", type="password")
        if st.form_submit_button("Login", use_container_width=True):
            if input_user in usr_dict and verify_password(usr_dict[input_user]["password"], input_pass):
                st.session_state.logged_in = True
                st.session_state.user_name = input_user
                st.rerun()
            else:
                st.error("Invalid Credentials")
else:
    user_id = st.session_state.user_name
    user_scenes = all_scenes.get(user_id, {})

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown('<div style="background-color: #2e7d32; padding: 10px; border-radius: 10px; color: white; text-align: center;"><h3>🏡 MY HOME</h3></div>', unsafe_allow_html=True)
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.show_settings = not st.session_state.show_settings
        st.button("🚪 Logout", use_container_width=True, on_click=logout)
        st.divider()
        st.caption(f"User: {user_id}")

    st.title(f"Welcome, {user_id}!")

    # --- SETTINGS LOGIC ---
    if st.session_state.show_settings:
        with st.container(border=True):
            st.subheader("🛠️ Control Panel")
            c1, c2, c3 = st.columns(3)
            if c1.button("🔑 Password", use_container_width=True):
                st.session_state.change_pwd_mode = True
                st.session_state.customize_mode = False
            if c2.button("🎨 Add Mode", use_container_width=True):
                st.session_state.customize_mode = True
                st.session_state.change_pwd_mode = False
            if c3.button("📝 Edit Mode", use_container_width=True):
                st.session_state.edit_mode_selection = "Select" if user_scenes else None

            # Add/Edit Scene Form
            if st.session_state.customize_mode:
                with st.form("scene_form"):
                    name = st.text_input("Mode Name")
                    if st.form_submit_button("Save"):
                        # Logic to save to Firebase...
                        st.success("Mode Saved!")
            
            if st.button("Close Settings"):
                st.session_state.show_settings = False
                st.rerun()

    st.write("---")
    
    # --- DASHBOARD ---
    power_priodic_calc()
    fetch_priodic_state()

    # --- QUICK ACTIONS ---
    st.subheader("🎭 Scenes")
    if user_scenes:
        s_cols = st.columns(3)
        for i, name in enumerate(user_scenes.keys()):
            s_cols[i % 3].button(name, key=f"s_{name}", use_container_width=True, on_click=apply_scene, args=(name, user_scenes))

    st.write("")
    m1, m2 = st.columns(2)
    m1.button("🟢 All On", use_container_width=True, on_click=turn_all, args=(True,))
    m2.button("🔴 All Off", use_container_width=True, on_click=turn_all, args=(False,))