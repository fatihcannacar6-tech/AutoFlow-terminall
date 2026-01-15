import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import hashlib
import os
from datetime import datetime
import plotly.graph_objects as go
from scipy.optimize import minimize

# --- 1. SİSTEM AYARLARI VE DATABASE ---
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

# --- 2. BEYAZ ARAYÜZ ---
st.set_page_config(page_title="AutoFlow AI Terminal", layout="wide", page_icon="🏛️")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
    .ai-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .stMetric { background: white !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. YARDIMCI FONKSİYONLAR ---
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

# --- 4. GİRİŞ VE KAYIT PANELİ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    with tab1:
        with st.container(border=True):
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap", use_container_width=True, type="primary"):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(p)).hexdigest()
                user_match = users[(users['Username']==u) & (users['Password']==hp)]
                if not user_match.empty:
                    if user_match.iloc[0]['Status'] == "Active":
                        st.session_state.logged_in = True
                        st.session_state.u_data = user_match.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Hesabınız admin onayı bekliyor.")
                else: st.error("Kullanıcı adı veya şifre hatalı.")
    
    with tab2:
        with st.container(border=True):
            new_u = st.text_input("Yeni Kullanıcı Adı (Küçük harf)")
            new_n = st.text_input("Ad Soyad")
            new_p = st.text_input("Yeni Şifre", type="password")
            if st.button("Kayıt Talebi Gönder", use_container_width=True):
                users = pd.read_csv(USER_DB)
                if new_u in users['Username'].values: st.error("Bu kullanıcı adı zaten alınmış.")
                else:
                    hp = hashlib.sha256(str.encode(new_p)).hexdigest()
                    new_user = pd.DataFrame([[new_u, hp, new_n, "User", "Pending"]], columns=users.columns)
                    new_user.to_csv(USER_DB, mode='a', header=False, index=False)
                    st.success("Talebiniz iletildi. Admin (fatihcan) onayı bekleniyor.")

else:
    # --- 5. SIDEBAR NAVİGASYON ---
    with st.sidebar:
        st.markdown(f"### 🏛️ AutoFlow AI\n**{st.session_state.u_data.get('Name', 'Kullanıcı')}**")
        nav_options = ["📊 DASHBOARD", "🔍 PİYASA TAKİBİ", "🤖 AI STRATEJİST", "⚖️ OPTİMİZASYON", "💼 PORTFÖYÜM", "⚙️ AYARLAR"]
        
        # Admin Rolü Kontrolü (Hata düzeltilmiş hali)
        user_role = st.session_state.u_data.get('Role', 'User')
        if user_role == "Admin":
            nav_options.append("🔑 ADMIN PANELİ")
            
        menu = st.radio("MENÜ", nav_options)
        if st.button("Çıkış Yap"):
            st.session_state.logged_in = False
            st.rerun()

    # Ortak Veriler
    df_port = pd.read_csv(PORT_DB)
    my_port = df_port[df_port['Owner'] == st.session_state.u_data['Username']] if not df_port.empty else pd.DataFrame()

    # --- 6. DASHBOARD ---
    if menu == "📊 DASHBOARD":
        st.title("📊 Finansal Durum Paneli")
        if not my_port.empty:
            proc_df = fetch_prices(my_port)
            c1, c2, c3 = st.columns(3)
            val = proc_df['Toplam Değer'].sum()
            prof = proc_df['Kâr/Zarar'].sum()
            c1.metric("Toplam Varlık", f"₺{val:,.2f}")
            c2.metric("Net Kâr/Zarar", f"₺{prof:,.2f}", delta=f"{(prof/val*100):.2f}%" if val > 0 else "0%")
            c3.metric("Varlık Sayısı", len(proc_df))
            st.dataframe(proc_df[["Kod", "Kat", "Adet", "Maliyet", "Güncel Fiyat", "Kâr/Zarar"]], use_container_width=True, hide_index=True)
        else: st.info("Portföyünüz boş.")

    # --- 7. PİYASA TAKİBİ (YENİ ARAMA ÇUBUĞU) ---
    elif menu == "🔍 PİYASA TAKİBİ":
        st.title("🔍 Canlı Piyasa Arama")
        search = st.text_input("Sembol Girin (Örn: THYAO, BTC-USD, USDTRY=X, GOLD)", "THYAO")
        symbol = f"{search}.IS" if len(search) <= 5 and "-" not in search and "=" not in search else search
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1mo")
            if not data.empty:
                curr = data['Close'].iloc[-1]
                diff = ((curr - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
                st.metric(f"{search.upper()} Fiyatı", f"{curr:.2f}", f"{diff:.2f}%")
                st.line_chart(data['Close'])
            else: st.error("Veri bulunamadı.")
        except: st.error("Geçersiz sembol.")

    # --- 8. AI OPTİMİZASYON (DETAYLI RAPORLU) ---
    elif menu == "⚖️ OPTİMİZASYON":
        st.title("⚖️ Portföy Optimizasyonu")
        if len(my_port) >= 3:
            with st.spinner("Analiz ediliyor..."):
                assets = my_port['Kod'].unique()
                prices = pd.DataFrame()
                for a in assets:
                    tk = f"{a}.IS" if my_port[my_port['Kod']==a]['Kat'].values[0]=="Hisse" else f"{a}-USD"
                    prices[a] = yf.Ticker(tk).history(period="1y")['Close']
                
                returns = prices.pct_change().dropna()
                mean_ret = returns.mean() * 252
                cov_mat = returns.cov() * 252

                def get_stats(w):
                    p_ret = np.sum(mean_ret * w)
                    p_vol = np.sqrt(np.dot(w.T, np.dot(cov_mat, w)))
                    return p_ret, p_vol, (p_ret - 0.05) / p_vol # Sharpe

                res = minimize(lambda w: -get_stats(w)[2], [1./len(assets)]*len(assets), 
                               bounds=[(0,1)]*len(assets), constraints={'type':'eq','fun': lambda x: np.sum(x)-1})
                
                ret, vol, sharpe = get_stats(res.x)
                
                st.markdown(f"""
                <div class="ai-card">
                    <h4>📊 Optimizasyon Detay Raporu</h4>
                    <p>Bu dağılım, geçmiş 1 yıllık veriler baz alınarak <b>Maksimum Sharpe Oranı</b> (En iyi verimlilik) hedefiyle oluşturulmuştur.</p>
                    <ul>
                        <li>Beklenen Yıllık Getiri: <b>%{ret*100:.2f}</b></li>
                        <li>Yıllık Risk (Volatilite): <b>%{vol*100:.2f}</b></li>
                        <li>Sharpe Katsayısı: <b>{sharpe:.2f}</b></li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                fig = go.Figure(data=[go.Pie(labels=assets, values=res.x, hole=.3)])
                st.plotly_chart(fig, use_container_width=True)
                
        else: st.warning("Detaylı rapor için en az 3 farklı varlık eklemelisiniz.")

    # --- 9. ADMIN PANELİ ---
    elif menu == "🔑 ADMIN PANELİ":
        st.title("🔑 Admin Kontrol Merkezi")
        u_df = pd.read_csv(USER_DB)
        pending = u_df[u_df['Status'] == "Pending"]
        
        if not pending.empty:
            st.subheader(f"Onay Bekleyenler ({len(pending)})")
            for i, row in pending.iterrows():
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{row['Name']}** (@{row['Username']})")
                if c2.button("✅ ONAY", key=f"ok_{row['Username']}"):
                    u_df.loc[u_df['Username'] == row['Username'], 'Status'] = "Active"
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
                if c3.button("❌ RED", key=f"no_{row['Username']}"):
                    u_df = u_df[u_df['Username'] != row['Username']]
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
        else: st.info("Bekleyen talep yok.")
        
        st.divider()
        st.subheader("Sistemdeki Tüm Kullanıcılar")
        st.dataframe(u_df[["Username", "Name", "Role", "Status"]], use_container_width=True)

    # --- 10. PORTFÖYÜM ---
    elif menu == "💼 PORTFÖYÜM":
        st.title("💼 Varlık Yönetimi")
        with st.form("add_asset_v13"):
            c1, c2, c3, c4 = st.columns(4)
            k = c1.text_input("Kod (Örn: THYAO)").upper()
            a = c2.number_input("Adet", min_value=0.0)
            m = c3.number_input("Maliyet", min_value=0.0)
            cat = c4.selectbox("Tür", ["Hisse", "Kripto", "Döviz", "Altın"])
            if st.form_submit_button("Sisteme Ekle"):
                new = pd.DataFrame([[st.session_state.u_data['Username'], k, m, a, cat]], columns=df_port.columns)
                pd.concat([pd.read_csv(PORT_DB), new]).to_csv(PORT_DB, index=False)
                st.rerun()
        
        st.divider()
        st.subheader("Varlıkları Düzenle")
        edited = st.data_editor(my_port, num_rows="dynamic", use_container_width=True)
        if st.button("Güncellemeleri Kaydet"):
            others = df_port[df_port['Owner'] != st.session_state.u_data['Username']]
            pd.concat([others, edited]).to_csv(PORT_DB, index=False)
            st.success("Portföy güncellendi!")

    # --- 11. AYARLAR ---
    elif menu == "⚙️ AYARLAR":
        st.title("⚙️ Hesap Ayarları")
        with st.expander("🔐 Şifre Değiştir"):
            new_pw = st.text_input("Yeni Şifre", type="password")
            if st.button("Güncelle"):
                u_df = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(new_pw)).hexdigest()
                u_df.loc[u_df['Username'] == st.session_state.u_data['Username'], 'Password'] = hp
                u_df.to_csv(USER_DB, index=False)
                st.success("Şifreniz güncellendi.")