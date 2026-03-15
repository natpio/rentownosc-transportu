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
# FUNKCJE POMOCNICZE DANYCH
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
# STYLIZACJA VORTEZA SYSTEMS (PREMIUM DARK & COPPER)
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
                --v-panel: rgba(20, 20, 20, 0.9);
                --v-text: #E0E0E0;
            }

            .stApp {
                color: var(--v-text);
                font-family: 'Montserrat', sans-serif;
            }

            /* NAGŁÓWKI */
            h1, h2, h3, .stSubheader {
                color: var(--v-copper) !important;
                font-weight: 700 !important;
                letter-spacing: 1px;
                text-transform: uppercase;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }

            /* ETYKIETY FORMULARZY - POPRAWA WIDOCZNOŚCI */
            label[data-testid="stWidgetLabel"] {
                color: var(--v-copper) !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                letter-spacing: 1.2px;
                font-size: 0.9rem !important;
                background-color: rgba(0,0,0,0.2);
                padding: 2px 5px;
                border-radius: 3px;
            }

            /* INPUTY I SELECTBOXY */
            div[data-baseweb="select"] > div, input {
                background-color: rgba(15, 15, 15, 0.9) !important;
                color: white !important;
                border: 1px solid #444 !important;
            }
            
            /* STYLIZACJA KARTY WYNIKÓW */
            div[data-testid="stVerticalBlock"] > div:has(div.vorteza-card) {
                background-color: var(--v-panel);
                padding: 30px;
                border-radius: 5px;
                border-left: 5px solid var(--v-copper);
                box-shadow: 0 10px 40px rgba(0,0,0,0.8);
                backdrop-filter: blur(15px);
            }

            /* METRYKI */
            [data-testid="stMetricValue"] {
                color: var(--v-copper) !important;
                font-size: 3.2rem !important;
                font-weight: 700 !important;
            }
            [data-testid="stMetricLabel"] {
                color: #999 !important;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            /* PRZYCISKI */
            .stButton > button {
                background-color: rgba(0, 0, 0, 0.7);
                color: var(--v-copper);
                border: 1px solid var(--v-copper);
                border-radius: 0px;
                padding: 15px 30px;
                width: 100%;
                font-weight: 700;
                transition: 0.4s ease;
                text-transform: uppercase;
            }
            .stButton > button:hover {
                background-color: var(--v-copper);
                color: #000;
                box-shadow: 0 0 20px rgba(181, 136, 99, 0.4);
            }

            /* ZAKŁADKI (TABS) */
            .stTabs [data-baseweb="tab-list"] {
                gap: 10px;
                background-color: rgba(0, 0, 0, 0.5);
                padding: 10px;
                border-radius: 5px;
            }
            .stTabs [data-baseweb="tab"] {
                color: #888;
                font-weight: 400;
            }
            .stTabs [aria-selected="true"] {
                color: var(--v-copper) !important;
                border-bottom: 2px solid var(--v-copper) !important;
            }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# GŁÓWNA KONSTRUKCJA APLIKACJI
# =========================================================
st.set_page_config(page_title="VORTEZA SYSTEMS | LOGISTICS", layout="wide")
apply_vorteza_theme()

# Header z Logo
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        logo = Image.open('logo_vorteza.png')
        st.image(logo, use_container_width=True)
    except:
        st.title("VORTEZA")

if GITHUB_TOKEN == "BRAK":
    st.error("SYSTEM HALT: BRAK G_TOKEN W SEKRETACH STREAMLIT.")
else:
    config, file_sha = get_github_data()

    if config:
        tab1, tab2 = st.tabs(["📊 VORTEZA MARGIN", "⚙️ SYSTEM CORE"])

        # =========================================================
        # --- TAB 1: KALKULATOR RENTOWNOŚCI ---
        # =========================================================
        with tab1:
            c1, c2 = st.columns([1, 1], gap="large")
            
            with c1:
                st.subheader("Transport Configuration")
                
                # Wybór Jednostki
                v_type = st.selectbox("Select Vehicle Unit", list(config["VEHICLE_DATA"].keys()))
                
                # Wybór Punktu Startowego
                start_points = list(config["DISTANCES_AND_MYTO"].keys())
                start_p = st.selectbox("Starting Point", start_points)
                
                # Wybór Celu (filtrowany przez Punkt Startowy)
                available_dests = list(config["DISTANCES_AND_MYTO"][start_p].keys())
                if not available_dests:
                    st.warning(f"No routes defined for {start_p}. Add them in System Core.")
                    route = None
                else:
                    route = st.selectbox("Target Destination", available_dests)
                
                extra_km = st.number_input("Additional Distance (Total KM)", value=0, step=10)
                
                if route:
                    v_info = config["VEHICLE_DATA"][v_type]
                    r_info = config["DISTANCES_AND_MYTO"][start_p][route]
                    prices = config["PRICE"]
                    euro = config["EURO_RATE"]

                    # Obliczenia dystansów
                    dist_pl = r_info["distPL"]
                    dist_eu = r_info["distEU"] + extra_km
                    total_km = dist_pl + dist_eu

            with c2:
                if route:
                    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
                    st.subheader("Technical Margin Analysis")
                    
                    # Logika paliwa: zużycie całkowite -> najpierw tankujemy w PL do pełna (tankCapacity)
                    total_fuel_liters = total_km * v_info["fuelUsage"]
                    pl_liters = min(total_fuel_liters, v_info["tankCapacity"])
                    eu_liters = max(0, total_fuel_liters - pl_liters)
                    
                    # Koszty
                    cost_fuel = (pl_liters * prices["fuelPLN"]) + (eu_liters * prices["fuelEUR"] * euro)
                    cost_adblue = (total_km * v_info["adBlueUsage"]) * prices["adBluePLN"]
                    cost_service = (dist_pl * v_info["serviceCostPLN"]) + (dist_eu * v_info["serviceCostEUR"] * euro)
                    
                    # Myto dynamiczne (myto + NazwaJednostki)
                    myto_key = f"myto{v_type}"
                    cost_myto = r_info.get(myto_key, 0)

                    total_sum = cost_fuel + cost_adblue + cost_service + cost_myto

                    st.metric(label="TOTAL TECHNICAL COST (PLN)", value=f"{round(total_sum, 2)} zł")
                    
                    with st.expander("👁️ VIEW DETAILED TECHNICAL LOGS"):
                        st.write(f"⛽ Fuel Costs: **{round(cost_fuel, 2)} PLN**")
                        st.write(f"💧 AdBlue Fluids: **{round(cost_adblue, 2)} PLN**")
                        st.write(f"🛠️ Service & Maintenance: **{round(cost_service, 2)} PLN**")
                        st.write(f"🛣️ Tolls (Myto): **{round(cost_myto, 2)} PLN**")
                        st.write("---")
                        st.write(f"📊 Fuel Plan: {round(pl_liters)}L (PL) / {round(eu_liters)}L (EU)")
                        st.write(f"📏 Distance: {total_km} KM ({dist_pl} PL / {dist_eu} EU)")
                    st.markdown('</div>', unsafe_allow_html=True)

        # =========================================================
        # --- TAB 2: SYSTEM CORE (ADMIN & DATABASE) ---
        # =========================================================
        with tab2:
            st.subheader("Vorteza Master Access")
            pwd = st.text_input("Vorteza Master Key", type="password")
            
            if pwd == ADMIN_PASSWORD:
                st.success("Authentication Successful.")
                st.write("---")
                
                # --- 1. PARAMETRY EKONOMICZNE ---
                st.markdown("### 1. Global Economic Factors")
                e1, e2, e3 = st.columns(3)
                with e1:
                    new_euro = st.number_input("EURO Exchange Rate", value=config["EURO_RATE"], format="%.4f")
                with e2:
                    new_f_pl = st.number_input("Fuel Price PL (PLN/L)", value=config["PRICE"]["fuelPLN"])
                with e3:
                    new_f_eu = st.number_input("Fuel Price EU (EUR/L)", value=config["PRICE"]["fuelEUR"])
                
                st.write("---")

                # --- 2. ZARZĄDZANIE TRASAMI ---
                st.markdown("### 2. Route & Database Management")
                
                action = st.radio("Choose Action:", ["Add New Route", "Edit / Delete Existing Route"], horizontal=True)

                if action == "Add New Route":
                    st.info("Creating a new logistics entry.")
                    col_start, col_dest = st.columns(2)
                    with col_start:
                        starts = list(config["DISTANCES_AND_MYTO"].keys())
                        s_city = st.selectbox("Start Point", ["+ ADD NEW POINT"] + starts)
                        if s_city == "+ ADD NEW POINT":
                            s_city = st.text_input("Type New Starting City Name")
                    with col_dest:
                        d_city = st.text_input("Destination City Name")
                    
                    # Wartości domyślne dla nowej trasy
                    v_pl, v_eu, v_mftl, v_msolo, v_mbus = 100, 500, 0, 0, 0

                else: # EDIT / DELETE
                    st.info("Modifying existing database records.")
                    col_start, col_dest = st.columns(2)
                    with col_start:
                        s_city = st.selectbox("Select Start Point", list(config["DISTANCES_AND_MYTO"].keys()))
                    with col_dest:
                        dests = list(config["DISTANCES_AND_MYTO"][s_city].keys())
                        if dests:
                            d_city = st.selectbox("Select Destination", dests)
                        else:
                            st.error("No destinations found for this start point.")
                            d_city = None
                    
                    if d_city:
                        curr = config["DISTANCES_AND_MYTO"][s_city][d_city]
                        v_pl, v_eu = curr["distPL"], curr["distEU"]
                        v_mftl, v_msolo, v_mbus = curr.get("mytoFTL", 0), curr.get("mytoSolo", 0), curr.get("mytoBus", 0)

                # Formularz edycji danych technicznych trasy
                if s_city and d_city and s_city != "+ ADD NEW POINT":
                    st.markdown(f"#### Technical Specs: {s_city} ➔ {d_city}")
                    f1, f2 = st.columns(2)
                    with f1:
                        new_pl = st.number_input("Distance PL (KM)", value=v_pl)
                        new_eu = st.number_input("Distance EU (KM)", value=v_eu)
                    with f2:
                        new_mftl = st.number_input("Myto FTL (PLN)", value=v_mftl)
                        new_msolo = st.number_input("Myto Solo (PLN)", value=v_msolo)
                        new_mbus = st.number_input("Myto Bus (PLN)", value=v_mbus)

                    # Przyciski Zapisu/Usuwania
                    b1, b2 = st.columns([1, 1])
                    with b1:
                        if st.button("SAVE CHANGES TO CLOUD"):
                            if s_city not in config["DISTANCES_AND_MYTO"]:
                                config["DISTANCES_AND_MYTO"][s_city] = {}
                            
                            config["DISTANCES_AND_MYTO"][s_city][d_city] = {
                                "distPL": new_pl,
                                "distEU": new_eu,
                                "mytoFTL": new_mftl,
                                "mytoSolo": new_msolo,
                                "mytoBus": new_mbus
                            }
                            # Aktualizacja cen globalnych
                            config["EURO_RATE"] = new_euro
                            config["PRICE"]["fuelPLN"] = new_f_pl
                            config["PRICE"]["fuelEUR"] = new_f_eu
                            
                            if update_github_data(config, file_sha):
                                st.success("Vorteza Cloud Synchronized.")
                                st.rerun()
                    
                    with b2:
                        if action == "Edit / Delete Existing Route" and st.button("DELETE THIS ROUTE PERMANENTLY"):
                            del config["DISTANCES_AND_MYTO"][s_city][d_city]
                            if not config["DISTANCES_AND_MYTO"][s_city]:
                                del config["DISTANCES_AND_MYTO"][s_city]
                            
                            if update_github_data(config, file_sha):
                                st.warning("Entry removed from database.")
                                st.rerun()

            elif pwd != "":
                st.error("Authentication Failed. Access Denied.")
    else:
        st.error("CRITICAL ERROR: FAILED TO LOAD CONFIG.JSON FROM GITHUB.")
