import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
from datetime import datetime
import streamlit.components.v1 as components
import plotly.express as px

# --- 1. ENTERPRISE CONFIG & THEME ---
st.set_page_config(page_title="AKOSELL Enterprise SaaS", layout="wide", page_icon="🏛️")

# Kurumsal Beyaz Tema ve Modern CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #FFFFFF; color: #1E293B; }
    
    /* Sidebar Tasarımı */
    [data-testid="stSidebar"] { background-color: #F8FAFC !important; border-right: 1px solid #E2E8F0; }
    [data-testid="stSidebar"] * { color: #1E293B !important; }
    
    /* Kart Tasarımları */
    .metric-card {
        background: white; padding: 24px; border-radius: 12px; border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: left;
    }
    .metric-label { font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 28px; font-weight: 700; color: #0F172A; margin-top: 8px; }
    
    /* Tablo ve Inputlar */
    .stDataFrame { border-radius: 8px; overflow: hidden; border: 1px solid #E2E8F0; }
    .stButton>button { border-radius: 6px; font-weight: 600; }
    
    /* Badge Modelleri */
    .badge { padding: 4px 10px; border-radius: 99px; font-size: 11px; font-weight: 700; }
    .badge-crypto { background: #FFF7ED; color: #C2410C; }
    .badge-stock { background: #F0FDF4; color: #15803D; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ARCHITECTURE ---
USER_DB = "saas_users.csv"
PORT_DB = "saas_portfolio.csv"
LOG_DB = "saas_audit.csv"

def init_db():
    if not os.path.exists(USER_DB):
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        pd.DataFrame([["admin@akosell.com", admin_pw, "System Admin", "Approved", "Admin"]], 
                     columns=["Email", "Password", "Name", "Status", "Role"]).to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Symbol", "Type", "Qty", "AvgPrice", "Sector"]).to_csv(PORT_DB, index=False)
    if not os.path.exists(LOG_DB):
        pd.DataFrame(columns=["Time", "User", "Action"]).to_csv(LOG_DB, index=False)

init_db()

# --- 3. CORE FUNCTIONS ---
def get_price(symbol, type):
    try:
        suffix = ".IS" if type == "Hisse" else "-USD" if type == "Kripto" else ""
        data = yf.Ticker(f"{symbol}{suffix}").history(period="1d")
        return data['Close'].iloc[-1]
    except: return 0.0

def tv_chart(symbol="BIST:XU100"):
    chart_html = f"""
    <div style="height:500px;">
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
          "autosize": true, "symbol": "{symbol}", "interval": "D", "timezone": "Etc/UTC",
          "theme": "light", "style": "1", "locale": "tr", "container_id": "tv_chart"
        }});
        </script>
        <div id="tv_chart" style="height:500px;"></div>
    </div>
    """
    components.html(chart_html, height=520)

# --- 4. AUTHENTICATION & REGISTRATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 0.8, 1])
    with col:
        st.markdown("<h2 style='text-align:center;'>AKOSELL <span style='font-weight:300'>WMS</span></h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Talebi"])
        
        with tab1:
            email = st.text_input("E-posta")
            pw = st.text_input("Şifre", type="password")
            if st.button("Sisteme Eriş", use_container_width=True):
                df = pd.read_csv(USER_DB)
                hp = hashlib.sha256(pw.encode()).hexdigest()
                user = df[(df['Email']==email) & (df['Password']==hp)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.logged_in = True
                        st.session_state.user = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Hesabınız henüz Admin tarafından onaylanmamış.")
                else: st.error("Hatalı kimlik bilgileri.")
        
        with tab2:
            n_name = st.text_input("Ad Soyad")
            n_email = st.text_input("E-posta Adresi")
            n_pw = st.text_input("Şifre Belirle", type="password")
            if st.button("Kayıt Talebi Gönder", use_container_width=True):
                df = pd.read_csv(USER_DB)
                if n_email in df['Email'].values: st.error("Bu e-posta zaten kayıtlı.")
                else:
                    new_u = pd.DataFrame([[n_email, hashlib.sha256(n_pw.encode()).hexdigest(), n_name, "Pending", "User"]], columns=df.columns)
                    pd.concat([df, new_u]).to_csv(USER_DB, index=False)
                    st.success("Talebiniz iletildi. Admin onayı bekleniyor.")

else:
    # --- 5. ENTERPRISE DASHBOARD ---
    with st.sidebar:
        st.markdown(f"### {st.session_state.user['Name']}")
        st.markdown(f"`{st.session_state.user['Role']}`")
        st.divider()
        menu = st.radio("MENÜ", ["📊 Dashboard", "💼 Portföy Yönetimi", "📈 TradingView Analiz", "🛡️ Risk Modülü", "🔐 Admin Paneli" if st.session_state.user['Role'] == "Admin" else None])
        if st.button("Güvenli Çıkış"): st.session_state.logged_in = False; st.rerun()

    p_df = pd.read_csv(PORT_DB)
    my_p = p_df[p_df['Owner'] == st.session_state.user['Email']].copy()

    if menu == "📊 Dashboard":
        st.title("Executive Summary")
        
        if not my_p.empty:
            with st.spinner("Varlıklar değerleniyor..."):
                my_p['CurrentPrice'] = [get_price(r['Symbol'], r['Type']) for _, r in my_p.iterrows()]
                my_p['TotalValue'] = my_p['CurrentPrice'] * my_p['Qty']
                my_p['CostValue'] = my_p['AvgPrice'] * my_p['Qty']
                my_p['PL'] = my_p['TotalValue'] - my_p['CostValue']

            # Üst KPI Kartları
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="metric-card"><div class="metric-label">Toplam Portföy</div><div class="metric-value">₺{my_p["TotalValue"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><div class="metric-label">Net Kar/Zarar</div><div class="metric-value">₺{my_p["PL"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><div class="metric-label">Borsa Ağırlığı</div><div class="metric-value">%{ (my_p[my_p["Type"]=="Hisse"]["TotalValue"].sum() / my_p["TotalValue"].sum() * 100):.1f}</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-card"><div class="metric-label">Kripto Ağırlığı</div><div class="metric-value">%{ (my_p[my_p["Type"]=="Kripto"]["TotalValue"].sum() / my_p["TotalValue"].sum() * 100):.1f}</div></div>', unsafe_allow_html=True)
            
            st.divider()
            
            # Tablo Görünümü
            st.subheader("Gelişmiş Varlık Tablosu")
            st.dataframe(my_p[['Symbol', 'Type', 'Qty', 'AvgPrice', 'CurrentPrice', 'PL']], use_container_width=True)
        else:
            st.info("Henüz varlık eklenmemiş. Portföy Yönetimi sayfasından başlayın.")

    elif menu == "💼 Portföy Yönetimi":
        st.title("Varlık & API Yönetimi")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Varlık Ekle")
            with st.form("add_asset"):
                s = st.text_input("Sembol (THYAO / BTC)").upper()
                t = st.selectbox("Tür", ["Hisse", "Kripto", "Fon"])
                q = st.number_input("Adet", min_value=0.0)
                p = st.number_input("Maliyet")
                sk = st.text_input("Sektör/Kategori")
                if st.form_submit_button("Sisteme İşle"):
                    new_line = pd.DataFrame([[st.session_state.user['Email'], s, t, q, p, sk]], columns=p_df.columns)
                    pd.concat([p_df, new_line]).to_csv(PORT_DB, index=False)
                    st.success(f"{s} başarıyla eklendi.")
                    st.rerun()
        
        with col2:
            st.subheader("Düzenle / Sil")
            edited = st.data_editor(my_p, use_container_width=True, num_rows="dynamic")
            if st.button("Değişiklikleri Kaydet"):
                other_users = p_df[p_df['Owner'] != st.session_state.user['Email']]
                pd.concat([other_users, edited]).to_csv(PORT_DB, index=False)
                st.rerun()

    elif menu == "📈 TradingView Analiz":
        st.title("Teknik Analiz Terminali")
        target = st.selectbox("Varlık Seçin", my_p['Symbol'].unique() if not my_p.empty else ["XU100"])
        
        # Grafik için sembol formatlama
        is_crypto = my_p[my_p['Symbol'] == target]['Type'].values[0] == "Kripto" if not my_p.empty else False
        tv_symbol = f"BINANCE:{target}USDT" if is_crypto else f"BIST:{target}"
        
        tv_chart(tv_symbol)

    elif menu == "🛡️ Risk Modülü":
        st.title("Risk & Diversifikasyon Analizi")
        if not my_p.empty:
            c1, c2 = st.columns(2)
            with c1:
                fig = px.pie(my_p, values='TotalValue', names='Symbol', hole=0.6, title="Varlık Konsantrasyonu")
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                fig2 = px.bar(my_p, x='Symbol', y='PL', color='Type', title="Kar/Zarar Dağılımı")
                st.plotly_chart(fig2, use_container_width=True)

    elif menu == "🔐 Admin Paneli":
        st.title("Sistem Yönetim Merkezi")
        u_df = pd.read_csv(USER_DB)
        
        st.subheader("Kayıt Talepleri")
        pending = u_df[u_df['Status'] == "Pending"]
        if not pending.empty:
            for idx, row in pending.iterrows():
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{row['Name']}** ({row['Email']})")
                if c2.button("Onayla", key=f"app_{idx}"):
                    u_df.at[idx, 'Status'] = "Approved"
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
                if c3.button("Reddet", key=f"rej_{idx}"):
                    u_df = u_df.drop(idx)
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
        else:
            st.success("Bekleyen kayıt talebi yok.")
            
        st.divider()
        st.subheader("Tüm Kullanıcılar")
        st.dataframe(u_df, use_container_width=True)