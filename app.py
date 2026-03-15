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
ADMIN_PASSWORD = "admin" # Możesz zmienić na własne w Panelu

# =========================================================
# FUNKCJA POMOCNICZA DLA TŁA
# =========================================================
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# =========================================================
# STYLIZACJA VORTEZA SYSTEMS (PREMIUM DARK & COPPER)
# =========================================================
def apply_vorteza_theme():
    # Próba załadowania tła z pliku png
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
        # Fallback do koloru, jeśli pliku nie ma
        st.markdown("<style>.stApp { background-color: #0E0E0E; }</style>", unsafe_allow_html=True)

    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');

            /* Kolory przewodnie */
            :root {
                --v-copper: #B58863;
                --v-dark: #0E0E0E;
                --v-panel: rgba(26, 26, 26, 0.85); /* Lekka przezroczystość panelu */
                --v-text: #E0E0E0;
            }

            .stApp {
                color: var(--v-text);
                font-family: 'Montserrat', sans-serif;
            }

            /* Nagłówki i miedziane akcenty */
            h1, h2, h3, .stSubheader {
                color: var(--v-copper) !important;
                font-weight: 700 !important;
                letter-spacing: 1px;
                text-transform: uppercase;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }

            /* Kontener wyniku (Vorteza Margin Card) */
            div[data-testid="stVerticalBlock"] > div:has(div.vorteza-card) {
                background-color: var(--v-panel);
                padding: 30px;
                border-radius: 5px;
                border-left: 4px solid var(--v-copper);
                box-shadow: 0 10px 30px rgba(0,0,0,0.6);
                backdrop-filter: blur(10px); /* Efekt szkła dla czytelności na tle */
            }

            /* Metryki */
            [data-testid="stMetricValue"] {
                color: var(--v-copper) !important;
                font-size: 3.5rem !important;
                font-weight: 700 !important;
            }
            [data-testid="stMetricLabel"] {
                color: #AAA !important;
                text-transform: uppercase;
                font-size: 0.9rem !important;
            }

            /* Zakładki (Tabs) */
            .stTabs [data-baseweb="tab-list"] {
                gap: 20px;
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 5px;
            }
            .stTabs [data-baseweb="tab"] {
                color: #CCC;
                font-size: 1.1rem;
                padding: 10px 20px;
            }
            .stTabs [aria-selected="true"] {
                color: var(--v-copper) !important;
                border-bottom: 2px solid var(--v-copper) !important;
            }

            /* Przyciski */
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
            .stButton > button:hover {
                background-color: var(--v-copper);
                color: #000;
                box-shadow: 0 0 20px rgba(181, 136, 99, 0.3);
            }

            /* Formularze */
            input, div[data-baseweb="select"] {
                background-color: #222 !important;
                border: 1px solid #333 !important;
                color: white !important;
            }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# LOGIKA POBIERANIA / ZAPISU DANYCH
# =========================================================
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
# GŁÓWNA APLIKACJA
# =========================================================
st.set_page_config(page_title="VORTEZA SYSTEMS | TRACE", layout="wide")
apply_vorteza_theme()

# Header z Logo
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

        # --- TAB 1: KALKULATOR ---
        with tab1:
            c1, c2 = st.columns([1, 1], gap="large")
            
            with c1:
                st.subheader("Transport Configuration")
                v_type = st.selectbox("Select Vehicle Unit", list(config["VEHICLE_DATA"].keys()))
                route = st.selectbox("Target Destination", list(config["DISTANCES_AND_MYTO"].keys()))
                
                v_info = config["VEHICLE_DATA"][v_type]
                r_info = config["DISTANCES_AND_MYTO"][route]
                prices = config["PRICE"]
                euro = config["EURO_RATE"]

                extra_km = st.number_input("Additional Distance (Total KM)", value=0, step=10)
                
                # Obliczanie dystansów
                dist_pl = r_info["distPL"]
                dist_eu = r_info["distEU"] + extra_km
                total_km = dist_pl + dist_eu

            with c2:
                st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
                st.subheader("Technical Margin Analysis")
                
                # Kalkulacja paliwa (Bak w PL -> Reszta EU)
                total_fuel_liters = total_km * v_info["fuelUsage"]
                pl_liters = min(total_fuel_liters, v_info["tankCapacity"])
                eu_liters = max(0, total_fuel_liters - pl_liters)
                
                cost_fuel = (pl_liters * prices["fuelPLN"]) + (eu_liters * prices["fuelEUR"] * euro)
                
                # Pozostałe koszty techniczne
                cost_adblue = (total_km * v_info["adBlueUsage"]) * prices["adBluePLN"]
                cost_service = (dist_pl * v_info["serviceCostPLN"]) + (dist_eu * v_info["serviceCostEUR"] * euro)
                
                myto_key = f"myto{v_type}"
                cost_myto = r_info.get(myto_key, 0)

                total_sum = cost_fuel + cost_adblue + cost_service + cost_myto

                st.metric(label="TOTAL TECHNICAL COST (PLN)", value=f"{round(total_sum, 2)} zł")
                
                with st.expander("👁️ SHOW DETAILED LOGS"):
                    st.write(f"⛽ Fuel Costs: **{round(cost_fuel, 2)} PLN**")
                    st.write(f"💧 AdBlue Fluids: **{round(cost_adblue, 2)} PLN**")
                    st.write(f"🛠️ Service & Wear: **{round(cost_service, 2)} PLN**")
                    st.write(f"🛣️ Tolls/Myto: **{round(cost_myto, 2)} PLN**")
                    st.write("---")
                    st.write(f"📏 Distance Analysis: **{total_km} KM** ({dist_pl} PL / {dist_eu} EU)")
                st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 2: PANEL ADMINA ---
        with tab2:
            st.subheader("Authentication Required")
            pwd = st.text_input("Vorteza Master Key", type="password")
            
            if pwd == ADMIN_PASSWORD:
                st.success("Access Granted.")
                st.write("---")
                
                a1, a2, a3 = st.columns(3)
                with a1:
                    new_euro = st.number_input("EURO Exchange Rate", value=config["EURO_RATE"], format="%.4f")
                with a2:
                    new_fuel_pl = st.number_input("Fuel Price PL (PLN/L)", value=config["PRICE"]["fuelPLN"])
                with a3:
                    new_fuel_eu = st.number_input("Fuel Price EU (EUR/L)", value=config["PRICE"]["fuelEUR"])
                
                if st.button("PUSH DATA TO VORTEZA CLOUD"):
                    config["EURO_RATE"] = new_euro
                    config["PRICE"]["fuelPLN"] = new_fuel_pl
                    config["PRICE"]["fuelEUR"] = new_fuel_eu
                    
                    if update_github_data(config, file_sha):
                        st.success("Cloud Synchronized.")
                        st.rerun()
            elif pwd != "":
                st.error("Authentication Failed.")
    else:
        st.error("SYSTEM HALT: FAILED TO LOAD CONFIG.JSON FROM VORTEZA SYSTEMS.")
