import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="AKOSELL", layout="wide", page_icon="🏛️")

# --- 2. ÖZEL CSS TASARIMI ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    .user-profile { padding: 20px; background: #F8FAFC; border-radius: 12px; margin: 10px 15px 25px 15px; border: 1px solid #E2E8F0; text-align: center; }
    [data-testid="stSidebarNav"] { display: none; }
    .stRadio div[role="radiogroup"] { gap: 8px !important; padding: 0 15px !important; }
    .stRadio div[role="radiogroup"] label { background-color: #F1F5F9 !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; padding: 12px 16px !important; width: 100% !important; display: flex !important; align-items: center !important; cursor: pointer; }
    .stRadio div[role="radiogroup"] label [data-testid="stStyleTypeDefault"] { display: none !important; }
    .stRadio div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p { color: #1E293B !important; font-size: 14px !important; font-weight: 700 !important; margin: 0 !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #00D1FF !important; border-color: #00D1FF !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] p { color: #FFFFFF !important; }
    .metric-container { background: white; padding: 20px; border-radius: 15px; border: 1px solid #E2E8F0; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERİ SİSTEMİ ---
USER_DB, PORT_DB = "users_final_v2.csv", "portfolio_final_v2.csv"

def init_db():
    if not os.path.exists(USER_DB):
        admin_pw = hashlib.sha256(str.encode("admin123")).hexdigest()
        df = pd.DataFrame([["admin", admin_pw, "Yönetici", "admin@akosell.com", "Approved", "Admin"]], 
                          columns=["Username", "Password", "Name", "Email", "Status", "Role"])
        df.to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "Maliyet", "Adet", "Kat"]).to_csv(PORT_DB, index=False)

init_db()

# --- 4. GİRİŞ VE KAYIT SİSTEMİ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center; color:#1E293B;'>AKOSELL</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["GİRİŞ", "KAYIT TALEBİ"])
        with tab1:
            u = st.text_input("Kullanıcı")
            p = st.text_input("Şifre", type="password")
            if st.button("GİRİŞ YAP", use_container_width=True, type="primary"):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(p)).hexdigest()
                user = users[(users['Username']==u) & (users['Password']==hp)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.logged_in = True
                        st.session_state.u_data = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Kaydınız onay bekliyor.")
                else: st.error("Hatalı bilgiler.")
        with tab2:
            nu, nn, ne, np = st.text_input("Kullanıcı Adı"), st.text_input("Ad Soyad"), st.text_input("Email"), st.text_input("Şifre", type="password")
            if st.button("TALEBİ GÖNDER", use_container_width=True):
                users = pd.read_csv(USER_DB)
                if nu in users['Username'].values: st.error("Kullanıcı adı alınmış.")
                else:
                    new_u = pd.DataFrame([[nu, hashlib.sha256(str.encode(np)).hexdigest(), nn, ne, "Pending", "User"]], columns=users.columns)
                    pd.concat([users, new_u]).to_csv(USER_DB, index=False)
                    st.success("Talebiniz yöneticiye iletildi.")

else:
    # --- 5. SIDEBAR ---
    with st.sidebar:
        st.markdown(f"""<div class="user-profile"><small style="color:#64748B;">{st.session_state.u_data['Role']}</small><div style="font-size:18px; font-weight:800; color:#1E293B;">{st.session_state.u_data['Name'].upper()}</div><div style="color:#00D1FF; font-size:11px; font-weight:700;">AKOSELL WMS</div></div>""", unsafe_allow_html=True)
        menu_items = ["📊 DASHBOARD", "💼 PORTFÖYÜM", "📈 ANALİZLER", "📰 HABERLER", "⚙️ AYARLAR"]
        if st.session_state.u_data['Role'] == "Admin": menu_items.append("🔐 YÖNETİCİ PANELİ")
        menu = st.radio("NAV", menu_items, label_visibility="collapsed")
        if st.button("GÜVENLİ ÇIKIŞ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- YARDIMCI VERİ ÇEKME ---
    def get_data(symbol, kat):
        try:
            s = f"{symbol}.IS" if kat == "Hisse" else f"{symbol}-USD"
            t = yf.Ticker(s)
            return t.history(period="1d")['Close'].iloc[-1]
        except: return 0

    p_df = pd.read_csv(PORT_DB)
    my_p = p_df[p_df['Owner'] == st.session_state.u_data['Username']]

    # --- 6. DASHBOARD ---
    if menu == "📊 DASHBOARD":
        st.title("📊 Stratejik Varlık Analizi")
        if not my_p.empty:
            my_p['Current'] = [get_data(r['Kod'], r['Kat']) for i, r in my_p.iterrows()]
            my_p['Total_Cost'] = my_p['Maliyet'] * my_p['Adet']
            my_p['Total_Value'] = my_p['Current'] * my_p['Adet']
            my_p['PL'] = my_p['Total_Value'] - my_p['Total_Cost']
            
            c1, c2, c3 = st.columns(3)
            c1.metric("TOPLAM YATIRIM", f"₺{my_p['Total_Cost'].sum():,.2f}")
            c2.metric("PORTFÖY DEĞERİ", f"₺{my_p['Total_Value'].sum():,.2f}", delta=f"{my_p['PL'].sum():,.2f}")
            c3.metric("VARLIK SAYISI", len(my_p))
            st.dataframe(my_p.drop(columns=['Owner']), use_container_width=True, hide_index=True)
        else: st.info("Portföy boş.")

    # --- 7. DETAYLI ANALİZLER ---
    elif menu == "📈 ANALİZLER":
        st.title("📈 Detaylı Portföy Analitiği")
        if not my_p.empty:
            my_p['Current'] = [get_data(r['Kod'], r['Kat']) for i, r in my_p.iterrows()]
            my_p['Total_Value'] = my_p['Current'] * my_p['Adet']
            
            col1, col2 = st.columns(2)
            with col1:
                # Varlık Dağılımı Pastası
                fig1 = px.pie(my_p, values='Total_Value', names='Kod', hole=0.4, title="Varlık Dağılım Oranları (%)", color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Kategori Bazlı Dağılım
                fig2 = px.bar(my_p.groupby('Kat')['Total_Value'].sum().reset_index(), x='Kat', y='Total_Value', title="Kategori Bazlı Portföy Büyüklüğü", color='Kat', color_discrete_map={'Hisse':'#00D1FF', 'Kripto':'#FFB800'})
                st.plotly_chart(fig2, use_container_width=True)

            st.divider()
            
            # Risk ve Performans Tablosu
            st.subheader("🎯 Performans Metrikleri")
            perf_df = my_p.copy()
            perf_df['Ağırlık'] = (perf_df['Total_Value'] / perf_df['Total_Value'].sum() * 100).round(2)
            perf_df['Verimlilik'] = ((perf_df['Current'] / perf_df['Maliyet'] - 1) * 100).round(2)
            
            st.table(perf_df[['Kod', 'Kat', 'Ağırlık', 'Verimlilik']].sort_values(by='Ağırlık', ascending=False))
        else: st.warning("Analiz için veri ekleyin.")

    # --- 8. HABERLER ---
    elif menu == "📰 HABERLER":
        st.title("📰 Finansal Gündem")
        news_items = [
            {"title": "Borsa İstanbul'da Hareketlilik Sürüyor", "source": "AKOSELL Finans", "time": "10 dk önce"},
            {"title": "Kripto Varlıklarda Yeni Düzenleme Beklentisi", "source": "Analiz Merkezi", "time": "45 dk önce"},
            {"title": "Global Piyasalarda Faiz Kararı Bekleniyor", "source": "Bloomberg HT", "time": "2 saat önce"}
        ]
        for n in news_items:
            with st.container():
                st.markdown(f"""<div style='padding:15px; border-radius:10px; border:1px solid #E2E8F0; margin-bottom:10px;'>
                <h4 style='margin:0;'>{n['title']}</h4>
                <small style='color:#64748B;'>{n['source']} • {n['time']}</small>
                </div>""", unsafe_allow_html=True)

    # --- 9. AYARLAR ---
    elif menu == "⚙️ AYARLAR":
        st.title("⚙️ Hesap ve Terminal Ayarları")
        with st.expander("👤 Profil Bilgilerini Güncelle"):
            new_name = st.text_input("Görünen İsim", value=st.session_state.u_data['Name'])
            if st.button("GÜNCELLE"):
                u_df = pd.read_csv(USER_DB)
                u_df.loc[u_df['Username'] == st.session_state.u_data['Username'], 'Name'] = new_name
                u_df.to_csv(USER_DB, index=False)
                st.session_state.u_data['Name'] = new_name
                st.success("Profil güncellendi!")
                st.rerun()

        with st.expander("🔐 Güvenlik"):
            st.text_input("Yeni Şifre", type="password")
            st.button("ŞİFREYİ DEĞİŞTİR")

        st.divider()
        if st.button("🗑️ TÜM PORTFÖYÜ SIFIRLA", use_container_width=True):
            others = p_df[p_df['Owner'] != st.session_state.u_data['Username']]
            others.to_csv(PORT_DB, index=False)
            st.success("Tüm veriler temizlendi.")
            st.rerun()

    # --- 10. YÖNETİCİ PANELİ ---
    elif menu == "🔐 YÖNETİCİ PANELİ":
        st.title("🔐 Bekleyen Kayıt Onayları")
        u_df = pd.read_csv(USER_DB)
        pending = u_df[u_df['Status'] == "Pending"]
        if not pending.empty:
            for i, r in pending.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f"**{r['Name']}** ({r['Username']})")
                if col2.button("ONAYLA", key=f"app_{i}"):
                    u_df.loc[u_df['Username'] == r['Username'], 'Status'] = "Approved"
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
                if col3.button("REDDET", key=f"rej_{i}"):
                    u_df = u_df[u_df['Username'] != r['Username']]
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
        else: st.info("Onay bekleyen talep yok.")

    # --- PORTFÖYÜM ---
    elif menu == "💼 PORTFÖYÜM":
        st.title("💼 Varlık Yönetimi")
        with st.form("add_v"):
            c1, c2, c3, c4 = st.columns(4)
            k = c1.text_input("Varlık Kodu (THYAO, BTC)").upper()
            m = c2.number_input("Maliyet", min_value=0.0)
            a = c3.number_input("Adet", min_value=0.0)
            kat = c4.selectbox("Kategori", ["Hisse", "Kripto"])
            if st.form_submit_button("EKLE"):
                new_r = pd.DataFrame([[st.session_state.u_data['Username'], k, m, a, kat]], columns=p_df.columns)
                pd.concat([p_df, new_r]).to_csv(PORT_DB, index=False)
                st.rerun()
        st.divider()
        st.write("### Varlık Listesi")
        st.data_editor(my_p.drop(columns=['Owner']), use_container_width=True)