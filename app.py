import streamlit as st
import pandas as pd
import json
import requests
import base64
from PIL import Image
import io

# =========================================================
# KONFIGURACJA GITHUB - Z SECRETS
# =========================================================
try:
    GITHUB_TOKEN = st.secrets["G_TOKEN"]
except:
    GITHUB_TOKEN = "BRAK_TOKENA"

REPO_OWNER = "natpio"
REPO_NAME = "rentownosc-transportu"
FILE_PATH = "config.json"
ADMIN_PASSWORD = "admin" # Możesz zmienić w kodzie, lub przenieść do Secrets

# =========================================================
# FUNKCJE OPERACYJNE (TŁO Z PLIKU PNG)
# =========================================================

# Funkcja konwertująca plik binarny na Base64
@st.cache_data # Zapamiętujemy tło, żeby nie konwertować go co chwilę
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Funkcja ustawiająca tło z pliku
def set_bg_from_file(png_bg_img):
    bin_str = get_base64_of_bin_file(png_bg_img)
    page_bg_img = f'''
    <style>
    /* Ustawiamy tło na głównym kontenerze aplikacji */
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover; /* Pokrywa cały ekran */
        background-attachment: fixed; /* Nieruchome tło (paralaksa) */
        background-position: center; /* Wyśrodkowane */
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Funkcja pobierania danych z GitHub (z cachingiem)
@st.cache_data(ttl=60) # Dane cache'ujemy na 60 sekund
def get_github_data():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        content = response.json()
        decoded_content = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(decoded_content), content['sha']
    else:
        # Błędy wyświetlamy tylko raz, nie w pętli
        if response.status_code == 401:
            st.error("Błąd 401: Token G_TOKEN jest nieprawidłowy.")
        elif response.status_code == 404:
            st.error(f"Błąd 404: Nie znaleziono pliku {FILE_PATH} w repozytorium.")
        else:
            st.error(f"Błąd połączenia: {response.status_code}.")
        return None, None

def update_github_data(new_data, sha):
    """Zapisuje zaktualizowany plik config.json na GitHub."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    updated_content = json.dumps(new_data, indent=4, ensure_ascii=False)
    encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": "VORTEZA - Update stawek bazowych",
        "content": encoded_content,
        "sha": sha
    }
    
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code in [200, 201]

# =========================================================
# GŁÓWNA APLIKACJA Streamlit
# =========================================================

st.set_page_config(page_title="VORTEZA SYSTEMS - Trace", layout="wide")

# --- WDROŻENIE TŁA I STYLIZACJI (COPPER DESIGN) ---
try:
    # Zakładamy, że wrzuciłeś plik i nazwałeś go 'bg_vorteza.png'
    set_bg_from_file('bg_vorteza.png')
except FileNotFoundError:
    # Fallback, jeśli pliku nie ma
    st.markdown("<style>.stApp {background-color: #0E0E0E;}</style>", unsafe_allow_html=True)

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');

        /* Główne kolory */
        :root {
            --v-copper: #B58863; /* Miedź/Złoto z logo */
            --v-text: #E0E0E0;
        }

        .stApp {
            color: var(--v-text);
            font-family: 'Montserrat', sans-serif;
        }

        /* Nagłówki - Miedziane */
        h1, h2, h3, .stSubheader {
            color: var(--v-copper) !important;
            font-weight: 700 !important;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        /* Kontener Wyniku (Półprzezroczysty Panel) */
        div[data-testid="stVerticalBlock"] > div:has(div.vorteza-card) {
            background-color: rgba(26, 26, 26, 0.85) !important; /* Przezroczyste tło panelu */
            backdrop-filter: blur(10px); /* Rozmycie tła pod panelem */
            padding: 25px;
            border-radius: 5px;
            border: 1px solid rgba(181, 136, 99, 0.3); /* Delikatna miedziana ramka */
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        }

        /* Metryka */
        [data-testid="stMetricValue"] {
            color: var(--v-copper) !important;
            font-size: 3rem !important;
            font-weight: 700 !important;
        }
        [data-testid="stMetricLabel"] {
            color: #888 !important;
            text-transform: uppercase;
        }

        /* Zakładki (Tabs) - Półprzezroczyste */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: rgba(0,0,0,0.4) !important;
            padding: 5px;
            border-radius: 5px;
        }
        .stTabs [data-baseweb="tab"] {
            color: #A0A0A0;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] {
            color: var(--v-copper) !important;
            border-bottom: 2px solid var(--v-copper) !important;
        }

        /* Przyciski */
        .stButton > button {
            background-color: transparent;
            color: var(--v-copper);
            border: 1px solid var(--v-copper);
            border-radius: 0px;
            width: 100%;
            font-weight: 700;
        }
        .stButton > button:hover {
            background-color: var(--v-copper);
            color: #000;
        }

        /* Inputy */
        input, div[data-baseweb="select"] {
            background-color: rgba(30,30,30,0.9) !important;
            border: 1px solid #444 !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- LOGO I NAGŁÓWEK ---
col_logo, col_space = st.columns([1, 4])
with col_logo:
    try:
        # Zakładamy, że masz logo o nazwie 'logo_vorteza.png'
        st.image(Image.open('logo_vorteza.png'), use_container_width=True)
    except:
        st.title("VORTEZA")

if GITHUB_TOKEN == "BRAK_TOKENA":
    st.warning("HalT: Dodaj G_TOKEN do Secrets w Streamlit Cloud.")
else:
    # Pobranie danych na start
    config, file_sha = get_github_data()

    if config:
        # Zakładki: Zmieniamy nazwy na VORTEZA TRACE
        tab1, tab2 = st.tabs(["📊 VORTEZA MARGIN", "⚙️ SYSTEM CONFIG"])

        # --- TAB 1: KALKULATOR ---
        with tab1:
            c1, c2 = st.columns([1, 1], gap="large")
            
            with c1:
                st.subheader("Transport Configuration")
                v_type = st.selectbox("Vehicle Type", list(config["VEHICLE_DATA"].keys()))
                route = st.selectbox("Route Destination", list(config["DISTANCES_AND_MYTO"].keys()))
                
                v_info = config["VEHICLE_DATA"][v_type]
                r_info = config["DISTANCES_AND_MYTO"][route]
                prices = config["PRICE"]
                euro = config["EURO_RATE"]

                extra_km = st.number_input("Extra KM (adjustment)", value=0, step=10)
                
                # Obliczenia dystansów
                dist_pl = r_info["distPL"]
                dist_eu = r_info["distEU"] + extra_km
                total_km = dist_pl + dist_eu

            with c2:
                # Oznaczamy panel dla stylizacji
                st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
                st.subheader("Margin Analysis")
                
                # --- LOGIKA OBLICZEŃ (Logistyka Piotr Dukiel) ---
                
                # 1. Paliwo: Bak w PL -> Reszta EU
                total_fuel_liters = total_km * v_info["fuelUsage"]
                pl_liters = min(total_fuel_liters, v_info["tankCapacity"])
                eu_liters = max(0, total_fuel_liters - pl_liters)
                
                # Koszt paliwa (przeliczony z EUR -> PLN)
                cost_fuel = (pl_liters * prices["fuelPLN"]) + (eu_liters * prices["fuelEUR"] * euro)
                
                # 2. AdBlue
                cost_adblue = (total_km * v_info["adBlueUsage"]) * prices["adBluePLN"]
                
                # 3. Serwis (Zależny od kraju PL / EU)
                cost_service = (dist_pl * v_info["serviceCostPLN"]) + (dist_eu * v_info["serviceCostEUR"] * euro)
                
                # 4. Myto (zależy od Typu Pojazdu)
                myto_key = f"myto{v_type}"
                cost_myto = r_info.get(myto_key, 0)

                # Całkowity koszt techniczny
                grand_total = cost_fuel + cost_adblue + cost_service + cost_myto

                st.metric(label="TOTAL TECHNICAL COST (PLN)", value=f"{round(grand_total, 2)} zł")
                
                with st.expander("👁️ Detailed Logistics Analysis"):
                    st.write(f"⛽ Fuel Total: **{round(cost_fuel, 2)} PLN**")
                    st.write(f"💧 AdBlue Fluids: **{round(cost_adblue, 2)} PLN**")
                    st.write(f"🛠️ Service & Maintenance: **{round(cost_service, 2)} PLN**")
                    st.write(f"🛣️ Tolls (Myto): **{round(cost_myto, 2)} PLN**")
                    st.divider()
                    st.write(f"📏 Dystans: **{total_km} km** ({dist_pl} PL / {dist_eu} EU)")
                st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 2: PANEL ADMINA ---
        with tab2:
            st.subheader("Vorteza Master Access")
            pwd = st.text_input("Master Key", type="password")
            
            if pwd == ADMIN_PASSWORD:
                st.success("Access Granted.")
                
                col_a1, col_a2, col_a3 = st.columns(3)
                with col_a1:
                    new_euro = st.number_input("Kurs EURO (PLN)", value=config["EURO_RATE"], step=0.001)
                with col_a2:
                    new_f_pl = st.number_input("Paliwo PL (PLN/L)", value=config["PRICE"]["fuelPLN"], step=0.01)
                with col_a3:
                    new_f_eu = st.number_input("Paliwo EU (EUR/L)", value=config["PRICE"]["fuelEUR"], step=0.01)
                
                if st.button("PUSH NEW RATES TO CLOUD"):
                    config["EURO_RATE"] = new_euro
                    config["PRICE"]["fuelPLN"] = new_f_pl
                    config["PRICE"]["fuelEUR"] = new_f_eu
                    
                    if update_github_data(config, file_sha):
                        st.success("Stawki zaktualizowane pomyślnie. Cache wyczyszczony.")
                        st.cache_data.clear() # Czyścimy cache
                        st.rerun() # Przeładowujemy stronę
                    else:
                        st.error("Błąd zapisu. Sprawdź konfigurację GitHub.")
            elif pwd != "":
                st.error("Invalid Authentication.")
    else:
        st.error("Nie udało się połączyć z VORTEZA Cloud (config.json).")
