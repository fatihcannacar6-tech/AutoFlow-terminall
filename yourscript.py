import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- 1. KURUMSAL TEMA VE YAPILANDIRMA ---
st.set_page_config(page_title="AKOSELL WMS | Kurumsal Portföy", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'IBM+Plex+Sans', sans-serif; background-color: #FBFBFC; }
    
    /* Kurumsal Renk Paleti: Lacivert - Gri - Beyaz */
    [data-testid="stSidebar"] { background-color: #0F172A !important; color: white !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    
    /* KPI Kartları */
    .kpi-card { background: #FFFFFF; padding: 25px; border-radius: 4px; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .kpi-label { color: #64748B; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-value { color: #0F172A; font-size: 24px; font-weight: 700; margin-top: 5px; }
    
    /* Tablo ve Editor */
    .stDataFrame { border: 1px solid #E2E8F0; border-radius: 4px; }
    
    /* Radio Button Özelleştirme */
    .stRadio div[role="radiogroup"] { gap: 4px !important; }
    .stRadio div[role="radiogroup"] label { background-color: transparent !important; border: none !important; padding: 10px 15px !important; border-radius: 4px !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #1E293B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERİ VE GÜVENLİK SİSTEMİ ---
USER_DB, PORT_DB, LOG_DB = "users_pro.csv", "portfolio_pro.csv", "audit_log.csv"

def init_db():
    if not os.path.exists(USER_DB):
        admin_pw = hashlib.sha256(str.encode("admin123")).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Yönetici", "Admin"]], columns=["Username", "Password", "Name", "Role"]).to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB):
        pd.DataFrame(columns=["Owner", "Kod", "Kat", "Adet", "Maliyet", "Sektor"]).to_csv(PORT_DB, index=False)
    if not os.path.exists(LOG_DB):
        pd.DataFrame(columns=["Zaman", "Kullanıcı", "İşlem", "Detay"]).to_csv(LOG_DB, index=False)

def add_log(user, action, detail):
    log = pd.read_csv(LOG_DB)
    new_log = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), user, action, detail]], columns=log.columns)
    pd.concat([log, new_log]).to_csv(LOG_DB, index=False)

init_db()

# --- 3. GİRİŞ KONTROLÜ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 0.8, 1])
    with col:
        st.markdown("<br><h2 style='text-align:center; color:#0F172A;'>AKOSELL <span style='font-weight:300; font-size:16px;'>TERMINAL</span></h2>", unsafe_allow_html=True)
        u = st.text_input("Kullanıcı Kimliği", key="u_key")
        p = st.text_input("Erişim Şifresi", type="password", key="p_key")
        if st.button("SİSTEME GİRİŞ", use_container_width=True):
            users = pd.read_csv(USER_DB)
            hp = hashlib.sha256(str.encode(p)).hexdigest()
            user_row = users[(users['Username']==u) & (users['Password']==hp)]
            if not user_row.empty:
                st.session_state.logged_in = True
                st.session_state.u_data = user_row.iloc[0].to_dict()
                add_log(u, "Giriş", "Başarılı oturum açma")
                st.rerun()
            else: st.error("Kimlik doğrulanamadı.")
else:
    # --- 4. KURUMSAL SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### {st.session_state.u_data['Name']}\n`{st.session_state.u_data['Role']}`")
        st.divider()
        menu = st.radio("NAVIGASYON", ["DASHBOARD", "PORTFÖY YÖNETİMİ", "RİSK ANALİZİ", "AUDIT LOG", "AYARLAR"])
        st.markdown("<br>"*5, unsafe_allow_html=True)
        if st.button("OTURUMU KAPAT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Verileri Çek
    p_df = pd.read_csv(PORT_DB)
    my_p = p_df[p_df['Owner'] == st.session_state.u_data['Username']].copy()

    # --- 5. DASHBOARD (EXECUTIVE SUMMARY) ---
    if menu == "DASHBOARD":
        st.title("🏛️ Executive Summary")
        
        if not my_p.empty:
            # Gerçek Zamanlı Veri (Simüle / yFinance)
            with st.spinner("Piyasa verileri konsolide ediliyor..."):
                my_p['Güncel'] = [yf.Ticker(f"{r['Kod']}.IS" if r['Kat']=="Hisse" else f"{r['Kod']}-USD").history(period="1d")['Close'].iloc[-1] for i, r in my_p.iterrows()]
                my_p['Değer'] = my_p['Güncel'] * my_p['Adet']
                my_p['Maliyet_T'] = my_p['Maliyet'] * my_p['Adet']
                my_p['Kar_Zarar'] = my_p['Değer'] - my_p['Maliyet_T']
                my_p['P_L_Yuzde'] = (my_p['Kar_Zarar'] / my_p['Maliyet_T']) * 100

            # KPI Kartları
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-label">Toplam Varlık</div><div class="kpi-value">₺{my_p["Değer"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            with c2: 
                kz = my_p["Kar_Zarar"].sum()
                color = "#10B981" if kz >= 0 else "#EF4444"
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">Net P/L</div><div class="kpi-value" style="color:{color}">₺{kz:,.2f}</div></div>', unsafe_allow_html=True)
            with c3:
                bist = yf.Ticker("XU100.IS").history(period="2d")
                b_chg = ((bist['Close'].iloc[-1] / bist['Close'].iloc[-2]) - 1) * 100
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">BIST 100</div><div class="kpi-value">{bist["Close"].iloc[-1]:,.0f} <small style="font-size:12px; color:#10B981">%{b_chg:.2f}</small></div></div>', unsafe_allow_html=True)
            with c4:
                risk = "DÜŞÜK" if len(my_p) > 5 else "YÜKSEK"
                st.markdown(f'<div class="kpi-card"><div class="kpi-label">Risk Skoru</div><div class="kpi-value">{risk}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Grafikler
            g1, g2 = st.columns([2, 1])
            with g1:
                st.subheader("Varlık Dağılım ve Performans")
                fig = px.bar(my_p, x='Kod', y='Değer', color='Kar_Zarar', color_continuous_scale='RdYlGn', text_auto='.2s')
                fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
                st.plotly_chart(fig, use_container_width=True)
            with g2:
                st.subheader("Sektörel Dağılım")
                fig_pie = px.pie(my_p, values='Değer', names='Sektor', hole=0.5)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Henüz portföy verisi bulunmuyor.")

    # --- 6. PORTFÖY YÖNETİMİ ---
    elif menu == "PORTFÖY YÖNETİMİ":
        st.title("💼 Kurumsal Portföy Yapılandırma")
        
        with st.expander("➕ Yeni Varlık Tanımla"):
            with st.form("ekle"):
                cc1, cc2, cc3, cc4, cc5 = st.columns(5)
                k = cc1.text_input("Varlık Kodu (Örn: THYAO)")
                kt = cc2.selectbox("Sınıf", ["Hisse", "Kripto", "Nakit"])
                ad = cc3.number_input("Adet", min_value=0.0)
                ml = cc4.number_input("Maliyet", min_value=0.0)
                sk = cc5.text_input("Sektör")
                if st.form_submit_button("SİSTEME KAYDET"):
                    new_data = pd.DataFrame([[st.session_state.u_data['Username'], k.upper(), kt, ad, ml, sk]], columns=p_df.columns)
                    pd.concat([p_df, new_data]).to_csv(PORT_DB, index=False)
                    add_log(st.session_state.u_data['Username'], "Varlık Ekleme", f"{k} eklendi")
                    st.rerun()

        st.subheader("Mevcut Pozisyonlar")
        edited = st.data_editor(my_p.drop(columns=['Owner']), num_rows="dynamic", use_container_width=True)
        if st.button("TÜM DEĞİŞİKLİKLERİ ONAYLA"):
            others = p_df[p_df['Owner'] != st.session_state.u_data['Username']]
            edited['Owner'] = st.session_state.u_data['Username']
            pd.concat([others, edited]).to_csv(PORT_DB, index=False)
            add_log(st.session_state.u_data['Username'], "Portföy Güncelleme", "Tablo üzerinden toplu düzenleme yapıldı")
            st.success("Veritabanı güncellendi.")

    # --- 7. RİSK ANALİZİ ---
    elif menu == "RİSK ANALİZİ":
        st.title("🛡️ Risk & Uyum Analizi")
        if not my_p.empty:
            my_p['Agirlik'] = (my_p['Maliyet'] * my_p['Adet'] / (my_p['Maliyet'] * my_p['Adet']).sum()) * 100
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Varlık Konsantrasyonu")
                # %25 Üzeri risk uyarısı
                for _, r in my_p.iterrows():
                    if r['Agirlik'] > 25:
                        st.error(f"⚠️ **{r['Kod']}** portföyün %{r['Agirlik']:.1f}'ini kapsıyor. (Limit: %25)")
                    else:
                        st.write(f"✅ {r['Kod']}: %{r['Agirlik']:.1f}")
            
            with c2:
                st.subheader("İstatistiksel Veriler")
                st.write(f"Toplam Pozisyon Sayısı: {len(my_p)}")
                st.write(f"Sektörel Çeşitlilik: {my_p['Sektor'].nunique()} farklı sektör")
        else:
            st.warning("Analiz için veri girişi yapılması gerekmektedir.")

    # --- 8. AUDIT LOG ---
    elif menu == "AUDIT LOG":
        st.title("🕵️ Audit Log (Denetim Geçmişi)")
        logs = pd.read_csv(LOG_DB)
        st.dataframe(logs.sort_values(by="Zaman", ascending=False), use_container_width=True)

    # --- 9. AYARLAR ---
    elif menu == "AYARLAR":
        st.title("⚙️ Sistem Ayarları")
        st.write(f"Kullanıcı: **{st.session_state.u_data['Name']}**")
        st.write(f"Yetki Seviyesi: **{st.session_state.u_data['Role']}**")
        if st.button("VERİLERİ TEMİZLE (AUDIT DAHİL)"):
            add_log(st.session_state.u_data['Username'], "Sıfırlama", "Tüm portföy silindi")
            others = p_df[p_df['Owner'] != st.session_state.u_data['Username']]
            others.to_csv(PORT_DB, index=False)
            st.rerun()