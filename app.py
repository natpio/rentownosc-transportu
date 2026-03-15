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
# FUNKCJE GRAFICZNE I STYLIZACJA (DESIGN VORTEZA)
# =========================================================

def get_base64_of_bin_file(bin_file):
    """Odczytuje plik binarny i konwertuje go na Base64 dla CSS."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def apply_vorteza_design():
    """Wdraża tło z pliku i miedziany interfejs."""
    try:
        # Zakładamy, że plik tła nazywa się bg_vorteza.jpg
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

    # Stylizacja komponentów
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
        
        .stApp {
            color: #E0E0E0;
            font-family: 'Montserrat', sans-serif;
        }

        /* Miedziane nagłówki */
        h1, h2, h3, .stSubheader {
            color: #B58863 !important;
            font-weight: 700 !important;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        /* Przezroczyste karty dla czytelności na tle karbonu */
        div[data-testid="stVerticalBlock"] > div:has(div.vorteza-card) {
            background-color: rgba(15, 15, 15, 0.85) !important;
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 10px;
            border: 1px solid rgba(181, 136, 99, 0.3);
            box-shadow: 0 15px 35px rgba(0,0,0,0.7);
        }

        /* Metryki finansowe */
        [data-testid="stMetricValue"] {
            color: #B58863 !important;
            font-size: 3.5rem !important;
            font-weight: 700 !important;
        }
        
        /* Stylizacja przycisków */
        .stButton > button {
            background-color: transparent;
            color: #B58863;
            border: 1px solid #B58863;
            border-radius: 4px;
            width: 100%;
            height: 3em;
            font-weight: 700;
        }
        .stButton > button:hover {
            background-color: #B58863;
            color: #000;
            border: 1px solid #B58863;
        }

        /* Zakładki (Tabs) */
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(0,0,0,0.6);
            padding: 10px;
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            color: #888;
        }
        .stTabs [aria-selected="true"] {
            color: #B58863 !important;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# LOGIKA OPERACYJNA GITHUB
# =========================================================

def get_config():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = res.json()
        decoded = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(decoded), content['sha']
    return None, None

def save_config(new_data, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    encoded = base64.b64encode(json.dumps(new_data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    payload = {"message": "Update Vorteza Rates", "content": encoded, "sha": sha}
    return requests.put(url, headers=headers, json=payload).status_code in [200, 201]

# =========================================================
# GŁÓWNA APLIKACJA
# =========================================================

st.set_page_config(page_title="VORTEZA SYSTEMS", layout="wide")
apply_vorteza_design()

# Header z logo (Pamiętaj o wrzuceniu przezroczystego logo_vorteza.png)
c_logo, _ = st.columns([1, 4])
with c_logo:
    try:
        st.image(Image.open('logo_vorteza.png'), use_container_width=True)
    except:
        st.title("VORTEZA SYSTEMS")

if GITHUB_TOKEN == "BRAK":
    st.error("Błąd: Skonfiguruj G_TOKEN w Secrets.")
else:
    config, sha = get_config()

    if config:
        t1, t2 = st.tabs(["📊 VORTEZA MARGIN", "⚙️ SYSTEM CORE"])

        with t1:
            col_in, col_out = st.columns([1, 1], gap="large")
            
            with col_in:
                st.subheader("Parametry transportu")
                v_type = st.selectbox("Jednostka", list(config["VEHICLE_DATA"].keys()))
                route = st.selectbox("Kierunek", list(config["DISTANCES_AND_MYTO"].keys()))
                
                v = config["VEHICLE_DATA"][v_type]
                r = config["DISTANCES_AND_MYTO"][route]
                extra_km = st.number_input("Dodatkowe kilometry", value=0, step=10)
                
                total_km = r["distPL"] + r["distEU"] + extra_km

            with col_out:
                st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
                st.subheader("Kalkulacja kosztów")
                
                # Obliczenia paliwa (PL do pełna, reszta EU)
                total_fuel = total_km * v["fuelUsage"]
                f_pl = min(total_fuel, v["tankCapacity"])
                f_eu = max(0, total_fuel - f_pl)
                cost_fuel = (f_pl * config["PRICE"]["fuelPLN"]) + (f_eu * config["PRICE"]["fuelEUR"] * config["EURO_RATE"])
                
                # Pozostałe składowe
                cost_adblue = (total_km * v["adBlueUsage"]) * config["PRICE"]["adBluePLN"]
                cost_service = (r["distPL"] * v["serviceCostPLN"]) + ((r["distEU"] + extra_km) * v["serviceCostEUR"] * config["EURO_RATE"])
                cost_myto = r.get(f"myto{v_type}", 0)

                total_cost = cost_fuel + cost_adblue + cost_service + cost_myto

                st.metric("KOSZT TECHNICZNY (PLN)", f"{round(total_cost, 2)} zł")
                
                with st.expander("Rozbicie kosztów operacyjnych"):
                    st.write(f"⛽ Paliwo: **{round(cost_fuel, 2)} PLN**")
                    st.write(f"🛣️ Myto: **{round(cost_myto, 2)} PLN**")
                    st.write(f"🛠️ Serwis: **{round(cost_service, 2)} PLN**")
                    st.write(f"📏 Dystans: **{total_km} km**")
                st.markdown('</div>', unsafe_allow_html=True)

        with t2:
            st.subheader("Ustawienia systemowe")
            if st.text_input("Hasło", type="password") == ADMIN_PASSWORD:
                ca1, ca2, ca3 = st.columns(3)
                with ca1:
                    new_e = st.number_input("Kurs EUR", value=config["EURO_RATE"], format="%.4f")
                with ca2:
                    new_fpl = st.number_input("Paliwo PL", value=config["PRICE"]["fuelPLN"])
                with ca3:
                    new_feu = st.number_input("Paliwo EU", value=config["PRICE"]["fuelEUR"])
                
                if st.button("ZAPISZ ZMIANY W CHMURZE"):
                    config["EURO_RATE"] = new_e
                    config["PRICE"]["fuelPLN"] = new_fpl
                    config["PRICE"]["fuelEUR"] = new_feu
                    if save_config(config, sha):
                        st.success("Zaktualizowano pomyślnie.")
                        st.rerun()
    else:
        st.error("Błąd połączenia z bazą config.json.")
