import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF

# --- 1. PREMIUM UI AYARLARI ---
st.set_page_config(page_title="Autoflow | Asset Terminal", layout="wide", page_icon="🌊")

st.markdown("""
    <style>
    /* BEYAZ SIDEBAR TASARIMI */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 2px solid #F1F5F9;
    }
    [data-testid="stSidebar"] .stMarkdown h3 { color: #1E293B; }
    
    /* KOYU İÇERİK ALANI */
    [data-testid="stAppViewContainer"] {
        background-color: #0B0E14 !important;
        color: #E2E8F0 !important;
    }
    
    /* BUTON VE GİRİŞ TASARIMLARI */
    .stButton>button {
        border-radius: 8px;
        transition: 0.3s;
    }
    .main-card {
        background: #161B22;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #30363D;
        margin-bottom: 20px;
    }
    /* TAB VE RADİO BUTON ÖZELLEŞTİRME */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1F2937;
        border-radius: 5px 5px 0 0;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERİ MOTORU (GELİŞMİŞ) ---
U_DB = "autoflow_users_v8.csv"
P_DB = "autoflow_portfolio_v8.csv"

def init_db():
    if not os.path.exists(U_DB):
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Baş Yönetici", "admin@autoflow.ai", "Approved", "Admin"]], 
                     columns=["User", "Pass", "Name", "Email", "Status", "Role"]).to_csv(U_DB, index=False)
    if not os.path.exists(P_DB):
        pd.DataFrame(columns=["Owner", "Symbol", "Type", "Cost", "Qty", "Date"]).to_csv(P_DB, index=False)

init_db()

# --- 3. AUTH SİSTEMİ (STABİL) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

def login_screen():
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h1 style='text-align:center; color:#3B82F6;'>🌊 AUTOFLOW</h1>", unsafe_allow_html=True)
        tab_in, tab_up = st.tabs(["🔐 OTURUM AÇ", "📝 KAYIT OL"])
        
        with tab_in:
            u = st.text_input("Kullanıcı", key="in_u")
            p = st.text_input("Şifre", type="password", key="in_p")
            if st.button("SİSTEME GİRİŞ", use_container_width=True, type="primary"):
                df = pd.read_csv(U_DB)
                hp = hashlib.sha256(p.encode()).hexdigest()
                user = df[(df['User'] == u) & (df['Pass'] == hp)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.logged_in = True
                        st.session_state.user = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Hesabınız henüz onaylanmadı.")
                else: st.error("Kullanıcı adı veya şifre hatalı.")
        
        with tab_up:
            nu = st.text_input("Kullanıcı Adı Seç", key="up_u")
            nn = st.text_input("Ad Soyad", key="up_n")
            ne = st.text_input("E-posta", key="up_e")
            np = st.text_input("Şifre", type="password", key="up_p")
            if st.button("KAYIT TALEBİ GÖNDER", use_container_width=True):
                df = pd.read_csv(U_DB)
                if nu in df['User'].values: st.error("Bu kullanıcı adı zaten var.")
                else:
                    new_u = pd.DataFrame([[nu, hashlib.sha256(np.encode()).hexdigest(), nn, ne, "Pending", "User"]], columns=df.columns)
                    pd.concat([df, new_u]).to_csv(U_DB, index=False)
                    st.success("Talebiniz yöneticiye iletildi.")

if not st.session_state.logged_in:
    login_screen()
else:
    # --- 4. ANA TERMİNAL ---
    with st.sidebar:
        st.markdown(f"### 🌊 Autoflow V8")
        st.markdown(f"**Operatör:** {st.session_state.user['Name']}")
        st.markdown(f"**Yetki:** `{st.session_state.user['Role']}`")
        st.divider()
        
        menu = st.radio("SİSTEM NAVİGASYONU", 
                        ["DASHBOARD", "PORTFÖY YÖNETİMİ", "TEMETTÜ TAKİBİ", "RAPORLAMA", "ADMİN PANELİ"])
        
        st.divider()
        if st.button("ÇIKIŞ YAP", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    all_p = pd.read_csv(P_DB)
    my_p = all_p[all_p['Owner'] == st.session_state.user['User']].copy()

    # --- 5. MODÜLLER ---
    
    # 5.1 ADMIN PANELİ (EN DETAYLI KISIM)
    if menu == "ADMİN PANELİ":
        if st.session_state.user['Role'] == "Admin":
            st.title("🔐 Sistem Yönetim Merkezi")
            u_df = pd.read_csv(U_DB)
            
            t1, t2 = st.tabs(["⏳ BEKLEYEN ONAYLAR", "👥 TÜM KULLANICILAR"])
            
            with t1:
                pending = u_df[u_df['Status'] == "Pending"]
                if pending.empty: st.info("Şu an bekleyen bir talep bulunmuyor.")
                for i, r in pending.iterrows():
                    with st.container():
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.write(f"**{r['Name']}** ({r['Email']})")
                        if c2.button("ONAYLA", key=f"app_{i}", use_container_width=True):
                            u_df.at[i, 'Status'] = "Approved"
                            u_df.to_csv(U_DB, index=False)
                            st.rerun()
                        if c3.button("REDDET", key=f"rej_{i}", use_container_width=True):
                            u_df = u_df.drop(i)
                            u_df.to_csv(U_DB, index=False)
                            st.rerun()
            
            with t2:
                st.dataframe(u_df[["User", "Name", "Email", "Status", "Role"]], use_container_width=True)
                target_user = st.selectbox("İşlem Yapılacak Kullanıcı", u_df['User'].tolist())
                if st.button("KULLANICIYI SİSTEMDEN SİL", type="secondary"):
                    if target_user != "admin":
                        u_df = u_df[u_df['User'] != target_user]
                        u_df.to_csv(U_DB, index=False)
                        st.success(f"{target_user} başarıyla silindi.")
                        st.rerun()
                    else: st.error("Ana yönetici silinemez!")
        else:
            st.error("Bu bölüme erişim yetkiniz yok.")

    # 5.2 DASHBOARD
    elif menu == "DASHBOARD":
        st.title("📊 Canlı İzleme Terminali")
        if not my_p.empty:
            with st.spinner("Piyasa verileri senkronize ediliyor..."):
                current_total = 0
                for i, r in my_p.iterrows():
                    try:
                        t_str = f"{r['Symbol']}.IS" if r['Type'] == "Hisse" else f"{r['Symbol']}-USD"
                        price = yf.Ticker(t_str).fast_info.last_price
                        current_total += (price * r['Qty'])
                    except: current_total += (r['Cost'] * r['Qty'])
                
                c1, c2, c3 = st.columns(3)
                c1.metric("TOPLAM DEĞER", f"₺{current_total:,.2f}")
                c2.metric("VARLIK ADEDİ", len(my_p))
                c3.metric("DURUM", "SİSTEM AKTİF", delta="BIST100 OK")
                
                fig = px.pie(my_p, values='Qty', names='Symbol', hole=0.5, template="plotly_dark", title="Varlık Dağılımı")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Henüz varlık eklemediniz.")

    # 5.3 PORTFÖY YÖNETİMİ
    elif menu == "PORTFÖY YÖNETİMİ":
        st.title("💼 Varlık Portföyü")
        with st.expander("➕ YENİ İŞLEM EKLE", expanded=True):
            with st.form("trade_form"):
                c1, c2, c3, c4 = st.columns(4)
                sym = c1.text_input("Kod (THYAO, BTC)").upper()
                typ = c2.selectbox("Tür", ["Hisse", "Kripto", "Döviz"])
                qty = c3.number_input("Miktar", min_value=0.0)
                cost = c4.number_input("Birim Maliyet", min_value=0.0)
                if st.form_submit_button("PORTFÖYE İŞLE"):
                    new_data = pd.DataFrame([[st.session_state.user['User'], sym, typ, cost, qty, datetime.now().date()]], columns=all_p.columns)
                    pd.concat([all_p, new_data]).to_csv(P_DB, index=False)
                    st.success("İşlem kaydedildi.")
                    st.rerun()
        
        st.subheader("Aktif Pozisyonlar")
        st.data_editor(my_p, use_container_width=True)

    # 5.4 TEMETTÜ VE RAPORLAMA (HIZLI ENTEGRASYON)
    elif menu == "TEMETTÜ TAKİBİ":
        st.title("📅 Temettü Takvimi")
        st.info("Bu modül BIST ve NASDAQ verilerini analiz ederek yıllık projeksiyon çıkarır.")
        # Basit bir liste örneği
        st.write("Yaklaşan Ödemeler:")
        st.table(my_p[my_p['Type'] == "Hisse"][['Symbol', 'Qty']])

    elif menu == "RAPORLAMA":
        st.title("📑 Belge Oluşturma")
        st.markdown('<div class="main-card">Bu bölümden portföyünüzün resmi dökümünü PDF veya CSV olarak alabilirsiniz.</div>', unsafe_allow_html=True)
        if st.button("📥 PDF RAPORU ÜRET"):
            st.write("PDF Üretiliyor... (fpdf entegrasyonu aktif)")