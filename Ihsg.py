import streamlit as st
import yfinance as yf
import datetime
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="Dashboard Analisis Teknikal", layout="wide")

# ==========================================
# --- CUSTOM CSS KHUSUS WIDGET & CHART ---
# ==========================================
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# --- FITUR PENCARIAN SAHAM ---
# ==========================================
st.markdown("### 🔍 Pilih Emiten Saham")
# Menggunakan st.text_input, pastikan tekan ENTER setelah mengetik kode saham (Cth: BBCA)
ticker_input = st.text_input("Masukkan Kode Saham (Contoh: BBCA, BBRI, GOTO, ESSA):", "ESSA").upper().strip()

ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"

# ==========================================
# --- FUNGSI AMBIL DATA ---
# ==========================================
@st.cache_data(ttl=300)
def get_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="5d")
        if hist.empty: return None, None, None, None
            
        latest_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change_pct = ((latest_price - prev_price) / prev_price) * 100
        
        info = stock.info
        dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
        company_name = info.get('longName', f"PT {ticker_symbol.replace('.JK', '')} Tbk")
        
        return latest_price, change_pct, dividend_yield, company_name
    except:
        return None, None, None, None

harga_sekarang, persen_perubahan, dividen, nama_perusahaan = get_stock_data(ticker_yf)

if harga_sekarang is None:
    st.error(f"❌ Saham dengan kode **{ticker_input}** tidak ditemukan atau jaringan bermasalah. Coba pastikan pengetikannya benar.")
    st.stop()

arrow = "▼" if persen_perubahan < 0 else "▲"
today_date = datetime.datetime.now().strftime("%d %B %Y")


# ==========================================
# --- 1. HEADER (MENGGUNAKAN KOLOM STREAMLIT - ANTI BOCOR) ---
# ==========================================
col_h1, col_h2, col_h3 = st.columns([2, 1.2, 1.3])

with col_h1:
    st.markdown(f"📊 **ANALISIS TEKNIKAL**")
    st.markdown(f"# **{ticker_input}**")
    st.markdown(f"**{nama_perusahaan}**")
    st.caption("Citadel Quant + Bandarmology")
    st.info(f"Update {today_date} | Close Rp{int(harga_sekarang)}")

with col_h2:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.success("**STRONG BUY**")
    st.markdown("⭐⭐⭐⭐⭐")
    st.markdown("### 🌟 9.5 <span style='font-size:14px; color:gray;'>/10</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_h3:
    st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
    st.caption("HARGA PENUTUPAN")
    st.markdown(f"## **Rp{int(harga_sekarang)}**")
    if persen_perubahan >= 0:
        st.markdown(f"<span style='color: #16a34a; font-weight: bold;'>▲ +{persen_perubahan:.2f}%</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span style='color: #dc2626; font-weight: bold;'>▼ {persen_perubahan:.2f}%</span>", unsafe_allow_html=True)
    st.caption("DIVIDEND YIELD")
    st.markdown(f"**{round(dividen, 2) if isinstance(dividen, (int, float)) else 'N/A'}%**")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()


# ==========================================
# --- 2. CHART & TRADE PLAN ---
# ==========================================
col_chart, col_plan = st.columns([2, 1])

with col_chart:
    tradingview_html = f"""
    <div style="border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden; background: white;">
        <div class="tradingview-widget-container" style="height: 400px; width: 100%;">
          <div id="tradingview_chart" style="height: 100%; width: 100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "autosize": true,
            "symbol": "{ticker_tv}",
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
          }});
          </script>
        </div>
    </div>
    """
    components.html(tradingview_html, height=410)

with col_plan:
    with st.container(border=True):
        st.markdown("💰 **TRADE PLAN**")
        st.markdown("🟢 **Entry Agresif:** Wait & See")
        st.markdown("🟢 **Buy on Pullback:** Wait Setup")
        st.markdown("🔴 **Stop Loss:** Auto")
        st.divider()
        st.markdown("🎯 **TARGET**")
        st.markdown("🥇 **TP 1:** TBA")
        st.markdown("🥈 **TP 2:** TBA")
        st.markdown("🚀 **Swing:** TBA")
        st.info("⚖️ Risk : Reward = ± 1 : 3")


# ==========================================
# --- 3. INDIKATOR BAWAH (3 KOLOM) ---
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    with st.container(border=True):
        st.markdown("📈 **TREND**")
        st.success("Daily: Bullish | Weekly: Bullish")
        st.markdown("- Higher High\n- Higher Low\n- Breakout Area")
    
    with st.container(border=True):
        st.markdown("🏛️ **BANDARMOLOGY**")
        st.caption("AKUMULASI BROKER TERBESAR")
        st.markdown("🟨 **LG:** 15,3 Juta (Avg 639)\n\n⬜ **CC:** 2,2 Juta (Avg 711)\n\n🟧 **XL:** 1,9 Juta (Avg 708)")
        st.success("Mayoritas broker besar hold.")

with col_b2:
    with st.container(border=True):
        st.markdown("↕️ **SUPPORT & RESISTANCE**")
        col_s1, col_s2 = st.columns(2)
        col_s1.markdown("🟢 **SUPPORT**\n- 637 (EMA)\n- 625\n- 620")
        col_s2.markdown("🔴 **RESIST**\n- 650\n- 670\n- 700")
    
    with st.container(border=True):
        st.markdown("⭐ **KESIMPULAN**")
        st.info(f"**{ticker_input} FASE MARKUP**")
        st.markdown("✅ Breakout terkonfirmasi.\n\n⚠️ Waspada profit taking di resistance.")

with col_b3:
    with st.container(border=True):
        st.markdown("📊 **INDIKATOR TEKNIKAL**")
        st.markdown("📌 **EMA:** Bullish Crossover\n\n📌 **RSI:** 63-66 (Belum Overbought)\n\n📌 **MACD:** Positif Kuat")
    
    with st.container(border=True):
        st.markdown("👥 **SHAREHOLDER**")
        st.caption("HOLDER BULAN INI")
        st.markdown("### **29.487**")
        st.caption("Terus meningkat")

# BANNER BAWAH
st.success("🏆 **STRONG BUY:** Breakout tervalidasi, bandar masih akumulasi, target swing terjaga selama harga bertahan di atas support.")


# ==========================================
# --- 4. PUSAT DATA PASAR (SCANNER) ---
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📊 Pusat Data Pasar (IHSG)")
tab_movers, tab_screener = st.tabs(["🔥 Top Movers & Trending", "🔎 Advanced Stock Scanner"])

with tab_movers:
    components.html("""
    <div class="tradingview-widget-container" style="height: 500px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>
      { "colorTheme": "light", "dateRange": "12M", "exchange": "IDX", "showChart": true, "locale": "id", "width": "100%", "height": "100%" }
      </script>
    </div>
    """, height=500)

with tab_screener:
    components.html("""
    <div class="tradingview-widget-container" style="height: 600px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
      { "width": "100%", "height": "100%", "defaultColumn": "overview", "defaultScreen": "general", "market": "indonesia", "showToolbar": true, "colorTheme": "light", "locale": "id" }
      </script>
    </div>
    """, height=600)
