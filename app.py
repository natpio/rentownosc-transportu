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
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

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
# STYLIZACJA VORTEZA SYSTEMS (PREMIUM COPPER & DARK)
# =========================================================
def apply_vorteza_theme():
    bin_str = get_base64_of_bin_file('bg_vorteza.png')
    if bin_str:
        bg_style = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(bg_style, unsafe_allow_html=True)
    else:
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

            h1, h2, h3, .stSubheader {
                color: var(--v-copper) !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                letter-spacing: 1px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }

            /* ETYKIETY INPUTÓW */
            label[data-testid="stWidgetLabel"] {
                color: var(--v-copper) !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                font-size: 0.85rem !important;
                letter-spacing: 1px;
            }

            /* POLA SELECT I INPUT */
            div[data-baseweb="select"] > div, input {
                background-color: rgba(15, 15, 15, 0.9) !important;
                color: white !important;
                border: 1px solid #444 !important;
            }
            
            /* KARTA ANALIZY */
            div[data-testid="stVerticalBlock"] > div:has(div.vorteza-card) {
                background-color: var(--v-panel);
                padding: 30px;
                border-radius: 5px;
                border-left: 5px solid var(--v-copper);
                box-shadow: 0 10px 40px rgba(0,0,0,0.8);
                backdrop-filter: blur(15px);
            }

            [data-testid="stMetricValue"] {
                color: var(--v-copper) !important;
                font-size: 2.2rem !important;
                font-weight: 700 !important;
            }

            /* PRZYCISKI */
            .stButton > button {
                background-color: rgba(0, 0, 0, 0.7);
                color: var(--v-copper);
                border: 1px solid var(--v-copper);
                border-radius: 0px;
                padding: 12px;
                width: 100%;
                font-weight: 700;
                text-transform: uppercase;
                transition: 0.3s;
            }
            .stButton > button:hover {
                background-color: var(--v-copper);
                color: black;
            }

            /* TABELA KOSZTÓW */
            .cost-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            .cost-table th {
                text-align: left;
                color: var(--v-copper);
                border-bottom: 1px solid #444;
                padding: 8px;
                font-size: 0.8rem;
                text-transform: uppercase;
            }
            .cost-table td {
                padding: 10px 8px;
                border-bottom: 1px solid #222;
                font-size: 0.9rem;
            }
        </style>
    """, unsafe_allow_html=True)

# =========================================================
# LOGIKA APLIKACJI
# =========================================================
st.set_page_config(page_title="VORTEZA SYSTEMS | LOGISTICS", layout="wide")
apply_vorteza_theme()

if GITHUB_TOKEN == "BRAK":
    st.error("GITHUB TOKEN NOT FOUND.")
else:
    config, file_sha = get_github_data()

    if config:
        tab1, tab2 = st.tabs(["📊 VORTEZA MARGIN", "⚙️ SYSTEM CORE"])

        # --- TAB 1: KALKULATOR ---
        with tab1:
            col_cfg, col_res = st.columns([1, 1], gap="large")
            
            with col_cfg:
                st.subheader("Transport Configuration")
                v_type = st.selectbox("Select Vehicle Unit", list(config["VEHICLE_DATA"].keys()))
                
                start_points = list(config["DISTANCES_AND_MYTO"].keys())
                start_p = st.selectbox("Starting Point", start_points)
                
                available_dests = list(config["DISTANCES_AND_MYTO"][start_p].keys())
                if not available_dests:
                    st.warning(f"No destinations defined for {start_p}")
                    route = None
                else:
                    route = st.selectbox("Target Destination", available_dests)
                
                extra_km = st.number_input("Additional Distance (Total KM)", value=0, step=10)
                
                if route:
                    v_info = config["VEHICLE_DATA"][v_type]
                    r_info = config["DISTANCES_AND_MYTO"][start_p][route]
                    prices = config["PRICE"]
                    euro_rate = config["EURO_RATE"]

                    dist_pl = r_info["distPL"]
                    dist_eu = r_info["distEU"] + extra_km
                    total_km = dist_pl + dist_eu

            with col_res:
                if route:
                    st.markdown('<div class="vorteza-card">', unsafe_allow_html=True)
                    st.subheader("Technical Margin Analysis")
                    
                    # Obliczenia paliwa (PL vs EU)
                    total_fuel_liters = total_km * v_info["fuelUsage"]
                    pl_liters = min(total_fuel_liters, v_info["tankCapacity"])
                    eu_liters = max(0, total_fuel_liters - pl_liters)
                    
                    # Składowe PLN
                    cost_fuel_pln = (pl_liters * prices["fuelPLN"]) + (eu_liters * prices["fuelEUR"] * euro_rate)
                    cost_adblue_pln = (total_km * v_info["adBlueUsage"]) * prices["adBluePLN"]
                    cost_service_pln = (dist_pl * v_info["serviceCostPLN"]) + (dist_eu * v_info["serviceCostEUR"] * euro_rate)
                    
                    myto_key = f"myto{v_type}"
                    cost_myto_pln = r_info.get(myto_key, 0)
                    
                    total_pln = cost_fuel_pln + cost_adblue_pln + cost_service_pln + cost_myto_pln
                    total_eur = total_pln / euro_rate

                    # Główne metryki
                    m1, m2 = st.columns(2)
                    m1.metric("TOTAL COST (PLN)", f"{round(total_pln, 2)} zł")
                    m2.metric("TOTAL COST (EUR)", f"€ {round(total_eur, 2)}")

                    # Tabela szczegółowa PLN / EUR
                    st.markdown(f"""
                        <table class="cost-table">
                            <tr>
                                <th>Cost Category</th>
                                <th>PLN Value</th>
                                <th>EUR Value</th>
                            </tr>
                            <tr>
                                <td>Fuel & Energy</td>
                                <td>{round(cost_fuel_pln, 2)} zł</td>
                                <td>€ {round(cost_fuel_pln / euro_rate, 2)}</td>
                            </tr>
                            <tr>
                                <td>AdBlue Consumption</td>
                                <td>{round(cost_adblue_pln, 2)} zł</td>
                                <td>€ {round(cost_adblue_pln / euro_rate, 2)}</td>
                            </tr>
                            <tr>
                                <td>Technical Service</td>
                                <td>{round(cost_service_pln, 2)} zł</td>
                                <td>€ {round(cost_service_pln / euro_rate, 2)}</td>
                            </tr>
                            <tr>
                                <td>Road Tolls (Myto)</td>
                                <td>{round(cost_myto_pln, 2)} zł</td>
                                <td>€ {round(cost_myto_pln / euro_rate, 2)}</td>
                            </tr>
                        </table>
                        <div style="margin-top:15px; font-size:0.75rem; color:#666;">
                            Exchange rate: 1 EUR = {euro_rate} PLN | Unit: {v_type} | Route: {start_p}-{route}
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 2: SYSTEM CORE ---
        with tab2:
            st.subheader("Vorteza Master Access")
            pwd = st.text_input("Vorteza Master Key", type="password")
            
            if pwd == ADMIN_PASSWORD:
                st.success("Access Granted.")
                
                # 1. Czynniki Ekonomiczne
                st.markdown("### 1. Global Economic Factors")
                e1, e2, e3 = st.columns(3)
                with e1: new_euro = st.number_input("EURO Rate", value=config["EURO_RATE"], format="%.4f")
                with e2: new_f_pl = st.number_input("Fuel PLN/L", value=config["PRICE"]["fuelPLN"])
                with e3: new_f_eu = st.number_input("Fuel EUR/L", value=config["PRICE"]["fuelEUR"])
                
                st.write("---")

                # 2. Zarządzanie Trasami
                st.markdown("### 2. Route Management")
                adm_mode = st.radio("Mode:", ["Add New Route", "Edit / Delete Existing"], horizontal=True)

                if adm_mode == "Add New Route":
                    as1, as2 = st.columns(2)
                    with as1:
                        starts = list(config["DISTANCES_AND_MYTO"].keys())
                        s_city = st.selectbox("Start Point", ["+ NEW"] + starts)
                        if s_city == "+ NEW": s_city = st.text_input("New Start Point Name")
                    with as2:
                        d_city = st.text_input("New Destination Name")
                    v_pl, v_eu, v_mftl, v_msolo, v_mbus = 0, 0, 0, 0, 0
                else:
                    as1, as2 = st.columns(2)
                    with as1: s_city = st.selectbox("Select Start Point", list(config["DISTANCES_AND_MYTO"].keys()))
                    with as2: 
                        d_list = list(config["DISTANCES_AND_MYTO"][s_city].keys())
                        d_city = st.selectbox("Select Destination", d_list) if d_list else None
                    
                    if d_city:
                        curr = config["DISTANCES_AND_MYTO"][s_city][d_city]
                        v_pl, v_eu = curr["distPL"], curr["distEU"]
                        v_mftl, v_msolo, v_mbus = curr.get("mytoFTL", 0), curr.get("mytoSolo", 0), curr.get("mytoBus", 0)

                if s_city and d_city and s_city != "+ NEW":
                    st.markdown(f"#### Data Editor: {s_city} ➔ {d_city}")
                    ed1, ed2 = st.columns(2)
                    with ed1:
                        n_pl = st.number_input("Distance PL", value=v_pl)
                        n_eu = st.number_input("Distance EU", value=v_eu)
                    with ed2:
                        n_mftl = st.number_input("Myto FTL (PLN)", value=v_mftl)
                        n_msolo = st.number_input("Myto Solo (PLN)", value=v_msolo)
                        n_mbus = st.number_input("Myto Bus (PLN)", value=v_mbus)

                    if st.button("SYNC DATABASE WITH CLOUD"):
                        if s_city not in config["DISTANCES_AND_MYTO"]: config["DISTANCES_AND_MYTO"][s_city] = {}
                        config["DISTANCES_AND_MYTO"][s_city][d_city] = {
                            "distPL": n_pl, "distEU": n_eu, "mytoFTL": n_mftl, "mytoSolo": n_msolo, "mytoBus": n_mbus
                        }
                        config["EURO_RATE"] = new_euro
                        config["PRICE"]["fuelPLN"] = new_f_pl
                        config["PRICE"]["fuelEUR"] = new_f_eu
                        
                        if update_github_data(config, file_sha):
                            st.success("Successfully updated.")
                            st.rerun()

                    if adm_mode == "Edit / Delete Existing" and st.button("DELETE THIS ROUTE"):
                        del config["DISTANCES_AND_MYTO"][s_city][d_city]
                        if not config["DISTANCES_AND_MYTO"][s_city]: del config["DISTANCES_AND_MYTO"][s_city]
                        update_github_data(config, file_sha)
                        st.rerun()

            elif pwd != "":
                st.error("Invalid Master Key.")
    else:
        st.error("FAILED TO LOAD DATA FROM GITHUB.")
