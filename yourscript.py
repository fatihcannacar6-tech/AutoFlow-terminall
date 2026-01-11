import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
from datetime import datetime
import numpy as np

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="AKOSELL", layout="wide", page_icon="🏛️")

# --- 2. CSS TASARIM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    .user-profile { padding: 20px; background: #F8FAFC; border-radius: 12px; margin: 10px 15px 25px 15px; border: 1px solid #E2E8F0; text-align: center; }
    [data-testid="stSidebarNav"] { display: none; }
    .stRadio div[role="radiogroup"] { gap: 8px !important; padding: 0 15px !important; }
    .stRadio div[role="radiogroup"] label { background-color: #F1F5F9 !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; padding: 12px 16px !important; width: 100% !important; cursor: pointer !important; display: flex !important; align-items: center !important; transition: all 0.2s ease; }
    .stRadio div[role="radiogroup"] label [data-testid="stStyleTypeDefault"] { display: none !important; }
    .stRadio div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p { color: #1E293B !important; font-size: 14px !important; font-weight: 700 !important; margin: 0 !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #00D1FF !important; border-color: #00D1FF !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] p { color: #FFFFFF !important; }
    .sidebar-footer { position: fixed; bottom: 20px; width: 270px; padding: 0 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERİ SİSTEMİ ---
USER_DB, PORT_DB = "users_v13.csv", "portfolio_v13.csv"

def init_db():
    if not os.path.exists(USER_DB):
        # Varsayılan admin hesabı oluştur (Şifre: admin123)
        admin_pw = hashlib.sha256(str.encode("admin123")).hexdigest()
        df = pd.DataFrame([["admin", admin_pw, "Yönetici", "admin@akosell.com", "Approved", "Admin"]], 
                          columns=["Username", "Password", "Name", "Email", "Status", "Role"])
        df.to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "YF_Kod", "Maliyet", "Adet", "Kat"]).to_csv(PORT_DB, index=False)

init_db()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 4. GİRİŞ VE KAYIT SİSTEMİ ---
if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown("<br><h1 style='text-align:center;'>AKOSELL</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["GİRİŞ YAP", "KAYIT OL"])
        
        with tab1:
            u = st.text_input("Kullanıcı")
            p = st.text_input("Şifre", type="password")
            if st.button("SİSTEME GİRİŞ", use_container_width=True, type="primary"):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(p)).hexdigest()
                user_match = users[(users['Username']==u) & (users['Password']==hp)]
                
                if not user_match.empty:
                    user_status = user_match.iloc[0]['Status']
                    if user_status == "Approved":
                        st.session_state.logged_in = True
                        st.session_state.u_data = user_match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.warning("Hesabınız henüz onaylanmamış. Lütfen yöneticinin onaylamasını bekleyin.")
                else:
                    st.error("Kullanıcı adı veya şifre hatalı.")
        
        with tab2:
            new_user = st.text_input("Yeni Kullanıcı Adı")
            new_name = st.text_input("Ad Soyad")
            new_email = st.text_input("E-Posta")
            new_pw = st.text_input("Şifre Belirle", type="password")
            if st.button("KAYIT TALEBİ GÖNDER", use_container_width=True):
                users = pd.read_csv(USER_DB)
                if new_user in users['Username'].values:
                    st.error("Bu kullanıcı adı zaten alınmış.")
                elif len(new_pw) < 4:
                    st.error("Şifre çok kısa.")
                else:
                    hp = hashlib.sha256(str.encode(new_pw)).hexdigest()
                    new_entry = pd.DataFrame([[new_user, hp, new_name, new_email, "Pending", "User"]], columns=users.columns)
                    pd.concat([users, new_entry]).to_csv(USER_DB, index=False)
                    st.success("Talebiniz alındı! Yönetici onayından sonra giriş yapabilirsiniz.")

else:
    # --- 5. SIDEBAR ---
    with st.sidebar:
        st.markdown(f"""<div class="user-profile"><small style="color:#64748B;">{st.session_state.u_data['Role'].upper()}</small><div style="font-size:18px; font-weight:800; color:#1E293B;">{st.session_state.u_data['Name'].upper()}</div><div style="color:#00D1FF; font-size:11px; font-weight:700;">PREMIUM PLUS</div></div>""", unsafe_allow_html=True)
        
        menu_items = ["📊 DASHBOARD", "💼 PORTFÖYÜM", "📈 ANALİZLER", "📅 TAKVİM", "📰 HABERLER", "⚙️ AYARLAR"]
        # Eğer admin ise menüye YÖNETİCİ PANELİ ekle
        if st.session_state.u_data['Role'] == "Admin":
            menu_items.append("🔐 YÖNETİCİ PANELİ")
            
        menu = st.radio("NAV", menu_items, label_visibility="collapsed")
        
        st.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)
        if st.button("ÇIKIŞ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. YARDIMCI FONKSİYONLAR ---
    def get_single_price(symbol, kat):
        try:
            ticker_map = {"Hisse": f"{symbol}.IS", "Kripto": f"{symbol}-USD"}
            ticker_name = ticker_map.get(kat, symbol)
            data = yf.Ticker(ticker_name).history(period="1d")
            return float(data['Close'].iloc[-1]) if not data.empty else 0.0
        except: return 0.0

    df_port = pd.read_csv(PORT_DB)
    my_port = df_port[df_port['Owner'] == st.session_state.u_data['Username']]

    # --- SAYFA İÇERİKLERİ ---
    if menu == "📊 DASHBOARD":
        st.title("📊 Stratejik Varlık Analizi")
        if not my_port.empty:
            with st.spinner('Veriler güncelleniyor...'):
                display_df = my_port.copy()
                prices = [get_single_price(r['Kod'], r['Kat']) for i, r in display_df.iterrows()]
                display_df['Güncel Fiyat'] = [p if p > 0 else r['Maliyet'] for p, (i, r) in zip(prices, display_df.iterrows())]
                display_df['Toplam Maliyet'] = display_df['Maliyet'] * display_df['Adet']
                display_df['Toplam Değer'] = display_df['Güncel Fiyat'] * display_df['Adet']
                display_df['Kâr/Zarar'] = display_df['Toplam Değer'] - display_df['Toplam Maliyet']
                t_cost = display_df['Toplam Maliyet'].sum()
                t_value = display_df['Toplam Değer'].sum()
                t_profit = t_value - t_cost
                p_ratio = (t_profit / t_cost * 100) if t_cost > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("TOPLAM YATIRIM", f"₺{t_cost:,.2f}")
            c2.metric("NET KÂR / ZARAR", f"₺{t_profit:,.2f}", delta=f"{p_ratio:.2f}%")
            c3.metric("PORTFÖY DEĞERİ", f"₺{t_value:,.2f}")
            st.dataframe(display_df[["Kod", "Kat", "Adet", "Maliyet", "Güncel Fiyat", "Kâr/Zarar"]], use_container_width=True, hide_index=True)
        else: st.info("Portföyünüzde henüz varlık bulunmuyor.")

    elif menu == "💼 PORTFÖYÜM":
        st.title("💼 Portföy Yönetimi")
        t1, t2 = st.tabs(["VARLIK EKLE", "DÜZENLE/SİL"])
        with t1:
            with st.form("add_form"):
                c1, c2, c3 = st.columns(3)
                k = c1.text_input("Varlık Kodu (Örn: THYAO, BTC)").upper()
                m = c2.number_input("Birim Maliyet", min_value=0.0)
                a = c3.number_input("Adet", min_value=0.0)
                cat = st.selectbox("Tür", ["Hisse", "Kripto", "Altın", "Döviz"])
                if st.form_submit_button("LİSTEYE EKLE"):
                    new_row = pd.DataFrame([[st.session_state.u_data['Username'], k, k, m, a, cat]], columns=df_port.columns)
                    pd.concat([df_port, new_row]).to_csv(PORT_DB, index=False)
                    st.success("Varlık başarıyla eklendi.")
                    st.rerun()
        with t2:
            edited = st.data_editor(my_port[["Kod", "Maliyet", "Adet", "Kat"]], num_rows="dynamic", use_container_width=True)
            if st.button("DEĞİŞİKLİKLERİ UYGULA"):
                others = df_port[df_port['Owner'] != st.session_state.u_data['Username']]
                edited['Owner'] = st.session_state.u_data['Username']
                edited['YF_Kod'] = edited['Kod']
                pd.concat([others, edited]).to_csv(PORT_DB, index=False)
                st.success("Portföy güncellendi.")
                st.rerun()

    elif menu == "🔐 YÖNETİCİ PANELİ":
        st.title("🔐 Üyelik Onay Merkezi")
        u_df = pd.read_csv(USER_DB)
        pending_users = u_df[u_df['Status'] == "Pending"]
        
        if pending_users.empty:
            st.info("Onay bekleyen herhangi bir kayıt talebi bulunmuyor.")
        else:
            st.subheader(f"Bekleyen Talepler ({len(pending_users)})")
            for idx, row in pending_users.iterrows():
                with st.expander(f"Talep: {row['Name']} (@{row['Username']})"):
                    st.write(f"**E-Posta:** {row['Email']}")
                    col_onay, col_red, _ = st.columns([1, 1, 3])
                    
                    if col_onay.button("ONAYLA", key=f"app_{row['Username']}"):
                        u_df.loc[u_df['Username'] == row['Username'], 'Status'] = 'Approved'
                        u_df.to_csv(USER_DB, index=False)
                        st.success(f"{row['Username']} onaylandı!")
                        st.rerun()
                        
                    if col_red.button("REDDET", key=f"rej_{row['Username']}"):
                        u_df = u_df[u_df['Username'] != row['Username']]
                        u_df.to_csv(USER_DB, index=False)
                        st.error(f"{row['Username']} talebi silindi.")
                        st.rerun()

    # Diğer bölümler (Analizler, Takvim vb.) mevcut kodunuzdaki gibi devam eder...
    elif menu == "⚙️ AYARLAR":
        st.title("⚙️ Ayarlar")
        st.info("Profil ve şifre güncelleme işlemleri buradan yapılır.")