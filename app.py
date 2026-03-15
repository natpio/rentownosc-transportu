import streamlit as st
import pandas as pd
import json
import requests
import base64

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
ADMIN_PASSWORD = "admin" # Zalecana zmiana w Secrets

# =========================================================
# STYLIZACJA PREMIUM (DARK & COPPER)
# =========================================================
def apply_custom_style():
    st.markdown("""
        <style>
            /* Główn tło i kolory tekstu */
            .stApp {
                background-color: #121212;
                color: #E0E0E0;
            }
            
            /* Nagłówki - Kolor miedziany/złoty */
            h1, h2, h3, .stSubheader {
                color: #B58863 !important; /* Przykładowy kolor miedziany z logo */
                font-family: 'Montserrat', sans-serif;
                font-weight: 700;
            }

            /* Unikalny styl dla głównego tytułu z logo */
            .main-title {
                font-size: 2.5rem;
                display: flex;
                align-items: center;
                gap: 15px;
                padding-bottom: 20px;
                border-bottom: 2px solid #333;
            }

            /* Stylizowanie Tabs (zakładek) */
            .stTabs [data-baseweb="tab-list"] {
                gap: 10px;
                background-color: #1E1E1E;
                padding: 10px;
                border-radius: 10px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                background-color: transparent;
                border-radius: 5px;
                color: #A0A0A0;
                border: none;
            }
            .stTabs [aria-selected="true"] {
                background-color: #333333 !important;
                color: #B58863 !important;
                font-weight: bold;
            }

            /* Stylizowanie bocznego paska (jeśli używany) */
            [data-testid="stSidebar"] {
                background-color: #1E1E1E;
                border-right: 1px solid #333;
            }

            /* Stylizowanie kontenerów (np. c2 z wynikami) */
            [data-testid="stVerticalBlock"] > div:has(div.metric-container) {
                background-color: #1E1E1E;
                padding: 20px;
                border-radius: 15px;
                border: 1px solid #333;
            }

            /* Własny styl dla Metric */
            [data-testid="stMetricValue"] {
                color: #B58863 !important;
                font-size: 3rem !important;
            }
            [data-testid="stMetricLabel"] {
                color: #A0A0A0 !important;
            }

            /* Przyciski */
            .stButton > button {
                background-color: transparent;
                color: #B58863;
                border: 2px solid #B58863;
                border-radius: 20px;
                padding: 10px 24px;
                transition: all 0.3s;
            }
            .stButton > button:hover {
                background-color: #B58863;
                color: #121212;
            }

            /* Expander */
            .stExpander {
                background-color: #1E1E1E;
                border: 1px solid #333;
                border-radius: 10px;
            }

            /* Inputy (number, selectbox) */
            div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
                background-color: #1E1E1E !important;
                color: #E0E0E0 !important;
                border-color: #333 !important;
            }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# FUNKCJE OPERACYJNE (BEZ ZMIAN)
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
    payload = {"message": "Aktualizacja stawek bazowych", "content": encoded, "sha": sha}
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code in [200, 201]

# =========================================================
# GŁÓWNA APLIKACJA
# =========================================================

st.set_page_config(page_title="VORTEZA TRACE - Kalkulator Kosztów", layout="wide", page_icon="🚚")

# Wdrożenie stylów
apply_custom_style()

# Nagłówek z LOGO VORTEZA (Używamy Emoji zamiast obrazka, dopóki nie masz pliku logo)
st.markdown('<div class="main-title">📈 VORTEZA <span style="font-weight:300; font-size:1.5rem;">Logistics Intelligence</span></div>', unsafe_allow_html=True)

if GITHUB_TOKEN == "BRAK":
    st.error("Błąd: Skonfiguruj G_TOKEN w Secrets!")
else:
    config, file_sha = get_github_data()

    if config:
        # Zmieniamy nazwy zakładek na bardziej spójne ze stylem (np. VORTEZA MARGIN)
        tabs = st.tabs(["📊 VORTEZA MARGIN - Kalkulator", "⚙️ Konfiguracja Systemu"])

        with tabs[0]:
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.subheader("Parametry Transportu")
                v_type = st.selectbox("Typ pojazdu", list(config["VEHICLE_DATA"].keys()))
                route = st.selectbox("Kierunek docelowy", list(config["DISTANCES_AND_MYTO"].keys()))
                
                v_info = config["VEHICLE_DATA"][v_type]
                r_info = config["DISTANCES_AND_MYTO"][route]
                prices = config["PRICE"]
                euro = config["EURO_RATE"]

                extra_km = st.number_input("Dodatkowe kilometry (objazdy, puste)", value=0)
                dist_pl = r_info["distPL"]
                dist_eu = r_info["distEU"] + extra_km
                total_km = dist_pl + dist_eu

            with c2:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.subheader("Całkowity Koszt Techniczny")
                
                # Obliczenia paliwa (logika z poprzedniego kroku)
                total_fuel = total_km * v_info["fuelUsage"]
                fuel_pl_liters = min(total_fuel, v_info["tankCapacity"])
                fuel_eu_liters = max(0, total_fuel - fuel_pl_liters)
                cost_fuel = (fuel_pl_liters * prices["fuelPLN"]) + (fuel_eu_liters * prices["fuelEUR"] * euro)
                
                # AdBlue, Serwis, Myto
                cost_adblue = (total_km * v_info["adBlueUsage"]) * prices["adBluePLN"]
                cost_service = (dist_pl * v_info["serviceCostPLN"]) + (dist_eu * v_info["serviceCostEUR"] * euro)
                myto_key = f"myto{v_type}"
                cost_myto = r_info.get(myto_key, 0)

                total_sum = cost_fuel + cost_adblue + cost_service + cost_myto

                st.metric(label="KOSZT CAŁKOWITY (PLN)", value=f"{round(total_sum, 2)} zł")
                
                with st.expander("👁️ Pokaż szczegółowe rozbicie kosztów"):
                    st.write(f"⛽ Paliwo suma: **{round(cost_fuel, 2)} PLN**")
                    st.write(f"💧 AdBlue: **{round(cost_adblue, 2)} PLN**")
                    st.write(f"🛠️ Serwis/Eksploatacja: **{round(cost_service, 2)} PLN**")
                    st.write(f"🛣️ Myto: **{round(cost_myto, 2)} PLN**")
                    st.write("---")
                    st.write(f"📏 Dystans: **{total_km} km** ({dist_pl} PL / {dist_eu} EU)")
                st.markdown('</div>', unsafe_allow_html=True)

        with tabs[1]:
            st.subheader("Panel Administracyjny Systemu")
            pwd = st.text_input("Hasło dostępu", type="password")
            if pwd == ADMIN_PASSWORD:
                st.success("Dostęp autoryzowany")
                
                col_a1, col_a2, col_a3 = st.columns(3)
                with col_a1:
                    new_euro = st.number_input("Kurs EURO (PLN)", value=config["EURO_RATE"], step=0.001)
                with col_a2:
                    new_f_pl = st.number_input("Paliwo PL (PLN/L)", value=config["PRICE"]["fuelPLN"], step=0.01)
                with col_a3:
                    new_f_eu = st.number_input("Paliwo EU (EUR/L)", value=config["PRICE"]["fuelEUR"], step=0.01)
                
                st.write("---")
                if st.button("ZAPISZ NOWE STAWKI BAZOWE"):
                    config["EURO_RATE"] = new_euro
                    config["PRICE"]["fuelPLN"] = new_f_pl
                    config["PRICE"]["fuelEUR"] = new_f_eu
                    if update_github_data(config, file_sha):
                        st.success("Zmiany zapisane w repozytorium VORTEZA.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Błąd zapisu. Sprawdź konfigurację GitHub.")
            elif pwd != "":
                st.error("Błędne hasło")
    else:
        st.error("Nie udało się pobrać konfiguracji z VORTEZA Systems.")
