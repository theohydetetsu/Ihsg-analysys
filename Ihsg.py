import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="Dashboard Analisis Teknikal", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# --- CUSTOM CSS ---
# ==========================================
st.markdown("""
    <style>
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border: 1px solid #e0e0e0;
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# --- FUNGSI AMBIL DATA (YAHOO FINANCE) ---
# ==========================================
@st.cache_data(ttl=900)
def get_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="5d")
        latest_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change_pct = ((latest_price - prev_price) / prev_price) * 100
        
        info = stock.info
        dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else "N/A"
        
        return latest_price, change_pct, dividend_yield
    except:
        return 640, -0.78, 8.74

harga_sekarang, persen_perubahan, dividen = get_stock_data("ESSA.JK")

# ==========================================
# --- BAGIAN 1: HEADER ---
# ==========================================
col1, col2, col3 = st.columns([1.5, 1, 1])

with col1:
    st.markdown("""
    <div class="card">
        <div style="background-color:#1e3a8a; color:white; display:inline-block; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold; margin-bottom:8px;">📊 ANALISIS TEKNIKAL</div>
        <h1 style="color: #1e3a8a; margin: 0; padding: 0; font-size: 3.5rem;">ESSA</h1>
        <p style="margin: 0; font-weight: bold; font-size: 1.1rem;">PT ESSA Industries Indonesia Tbk.</p>
        <p style="margin: 0; color: #666; font-size: 0.9rem;">Citadel Quant + Bandarmology</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card" style="text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 90%;">
        <div style="background-color: #16a34a; color: white; padding: 5px 20px; border-radius: 5px; font-weight: bold; font-size: 1.2rem; margin-bottom: 10px;">STRONG BUY</div>
        <div style="color: #eab308; font-size: 1.5rem; letter-spacing: 2px;">⭐⭐⭐⭐⭐</div>
        <h2 style="color: #ca8a04; font-size: 3rem; margin: 5px 0 0 0;">9.5 <span style="font-size: 1rem; color: gray;">/ 10</span></h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    arrow = "▲" if persen_perubahan > 0 else "▼"
    color = "#16a34a" if persen_perubahan > 0 else "#dc2626"
    
    st.markdown(f"""
    <div class="card" style="text-align: right; height: 90%;">
        <p style="margin: 0; color: #666; font-weight: bold; font-size: 0.8rem; text-transform: uppercase;">Harga Penutupan</p>
        <h2 style="color: #1e3a8a; font-size: 2.8rem; margin: 0;">Rp{int(harga_sekarang)}</h2>
        <p style="color: {color}; font-weight: bold; font-size: 1.1rem; margin: 0;">{arrow} {persen_perubahan:.2f}%</p>
        <div style="margin-top: 15px;">
            <p style="margin: 0; color: #666; font-weight: bold; font-size: 0.8rem; text-transform: uppercase;">Dividend Yield</p>
            <p style="color: #1e3a8a; font-weight: bold; font-size: 1.5rem; margin: 0;">{dividen if isinstance(dividen, str) else round(dividen, 2)}%</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# --- BAGIAN 2: CHART & TRADE PLAN ---
# ==========================================
col_chart, col_plan = st.columns([2, 1])

with col_chart:
    st.markdown('<div class="card" style="padding: 0; overflow: hidden; height: 400px;">', unsafe_allow_html=True)
    tradingview_html = """
    <div class="tradingview-widget-container" style="height: 100%; width: 100%;">
      <div id="tradingview_chart" style="height: 100%; width: 100%;"></div>
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
    st.markdown("""
    <div class="card" style="height: 360px;">
        <h3 style="color: #16a34a; font-size: 1.2rem; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-top:0;">💰 TRADE PLAN</h3>
        <p style="margin: 10px 0; display: flex; justify-content: space-between;"><strong style="color: #16a34a;">+ Entry Agresif</strong> <span>Rp635 - Rp645</span></p>
        <p style="margin: 10px 0; display: flex; justify-content: space-between;"><strong style="color: #16a34a;">+ Buy on Pullback</strong> <span>Rp620 - Rp625</span></p>
        <p style="margin: 10px 0; display: flex; justify-content: space-between;"><strong style="color: #dc2626;">x Stop Loss</strong> <span style="color: #dc2626; font-weight: bold;">Rp610</span></p>
        
        <h3 style="color: #16a34a; font-size: 1.2rem; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-top: 20px;">🎯 TARGET</h3>
        <p style="margin: 10px 0; display: flex; justify-content: space-between;"><strong>🥇 TP1 :</strong> <span>Rp670</span></p>
        <p style="margin: 10px 0; display: flex; justify-content: space-between;"><strong>🥈 TP2 :</strong> <span>Rp700</span></p>
        <p style="margin: 10px 0; display: flex; justify-content: space-between;"><strong>🚀 Swing :</strong> <span>Rp740 - Rp780</span></p>
        
        <div style="background-color: #f3f4f6; text-align: center; padding: 10px; border-radius: 5px; font-weight: bold; margin-top: 15px;">
            ⚖️ Risk : Reward &nbsp;&nbsp;&nbsp; <span style="color: #16a34a; font-size: 1.2rem;">± 1 : 4</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# --- BAGIAN 3: INDIKATOR BAWAH ---
# ==========================================
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📈 TREND")
    st.success("Harian: **Bullish** \n\n Mingguan: **Bullish**")
    st.markdown('</div>', unsafe_allow_html=True)

with col_b2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### ⭐ KESIMPULAN")
    st.info("**ESSA MEMASUKI FASE MARKUP**")
    st.write("✅ Breakout area 620 terkonfirmasi")
    st.write("⚠️ Area 650-670 menjadi resistance terdekat")
    st.markdown('</div>', unsafe_allow_html=True)

with col_b3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📊 INDIKATOR TEKNIKAL")
    st.write("📌 **EMA:** Bullish Crossover")
    st.write("📌 **RSI:** 63 - Belum Overbought")
    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# --- BAGIAN 4: FITUR SCANNER & TOP MOVERS ---
# ==========================================
st.markdown("---")
st.markdown("<h2 style='color: #1e3a8a;'>Pusat Data Pasar (IHSG)</h2>", unsafe_allow_html=True)

tab_movers, tab_screener = st.tabs(["🔥 Top Movers & Trending", "🔎 Advanced Stock Scanner"])

with tab_movers:
    st.write("Daftar saham dengan kenaikan (Gainers), penurunan (Losers), dan volume tertinggi hari ini.")
    hotlist_html = """
    <div class="tradingview-widget-container" style="height: 500px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>
      {
      "colorTheme": "light",
      "dateRange": "12M",
      "exchange": "IDX",
      "showChart": true,
      "locale": "id",
      "width": "100%",
      "height": "100%",
      "largeChartUrl": "",
      "isTransparent": false,
      "showSymbolLogo": true,
      "showFloatingTooltip": false,
      "plotLineColorGrowing": "rgba(22, 163, 74, 1)",
      "plotLineColorFalling": "rgba(220, 38, 38, 1)",
      "gridLineColor": "rgba(240, 243, 250, 1)",
      "scaleFontColor": "rgba(120, 123, 134, 1)",
      "belowLineFillColorGrowing": "rgba(22, 163, 74, 0.12)",
      "belowLineFillColorFalling": "rgba(220, 38, 38, 0.12)",
      "belowLineFillColorGrowingBottom": "rgba(22, 163, 74, 0)",
      "belowLineFillColorFallingBottom": "rgba(220, 38, 38, 0)",
      "symbolActiveColor": "rgba(41, 98, 255, 0.12)"
      }
      </script>
    </div>
    """
    components.html(hotlist_html, height=500)

with tab_screener:
    st.write("Gunakan filter di bawah untuk memindai saham berdasarkan Valuasi, Dividen, Kinerja, atau Indikator Teknikal.")
    screener_html = """
    <div class="tradingview-widget-container" style="height: 600px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
      {
      "width": "100%",
      "height": "100%",
      "defaultColumn": "overview",
      "defaultScreen": "general",
      "market": "indonesia",
      "showToolbar": true,
      "colorTheme": "light",
      "locale": "id"
      }
      </script>
    </div>
    """
    components.html(screener_html, height=600)
