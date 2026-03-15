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
ADMIN_PASSWORD = "admin" # Możesz zmienić na swoje

# =========================================================
# FUNKCJE OPERACYJNE
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
    payload = {"message": "Update logistyka", "content": encoded, "sha": sha}
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code in [200, 201]

# =========================================================
# INTERFEJS
# =========================================================

st.set_page_config(page_title="Kalkulator Transportowy", layout="wide")
st.title("🚛 Kalkulator Kosztów Transportu")

if GITHUB_TOKEN == "BRAK":
    st.error("Błąd: Skonfiguruj G_TOKEN w Secrets!")
else:
    config, file_sha = get_github_data()

    if config:
        tabs = st.tabs(["📊 Kalkulator Trasy", "⚙️ Ustawienia Cen"])

        with tabs[0]:
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.subheader("Parametry")
                v_type = st.selectbox("Typ pojazdu", list(config["VEHICLE_DATA"].keys()))
                route = st.selectbox("Kierunek (Trasa)", list(config["DISTANCES_AND_MYTO"].keys()))
                
                # Pobranie danych z config
                v_info = config["VEHICLE_DATA"][v_type]
                r_info = config["DISTANCES_AND_MYTO"][route]
                prices = config["PRICE"]
                euro = config["EURO_RATE"]

                extra_km = st.number_input("Dodatkowe km (łącznie)", value=0)
                # Rozdzielamy dodatkowe km proporcjonalnie lub uznajemy za EU
                dist_pl = r_info["distPL"]
                dist_eu = r_info["distEU"] + extra_km
                total_km = dist_pl + dist_eu

            with c2:
                st.subheader("Wyniki Obliczeń")
                
                # Obliczenia paliwa
                total_fuel = total_km * v_info["fuelUsage"]
                # Zakładamy tankowanie w PL do pełna, reszta w EU (uproszczenie logistyczne)
                fuel_pl_liters = min(total_fuel, v_info["tankCapacity"])
                fuel_eu_liters = max(0, total_fuel - fuel_pl_liters)
                
                cost_fuel = (fuel_pl_liters * prices["fuelPLN"]) + (fuel_eu_liters * prices["fuelEUR"] * euro)
                
                # AdBlue
                cost_adblue = (total_km * v_info["adBlueUsage"]) * prices["adBluePLN"]
                
                # Serwis
                cost_service = (dist_pl * v_info["serviceCostPLN"]) + (dist_eu * v_info["serviceCostEUR"] * euro)
                
                # Myto (pobierane z klucza myto + TypPojazdu)
                myto_key = f"myto{v_type}"
                cost_myto = r_info.get(myto_key, 0)

                total_sum = cost_fuel + cost_adblue + cost_service + cost_myto

                st.metric("Całkowity koszt (PLN)", f"{round(total_sum, 2)} zł")
                
                with st.expander("Szczegóły kosztów"):
                    st.write(f"⛽ Paliwo suma: {round(cost_fuel, 2)} PLN")
                    st.write(f"💧 AdBlue: {round(cost_adblue, 2)} PLN")
                    st.write(f"🛠️ Serwis/Eksploatacja: {round(cost_service, 2)} PLN")
                    st.write(f"🛣️ Myto: {round(cost_myto, 2)} PLN")
                    st.write(f"📏 Dystans: {total_km} km ({dist_pl} PL / {dist_eu} EU)")

        with tabs[1]:
            st.subheader("Aktualizacja stawek bazowych")
            pwd = st.text_input("Hasło", type="password")
            if pwd == ADMIN_PASSWORD:
                new_euro = st.number_input("Kurs EURO", value=config["EURO_RATE"])
                new_f_pl = st.number_input("Paliwo PL (PLN)", value=config["PRICE"]["fuelPLN"])
                new_f_eu = st.number_input("Paliwo EU (EUR)", value=config["PRICE"]["fuelEUR"])
                
                if st.button("Zapisz zmiany"):
                    config["EURO_RATE"] = new_euro
                    config["PRICE"]["fuelPLN"] = new_f_pl
                    config["PRICE"]["fuelEUR"] = new_f_eu
                    if update_github_data(config, file_sha):
                        st.success("Zapisano!")
                        st.rerun()
            elif pwd != "":
                st.error("Błędne hasło")
    else:
        st.error("Nie udało się załadować config.json. Sprawdź plik i Token.")
