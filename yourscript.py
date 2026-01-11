import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import feedparser
from datetime import datetime

# --- 1. VERİTABANI VE DOSYA YAPILANDIRMASI ---
USER_DB, PORT_DB = "users_v15.csv", "portfolio_v15.csv"
if not os.path.exists("avatars"):
    os.makedirs("avatars")

def init_db():
    if not os.path.exists(USER_DB):
        admin_pw = hashlib.sha256(str.encode("admin123")).hexdigest()
        df = pd.DataFrame([["admin", admin_pw, "Admin", "admin@akosell.com", "Approved", "Admin"]], 
                          columns=["Username", "Password", "Name", "Email", "Status", "Role"])
        df.to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "YF_Kod", "Maliyet", "Adet", "Kat"]).to_csv(PORT_DB, index=False)

init_db()

# --- 2. HIZ OPTİMİZASYONU (CACHING) ---
@st.cache_data(ttl=600)  # 10 Dakika boyunca fiyatları hafızada tutar
def get_stock_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        return data['Close'].iloc[-1] if not data.empty else None
    except:
        return None

@st.cache_data(ttl=900)  # 15 Dakika boyunca haberleri hafızada tutar
def fetch_news():
    return feedparser.parse("https://www.haberturk.com/rss/kategori/ekonomi.xml")

# --- 3. SAYFA AYARLARI VE TASARIM ---
st.set_page_config(page_title="AKOSELL WMS", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    .user-profile { padding: 20px; background: #F8FAFC; border-radius: 12px; margin: 10px 15px 25px 15px; border: 1px solid #E2E8F0; text-align: center; }
    [data-testid="stSidebarNav"] { display: none; }
    .stRadio div[role="radiogroup"] { gap: 8px !important; padding: 0 15px !important; }
    .stRadio div[role="radiogroup"] label { background-color: #F1F5F9 !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; padding: 12px 16px !important; width: 100% !important; display: flex !important; align-items: center !important; transition: all 0.2s ease; cursor: pointer; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #00D1FF !important; border-color: #00D1FF !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] p { color: #FFFFFF !important; }
    .sidebar-footer { position: fixed; bottom: 20px; width: 270px; padding: 0 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. GİRİŞ VE KAYIT EKRANI ---
if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown("<br><h1 style='text-align:center;'>AKOSELL WMS</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["GİRİŞ YAP", "KAYIT OL"])
        with t_log:
            u = st.text_input("Kullanıcı")
            p = st.text_input("Şifre", type="password")
            if st.button("SİSTEME GİR", use_container_width=True, type="primary"):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(p)).hexdigest()
                match = users[(users['Username']==u) & (users['Password']==hp)]
                if not match.empty:
                    if match.iloc[0]['Status'] == "Approved":
                        st.session_state.logged_in = True
                        st.session_state.u_data = match.iloc[0].to_dict()
                        st.rerun()
                    else: st.error("Hesabınız admin onayı bekliyor.")
                else: st.error("Kullanıcı adı veya şifre hatalı.")
        with t_reg:
            nu, nn, ne, npw = st.text_input("Yeni Kullanıcı Adı"), st.text_input("Ad Soyad"), st.text_input("E-posta"), st.text_input("Şifre", type="password")
            if st.button("KAYIT TALEBİ GÖNDER", use_container_width=True):
                users = pd.read_csv(USER_DB)
                if nu in users['Username'].values: st.warning("Bu kullanıcı adı sistemde mevcut.")
                else:
                    new_u = pd.DataFrame([[nu, hashlib.sha256(str.encode(npw)).hexdigest(), nn, ne, "Pending", "User"]], columns=users.columns)
                    pd.concat([users, new_u]).to_csv(USER_DB, index=False)
                    st.success("Talebiniz iletildi, lütfen onay bekleyin.")

else:
    # --- 5. SIDEBAR ---
    with st.sidebar:
        avatar_path = f"avatars/{st.session_state.u_data['Username']}.png"
        img_display = avatar_path if os.path.exists(avatar_path) else "https://cdn-icons-png.flaticon.com/512/149/149071.png"
        st.markdown(f"""<div class="user-profile"><img src="{img_display}" style="width:80px; height:80px; border-radius:50%; object-fit:cover; border:3px solid #00D1FF; margin-bottom:10px;"><br><div style="font-size:18px; font-weight:800; color:#1E293B;">{st.session_state.u_data['Name'].upper()}</div><div style="color:#00D1FF; font-size:11px; font-weight:700;">{st.session_state.u_data['Role']}</div></div>""", unsafe_allow_html=True)
        menu_items = ["📊 DASHBOARD", "💼 PORTFÖYÜM", "📈 ANALİZLER", "📅 TAKVİM", "📰 HABERLER", "⚙️ AYARLAR"]
        if st.session_state.u_data['Role'] == "Admin": menu_items.append("🔐 ADMIN PANELİ")
        menu = st.radio("NAV", menu_items, label_visibility="collapsed")
        if st.button("ÇIKIŞ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    p_df = pd.read_csv(PORT_DB)
    my_port = p_df[p_df['Owner'] == st.session_state.u_data['Username']]

    # --- 6. DASHBOARD (HIZLI) ---
    if "DASHBOARD" in menu:
        st.title("📊 Stratejik Varlık Analizi")
        if not my_port.empty:
            with st.spinner('Veriler yükleniyor...'):
                prices = []
                for _, r in my_port.iterrows():
                    sym = f"{r['Kod']}.IS" if r['Kat'] == "Hisse" else f"{r['Kod']}-USD"
                    p = get_stock_price(sym)
                    prices.append(p if p else r['Maliyet'])
                my_port['Güncel'] = prices
                t_cost = (my_port['Maliyet'] * my_port['Adet']).sum()
                t_val = (my_port['Güncel'] * my_port['Adet']).sum()
                t_profit = t_val - t_cost

            c1, c2, c3 = st.columns(3)
            c1.metric("TOPLAM YATIRIM", f"₺{t_cost:,.2f}")
            c2.metric("KÂR / ZARAR", f"₺{t_profit:,.2f}", delta=f"{(t_profit/t_cost*100) if t_cost > 0 else 0:.2f}%")
            c3.metric("PORTFÖY DEĞERİ", f"₺{t_val:,.2f}")
            
            st.subheader("📈 Seçili Varlık Grafiği")
            sel_s = st.selectbox("Varlık Seçin", my_port['Kod'].unique())
            sym_s = f"{sel_s}.IS" if my_port[my_port['Kod']==sel_s]['Kat'].iloc[0] == "Hisse" else f"{sel_s}-USD"
            h_data = yf.Ticker(sym_s).history(period="1mo")
            fig = go.Figure(data=[go.Candlestick(x=h_data.index, open=h_data['Open'], high=h_data['High'], low=h_data['Low'], close=h_data['Close'])])
            fig.update_layout(template="plotly_white", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Henüz portföyünüzde varlık yok.")

    # --- 7. AYARLAR (FOTO, ŞİFRE, KULLANICI ADI, SIFIRLAMA) ---
    elif "AYARLAR" in menu:
        st.title("⚙️ Ayarlar")
        u_df = pd.read_csv(USER_DB)
        
        with st.expander("🖼️ Profil Fotoğrafı"):
            f = st.file_uploader("Dosya Seç", type=["png","jpg","jpeg"])
            if f:
                with open(f"avatars/{st.session_state.u_data['Username']}.png", "wb") as file: file.write(f.getbuffer())
                st.success("Fotoğraf yüklendi!")
                st.button("Yenile")

        with st.expander("👤 Hesap Bilgileri"):
            new_u = st.text_input("Kullanıcı Adı", value=st.session_state.u_data['Username'])
            new_n = st.text_input("Ad Soyad", value=st.session_state.u_data['Name'])
            if st.button("Bilgileri Güncelle"):
                if new_u != st.session_state.u_data['Username']:
                    p_df.loc[p_df['Owner'] == st.session_state.u_data['Username'], 'Owner'] = new_u
                    p_df.to_csv(PORT_DB, index=False)
                u_df.loc[u_df['Username'] == st.session_state.u_data['Username'], ['Username', 'Name']] = [new_u, new_n]
                u_df.to_csv(USER_DB, index=False)
                st.session_state.u_data['Username'] = new_u
                st.session_state.u_data['Name'] = new_n
                st.success("Güncellendi!")
                st.rerun()

        with st.expander("🔐 Şifre Değiştir"):
            new_p = st.text_input("Yeni Şifre", type="password")
            if st.button("Şifreyi Güncelle"):
                h_p = hashlib.sha256(str.encode(new_p)).hexdigest()
                u_df.loc[u_df['Username'] == st.session_state.u_data['Username'], 'Password'] = h_p
                u_df.to_csv(USER_DB, index=False)
                st.success("Şifre değişti.")

        with st.expander("🗑️ Verileri Sıfırla"):
            if st.button("Tüm Portföyümü Sil"):
                p_df = p_df[p_df['Owner'] != st.session_state.u_data['Username']]
                p_df.to_csv(PORT_DB, index=False)
                st.success("Portföy sıfırlandı.")
                st.rerun()

    # --- 8. ADMIN PANELİ (ONAY/RED) ---
    elif "ADMIN PANELİ" in menu:
        st.title("🔐 Admin Kontrol")
        u_df = pd.read_csv(USER_DB)
        pend = u_df[u_df['Status'] == "Pending"]
        if not pend.empty:
            for i, r in pend.iterrows():
                c1, c2, c3 = st.columns([2,1,1])
                c1.write(f"**{r['Name']}** (@{r['Username']})")
                if c2.button("✅ ONAYLA", key=f"y_{r['Username']}"):
                    u_df.loc[u_df['Username'] == r['Username'], 'Status'] = "Approved"
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
                if c3.button("❌ REDDET", key=f"n_{r['Username']}"):
                    u_df = u_df[u_df['Username'] != r['Username']]
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
        else: st.info("Bekleyen onay yok.")

    # --- 9. HABERLER (HIZLI) ---
    elif "HABERLER" in menu:
        st.title("📰 Canlı Ekonomi Haberleri")
        feed = fetch_news()
        for entry in feed.entries[:8]:
            with st.expander(entry.title):
                st.write(entry.published)
                st.markdown(f"[Haber Detayı]({entry.link})")

    # --- 10. ANALİZLER ---
    elif "ANALİZLER" in menu:
        st.title("📈 Portföy Analitiği")
        if not my_port.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(my_port, values='Adet', names='Kod', hole=0.4, title="Varlık Dağılımı")
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                fig_bar = px.bar(my_port, x='Kod', y='Adet', color='Kat', title="Miktar Bazlı Dağılım")
                st.plotly_chart(fig_bar, use_container_width=True)
        else: st.warning("Veri bulunamadı.")

    # --- 11. PORTFÖYÜM ---
    elif "PORTFÖYÜM" in menu:
        st.title("💼 Portföy Yönetimi")
        with st.form("ekle_v15"):
            c1, c2, c3 = st.columns(3)
            k = c1.text_input("Varlık Kodu (Örn: THYAO)").upper()
            m = c2.number_input("Maliyet", min_value=0.0)
            a = c3.number_input("Adet", min_value=0.0)
            cat = st.selectbox("Tür", ["Hisse", "Kripto", "Altın"])
            if st.form_submit_button("Sisteme Ekle"):
                new_row = pd.DataFrame([[st.session_state.u_data['Username'], k, k, m, a, cat]], columns=p_df.columns)
                pd.concat([p_df, new_row]).to_csv(PORT_DB, index=False)
                st.rerun()