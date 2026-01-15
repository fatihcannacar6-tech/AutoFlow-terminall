import streamlit as st
import pandas as pd
import os
import hashlib
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. SİSTEM YAPILANDIRMASI & PREMİUM TEMA ---
st.set_page_config(page_title="AKOSELL ULTIMATE TERMINAL", layout="wide", page_icon="🏛️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #FFFFFF; }
    
    /* Modern Kart Tasarımları */
    .metric-box {
        background: #FFFFFF; border: 1px solid #E2E8F0; padding: 25px; border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03); transition: transform 0.2s;
    }
    .metric-box:hover { transform: translateY(-5px); border-color: #00D1FF; }
    .label { color: #64748B; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .value { color: #0F172A; font-size: 32px; font-weight: 800; margin-top: 10px; }
    
    /* Sidebar Özelleştirme */
    [data-testid="stSidebar"] { background-color: #F8FAFC !important; border-right: 1px solid #E2E8F0; width: 320px !important; }
    .stRadio div[role="radiogroup"] label {
        padding: 12px 20px !important; border-radius: 12px !important; margin-bottom: 6px !important;
        border: 1px solid transparent !important; transition: all 0.3s;
    }
    .stRadio div[role="radiogroup"] label[data-checked="true"] {
        background: #00D1FF !important; border-color: #00D1FF !important; box-shadow: 0 4px 12px rgba(0,209,255,0.3);
    }
    .stRadio div[role="radiogroup"] label[data-checked="true"] p { color: white !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. VERİ MOTORU (DATABASE) ---
FILES = {"users": "u_v15.csv", "port": "p_v15.csv", "logs": "l_v15.csv"}

def init_db():
    if not os.path.exists(FILES["users"]):
        admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
        pd.DataFrame([["admin", admin_pw, "Baş Yönetici", "Approved", "Admin"]], 
                     columns=["Username", "Password", "Name", "Status", "Role"]).to_csv(FILES["users"], index=False)
    for f in ["port", "logs"]:
        if not os.path.exists(FILES[f]): pd.DataFrame().to_csv(FILES[f], index=False)

init_db()

# --- 3. KÜRESEL VERİ FONKSİYONLARI ---
@st.cache_data(ttl=300)
def fetch_global_data(symbol):
    try:
        t = yf.Ticker(symbol)
        h = t.history(period="1mo")
        return h if not h.empty else None
    except: return None

def get_current_price(symbol):
    try:
        return yf.Ticker(symbol).fast_info.last_price
    except: return 0.0

# --- 4. KİMLİK DOĞRULAMA ---
if 'terminal_auth' not in st.session_state: st.session_state.terminal_auth = False

if not st.session_state.terminal_auth:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>AKOSELL</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["ERİŞİM PANELİ", "KAYIT OL"])
        with t1:
            u = st.text_input("Kullanıcı")
            p = st.text_input("Şifre", type="password")
            if st.button("SİSTEMİ BAŞLAT", use_container_width=True):
                users = pd.read_csv(FILES["users"])
                hp = hashlib.sha256(p.encode()).hexdigest()
                user = users[(users['Username']==u) & (users['Password']==hp)]
                if not user.empty:
                    if user.iloc[0]['Status'] == "Approved":
                        st.session_state.terminal_auth = True
                        st.session_state.user = user.iloc[0].to_dict()
                        st.rerun()
                    else: st.warning("Erişim talebiniz onay aşamasında.")
                else: st.error("Kimlik doğrulanamadı.")
        with t2:
            nu, nn, npw = st.text_input("Kullanıcı Adı"), st.text_input("Ad Soyad"), st.text_input("Şifre Belirle", type="password")
            if st.button("YÖNETİME İLET", use_container_width=True):
                df_u = pd.read_csv(FILES["users"])
                if nu in df_u['Username'].values: st.error("Kullanıcı adı mevcut.")
                else:
                    new_u = pd.DataFrame([[nu, hashlib.sha256(npw.encode()).hexdigest(), nn, "Pending", "User"]], columns=df_u.columns)
                    pd.concat([df_u, new_u]).to_csv(FILES["users"], index=False)
                    st.success("Talebiniz gönderildi.")

else:
    # --- 5. TERMİNAL NAVİGASYON ---
    with st.sidebar:
        st.markdown(f"""<div style="background:white; border:1px solid #E2E8F0; padding:20px; border-radius:12px; margin-bottom:20px;">
            <div style="font-size:12px; color:#64748B; font-weight:700;">AKTİF TERMİNAL</div>
            <div style="font-size:20px; font-weight:800; color:#0F172A;">{st.session_state.user['Name']}</div>
            <div style="color:#00D1FF; font-size:11px; font-weight:700;">SaaS ENTERPRISE LICENSE</div>
        </div>""", unsafe_allow_html=True)
        
        menu = st.radio("MENÜ", ["📊 ANALİTİK DASHBOARD", "🌐 GLOBAL PİYASA", "💼 PORTFÖY MERKEZİ", "📉 RİSK & RAPORLAMA", "🛠️ TERMİNAL AYARLARI", "🔐 ADMIN KONTROL" if st.session_state.user['Role'] == "Admin" else None], label_visibility="collapsed")
        
        st.divider()
        if st.button("OTURUMU KAPAT", use_container_width=True):
            st.session_state.terminal_auth = False
            st.rerun()

    # Verileri Yükle
    df_p = pd.read_csv(FILES["port"]) if os.path.getsize(FILES["port"]) > 2 else pd.DataFrame(columns=["Owner", "Symbol", "Cat", "Qty", "Cost"])
    my_p = df_p[df_p['Owner'] == st.session_state.user['Username']].copy()

    # --- 6. DASHBOARD (PREMIUM) ---
    if menu == "📊 ANALİTİK DASHBOARD":
        st.title("Executive Analytical Dashboard")
        
        if not my_p.empty:
            with st.spinner("Piyasa verileri konsolide ediliyor..."):
                my_p['Current'] = [get_current_price(s) for s in my_p['Symbol']]
                my_p['Value'] = my_p['Current'] * my_p['Qty']
                my_p['PL'] = my_p['Value'] - (my_p['Cost'] * my_p['Qty'])
                my_p['PL%'] = (my_p['PL'] / (my_p['Cost'] * my_p['Qty'])) * 100

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="metric-box"><div class="label">Net Portföy</div><div class="value">₺{my_p["Value"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-box"><div class="label">Toplam Kar/Zarar</div><div class="value" style="color:{"#10B981" if my_p["PL"].sum() > 0 else "#EF4444"}">₺{my_p["PL"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-box"><div class="label">Ağırlıklı Getiri</div><div class="value">%{ (my_p["PL"].sum() / (my_p["Cost"]*my_p["Qty"]).sum() * 100):.2f}</div></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-box"><div class="label">Varlık Çeşitliliği</div><div class="value">{my_p["Symbol"].nunique()}</div></div>', unsafe_allow_html=True)

            st.divider()
            col_left, col_right = st.columns([2, 1])
            with col_left:
                st.subheader("Varlık Bazlı Getiri Analizi")
                fig = px.bar(my_p, x='Symbol', y='PL', color='PL', color_continuous_scale='RdYlGn', template="plotly_white", barmode='group')
                st.plotly_chart(fig, use_container_width=True)
            with col_right:
                st.subheader("Stratejik Varlık Dağılımı")
                fig_pie = px.pie(my_p, values='Value', names='Cat', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sistemde aktif pozisyon bulunamadı. Lütfen Portföy Merkezi'nden varlık ekleyin.")

    # --- 7. GLOBAL PİYASA (CANLI DATA) ---
    elif menu == "🌐 GLOBAL PİYASA":
        st.title("Küresel Piyasa Terminali")
        
        search_col, data_col = st.columns([1, 3])
        with search_col:
            st.markdown("### Varlık Tarayıcı")
            target = st.text_input("Sembol (Örn: THYAO.IS, BTC-USD, AAPL, GC=F)").upper()
            if target:
                hist = fetch_global_data(target)
                if hist is not None:
                    st.success(f"Bağlantı Başarılı: {target}")
                    st.metric("Son Fiyat", f"{hist['Close'].iloc[-1]:,.2f}")
                    st.metric("24s Değişim", f"{((hist['Close'].iloc[-1]/hist['Close'].iloc[-2])-1)*100:.2f}%")
                    if st.button("PORTFÖYE AKTAR"):
                        st.session_state.pre_sym = target
                        st.info("Portföy Merkezi'ne yönlendiriliyorsunuz...")
                else: st.error("Sembol bulunamadı.")
        
        with data_col:
            if target and hist is not None:
                fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
                fig.update_layout(title=f"{target} Teknik Analiz Görünümü", template="plotly_white", xaxis_rangeslider_visible=False, height=600)
                st.plotly_chart(fig, use_container_width=True)

    # --- 8. PORTFÖY MERKEZİ ---
    elif menu == "💼 PORTFÖY MERKEZİ":
        st.title("Pozisyon Yönetimi")
        tab_new, tab_edit = st.tabs(["🆕 YENİ İŞLEM", "⚙️ PORTFÖYÜ DÜZENLE"])
        
        with tab_new:
            with st.form("trade_form"):
                c1, c2, c3, c4 = st.columns(4)
                s = c1.text_input("Sembol", value=st.session_state.get('pre_sym', '')).upper()
                ct = c2.selectbox("Sınıf", ["Hisse", "Kripto", "Emtia", "Döviz", "Fon"])
                q = c3.number_input("Adet", min_value=0.0)
                c = c4.number_input("Maliyet", min_value=0.0)
                if st.form_submit_button("İŞLEMİ ONAYLA"):
                    new_trade = pd.DataFrame([[st.session_state.user['Username'], s, ct, q, c]], columns=["Owner", "Symbol", "Cat", "Qty", "Cost"])
                    pd.concat([df_p, new_trade]).to_csv(FILES["port"], index=False)
                    st.success("Pozisyon kaydedildi."); st.rerun()

        with tab_edit:
            if not my_p.empty:
                edited = st.data_editor(my_p.drop(columns=['Owner']), use_container_width=True, num_rows="dynamic")
                if st.button("TÜMÜNÜ GÜNCELLE"):
                    others = df_p[df_p['Owner'] != st.session_state.user['Username']]
                    edited['Owner'] = st.session_state.user['Username']
                    pd.concat([others, edited]).to_csv(FILES["port"], index=False)
                    st.rerun()

    # --- 9. RİSK & RAPORLAMA ---
    elif menu == "📉 RİSK & RAPORLAMA":
        st.title("Kurumsal Risk ve Raporlama")
        if not my_p.empty:
            st.subheader("Varlık Risk Matrisi")
            my_p['Ağırlık%'] = (my_p['Value'] / my_p['Value'].sum()) * 100
            st.dataframe(my_p[['Symbol', 'Cat', 'Qty', 'Cost', 'Current', 'PL', 'PL%', 'Ağırlık%']].style.background_gradient(subset=['PL%'], cmap='RdYlGn'), use_container_width=True)
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### Risk Notu")
                max_w = my_p['Ağırlık%'].max()
                if max_w > 50: st.error(f"KRİTİK: Portföyün %{max_w:.1f}'i tek varlıkta!")
                elif max_w > 25: st.warning(f"DİKKAT: %{max_w:.1f} yoğunlaşma riski.")
                else: st.success("DENGELİ: Portföy dağılımı ideal.")
            
            with c2:
                st.markdown("### Raporu İndir")
                csv = my_p.to_csv(index=False).encode('utf-8')
                st.download_button("📥 EXCEL/CSV RAPORU OLUŞTUR", csv, f"AKOSELL_{datetime.now().date()}.csv", "text/csv", use_container_width=True)
        else: st.warning("Rapor oluşturmak için veri bulunamadı.")

    # --- 10. ADMIN KONTROL ---
    elif menu == "🔐 ADMIN KONTROL":
        st.title("Sistem Yönetim Paneli")
        u_df = pd.read_csv(FILES["users"])
        
        st.subheader("Onay Bekleyen Kullanıcılar")
        pending = u_df[u_df['Status'] == "Pending"]
        if not pending.empty:
            for i, r in pending.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                col1.info(f"**{r['Name']}** (@{r['Username']})")
                if col2.button("✅ ONAY", key=f"y_{i}"):
                    u_df.at[i, 'Status'] = "Approved"
                    u_df.to_csv(FILES["users"], index=False); st.rerun()
                if col3.button("❌ RED", key=f"n_{i}"):
                    u_df = u_df.drop(i)
                    u_df.to_csv(FILES["users"], index=False); st.rerun()
        else: st.success("Onay bekleyen kayıt yok.")
        
        st.divider()
        st.subheader("Sistem Veritabanı")
        st.dataframe(u_df, use_container_width=True)