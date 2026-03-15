import streamlit as st
import pandas as pd
import json
import requests
import base64
from PIL import Image

# =========================================================
# KONFIGURACJA GITHUB
# =========================================================
try:
    GITHUB_TOKEN = st.secrets["G_TOKEN"]
except:
    GITHUB_TOKEN = "BRAK"

REPO_OWNER = "natpio"
REPO_NAME = "rentownosc-transportu"
FILE_PATH = "config.json"
ADMIN_PASSWORD = "admin" 

# =========================================================
# FUNKCJE POMOCNICZE
# =========================================================
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def get_github_data():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        decoded = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(decoded), content['sha']
    return None, None

def update_github_data(new_data, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    updated_content = json.dumps(new_data, indent=4, ensure_ascii=False)
    encoded = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
    payload = {"message": "Update from Vorteza Systems Interface", "content": encoded, "sha": sha}
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code in [200, 201]

# =========================================================
# STYLIZACJA VORTEZA SYSTEMS
# =========================================================
def apply_vorteza_theme():
    try:
        bin_str = get_base64_of_bin_file('bg_vorteza.png')
        bg_img_style = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(bg_img_style, unsafe_allow_html=True)
    except:
        st.markdown("<style>.stApp { background-color: #0E0E0E; }</style>", unsafe_allow_html=True)

    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            :root {
                --v-copper: #B58863;
                --v-dark: #0E0E0E;
                --v-panel: rgba(26, 26, 26, 0.85);
                --v-text: #E0E0E0;
            }
            .stApp { color: var(--v-text); font-family: 'Montserrat', sans-serif; }
            h1, h2, h3, .stSubheader {
                color: var(--v-copper) !important;
                font-weight: 700 !important;
                letter-spacing: 1px;
                text-transform: uppercase;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }
            div[data-testid="stVerticalBlock"] > div:has(div.vorteza-card) {
                background-color: var(--v-panel);
                padding: 30px;
                border-radius: 5px;
                border-left: 4px solid var(--v-copper);
                box-shadow: 0 10px 30px rgba(0,0,0,0.6);
                backdrop-filter: blur(10px);
            }
            [data-testid="stMetricValue"] { color: var(--v-copper) !important; font-size: 3.5rem !important; font-weight: 700 !important; }
            [data-testid="stMetricLabel"] { color: #AAA !important; text-transform: uppercase; font-size: 0.9rem !important; }
            .stButton > button {
                background-color: rgba(0, 0, 0, 0.5);
                color: var(--v-copper);
                border: 1px solid var(--v-copper);
                border-radius: 0px;
                padding: 15px 30px;
                width: 100%;
                font-weight: 700;
                transition: 0.4s ease;
            }
            .stButton > button:hover { background-color: var(--v-copper); color: #000; }
            input, div[data-baseweb="select"] { background-color: #222 !important; border: 1px solid #333 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# GŁÓWNA APLIKACJA
# =========================================================
st.set_page_config(page_title="VORTEZA SYSTEMS | TRACE", layout="wide")
apply_vorteza_theme()

col_l, col_r = st.columns([1, 4])
with col_l:
    try:
        logo = Image.open('logo_vorteza.png')
        st.image(logo, use_container_width=True)
    except:
        st.title("VORTEZA")

if GITHUB_TOKEN == "BRAK":
    st.error("SYSTEM ERROR: BRAK G_TOKEN W SEKRETACH STREAMLIT.")
else:
    config, file_sha = get_github_data()

    if config:
        tab1, tab2 = st.tabs(["📊 VORTEZA MARGIN", "⚙️ SYSTEM CORE"])

        # --- TAB 1: KALKULATOR RENTOWNOŚCI ---
        with tab1:
            c1, c2 = st.columns([1, 1], gap="large")
            
            with c1:
                st.subheader("Transport Configuration")
                v_type = st.selectbox("Select Vehicle Unit", list(config["VEHICLE_DATA"].keys()))
                
                # Dynamiczny wybór Start -> Cel
                start_points = list(config["DISTANCES_AND_MYTO"].keys())
                start_p = st.selectbox("Starting Point", start_points)
                
                destinations = list(config["DISTANCES_AND_MYTO"][start_p].keys())
                route = st.selectbox("Target Destination", destinations)
                
                v_info = config["VEHICLE_DATA"][v_type]
                r_info = config["DISTANCES_AND_MYTO"][start_p][route]
                prices = config["PRICE"]
                euro = config["EURO_RATE"]

                extra_km = st.number_input("Additional Distance (Total KM)", value=0, step=10)
                
                dist_pl = r_info["distPL"]
                dist_eu = r_info["distEU"] + extra_km
                total_km = dist_pl + dist_eu

            with c2:
                st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
                st.subheader("Technical Margin Analysis")
                
                total_fuel_liters = total_km * v_info["fuelUsage"]
                pl_liters = min(total_fuel_liters, v_info["tankCapacity"])
                eu_liters = max(0, total_fuel_liters - pl_liters)
                
                cost_fuel = (pl_liters * prices["fuelPLN"]) + (eu_liters * prices["fuelEUR"] * euro)
                cost_adblue = (total_km * v_info["adBlueUsage"]) * prices["adBluePLN"]
                cost_service = (dist_pl * v_info["serviceCostPLN"]) + (dist_eu * v_info["serviceCostEUR"] * euro)
                
                # Klucz myta (np. mytoTIR lub mytoBUS)
                myto_key = f"myto{v_type}"
                cost_myto = r_info.get(myto_key, 0)

                total_sum = cost_fuel + cost_adblue + cost_service + cost_myto

                st.metric(label="TOTAL TECHNICAL COST (PLN)", value=f"{round(total_sum, 2)} zł")
                
                with st.expander("👁️ SHOW DETAILED LOGS"):
                    st.write(f"⛽ Fuel: **{round(cost_fuel, 2)} PLN** ({round(pl_liters)}L PL / {round(eu_liters)}L EU)")
                    st.write(f"💧 AdBlue: **{round(cost_adblue, 2)} PLN**")
                    st.write(f"🛠️ Service: **{round(cost_service, 2)} PLN**")
                    st.write(f"🛣️ Tolls/Myto: **{round(cost_myto, 2)} PLN**")
                    st.write("---")
                    st.write(f"📏 Total Distance: **{total_km} KM**")
                st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 2: SYSTEM CORE (ADMIN & DATABASE) ---
        with tab2:
            st.subheader("Vorteza Master Access")
            pwd = st.text_input("Vorteza Master Key", type="password")
            
            if pwd == ADMIN_PASSWORD:
                st.success("Access Granted.")
                
                # SEKCJA EKONOMICZNA
                st.markdown("### 1. Global Economic Factors")
                a1, a2, a3 = st.columns(3)
                with a1:
                    new_euro = st.number_input("EURO Rate", value=config["EURO_RATE"], format="%.4f")
                with a2:
                    new_fuel_pl = st.number_input("Fuel PL (PLN)", value=config["PRICE"]["fuelPLN"])
                with a3:
                    new_fuel_eu = st.number_input("Fuel EU (EUR)", value=config["PRICE"]["fuelEUR"])
                
                st.write("---")

                # ZARZĄDZANIE TRASAMI
                st.markdown("### 2. Route Management")
                action = st.radio("Mode:", ["Add New Route", "Edit/Delete Existing"], horizontal=True)

                if action == "Add New Route":
                    c_s, c_d = st.columns(2)
                    with c_s:
                        starts = list(config["DISTANCES_AND_MYTO"].keys())
                        s_city = st.selectbox("Start Point", ["+ NEW"] + starts)
                        if s_city == "+ NEW": s_city = st.text_input("New Start Name")
                    with c_d:
                        d_city = st.text_input("Destination Name")
                    
                    val_pl, val_eu, val_mtir, val_mbus = 100, 500, 0, 0
                else:
                    c_s, c_d = st.columns(2)
                    with c_s:
                        s_city = st.selectbox("Select Start Point", list(config["DISTANCES_AND_MYTO"].keys()))
                    with c_d:
                        dests = list(config["DISTANCES_AND_MYTO"][s_city].keys())
                        d_city = st.selectbox("Select Destination", dests)
                    
                    curr = config["DISTANCES_AND_MYTO"][s_city][d_city]
                    val_pl, val_eu = curr["distPL"], curr["distEU"]
                    val_mtir, val_mbus = curr.get("mytoTIR", 0), curr.get("mytoBUS", 0)

                if s_city and d_city and s_city != "+ NEW":
                    st.markdown(f"**Configuration for: {s_city} -> {d_city}**")
                    f1, f2, f3, f4 = st.columns(4)
                    with f1: n_pl = st.number_input("Dist PL", value=val_pl)
                    with f2: n_eu = st.number_input("Dist EU", value=val_eu)
                    with f3: n_tir = st.number_input("Myto TIR", value=val_mtir)
                    with f4: n_bus = st.number_input("Myto BUS", value=val_mbus)

                    if st.button("PUSH TO VORTEZA CLOUD"):
                        if s_city not in config["DISTANCES_AND_MYTO"]: config["DISTANCES_AND_MYTO"][s_city] = {}
                        config["DISTANCES_AND_MYTO"][s_city][d_city] = {
                            "distPL": n_pl, "distEU": n_eu, "mytoTIR": n_tir, "mytoBUS": n_bus
                        }
                        config["EURO_RATE"], config["PRICE"]["fuelPLN"], config["PRICE"]["fuelEUR"] = new_euro, new_fuel_pl, new_fuel_eu
                        
                        if update_github_data(config, file_sha):
                            st.success("Data Synchronized.")
                            st.rerun()
                    
                    if action == "Edit/Delete Existing":
                        if st.button("DELETE ROUTE", type="secondary"):
                            del config["DISTANCES_AND_MYTO"][s_city][d_city]
                            if not config["DISTANCES_AND_MYTO"][s_city]: del config["DISTANCES_AND_MYTO"][s_city]
                            update_github_data(config, file_sha)
                            st.rerun()

            elif pwd != "":
                st.error("Access Denied.")
    else:
        st.error("SYSTEM HALT: FAILED TO LOAD CONFIG.JSON.")
