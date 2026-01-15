import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import hashlib
import os
from datetime import datetime
import plotly.graph_objects as go
from scipy.optimize import minimize

# --- 1. VERİTABANI VE YÖNETİM AYARLARI ---
USER_DB, PORT_DB = "users_v13.csv", "portfolio_v13.csv"

def init_db():
    if not os.path.exists(USER_DB):
        # Admin: fatihcan / 8826244 (Status: Active)
        hp = hashlib.sha256(str.encode("8826244")).hexdigest()
        users = pd.DataFrame([["fatihcan", hp, "Fatih Can", "Admin", "Active"]], 
                             columns=["Username", "Password", "Name", "Role", "Status"])
        users.to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "Maliyet", "Adet", "Kat"]).to_csv(PORT_DB, index=False)

init_db()

# --- 2. BEYAZ ARAYÜZ VE STİL ---
st.set_page_config(page_title="AutoFlow AI Terminal", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    .ai-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 20px; }
    .status-pending { color: #F59E0B; font-weight: bold; }
    .status-active { color: #10B981; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GİRİŞ VE KAYIT SİSTEMİ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab1:
        with st.container(border=True):
            u = st.text_input("Kullanıcı Adı", key="login_u")
            p = st.text_input("Şifre", type="password", key="login_p")
            if st.button("Giriş", use_container_width=True):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(p)).hexdigest()
                user_match = users[(users['Username']==u) & (users['Password']==hp)]
                if not user_match.empty:
                    if user_match.iloc[0]['Status'] == "Active":
                        st.session_state.logged_in = True
                        st.session_state.u_data = user_match.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Hesabınız admin onayı bekliyor.")
                else: st.error("Hatalı bilgiler.")
                
    with tab2:
        with st.container(border=True):
            new_u = st.text_input("Yeni Kullanıcı Adı")
            new_n = st.text_input("Ad Soyad")
            new_p = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Talebi Gönder", use_container_width=True):
                users = pd.read_csv(USER_DB)
                if new_u in users['Username'].values: st.error("Bu kullanıcı adı alınmış.")
                else:
                    hp = hashlib.sha256(str.encode(new_p)).hexdigest()
                    new_user = pd.DataFrame([[new_u, hp, new_n, "User", "Pending"]], columns=users.columns)
                    new_user.to_csv(USER_DB, mode='a', header=False, index=False)
                    st.success("Talebiniz iletildi. Admin onayı bekleniyor.")

else:
    # --- 4. SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 🏛️ AutoFlow AI\n**{st.session_state.u_data['Name']}**")
        nav_options = ["📊 DASHBOARD", "🔍 PİYASA TAKİBİ", "🤖 AI STRATEJİST", "⚖️ OPTİMİZASYON", "💼 PORTFÖYÜM", "⚙️ AYARLAR"]
        if st.session_state.u_data['Role'] == "Admin": nav_options.append("🔑 ADMIN PANELİ")
        menu = st.radio("MENÜ", nav_options)
        if st.button("Çıkış"):
            st.session_state.logged_in = False
            st.rerun()

    df_port = pd.read_csv(PORT_DB)
    my_port = df_port[df_port['Owner'] == st.session_state.u_data['Username']]

    # --- 5. PİYASA TAKİBİ (YENİ ÖZELLİK) ---
    if menu == "🔍 PİYASA TAKİBİ":
        st.title("🔍 Canlı Piyasa Explorer")
        search_query = st.text_input("Hisse veya Kripto Ara (Örn: THYAO, BTC-USD, GOLD)", "THYAO")
        
        ticker_code = search_query + ".IS" if len(search_query) <= 5 and "-" not in search_query else search_query
        try:
            asset = yf.Ticker(ticker_code)
            info = asset.history(period="1d")
            if not info.empty:
                c1, c2, c3 = st.columns(3)
                curr_price = info['Close'].iloc[-1]
                prev_price = asset.history(period="2d")['Close'].iloc[0]
                diff = ((curr_price - prev_price) / prev_price) * 100
                
                c1.metric(search_query, f"{curr_price:.2f}", f"{diff:.2f}%")
                
                st.subheader("Fiyat Grafiği (7 Günlük)")
                st.line_chart(asset.history(period="7d")['Close'])
            else: st.error("Varlık bulunamadı.")
        except: st.error("Hatalı kod girişi.")

    # --- 6. OPTİMİZASYON (DETAYLI RAPORLU) ---
    elif menu == "⚖️ OPTİMİZASYON":
        st.title("⚖️ Modern Portföy Optimizasyonu")
        if len(my_port) >= 3:
            assets = my_port['Kod'].unique()
            data = pd.DataFrame()
            for a in assets:
                tk = f"{a}.IS" if my_port[my_port['Kod']==a]['Kat'].values[0]=="Hisse" else f"{a}-USD"
                data[a] = yf.Ticker(tk).history(period="1y")['Close']
            
            returns = data.pct_change().dropna()
            mean_ret = returns.mean() * 252
            cov_mat = returns.cov() * 252
            
            def port_stats(w):
                p_ret = np.sum(mean_ret * w)
                p_vol = np.sqrt(np.dot(w.T, np.dot(cov_mat, w)))
                return p_ret, p_vol, p_ret/p_vol

            res = minimize(lambda w: -port_stats(w)[2], [1./len(assets)]*len(assets), 
                           bounds=[(0,1)]*len(assets), constraints={'type':'eq','fun': lambda x: np.sum(x)-1})
            
            # Detaylı Rapor Alanı
            opt_ret, opt_vol, opt_sharpe = port_stats(res.x)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Beklenen Yıllık Getiri", f"%{opt_ret*100:.2f}")
            c2.metric("Portföy Riski (Volatilite)", f"%{opt_vol*100:.2f}")
            c3.metric("Sharpe Oranı (Verimlilik)", f"{opt_sharpe:.2f}")
            
            st.divider()
            st.subheader("İdeal Dağılım Raporu")
            st.plotly_chart(go.Figure(data=[go.Pie(labels=assets, values=res.x, hole=.4)]))
            
            

        else: st.warning("En az 3 varlık eklemelisiniz.")

    # --- 7. ADMIN PANELİ (ONAY/RET) ---
    elif menu == "🔑 ADMIN PANELİ":
        st.title("🔑 Admin Kontrol Merkezi")
        users_df = pd.read_csv(USER_DB)
        pending = users_df[users_df['Status'] == "Pending"]
        
        if not pending.empty:
            st.write(f"Onay bekleyen {len(pending)} kullanıcı var.")
            for i, row in pending.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f"**{row['Name']}** (@{row['Username']})")
                if col2.button("✅ Onayla", key=f"app_{row['Username']}"):
                    users_df.loc[users_df['Username'] == row['Username'], 'Status'] = "Active"
                    users_df.to_csv(USER_DB, index=False)
                    st.rerun()
                if col3.button("❌ Reddet", key=f"rej_{row['Username']}"):
                    users_df = users_df[users_df['Username'] != row['Username']]
                    users_df.to_csv(USER_DB, index=False)
                    st.rerun()
        else:
            st.info("Onay bekleyen kullanıcı bulunmuyor.")
        
        st.divider()
        st.subheader("Tüm Kullanıcılar")
        st.dataframe(users_df[["Username", "Name", "Role", "Status"]])

    # (Dashboard, AI Stratejist, Portföyüm ve Ayarlar kısımları aynı mantıkla çalışır)
    elif menu == "📊 DASHBOARD":
        st.title("📊 Finansal Durum")
        # Mevcut Dashboard kodun...
        st.write("Hoş geldiniz. Portföy verileriniz burada listelenir.")

    elif menu == "💼 PORTFÖYÜM":
        st.title("💼 Varlık Yönetimi")
        # Varlık ekleme kodun...
        with st.form("add_v13"):
            c1, c2, c3 = st.columns(3)
            k = c1.text_input("Kod").upper()
            a = c2.number_input("Adet")
            m = c3.number_input("Maliyet")
            if st.form_submit_button("Ekle"):
                new = pd.DataFrame([[st.session_state.u_data['Username'], k, m, a, "Hisse"]], columns=df_port.columns)
                pd.concat([pd.read_csv(PORT_DB), new]).to_csv(PORT_DB, index=False)
                st.rerun()