import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import hashlib
import os
import base64
from datetime import datetime, timedelta
try:
    from scipy.optimize import minimize
except ImportError:
    st.error("Kütüphane hatası: 'scipy' bulunamadı. Lütfen 'pip install scipy' komutuyla yükleyin.")
from fpdf import FPDF
import plotly.graph_objects as go

# --- 1. VERİTABANI VE SİSTEM AYARLARI ---
USER_DB, PORT_DB = "users_v12.csv", "portfolio_v12.csv"

def init_db():
    if not os.path.exists(USER_DB):
        pd.DataFrame(columns=["Username", "Password", "Name", "Email"]).to_csv(USER_DB, index=False)
        # Varsayılan Admin (Şifre: 1234)
        hp = hashlib.sha256(str.encode("1234")).hexdigest()
        admin = pd.DataFrame([["admin", hp, "AutoFlow Admin", "admin@autoflow.com"]], columns=["Username", "Password", "Name", "Email"])
        admin.to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "Maliyet", "Adet", "Kat"]).to_csv(PORT_DB, index=False)

init_db()

# --- 2. MODERN BEYAZ ARAYÜZ (CSS) ---
st.set_page_config(page_title="AutoFlow AI Terminal", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #F8FAFC; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    .ai-card { background: white; padding: 25px; border-radius: 15px; border-left: 6px solid #4F46E5; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .stMetric { background: white !important; padding: 20px !important; border-radius: 12px !important; border: 1px solid #F1F5F9 !important; }
    .user-profile { padding: 20px; background: #F8FAFC; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 20px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FONKSİYONLAR ---
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
    df['Güncel Fiyat'] = prices
    df['Toplam Değer'] = df['Güncel Fiyat'] * df['Adet']
    df['Kâr/Zarar'] = df['Toplam Değer'] - (df['Maliyet'] * df['Adet'])
    return df

# --- 4. GİRİŞ PANELİ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<h1 style='text-align:center;'>AKOSELL WMS</h1>", unsafe_allow_html=True)
        with st.container(border=True):
            user = st.text_input("Kullanıcı")
            pw = st.text_input("Şifre", type="password")
            if st.button("TERMİNALE GİRİŞ YAP", use_container_width=True, type="primary"):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(pw)).hexdigest()
                if not users[(users['Username']==user) & (users['Password']==hp)].empty:
                    st.session_state.logged_in = True
                    st.session_state.u_data = users[users['Username']==user].iloc[0].to_dict()
                    st.rerun()
                else: st.error("Kullanıcı adı veya şifre hatalı.")
else:
    # --- 5. SIDEBAR ---
    with st.sidebar:
        st.markdown(f"""<div class="user-profile"><small>HOŞ GELDİN</small><br><b>{st.session_state.u_data['Name'].upper()}</b><br><span style="color:#4F46E5; font-size:11px;">AUTOFLOW PRO</span></div>""", unsafe_allow_html=True)
        menu = st.radio("MENÜ", ["📊 DASHBOARD", "🤖 AI STRATEJİST", "⚖️ OPTİMİZASYON", "⏪ BACKTEST", "💼 PORTFÖYÜM", "⚙️ AYARLAR"])
        st.divider()
        if st.button("GÜVENLİ ÇIKIŞ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Veri Hazırlama
    df_port = pd.read_csv(PORT_DB)
    my_port = df_port[df_port['Owner'] == st.session_state.u_data['Username']] if not df_port.empty else pd.DataFrame()

    # --- 6. DASHBOARD ---
    if menu == "📊 DASHBOARD":
        st.title("Finansal Durum Özeti")
        if not my_port.empty:
            with st.spinner("Piyasa verileri güncelleniyor..."):
                proc_df = fetch_prices(my_port)
                c1, c2, c3 = st.columns(3)
                total_val = proc_df['Toplam Değer'].sum()
                total_profit = proc_df['Kâr/Zarar'].sum()
                
                c1.metric("Toplam Varlık Değeri", f"₺{total_val:,.2f}")
                c2.metric("Net Kâr / Zarar", f"₺{total_profit:,.2f}", delta=f"{(total_profit/(total_val-total_profit)*100):.2f}%")
                c3.metric("Varlık Sayısı", f"{len(proc_df)} Adet")
                
                st.dataframe(proc_df[["Kod", "Kat", "Adet", "Maliyet", "Güncel Fiyat", "Kâr/Zarar"]], use_container_width=True)
        else:
            st.info("Portföyünüz boş. 'PORTFÖYÜM' sekmesinden varlık ekleyin.")

    # --- 7. AI STRATEJİST ---
    elif menu == "🤖 AI STRATEJİST":
        st.title("AutoFlow AI Strateji Merkezi")
        if not my_port.empty:
            target = st.selectbox("Analiz Edilecek Varlık", my_port['Kod'].unique())
            ticker = f"{target}.IS" if my_port[my_port['Kod']==target]['Kat'].values[0]=="Hisse" else f"{target}-USD"
            hist = yf.Ticker(ticker).history(period="1mo")
            
            st.line_chart(hist['Close'])
            
            last_price = hist['Close'].iloc[-1]
            ma20 = hist['Close'].rolling(20).mean().iloc[-1]
            
            st.markdown(f"""
            <div class="ai-card">
                <h3>AI Teknik Analiz: {target}</h3>
                <p>Mevcut Fiyat: <b>{last_price:.2f}</b> | 20 Günlük Trend Ortalaması: <b>{ma20:.2f}</b></p>
                <h4>Sinyal: {"🟢 GÜÇLÜ TREND" if last_price > ma20 else "🔴 ZAYIF TREND"}</h4>
            </div>
            """, unsafe_allow_html=True)
        else: st.warning("Analiz için varlık bulunamadı.")

    # --- 8. OPTİMİZASYON ---
    elif menu == "⚖️ OPTİMİZASYON":
        st.title("Portföy Optimizasyonu (Markowitz)")
        if len(my_port) >= 3:
            assets = my_port['Kod'].unique()
            data = pd.DataFrame()
            for a in assets:
                tk = f"{a}.IS" if my_port[my_port['Kod']==a]['Kat'].values[0]=="Hisse" else f"{a}-USD"
                data[a] = yf.Ticker(tk).history(period="1y")['Close']
            
            returns = data.pct_change().dropna()
            def get_vol(w): return np.sqrt(np.dot(w.T, np.dot(returns.cov() * 252, w)))
            
            cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            res = minimize(get_vol, [1./len(assets)]*len(assets), bounds=[(0,1)]*len(assets), constraints=cons)
            
            st.plotly_chart(go.Figure(data=[go.Pie(labels=assets, values=res.x, hole=.3)]))
            st.success("AI tarafından önerilen en düşük riskli varlık dağılımı yukarıdadır.")
        else: st.warning("Optimizasyon için en az 3 farklı varlık eklemelisiniz.")

    # --- 9. BACKTEST ---
    elif menu == "⏪ BACKTEST":
        st.title("Geçmiş Performans Testi")
        st.write("Portföyünüzün son 1 yıllık seyri ve piyasa (BIST100) kıyaslaması.")
        bist = yf.Ticker("XU100.IS").history(period="1y")['Close']
        st.line_chart((bist / bist.iloc[0]) * 100)
        st.info("Bu grafik BIST100 endeksinin son 1 yıllık normalize edilmiş getirisini gösterir.")

    # --- 10. PORTFÖY YÖNETİMİ ---
    elif menu == "💼 PORTFÖYÜM":
        st.title("Varlık Yönetimi")
        t1, t2 = st.tabs(["Varlık Ekle", "Düzenle / Sil"])
        
        with t1:
            with st.form("ekle_form"):
                c1, c2, c3, c4 = st.columns(4)
                k = c1.text_input("Varlık Kodu (Örn: THYAO, BTC)").upper()
                a = c2.number_input("Adet", min_value=0.0)
                m = c3.number_input("Maliyet", min_value=0.0)
                cat = c4.selectbox("Tür", ["Hisse", "Kripto", "Döviz", "Altın"])
                if st.form_submit_button("SİSTEME KAYDET"):
                    new_row = pd.DataFrame([[st.session_state.u_data['Username'], k, m, a, cat]], columns=["Owner", "Kod", "Maliyet", "Adet", "Kat"])
                    pd.concat([pd.read_csv(PORT_DB), new_row]).to_csv(PORT_DB, index=False)
                    st.success("Varlık eklendi!")
                    st.rerun()
        
        with t2:
            edited = st.data_editor(my_port, num_rows="dynamic", use_container_width=True)
            if st.button("DEĞİŞİKLİKLERİ UYGULA"):
                others = df_port[df_port['Owner'] != st.session_state.u_data['Username']]
                pd.concat([others, edited]).to_csv(PORT_DB, index=False)
                st.success("Portföy güncellendi!")
                st.rerun()

    # --- 11. AYARLAR ---
    elif menu == "⚙️ AYARLAR":
        st.title("Terminal Ayarları")
        with st.expander("🔐 Şifre Değiştir"):
            new_pw = st.text_input("Yeni Şifre", type="password")
            confirm = st.text_input("Şifre Tekrar", type="password")
            if st.button("Şifreyi Güncelle"):
                if new_pw == confirm and len(new_pw) > 3:
                    u_df = pd.read_csv(USER_DB)
                    hp = hashlib.sha256(str.encode(new_pw)).hexdigest()
                    u_df.loc[u_df['Username'] == st.session_state.u_data['Username'], 'Password'] = hp
                    u_df.to_csv(USER_DB, index=False)
                    st.success("Şifreniz başarıyla değiştirildi.")
                else: st.error("Şifreler uyuşmuyor veya çok kısa.")