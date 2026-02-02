import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. NASTAVENÍ STRÁNKY
st.set_page_config(
    page_title="Investiční Sniper",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS STYLOVÁNÍ
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        border: 1px solid #f0f2f6;
    }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    h1 { color: #1f77b4; text-align: center; margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# 3. NAČTENÍ DAT (S CACHINGEM)
@st.cache_data(ttl=3600)
def nacti_data():
    soubory = [f for f in os.listdir('.') if f.startswith('INVESTICNI_HITPARADA') and f.endswith('.xlsx')]
    if not soubory:
        return None, None
    nejnovejsi = max(soubory, key=os.path.getctime)
    df_nacteno = pd.read_excel(nejnovejsi)
    
    # Doplnění sloupců
    for col in ['JePodil', 'JeDrazba']:
        if col not in df_nacteno.columns: df_nacteno[col] = False
    if 'Lat' not in df_nacteno.columns: df_nacteno['Lat'] = 0
    if 'Lon' not in df_nacteno.columns: df_nacteno['Lon'] = 0
    if 'Popis' not in df_nacteno.columns: df_nacteno['Popis'] = ""
    
    cas = datetime.fromtimestamp(os.path.getctime(nejnovejsi)).strftime('%H:%M %d.%m.')
    return df_nacteno, cas

df, datum_dat = nacti_data()

if df is None:
    st.error("⚠️ Žádná data! Spusť bota (super_bot_final.py).")
    st.stop()

# --- FUNKCE PRO AI ANALÝZU ---
def ziskej_tagy(text):
    tagy = []
    text = str(text).lower()
    
    # Stav
    if "rekonstruk" in text: tagy.append(("🛠️ Po rekonstrukci", "green"))
    elif "původní" in text or "k rekonstrukci" in text: tagy.append(("🏚️ Původní stav", "orange"))
    elif "novostavb" in text or "projekt" in text: tagy.append(("✨ Novostavba", "blue"))
    
    # Materiál
    if "cihla" in text or "cihlov" in text: tagy.append(("🧱 Cihla", "red"))
    if "panel" in text: tagy.append(("🏢 Panel", "grey"))
    
    # Vybavení
    if "balkon" in text or "balkón" in text: tagy.append(("☀️ Balkón", "blue"))
    if "lodži" in text: tagy.append(("☀️ Lodžie", "blue"))
    if "teras" in text: tagy.append(("🍹 Terasa", "blue"))
    if "zahrada" in text or "předzahrád" in text: tagy.append(("🌳 Zahrada", "green"))
    if "sklep" in text: tagy.append(("📦 Sklep", "grey"))
    if "výtah" in text: tagy.append(("🛗 Výtah", "grey"))
    if "parkování" in text or "garáž" in text: tagy.append(("🚗 Parkování", "blue"))
    
    return tagy

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("🔍 Filtry")
    max_polozek = st.slider("⚡ Počet inzerátů", 10, 200, 30)
    st.divider()
    vsechna_mesta = sorted([str(m) for m in df['Lokalita'].unique() if str(m) != 'nan'])
    vybrana_mesta = st.multiselect("📍 Města", vsechna_mesta)
    typ_prodeje = st.radio("🔨 Typ prodeje", ["Bez dražeb", "Jen dražby", "Vše"], index=0)
    min_vynos = st.slider("💰 Min. výnos (%)", 0.0, 15.0, 4.0, step=0.5)
    max_cena = st.slider("💳 Max cena (mil. Kč)", 0.5, 15.0, 8.0, step=0.5) * 1000000
    col_check1, col_check2 = st.columns(2)
    with col_check1: skryt_podily = st.checkbox("🚫 Podíly", value=True)
    with col_check2: jen_s_fotkou = st.checkbox("📷 Fotky", value=True)
    st.markdown("---")
    st.header("🧮 Kalkulačka")
    vlastni_zdroje = st.number_input("💵 Vlastní zdroje", value=1000000, step=100000)
    urok = st.number_input("📉 Úrok (%)", value=5.1, step=0.1)
    doba_let = st.number_input("⏳ Doba (let)", value=30)
    fond_oprav = st.number_input("🛠️ Fond oprav", value=3500, step=500)
    st.markdown("---")
    st.caption(f"📅 Data z: {datum_dat}")

# --- 5. FILTRACE ---
df_filtered = df.copy()
df_filtered = df_filtered[(df_filtered['Výnos %'] >= min_vynos) & (df_filtered['Cena'] <= max_cena)]
if skryt_podily: df_filtered = df_filtered[df_filtered['JePodil'] == False]
if jen_s_fotkou: df_filtered = df_filtered[df_filtered['Obrazek'].notna()]
if vybrana_mesta: df_filtered = df_filtered[df_filtered['Lokalita'].isin(vybrana_mesta)]
if typ_prodeje == "Bez dražeb": df_filtered = df_filtered[df_filtered['JeDrazba'] == False]
elif typ_prodeje == "Jen dražby": df_filtered = df_filtered[df_filtered['JeDrazba'] == True]
df_filtered = df_filtered.sort_values(by='Výnos %', ascending=False)

# --- 6. OBSAH ---
st.title("🏠 Realitní Sniper")
c1, c2, c3 = st.columns(3)
c1.metric("Nalezeno", len(df_filtered))
if not df_filtered.empty:
    c2.metric("Průměrný výnos", f"{df_filtered['Výnos %'].mean():.2f} %")
    c3.metric("Průměrná cena", f"{df_filtered['Cena'].mean()/1000000:.1f} M")
st.divider()

# MAPA
st.subheader("🗺️ Mapa příležitostí")
map_data = df_filtered[df_filtered['Lat'] != 0].copy()
if not map_data.empty:
    map_data['size'] = map_data['Výnos %'] * 15
    st.map(map_data.head(500), latitude='Lat', longitude='Lon', size='size', use_container_width=True)
else: st.info("Žádná GPS data pro mapu.")
st.divider()

# VÝPIS
df_display = df_filtered.head(max_polozek)
if df_display.empty:
    st.warning("😔 Žádné inzeráty.")
else:
    for index, row in df_display.iterrows():
        with st.container():
            col_img, col_info = st.columns([1, 2])
            
            # A) OBRÁZKY
            with col_img:
                raw_imgs = str(row['Obrazek']).strip()
                ma_obrazek = False
                if pd.notna(row['Obrazek']) and "http" in raw_imgs:
                    img_list = [img.strip() for img in raw_imgs.split(';;;') if img.strip().startswith('http')]
                    if img_list:
                        st.image(img_list[0], use_container_width=True)
                        ma_obrazek = True
                        if len(img_list) > 1:
                            with st.expander(f"📸 Galerie ({len(img_list)-1})"):
                                for img_url in img_list[1:]: st.image(img_url, use_container_width=True)
                if not ma_obrazek: st.info("📷 Bez náhledu")

            # B) INFORMACE
            with col_info:
                st.subheader(row['Název'])
                
                # --- NOVINKA: AI TAGY (ŠTÍTKY) ---
                tagy = ziskej_tagy(row['Popis'])
                if tagy:
                    html_tagy = ""
                    for text, color in tagy:
                        # Barvy pro Streamlit badges
                        bg_color = "#e6f9e6" if color == "green" else "#e6f2ff" if color == "blue" else "#ffe6e6" if color == "red" else "#f0f2f6"
                        text_color = "#006600" if color == "green" else "#004085" if color == "blue" else "#850000" if color == "red" else "#333333"
                        html_tagy += f'<span style="background-color:{bg_color};color:{text_color};padding:4px 8px;border-radius:12px;margin-right:5px;font-size:0.85rem;font-weight:bold;">{text}</span>'
                    st.markdown(html_tagy, unsafe_allow_html=True)
                    st.markdown("") # Mezera
                # ---------------------------------

                c_loc, c_source = st.columns([3, 1])
                c_loc.caption(f"📍 {row['Lokalita']}")
                zdroj = row['Zdroj']
                barva_zdroje = "red" if zdroj == 'Sreality' else "green" if zdroj == 'Bezrealitky' else "blue"
                c_source.markdown(f":{barva_zdroje}[{zdroj}]")
                
                if row['JePodil']: st.warning("⚠️ PRODEJ PODÍLU")
                if row['JeDrazba']: st.error("🔨 DRAŽBA / AUKCE")
                st.markdown("---")

                # CASHFLOW
                cena = row['Cena']
                vyse_uveru = max(0, cena - vlastni_zdroje)
                if vyse_uveru > 0:
                    r = urok / 100 / 12
                    n = doba_let * 12
                    splatka = vyse_uveru * (r * (1 + r)**n) / ((1 + r)**n - 1)
                else: splatka = 0
                mesicni_najem_odhad = (row['Výnos %'] * cena / 100) / 12
                cashflow = mesicni_najem_odhad - splatka - fond_oprav
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Cena", f"{cena/1000000:.2f} M")
                m2.metric("Plocha", f"{row['m2']} m²")
                m3.metric("Hrubý výnos", f"{row['Výnos %']} %")
                
                cf_col1, cf_col2 = st.columns(2)
                barva_cf = "green" if cashflow > 0 else "red"
                emoji_cf = "🤑" if cashflow > 0 else "💸"
                with cf_col1: st.markdown(f"""<div style="background-color:#f0f2f6;padding:10px;border-radius:10px;"><small>Odhad nájmu</small><br><b>{int(mesicni_najem_odhad):,} Kč</b></div>""", unsafe_allow_html=True)
                with cf_col2: st.markdown(f"""<div style="background-color:#f0f2f6;padding:10px;border-radius:10px;"><small>Splátka hypo</small><br><b>{int(splatka):,} Kč</b></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div style="margin-top:10px;font-size:18px;">{emoji_cf} Čisté Cashflow: <b style="color:{barva_cf}">{int(cashflow):,} Kč / měsíc</b></div>""", unsafe_allow_html=True)
                st.markdown("")
                st.link_button("👉 Otevřít inzerát", row['URL'], use_container_width=True)