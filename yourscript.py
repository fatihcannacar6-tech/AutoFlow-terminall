import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import feedparser
from datetime import datetime

# --- 1. SİSTEM AYARLARI VE VERİTABANI ---
USER_DB, PORT_DB = "users_v16.csv", "portfolio_v16.csv"
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

# --- 3. ULTRA MODERN CSS TASARIM ---
st.set_page_config(page_title="AKOSELL WMS", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    /* Ana Arkaplan */
    .stApp { background-color: #FDFDFF; }
    
    /* Sidebar Tasarımı */
    [data-testid="stSidebar"] { background-color: #0F172A !important; border-right: 1px solid #1E293B; }
    [data-testid="stSidebar"] * { color: #F8FAFC !important; }
    
    /* Kart Yapıları */
    .metric-card {
        background: white; padding: 24px; border-radius: 20px;
        border: 1px solid #F1F5F9; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }
    .metric-card:hover { transform: translateY(-5px); }
    
    /* Modern Inputlar */
    .stTextInput input, .stNumberInput input {
        border-radius: 12px !important; border: 1px solid #E2E8F0 !important;
        padding: 12px !important;
    }
    
    /* Sidebar Profil */
    .profile-box {
        text-align: center; padding: 30px 10px;
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        margin: -20px -15px 20px -15px; border-bottom: 1px solid #1E293B;
    }
    
    /* Butonlar */
    .stButton button {
        border-radius: 12px !important; font-weight: 600 !important;
        transition: all 0.3s !important; text-transform: uppercase; letter-spacing: 1px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. OTURUM YÖNETİMİ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Giriş Ekranı Tasarımı
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div style='text-align:center; padding:50px 0;'><h1>💎 AKOSELL <span style='color:#3B82F6'>WMS</span></h1><p style='color:#64748B'>Varlık Yönetiminde Yeni Nesil Standart</p></div>", unsafe_allow_html=True)
        tab_l, tab_r = st.tabs(["🔒 Giriş Yap", "🚀 Kayıt Ol"])
        
        with tab_l:
            u = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı adınız...")
            p = st.text_input("Şifre", type="password", placeholder="••••••••")
            if st.button("Sisteme Eriş", use_container_width=True):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(p)).hexdigest()
                user = users[(users['Username']==u) & (users['Password']==hp)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.logged_in = True
                        st.session_state.u_data = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Hesabınız henüz onaylanmadı.")
                else: st.error("Bilgiler hatalı.")
        
        with tab_r:
            nu = st.text_input("Yeni Kullanıcı")
            nn = st.text_input("Ad Soyad")
            ne = st.text_input("E-posta")
            np = st.text_input("Şifre Belirle", type="password")
            if st.button("Kayıt Talebi Oluştur", use_container_width=True):
                users = pd.read_csv(USER_DB)
                if nu in users['Username'].values: st.error("Kullanıcı adı alınmış.")
                else:
                    new_user = pd.DataFrame([[nu, hashlib.sha256(str.encode(np)).hexdigest(), nn, ne, "Pending", "User"]], columns=users.columns)
                    pd.concat([users, new_user]).to_csv(USER_DB, index=False)
                    st.success("Talebiniz yöneticiye iletildi.")

else:
    # --- 5. SIDEBAR ---
    with st.sidebar:
        avatar = f"{AVATAR_DIR}/{st.session_state.u_data['Username']}.png"
        img = avatar if os.path.exists(avatar) else "https://ui-avatars.com/api/?name=" + st.session_state.u_data['Name']
        
        st.markdown(f"""
            <div class="profile-box">
                <img src="{img}" style="width:90px; height:90px; border-radius:25px; object-fit:cover; margin-bottom:15px; border: 2px solid #3B82F6;">
                <h3 style="margin:0; font-size:18px;">{st.session_state.u_data['Name']}</h3>
                <p style="color:#94A3B8 !important; font-size:12px; margin-top:5px;">{st.session_state.u_data['Role'].upper()} PANELİ</p>
            </div>
        """, unsafe_allow_html=True)
        
        m_items = ["📊 Dashboard", "💼 Portföy", "📈 Analiz", "📅 Takvim", "📰 Haberler", "⚙️ Ayarlar"]
        if st.session_state.u_data['Role'] == "Admin": m_items.append("🔐 Yönetim")
        
        menu = st.radio("MENÜ", m_items, label_visibility="collapsed")
        
        st.markdown("<br>"*5, unsafe_allow_html=True)
        if st.button("🚪 Oturumu Kapat", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- 6. SAYFA İÇERİKLERİ ---
    p_df = pd.read_csv(PORT_DB)
    my_p = p_df[p_df['Owner'] == st.session_state.u_data['Username']]

    if "Dashboard" in menu:
        st.markdown(f"<h2>Hoş Geldin, {st.session_state.u_data['Name']} 👋</h2>", unsafe_allow_html=True)
        
        if not my_p.empty:
            with st.spinner("Piyasalar taranıyor..."):
                prices = []
                for _, r in my_p.iterrows():
                    sym = f"{r['Kod']}.IS" if r['Kat'] == "Hisse" else f"{r['Kod']}-USD"
                    val = get_stock_price(sym)
                    prices.append(val if val else r['Maliyet'])
                
                my_p['Current'] = prices
                total_m = (my_p['Maliyet'] * my_p['Adet']).sum()
                total_v = (my_p['Current'] * my_p['Adet']).sum()
                diff = total_v - total_m

            # Metrik Kartları
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='metric-card'><small>TOPLAM MALİYET</small><h3>₺{total_m:,.2f}</h3></div>", unsafe_allow_html=True)
            with c2: 
                color = "#10B981" if diff >= 0 else "#EF4444"
                st.markdown(f"<div class='metric-card'><small>NET K/Z DURUMU</small><h3 style='color:{color}'>₺{diff:,.2f}</h3></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-card'><small>PORTFÖY HACMİ</small><h3>₺{total_v:,.2f}</h3></div>", unsafe_allow_html=True)
            
            # Ana Grafik
            st.markdown("<br>", unsafe_allow_html=True)
            sel = st.selectbox("Detaylı Grafik İncele", my_p['Kod'].unique())
            s_sym = f"{sel}.IS" if my_p[my_p['Kod']==sel]['Kat'].iloc[0] == "Hisse" else f"{sel}-USD"
            hist = yf.Ticker(s_sym).history(period="1mo")
            fig = px.area(hist, x=hist.index, y="Close", title=f"{sel} Aylık Değişim")
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Portföyünüzde henüz veri bulunmuyor. Lütfen varlık ekleyin.")

    elif "Ayarlar" in menu:
        st.title("⚙️ Profil ve Güvenlik")
        u_df = pd.read_csv(USER_DB)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Görünüm")
            f = st.file_uploader("Profil Fotoğrafı Yükle", type=["jpg","png"])
            if f:
                with open(f"{AVATAR_DIR}/{st.session_state.u_data['Username']}.png", "wb") as file:
                    file.write(f.getbuffer())
                st.success("Fotoğraf güncellendi! Lütfen sayfayı yenileyin.")

        with col_b:
            st.subheader("Hesap Güvenliği")
            new_n = st.text_input("Görünen Ad", value=st.session_state.u_data['Name'])
            new_p = st.text_input("Yeni Şifre", type="password")
            if st.button("Bilgileri Güncelle"):
                u_df.loc[u_df['Username'] == st.session_state.u_data['Username'], 'Name'] = new_n
                if new_p:
                    u_df.loc[u_df['Username'] == st.session_state.u_data['Username'], 'Password'] = hashlib.sha256(str.encode(new_p)).hexdigest()
                u_df.to_csv(USER_DB, index=False)
                st.success("Başarıyla güncellendi.")

        st.divider()
        if st.button("🔴 TÜM VERİLERİMİ SIFIRLA"):
            p_df = p_df[p_df['Owner'] != st.session_state.u_data['Username']]
            p_df.to_csv(PORT_DB, index=False)
            st.warning("Portföy verileriniz silindi.")

    elif "Yönetim" in menu:
        st.title("🔐 Yönetici Paneli")
        u_df = pd.read_csv(USER_DB)
        pend = u_df[u_df['Status'] == "Pending"]
        
        if not pend.empty:
            for i, r in pend.iterrows():
                with st.container():
                    cx, cy, cz = st.columns([2, 1, 1])
                    cx.write(f"**{r['Name']}** ({r['Email']})")
                    if cy.button("ONAYLA", key=f"app_{i}"):
                        u_df.loc[u_df['Username'] == r['Username'], 'Status'] = "Approved"
                        u_df.to_csv(USER_DB, index=False)
                        st.rerun()
                    if cz.button("REDDET", key=f"rej_{i}"):
                        u_df = u_df[u_df['Username'] != r['Username']]
                        u_df.to_csv(USER_DB, index=False)
                        st.rerun()
        else: st.write("Bekleyen kullanıcı talebi yok.")

    elif "Portföy" in menu:
        st.title("💼 Varlık Yönetimi")
        with st.expander("➕ Yeni Varlık Ekle", expanded=True):
            with st.form("add_f"):
                c1, c2, c3, c4 = st.columns(4)
                k = c1.text_input("Varlık Kodu (Örn: BTC, THYAO)")
                m = c2.number_input("Birim Maliyet", min_value=0.0)
                a = c3.number_input("Adet", min_value=0.0)
                cat = c4.selectbox("Kategori", ["Hisse", "Kripto", "Emtia"])
                if st.form_submit_button("Portföye Ekle"):
                    new_r = pd.DataFrame([[st.session_state.u_data['Username'], k.upper(), m, a, cat]], columns=p_df.columns)
                    pd.concat([p_df, new_r]).to_csv(PORT_DB, index=False)
                    st.success("Eklendi!")
                    st.rerun()
        
        if not my_p.empty:
            st.subheader("Mevcut Varlıklarınız")
            st.dataframe(my_p, use_container_width=True)

    elif "Haberler" in menu:
        st.title("📰 Piyasa Gündemi")
        feed = get_news_feed()
        for item in feed.entries[:10]:
            with st.container():
                st.markdown(f"#### {item.title}")
                st.caption(f"Yayınlanma: {item.published}")
                st.markdown(f"[Haberin Tamamı]({item.link})")
                st.divider()

    elif "Analiz" in menu:
        st.title("📈 Stratejik Analiz")
        if not my_p.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig_p = px.pie(my_p, values='Adet', names='Kod', hole=0.5, title="Varlık Dağılımı")
                st.plotly_chart(fig_p, use_container_width=True)
            with col2:
                fig_b = px.bar(my_p, x='Kod', y='Adet', color='Kat', title="Kategori Kıyaslaması")
                st.plotly_chart(fig_b, use_container_width=True)
        else: st.warning("Analiz yapılacak veri yok.")

    elif "Takvim" in menu:
        st.title("📅 Ekonomik Takvim")
        events = [
            {"Tarih": "15 Ocak", "Olay": "Enflasyon Verisi", "Önem": "Kritik 🔥"},
            {"Tarih": "22 Ocak", "Olay": "Faiz Kararı", "Etki": "Yüksek 🚀"}
        ]
        st.table(events)