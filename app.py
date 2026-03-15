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
# FUNKCJA DO TŁA Z PLIKU
# =========================================================
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_bg_from_file(main_bg_img):
    bin_str = get_base64_of_bin_file(main_bg_img)
    page_bg_img = f'''
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{bin_str}");
        background-size: cover;
        background-attachment: fixed;
    }}
    
    /* Półprzezroczyste panele, żeby tekst był czytelny na ciemnym tle */
    [data-testid="stVerticalBlock"] > div:has(div.vorteza-card) {{
        background-color: rgba(26, 26, 26, 0.85) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(181, 136, 99, 0.3);
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background-color: rgba(26, 26, 26, 0.7) !important;
    }}

    h1, h2, h3, .stSubheader, [data-testid="stMetricValue"] {{
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# =========================================================
# START APLIKACJI
# =========================================================
st.set_page_config(page_title="VORTEZA SYSTEMS | TRACE", layout="wide")

# Próba wczytania tła
try:
    set_bg_from_file('bg_vorteza.jpg')
except:
    st.markdown("<style>.stApp {background-color: #0E0E0E;}</style>", unsafe_allow_html=True)

# Reszta stylizacji (miedziane akcenty)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
    :root { --v-copper: #B58863; }
    .stApp { color: #E0E0E0; font-family: 'Montserrat', sans-serif; }
    h1, h2, h3, .stSubheader { color: var(--v-copper) !important; font-weight: 700 !important; text-transform: uppercase; }
    [data-testid="stMetricValue"] { color: var(--v-copper) !important; font-size: 3rem !important; }
    .stButton > button { background-color: rgba(0,0,0,0.5); color: var(--v-copper); border: 1px solid var(--v-copper); font-weight: 700; }
    .stButton > button:hover { background-color: var(--v-copper); color: #000; }
    input, div[data-baseweb="select"] { background-color: rgba(30,30,30,0.9) !important; border: 1px solid #444 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Header z Logo
col_l, _ = st.columns([1, 4])
with col_l:
    try:
        st.image(Image.open('logo_vorteza.png'), use_container_width=True)
    except:
        st.title("VORTEZA SYSTEMS")

# Logika danych (bez zmian)
if GITHUB_TOKEN == "BRAK":
    st.error("SYSTEM ERROR: BRAK G_TOKEN.")
else:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    
    if res.status_code == 200:
        data = res.json()
        config = json.loads(base64.b64decode(data['content']).decode('utf-8'))
        sha = data['sha']

        tab1, tab2 = st.tabs(["📊 VORTEZA MARGIN", "⚙️ SYSTEM CORE"])

        with tab1:
            c1, c2 = st.columns([1, 1], gap="large")
            with c1:
                st.subheader("Transport Configuration")
                v_type = st.selectbox("Vehicle Unit", list(config["VEHICLE_DATA"].keys()))
                route = st.selectbox("Destination", list(config["DISTANCES_AND_MYTO"].keys()))
                extra_km = st.number_input("Extra KM", value=0)
                
                v = config["VEHICLE_DATA"][v_type]
                r = config["DISTANCES_AND_MYTO"][route]
                
                total_km = r["distPL"] + r["distEU"] + extra_km
            
            with c2:
                st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
                st.subheader("Margin Analysis")
                
                # Uproszczone obliczenie dla testu wyglądu
                fuel_cost = (total_km * v["fuelUsage"]) * config["PRICE"]["fuelPLN"]
                myto = r.get(f"myto{v_type}", 0)
                total = fuel_cost + myto + (total_km * v["serviceCostPLN"])
                
                st.metric("ESTIMATED COST", f"{round(total, 2)} PLN")
                st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.subheader("Admin Access")
            if st.text_input("Key", type="password") == ADMIN_PASSWORD:
                st.success("Authenticated")
                # Tu możesz dodać resztę edycji...
    else:
        st.error("Nie znaleziono pliku config.json")
