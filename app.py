import streamlit as st
import json
import base64
import requests
import pandas as pd

# =========================================================
# KONFIGURACJA GITHUB - DANE ZAKTUALIZOWANE
# =========================================================
GITHUB_TOKEN = "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"
REPO_OWNER = "natpio"
REPO_NAME = "rentownosc-transportu"
FILE_PATH = "config.json"
# =========================================================

def get_github_data():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = r.json()
        decoded = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(decoded), content['sha']
    return None, None

def save_to_github(new_data, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    encoded = base64.b64encode(json.dumps(new_data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    payload = {"message": "Aktualizacja danych z aplikacji Streamlit", "content": encoded, "sha": sha}
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code == 200

# Zarządzanie danymi w sesji Streamlit
if 'config' not in st.session_state:
    data, sha = get_github_data()
    if data:
        st.session_state.config = data
        st.session_state.sha = sha
    else:
        st.session_state.config = None

st.set_page_config(page_title="SQM Logistics | Rentowność", layout="wide")
st.title("🚚 Kalkulator Transportowy SQM")

tab1, tab2 = st.tabs(["🧮 Kalkulator", "🔐 Panel Admina"])

with tab1:
    if st.session_state.config:
        conf = st.session_state.config
        col_inp, col_res = st.columns([1, 1])
        
        with col_inp:
            st.subheader("Parametry Kursu")
            pojazd = st.selectbox("Wybierz pojazd", list(conf['VEHICLE_DATA'].keys()))
            trasa = st.selectbox("Wybierz cel/trasę", list(conf['DISTANCES_AND_MYTO'].keys()))
            euro = st.number_input("Kurs EUR (aktualny)", value=float(conf['EURO_RATE']), step=0.01)
            m_pln = st.number_input("Dodatki PLN (np. promy)", value=0.0)
            m_eur = st.number_input("Dodatki EUR (np. myto EU)", value=0.0)

        with col_res:
            st.subheader("Wynik Kalkulacji")
            v = conf['VEHICLE_DATA'][pojazd]
            t = conf['DISTANCES_AND_MYTO'][trasa]
            p = conf['PRICE']
            
            d_total = t['distPL'] + t['distEU']
            f_total = d_total * v['fuelUsage']
            f_pl = min(f_total, v['tankCapacity'])
            f_eu = max(0, f_total - f_pl)
            
            # Obliczenia kosztów
            c_fuel = (f_pl * p['fuelPLN']) + (f_eu * p['fuelEUR'] * euro)
            ab_total = d_total * v['adBlueUsage']
            ratio = f_pl / f_total if f_total > 0 else 0
            c_ab = (ab_total * ratio * p['adBluePLN']) + (ab_total * (1-ratio) * p['adBlueEUR'] * euro)
            c_srv = (t['distPL'] * v['serviceCostPLN']) + (t['distEU'] * v['serviceCostEUR'] * euro)
            
            # Pobranie myta stałego dla wybranego pojazdu
            myto_key = f"myto{pojazd}"
            myto = t.get(myto_key, 0) if t['distEU'] == 0 else 0
            
            suma = c_fuel + c_ab + c_srv + myto + m_pln + (m_eur * euro)
            
            st.markdown(f"### Koszt własny: **{suma:.2f} PLN**")
            st.write(f"Dystans: {d_total} km ({t['distPL']} PL / {t['distEU']} EU)")
            st.info("Pamiętaj, że wynik to szacunkowy koszt własny (bez marży).")
    else:
        st.error("Błąd: Nie znaleziono pliku config.json lub Token jest nieprawidłowy. Sprawdź nazwę repozytorium!")

with tab2:
    st.subheader("Panel Administracyjny")
    pin = st.text_input("Hasło", type="password")
    if pin == "SQM2026":
        if st.session_state.config:
            st.write("### ⛽ Ceny paliw i mediów")
            c1, c2 = st.columns(2)
            with c1:
                conf['PRICE']['fuelPLN'] = st.number_input("Paliwo PL (PLN)", value=float(conf['PRICE']['fuelPLN']))
                conf['PRICE']['adBluePLN'] = st.number_input("AdBlue PL (PLN)", value=float(conf['PRICE']['adBluePLN']))
            with c2:
                conf['PRICE']['fuelEUR'] = st.number_input("Paliwo EU (EUR)", value=float(conf['PRICE']['fuelEUR']))
                conf['PRICE']['adBlueEUR'] = st.number_input("AdBlue EU (EUR)", value=float(conf['PRICE']['adBlueEUR']))
            
            st.write("### 🛣️ Zarządzanie Trasami")
            df = pd.DataFrame(conf['DISTANCES_AND_MYTO']).T
            edited_df = st.data_editor(df, num_rows="dynamic")
            
            if st.button("💾 ZAPISZ ZMIANY W REPOZYTORIUM"):
                conf['DISTANCES_AND_MYTO'] = edited_df.to_dict('index')
                if save_to_github(conf, st.session_state.sha):
                    st.success("SUKCES! Dane zostały nadpisane na GitHubie.")
                    # Odświeżamy dane w aplikacji
                    st.session_state.config, st.session_state.sha = get_github_data()
                else:
                    st.error("Błąd zapisu. Sprawdź, czy Twój Token ma uprawnienia 'Write'.")
