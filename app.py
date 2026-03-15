import streamlit as st
import pandas as pd
import json
import requests
import base64
from PIL import Image
import io

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
# FUNKCJE GRAFICZNE I STYLIZACJA (POWRÓT DO ORIGINAŁU)
# =========================================================

def get_base64_of_bin_file(bin_file):
    """Konwertuje obraz na base64, aby CSS mógł go użyć jako tło."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def apply_vorteza_classic_theme():
    """Wdraża karbonowe tło i miedziany interfejs."""
    try:
        # Próba wczytania Twojego tła karbonowego
        bg_base64 = get_base64_of_bin_file('bg_vorteza.jpg')
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpeg;base64,{bg_base64}");
                background-size: cover;
                background-attachment: fixed;
                background-position: center;
            }}
            </style>
        """, unsafe_allow_html=True)
    except:
        st.markdown("<style>.stApp { background-color: #0E0E0E; }</style>", unsafe_allow_html=True)

    # Globalna stylizacja UI
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
        
        .stApp {
            color: #E0E0E0;
            font-family: 'Montserrat', sans-serif;
        }

        /* Miedziane akcenty - Kolor z logo */
        h1, h2, h3, .stSubheader {
            color: #B58863 !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Stylizacja kart wyników (Margin Card) */
        div[data-testid="stVerticalBlock"] > div:has(div.vorteza-card) {
            background-color: rgba(15, 15, 15, 0.9) !important;
            backdrop-filter: blur(12px);
            padding: 30px;
            border-radius: 4px;
            border-left: 5px solid #B58863;
            box-shadow: 0 20px 40px rgba(0,0,0,0.8);
        }

        /* Główne liczby (Metryki) */
        [data-testid="stMetricValue"] {
            color: #B58863 !important;
            font-size: 3.5rem !important;
            font-weight: 700 !important;
        }
        
        /* Przyciski w stylu VORTEZA */
        .stButton > button {
            background-color: transparent;
            color: #B58863;
            border: 1px solid #B58863;
            border-radius: 0px;
            font-weight: 700;
            text-transform: uppercase;
            transition: 0.4s;
        }
        .stButton > button:hover {
            background-color: #B58863;
            color: #000;
            box-shadow: 0 0 20px rgba(181, 136, 99, 0.4);
        }

        /* Zakładki (Tabs) */
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(30, 30, 30, 0.7);
            padding: 10px;
            border-radius: 0px;
        }
        .stTabs [aria-selected="true"] {
            color: #B58863 !important;
            border-bottom: 2px solid #B58863 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# LOGIKA POBIERANIA DANYCH
# =========================================================

def get_config_from_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        decoded = base64.b64decode(data['content']).decode('utf-8')
        return json.loads(decoded), data['sha']
    return None, None

def save_config_to_github(new_data, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    encoded = base64.b64encode(json.dumps(new_data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    payload = {"message": "System Update: Vorteza Rates", "content": encoded, "sha": sha}
    return requests.put(url, headers=headers, json=payload).status_code in [200, 201]

# =========================================================
# GŁÓWNA STRUKTURA APLIKACJI
# =========================================================

st.set_page_config(page_title="VORTEZA SYSTEMS | LOGISTICS", layout="wide")
apply_vorteza_classic_theme()

# Header z poprzednim logo
c_logo, _ = st.columns([1, 4])
with c_logo:
    try:
        # Ładujemy plik logo_vorteza.jpg (to z heksagonami)
        st.image(Image.open('logo_vorteza.jpg'), use_column_width=True)
    except:
        st.title("VORTEZA SYSTEMS")

if GITHUB_TOKEN == "BRAK":
    st.error("Błąd: Skonfiguruj G_TOKEN w Secrets!")
else:
    config, current_sha = get_config_from_github()

    if config:
        tabs = st.tabs(["📊 VORTEZA MARGIN", "⚙️ SYSTEM CONFIG"])

        with tabs[0]:
            col_in, col_out = st.columns([1, 1], gap="large")
            
            with col_in:
                st.subheader("Transport Input")
                v_type = st.selectbox("Vehicle Type", list(config["VEHICLE_DATA"].keys()))
                route = st.selectbox("Destination", list(config["DISTANCES_AND_MYTO"].keys()))
                
                v = config["VEHICLE_DATA"][v_type]
                r = config["DISTANCES_AND_MYTO"][route]
                extra_km = st.number_input("Adjustment KM", value=0, step=10)
                
                total_km = r["distPL"] + r["distEU"] + extra_km

            with col_out:
                st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
                st.subheader("Technical Costs")
                
                # Obliczenia paliwa (PL -> EU)
                total_fuel = total_km * v["fuelUsage"]
                f_pl = min(total_fuel, v["tankCapacity"])
                f_eu = max(0, total_fuel - f_pl)
                cost_fuel = (f_pl * config["PRICE"]["fuelPLN"]) + (f_eu * config["PRICE"]["fuelEUR"] * config["EURO_RATE"])
                
                # Reszta składowych
                cost_adblue = (total_km * v["adBlueUsage"]) * config["PRICE"]["adBluePLN"]
                cost_service = (r["distPL"] * v["serviceCostPLN"]) + ((r["distEU"] + extra_km) * v["serviceCostEUR"] * config["EURO_RATE"])
                cost_myto = r.get(f"myto{v_type}", 0)

                grand_total = cost_fuel + cost_adblue + cost_service + cost_myto

                st.metric("GRAND TOTAL (PLN)", f"{round(grand_total, 2)} zł")
                
                with st.expander("👁️ System Log - Detailed Breakdown"):
                    st.write(f"⛽ Fuel: **{round(cost_fuel, 2)} PLN**")
                    st.write(f"🛣️ Tolls/Myto: **{round(cost_myto, 2)} PLN**")
                    st.write(f"🛠️ Service/Wear: **{round(cost_service, 2)} PLN**")
                    st.write(f"💧 AdBlue: **{round(cost_adblue, 2)} PLN**")
                    st.divider()
                    st.write(f"📏 Dystans: {total_km} km")
                st.markdown('</div>', unsafe_allow_html=True)

        with tabs[1]:
            st.subheader("Admin Control Panel")
            if st.text_input("Master Key", type="password") == ADMIN_PASSWORD:
                ca1, ca2, ca3 = st.columns(3)
                with ca1:
                    new_euro = st.number_input("EURO Rate", value=config["EURO_RATE"], format="%.4f")
                with ca2:
                    new_f_pl = st.number_input("Fuel PL (PLN)", value=config["PRICE"]["fuelPLN"])
                with ca3:
                    new_f_eu = st.number_input("Fuel EU (EUR)", value=config["PRICE"]["fuelEUR"])
                
                if st.button("UPDATE CLOUD DATA"):
                    config["EURO_RATE"] = new_euro
                    config["PRICE"]["fuelPLN"] = new_f_pl
                    config["PRICE"]["fuelEUR"] = new_f_eu
                    if save_config_to_github(config, current_sha):
                        st.success("Synchronizacja zakończona.")
                        st.rerun()
    else:
        st.error("Błąd ładowania config.json.")
