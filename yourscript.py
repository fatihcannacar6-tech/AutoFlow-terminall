import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="AKOSELL ENTERPRISE", layout="wide", page_icon="🏛️")

# --- 2. GELİŞMİŞ CSS (BEYAZ TEMA & MODERN UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    
    /* KPI Kartları */
    .kpi-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .kpi-label { color: #64748B; font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .kpi-value { color: #0F172A; font-size: 24px; font-weight: 700; }
    
    /* Menü Tasarımı */
    [data-testid="stSidebarNav"] { display: none; }
    .stRadio div[role="radiogroup"] { gap: 8px !important; padding: 0 15px !important; }
    .stRadio div[role="radiogroup"] label { 
        background-color: #F8FAFC !important; border: 1px solid #E2E8F0 !important; 
        border-radius: 10px !important; padding: 12px 16px !important; width: 100% !important; 
        cursor: pointer !important; transition: all 0.2s ease; 
    }
    .stRadio div[role="radiogroup"] label[data-checked="true"] { background-color: #00D1FF !important; border-color: #00D1FF !important; }
    .stRadio div[role="radiogroup"] label[data-checked="true"] p { color: #FFFFFF !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERİ SİSTEMİ ---
USER_DB, PORT_DB, LOG_DB = "users_v13.csv", "portfolio_v13.csv", "logs_v13.csv"

def init_db():
    if not os.path.exists(USER_DB):
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Admin", "admin@akosell.com", "Approved", "Admin"]], 
                     columns=["Username", "Password", "Name", "Email", "Status", "Role"]).to_csv(USER_DB, index=False)
    if not os.path.exists(PORT_DB): 
        pd.DataFrame(columns=["Owner", "Kod", "Kat", "Maliyet", "Adet"]).to_csv(PORT_DB, index=False)
    if not os.path.exists(LOG_DB):
        pd.DataFrame(columns=["Zaman", "Kullanıcı", "İşlem"]).to_csv(LOG_DB, index=False)

init_db()

# --- 4. GİRİŞ VE KAYIT SİSTEMİ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>AKOSELL</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["GİRİŞ", "KAYIT OL"])
        with t1:
            u = st.text_input("Kullanıcı")
            p = st.text_input("Şifre", type="password")
            if st.button("GİRİŞ YAP", use_container_width=True):
                users = pd.read_csv(USER_DB)
                hp = hashlib.sha256(p.encode()).hexdigest()
                user = users[(users['Username']==u) & (users['Password']==hp)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.logged_in = True
                        st.session_state.u_data = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Kaydınız onay bekliyor.")
                else: st.error("Hatalı bilgiler.")
        with t2:
            nu = st.text_input("Kullanıcı Adı")
            nn = st.text_input("Ad Soyad")
            npw = st.text_input("Şifre Belirle", type="password")
            if st.button("KAYIT TALEBİ OLUŞTUR", use_container_width=True):
                users = pd.read_csv(USER_DB)
                if nu in users['Username'].values: st.error("Bu kullanıcı adı alınmış.")
                else:
                    new_u = pd.DataFrame([[nu, hashlib.sha256(npw.encode()).hexdigest(), nn, "", "Pending", "User"]], columns=users.columns)
                    pd.concat([users, new_u]).to_csv(USER_DB, index=False)
                    st.success("Talebiniz Admin'e iletildi.")

else:
    # --- 5. SIDEBAR ---
    with st.sidebar:
        st.markdown(f"""<div style="text-align:center; padding:20px; border-bottom:1px solid #EEE;">
            <div style="font-weight:800; color:#1E293B;">{st.session_state.u_data['Name'].upper()}</div>
            <small style="color:#00D1FF;">{st.session_state.u_data['Role']}</small>
        </div>""", unsafe_allow_html=True)
        menu = st.radio("NAV", ["📊 DASHBOARD", "🔍 PİYASA ARA", "💼 PORTFÖYÜM", "📈 ANALİZ RAPORU", "🔐 ADMIN PANELİ" if st.session_state.u_data['Role'] == "Admin" else None], label_visibility="collapsed")
        if st.button("GÜVENLİ ÇIKIŞ", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Verileri Yükle
    df_port = pd.read_csv(PORT_DB)
    my_port = df_port[df_port['Owner'] == st.session_state.u_data['Username']]

    # --- 6. DASHBOARD ---
    if menu == "📊 DASHBOARD":
        st.title("Gelişmiş Dashboard")
        if not my_port.empty:
            with st.spinner("Piyasa verileri konsolide ediliyor..."):
                # Basit fiyat çekme simülasyonu/hızlı motor
                prices = []
                for _, r in my_port.iterrows():
                    s = f"{r['Kod']}.IS" if r['Kat'] == "Hisse" else f"{r['Kod']}-USD" if r['Kat'] == "Kripto" else r['Kod']
                    try: prices.append(yf.Ticker(s).history(period="1d")['Close'].iloc[-1])
                    except: prices.append(r['Maliyet'])
                
                my_port['Güncel'] = prices
                my_port['Değer'] = my_port['Güncel'] * my_port['Adet']
                my_port['KarZarar'] = my_port['Değer'] - (my_port['Maliyet'] * my_port['Adet'])
                
            c1, c2, c3 = st.columns(3)
            c1.metric("PORTFÖY DEĞERİ", f"₺{my_port['Değer'].sum():,.2f}")
            c2.metric("NET KÂR/ZARAR", f"₺{my_port['KarZarar'].sum():,.2f}", delta=f"{(my_port['KarZarar'].sum() / (my_port['Maliyet']*my_port['Adet']).sum() * 100):.2f}%")
            c3.metric("VARLIK SAYISI", len(my_port))
            
            st.divider()
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.subheader("Varlık Dağılım Performansı")
                fig = px.bar(my_port, x='Kod', y='Değer', color='KarZarar', color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
            with col_b:
                st.subheader("Kategori Dağılımı")
                fig_pie = px.pie(my_port, values='Değer', names='Kat', hole=0.5)
                st.plotly_chart(fig_pie, use_container_width=True)
        else: st.info("Henüz portföyünüzde varlık bulunmuyor.")

    # --- 7. PİYASA ARA (TÜM BORSALAR) ---
    elif menu == "🔍 PİYASA ARA":
        st.title("Küresel Piyasa Tarayıcı")
        query = st.text_input("Hisse veya Kripto Sembolü Girin (Örn: THYAO, BTC, AAPL, GOLD)")
        if query:
            with st.spinner("Veri getiriliyor..."):
                # Borsa İstanbul için .IS eki ekleme denemesi
                s = query.upper()
                options = [f"{s}.IS", f"{s}-USD", s]
                data = None
                for opt in options:
                    t = yf.Ticker(opt)
                    hist = t.history(period="1mo")
                    if not hist.empty:
                        data = hist
                        symbol_found = opt
                        break
                
                if data is not None:
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.subheader(f"{symbol_found} - 30 Günlük Grafik")
                        st.line_chart(data['Close'])
                    with c2:
                        st.subheader("Varlık Detayları")
                        st.metric("Son Fiyat", f"{data['Close'].iloc[-1]:,.2f}")
                        st.metric("Günlük Değişim", f"{((data['Close'].iloc[-1]/data['Close'].iloc[-2])-1)*100:.2f}%")
                        if st.button("PORTFÖYÜME EKLE"):
                            st.session_state.pending_symbol = s
                            st.success("Portföyüm sekmesine yönlendiriliyorsunuz...")
                else: st.error("Sembol bulunamadı. Lütfen tam kodu girin.")

    # --- 8. ANALİZ RAPORU ---
    elif menu == "📈 ANALİZ RAPORU":
        st.title("Detaylı Portföy Analiz Raporu")
        if not my_port.empty:
            # Risk Analizi
            st.subheader("Risk & Getiri Analizi")
            my_port['Ağırlık'] = (my_port['Değer'] / my_port['Değer'].sum()) * 100
            
            st.dataframe(my_port[['Kod', 'Kat', 'Adet', 'Maliyet', 'Güncel', 'KarZarar', 'Ağırlık']].style.format({'Ağırlık': '{:.2f}%'}), use_container_width=True)
            
            # Excel Kayıt Butonu
            csv = my_port.to_csv(index=False).encode('utf-8')
            st.download_button("ANALİZ RAPORUNU İNDİR (CSV)", csv, f"rapor_{datetime.now().date()}.csv", "text/csv")
            
            # Strateji Önerisi
            max_asset = my_port.loc[my_port['Ağırlık'].idxmax()]
            if max_asset['Ağırlık'] > 40:
                st.warning(f"⚠️ **Konsantrasyon Riski:** {max_asset['Kod']} varlığı portföyünüzün %{max_asset['Ağırlık']:.1f}'ini oluşturuyor. Çeşitlendirme önerilir.")
            else:
                st.success("✅ **Çeşitlendirme:** Portföy dağılımınız dengeli görünüyor.")
        else: st.warning("Analiz için veri yetersiz.")

    # --- 9. PORTFÖYÜM (EKLE/DÜZENLE) ---
    elif menu == "💼 PORTFÖYÜM":
        st.title("Varlık Yönetimi")
        t1, t2 = st.tabs(["VARLIK EKLE", "VARLIKLARI DÜZENLE"])
        with t1:
            with st.form("ekle_v13"):
                c1, c2, c3 = st.columns(3)
                kod = c1.text_input("Varlık Kodu (Örn: THYAO, BTC)", value=st.session_state.get('pending_symbol', '')).upper()
                adet = c2.number_input("Adet", min_value=0.0)
                mali = c3.number_input("Birim Maliyet", min_value=0.0)
                kat = st.selectbox("Tür", ["Hisse", "Kripto", "Emtia", "Döviz"])
                if st.form_submit_button("LİSTEYE EKLE"):
                    new_row = pd.DataFrame([[st.session_state.u_data['Username'], kod, kat, mali, adet]], columns=df_port.columns)
                    pd.concat([df_port, new_row]).to_csv(PORT_DB, index=False)
                    st.success("Varlık başarıyla kaydedildi.")
                    st.rerun()
        with t2:
            edited = st.data_editor(my_port[['Kod', 'Kat', 'Maliyet', 'Adet']], num_rows="dynamic", use_container_width=True)
            if st.button("DEĞİŞİKLİKLERİ KAYDET"):
                others = df_port[df_port['Owner'] != st.session_state.u_data['Username']]
                edited['Owner'] = st.session_state.u_data['Username']
                pd.concat([others, edited]).to_csv(PORT_DB, index=False)
                st.rerun()

    # --- 10. ADMIN PANELİ ---
    elif menu == "🔐 ADMIN PANELİ":
        st.title("Sistem Yönetimi")
        u_df = pd.read_csv(USER_DB)
        
        st.subheader("Bekleyen Kayıt Onayları")
        pending = u_df[u_df['Status'] == "Pending"]
        if not pending.empty:
            for i, r in pending.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(f"**{r['Name']}** (@{r['Username']})")
                if col2.button("ONAYLA", key=f"ok_{i}"):
                    u_df.at[i, 'Status'] = "Approved"
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
                if col3.button("REDDET", key=f"no_{i}"):
                    u_df = u_df.drop(i)
                    u_df.to_csv(USER_DB, index=False)
                    st.rerun()
        else: st.success("Onay bekleyen talep yok.")
        
        st.divider()
        st.subheader("Kullanıcı Listesi")
        st.dataframe(u_df[['Username', 'Name', 'Status', 'Role']], use_container_width=True)