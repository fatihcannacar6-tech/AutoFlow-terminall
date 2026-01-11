import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import feedparser
from datetime import datetime

# --- 1. SİSTEM YAPILANDIRMASI ---
USER_DB, PORT_DB = "users_v17.csv", "portfolio_v17.csv"
AVATAR_DIR = "avatars"

if not os.path.exists(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

def init_db():
    if not os.path.exists(USER_DB):
        admin_pw = hashlib.sha256(str.encode("admin123")).hexdigest()
        df = pd.DataFrame([["admin", admin_pw, "Yönetici", "admin@akosell.com", "Approved", "Admin"]], 
                          columns=["Username", "Password", "Name", "Email", "Status", "Role"])
        df.to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "Maliyet", "Adet", "Kat"]).to_csv(PORT_DB, index=False)

init_db()

# --- 2. HIZ OPTİMİZASYONU (CACHING) ---
@st.cache_data(ttl=300)
def get_stock_price(symbol):
    try:
        data = yf.Ticker(symbol).history(period="1d")
        return data['Close'].iloc[-1] if not data.empty else None
    except: return None

@st.cache_data(ttl=600)
def get_news_feed():
    return feedparser.parse("https://www.haberturk.com/rss/kategori/ekonomi.xml")

# --- 3. PROFESYONEL BEYAZ ARAYÜZ (CLEAN UI) ---
st.set_page_config(page_title="AKOSELL WMS", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    /* Ana Arkaplan ve Temizlik */
    .stApp { background-color: #FFFFFF; }
    
    /* Sidebar - Soft Gray Style */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Metrik Kartları - Minimalist */
    .metric-card {
        background: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    .metric-title { color: #64748B; font-size: 13px; font-weight: 500; text-transform: uppercase; }
    .metric-value { color: #0F172A; font-size: 24px; font-weight: 700; margin-top: 5px; }

    /* Profil Alanı */
    .profile-section {
        text-align: center;
        padding: 20px 0;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    
    /* Buton Tasarımları */
    .stButton button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background-color: #F1F5F9 !important;
        border-color: #CBD5E1 !important;
    }
    
    /* Tab ve Inputlar */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #F1F5F9;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. OTURUM YÖNETİMİ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='text-align:center; padding:60px 0;'><h1 style='color:#0F172A; font-weight:800; letter-spacing:-1px;'>AKOSELL <span style='color:#2563EB'>WMS</span></h1><p style='color:#64748B'>Kurumsal Varlık Yönetim Terminali</p></div>", unsafe_allow_html=True)
        tab_in, tab_up = st.tabs(["🔐 Giriş", "📝 Kayıt"])
        
        with tab_in:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("Sisteme Giriş Yap", use_container_width=True):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(p)).hexdigest()
                user = users[(users['Username']==u) & (users['Password']==hp)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.logged_in = True
                        st.session_state.u_data = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Erişim için yönetici onayı bekleniyor.")
                else: st.error("Geçersiz kimlik bilgileri.")
        
        with tab_up:
            nu, nn, ne, np = st.text_input("Kullanıcı Adı *"), st.text_input("Ad Soyad"), st.text_input("E-posta"), st.text_input("Şifre *", type="password")
            if st.button("Kayıt Ol", use_container_width=True):
                users = pd.read_csv(USER_DB)
                if nu in users['Username'].values: st.error("Kullanıcı adı kullanımda.")
                else:
                    new_u = pd.DataFrame([[nu, hashlib.sha256(str.encode(np)).hexdigest(), nn, ne, "Pending", "User"]], columns=users.columns)
                    pd.concat([users, new_u]).to_csv(USER_DB, index=False)
                    st.success("Talebiniz yöneticinize iletildi.")

else:
    # --- 5. SIDEBAR ---
    with st.sidebar:
        avatar = f"{AVATAR_DIR}/{st.session_state.u_data['Username']}.png"
        img = avatar if os.path.exists(avatar) else "https://ui-avatars.com/api/?background=E2E8F0&color=475569&name=" + st.session_state.u_data['Name']
        
        st.markdown(f"""
            <div class="profile-section">
                <img src="{img}" style="width:70px; height:70px; border-radius:50%; object-fit:cover; margin-bottom:10px; border: 1px solid #E2E8F0;">
                <div style="font-weight:700; color:#0F172A; font-size:16px;">{st.session_state.u_data['Name']}</div>
                <div style="font-size:12px; color:#64748B;">{st.session_state.u_data['Role']} Account</div>
            </div>
        """, unsafe_allow_html=True)
        
        menu_options = {
            "📊 Dashboard": "Dashboard",
            "💼 Portföy Yönetimi": "Portföy",
            "📈 Analitik Raporlar": "Analiz",
            "📅 Takvim": "Takvim",
            "📰 Canlı Haberler": "Haberler",
            "⚙️ Ayarlar": "Ayarlar"
        }
        if st.session_state.u_data['Role'] == "Admin": menu_options["🔐 Yönetici Paneli"] = "Yönetim"
        
        selection = st.radio("ANA MENÜ", list(menu_options.keys()), label_visibility="collapsed")
        menu = menu_options[selection]
        
        st.markdown("<br>"*2, unsafe_allow_html=True)
        if st.button("🚪 Güvenli Çıkış", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- 6. SAYFA İÇERİKLERİ ---
    p_df = pd.read_csv(PORT_DB)
    my_p = p_df[p_df['Owner'] == st.session_state.u_data['Username']]

    if menu == "Dashboard":
        st.markdown(f"<h2 style='letter-spacing:-1px;'>Genel Bakış</h2>", unsafe_allow_html=True)
        if not my_p.empty:
            with st.spinner("Piyasa verileri senkronize ediliyor..."):
                prices = []
                for _, r in my_p.iterrows():
                    sym = f"{r['Kod']}.IS" if r['Kat'] == "Hisse" else f"{r['Kod']}-USD"
                    val = get_stock_price(sym)
                    prices.append(val if val else r['Maliyet'])
                
                my_p['Current'] = prices
                total_m = (my_p['Maliyet'] * my_p['Adet']).sum()
                total_v = (my_p['Current'] * my_p['Adet']).sum()
                diff = total_v - total_m

            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='metric-card'><div class='metric-title'>Ana Sermaye</div><div class='metric-value'>₺{total_m:,.2f}</div></div>", unsafe_allow_html=True)
            with c2: 
                color = "#059669" if diff >= 0 else "#DC2626"
                st.markdown(f"<div class='metric-card'><div class='metric-title'>Toplam Getiri</div><div class='metric-value' style='color:{color}'>₺{diff:,.2f}</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-card'><div class='metric-title'>Portföy Değeri</div><div class='metric-value'>₺{total_v:,.2f}</div></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            sel_asset = st.selectbox("Varlık Grafiği", my_p['Kod'].unique())
            s_sym = f"{sel_asset}.IS" if my_p[my_p['Kod']==sel_asset]['Kat'].iloc[0] == "Hisse" else f"{sel_asset}-USD"
            hist = yf.Ticker(s_sym).history(period="1mo")
            fig = px.line(hist, y="Close", title=f"{sel_asset} - 30 Günlük Seyir", color_discrete_sequence=['#2563EB'])
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_title="", yaxis_title="Fiyat")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("İstatistikleri görmek için lütfen Portföy sekmesinden varlık ekleyin.")

    elif menu == "Portföy":
        st.title("💼 Varlıklarım")
        with st.expander("➕ Varlık Ekle", expanded=True):
            with st.form("add_form"):
                cx1, cx2, cx3, cx4 = st.columns(4)
                k = cx1.text_input("Kod (Örn: BTC, EREGL)")
                m = cx2.number_input("Maliyet", min_value=0.0)
                a = cx3.number_input("Adet", min_value=0.0)
                cat = cx4.selectbox("Tür", ["Hisse", "Kripto", "Emtia"])
                if st.form_submit_button("Listeye Ekle"):
                    new_r = pd.DataFrame([[st.session_state.u_data['Username'], k.upper(), m, a, cat]], columns=p_df.columns)
                    pd.concat([p_df, new_r]).to_csv(PORT_DB, index=False)
                    st.success("Başarıyla eklendi.")
                    st.rerun()
        
        if not my_p.empty:
            st.subheader("Varlık Listesi")
            st.dataframe(my_p, use_container_width=True, hide_index=True)

    elif menu == "Analiz":
        st.title("📈 Portföy Analitiği")
        if not my_p.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                fig_p = px.pie(my_p, values='Adet', names='Kod', hole=0.4, title="Dağılım", color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_p, use_container_width=True)
            with col_b:
                fig_b = px.bar(my_p, x='Kod', y='Adet', title="Varlık Miktarları", color='Kat', color_discrete_map={'Hisse':'#2563EB', 'Kripto':'#F59E0B', 'Emtia':'#10B981'})
                st.plotly_chart(fig_b, use_container_width=True)
        else: st.warning("Analiz edilecek veri bulunamadı.")

    elif menu == "Haberler":
        st.title("📰 Finans Gündemi")
        news = get_news_feed()
        for item in news.entries[:10]:
            st.markdown(f"""
                <div style="padding:15px; border-bottom:1px solid #F1F5F9;">
                    <a href="{item.link}" style="text-decoration:none; color:#1E293B; font-weight:600; font-size:16px;">{item.title}</a>
                    <p style="color:#64748B; font-size:12px; margin-top:5px;">{item.published}</p>
                </div>
            """, unsafe_allow_html=True)

    elif menu == "Ayarlar":
        st.title("⚙️ Hesap Ayarları")
        u_df = pd.read_csv(USER_DB)
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader("Profil Görseli")
            img_file = st.file_uploader("Yeni Fotoğraf Yükle", type=["jpg", "png"])
            if img_file:
                with open(f"{AVATAR_DIR}/{st.session_state.u_data['Username']}.png", "wb") as f:
                    f.write(img_file.getbuffer())
                st.success("Fotoğraf güncellendi. Sidebar'da görmek için sayfayı yenileyin.")
        
        with col_s2:
            st.subheader("Güvenlik & Kimlik")
            new_n = st.text_input("Görünen Ad", value=st.session_state.u_data['Name'])
            new_p = st.text_input("Yeni Şifre (Değiştirmek istemiyorsanız boş bırakın)", type="password")
            if st.button("Güncellemeleri Kaydet"):
                u_df.loc[u_df['Username'] == st.session_state.u_data['Username'], 'Name'] = new_n
                if new_p:
                    u_df.loc[u_df['Username'] == st.session_state.u_data['Username'], 'Password'] = hashlib.sha256(str.encode(new_p)).hexdigest()
                u_df.to_csv(USER_DB, index=False)
                st.success("Bilgileriniz güncellendi.")

        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🗑️ TÜM PORTFÖY VERİLERİMİ TEMİZLE", use_container_width=True):
            p_df = p_df[p_df['Owner'] != st.session_state.u_data['Username']]
            p_df.to_csv(PORT_DB, index=False)
            st.warning("Verileriniz kalıcı olarak silindi.")
            st.rerun()

    elif menu == "Yönetim":
        st.title("🔐 Yönetici Paneli")
        u_df = pd.read_csv(USER_DB)
        pend = u_df[u_df['Status'] == "Pending"]
        
        if not pend.empty:
            for i, r in pend.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{r['Name']}** (@{r['Username']})")
                    if c2.button("✅ ONAY", key=f"ok_{i}"):
                        u_df.loc[u_df['Username'] == r['Username'], 'Status'] = "Approved"
                        u_df.to_csv(USER_DB, index=False)
                        st.rerun()
                    if c3.button("❌ RED", key=f"no_{i}"):
                        u_df = u_df[u_df['Username'] != r['Username']]
                        u_df.to_csv(USER_DB, index=False)
                        st.rerun()
        else: st.info("Onay bekleyen yeni kayıt bulunmuyor.")

    elif menu == "Takvim":
        st.title("📅 Ekonomik Takvim")
        st.info("Piyasa yapıcı veriler ve önemli tarihler burada listelenir.")
        events = [{"Tarih": "15 Ocak", "Olay": "TÜFE Verisi", "Önem": "Yüksek"}, {"Tarih": "22 Ocak", "Olay": "Faiz Kararı", "Önem": "Kritik"}]
        st.table(events)