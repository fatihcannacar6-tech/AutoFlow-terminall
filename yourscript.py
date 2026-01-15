import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import hashlib
import os
from datetime import datetime
import plotly.graph_objects as go
from scipy.optimize import minimize

# --- 1. VERİTABANI SİSTEMİ ---
USER_DB, PORT_DB = "users_v17.csv", "portfolio_v17.csv"

def init_db():
    if not os.path.exists(USER_DB):
        hp = hashlib.sha256(str.encode("8826244")).hexdigest()
        users = pd.DataFrame([["fatihcan", hp, "Fatih Can", "Admin", "Active"]], 
                             columns=["Username", "Password", "Name", "Role", "Status"])
        users.to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "Maliyet", "Adet", "Kat"]).to_csv(PORT_DB, index=False)

init_db()

# --- 2. MODERN BEYAZ ARAYÜZ ---
st.set_page_config(page_title="AKOSELL WMS Terminal", layout="wide", page_icon="🏛️")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #F8FAFC; }
    .ai-card { background: white; padding: 25px; border-radius: 15px; border-left: 6px solid #4F46E5; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .stMetric { background: white !important; padding: 20px !important; border-radius: 12px !important; border: 1px solid #F1F5F9 !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ANALİZ FONKSİYONLARI ---
def fetch_prices(df):
    if df.empty: return df
    df = df.copy()
    prices = []
    for _, r in df.iterrows():
        sym = f"{r['Kod']}.IS" if r['Kat'] == "Hisse" else (f"{r['Kod']}-USD" if r['Kat'] == "Kripto" else r['Kod'])
        try:
            data = yf.Ticker(sym).history(period="1d")
            prices.append(data['Close'].iloc[-1] if not data.empty else r['Maliyet'])
        except: prices.append(r['Maliyet'])
    df['Güncel'] = prices
    df['Değer'] = df['Güncel'] * df['Adet']
    df['Kâr/Zarar'] = df['Değer'] - (df['Maliyet'] * df['Adet'])
    return df

# --- 4. GİRİŞ VE KAYIT PANELİ (Hata Giderildi) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    with tab1:
        u = st.text_input("Kullanıcı Adı", key="login_u")
        p = st.text_input("Şifre", type="password", key="login_p")
        if st.button("TERMİNALE GİRİŞ", use_container_width=True, type="primary"):
            users = pd.read_csv(USER_DB)
            hp = hashlib.sha256(str.encode(p)).hexdigest()
            match = users[(users['Username']==u) & (users['Password']==hp)]
            if not match.empty:
                if match.iloc[0]['Status'] == "Active":
                    st.session_state.logged_in = True
                    st.session_state.u_data = match.iloc[0].to_dict()
                    st.rerun()
                else: st.warning("Hesabınız admin onayı bekliyor.")
            else: st.error("Hatalı bilgiler.")
    with tab2:
        new_u = st.text_input("Kullanıcı Adı Belirle", key="reg_u").lower()
        new_n = st.text_input("Ad Soyad", key="reg_n")
        new_p = st.text_input("Yeni Şifre Oluştur", type="password", key="reg_p")
        if st.button("KAYIT TALEBİ GÖNDER", use_container_width=True):
            users = pd.read_csv(USER_DB)
            if new_u in users['Username'].values: st.error("Kullanıcı adı mevcut.")
            else:
                hp = hashlib.sha256(str.encode(new_p)).hexdigest()
                new_user = pd.DataFrame([[new_u, hp, new_n, "User", "Pending"]], columns=users.columns)
                new_user.to_csv(USER_DB, mode='a', header=False, index=False)
                st.success("Talep admin (fatihcan) onayına gönderildi.")

else:
    # --- 5. SIDEBAR ---
    with st.sidebar:
        u_name = st.session_state.u_data.get('Name', 'Kullanıcı')
        u_role = st.session_state.u_data.get('Role', 'User')
        st.markdown(f"### 🏛️ AKOSELL WMS\n**{u_name}**")
        nav = ["📊 DASHBOARD", "⚖️ OPTİMİZASYON", "💼 PORTFÖYÜM", "⚙️ AYARLAR"]
        if u_role == "Admin": nav.append("🔑 ADMIN PANELİ")
        menu = st.radio("MENÜ", nav)
        if st.button("Güvenli Çıkış"):
            st.session_state.logged_in = False
            st.rerun()

    df_port = pd.read_csv(PORT_DB)
    my_port = df_port[df_port['Owner'] == st.session_state.u_data.get('Username')]

    # --- 6. DASHBOARD ---
    if menu == "📊 DASHBOARD":
        st.title("📊 Portföy Detaylı Raporu")
        if not my_port.empty:
            proc_df = fetch_prices(my_port)
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Varlık", f"₺{proc_df['Değer'].sum():,.2f}")
            c2.metric("Toplam Kâr/Zarar", f"₺{proc_df['Kâr/Zarar'].sum():,.2f}")
            c3.metric("Aktif Varlık", f"{len(proc_df)} Kalem")
            st.dataframe(proc_df[["Kod", "Adet", "Maliyet", "Güncel", "Kâr/Zarar"]], use_container_width=True, hide_index=True)
            st.plotly_chart(go.Figure(data=[go.Pie(labels=proc_df['Kod'], values=proc_df['Değer'], hole=.4)]))
        else: st.info("Varlık ekleyin.")

    # --- 7. AI PORTFÖY OPTİMİZASYONU (İSTEDİĞİN GÜNCELLEME) ---
    elif menu == "⚖️ OPTİMİZASYON":
        st.title("⚖️ AI Risk & Optimizasyon Analizi")
        if len(my_port) >= 2:
            assets = my_port['Kod'].unique()
            data = pd.DataFrame()
            analysis_results = []

            with st.spinner("AI Hisse bazlı risk analizi yapıyor..."):
                for a in assets:
                    tk = f"{a}.IS" if my_port[my_port['Kod']==a]['Kat'].values[0]=="Hisse" else f"{a}-USD"
                    hist = yf.Ticker(tk).history(period="1y")['Close']
                    data[a] = hist
                    
                    # Risk ve Sinyal Hesaplama
                    vol = hist.pct_change().std() * np.sqrt(252) * 100
                    ma20 = hist.rolling(20).mean().iloc[-1]
                    last = hist.iloc[-1]
                    
                    risk_cat = "Düşük" if vol < 25 else ("Orta" if vol < 45 else "Yüksek")
                    signal = "🟢 AL / TUT" if last > ma20 else "🔴 SAT / İZLE"
                    
                    analysis_results.append({"Varlık": a, "Yıllık Risk (%)": f"{vol:.2f}", "Risk Seviyesi": risk_cat, "AI Sinyali": signal})

            # Hisse Hisse Detaylı Rapor
            st.subheader("📋 Hisse Bazlı AI Sinyalleri")
            st.table(pd.DataFrame(analysis_results))

            # Sepet Optimizasyonu
            st.divider()
            st.subheader("🎯 İdeal Portföy Dağılımı (Modern Portföy Teorisi)")
            returns = data.pct_change().dropna()
            def get_vol(w): return np.sqrt(np.dot(w.T, np.dot(returns.cov() * 252, w)))
            res = minimize(get_vol, [1./len(assets)]*len(assets), bounds=[(0,1)]*len(assets), constraints={'type':'eq','fun': lambda x: np.sum(x)-1})
            
            st.plotly_chart(go.Figure(data=[go.Pie(labels=assets, values=res.x, hole=.3)]))
            st.success("AI Önerisi: Yukarıdaki dağılım riskinizi minimize eder.")
        else: st.warning("Analiz için en az 2 farklı varlık ekleyin.")

    # --- 8. ADMIN PANELİ ---
    elif menu == "🔑 ADMIN PANELİ":
        st.title("🔑 Admin Onay Sistemi")
        u_df = pd.read_csv(USER_DB)
        pending = u_df[u_df['Status'] == "Pending"]
        if not pending.empty:
            for i, row in pending.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f"**{row['Name']}** (@{row['Username']})")
                if col2.button("✅ ONAYLA", key=f"ok_{row['Username']}"):
                    u_df.loc[u_df['Username'] == row['Username'], 'Status'] = "Active"
                    u_df.to_csv(USER_DB, index=False); st.rerun()
                if col3.button("❌ REDDET", key=f"no_{row['Username']}"):
                    u_df = u_df[u_df['Username'] != row['Username']]
                    u_df.to_csv(USER_DB, index=False); st.rerun()
        else: st.info("Bekleyen onay yok.")

    # --- 9. PORTFÖYÜM ---
    elif menu == "💼 PORTFÖYÜM":
        st.title("💼 Varlık Yönetimi")
        with st.form("add_asset"):
            c1, c2, c3, c4 = st.columns(4)
            k = c1.text_input("Sembol (Örn: THYAO)").upper()
            a = c2.number_input("Adet", min_value=0.0)
            m = c3.number_input("Maliyet", min_value=0.0)
            cat = c4.selectbox("Tür", ["Hisse", "Kripto", "Altın"])
            if st.form_submit_button("Sisteme Kaydet"):
                new = pd.DataFrame([[st.session_state.u_data.get('Username'), k, m, a, cat]], columns=df_port.columns)
                pd.concat([pd.read_csv(PORT_DB), new]).to_csv(PORT_DB, index=False)
                st.rerun()
        st.divider()
        st.subheader("Mevcut Varlıklar")
        st.dataframe(my_port, use_container_width=True)

    # --- 10. AYARLAR ---
    elif menu == "⚙️ AYARLAR":
        st.title("⚙️ Hesap Ayarları")
        st.write(f"Kullanıcı: **{u_name}** | Yetki: **{u_role}**")
        with st.expander("Şifre Değiştir"):
            new_p = st.text_input("Yeni Şifre", type="password")
            if st.button("Güncelle"):
                u_df = pd.read_csv(USER_DB)
                u_df.loc[u_df['Username'] == st.session_state.u_data.get('Username'), 'Password'] = hashlib.sha256(str.encode(new_p)).hexdigest()
                u_df.to_csv(USER_DB, index=False); st.success("Şifre güncellendi.")