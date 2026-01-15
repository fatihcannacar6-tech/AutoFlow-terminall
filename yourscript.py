import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. AYARLAR VE BEYAZ ARAYÜZ TASARIMI ---
st.set_page_config(page_title="Autoflow | White Edition", layout="wide", page_icon="🌊")

st.markdown("""
    <style>
    /* GENEL BEYAZ TEMA */
    .stApp { background-color: #FFFFFF !important; color: #1E293B !important; }
    
    /* SIDEBAR (BEYAZ & GRİ SINIR) */
    [data-testid="stSidebar"] { 
        background-color: #F8FAFC !important; 
        border-right: 1px solid #E2E8F0; 
    }

    /* KART TASARIMLARI (MODERN BEYAZ) */
    .metric-card {
        background: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        margin-bottom: 15px;
    }
    
    .ai-gradient-card {
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
    }

    /* INPUT VE BUTONLAR */
    .stButton>button { border-radius: 8px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERİ TABANI ---
U_DB = "autoflow_v9_users.csv"
P_DB = "autoflow_v9_portfolio.csv"

def init_db():
    if not os.path.exists(U_DB):
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Yönetici", "admin@autoflow.ai", "Approved", "Admin"]], 
                     columns=["User", "Pass", "Name", "Email", "Status", "Role"]).to_csv(U_DB, index=False)
    if not os.path.exists(P_DB):
        pd.DataFrame(columns=["Owner", "Symbol", "Type", "Cost", "Qty", "Date"]).to_csv(P_DB, index=False)

init_db()

# --- 3. KİMLİK DOĞRULAMA ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center; color:#4F46E5;'>🌊 AUTOFLOW</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["GİRİŞ", "KAYIT"])
        with tab_log:
            u = st.text_input("Kullanıcı Adı", key="log_u")
            p = st.text_input("Şifre", type="password", key="log_p")
            if st.button("Sisteme Eriş", use_container_width=True):
                df = pd.read_csv(U_DB)
                hp = hashlib.sha256(p.encode()).hexdigest()
                user = df[(df['User'] == u) & (df['Pass'] == hp)]
                if not user.empty and user.iloc[0]['Status'] == "Approved":
                    st.session_state.logged_in = True
                    st.session_state.user = user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Bilgiler hatalı veya hesap onaylanmamış.")
else:
    # --- 4. ANA PANEL ---
    with st.sidebar:
        st.title("Autoflow V9")
        st.write(f"Hoş geldin, **{st.session_state.user['Name']}**")
        menu = st.radio("Menü", ["PİYASA TAKİBİ", "DASHBOARD", "PORTFÖY", "AI ASİSTAN", "ADMİN", "AYARLAR"])
        if st.button("Oturumu Kapat"):
            st.session_state.logged_in = False
            st.rerun()

    # --- PİYASA TAKİBİ ---
    if menu == "PİYASA TAKİBİ":
        st.title("🌍 Canlı Piyasa Takibi")
        indices = ["BTC-USD", "ETH-USD", "GC=F", "USDTRY=X", "THYAO.IS", "EREGL.IS"]
        cols = st.columns(3)
        for i, sym in enumerate(indices):
            t = yf.Ticker(sym)
            info = t.fast_info
            cols[i % 3].metric(sym, f"{info.last_price:,.2f}", f"{((info.last_price - info.previous_close)/info.previous_close)*100:.2f}%")
        
        target = st.text_input("Grafik İçin Sembol Girin (Örn: AAPL)", "BTC-USD").upper()
        hist = yf.Ticker(target).history(period="1mo")
        st.line_chart(hist['Close'])

    # --- AI ASİSTAN ---
    elif menu == "AI ASİSTAN":
        st.title("🧠 Autoflow Intelligence")
        st.markdown("""
        <div class="ai-gradient-card">
            <h3>🤖 AI Portföy Analisti</h3>
            <p>Piyasaları 7/24 izliyor ve sizin için strateji geliştiriyorum.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("---")
        st.info("AI Tavsiyesi: Portföyünüzdeki teknoloji ağırlığı yüksek. Enerji sektörüne yönelmek riski dağıtabilir.")

    # --- AYARLAR (KULLANICI ADI & ŞİFRE DEĞİŞTİRME) ---
    elif menu == "AYARLAR":
        st.title("⚙️ Hesap Ayarları")
        u_df = pd.read_csv(U_DB)
        idx = u_df[u_df['User'] == st.session_state.user['User']].index[0]

        with st.form("settings_form"):
            st.subheader("Profil Güncelle")
            new_name = st.text_input("Ad Soyad", value=st.session_state.user['Name'])
            new_pass = st.text_input("Yeni Şifre (Boş bırakılırsa değişmez)", type="password")
            
            if st.form_submit_button("Güncelle"):
                u_df.at[idx, 'Name'] = new_name
                if new_pass:
                    u_df.at[idx, 'Pass'] = hashlib.sha256(new_pass.encode()).hexdigest()
                u_df.to_csv(U_DB, index=False)
                st.session_state.user['Name'] = new_name
                st.success("Bilgiler güncellendi!")

    # --- ADMİN (ONAY/RET/SİL) ---
    elif menu == "ADMİN":
        if st.session_state.user['Role'] == "Admin":
            st.title("🔐 Yönetici Paneli")
            u_df = pd.read_csv(U_DB)
            
            st.subheader("Bekleyen Talepler")
            pending = u_df[u_df['Status'] == "Pending"]
            for i, r in pending.iterrows():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{r['Name']}** (@{r['User']})")
                if c2.button("ONAY", key=f"a_{i}"):
                    u_df.at[i, 'Status'] = "Approved"
                    u_df.to_csv(U_DB, index=False)
                    st.rerun()
                if c3.button("RET/SİL", key=f"d_{i}"):
                    u_df = u_df.drop(i)
                    u_df.to_csv(U_DB, index=False)
                    st.rerun()
            
            st.subheader("Kullanıcı Listesi")
            st.dataframe(u_df)
        else:
            st.error("Yetkiniz yok.")

    # --- DASHBOARD & PORTFÖY (ÖNCEKİ STABİL KODLARIN ENTEGRASYONU) ---
    elif menu == "DASHBOARD":
        st.title("📊 Genel Durum")
        st.write("Portföy özetiniz burada görünecektir.")
    elif menu == "PORTFÖY":
        st.title("💼 Varlıklarım")
        st.write("Varlık ekleme ve düzenleme ekranı.")