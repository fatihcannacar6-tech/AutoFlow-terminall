import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SİSTEM YAPILANDIRMASI (KURUMSAL) ---
st.set_page_config(page_title="AKOSELL WMS | Enterprise", layout="wide", page_icon="🏛️")

# Ultra Profesyonel Beyaz UI/UX Tasarımı
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #FFFFFF; }
    
    /* Sidebar Modernizasyonu */
    [data-testid="stSidebar"] { background-color: #F8FAFC !important; border-right: 1px solid #E2E8F0; width: 300px !important; }
    
    /* Metric Kartları (Premium Look) */
    .metric-container { background: #FFFFFF; border: 1px solid #E2E8F0; padding: 24px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .metric-title { color: #64748B; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; }
    .metric-value { color: #0F172A; font-size: 28px; font-weight: 700; margin-top: 8px; }
    
    /* Menü Butonları */
    .stRadio div[role="radiogroup"] label {
        background: transparent !important; border: none !important; padding: 10px 20px !important;
        margin-bottom: 5px !important; border-radius: 8px !important; transition: 0.3s;
    }
    .stRadio div[role="radiogroup"] label:hover { background: #F1F5F9 !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] { background: #00D1FF !important; color: white !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] p { color: white !important; font-weight: 600 !important; }
    
    /* Global Status Badges */
    .badge { padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; }
    .badge-up { background: #DCFCE7; color: #166534; }
    .badge-down { background: #FEE2E2; color: #991B1B; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE ---
USER_DB, PORT_DB, WATCH_DB = "users_pro.csv", "portfolio_pro.csv", "watchlist_pro.csv"

def init_db():
    if not os.path.exists(USER_DB):
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Baş Yönetici", "admin@akosell.com", "Approved", "Admin"]], 
                     columns=["Username", "Password", "Name", "Email", "Status", "Role"]).to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB): 
        pd.DataFrame(columns=["Owner", "Symbol", "Cat", "Cost", "Qty", "Date"]).to_csv(PORT_DB, index=False)
    if not os.path.exists(WATCH_DB):
        pd.DataFrame([["THYAO.IS"], ["BTC-USD"], ["XAU=F"], ["AAPL"], ["EREGL.IS"]], columns=["Symbol"]).to_csv(WATCH_DB, index=False)

init_db()

# --- 3. AUTH LOGIC ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, center, _ = st.columns([1, 0.8, 1])
    with center:
        st.markdown("<h1 style='text-align:center; color:#0F172A; letter-spacing:-1px;'>AKOSELL <span style='font-weight:300'>WMS</span></h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["PROFESYONEL GİRİŞ", "KAYIT TALEBİ"])
        with t1:
            u = st.text_input("Kullanıcı Kimliği")
            p = st.text_input("Güvenlik Anahtarı", type="password")
            if st.button("TERMİNALİ AÇ", use_container_width=True):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(p.encode()).hexdigest()
                user = users[(users['Username']==u) & (users['Password']==hp)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.auth = True
                        st.session_state.u_data = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Erişim yetkiniz henüz onaylanmadı.")
                else: st.error("Kimlik doğrulanamadı.")
        with t2:
            nu, nn, npw = st.text_input("Kullanıcı Adı Seçin"), st.text_input("Tam İsim"), st.text_input("Şifre", type="password")
            if st.button("YÖNETİME GÖNDER", use_container_width=True):
                df_u = pd.read_csv(USER_DB)
                new_u = pd.DataFrame([[nu, hashlib.sha256(npw.encode()).hexdigest(), nn, "", "Pending", "User"]], columns=df_u.columns)
                pd.concat([df_u, new_u]).to_csv(USER_DB, index=False)
                st.info("Talebiniz kuyruğa alındı.")

else:
    # --- 4. NAVIGATION ---
    with st.sidebar:
        st.markdown(f"""<div style="background:#0F172A; padding:25px; border-radius:12px; margin-bottom:20px; color:white;">
            <small style="opacity:0.6">TERMİNAL YETKİLİSİ</small><br>
            <span style="font-size:18px; font-weight:700;">{st.session_state.u_data['Name']}</span>
        </div>""", unsafe_allow_html=True)
        
        menu = st.radio("MENÜ", ["📊 EXECUTIVE DASHBOARD", "🌍 GLOBAL PİYASA EKRANI", "💼 PORTFÖY YÖNETİMİ", "📑 ANALİZ & RAPORLAMA", "🔐 YÖNETİCİ PANELİ" if st.session_state.u_data['Role'] == "Admin" else None], label_visibility="collapsed")
        
        st.divider()
        if st.button("SİSTEMDEN ÇIK"): st.session_state.auth = False; st.rerun()

    # Data Load
    df_p = pd.read_csv(PORT_DB)
    my_p = df_p[df_p['Owner'] == st.session_state.u_data['Username']].copy()

    # --- 5. EXECUTIVE DASHBOARD ---
    if menu == "📊 EXECUTIVE DASHBOARD":
        st.title("Executive Dashboard")
        
        if not my_p.empty:
            with st.spinner("Piyasa verileri canlı senkronize ediliyor..."):
                all_symbols = my_p['Symbol'].unique()
                prices = {s: yf.Ticker(s).history(period="1d")['Close'].iloc[-1] for s in all_symbols}
                my_p['Current'] = my_p['Symbol'].map(prices)
                my_p['Value'] = my_p['Current'] * my_p['Qty']
                my_p['PL'] = my_p['Value'] - (my_p['Cost'] * my_p['Qty'])
                my_p['PL_Perc'] = (my_p['PL'] / (my_p['Cost'] * my_p['Qty'])) * 100

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="metric-container"><div class="metric-title">Toplam Portföy</div><div class="metric-value">₺{my_p["Value"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-container"><div class="metric-title">Net Kar/Zarar</div><div class="metric-value" style="color:{"#10B981" if my_p["PL"].sum() > 0 else "#EF4444"}">₺{my_p["PL"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-container"><div class="metric-title">Büyüme Oranı</div><div class="metric-value">%{ (my_p["PL"].sum() / (my_p["Cost"]*my_p["Qty"]).sum() * 100):.2f}</div></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-container"><div class="metric-title">Varlık Adedi</div><div class="metric-value">{len(my_p)}</div></div>', unsafe_allow_html=True)

            st.divider()
            col_l, col_r = st.columns([2, 1])
            with col_l:
                st.subheader("Varlık Performans Matrisi")
                fig = px.bar(my_p, x='Symbol', y='PL', color='PL', color_continuous_scale='RdYlGn', template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            with col_r:
                st.subheader("Stratejik Dağılım")
                fig_pie = px.pie(my_p, values='Value', names='Cat', hole=0.6, color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Portföy verisi bulunamadı. Lütfen varlık ekleyin.")

    # --- 6. GLOBAL PİYASA EKRANI (FULL ACCESS) ---
    elif menu == "🌍 GLOBAL PİYASA EKRANI":
        st.title("Global Piyasa Terminali")
        
        c1, c2 = st.columns([1, 3])
        with c1:
            st.subheader("Varlık Arama")
            search = st.text_input("Sembol Girin", placeholder="Örn: THYAO.IS, BTC-USD, TSLA, GC=F").upper()
            period = st.selectbox("Zaman Dilimi", ["1mo", "3mo", "1y", "5y", "max"])
            
            if search:
                ticker = yf.Ticker(search)
                try:
                    info = ticker.info
                    st.success(f"Varlık Bulundu: {info.get('longName', search)}")
                    st.metric("Güncel Fiyat", f"{ticker.history(period='1d')['Close'].iloc[-1]:,.2f}")
                    if st.button("PORTFÖYE EKLEMEK İÇİN SEÇ"):
                        st.session_state.tmp_symbol = search
                except: st.error("Sembol doğrulanamadı.")
        
        with c2:
            if search:
                data = yf.download(search, period=period)
                if not data.empty:
                    fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
                    fig.update_layout(title=f"{search} Teknik Görünüm", template="plotly_white", xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                else: st.warning("Grafik verisi yüklenemedi.")

    # --- 7. PORTFÖY YÖNETİMİ ---
    elif menu == "💼 PORTFÖY YÖNETİMİ":
        st.title("Varlık Yönetim Merkezi")
        t1, t2 = st.tabs(["🆕 YENİ POZİSYON AÇ", "⚙️ MEVCUT POZİSYONLARI YÖNET"])
        
        with t1:
            with st.form("add_asset_form"):
                c1, c2, c3, c4 = st.columns(4)
                sym = c1.text_input("Sembol", value=st.session_state.get('tmp_symbol', '')).upper()
                cat = c2.selectbox("Kategori", ["Hisse Senedi", "Kripto Varlık", "Emtia", "Yabancı Hisse", "Döviz"])
                qty = c3.number_input("Miktar", min_value=0.0, step=0.01)
                cost = c4.number_input("Birim Maliyet", min_value=0.0)
                if st.form_submit_button("SİSTEME İŞLE"):
                    new_row = pd.DataFrame([[st.session_state.u_data['Username'], sym, cat, cost, qty, datetime.now().date()]], columns=df_p.columns)
                    pd.concat([df_p, new_row]).to_csv(PORT_DB, index=False)
                    st.success("İşlem başarıyla kaydedildi."); st.rerun()

        with t2:
            if not my_p.empty:
                edited = st.data_editor(my_p.drop(columns=['Owner']), use_container_width=True, num_rows="dynamic")
                if st.button("GÜNCELLEMELERİ YAYINLA"):
                    others = df_p[df_p['Owner'] != st.session_state.u_data['Username']]
                    edited['Owner'] = st.session_state.u_data['Username']
                    pd.concat([others, edited]).to_csv(PORT_DB, index=False)
                    st.rerun()
            else: st.info("Düzenlenecek varlık yok.")

    # --- 8. ANALİZ & RAPORLAMA ---
    elif menu == "📑 ANALİZ & RAPORLAMA":
        st.title("Kurumsal Analiz Raporu")
        if not my_p.empty:
            # Excel/CSV İndirme
            st.download_button("📥 ANALİZİ DIŞA AKTAR (CSV)", my_p.to_csv(index=False), f"AKOSELL_Rapor_{datetime.now().date()}.csv", "text/csv")
            
            # Detaylı Analiz Tablosu
            st.subheader("Varlık Detaylı Döküm")
            st.dataframe(my_p.style.background_gradient(subset=['PL'], cmap='RdYlGn'), use_container_width=True)
            
            # Risk Metrikleri
            st.divider()
            st.subheader("Risk Değerlendirmesi")
            max_risk = my_p.loc[my_p['Value'].idxmax()]
            st.warning(f"**En Yüksek Konsantrasyon:** {max_risk['Symbol']} (%{(max_risk['Value']/my_p['Value'].sum()*100):.1f})")
            
    # --- 9. YÖNETİCİ PANELİ ---
    elif menu == "🔐 YÖNETİCİ PANELİ":
        st.title("Admin Kontrol Merkezi")
        u_df = pd.read_csv(USER_DB)
        
        st.subheader("Bekleyen Erişim Talepleri")
        pending = u_df[u_df['Status'] == "Pending"]
        if not pending.empty:
            for i, r in pending.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.info(f"Kullanıcı: **{r['Name']}** | Kimlik: **{r['Username']}**")
                if col2.button("✅ ONAYLA", key=f"y_{i}"):
                    u_df.at[i, 'Status'] = "Approved"
                    u_df.to_csv(USER_DB, index=False); st.rerun()
                if col3.button("❌ REDDET", key=f"n_{i}"):
                    u_df = u_df.drop(i)
                    u_df.to_csv(USER_DB, index=False); st.rerun()
        else: st.success("Bekleyen onay talebi bulunmuyor.")
        
        st.divider()
        st.subheader("Tüm Kayıtlı Kullanıcılar")
        st.dataframe(u_df[['Username', 'Name', 'Status', 'Role']], use_container_width=True)