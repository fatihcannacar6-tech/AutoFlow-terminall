import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
from datetime import datetime
import streamlit.components.v1 as components
import plotly.express as px

# --- 1. ENTERPRISE UI CONFIGURATION ---
st.set_page_config(page_title="AKOSELL ENTERPRISE WMS", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
    
    /* Kurumsal Renk Paleti */
    [data-testid="stSidebar"] { background-color: #0F172A !important; }
    [data-testid="stHeader"] { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); }
    
    /* KPI Kartları */
    .kpi-container { display: flex; gap: 20px; margin-bottom: 25px; }
    .kpi-card { 
        background: white; padding: 20px; border-radius: 8px; border: 1px solid #E2E8F0; 
        flex: 1; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .kpi-title { color: #64748B; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .kpi-value { color: #0F172A; font-size: 24px; font-weight: 700; margin-top: 8px; }
    
    /* Durum Etiketleri */
    .status-tag { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .risk-low { background: #DCFCE7; color: #166534; }
    .risk-high { background: #FEE2E2; color: #991B1B; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. TRADINGVIEW COMPONENT ---
def tradingview_chart(symbol="BIST:XU100"):
    # TradingView Advanced Real-Time Chart Widget
    chart_code = f"""
    <div class="tradingview-widget-container" style="height:500px;width:100%;">
      <div id="tradingview_akosell"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{symbol}",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "light",
        "style": "1",
        "locale": "tr",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "hide_top_toolbar": false,
        "save_image": false,
        "container_id": "tradingview_akosell"
      }});
      </script>
    </div>
    """
    components.html(chart_code, height=500)

# --- 3. DATA PERSISTENCE & LOGGING ---
DB_PORT = "enterprise_portfolio.csv"
DB_LOG = "enterprise_audit.csv"

def init_db():
    if not os.path.exists(DB_PORT):
        pd.DataFrame(columns=["Owner", "Kod", "Varlik_Adi", "Adet", "Maliyet", "Sektor"]).to_csv(DB_PORT, index=False)
    if not os.path.exists(DB_LOG):
        pd.DataFrame(columns=["Timestamp", "User", "Action", "Detail"]).to_csv(DB_LOG, index=False)

def log_action(user, action, detail):
    df = pd.read_csv(DB_LOG)
    new_log = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, action, detail]], columns=df.columns)
    pd.concat([df, new_log]).to_csv(DB_LOG, index=False)

init_db()

# --- 4. AUTHENTICATION (SIMPLIFIED FOR MVP) ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, center_col, _ = st.columns([1, 0.8, 1])
    with center_col:
        st.markdown("<h2 style='text-align:center;'>AKOSELL <span style='font-weight:200'>ENTERPRISE</span></h2>", unsafe_allow_html=True)
        user = st.text_input("Kurumsal Kimlik")
        pw = st.text_input("Şifre", type="password")
        if st.button("SİSTEME GİRİŞ YAP", use_container_width=True):
            if user == "admin" and pw == "admin123":
                st.session_state.auth = True
                st.session_state.user = "Yönetici"
                log_action(user, "LOGIN", "Sisteme giriş yapıldı")
                st.rerun()
            else: st.error("Yetkisiz erişim.")
else:
    # --- 5. SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.markdown("<h3 style='color:white'>AKOSELL WMS</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94A3B8'>Kullanıcı: {st.session_state.user}</p>", unsafe_allow_html=True)
        st.divider()
        menu = st.radio("ANA MENÜ", ["🏛️ EXECUTIVE SUMMARY", "💼 PORTFÖY YÖNETİMİ", "📈 ANALİZ & CHART", "🕵️ AUDIT LOG"])
        if st.button("GÜVENLİ ÇIKIŞ"): st.session_state.auth = False; st.rerun()

    p_df = pd.read_csv(DB_PORT)

    # --- 6. EXECUTIVE SUMMARY ---
    if menu == "🏛️ EXECUTIVE SUMMARY":
        st.title("Executive Summary")
        
        # Üst KPI Kartları
        c1, c2, c3, c4 = st.columns(4)
        total_val = (p_df['Adet'] * p_df['Maliyet']).sum() # Basit hesap, canlı veri eklenebilir
        
        with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">Toplam Portföy</div><div class="kpi-value">₺{total_val:,.2f}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">YTD Getiri</div><div class="kpi-value" style="color:#10B981">+%18.4</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">Günlük Değişim</div><div class="kpi-value">₺4,210 <small style="font-size:12px; color:#10B981">▲ %1.2</small></div></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="kpi-card"><div class="kpi-title">Risk Skoru</div><div class="kpi-value"><span class="status-tag risk-low">MODERATE</span></div></div>', unsafe_allow_html=True)

        st.divider()
        
        col_chart, col_risk = st.columns([2, 1])
        with col_chart:
            st.subheader("Benchmark Karşılaştırması (Portföy vs BIST100)")
            # Simüle benchmark grafiği
            chart_data = pd.DataFrame({
                "Tarih": pd.date_range(start="2025-01-01", periods=10, freq="D"),
                "Portföy": [100, 102, 101, 105, 108, 107, 110, 112, 115, 118],
                "BIST100": [100, 101, 100, 103, 104, 103, 105, 106, 108, 110]
            })
            st.line_chart(chart_data.set_index("Tarih"))

        with col_risk:
            st.subheader("Sektörel Konsantrasyon")
            if not p_df.empty:
                fig = px.pie(p_df, values='Adet', names='Sektor', hole=0.7, color_discrete_sequence=px.colors.sequential.Blues_r)
                fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)

    # --- 7. PORTFÖY YÖNETİMİ ---
    elif menu == "💼 PORTFÖY YÖNETİMİ":
        st.title("Varlık Yönetimi")
        
        with st.expander("➕ Kurumsal Varlık Girişi"):
            with st.form("add_asset"):
                c1, c2, c3, c4 = st.columns(4)
                kod = c1.text_input("Sembol (Örn: THYAO)").upper()
                ad = c2.number_input("Adet", min_value=0.1)
                ml = c3.number_input("Birim Maliyet")
                sk = c4.selectbox("Sektör", ["Banka", "Ulaşım", "Enerji", "Teknoloji", "Gıda", "Kripto"])
                if st.form_submit_button("SİSTEME KAYDET"):
                    new_row = pd.DataFrame([["admin", kod, kod, ad, ml, sk]], columns=p_df.columns)
                    pd.concat([p_df, new_row]).to_csv(DB_PORT, index=False)
                    log_action("admin", "ADD_ASSET", f"{kod} eklendi")
                    st.rerun()

        st.subheader("Mevcut Pozisyonlar")
        # Kurumsal tablo görünümü
        st.data_editor(p_df, use_container_width=True, hide_index=True)

    # --- 8. ANALİZ & TRADINGVIEW ---
    elif menu == "📈 ANALİZ & CHART":
        st.title("Teknik Analiz Terminali")
        
        target = st.selectbox("Analiz Edilecek Varlık", p_df['Kod'].unique() if not p_df.empty else ["XU100"])
        
        # TradingView Entegrasyonu
        if target:
            # BIST hisseleri için TradingView formatı BIST:HİSSE şeklindedir
            tv_symbol = f"BIST:{target}" if target != "XU100" else "BIST:XU100"
            tradingview_chart(tv_symbol)
            
        st.divider()
        st.subheader("Temel Veri Özetleri")
        ca, cb, cc = st.columns(3)
        ca.metric("Analist Hedefi", "₺420.00", "+%12")
        cb.metric("F/K Oranı", "8.4", "-0.2")
        cc.metric("PD/DD", "1.1", "Stabil")

    # --- 9. AUDIT LOG ---
    elif menu == "🕵️ AUDIT LOG":
        st.title("Audit Log & İşlem Geçmişi")
        log_df = pd.read_csv(DB_LOG)
        st.table(log_df.sort_values(by="Timestamp", ascending=False))