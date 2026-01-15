import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from fpdf import FPDF

# --- 1. AYARLAR VE TASARIM ---
st.set_page_config(page_title="Autoflow Terminal", layout="wide", page_icon="🌊")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    [data-testid="stAppViewContainer"] { background-color: #0F1115 !important; color: #F8FAFC !important; }
    .stRadio div[role="radiogroup"] label {
        background-color: #F8FAFC !important; border: 1px solid #F1F5F9 !important;
        border-radius: 10px !important; padding: 10px 15px !important; margin-bottom: 6px !important;
    }
    .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #2563EB !important; border-color: #2563EB !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] p { color: white !important; }
    .metric-card { background: #1A1D23; padding: 20px; border-radius: 15px; border-left: 5px solid #3B82F6; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERİ TABANI SİSTEMİ ---
U_DB, P_DB = "autoflow_users.csv", "autoflow_portfolio.csv"

def init_db():
    if not os.path.exists(U_DB):
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Sistem Yönetici", "admin@autoflow.ai", "Approved", "Admin"]], 
                     columns=["User", "Pass", "Name", "Email", "Status", "Role"]).to_csv(U_DB, index=False)
    if not os.path.exists(P_DB):
        pd.DataFrame(columns=["Owner", "Symbol", "Type", "Cost", "Qty", "Date"]).to_csv(P_DB, index=False)

init_db()

# --- 3. PDF FONKSİYONU ---
def create_pdf(df, user_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="AUTOFLOW STRATEJIK PORTFOY RAPORU", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        pdf.cell(190, 8, txt=f"{row['Symbol']} | {row['Type']} | Adet: {row['Qty']} | Maliyet: {row['Cost']}", ln=True, border=1)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. GİRİŞ KONTROLÜ ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center; color:#3B82F6;'>AUTOFLOW</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["GİRİŞ", "KAYIT"])
        
        with t_log:
            u = st.text_input("Kullanıcı Adı", key="l_user")
            p = st.text_input("Şifre", type="password", key="l_pass")
            if st.button("GİRİŞ YAP", use_container_width=True):
                users = pd.read_csv(U_DB)
                hp = hashlib.sha256(p.encode()).hexdigest()
                found = users[(users['User'] == u) & (users['Pass'] == hp)]
                if not found.empty:
                    if found.iloc[0]['Status'] == "Approved":
                        st.session_state.auth = True
                        st.session_state.u_data = found.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Hesabınız onay bekliyor.")
                else: st.error("Hatalı bilgiler.")

        with t_reg:
            nu = st.text_input("Kullanıcı Adı", key="r_user")
            nn = st.text_input("Ad Soyad", key="r_name")
            ne = st.text_input("E-Posta", key="r_mail")
            np = st.text_input("Şifre", type="password", key="r_pass")
            if st.button("KAYIT TALEBİ GÖNDER", use_container_width=True):
                users = pd.read_csv(U_DB)
                if nu in users['User'].values: st.error("Bu kullanıcı adı alınmış.")
                else:
                    new_u = pd.DataFrame([[nu, hashlib.sha256(np.encode()).hexdigest(), nn, ne, "Pending", "User"]], columns=users.columns)
                    pd.concat([users, new_u]).to_csv(U_DB, index=False)
                    st.success("Talep iletildi.")

else:
    # --- 5. PANEL ---
    with st.sidebar:
        st.markdown(f"### 🌊 Autoflow\n**{st.session_state.u_data['Name']}**")
        menu = st.radio("MENÜ", ["📊 DASHBOARD", "💼 PORTFÖY", "📅 TEMETTÜ", "📑 RAPOR", "🧠 AI", "🔐 ADMİN"])
        
        st.divider()
        # Fiyat Alarmı (Sidebar)
        st.subheader("🚨 Fiyat Alarmı")
        alarm_sym = st.text_input("Sembol", "BTC-USD").upper()
        alarm_val = st.number_input("Hedef Fiyat ($)", value=90000.0)
        
        if st.button("ÇIKIŞ"):
            st.session_state.auth = False
            st.rerun()

    all_p = pd.read_csv(P_DB)
    my_p = all_p[all_p['Owner'] == st.session_state.u_data['User']].copy()

    # --- DASHBOARD ---
    if menu == "📊 DASHBOARD":
        st.title("📊 Terminal Özeti")
        if not my_p.empty:
            # Canlı Fiyat & Alarm Kontrolü
            try:
                price_now = yf.Ticker(alarm_sym).fast_info.last_price
                if price_now < alarm_val:
                    st.error(f"⚠️ ALARM: {alarm_sym} fiyatı {price_now:,.2f} seviyesinde! (Hedef: {alarm_val})")
                else:
                    st.success(f"✅ {alarm_sym} Stabil: {price_now:,.2f}")
            except: pass

            # Portföy Hesaplama
            vals = []
            for i, r in my_p.iterrows():
                try:
                    t_str = f"{r['Symbol']}.IS" if r['Type']=="Hisse" else f"{r['Symbol']}-USD"
                    vals.append(yf.Ticker(t_str).fast_info.last_price * r['Qty'])
                except: vals.append(r['Cost'] * r['Qty'])
            
            my_p['CurrentVal'] = vals
            st.metric("TOPLAM PORTFÖY DEĞERİ", f"₺{sum(vals):,.2f}")
            st.plotly_chart(px.pie(my_p, values='CurrentVal', names='Symbol', hole=0.4, template="plotly_dark"), use_container_width=True)
        else:
            st.info("Portföy boş.")

    # --- PORTFÖY ---
    elif menu == "💼 PORTFÖY":
        st.title("💼 Varlık Yönetimi")
        with st.form("ekle"):
            c1, c2, c3, c4 = st.columns(4)
            s = c1.text_input("Varlık Kodu").upper()
            t = c2.selectbox("Tür", ["Hisse", "Kripto", "Döviz"])
            q = c3.number_input("Adet", min_value=0.0)
            c = c4.number_input("Birim Maliyet", min_value=0.0)
            if st.form_submit_button("EKLE"):
                new_row = pd.DataFrame([[st.session_state.u_data['User'], s, t, c, q, datetime.now().date()]], columns=all_p.columns)
                pd.concat([all_p, new_row]).to_csv(P_DB, index=False)
                st.rerun()
        st.data_editor(my_p, use_container_width=True)

    # --- TEMETTÜ ---
    elif menu == "📅 TEMETTÜ":
        st.title("📅 Temettü Takvimi")
        if not my_p.empty:
            div_data = []
            for s in my_p[my_p['Type']=="Hisse"]['Symbol'].unique():
                t = yf.Ticker(f"{s}.IS")
                if not t.dividends.empty:
                    div_data.append({"Hisse": s, "Son Temettü": t.dividends.tail(1).values[0], "Tarih": t.dividends.tail(1).index[0].date()})
            if div_data: st.table(pd.DataFrame(div_data))
            else: st.write("Temettü verisi bulunamadı.")

    # --- RAPOR ---
    elif menu == "📑 RAPOR":
        st.title("📑 Rapor Oluştur")
        if not my_p.empty:
            pdf_bytes = create_pdf(my_p, st.session_state.u_data['Name'])
            st.download_button("📥 PDF OLARAK İNDİR", data=pdf_bytes, file_name="autoflow_rapor.pdf")
            csv = my_p.to_csv(index=False).encode('utf-8')
            st.download_button("📥 EXCEL (CSV) İNDİR", data=csv, file_name="autoflow_portfoy.csv")

    # --- AI ---
    elif menu == "🧠 AI":
        st.title("🧠 AI Strategist")
        st.info("Autoflow Yapay Zeka: Mevcut piyasa koşullarında nakit oranınızı %15 artırmak mantıklı olabilir.")
        st.line_chart(np.random.randn(20, 1).cumsum())

    # --- ADMIN ---
    elif menu == "🔐 ADMİN":
        if st.session_state.u_data['Role'] == "Admin":
            st.title("🔐 Yönetici Paneli")
            users = pd.read_csv(U_DB)
            pending = users[users['Status'] == "Pending"]
            for i, r in pending.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"{r['Name']} (@{r['User']})")
                if col2.button("ONAYLA", key=f"app_{i}"):
                    users.at[i, 'Status'] = "Approved"
                    users.to_csv(U_DB, index=False)
                    st.rerun()
        else: st.error("Yetkiniz yok.")