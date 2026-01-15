import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import hashlib
import os
import time

# ==========================================
# 1. KONFİGÜRASYON VE CSS (UI MOTORU)
# ==========================================
st.set_page_config(
    page_title="AUTOFLOW | Terminal",
    layout="wide",
    page_icon="🌊",
    initial_sidebar_state="expanded"
)

# --- TASARIM SİSTEMİ (CSS) ---
st.markdown("""
<style>
    /* 1. GLOBAL RESET & FONTLAR */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #000000 !important; /* Gerçek Siyah */
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
    }
    
    /* 2. SIDEBAR (NAVIGASYON) */
    [data-testid="stSidebar"] {
        background-color: #0E0E10 !important;
        border-right: 1px solid #1F1F23;
    }
    
    /* 3. KART TASARIMLARI (MODÜLER) */
    .metric-card {
        background-color: #111113;
        border: 1px solid #2A2A2E;
        border-radius: 12px;
        padding: 24px;
        transition: transform 0.2s ease;
        height: 100%;
    }
    .metric-card:hover {
        border-color: #3B82F6; /* Hover'da Mavi Çerçeve */
        transform: translateY(-2px);
    }
    
    .card-label {
        font-size: 12px;
        color: #888888;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    .card-value {
        font-size: 28px;
        font-weight: 700;
        color: #FFFFFF;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .trend-up { color: #00C853; font-size: 14px; font-weight: 600; }
    .trend-down { color: #FF3D00; font-size: 14px; font-weight: 600; }
    
    /* 4. AI & HABER KARTLARI */
    .ai-box {
        background: linear-gradient(145deg, #111113 0%, #0D131F 100%);
        border-left: 4px solid #3B82F6;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    
    /* 5. INPUT & BUTTONS */
    .stTextInput > div > div > input {
        background-color: #1A1A1D;
        color: white;
        border: 1px solid #333;
        border-radius: 6px;
    }
    .stSelectbox > div > div > div {
        background-color: #1A1A1D;
        color: white;
    }
    button[kind="primary"] {
        background-color: #2962FF !important;
        border: none;
        color: white;
        font-weight: 600;
        border-radius: 6px;
        transition: 0.3s;
    }
    button[kind="primary"]:hover {
        box-shadow: 0 0 15px rgba(41, 98, 255, 0.4);
    }
    
    /* 6. TABLO VE GRAFİKLER */
    [data-testid="stDataFrame"] { border: 1px solid #222; border-radius: 8px; }
    
    /* 7. CUSTOM HEADERS */
    h1, h2, h3 { color: #FFFFFF; font-weight: 700; letter-spacing: -0.5px; }
    hr { border-color: #222; }
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. VERİ ALTYAPISI (DATABASE)
# ==========================================
FILES = {"users": "af_users.csv", "port": "af_assets.csv"}

def init_system():
    # Kullanıcı DB
    if not os.path.exists(FILES["users"]):
        # Varsayılan Admin: admin / admin123
        admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
        df = pd.DataFrame([["admin", admin_pass, "System Director", "Approved", "Admin"]], 
                          columns=["User", "Pass", "Name", "Status", "Role"])
        df.to_csv(FILES["users"], index=False)
    
    # Portföy DB
    if not os.path.exists(FILES["port"]):
        pd.DataFrame(columns=["Owner", "Sym", "Type", "Qty", "Cost", "Date"]).to_csv(FILES["port"], index=False)

init_system()

# ==========================================
# 3. YARDIMCI FONKSİYONLAR
# ==========================================
@st.cache_data(ttl=60)
def get_price_data(symbol):
    try:
        # Hızlandırmak için fast_info veya history(1d)
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1mo")
        current = history['Close'].iloc[-1]
        prev = history['Close'].iloc[-2]
        change = ((current - prev) / prev) * 100
        return current, change, history
    except:
        return 0.0, 0.0, pd.DataFrame()

def calculate_portfolio(df_p):
    if df_p.empty: return df_p, 0, 0
    
    # Gerçek zamanlı fiyat çekimi (Simüle edilmiş toplu işlem)
    # Not: Gerçekte burası her sembol için api çağrısı yapar.
    df_p['Current_Price'] = df_p['Sym'].apply(lambda x: get_price_data(x)[0])
    df_p['Total_Value'] = df_p['Current_Price'] * df_p['Qty']
    df_p['PL'] = df_p['Total_Value'] - (df_p['Cost'] * df_p['Qty'])
    df_p['PL_Perc'] = (df_p['PL'] / (df_p['Cost'] * df_p['Qty'])) * 100
    df_p['PL_Perc'] = df_p['PL_Perc'].fillna(0)
    
    return df_p, df_p['Total_Value'].sum(), df_p['PL'].sum()

# ==========================================
# 4. UYGULAMA MANTIĞI
# ==========================================

# Oturum Kontrolü
if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN EKRANI ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 0.8, 1])
    with c2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="text-align:center; margin-bottom:30px;">
                <h1 style="font-size:50px; margin:0;">AUTO<span style="color:#2962FF">FLOW</span></h1>
                <p style="color:#666; font-size:14px; letter-spacing:2px;">INTELLIGENT ASSET OS</p>
            </div>
            """, unsafe_allow_html=True
        )
        
        tab_login, tab_reg = st.tabs(["GİRİŞ YAP", "KAYIT OL"])
        
        with tab_login:
            u = st.text_input("Kullanıcı Adı", key="l_u")
            p = st.text_input("Şifre", type="password", key="l_p")
            if st.button("SİSTEME BAĞLAN", use_container_width=True, type="primary"):
                udf = pd.read_csv(FILES["users"])
                ph = hashlib.sha256(p.encode()).hexdigest()
                user = udf[(udf['User'] == u) & (udf['Pass'] == ph)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.auth = True
                        st.session_state.user = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("⚠️ Hesabınız yönetici onayı bekliyor.")
                else: st.error("❌ Hatalı bilgiler.")

        with tab_reg:
            nu = st.text_input("Kullanıcı Adı Seç", key="r_u")
            nn = st.text_input("Ad Soyad", key="r_n")
            npw = st.text_input("Şifre Belirle", type="password", key="r_p")
            if st.button("KAYIT TALEBİ GÖNDER", use_container_width=True):
                udf = pd.read_csv(FILES["users"])
                if nu in udf['User'].values:
                    st.error("Bu kullanıcı adı dolu.")
                elif len(nu) < 3:
                    st.error("Kullanıcı adı çok kısa.")
                else:
                    new = pd.DataFrame([[nu, hashlib.sha256(npw.encode()).hexdigest(), nn, "Pending", "User"]], columns=udf.columns)
                    pd.concat([udf, new]).to_csv(FILES["users"], index=False)
                    st.success("✅ Talep alındı. Admin onayı bekleniyor.")

else:
    # --- ANA TERMİNAL ARAYÜZÜ ---
    
    # 1. Sidebar (Sol Menü)
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:#161618; margin-bottom:20px; border:1px solid #222;">
            <div style="font-size:10px; color:#666; font-weight:700; letter-spacing:1px;">OPERATÖR</div>
            <div style="font-size:18px; font-weight:700; color:white;">{st.session_state.user['Name']}</div>
            <div style="font-size:11px; color:#2962FF;">● {st.session_state.user['Role']} Access</div>
        </div>
        """, unsafe_allow_html=True)
        
        menu = st.radio("NAVİGASYON", 
            ["📊 KONTROL PANELİ", "🧠 AI STRATEJİST", "🌍 PİYASA RADARI", "💼 PORTFÖY", "🔐 YÖNETİM"],
            label_visibility="collapsed"
        )
        
        # Özel Buton Tasarımı için radio yerine markdown kullanabilirdik ama işlevsellik için radio daha iyi.
        # CSS ile radio butonları zaten özelleştirildi.
        
        st.markdown("---")
        if st.button("ÇIKIŞ YAP", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

    # Verileri Yükle
    df_assets = pd.read_csv(FILES["port"])
    my_assets = df_assets[df_assets['Owner'] == st.session_state.user['User']].copy()
    
    # --- SAYFA 1: KONTROL PANELİ (DASHBOARD) ---
    if menu == "📊 KONTROL PANELİ":
        st.markdown("## Varlık Genel Bakış")
        
        if not my_assets.empty:
            with st.spinner("Piyasa verileri işleniyor..."):
                my_assets, total_val, total_pl = calculate_portfolio(my_assets)
                pl_perc = (total_pl / (total_val - total_pl) * 100) if (total_val - total_pl) != 0 else 0

            # METRİK KARTLARI
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="card-label">TOPLAM VARLIK</div>
                    <div class="card-value">₺{total_val:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                color_class = "trend-up" if total_pl >= 0 else "trend-down"
                sign = "+" if total_pl >= 0 else ""
                st.markdown(f"""
                <div class="metric-card">
                    <div class="card-label">NET K/Z</div>
                    <div class="card-value" style="color:{'#00C853' if total_pl>=0 else '#FF3D00'}">{sign}₺{total_pl:,.2f}</div>
                    <div class="{color_class}">%{pl_perc:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="card-label">EN İYİ PERFORMANS</div>
                    <div class="card-value" style="font-size:20px;">{my_assets.loc[my_assets['PL'].idxmax()]['Sym']}</div>
                    <div class="trend-up">+₺{my_assets['PL'].max():,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="card-label">POZİSYON ADEDİ</div>
                    <div class="card-value">{len(my_assets)}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # GRAFİKLER
            g1, g2 = st.columns([2, 1])
            with g1:
                st.markdown("### 📈 Varlık Performans Isı Haritası")
                fig = px.treemap(my_assets, path=['Type', 'Sym'], values='Total_Value',
                                 color='PL_Perc', color_continuous_scale=['#FF3D00', '#111', '#00C853'],
                                 range_color=[-10, 10])
                fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
                
            with g2:
                st.markdown("### 🥧 Dağılım")
                fig2 = px.pie(my_assets, values='Total_Value', names='Type', hole=0.7, color_discrete_sequence=px.colors.sequential.Plasma)
                fig2.update_layout(margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
                fig2.add_annotation(text=f"₺{total_val/1000:.0f}K", font=dict(size=20, color="white"), showarrow=False)
                st.plotly_chart(fig2, use_container_width=True)

        else:
            st.info("Portföyünüz boş. 'Portföy' sekmesinden varlık ekleyin.")

    # --- SAYFA 2: AI STRATEJİST ---
    elif menu == "🧠 AI STRATEJİST":
        st.markdown("## AutoFlow Intelligence")
        
        c_ai_1, c_ai_2 = st.columns([2, 1])
        
        with c_ai_1:
            if not my_assets.empty:
                # Basit bir kural tabanlı AI simülasyonu
                st.markdown('<div class="ai-box">🤖 <b>Sistem Analizi:</b> Portföy verileriniz işleniyor...</div>', unsafe_allow_html=True)
                
                # Risk Analizi
                total_v = (my_assets['Qty'] * my_assets['Cost']).sum() # Cost value approximate
                if total_v > 0:
                    crypto_ratio = my_assets[my_assets['Type']=='Kripto']['Cost'].sum() * my_assets[my_assets['Type']=='Kripto']['Qty'].sum() / total_v
                    if crypto_ratio > 0.5:
                        st.markdown("""
                        <div class="ai-box" style="border-left-color: #FF3D00;">
                        ⚠️ <b>Yüksek Volatilite Uyarısı:</b> Portföyünüzün %50'sinden fazlası kripto varlıklarda. 
                        Bu durum piyasa düşüşlerinde yüksek risk oluşturur. Altın veya Fon gibi defansif varlıklarla hedge etmeniz önerilir.
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="ai-box" style="border-left-color: #00C853;">
                        ✅ <b>Dengeli Dağılım:</b> Varlık sınıfları arasındaki dağılımınız makul seviyede.
                        </div>""", unsafe_allow_html=True)

                # Kar Alımı Önerisi
                profit_assets = my_assets[my_assets['PL_Perc'] > 20]
                if not profit_assets.empty:
                     st.markdown(f"""
                        <div class="ai-box" style="border-left-color: #2962FF;">
                        💎 <b>Kar Realizasyonu Fırsatı:</b> {', '.join(profit_assets['Sym'].tolist())} varlıklarında %20 üzeri getiri mevcut. 
                        Kademeli satış stratejisi uygulanabilir.
                        </div>""", unsafe_allow_html=True)
            else:
                st.warning("Analiz için veri yok.")

        with c_ai_2:
            st.markdown("### 📰 Akıllı Haber Akışı")
            news = [
                {"title": "FED Faiz Kararı Bekleniyor", "time": "10 dk önce", "src": "Bloomberg"},
                {"title": "Bitcoin 95k Direncini Kırdı", "time": "32 dk önce", "src": "CoinDesk"},
                {"title": "BIST100 Rekor Tazeledi", "time": "1 saat önce", "src": "Reuters"},
                {"title": "Petrol Fiyatlarında Düşüş", "time": "2 saat önce", "src": "ForexLive"},
            ]
            for n in news:
                st.markdown(f"""
                <div style="border-bottom:1px solid #222; padding:10px 0;">
                    <div style="color:#2962FF; font-size:10px; font-weight:700;">{n['src']} • {n['time']}</div>
                    <div style="color:#DDD; font-size:14px;">{n['title']}</div>
                </div>
                """, unsafe_allow_html=True)

    # --- SAYFA 3: PİYASA RADARI (TRADINGVIEW STYLE) ---
    elif menu == "🌍 PİYASA RADARI":
        # Header Bölümü
        col_search, col_info = st.columns([1, 3])
        with col_search:
            symbol = st.text_input("Sembol Arama", value="BTC-USD", placeholder="Örn: AAPL").upper()
        
        # Veri Çekme
        price, change_pct, hist = get_price_data(symbol)
        
        with col_info:
            if not hist.empty:
                color = "#00C853" if change_pct >= 0 else "#FF3D00"
                arrow = "▲" if change_pct >= 0 else "▼"
                st.markdown(f"""
                <div style="display:flex; align-items:baseline; gap:15px; padding-top:20px;">
                    <span style="font-size:32px; font-weight:700; color:white;">{symbol}</span>
                    <span style="font-size:32px; font-weight:400; color:white;">${price:,.2f}</span>
                    <span style="font-size:18px; font-weight:600; color:{color};">{arrow} %{abs(change_pct):.2f}</span>
                </div>
                """, unsafe_allow_html=True)

        if not hist.empty:
            # Candlestick Grafik
            fig = go.Figure(data=[go.Candlestick(x=hist.index,
                            open=hist['Open'], high=hist['High'],
                            low=hist['Low'], close=hist['Close'],
                            increasing_line_color='#00C853', decreasing_line_color='#FF3D00')])

            fig.update_layout(
                xaxis_rangeslider_visible=False,
                paper_bgcolor='rgba(0,0,0,0)', # Şeffaf
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#888"),
                grid=dict(color="#222"),
                height=500,
                margin=dict(l=0,r=0,t=20,b=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#222")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Alt Butonlar (Zaman Dilimi Simülasyonu)
            bt1, bt2, bt3, bt4, bt5 = st.columns(5)
            bt1.button("1G", use_container_width=True)
            bt2.button("1H", use_container_width=True)
            bt3.button("1A", use_container_width=True)
            bt4.button("1Y", use_container_width=True)
            bt5.button("TÜMÜ", use_container_width=True)
            
        else:
            st.error("Sembol bulunamadı. Lütfen kontrol edin (Örn: BTC-USD, AAPL, THYAO.IS)")

    # --- SAYFA 4: PORTFÖY YÖNETİMİ ---
    elif menu == "💼 PORTFÖY":
        st.markdown("## Varlık Yönetim Merkezi")
        
        with st.expander("➕ YENİ POZİSYON GİRİŞİ", expanded=False):
            with st.form("new_asset"):
                c1, c2, c3, c4 = st.columns(4)
                f_sym = c1.text_input("Sembol").upper()
                f_type = c2.selectbox("Tür", ["Hisse", "Kripto", "Emtia", "Döviz", "Fon"])
                f_qty = c3.number_input("Adet", min_value=0.0, step=0.01)
                f_cost = c4.number_input("Birim Maliyet", min_value=0.0, step=0.01)
                
                if st.form_submit_button("ONAYLA VE EKLE", type="primary"):
                    new_entry = pd.DataFrame([[st.session_state.user['User'], f_sym, f_type, f_qty, f_cost, datetime.now().date()]], 
                                             columns=df_assets.columns)
                    pd.concat([df_assets, new_entry]).to_csv(FILES["port"], index=False)
                    st.success("✅ Varlık portföye eklendi.")
                    time.sleep(1)
                    st.rerun()

        if not my_assets.empty:
            my_assets, _, _ = calculate_portfolio(my_assets)
            
            st.markdown("### Mevcut Envanter")
            # Dataframe'i düzenlenebilir yap
            edited_df = st.data_editor(
                my_assets[['Sym', 'Type', 'Qty', 'Cost', 'Current_Price', 'PL', 'PL_Perc']],
                column_config={
                    "PL_Perc": st.column_config.ProgressColumn("K/Z %", format="%.2f%%", min_value=-50, max_value=50),
                    "Current_Price": st.column_config.NumberColumn("Fiyat", format="₺%.2f"),
                    "PL": st.column_config.NumberColumn("Net K/Z", format="₺%.2f")
                },
                use_container_width=True,
                disabled=["Current_Price", "PL", "PL_Perc"] # Sadece miktar ve maliyet düzenlenebilsin
            )
            
            c_d1, c_d2 = st.columns(2)
            c_d1.download_button("📥 Excel Raporu İndir", my_assets.to_csv(index=False), "autoflow_report.csv", "text/csv")
        else:
            st.info("Henüz varlık eklenmedi.")

    # --- SAYFA 5: YÖNETİM ---
    elif menu == "🔐 YÖNETİM":
        if st.session_state.user['Role'] == "Admin":
            st.markdown("## Admin Paneli")
            
            udf = pd.read_csv(FILES["users"])
            
            t1, t2 = st.tabs(["ONAY BEKLEYENLER", "TÜM KULLANICILAR"])
            
            with t1:
                pending = udf[udf['Status'] == "Pending"]
                if not pending.empty:
                    for idx, row in pending.iterrows():
                        with st.container():
                            col_info, col_act = st.columns([3, 1])
                            col_info.info(f"**{row['Name']}** ({row['User']})")
                            if col_act.button("ONAYLA", key=f"app_{idx}"):
                                udf.at[idx, 'Status'] = "Approved"
                                udf.to_csv(FILES["users"], index=False)
                                st.rerun()
                else:
                    st.success("Bekleyen talep yok.")
            
            with t2:
                st.dataframe(udf, use_container_width=True)
        else:
            st.error("⛔ Yetkisiz Giriş. Bu alan sadece yöneticiler içindir.")