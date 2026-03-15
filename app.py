import streamlit as st
import pandas as pd
import json
import requests
import base64

# =========================================================
# KONFIGURACJA GITHUB - ZWERYFIKOWANA
# =========================================================
GITHUB_TOKEN = "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"
REPO_OWNER = "natpio"
REPO_NAME = "rentownosc-transportu"
FILE_PATH = "config.json"
ADMIN_PASSWORD = "Vorteza2026"

# =========================================================
# FUNKCJE DO OBSŁUGI DANYCH
# =========================================================

def get_github_data():
    """Pobiera plik config.json z GitHub."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        decoded_content = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(decoded_content), content['sha']
    else:
        st.error(f"Błąd: Nie znaleziono pliku config.json lub Token jest nieprawidłowy. Status: {response.status_code}")
        return None, None

def update_github_data(new_data, sha):
    """Zapisuje zaktualizowany plik config.json na GitHub."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    updated_content = json.dumps(new_data, indent=4, ensure_ascii=False)
    encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": "Aktualizacja cen i parametrów (Panel Admina)",
        "content": encoded_content,
        "sha": sha
    }
    
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code == 200

# =========================================================
# INTERFEJS UŻYTKOWNIKA - STREAMLIT
# =========================================================

st.set_page_config(page_title="VORTEZA flow", layout="wide")
st.title("🚚 VORTEZA flow")

# Pobieranie danych na start
config, file_sha = get_github_data()

if config:
    tabs = st.tabs(["📊 Kalkulator", "🔐 Panel Admina"])

    # --- TAB 1: KALKULATOR ---
    with tabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Parametry Trasy")
            pojazdy_lista = list(config["pojazdy"].keys())
            wybrany_pojazd = st.selectbox("Wybierz pojazd", pojazdy_lista)
            
            trasy_lista = list(config["trasy"].keys())
            wybrana_trasa = st.selectbox("Wybierz trasę (powrotna)", trasy_lista)
            
            km_dodatkowe = st.number_input("Dodatkowe kilometry (np. objazdy)", min_value=0, value=0)
            
        with col2:
            st.subheader("Koszty i Wynik")
            paliwo_cena = config["ceny_bazowe"]["paliwo_on"]
            auto_data = config["pojazdy"][wybrany_pojazd]
            trasa_km = config["trasy"][wybrana_trasa]
            total_km = trasa_km + km_dodatkowe
            
            # Obliczenia
            koszt_paliwa = (total_km / 100) * auto_data["spalanie"] * paliwo_cena
            koszt_diet = auto_data["dieta_dzienna"] * (total_km / 700) # uproszczenie: 700km dziennie
            koszt_eksploatacji = total_km * auto_data["koszt_km_eksploatacja"]
            
            total_cost = koszt_paliwa + koszt_diet + koszt_eksploatacji
            
            st.info(f"Całkowity dystans: **{total_km} km**")
            st.metric("Szacowany koszt transportu", f"{round(total_cost, 2)} PLN")
            
            with st.expander("Szczegóły kosztów"):
                st.write(f"- Paliwo: {round(koszt_paliwa, 2)} PLN")
                st.write(f"- Diety/Kierowca: {round(koszt_diet, 2)} PLN")
                st.write(f"- Eksploatacja (opony, serwis, AdBlue): {round(koszt_eksploatacji, 2)} PLN")

    # --- TAB 2: PANEL ADMINA ---
    with tabs[1]:
        st.subheader("Ustawienia systemowe")
        pwd = st.text_input("Hasło dostępu", type="password")
        
        if pwd == ADMIN_PASSWORD:
            st.success("Dostęp autoryzowany")
            
            # Edycja cen paliwa
            new_fuel = st.number_input("Cena paliwa ON (PLN)", value=config["ceny_bazowe"]["paliwo_on"], step=0.01)
            
            # Edycja spalania pojazdów
            st.write("---")
            st.write("**Spalanie i koszty pojazdów:**")
            updated_pojazdy = config["pojazdy"].copy()
            for p_name, p_data in updated_pojazdy.items():
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    updated_pojazdy[p_name]["spalanie"] = st.number_input(f"{p_name} - spalanie/100km", value=p_data["spalanie"])
                with col_p2:
                    updated_pojazdy[p_name]["koszt_km_eksploatacja"] = st.number_input(f"{p_name} - koszt eksploatacji/km", value=p_data["koszt_km_eksploatacja"])

            if st.button("✅ ZAPISZ ZMIANY W REPOZYTORIUM"):
                config["ceny_bazowe"]["paliwo_on"] = new_fuel
                config["pojazdy"] = updated_pojazdy
                
                success = update_github_data(config, file_sha)
                if success:
                    st.success("Zmiany zostały zapisane na GitHub! Odśwież stronę za moment.")
                else:
                    st.error("Błąd zapisu. Sprawdź uprawnienia Tokena.")
        elif pwd != "":
            st.error("Błędne hasło")
