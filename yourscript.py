import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SAYFA VE LOGO ---
st.set_page_config(page_title="AKOSELL", layout="wide", page_icon="🏛️")

# --- 2. ÖZEL TASARIM (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    .user-profile { padding: 20px; background: #F8FAFC; border-radius: 12px; margin: 10px 15px 25px 15px; border: 1px solid #E2E8F0; text-align: center; }
    .stRadio div[role="radiogroup"] { gap: 8px !important; padding: 0 15px !important; }
    .stRadio div[role="radiogroup"] label { background-color: #F1F5F9 !important; border-radius: 10px !important; padding: 12px 16px !important; border: 1px solid #E2E8F0 !important; cursor: pointer; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #00D1FF !important; border-color: #00D1FF !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] p { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERİ TABANI ---
USER_DB, PORT_DB = "users_v14.csv", "portfolio_v14.csv"

def init_db():
    if not os.path.exists(USER_DB):
        admin_pw = hashlib.sha256(str.encode("admin123")).hexdigest()
        df = pd.DataFrame([["admin", admin_pw, "Yönetici", "admin@akosell.com", "Approved", "Admin"]], 
                          columns=["Username", "Password", "Name", "Email", "Status", "Role"])
        df.to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "Maliyet", "Adet", "Kat"]).to_csv(PORT_DB, index=False)

init_db()

# --- 4. GİRİŞ & KAYIT SİSTEMİ (KEY HATALARI DÜZELTİLDİ) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>AKOSELL</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["GİRİŞ", "KAYIT TALEBİ"])
        with tab1:
            u = st.text_input("Kullanıcı", key="login_u")
            p = st.text_input("Şifre", type="password", key="login_p")
            if st.button("SİSTEME GİRİŞ", use_container_width=True, type="primary"):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(p)).hexdigest()
                user = users[(users['Username']==u) & (users['Password']==hp)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.logged_in = True
                        st.session_state.u_data = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Kaydınız onay aşamasında.")
                else: st.error("Hatalı kullanıcı bilgileri.")
        with tab2:
            nu = st.text_input("Kullanıcı Adı", key="reg_u")
            nn = st.text_input("Ad Soyad", key="reg_n")
            ne = st.text_input("E-Posta", key="reg_e")
            np = st.text_input("Şifre Belirle", type="password", key="reg_p")
            if st.button("KAYIT TALEBİ GÖNDER", use_container_width=True):
                users = pd.read_csv(USER_DB)
                if nu in users['Username'].values: st.error("Bu kullanıcı adı zaten mevcut.")
                else:
                    new_u = pd.DataFrame([[nu, hashlib.sha256(str.encode(np)).hexdigest(), nn, ne, "Pending", "User"]], columns=users.columns)
                    pd.concat([users, new_u]).to_csv(USER_DB, index=False)
                    st.success("Talebiniz yöneticiye iletildi.")

else:
    # --- 5. SIDEBAR ---
    with st.sidebar:
        initial = st.session_state.u_data['Name'][0].upper()
        st.markdown(f'<div class="user-profile"><div style="width:50px; height:50px; background:#00D1FF; color:white; border-radius:50%; display:flex; align-items:center; justify-content:center; margin: 0 auto 10px; font-size:20px; font-weight:bold;">{initial}</div><div style="font-weight:800;">{st.session_state.u_data["Name"].upper()}</div><small>{st.session_state.u_data["Role"]}</small></div>', unsafe_allow_html=True)
        
        menu_items = ["📊 DASHBOARD", "💼 PORTFÖYÜM", "📈 ANALİZLER", "📰 HABERLER", "⚙️ AYARLAR"]
        if st.session_state.u_data['Role'] == "Admin": menu_items.append("🔐 YÖNETİCİ PANELİ")
        menu = st.radio("MENÜ", menu_items, label_visibility="collapsed")
        
        if st.button("ÇIKIŞ YAP", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    p_df = pd.read_csv(PORT_DB)
    my_p = p_df[p_df['Owner'] == st.session_state.u_data['Username']]

    # --- 6. DASHBOARD ---
    if menu == "📊 DASHBOARD":
        st.title("📊 Portföy Özeti")
        if not my_p.empty:
            # Fiyatları Çekme
            current_prices = []
            for _, r in my_p.iterrows():
                try:
                    sym = f"{r['Kod']}.IS" if r['Kat'] == "Hisse" else f"{r['Kod']}-USD"
                    val = yf.Ticker(sym).history(period="1d")['Close'].iloc[-1]
                    current_prices.append(val)
                except: current_prices.append(r['Maliyet'])
            
            my_p['Güncel'] = current_prices
            my_p['Değer'] = my_p['Güncel'] * my_p['Adet']
            my_p['Maliyet_T'] = my_p['Maliyet'] * my_p['Adet']
            my_p['Kar_Zarar'] = my_p['Değer'] - my_p['Maliyet_T']

            c1, c2, c3 = st.columns(3)
            c1.metric("TOPLAM VARLIK", f"₺{my_p['Değer'].sum():,.2f}")
            c2.metric("TOPLAM KAR/ZARAR", f"₺{my_p['Kar_Zarar'].sum():,.2f}", delta=f"{(my_p['Kar_Zarar'].sum()/my_p['Maliyet_T'].sum()*100):.2f}%")
            c3.metric("YATIRIM MİKTARI", f"₺{my_p['Maliyet_T'].sum():,.2f}")

            st.dataframe(my_p.drop(columns=['Owner']), use_container_width=True)
        else: st.info("Henüz varlık eklemediniz.")

    # --- 7. DETAYLI ANALİZ (RESİMDEKİ GİBİ) ---
    elif menu == "📈 ANALİZLER":
        st.title("📈 Stratejik Varlık Analizi")
        if not my_p.empty:
            my_p['Değer'] = my_p['Maliyet'] * my_p['Adet'] # Örnek hesaplama
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Varlık Dağılım Oranları")
                fig_pie = px.pie(my_p, values='Değer', names='Kod', hole=0.5, color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("Kategori Bazlı Analiz")
                fig_bar = px.bar(my_p.groupby('Kat')['Değer'].sum().reset_index(), x='Kat', y='Değer', color='Kat', text_auto='.2s')
                st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("Varlık Performans Matrisi")
            # Detaylı Analiz Tablosu
            analysis_df = my_p.copy()
            analysis_df['Ağırlık (%)'] = (analysis_df['Değer'] / analysis_df['Değer'].sum() * 100).round(2)
            st.table(analysis_df[['Kod', 'Kat', 'Adet', 'Maliyet', 'Değer', 'Ağırlık (%)']])
        else: st.warning("Veri bulunamadı.")

    # --- 8. AYARLAR (İSTENEN SADELEŞTİRME) ---
    elif menu == "⚙️ AYARLAR":
        st.title("⚙️ Ayarlar")
        u_df = pd.read_csv(USER_DB)
        
        with st.expander("👤 Kullanıcı Adı ve Şifre Değiştir"):
            new_un = st.text_input("Yeni Kullanıcı Adı", value=st.session_state.u_data['Username'])
            new_pw = st.text_input("Yeni Şifre", type="password")
            if st.button("GÜNCELLE"):
                idx = u_df[u_df['Username'] == st.session_state.u_data['Username']].index
                u_df.loc[idx, 'Username'] = new_un
                if new_pw:
                    u_df.loc[idx, 'Password'] = hashlib.sha256(str.encode(new_pw)).hexdigest()
                u_df.to_csv(USER_DB, index=False)
                st.success("Bilgiler güncellendi. Lütfen tekrar giriş yapın.")
                st.session_state.logged_in = False
                st.rerun()

        if st.button("🗑️ TÜM VERİLERİ SIFIRLA", use_container_width=True):
            p_all = pd.read_csv(PORT_DB)
            p_all = p_all[p_all['Owner'] != st.session_state.u_data['Username']]
            p_all.to_csv(PORT_DB, index=False)
            st.warning("Portföyünüz tamamen temizlendi.")
            st.rerun()

    # --- 9. YÖNETİCİ PANELİ ---
    elif menu == "🔐 YÖNETİCİ PANELİ":
        st.title("🔐 Kayıt Onayları")
        u_df = pd.read_csv(USER_DB)
        pending = u_df[u_df['Status'] == "Pending"]
        if not pending.empty:
            for i, r in pending.iterrows():
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{r['Name']}** (@{r['Username']})")
                if c2.button("ONAYLA", key=f"ok_{i}"):
                    u_df.loc[u_df['Username'] == r['Username'], 'Status'] = "Approved"
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
                if c3.button("REDDET", key=f"no_{i}"):
                    u_df = u_df[u_df['Username'] != r['Username']]
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
        else: st.info("Bekleyen talep yok.")
    
    # --- PORTFÖYÜM ---
    elif menu == "💼 PORTFÖYÜM":
        st.title("💼 Portföy Yönetimi")
        with st.form("ekle_v"):
            c1, c2, c3, c4 = st.columns(4)
            k = c1.text_input("Varlık Kodu").upper()
            m = c2.number_input("Maliyet", min_value=0.0)
            a = c3.number_input("Adet", min_value=0.0)
            kat = c4.selectbox("Tür", ["Hisse", "Kripto"])
            if st.form_submit_button("EKLE"):
                new_row = pd.DataFrame([[st.session_state.u_data['Username'], k, m, a, kat]], columns=p_df.columns)
                pd.concat([p_df, new_row]).to_csv(PORT_DB, index=False)
                st.success("Eklendi.")
                st.rerun()
        
        st.divider()
        st.subheader("Varlıkları Düzenle/Sil")
        edited_df = st.data_editor(my_p.drop(columns=['Owner']), num_rows="dynamic")
        if st.button("DEĞİŞİKLİKLERİ KAYDET"):
            others = p_df[p_df['Owner'] != st.session_state.u_data['Username']]
            edited_df['Owner'] = st.session_state.u_data['Username']
            pd.concat([others, edited_df]).to_csv(PORT_DB, index=False)
            st.success("Kaydedildi.")
            st.rerun()