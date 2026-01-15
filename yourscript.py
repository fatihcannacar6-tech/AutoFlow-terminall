import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import time
from fpdf import FPDF
import io

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="Autoflow Terminal | V7", layout="wide", page_icon="🌊")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* HYBRID UI: BEYAZ SIDEBAR / DARK CONTENT */
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    [data-testid="stAppViewContainer"] { background-color: #0F1115 !important; color: #F8FAFC !important; }
    
    .stRadio div[role="radiogroup"] label {
        background-color: #F8FAFC !important;
        border: 1px solid #F1F5F9 !important;
        border-radius: 10px !important;
        padding: 10px 15px !important;
        margin-bottom: 6px !important;
        font-weight: 600 !important;
        color: #475569 !important;
    }
    .stRadio div[role="radiogroup"] label[data-checked="true"] {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
    }
    .stRadio div[role="radiogroup"] label[data-checked="true"] p { color: white !important; }

    .metric-card {
        background: #1A1D23;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .dividend-box {
        background: #111827;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2D333D;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERİ TABANI ---
U_DB, P_DB = "autoflow_v7_users.csv", "autoflow_v7_portfolio.csv"

def init_db():
    if not os.path.exists(U_DB):
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Sistem Yönetici", "admin@autoflow.ai", "Approved", "Admin"]], 
                     columns=["User", "Pass", "Name", "Email", "Status", "Role"]).to_csv(U_DB, index=False)
    if not os.path.exists(P_DB):
        pd.DataFrame(columns=["Owner", "Symbol", "Type", "Cost", "Qty", "Date"]).to_csv(P_DB, index=False)

init_db()

# --- 3. PDF OLUŞTURMA FONKSİYONU ---
def create_pdf(df, user_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="AUTOFLOW STRATEJIK PORTFOY RAPORU", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Hazirlayan: {user_name} | Tarih: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Tablo Başlıkları
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Sembol", 1, 0, 'C', True)
    pdf.cell(40, 10, "Tür", 1, 0, 'C', True)
    pdf.cell(40, 10, "Adet", 1, 0, 'C', True)
    pdf.cell(40, 10, "Maliyet", 1, 1, 'C', True)
    
    # Veriler
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        pdf.cell(40, 10, str(row['Symbol']), 1)
        pdf.cell(40, 10, str(row['Type']), 1)
        pdf.cell(40, 10, f"{row['Qty']:.2f}", 1)
        pdf.cell(40, 10, f"{row['Cost']:.2f}", 1, 1)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. ANA DÖNGÜ VE AUTH ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    # Giriş Ekranı (Daha önce yaptığımız stabil yapı)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center; color:#3B82F6;'>AUTOFLOW</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["GİRİŞ", "KAYIT"])
        with tab_log:
            u = st.text_input("Kullanıcı")
            p = st.text_input("Şifre", type="password")
            if st.button("SİSTEME GİR", use_container_width=True):
                df = pd.read_csv(U_DB)
                hp = hashlib.sha256(p.encode()).hexdigest()
                user = df[(df['User'] == u) & (df['Pass'] == hp)]
                if not user.empty and user.iloc[0]['Status'] == "Approved":
                    st.session_state.auth = True
                    st.session_state.u_data = user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Hatalı giriş veya onaylanmamış hesap.")
        with tab_reg:
            nu, nn, ne, npw = st.text_input("K.Adı"), st.text_input("Ad Soyad"), st.text_input("Email"), st.text_input("Şifre", type="password")
            if st.button("KAYIT OL"):
                udf = pd.read_csv(U_DB)
                new_u = pd.DataFrame([[nu, hashlib.sha256(npw.encode()).hexdigest(), nn, ne, "Pending", "User"]], columns=udf.columns)
                pd.concat([udf, new_u]).to_csv(U_DB, index=False)
                st.success("Talep gönderildi.")

else:
    # --- TERMİNAL İÇİ ---
    with st.sidebar:
        st.markdown(f"### 🌊 Autoflow V7\n**{st.session_state.u_data['Name']}**")
        menu = st.radio("MENÜ", ["DASHBOARD", "PORTFÖY", "TEMETTÜ TAKVİMİ", "AI ANALİZ", "RAPORLAMA", "ADMİN"])
        if st.button("ÇIKIŞ"): 
            st.session_state.auth = False
            st.rerun()

    full_p = pd.read_csv(P_DB)
    my_p = full_p[full_p['Owner'] == st.session_state.u_data['User']].copy()

    # --- TEMETTÜ TAKVİMİ (YENİ ÖZELLİK) ---
    if menu == "TEMETTÜ TAKVİMİ":
        st.title("📅 Temettü Takvimi")
        st.markdown("Portföyünüzdeki varlıkların temettü geçmişi ve projeksiyonları.")
        
        if not my_p.empty:
            dividend_list = []
            with st.spinner("Temettü verileri toplanıyor..."):
                for sym in my_p['Symbol'].unique():
                    ticker_str = f"{sym}.IS" if my_p[my_p['Symbol']==sym]['Type'].iloc[0] == "Hisse" else None
                    if ticker_str:
                        t = yf.Ticker(ticker_str)
                        divs = t.dividends
                        if not divs.empty:
                            last_div = divs.tail(1)
                            dividend_list.append({
                                "Sembol": sym,
                                "Son Temettü": last_div.values[0],
                                "Tarih": last_div.index[0].strftime('%d/%m/%Y')
                            })
            
            if dividend_list:
                div_df = pd.DataFrame(dividend_list)
                st.table(div_df)
                
                # Temettü Verimi Grafiği (Mockup Projeksiyon)
                st.subheader("Yıllık Tahmini Temettü Verimi")
                fig = px.bar(div_df, x="Sembol", y="Son Temettü", color="Sembol", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Hisse senetleriniz için yakın zamanda bir temettü kaydı bulunamadı.")
        else:
            st.warning("Portföyünüzde henüz hisse senedi bulunmuyor.")

    # --- RAPORLAMA (YENİ ÖZELLİK) ---
    elif menu == "RAPORLAMA":
        st.title("📑 Profesyonel Raporlama")
        st.markdown("Mevcut portföy durumunuzu PDF veya Excel formatında dışa aktarın.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="metric-card"><h4>PDF Raporu</h4><p>Resmi formatta, onaylı portföy özeti.</p></div>', unsafe_allow_html=True)
            if not my_p.empty:
                pdf_data = create_pdf(my_p, st.session_state.u_data['Name'])
                st.download_button(label="📥 PDF İNDİR", data=pdf_data, file_name=f"Autoflow_Rapor_{datetime.now().date()}.pdf", mime="application/pdf")
        
        with c2:
            st.markdown('<div class="metric-card"><h4>Excel Verisi</h4><p>Ham verileri analiz etmek için dışa aktarın.</p></div>', unsafe_allow_html=True)
            if not my_p.empty:
                csv = my_p.to_csv(index=False).encode('utf-8')
                st.download_button(label="📥 EXCEL/CSV İNDİR", data=csv, file_name="autoflow_data.csv", mime="text/csv")

    # --- DASHBOARD (STANDART AMA GELİŞMİŞ) ---
    elif menu == "DASHBOARD":
        st.title("📊 Terminal Özeti")
        if not my_p.empty:
            # Hızlı Veri Çekimi
            prices = []
            for _, r in my_p.iterrows():
                try:
                    t_str = f"{r['Symbol']}.IS" if r['Type']=="Hisse" else f"{r['Symbol']}-USD"
                    prices.append(yf.Ticker(t_str).fast_info.last_price)
                except: prices.append(r['Cost'])
            
            my_p['Current'] = prices
            my_p['Total'] = my_p['Current'] * my_p['Qty']
            
            col1, col2, col3 = st.columns(3)
            col1.metric("TOPLAM VARLIK", f"₺{my_p['Total'].sum():,.2f}")
            col2.metric("POZİSYON SAYISI", len(my_p))
            col3.metric("PİYASA DURUMU", "AKTİF", delta="BIST100 %0.45")
            
            st.plotly_chart(px.pie(my_p, values='Total', names='Symbol', hole=0.4, template="plotly_dark"), use_container_width=True)
        else:
            st.info("Hoşgeldiniz! Başlamak için portföy ekleyin.")

    # --- PORTFÖY, AI VE ADMİN (ÖNCEKİ KODLARIN ENTEGRASYONU) ---
    elif menu == "PORTFÖY":
        st.title("💼 Varlık Yönetimi")
        with st.form("add"):
            c1, c2, c3, c4 = st.columns(4)
            s = c1.text_input("Sembol").upper()
            t = c2.selectbox("Tür", ["Hisse", "Kripto", "Döviz"])
            q = c3.number_input("Adet", min_value=0.0)
            c = c4.number_input("Maliyet", min_value=0.0)
            if st.form_submit_button("EKLE"):
                new = pd.DataFrame([[st.session_state.u_data['User'], s, t, c, q, datetime.now().date()]], columns=full_p.columns)
                pd.concat([full_p, new]).to_csv(P_DB, index=False)
                st.rerun()
        st.dataframe(my_p, use_container_width=True)

    elif menu == "AI ANALİZ":
        st.title("🧠 AI Strategist")
        st.info("Autoflow AI: Portföyünüzdeki çeşitlendirme oranı %85. Risk seviyesi: Düşük.")
        st.line_chart(np.random.randn(20, 1).cumsum())

    elif menu == "ADMİN":
        if st.session_state.u_data['Role'] == "Admin":
            st.title("🔐 Admin Paneli")
            udf = pd.read_csv(U_DB)
            pending = udf[udf['Status'] == "Pending"]
            if not pending.empty:
                for i, r in pending.iterrows():
                    col_u, col_b = st.columns([3, 1])
                    col_u.write(f"Talep: {r['Name']} (@{r['User']})")
                    if col_b.button("ONAYLA", key=i):
                        udf.at[i, 'Status'] = "Approved"
                        udf.to_csv(U_DB, index=False)
                        st.rerun()
                    if col_b.button("RET / SİL", key=f"r{i}"):
                        udf = udf.drop(i)
                        udf.to_csv(U_DB, index=False)
                        st.rerun()
            else: st.success("Bekleyen talep yok.")
        else: st.error("Yetkisiz erişim.")