import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="AKOSELL WMS", layout="wide", page_icon="🏛️")

# --- 2. GELİŞMİŞ UI TASARIMI (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    .user-profile { padding: 20px; background: #F8FAFC; border-radius: 12px; margin: 10px 15px 25px 15px; border: 1px solid #E2E8F0; text-align: center; }
    [data-testid="stSidebarNav"] { display: none; }
    .stRadio div[role="radiogroup"] { gap: 8px !important; padding: 0 15px !important; }
    .stRadio div[role="radiogroup"] label { background-color: #F1F5F9 !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; padding: 12px 16px !important; width: 100% !important; cursor: pointer !important; display: flex !important; align-items: center !important; }
    .stRadio div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p { color: #1E293B !important; font-size: 14px !important; font-weight: 700 !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #00D1FF !important; border-color: #00D1FF !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] p { color: #FFFFFF !important; }
    .metric-card { background: white; padding: 20px; border-radius: 15px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
    .stExpander { border: none !important; box-shadow: none !important; background: #F8FAFC !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERİ SİSTEMİ ---
USER_DB, PORT_DB, HISTORY_DB = "users_v26.csv", "portfolio_v26.csv", "history_v26.csv"

def init_db():
    for db, cols in zip([USER_DB, PORT_DB, HISTORY_DB], 
                        [["Username", "Password", "Name", "Email", "Status", "Role"],
                         ["Owner", "Kod", "Maliyet", "Adet", "Kat", "Sektor"],
                         ["Owner", "Tarih", "Kod", "Tip", "Adet", "Fiyat"]]):
        if not os.path.exists(db):
            if db == USER_DB:
                admin_pw = hashlib.sha256(str.encode("admin123")).hexdigest()
                pd.DataFrame([["admin", admin_pw, "Yönetici", "admin@akosell.com", "Approved", "Admin"]], columns=cols).to_csv(db, index=False)
            else:
                pd.DataFrame(columns=cols).to_csv(db, index=False)

init_db()

# --- 4. YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=600)
def fetch_live_data(symbol, kat):
    try:
        s = f"{symbol}.IS" if kat == "Hisse" else (f"{symbol}-USD" if kat == "Kripto" else symbol)
        t = yf.Ticker(s)
        hist = t.history(period="2d")
        curr = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        change = ((curr - prev) / prev) * 100
        return round(curr, 2), round(change, 2)
    except: return 0.0, 0.0

# --- 5. AUTH SİSTEMİ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<h1 style='text-align:center;'>AKOSELL</h1>", unsafe_allow_html=True)
        tab_in, tab_up = st.tabs(["GİRİŞ", "KAYIT"])
        with tab_in:
            u = st.text_input("Kullanıcı", key="li_u")
            p = st.text_input("Şifre", type="password", key="li_p")
            if st.button("SİSTEME GİRİŞ", use_container_width=True, type="primary"):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(str.encode(p)).hexdigest()
                user = users[(users['Username']==u) & (users['Password']==hp)]
                if not user.empty and user.iloc[0]['Status'] == "Approved":
                    st.session_state.logged_in, st.session_state.u_data = True, user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Hatalı giriş veya onaylanmamış hesap.")
        with tab_up:
            nu, nn, ne, npw = st.text_input("Kullanıcı Adı", key="re_u"), st.text_input("Ad Soyad", key="re_n"), st.text_input("E-Posta", key="re_e"), st.text_input("Şifre", type="password", key="re_p")
            if st.button("KAYIT OL", use_container_width=True):
                db = pd.read_csv(USER_DB)
                if nu in db['Username'].values: st.error("Kullanıcı adı alınmış.")
                else:
                    new_u = pd.DataFrame([[nu, hashlib.sha256(str.encode(npw)).hexdigest(), nn, ne, "Pending", "User"]], columns=db.columns)
                    pd.concat([db, new_u]).to_csv(USER_DB, index=False); st.success("Talep gönderildi.")

else:
    # --- 6. SIDEBAR NAV ---
    with st.sidebar:
        st.markdown(f"""<div class="user-profile"><small>AKOSELL WMS</small><div style="font-size:18px; font-weight:800;">{st.session_state.u_data['Name'].upper()}</div><div style="color:#00D1FF; font-size:11px; font-weight:700;">PRO TERMINAL</div></div>""", unsafe_allow_html=True)
        menu = st.radio("NAV", ["📊 DASHBOARD", "💼 PORTFÖYÜM", "📈 ANALİZLER", "📅 TAKVİM", "📰 HABERLER", "⚙️ AYARLAR"], label_visibility="collapsed")
        if st.button("GÜVENLİ ÇIKIŞ", use_container_width=True): st.session_state.logged_in = False; st.rerun()

    p_df = pd.read_csv(PORT_DB)
    my_p = p_df[p_df['Owner'] == st.session_state.u_data['Username']].copy()

    # --- 7. DASHBOARD (BENCHMARK & ÖZET) ---
    if menu == "📊 DASHBOARD":
        st.title("📊 Finansal Özet")
        if not my_p.empty:
            with st.spinner("Canlı veriler işleniyor..."):
                results = [fetch_live_data(r['Kod'], r['Kat']) for i, r in my_p.iterrows()]
                my_p['Güncel'], my_p['Değişim'] = [res[0] for res in results], [res[1] for res in results]
                my_p['Değer'] = my_p['Güncel'] * my_p['Adet']
                my_p['Maliyet_T'] = my_p['Maliyet'] * my_p['Adet']
                my_p['Net_PL'] = my_p['Değer'] - my_p['Maliyet_T']
            
            # Üst Metrikler
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PORTFÖY DEĞERİ", f"₺{my_p['Değer'].sum():,.2f}")
            c2.metric("TOPLAM K/Z", f"₺{my_p['Net_PL'].sum():,.2f}", f"{((my_p['Değer'].sum()/my_p['Maliyet_T'].sum()-1)*100):.2f}%")
            
            # Benchmark (BIST100 Karşılaştırma)
            bist_price, bist_chg = fetch_live_data("XU100", "Hisse")
            c3.metric("BIST 100", f"{bist_price:,.0f}", f"{bist_chg}%")
            
            # Günlük Kar/Zarar Tahmini
            daily_pl = (my_p['Değer'] * (my_p['Değişim']/100)).sum()
            c4.metric("GÜNLÜK DEĞİŞİM", f"₺{daily_pl:,.2f}", f"{(daily_pl/my_p['Değer'].sum()*100):.2f}%")

            st.divider()
            col_l, col_r = st.columns([2, 1])
            with col_l:
                st.subheader("Varlık Listesi")
                st.dataframe(my_p[['Kod', 'Kat', 'Adet', 'Maliyet', 'Güncel', 'Değişim', 'Net_PL']], use_container_width=True, hide_index=True)
            with col_r:
                st.subheader("Performans Liderleri")
                st.table(my_p.sort_values(by='Değişim', ascending=False)[['Kod', 'Değişim']].head(3))
        else: st.info("Veri girişi yapın.")

    # --- 8. PORTFÖYÜM (İŞLEM GEÇMİŞİ & YÖNETİM) ---
    elif menu == "💼 PORTFÖYÜM":
        st.title("💼 Varlık ve İşlem Yönetimi")
        t_add, t_hist = st.tabs(["YENİ İŞLEM", "GEÇMİŞ"])
        
        with t_add:
            with st.form("trade"):
                c1, c2, c3, c4 = st.columns(4)
                tk, tt = c1.text_input("Kod").upper(), c2.selectbox("İşlem", ["ALIM", "SATIM"])
                ta, tf = c3.number_input("Adet", min_value=0.01), c4.number_input("Fiyat")
                tcat, tsek = st.selectbox("Kategori", ["Hisse", "Kripto", "Emtia"]), st.text_input("Sektör (Opsiyonel)")
                if st.form_submit_button("İŞLEMİ ONAYLA"):
                    # Portföyü Güncelle
                    if tt == "ALIM":
                        if tk in my_p['Kod'].values:
                            idx = p_df[(p_df['Owner']==st.session_state.u_data['Username']) & (p_df['Kod']==tk)].index
                            old_a, old_m = p_df.loc[idx, 'Adet'].values[0], p_df.loc[idx, 'Maliyet'].values[0]
                            new_a = old_a + ta
                            new_m = ((old_a * old_m) + (ta * tf)) / new_a
                            p_df.loc[idx, 'Adet'], p_df.loc[idx, 'Maliyet'] = new_a, new_m
                        else:
                            new_row = pd.DataFrame([[st.session_state.u_data['Username'], tk, tf, ta, tcat, tsek]], columns=p_df.columns)
                            p_df = pd.concat([p_df, new_row])
                    p_df.to_csv(PORT_DB, index=False)
                    
                    # Geçmişe Yaz
                    h_df = pd.read_csv(HISTORY_DB)
                    h_new = pd.DataFrame([[st.session_state.u_data['Username'], datetime.now().date(), tk, tt, ta, tf]], columns=h_df.columns)
                    pd.concat([h_df, h_new]).to_csv(HISTORY_DB, index=False)
                    st.success("İşlem kaydedildi."); st.rerun()
        
        with t_hist:
            h_df = pd.read_csv(HISTORY_DB)
            st.dataframe(h_df[h_df['Owner'] == st.session_state.u_data['Username']].sort_values(by='Tarih', ascending=False), use_container_width=True)

    # --- 9. ANALİZLER (RİSK & DAĞILIM) ---
    elif menu == "📈 ANALİZLER":
        st.title("📈 Stratejik Analiz Paneli")
        if not my_p.empty:
            my_p['Value'] = my_p['Maliyet'] * my_p['Adet']
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.pie(my_p, values='Value', names='Kod', hole=0.6, title="Varlık Dağılımı", color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
            with c2:
                st.plotly_chart(px.bar(my_p, x='Kod', y='Value', color='Kat', title="Varlık Büyüklükleri"), use_container_width=True)
            
            # Risk Analizi (Zeka Katmanı)
            st.subheader("🛡️ Risk ve Diversifikasyon Analizi")
            max_weight = (my_p['Value'].max() / my_p['Value'].sum()) * 100
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                <div class="analysis-card">
                    <h4>Konsantrasyon Riski</h4>
                    <p>En büyük pozisyon ağırlığı: <b>%{max_weight:.1f}</b></p>
                    {"⚠️ Uyarı: Tek varlık %30'u geçmiş!" if max_weight > 30 else "✅ Portföy dengeli görünüyor."}
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""
                <div class="analysis-card">
                    <h4>Sektörel Çeşitlilik</h4>
                    <p>Toplam Kategori Sayısı: <b>{my_p['Kat'].nunique()}</b></p>
                    {"ℹ️ Farklı varlık sınıfları eklemeyi düşünebilirsiniz." if my_p['Kat'].nunique() < 2 else "✅ Sektörel dağılım başarılı."}
                </div>
                """, unsafe_allow_html=True)
        else: st.warning("Analiz için veri yetersiz.")

    # --- 10. TAKVİM & HABERLER ---
    elif menu == "📅 TAKVİM":
        st.title("📅 Ekonomik Takvim")
        st.table([
            {"Tarih": "22 Ocak", "Olay": "TCMB Faiz Kararı", "Önem": "Yüksek 🔥"},
            {"Tarih": "29 Ocak", "Olay": "ABD GSYH Verisi", "Önem": "Orta ⚡"},
            {"Tarih": "05 Şubat", "Olay": "Enflasyon Verisi (TÜİK)", "Önem": "Yüksek 🔥"}
        ])

    elif menu == "📰 HABERLER":
        st.title("📰 Piyasa Akışı")
        for h in [
            {"T": "BIST 100 Yeni Zirveyi Zorluyor", "S": "AKOSELL Haber", "D": "Analistler 11.000 seviyesinin kritik olduğunu belirtiyor."},
            {"T": "Kripto Varlıklarda ETF Rüzgarı", "S": "Global Finans", "D": "Kurumsal girişler kripto piyasasını domine ediyor."}
        ]:
            st.markdown(f"<div class='metric-card'><b>{h['S']}</b><br><h4>{h['T']}</h4><p>{h['D']}</p></div><br>", unsafe_allow_html=True)

    # --- 11. AYARLAR ---
    elif menu == "⚙️ AYARLAR":
        st.title("⚙️ Terminal Ayarları")
        with st.expander("👤 Profil Bilgileri"):
            st.text_input("Görünen İsim", value=st.session_state.u_data['Name'])
            st.button("GÜNCELLE")
        
        if st.button("🗑️ TÜM VERİLERİ SIFIRLA", type="secondary"):
            pd.DataFrame(columns=p_df.columns).to_csv(PORT_DB, index=False)
            pd.DataFrame(columns=pd.read_csv(HISTORY_DB).columns).to_csv(HISTORY_DB, index=False)
            st.rerun()