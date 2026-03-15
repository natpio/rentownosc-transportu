import streamlit as st
import json
import base64
import requests
import pandas as pd

# =========================================================
# TUTAJ WPISZ SWOJE DANE (Pomiędzy cudzysłowy "")
# =========================================================
GITHUB_TOKEN = "TUTAJ_WKLEJ_TWÓJ_TOKEN_Z_NOTATNIKA"
REPO_OWNER = "TWOJA_NAZWA_UZYTKOWNIKA_GITHUB"
REPO_NAME = "kalkulator-sqm"
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
    payload = {"message": "Aktualizacja z aplikacji Streamlit", "content": encoded, "sha": sha}
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code == 200

if 'config' not in st.session_state:
    data, sha = get_github_data()
    st.session_state.config = data
    st.session_state.sha = sha

st.set_page_config(page_title="SQM Logistics", layout="wide")
st.title("🚚 Kalkulator Transportowy SQM")

tab1, tab2 = st.tabs(["🧮 Kalkulator", "🔐 Panel Admina"])

with tab1:
    if st.session_state.config:
        conf = st.session_state.config
        col_inp, col_res = st.columns([1, 1])
        
        with col_inp:
            st.subheader("Parametry")
            pojazd = st.selectbox("Pojazd", list(conf['VEHICLE_DATA'].keys()))
            trasa = st.selectbox("Trasa", list(conf['DISTANCES_AND_MYTO'].keys()))
            euro = st.number_input("Kurs EUR", value=float(conf['EURO_RATE']), step=0.01)
            m_pln = st.number_input("Dodatki PLN", value=0.0)
            m_eur = st.number_input("Dodatki EUR", value=0.0)

        with col_res:
            st.subheader("Wyniki")
            v = conf['VEHICLE_DATA'][pojazd]
            t = conf['DISTANCES_AND_MYTO'][trasa]
            p = conf['PRICE']
            
            d_total = t['distPL'] + t['distEU']
            f_total = d_total * v['fuelUsage']
            f_pl = min(f_total, v['tankCapacity'])
            f_eu = max(0, f_total - f_pl)
            
            c_fuel = (f_pl * p['fuelPLN']) + (f_eu * p['fuelEUR'] * euro)
            ab_total = d_total * v['adBlueUsage']
            ratio = f_pl / f_total if f_total > 0 else 0
            c_ab = (ab_total * ratio * p['adBluePLN']) + (ab_total * (1-ratio) * p['adBlueEUR'] * euro)
            c_srv = (t['distPL'] * v['serviceCostPLN']) + (t['distEU'] * v['serviceCostEUR'] * euro)
            myto = t[f'myto{pojazd}'] if t['distEU'] == 0 else 0
            
            suma = c_fuel + c_ab + c_srv + myto + m_pln + (m_eur * euro)
            
            st.metric("KOSZT CAŁKOWITY", f"{suma:.2f} PLN")
            st.write(f"Dystans: {d_total} km")
    else:
        st.error("Błąd połączenia z GitHub. Sprawdź token!")

with tab2:
    st.subheader("Ustawienia (Tylko dla Ciebie)")
    pin = st.text_input("Hasło", type="password")
    if pin == "SQM2026":
        if st.session_state.config:
            st.write("### Ceny paliw")
            conf['PRICE']['fuelPLN'] = st.number_input("Paliwo PL", value=float(conf['PRICE']['fuelPLN']))
            conf['PRICE']['fuelEUR'] = st.number_input("Paliwo EU", value=float(conf['PRICE']['fuelEUR']))
            
            st.write("### Baza Tras")
            df = pd.DataFrame(conf['DISTANCES_AND_MYTO']).T
            edited_df = st.data_editor(df, num_rows="dynamic")
            
            if st.button("ZAPISZ ZMIANY W CHMURZE"):
                conf['DISTANCES_AND_MYTO'] = edited_df.to_dict('index')
                if save_to_github(conf, st.session_state.sha):
                    st.success("Zapisano! Odśwież stronę.")
                    st.session_state.config, st.session_state.sha = get_github_data()
                else:
                    st.error("Błąd zapisu.")
