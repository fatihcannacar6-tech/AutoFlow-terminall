import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import hashlib
import os
from datetime import datetime
import plotly.graph_objects as go
from scipy.optimize import minimize
from fpdf import FPDF

# --- 1. VERİTABANI SİSTEMİ ---
USER_DB, PORT_DB = "users_v17.csv", "portfolio_v17.csv"

def init_db():
    if not os.path.exists(USER_DB):
        hp = hashlib.sha256(str.encode("8826244")).hexdigest()
        users = pd.DataFrame([["fatihcan", hp, "Fatih Can", "Admin", "Active"]], 
                             columns=["Username", "Password", "Name", "Role", "Status"])
        users.to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "Maliyet", "Adet", "Kat"]).to_csv(PORT_DB, index=False)

init_db()

# --- 2. MODER VE MOBİL UYUMLU ARAYÜZ ---
st.set_page_config(page_title="AutoFlow", layout="wide", page_icon="🏛️")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #F8FAFC; }
    
    .login-box {
        max-width: 420px;
        margin: auto;
        padding: 30px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    
    .stMetric { background: white !important; padding: 20px !important; border-radius: 12px !important; border: 1px solid #F1F5F9 !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    div.stButton > button { width: 100% !important; border-radius: 10px; height: 45px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. YARDIMCI FONKSİYONLAR ---
def tr_fix(text):
    chars = {"İ": "I", "ı": "i", "Ş": "S", "ş": "s", "Ğ": "G", "ğ": "g", "Ü": "U", "ü": "u", "Ö": "O", "ö": "o", "Ç": "C", "ç": "c"}
    for tr, eng in chars.items():
        text = text.replace(tr, eng)
    return text

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
    df['Güncel'] = prices
    df['Değer'] = df['Güncel'] * df['Adet']
    df['Kâr/Zarar'] = df['Değer'] - (df['Maliyet'] * df['Adet'])
    return df

# --- 4. GİRİŞ VE KAYIT PANELİ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.write("##") 
    _, col_mid, _ = st.columns([1, 1.2, 1])
    with col_mid:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🏛️ AutoFlow</h2>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
        with tab1:
            u = st.text_input("Kullanıcı Adı", key="login_u")
            p = st.text_input("Şifre", type="password", key="login_p")
            if st.button("GİRİŞ YAP", type="primary"):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(p)).hexdigest()
                match = users[(users['Username']==u) & (users['Password']==hp)]
                if not match.empty:
                    if match.iloc[0]['Status'] == "Active":
                        st.session_state.logged_in = True
                        st.session_state.u_data = match.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Hesabınız admin onayı bekliyor.")
                else: st.error("Hatalı bilgiler.")
        with tab2:
            new_u = st.text_input("Kullanıcı Adı Belirle", key="reg_u").lower()
            new_n = st.text_input("Ad Soyad", key="reg_n")
            new_p = st.text_input("Yeni Şifre Oluştur", type="password", key="reg_p")
            if st.button("KAYIT TALEBİ GÖNDER"):
                users = pd.read_csv(USER_DB)
                if new_u in users['Username'].values: st.error("Kullanıcı adı mevcut.")
                else:
                    hp = hashlib.sha256(str.encode(new_p)).hexdigest()
                    new_user = pd.DataFrame([[new_u, hp, new_n, "User", "Pending"]], columns=users.columns)
                    new_user.to_csv(USER_DB, mode='a', header=False, index=False)
                    st.success("Talep gönderildi.")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- 5. SIDEBAR ---
    with st.sidebar:
        u_name = st.session_state.u_data.get('Name', 'Kullanıcı')
        u_role = st.session_state.u_data.get('Role', 'User')
        st.markdown(f"### 🏛️ AutoFlow\n**{u_name}**")
        menu = st.radio("MENÜ", ["📊 DASHBOARD", "⚖️ OPTİMİZASYON", "💼 PORTFÖYÜM", "⚙️ AYARLAR"] + (["🔑 ADMIN PANELİ"] if u_role == "Admin" else []))
        if st.button("Güvenli Çıkış"):
            st.session_state.logged_in = False
            st.rerun()

    df_port = pd.read_csv(PORT_DB)
    my_port = df_port[df_port['Owner'] == st.session_state.u_data.get('Username')]

    # --- 6. DASHBOARD ---
    if menu == "📊 DASHBOARD":
        st.title("📊 Mevcut Portföy Durumu")
        if not my_port.empty:
            proc_df = fetch_prices(my_port)
            st.dataframe(proc_df[["Kod", "Adet", "Maliyet", "Güncel", "Kâr/Zarar"]], use_container_width=True, hide_index=True)
        else: st.info("Henüz varlık eklemediniz.")

    # --- 7. AI OPTİMİZASYON ---
    elif menu == "⚖️ OPTİMİZASYON":
        st.title("⚖️ AI Risk & Optimizasyon Analizi")
        if len(my_port) >= 2:
            assets = my_port['Kod'].unique()
            data = pd.DataFrame()
            analysis_results = []
            with st.spinner("AI Analiz Yapıyor..."):
                for a in assets:
                    tk = f"{a}.IS" if my_port[my_port['Kod']==a]['Kat'].values[0]=="Hisse" else f"{a}-USD"
                    hist = yf.Ticker(tk).history(period="1y")['Close']
                    data[a] = hist
                    vol = hist.pct_change().std() * np.sqrt(252) * 100
                    ma20 = hist.rolling(20).mean().iloc[-1]
                    last = hist.iloc[-1]
                    signal = "🟢 AL TUT" if last > ma20 else "🔴 SAT İZLE"
                    analysis_results.append({"Varlık": a, "Risk (%)": f"{vol:.2f}", "Sinyal": signal})

            res_df = pd.DataFrame(analysis_results)
            st.table(res_df)

            def export_pdf(df):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, tr_fix("AutoFlow AI Analiz Raporu"), ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(60, 10, tr_fix("Varlik"), 1)
                pdf.cell(60, 10, tr_fix("Risk %"), 1)
                pdf.cell(60, 10, tr_fix("Sinyal"), 1)
                pdf.ln()
                pdf.set_font("Arial", '', 12)
                for i, row in df.iterrows():
                    pdf.cell(60, 10, tr_fix(str(row['Varlık'])), 1)
                    pdf.cell(60, 10, tr_fix(str(row['Risk (%)'])), 1)
                    pdf.cell(60, 10, tr_fix(str(row['Sinyal'])), 1)
                    pdf.ln()
                return pdf.output(dest='S').encode('latin-1', 'ignore')

            pdf_bytes = export_pdf(res_df)
            st.download_button("📄 ANALİZ RAPORUNU PDF İNDİR", data=pdf_bytes, file_name="AI_Analiz.pdf", mime="application/pdf")
        else: st.warning("En az 2 varlık ekleyin.")

    # --- 8. PORTFÖYÜM ---
    elif menu == "💼 PORTFÖYÜM":
        st.title("💼 Varlık Düzenle ve Kaydet")
        if not my_port.empty:
            st.subheader("Hisseleri Güncelle")
            updated_data = []
            for i, row in my_port.iterrows():
                col1, col2, col3 = st.columns(3)
                new_adet = col1.number_input(f"{row['Kod']} Adet", value=float(row['Adet']), key=f"a_{i}")
                new_maliyet = col2.number_input(f"{row['Kod']} Maliyet", value=float(row['Maliyet']), key=f"m_{i}")
                if col3.button(f"Sil: {row['Kod']}", key=f"del_{i}"):
                    df_all = pd.read_csv(PORT_DB)
                    df_all = df_all.drop(i)
                    df_all.to_csv(PORT_DB, index=False)
                    st.rerun()
                updated_data.append([st.session_state.u_data['Username'], row['Kod'], new_maliyet, new_adet, row['Kat']])
            
            if st.button("TÜM DEĞİŞİKLİKLERİ KAYDET"):
                df_all = pd.read_csv(PORT_DB)
                df_others = df_all[df_all['Owner'] != st.session_state.u_data['Username']]
                df_new_mine = pd.DataFrame(updated_data, columns=df_all.columns)
                pd.concat([df_others, df_new_mine]).to_csv(PORT_DB, index=False)
                st.success("Portföy güncellendi!")
                st.rerun()

        st.divider()
        st.subheader("Yeni Varlık Ekle")
        with st.form("add_asset"):
            c1, c2, c3, c4 = st.columns(4)
            k = c1.text_input("Kod (THYAO)").upper()
            a = c2.number_input("Adet", min_value=0.0)
            m = c3.number_input("Maliyet", min_value=0.0)
            cat = c4.selectbox("Tür", ["Hisse", "Kripto"])
            if st.form_submit_button("Yeni Ekle"):
                new_entry = pd.DataFrame([[st.session_state.u_data['Username'], k, m, a, cat]], columns=df_port.columns)
                pd.concat([pd.read_csv(PORT_DB), new_entry]).to_csv(PORT_DB, index=False)
                st.rerun()

    # --- 9. ADMIN & 10. AYARLAR ---
    elif menu == "🔑 ADMIN PANELİ":
        st.title("🔑 Admin Onay")
        u_df = pd.read_csv(USER_DB)
        pending = u_df[u_df['Status'] == "Pending"]
        for i, row in pending.iterrows():
            c1, c2, c3 = st.columns([2,1,1])
            c1.write(f"{row['Name']} (@{row['Username']})")
            if c2.button("✅", key=f"y_{i}"):
                u_df.loc[i, 'Status'] = "Active"; u_df.to_csv(USER_DB, index=False); st.rerun()
            if c3.button("❌", key=f"n_{i}"):
                u_df.drop(i).to_csv(USER_DB, index=False); st.rerun()

    elif menu == "⚙️ AYARLAR":
        st.title("⚙️ Şifre Değiştir")
        new_p = st.text_input("Yeni Şifre", type="password")
        if st.button("Güncelle"):
            u_df = pd.read_csv(USER_DB)
            u_df.loc[u_df['Username'] == st.session_state.u_data['Username'], 'Password'] = hashlib.sha256(str.encode(new_p)).hexdigest()
            u_df.to_csv(USER_DB, index=False); st.success("Şifre güncellendi.")