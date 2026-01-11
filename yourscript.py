import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
import plotly.express as px

# --- 1. VERİ SİSTEMİ ---
USER_DB, PORT_DB = "users_final.csv", "portfolio_final.csv"

def init_db():
    if not os.path.exists(USER_DB):
        admin_pw = hashlib.sha256(str.encode("admin123")).hexdigest()
        df = pd.DataFrame([["admin", admin_pw, "AKOSELL", "Approved", "Admin"]], 
                          columns=["Username", "Password", "Name", "Status", "Role"])
        df.to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "Kat", "Adet", "Maliyet"]).to_csv(PORT_DB, index=False)

init_db()

@st.cache_data(ttl=300)
def get_price(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d")
        return round(data['Close'].iloc[-1], 2) if not data.empty else 0
    except: return 0

# --- UI AYARLARI ---
st.set_page_config(page_title="AKOSELL WMS", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #F8FAFC !important; border-right: 1px solid #E2E8F0; }
    .user-initial { width: 50px; height: 50px; background: #2563EB; color: white; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 20px; font-weight: 700; margin: 0 auto 10px auto; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # --- GİRİŞ EKRANI (Aynı Mantık) ---
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>AKOSELL</h1>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Giriş", use_container_width=True):
            users = pd.read_csv(USER_DB)
            hp = hashlib.sha256(str.encode(p)).hexdigest()
            user = users[(users['Username']==u) & (users['Password']==hp)]
            if not user.empty and user.iloc[0]['Status'] == "Approved":
                st.session_state.logged_in = True
                st.session_state.u_data = user.iloc[0].to_dict()
                st.rerun()
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f'<div class="user-initial">{st.session_state.u_data["Name"][0].upper()}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="text-align:center; font-weight:700;">{st.session_state.u_data["Name"].upper()}</div>', unsafe_allow_html=True)
        menu = st.radio("NAV", ["📊 DASHBOARD", "💼 PORTFÖYÜM", "📈 ANALİZLER", "⚙️ AYARLAR", "🔐 YÖNETİCİ PANELİ"])

    p_df = pd.read_csv(PORT_DB)
    
    # --- PORTFÖYÜM MODÜLÜ (DÜZENLE/SİL/EKLE) ---
    if menu == "💼 PORTFÖYÜM":
        st.title("💼 Varlık Yönetimi")
        
        # 1. YENİ VARLIK EKLE
        with st.expander("➕ Yeni Varlık Ekle", expanded=False):
            with st.form("ekle_form"):
                c1, c2, c3, c4 = st.columns(4)
                k = c1.text_input("Kod (Örn: THYAO, BTC)")
                kt = c2.selectbox("Kategori", ["Hisse", "Kripto"])
                a = c3.number_input("Adet", min_value=0.01, step=0.01)
                m = c4.number_input("Birim Maliyet", min_value=0.01)
                if st.form_submit_button("Portföye Ekle"):
                    new_data = pd.DataFrame([[st.session_state.u_data['Username'], k.upper(), kt, a, m]], columns=p_df.columns)
                    pd.concat([p_df, new_data]).to_csv(PORT_DB, index=False)
                    st.success(f"{k.upper()} eklendi.")
                    st.rerun()

        st.divider()

        # 2. VARLIKLARI LİSTELE VE YÖNET
        my_p = p_df[p_df['Owner'] == st.session_state.u_data['Username']]
        
        if not my_p.empty:
            st.subheader("Mevcut Varlıklarınız")
            # Her satır için Düzenle/Sil butonları
            for index, row in my_p.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                    col1.write(f"**{row['Kod']}** ({row['Kat']})")
                    new_adet = col2.number_input("Adet", value=float(row['Adet']), key=f"a_{index}")
                    new_maliyet = col3.number_input("Maliyet", value=float(row['Maliyet']), key=f"m_{index}")
                    
                    if col4.button("Güncelle", key=f"up_{index}"):
                        p_df.loc[index, 'Adet'] = new_adet
                        p_df.loc[index, 'Maliyet'] = new_maliyet
                        p_df.to_csv(PORT_DB, index=False)
                        st.toast(f"{row['Kod']} güncellendi!")
                        st.rerun()
                        
                    if col5.button("🗑️", key=f"del_{index}"):
                        p_df = p_df.drop(index)
                        p_df.to_csv(PORT_DB, index=False)
                        st.error(f"{row['Kod']} silindi.")
                        st.rerun()
                st.markdown("---")
        else:
            st.info("Henüz varlık eklenmemiş.")

    # --- DİĞER SAYFALAR (Dashboard, Analiz vb. önceki kodla aynı kalacak) ---
    elif menu == "📊 DASHBOARD":
        st.write("Dashboard içeriği buraya gelecek (Önceki kodunuzdaki mantıkla).")