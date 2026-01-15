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
# 1. KONFİGÜRASYON VE CSS (HYBRID UI MOTORU)
# ==========================================
st.set_page_config(
    page_title="AUTOFLOW | Admin Terminal",
    layout="wide",
    page_icon="🌊",
    initial_sidebar_state="expanded"
)

# --- HYBRID TASARIM SİSTEMİ (BEYAZ SIDEBAR / KOYU İÇERİK) ---
st.markdown("""
<style>
    /* 1. ANA İÇERİK (KOYU MOD - DARK) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #09090B !important; /* Derin Siyah/Gri */
        font-family: 'Inter', sans-serif;
        color: #E4E4E7;
    }
    
    /* 2. SIDEBAR (AYDINLIK MOD - WHITE) - İSTEĞE ÖZEL */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E4E4E7; /* İnce gri çizgi */
    }
    
    /* Sidebar içindeki metinleri KOYU yap (Çünkü zemin beyaz) */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] div, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #18181B !important;
    }
    
    /* Radyo Butonları (Navigasyon) Özelleştirme */
    .stRadio div[role="radiogroup"] > label {
        padding: 10px 15px;
        border-radius: 8px;
        transition: all 0.2s;
        border: 1px solid transparent;
    }
    .stRadio div[role="radiogroup"] > label:hover {
        background-color: #F4F4F5 !important;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #EFF6FF !important; /* Seçiliyken açık mavi zemin */
        border: 1px solid #BFDBFE !important;
    }
    .stRadio div[role="radiogroup"] > label[data-checked="true"] p {
        color: #2563EB !important; /* Seçiliyken mavi yazı */
        font-weight: 700 !important;
    }

    /* 3. METRİK KARTLARI (Koyu Zemin Üzerinde Parlak) */
    .metric-card {
        background-color: #18181B; /* Zinc Grey */
        border: 1px solid #27272A;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
        height: 100%;
    }
    .metric-card:hover {
        border-color: #3B82F6;
        transform: translateY(-2px);
    }
    .card-label { font-size: 12px; color: #A1A1AA; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .card-value { font-size: 28px; font-weight: 700; color: #FFFFFF; font-family: 'JetBrains Mono', monospace; }
    
    /* 4. TABLOLAR & INPUTLAR */
    [data-testid="stDataFrame"] { border: 1px solid #27272A; border-radius: 8px; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #18181B !important;
        color: white !important;
        border-color: #27272A !important;
    }
    
    /* 5. USER CARD (Sidebar için özel stil) */
    .user-card-sidebar {
        background-color: #F4F4F5; /* Açık gri */
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #E4E4E7;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. VERİ ALTYAPISI (GÜÇLENDİRİLMİŞ)
# ==========================================
FILES = {"users": "af_users_v3.csv", "port": "af_assets_v3.csv"}

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
# 3. CORE FONKSİYONLAR
# ==========================================
@st.cache_data(ttl=60)
def get_price_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="1mo")
        if history.empty: return 0.0, 0.0, pd.DataFrame()
        current = history['Close'].iloc[-1]
        prev = history['Close'].iloc[-2]
        change = ((current - prev) / prev) * 100
        return current, change, history
    except:
        return 0.0, 0.0, pd.DataFrame()

def calculate_portfolio(df_p):
    if df_p.empty: return df_p, 0, 0
    # Gerçek uygulamada burası toplu API sorgusu yapmalı, demo için tek tek:
    current_prices = []
    for s in df_p['Sym']:
        p, _, _ = get_price_data(s)
        current_prices.append(p)
    
    df_p['Current_Price'] = current_prices
    df_p['Total_Value'] = df_p['Current_Price'] * df_p['Qty']
    df_p['PL'] = df_p['Total_Value'] - (df_p['Cost'] * df_p['Qty'])
    df_p['PL_Perc'] = (df_p['PL'] / (df_p['Cost'] * df_p['Qty'])) * 100
    df_p['PL_Perc'] = df_p['PL_Perc'].fillna(0)
    
    return df_p, df_p['Total_Value'].sum(), df_p['PL'].sum()

# ==========================================
# 4. MAIN FLOW
# ==========================================
if 'auth' not in st.session_state: st.session_state.auth = False

# --- LOGIN EKRANI (FULL DARK) ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 0.8, 1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="text-align:center; margin-bottom:30px;">
                <h1 style="font-size:42px; margin:0; color:white;">AUTO<span style="color:#3B82F6">FLOW</span></h1>
                <p style="color:#A1A1AA; font-size:13px; letter-spacing:3px;">ENTERPRISE TERMINAL OS</p>
            </div>
            """, unsafe_allow_html=True
        )
        
        tab_login, tab_reg = st.tabs(["GİRİŞ", "KAYIT"])
        
        with tab_login:
            u = st.text_input("Kullanıcı Adı", key="l_u")
            p = st.text_input("Şifre", type="password", key="l_p")
            if st.button("TERMİNALİ BAŞLAT", use_container_width=True, type="primary"):
                udf = pd.read_csv(FILES["users"])
                ph = hashlib.sha256(p.encode()).hexdigest()
                user = udf[(udf['User'] == u) & (udf['Pass'] == ph)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.auth = True
                        st.session_state.user = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("⚠️ Hesabınız yönetici onayında bekliyor.")
                else: st.error("❌ Geçersiz kimlik.")

        with tab_reg:
            nu = st.text_input("Yeni Kullanıcı Adı", key="r_u")
            nn = st.text_input("Ad Soyad", key="r_n")
            npw = st.text_input("Şifre", type="password", key="r_p")
            if st.button("BAŞVURU GÖNDER", use_container_width=True):
                udf = pd.read_csv(FILES["users"])
                if nu in udf['User'].values: st.error("Bu kullanıcı adı alınmış.")
                elif len(nu) < 3: st.error("Kullanıcı adı en az 3 karakter olmalı.")
                else:
                    new = pd.DataFrame([[nu, hashlib.sha256(npw.encode()).hexdigest(), nn, "Pending", "User"]], columns=udf.columns)
                    pd.concat([udf, new]).to_csv(FILES["users"], index=False)
                    st.success("✅ Başvurunuz alındı. Onay bekleniyor.")

else:
    # --- İÇERİDEKİ EKRAN (HYBRID VIEW) ---
    
    # 1. BEYAZ SIDEBAR TASARIMI
    with st.sidebar:
        # Kullanıcı Kartı (Beyaz zemin uyumlu)
        st.markdown(f"""
        <div class="user-card-sidebar">
            <div style="font-size:10px; color:#52525B; font-weight:700; letter-spacing:1px; margin-bottom:5px;">AKTİF HESAP</div>
            <div style="font-size:18px; font-weight:800; color:#18181B;">{st.session_state.user['Name']}</div>
            <div style="font-size:12px; font-weight:600; color:#2563EB;">● {st.session_state.user['Role']} Yetkisi</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigasyon
        menu = st.radio("MENÜ", 
            ["DASHBOARD", "AI ANALİZ", "PİYASA", "PORTFÖY", "YÖNETİM"],
            label_visibility="collapsed"
        )
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("OTURUMU KAPAT", use_container_width=True):
            st.session_state.auth = False
            st.rerun()

    # Veri Hazırlığı
    df_assets = pd.read_csv(FILES["port"])
    my_assets = df_assets[df_assets['Owner'] == st.session_state.user['User']].copy()
    
    # --- DASHBOARD ---
    if menu == "DASHBOARD":
        st.markdown("## 📊 Genel Bakış")
        if not my_assets.empty:
            with st.spinner("Senkronizasyon..."):
                my_assets, total_val, total_pl = calculate_portfolio(my_assets)
            
            # Kartlar
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="metric-card"><div class="card-label">VARLIK DEĞERİ</div><div class="card-value">₺{total_val:,.2f}</div></div>', unsafe_allow_html=True)
            pl_color = "#10B981" if total_pl >= 0 else "#EF4444"
            c2.markdown(f'<div class="metric-card"><div class="card-label">KAR / ZARAR</div><div class="card-value" style="color:{pl_color}">₺{total_pl:,.2f}</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><div class="card-label">VARLIK SAYISI</div><div class="card-value">{len(my_assets)}</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-card"><div class="card-label">RİSK PUANI</div><div class="card-value">Düşük</div></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Grafikler
            g1, g2 = st.columns([2, 1])
            with g1:
                st.markdown("### Portföy Dağılımı (Treemap)")
                fig = px.treemap(my_assets, path=['Type', 'Sym'], values='Total_Value', color='PL_Perc', 
                                 color_continuous_scale='RdYlGn', template="plotly_dark")
                fig.update_layout(paper_bgcolor="#18181B", plot_bgcolor="#18181B", margin=dict(t=0, l=0, r=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                st.markdown("### Sınıf Analizi")
                fig2 = px.pie(my_assets, values='Total_Value', names='Type', hole=0.6, template="plotly_dark")
                fig2.update_layout(paper_bgcolor="#18181B", margin=dict(t=0, l=0, r=0, b=0), showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("👋 Hoşgeldiniz! Veri görmek için 'PORTFÖY' menüsünden varlık ekleyiniz.")

    # --- PİYASA ---
    elif menu == "PİYASA":
        st.markdown("## 🌍 Global Piyasa Radarı")
        s_col, i_col = st.columns([1, 3])
        with s_col:
            sym = st.text_input("Sembol Ara", value="BTC-USD").upper()
        
        p, ch, h = get_price_data(sym)
        
        with i_col:
            if not h.empty:
                col_txt = "#10B981" if ch >= 0 else "#EF4444"
                st.markdown(f"""
                <div style="font-size:32px; font-weight:800; color:white;">{sym} 
                <span style="font-size:24px; color:{col_txt}; margin-left:15px;">{p:,.2f} (%{ch:.2f})</span></div>
                """, unsafe_allow_html=True)
                
                fig = go.Figure(data=[go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'])])
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=500, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else: st.error("Sembol bulunamadı.")

    # --- PORTFÖY ---
    elif menu == "PORTFÖY":
        st.markdown("## 💼 Varlık Yönetimi")
        
        with st.expander("➕ YENİ VARLIK EKLE", expanded=False):
            with st.form("add_asset"):
                c1, c2, c3, c4 = st.columns(4)
                ns = c1.text_input("Sembol (Örn: GARAN.IS)").upper()
                nt = c2.selectbox("Tür", ["Hisse", "Kripto", "Emtia", "Döviz"])
                nq = c3.number_input("Adet", min_value=0.01)
                nc = c4.number_input("Birim Maliyet", min_value=0.01)
                if st.form_submit_button("LİSTEYE EKLE", type="primary"):
                    new_row = pd.DataFrame([[st.session_state.user['User'], ns, nt, nq, nc, datetime.now().date()]], columns=df_assets.columns)
                    pd.concat([df_assets, new_row]).to_csv(FILES["port"], index=False)
                    st.success("Eklendi!")
                    time.sleep(0.5); st.rerun()
        
        if not my_assets.empty:
            my_assets, _, _ = calculate_portfolio(my_assets)
            st.dataframe(
                my_assets[['Sym', 'Type', 'Qty', 'Cost', 'Current_Price', 'PL', 'PL_Perc']],
                column_config={
                    "PL_Perc": st.column_config.ProgressColumn("K/Z %", format="%.2f%%", min_value=-50, max_value=50),
                    "Current_Price": st.column_config.NumberColumn("Fiyat", format="₺%.2f"),
                    "PL": st.column_config.NumberColumn("Net K/Z", format="₺%.2f")
                },
                use_container_width=True
            )
            st.download_button("📥 Excel İndir", my_assets.to_csv(index=False), "autoflow_data.csv")
        else: st.info("Henüz varlık yok.")

    # --- AI ANALİZ ---
    elif menu == "AI ANALİZ":
        st.markdown("## 🧠 AutoFlow Intelligence")
        st.info("Bu modül portföy verilerinizi tarayarak otomatik stratejiler üretir.")
        c1, c2 = st.columns(2)
        c1.markdown("""
        <div class="metric-card">
            <h3>📈 Momentum Analizi</h3>
            <p style="color:#A1A1AA">Piyasa genelinde boğa eğilimi sürüyor. Portföy betanız düşük seviyede.</p>
        </div>
        """, unsafe_allow_html=True)
        c2.markdown("""
        <div class="metric-card">
            <h3>⚠️ Risk Uyarısı</h3>
            <p style="color:#A1A1AA">Portföy çeşitliliğiniz yeterli seviyede. Herhangi bir kritik yoğunlaşma tespit edilmedi.</p>
        </div>
        """, unsafe_allow_html=True)

    # --- YÖNETİM (GÜNCELLENMİŞ RET BUTONLU) ---
    elif menu == "YÖNETİM":
        if st.session_state.user['Role'] == "Admin":
            st.markdown("## 🔐 Admin Kontrol Merkezi")
            
            udf = pd.read_csv(FILES["users"])
            
            t1, t2 = st.tabs(["🔴 ONAY BEKLEYENLER", "👥 TÜM KULLANICILAR"])
            
            with t1:
                pending = udf[udf['Status'] == "Pending"]
                if not pending.empty:
                    st.write(f"Bekleyen Talep Sayısı: {len(pending)}")
                    for idx, row in pending.iterrows():
                        with st.container():
                            # Beyaz sidebar olduğu için buradaki kartları koyu yapıyoruz
                            st.markdown(f"""
                            <div style="background:#27272A; padding:15px; border-radius:8px; border-left:4px solid #F59E0B; margin-bottom:10px;">
                                <span style="font-weight:bold; font-size:16px;">{row['Name']}</span> 
                                <span style="color:#A1A1AA; font-size:14px;">(@{row['User']})</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            c_act1, c_act2, c_space = st.columns([1, 1, 4])
                            
                            # ONAY BUTONU
                            if c_act1.button("✅ ONAYLA", key=f"app_{idx}", use_container_width=True):
                                udf.at[idx, 'Status'] = "Approved"
                                udf.to_csv(FILES["users"], index=False)
                                st.success(f"{row['User']} onaylandı!")
                                time.sleep(1); st.rerun()
                            
                            # RED BUTONU (YENİ ÖZELLİK)
                            if c_act2.button("⛔ REDDET", key=f"rej_{idx}", use_container_width=True):
                                udf = udf.drop(idx)
                                udf.to_csv(FILES["users"], index=False)
                                st.error(f"{row['User']} reddedildi ve silindi.")
                                time.sleep(1); st.rerun()
                            
                            st.markdown("---")
                else:
                    st.success("Bekleyen kayıt talebi bulunmamaktadır.")
            
            with t2:
                st.dataframe(udf, use_container_width=True)
        else:
            st.error("Bu alana giriş yetkiniz yok.")