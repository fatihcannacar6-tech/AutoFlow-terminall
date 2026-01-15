import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. GLOBAL CORE CONFIG ---
st.set_page_config(page_title="AUTOFLOW | Strategic Terminal", layout="wide", page_icon="🌊")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&family=Inter:wght@400;600;800&display=swap');
    
    /* Global Typography */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0A0E14; color: #E2E8F0; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: #FFFFFF; }
    
    /* UI Element Styling */
    .stApp { background-color: #0A0E14; }
    [data-testid="stSidebar"] { background-color: #0F172A !important; border-right: 1px solid #1E293B; }
    
    /* Custom Cards */
    .flow-card {
        background: rgba(30, 41, 59, 0.5); border: 1px solid #334155; 
        padding: 24px; border-radius: 16px; backdrop-filter: blur(10px);
    }
    .ai-bubble {
        background: linear-gradient(90deg, #3B82F6 0%, #2DD4BF 100%);
        padding: 20px; border-radius: 12px; color: white; font-weight: 600; margin: 15px 0;
    }
    
    /* Performance Badges */
    .badge-profit { background: #064E3B; color: #34D399; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
    .badge-loss { background: #7F1D1D; color: #F87171; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INFRASTRUCTURE ---
DB = {"U": "af_users.csv", "P": "af_assets.csv"}

def secure_init():
    if not os.path.exists(DB["U"]):
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_hash, "System Director", "Approved", "Admin"]], 
                     columns=["User", "Pass", "Name", "Status", "Role"]).to_csv(DB["U"], index=False)
    if not os.path.exists(DB["P"]):
        pd.DataFrame(columns=["Owner", "Sym", "Type", "Qty", "Cost", "TS"]).to_csv(DB["P"], index=False)

secure_init()

# --- 3. AUTHENTICATION (FIXED & SECURE) ---
if 'flow_auth' not in st.session_state: st.session_state.flow_auth = False

if not st.session_state.flow_auth:
    _, center_col, _ = st.columns([1, 1, 1])
    with center_col:
        st.markdown("<h1 style='text-align:center; font-size:48px;'>AUTO<span style='color:#3B82F6'>FLOW</span></h1>", unsafe_allow_html=True)
        mode = st.tabs(["🔐 SİSTEME GİRİŞ", "🛰️ KAYIT TALEBİ"])
        
        with mode[0]:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("TERMİNALİ AKTİF ET", use_container_width=True):
                udf = pd.read_csv(DB["U"])
                phash = hashlib.sha256(p.encode()).hexdigest()
                user_match = udf[(udf['User'] == u) & (udf['Pass'] == phash)]
                if not user_match.empty:
                    if user_match.iloc[0]['Status'] == "Approved":
                        st.session_state.flow_auth = True
                        st.session_state.udata = user_match.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Erişim yetkiniz henüz onaylanmadı.")
                else: st.error("Kimlik doğrulanamadı.")
        
        with mode[1]:
            nu, nn, npw = st.text_input("Kimlik Seçin"), st.text_input("Tam Adınız"), st.text_input("Şifreniz", type="password")
            if st.button("MERKEZE GÖNDER", use_container_width=True):
                udf = pd.read_csv(DB["U"])
                if nu in udf['User'].values: st.error("Bu kimlik zaten kullanımda.")
                else:
                    new_req = pd.DataFrame([[nu, hashlib.sha256(npw.encode()).hexdigest(), nn, "Pending", "User"]], columns=udf.columns)
                    pd.concat([udf, new_req]).to_csv(DB["U"], index=False)
                    st.success("Talebiniz iletildi. Onay bekleyin.")

else:
    # --- 4. MASTER INTERFACE ---
    with st.sidebar:
        st.markdown(f"""<div style='background:#1E293B; padding:20px; border-radius:12px;'>
            <div style='font-size:11px; color:#94A3B8; font-weight:700;'>OPERASYON ŞEFİ</div>
            <div style='font-size:18px; font-weight:700;'>{st.session_state.udata['Name']}</div>
        </div>""", unsafe_allow_html=True)
        
        nav = st.radio("NAVİGASYON", ["📊 KONTROL PANELİ", "🧠 AUTOFLOW AI", "🌐 PİYASA RADARI", "💼 VARLIK YÖNETİMİ", "🔐 SİSTEM YÖNETİMİ" if st.session_state.udata['Role'] == "Admin" else None])
        
        st.divider()
        if st.button("TERMİNALİ KAPAT"): st.session_state.flow_auth = False; st.rerun()

    # Veri Yükleme
    pdf = pd.read_csv(DB["P"])
    my_assets = pdf[pdf['Owner'] == st.session_state.udata['User']].copy()

    # --- 5. KONTROL PANELİ (DASHBOARD) ---
    if nav == "📊 KONTROL PANELİ":
        st.title("Strategic Dashboard")
        if not my_assets.empty:
            with st.spinner("Piyasa akışı senkronize ediliyor..."):
                my_assets['Price'] = [yf.Ticker(s).fast_info.last_price for s in my_assets['Sym']]
                my_assets['Value'] = my_assets['Price'] * my_assets['Qty']
                my_assets['PL'] = my_assets['Value'] - (my_assets['Cost'] * my_assets['Qty'])
            
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="flow-card"><small>TOPLAM VARLIK</small><h2>₺{my_assets["Value"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="flow-card"><small>NET KAR/ZARAR</small><h2 style="color:#10B981">₺{my_assets["PL"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="flow-card"><small>VERİMLİLİK</small><h2>%{ (my_assets["PL"].sum() / (my_assets["Cost"]*my_assets["Qty"]).sum() * 100):.2f}</h2></div>', unsafe_allow_html=True)

            st.divider()
            col_left, col_right = st.columns([2, 1])
            with col_left:
                st.subheader("Varlık Performans Akışı")
                st.plotly_chart(px.bar(my_assets, x='Sym', y='PL', color='PL', template="plotly_dark"), use_container_width=True)
            with col_right:
                st.subheader("Sınıf Dağılımı")
                st.plotly_chart(px.pie(my_assets, values='Value', names='Type', hole=0.6, template="plotly_dark"), use_container_width=True)
        else: st.info("Varlık bulunamadı. Lütfen ekleme yapın.")

    # --- 6. AUTOFLOW AI (MÜSTAKİL AI SEKMESİ) ---
    elif nav == "🧠 AUTOFLOW AI":
        st.title("AutoFlow AI Strategist")
        if not my_assets.empty:
            st.markdown('<div class="ai-bubble">Sistem Analizi: Varlık akışınız optimize ediliyor...</div>', unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("💡 Stratejik Tavsiyeler")
                st.info("● Portföyünüzdeki teknoloji ağırlığını dengelemek için emtia girişi yapılabilir.")
                st.success("● Mevcut kar realizasyonu için BIST30 endeks direnci takip edilmeli.")
                
            with col_b:
                st.subheader("⚖️ Risk Skorlaması")
                risk_val = (my_assets['Value'].max() / my_assets['Value'].sum()) * 100
                st.warning(f"Yoğunlaşma Riski: %{risk_val:.1f}")
                st.progress(risk_val / 100)
        else: st.warning("AI'nın analiz yapabilmesi için portföy verisi gerekli.")

    # --- 7. PİYASA RADARI (ÇEŞİTLENDİRİLMİŞ) ---
    elif nav == "🌐 PİYASA RADARI":
        st.title("Global Market Radar")
        tabs = st.tabs(["📈 TEKNİK ANALİZ", "🌍 DÜNYA BORSALARI", "💎 KRİPTO & EMTİA"])
        
        with tabs[0]:
            sym = st.text_input("Sembol (Örn: AAPL, BTC-USD, THYAO.IS)", "THYAO.IS").upper()
            data = yf.download(sym, period="3mo")
            fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'])])
            fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with tabs[1]:
            st.subheader("Küresel Endeksler")
            indices = ["^GSPC", "^IXIC", "^FTSE", "^GDAXI", "XU100.IS"]
            idx_data = pd.DataFrame([{"Endeks": i, "Son": yf.Ticker(i).fast_info.last_price} for i in indices])
            st.table(idx_data)

    # --- 8. VARLIK YÖNETİMİ & RAPOR ---
    elif nav == "💼 VARLIK YÖNETİMİ":
        st.title("Varlık & Raporlama Merkezi")
        
        with st.expander("➕ YENİ VARLIK EKLE"):
            with st.form("add_form"):
                c1, c2, c3, c4 = st.columns(4)
                f_s = c1.text_input("Sembol").upper()
                f_t = c2.selectbox("Tür", ["Hisse", "Kripto", "Emtia", "Döviz"])
                f_q = c3.number_input("Miktar", min_value=0.0)
                f_c = c4.number_input("Maliyet", min_value=0.0)
                if st.form_submit_button("SİSTEME İŞLE"):
                    new_row = pd.DataFrame([[st.session_state.udata['User'], f_s, f_t, f_q, f_c, datetime.now()]], columns=pdf.columns)
                    pd.concat([pdf, new_row]).to_csv(DB["P"], index=False)
                    st.rerun()

        st.subheader("Detaylı Envanter Raporu")
        st.dataframe(my_assets, use_container_width=True)
        st.download_button("📥 RAPORU CSV OLARAK İNDİR", my_assets.to_csv(index=False), "autoflow_report.csv")

    # --- 9. ADMIN ---
    elif nav == "🔐 SİSTEM YÖNETİMİ":
        st.title("Admin Control Panel")
        udf = pd.read_csv(DB["U"])
        st.subheader("Bekleyen Erişim Talepleri")
        pending = udf[udf['Status'] == "Pending"]
        for i, r in pending.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.write(f"Kullanıcı: **{r['Name']}**")
            if col2.button("ONAYLA", key=i):
                udf.at[i, 'Status'] = "Approved"
                udf.to_csv(DB["U"], index=False); st.rerun()
        st.divider()
        st.subheader("Tüm Kullanıcılar")
        st.dataframe(udf)