import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard Analisis Teknikal", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (Untuk mempercantik tampilan agar mirip gambar) ---
st.markdown("""
    <style>
    .card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border: 1px solid #e0e0e0;
    }
    .metric-value { font-size: 2rem; font-weight: bold; color: #1e3a8a; }
    .green-text { color: #16a34a; font-weight: bold; }
    .red-text { color: #dc2626; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI AMBIL DATA (YAHOO FINANCE) ---
@st.cache_data(ttl=900) # Cache data selama 15 menit agar tidak lambat
def get_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="5d") # Ambil data 5 hari terakhir
        latest_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change_pct = ((latest_price - prev_price) / prev_price) * 100
        
        info = stock.info
        dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else "N/A"
        
        return latest_price, change_pct, dividend_yield
    except:
        return 640, -0.78, 8.74 # Fallback data dummy jika gagal akses internet

# Menjalankan fungsi ambil data saham ESSA
harga_sekarang, persen_perubahan, dividen = get_stock_data("ESSA.JK")

# --- BAGIAN 1: HEADER ---
col1, col2, col3 = st.columns([1.5, 1, 1])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("📊 **ANALISIS TEKNIKAL**")
    st.markdown("<h1 style='color: #1e3a8a; margin: 0; padding: 0;'>ESSA</h1>", unsafe_allow_html=True)
    st.write("**PT ESSA Industries Indonesia Tbk.**")
    st.caption("Citadel Quant + Bandarmology")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card" style="text-align: center;">', unsafe_allow_html=True)
    st.markdown("<h3 style='background-color: #16a34a; color: white; padding: 5px; border-radius: 5px;'>STRONG BUY</h3>", unsafe_allow_html=True)
    st.markdown("⭐⭐⭐⭐⭐")
    st.markdown("<h2>9.5 <span style='font-size: 1rem; color: gray;'>/ 10</span></h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="card" style="text-align: right;">', unsafe_allow_html=True)
    st.write("HARGA PENUTUPAN")
    st.markdown(f"<div class='metric-value'>Rp{int(harga_sekarang)}</div>", unsafe_allow_html=True)
    
    # Logika warna panah (Merah / Hijau)
    if persen_perubahan > 0:
        st.markdown(f"<div class='green-text'>▲ +{persen_perubahan:.2f}%</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='red-text'>▼ {persen_perubahan:.2f}%</div>", unsafe_allow_html=True)
        
    st.write(f"**DIVIDEND YIELD : {dividen if isinstance(dividen, str) else round(dividen, 2)}%**")
    st.markdown('</div>', unsafe_allow_html=True)


# --- BAGIAN 2: CHART & TRADE PLAN ---
col_chart, col_plan = st.columns([2, 1])

with col_chart:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    # Kode HTML Widget TradingView Asli
    tradingview_html = """
    <div class="tradingview-widget-container" style="height: 400px;">
      <div id="tradingview_chart" style="height: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({
        "autosize": true,
        "symbol": "IDX:ESSA",
        "interval": "D",
        "timezone": "Asia/Jakarta",
        "theme": "light",
        "style": "1",
        "locale": "id",
        "enable_publishing": false,
        "hide_top_toolbar": true,
        "hide_legend": false,
        "save_image": false,
        "container_id": "tradingview_chart",
        "studies": ["Moving Average@tv-basicstudies"]
      });
      </script>
    </div>
    """
    components.html(tradingview_html, height=400)
    st.markdown('</div>', unsafe_allow_html=True)

with col_plan:
    st.markdown('<div class="card" style="height: 430px;">', unsafe_allow_html=True)
    st.write("### 💰 TRADE PLAN")
    st.write("🟢 **Entry Agresif:** Rp635 - Rp645")
    st.write("🟢 **Buy on Pullback:** Rp620 - Rp625")
    st.write("🔴 **Stop Loss:** Rp610")
    st.divider()
    st.write("### 🎯 TARGET")
    st.write("🥇 **TP1:** Rp670")
    st.write("🥈 **TP2:** Rp700")
    st.write("🚀 **Swing:** Rp740 - Rp780")
    st.info("⚖️ Risk : Reward = ± 1 : 4")
    st.markdown('</div>', unsafe_allow_html=True)


# --- BAGIAN 3: INDIKATOR BAWAH (Statis sebagai template) ---
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("#### 📈 TREND")
    st.success("Harian: Bullish \n\n Mingguan: Bullish")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("#### 🏛️ BANDARMOLOGY")
    # Data broker summary umumnya berbayar, di sini di-mockup menggunakan DataFrame Pandas
    df_broker = pd.DataFrame({
        "Broker": ["LG", "CC", "XL"],
        "Volume": ["15.3 Juta Lot", "2.2 Juta Lot", "1.9 Juta Lot"],
        "Avg": [639, 711, 708]
    })
    st.dataframe(df_broker, hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_b2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("#### ↕️ SUPPORT & RESISTANCE")
    col_sup, col_res = st.columns(2)
    col_sup.write("**Support:** \n- 637 \n- 625 \n- 620")
    col_res.write("**Resistance:** \n- 650 \n- 670 \n- 700")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("#### ⭐ KESIMPULAN")
    st.info("ESSA MEMASUKI FASE MARKUP")
    st.write("✅ Breakout area 620 terkonfirmasi")
    st.write("⚠️ Area 650-670 menjadi resistance terdekat")
    st.markdown('</div>', unsafe_allow_html=True)

with col_b3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("#### 📊 INDIKATOR TEKNIKAL")
    st.write("📌 **EMA:** Bullish Crossover")
    st.write("📌 **RSI:** 63 - Belum Overbought")
    st.write("📌 **MACD:** Positif - Masih Kuat")
    st.markdown('</div>', unsafe_allow_html=True)
