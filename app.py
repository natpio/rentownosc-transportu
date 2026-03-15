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
# FUNKCJE STYLIZACJI I GRAFIKI
# =========================================================

def get_base64_of_bin_file(bin_file):
    """Konwertuje plik graficzny na base64 dla CSS."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def apply_vorteza_theme():
    """Wdraża tło karbonowe i miedziany interfejs."""
    try:
        # Zakładamy, że plik nazywa się bg_vorteza.jpg (zgodnie z uploadem)
        bg_base64 = get_base64_of_bin_file('bg_vorteza.jpg')
        bg_style = f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{bg_base64}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
        }}
        </style>
        """
        st.markdown(bg_style, unsafe_allow_html=True)
    except Exception as e:
        st.markdown("<style>.stApp {background-color: #0E0E0E;}</style>", unsafe_allow_html=True)

    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
        
        :root {
            --v-copper: #B58863;
        }

        .stApp {
            color: #E0E0E0;
            font-family: 'Montserrat', sans-serif;
        }

        /* Półprzezroczyste panele dla czytelności */
        div[data-testid="stVerticalBlock"] > div:has(div.vorteza-card) {
            background-color: rgba(20, 20, 20, 0.85) !important;
            backdrop-filter: blur(8px);
            padding: 25px;
            border-radius: 8px;
            border: 1px solid rgba(181, 136, 99, 0.2);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }

        h1, h2, h3, .stSubheader {
            color: var(--v-copper) !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        [data-testid="stMetricValue"] {
            color: var(--v-copper) !important;
            font-size: 3.2rem !important;
            font-weight: 700 !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(0,0,0,0.5);
            border-radius: 5px;
            padding: 5px;
        }
        
        .stButton > button {
            background-color: transparent;
            color: var(--v-copper);
            border: 1px solid var(--v-copper);
            border-radius: 4px;
            font-weight: 700;
            transition: 0.3s;
        }

        .stButton > button:hover {
            background-color: var(--v-copper);
            color: #000;
        }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# FUNKCJE DANYCH
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
    updated_json = json.dumps(new_data, indent=4, ensure_ascii=False)
    encoded = base64.b64encode(updated_json.encode('utf-8')).decode('utf-8')
    payload = {"message": "Update Vorteza Config", "content": encoded, "sha": sha}
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code in [200, 201]

# =========================================================
# GŁÓWNA APLIKACJA
# =========================================================

st.set_page_config(page_title="VORTEZA SYSTEMS", layout="wide")
apply_vorteza_theme()

# Header z Logo (Wczytujemy przezroczysty PNG)
col_l, col_r = st.columns([1, 4])
with col_l:
    try:
        # Pamiętaj, aby wrzucić przezroczyste logo jako 'logo_vorteza.png'
        st.image(Image.open('logo_vorteza.png'), use_container_width=True)
    except:
        st.title("VORTEZA")

if GITHUB_TOKEN == "BRAK":
    st.error("Błąd: Skonfiguruj G_TOKEN w Secrets!")
else:
    config, file_sha = get_github_data()

    if config:
        tab1, tab2 = st.tabs(["📊 VORTEZA MARGIN", "🔐 SYSTEM SETTINGS"])

        with tab1:
            c1, c2 = st.columns([1, 1], gap="large")
            
            with c1:
                st.subheader("Parametry Trasy")
                v_type = st.selectbox("Typ pojazdu", list(config["VEHICLE_DATA"].keys()))
                route = st.selectbox("Kierunek", list(config["DISTANCES_AND_MYTO"].keys()))
                
                v_info = config["VEHICLE_DATA"][v_type]
                r_info = config["DISTANCES_AND_MYTO"][route]
                prices = config["PRICE"]
                euro = config["EURO_RATE"]

                extra_km = st.number_input("Dodatkowe km", value=0, step=10)
                
                dist_pl = r_info["distPL"]
                dist_eu = r_info["distEU"] + extra_km
                total_km = dist_pl + dist_eu

            with c2:
                st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
                st.subheader("Analiza Rentowności")
                
                # Kalkulacja Paliwa
                total_fuel = total_km * v_info["fuelUsage"]
                pl_liters = min(total_fuel, v_info["tankCapacity"])
                eu_liters = max(0, total_fuel - pl_liters)
                cost_fuel = (pl_liters * prices["fuelPLN"]) + (eu_liters * prices["fuelEUR"] * euro)
                
                # AdBlue i Serwis
                cost_adblue = (total_km * v_info["adBlueUsage"]) * prices["adBluePLN"]
                cost_service = (dist_pl * v_info["serviceCostPLN"]) + (dist_eu * v_info["serviceCostEUR"] * euro)
                
                # Myto
                cost_myto = r_info.get(f"myto{v_type}", 0)

                grand_total = cost_fuel + cost_adblue + cost_service + cost_myto

                st.metric("KOSZT CAŁKOWITY", f"{round(grand_total, 2)} PLN")
                
                with st.expander("Szczegóły operacyjne"):
                    st.write(f"⛽ Paliwo: **{round(cost_fuel, 2)} PLN**")
                    st.write(f"🛣️ Myto: **{round(cost_myto, 2)} PLN**")
                    st.write(f"🛠️ Serwis: **{round(cost_service, 2)} PLN**")
                    st.divider()
                    st.write(f"📏 Dystans: {total_km} km ({dist_pl} PL / {dist_eu} EU)")
                st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.subheader("Panel Zarządzania Stawkami")
            pwd = st.text_input("Hasło systemowe", type="password")
            if pwd == ADMIN_PASSWORD:
                a1, a2, a3 = st.columns(3)
                with a1:
                    n_euro = st.number_input("Kurs EUR", value=config["EURO_RATE"])
                with a2:
                    n_f_pl = st.number_input("Paliwo PL", value=config["PRICE"]["fuelPLN"])
                with a3:
                    n_f_eu = st.number_input("Paliwo EU", value=config["PRICE"]["fuelEUR"])
                
                if st.button("AKTUALIZUJ SYSTEM"):
                    config["EURO_RATE"] = n_euro
                    config["PRICE"]["fuelPLN"] = n_f_pl
                    config["PRICE"]["fuelEUR"] = n_f_eu
                    if update_github_data(config, file_sha):
                        st.success("Zapisano w VORTEZA Cloud.")
                        st.rerun()
    else:
        st.error("Błąd ładowania danych z GitHub.")
