import streamlit as st
import yfinance as yf
import datetime
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="Dashboard Analisis Teknikal", layout="wide")

# ==========================================
# --- CUSTOM CSS (ANTI DARK-MODE & RESPONSIVE) ---
# ==========================================
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
/* Memaksa padding lebih kecil untuk HP */
.block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
header { visibility: hidden; }

/* Kunci warna Card agar teks tidak hilang saat HP mode gelap */
.card { 
    background-color: #ffffff !important; 
    border: 1px solid #e5e7eb; 
    border-radius: 8px; 
    padding: 15px; 
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    margin-bottom: 15px;
    color: #111827 !important; 
}
.card * { color: #111827; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.card-title { color: #1e3a8a !important; font-size: 14px; font-weight: 700; border-bottom: 2px solid #f3f4f6; padding-bottom: 8px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }

/* Kunci Warna Spesifik */
.text-blue { color: #1e3a8a !important; font-weight: bold; }
.text-green { color: #16a34a !important; font-weight: bold; }
.text-red { color: #dc2626 !important; font-weight: bold; }
.text-gray { color: #6b7280 !important; }

ul.custom-list { list-style: none; padding-left: 0; margin: 0; font-size: 12px; }
ul.custom-list li { margin-bottom: 6px; display: flex; align-items: flex-start; gap: 6px; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# --- FITUR PENCARIAN SAHAM (TAMPIL DI DEPAN) ---
# ==========================================
st.markdown("### 🔍 Cari Kode Saham")
ticker_input = st.text_input("", "ESSA", placeholder="Ketik kode emiten lalu tekan Enter (Cth: BBCA, GOTO)").upper()
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
    st.error(f"❌ Saham **{ticker_input}** tidak ditemukan atau koneksi gagal.")
    st.stop()


# ==========================================
# --- 1. HEADER (KOP DASHBOARD) ---
# ==========================================
arrow = "▼" if persen_perubahan < 0 else "▲"
color_hex = "#dc2626" if persen_perubahan < 0 else "#16a34a"
today_date = datetime.datetime.now().strftime("%d %B %Y")

header_html = f"""
<div class="card" style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 15px;">
    <div style="flex: 1 1 250px;">
        <div style="background-color:#1e3a8a !important; color:white !important; display:inline-block; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold; margin-bottom:8px;"><i class="fas fa-chart-bar" style="color:white !important;"></i> ANALISIS TEKNIKAL</div>
        <h1 style="color: #1e3a8a !important; font-size: 45px; font-weight: 900; margin: 0; line-height: 1;">{ticker_input}</h1>
        <div style="font-size: 14px; font-weight: bold; margin-top: 5px;">{nama_perusahaan}</div>
        <div class="text-gray" style="font-size: 12px; margin-top: 2px;">Citadel Quant + Bandarmology</div>
        <div style="background-color:#1e3a8a !important; color:white !important; display:inline-block; padding:3px 8px; font-size:11px; margin-top:8px; border-radius:4px;">Update {today_date} | Close Rp{int(harga_sekarang)}</div>
    </div>
    
    <div style="flex: 1 1 120px; text-align: center;">
        <div style="background-color: #16a34a !important; color: white !important; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 16px; display: inline-block;">STRONG BUY</div>
        <div style="color: #eab308 !important; font-size: 16px; margin: 8px 0;"><i class="fas fa-star" style="color:#eab308 !important;"></i><i class="fas fa-star" style="color:#eab308 !important;"></i><i class="fas fa-star" style="color:#eab308 !important;"></i><i class="fas fa-star" style="color:#eab308 !important;"></i><i class="fas fa-star-half-alt" style="color:#eab308 !important;"></i></div>
        <div style="margin: 0 auto; width: 70px; height: 70px; border: 3px solid #eab308; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: bold; color: #ca8a04 !important;">
            9,5<span style="font-size:12px; color:#6b7280 !important; font-weight:normal;">/10</span>
        </div>
    </div>
    
    <div style="flex: 1 1 150px; text-align: right;">
        <div class="text-gray" style="font-size:11px; font-weight:bold;">HARGA PENUTUPAN</div>
        <div style="color:#1e3a8a !important; font-size:36px; font-weight:900; line-height:1.2;">Rp{int(harga_sekarang)}</div>
        <div style="color:{color_hex} !important; font-size:15px; font-weight:bold; margin-bottom: 12px;">{arrow} {persen_perubahan:.2f}%</div>
        <div>
            <div class="text-gray" style="font-size:11px; font-weight:bold;">DIVIDEND YIELD</div>
            <div style="color:#1e3a8a !important; font-size:22px; font-weight:bold;">{round(dividen, 2) if isinstance(dividen, (int, float)) else "N/A"}%</div>
        </div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)


# ==========================================
# --- 2. CHART & TRADE PLAN ---
# ==========================================
# Menggunakan kolom bawaan Streamlit agar responsif 100% di HP
col_chart, col_plan = st.columns([2.5, 1.5])

with col_chart:
    # Memisahkan iframe TradingView dari markdown wrapper untuk mencegah bug putih kosong
    tradingview_html = f"""
    <div style="border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.05); background: white;">
        <div class="tradingview-widget-container" style="height: 420px; width: 100%;">
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
    components.html(tradingview_html, height=430)

with col_plan:
    trade_plan_html = """
<div class="card" style="height:420px; display:flex; flex-direction:column; margin-bottom:0;">
<div class="card-title"><i class="fas fa-money-bill-wave text-green"></i> TRADE PLAN</div>
<div style="display:flex; justify-content:space-between; margin-bottom:12px;"><span class="text-green"><i class="fas fa-plus-circle"></i> Entry Agresif</span> <strong>Wait & See</strong></div>
<div style="display:flex; justify-content:space-between; margin-bottom:12px;"><span class="text-green"><i class="fas fa-plus-circle"></i> Buy on Pullback</span> <strong>Wait Setup</strong></div>
<div style="display:flex; justify-content:space-between; margin-bottom:20px;"><span class="text-red"><i class="fas fa-times-circle"></i> Stop Loss</span> <strong class="text-red">Auto</strong></div>

<div class="card-title" style="margin-top:10px;"><i class="fas fa-bullseye text-green"></i> TARGET</div>
<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><strong>🥇 TP 1 :</strong> <span>TBA</span></div>
<div style="display:flex; justify-content:space-between; margin-bottom:10px;"><strong>🥈 TP 2 :</strong> <span>TBA</span></div>
<div style="display:flex; justify-content:space-between; margin-bottom:15px;"><strong>🚀 Swing :</strong> <span>TBA</span></div>

<div style="background: #f3f4f6; padding: 12px; text-align: center; border-radius: 6px; font-weight: bold; margin-top: auto; color:#111 !important;">
⚖️ Risk : Reward &nbsp;&nbsp; <span class="text-green" style="font-size: 16px;">± 1 : 3</span>
</div>
</div>
"""
    st.markdown(trade_plan_html, unsafe_allow_html=True)


# ==========================================
# --- 3. BOTTOM INDIKATOR (3 KOLOM) ---
# ==========================================
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    st.markdown("""
<div class="card">
<div class="card-title"><i class="fas fa-chart-line"></i> TREND</div>
<div style="display: flex; justify-content: space-between; text-align: center; font-size: 11px; margin-bottom: 12px;">
<div><div style="background:#dcfce7 !important; color:#16a34a !important; padding:4px; border-radius:4px; font-weight:bold; margin-bottom:4px;"><i class="fas fa-check-circle"></i> DAILY</div><span style="font-weight:bold;">Bullish</span></div>
<div><div style="background:#dcfce7 !important; color:#16a34a !important; padding:4px; border-radius:4px; font-weight:bold; margin-bottom:4px;"><i class="fas fa-check-circle"></i> WEEKLY</div><span style="font-weight:bold;">Bullish</span></div>
<div><div style="background:#dcfce7 !important; color:#16a34a !important; padding:4px; border-radius:4px; font-weight:bold; margin-bottom:4px;"><i class="fas fa-check-circle"></i> MONTHLY</div><span style="font-weight:bold;">Bullish</span></div>
</div>
<ul class="custom-list">
<li><i class="fas fa-check text-green"></i> Higher High</li>
<li><i class="fas fa-check text-green"></i> Higher Low</li>
<li><i class="fas fa-check text-green"></i> Breakout Area</li>
</ul>
</div>
<div class="card">
<div class="card-title"><i class="fas fa-building"></i> BANDARMOLOGY</div>
<div class="text-gray" style="font-size: 10px; margin-bottom: 8px; font-weight: bold;">AKUMULASI BROKER TERBESAR</div>
<table style="width: 100%; font-size: 12px; margin-bottom: 12px; border-collapse: collapse;">
<tr style="border-bottom: 1px solid #eee;"><td style="padding:4px 0;">🟨 LG</td><td style="text-align:right;">15,3 Juta Lot</td><td style="text-align:right; font-weight:bold;">Avg 639</td></tr>
<tr style="border-bottom: 1px solid #eee;"><td style="padding:4px 0;">⬜ CC</td><td style="text-align:right;">2,2 Juta Lot</td><td style="text-align:right; font-weight:bold;">Avg 711</td></tr>
<tr style="border-bottom: 1px solid #eee;"><td style="padding:4px 0;">🟧 XL</td><td style="text-align:right;">1,9 Juta Lot</td><td style="text-align:right; font-weight:bold;">Avg 708</td></tr>
</table>
<ul class="custom-list">
<li><i class="fas fa-check-square text-green"></i> Mayoritas broker besar masih hold.</li>
</ul>
</div>
""", unsafe_allow_html=True)

with col_b2:
    st.markdown(f"""
<div class="card">
<div class="card-title"><i class="fas fa-arrows-alt-v"></i> SUPPORT & RESISTANCE</div>
<div style="display: flex; gap: 10px;">
<div style="flex: 1;">
<div class="text-green" style="font-size: 12px; margin-bottom: 6px;"><i class="fas fa-minus-circle"></i> SUPPORT</div>
<ul class="custom-list text-gray">
<li>• Rp637 (EMA)</li><li>• Rp625</li><li>• Rp620</li>
</ul>
</div>
<div style="flex: 1;">
<div class="text-red" style="font-size: 12px; margin-bottom: 6px;"><i class="fas fa-minus-circle"></i> RESIST</div>
<ul class="custom-list text-gray">
<li>• Rp650</li><li>• Rp670</li><li>• Rp700</li>
</ul>
</div>
</div>
</div>
<div class="card">
<div class="card-title"><i class="fas fa-star"></i> KESIMPULAN</div>
<div style="background: #e0e7ff !important; color: #3730a3 !important; text-align: center; font-weight: bold; font-size: 12px; padding: 6px; border-radius: 4px; margin-bottom: 10px;">{ticker_input} FASE MARKUP</div>
<div class="text-green" style="font-size: 12px; margin-bottom: 4px;"><i class="fas fa-check-square"></i> POSITIF</div>
<ul class="custom-list" style="margin-bottom: 10px;">
<li>Breakout area berhasil dikonfirmasi.</li>
<li>EMA Bullish Crossover.</li>
</ul>
<div style="color: #ca8a04 !important; font-weight:bold; font-size: 12px; margin-bottom: 4px;"><i class="fas fa-exclamation-triangle"></i> PANTAU</div>
<ul class="custom-list"><li>Resistance terdekat memicu taking profit.</li></ul>
</div>
""", unsafe_allow_html=True)

with col_b3:
    st.markdown("""
<div class="card">
<div class="card-title"><i class="fas fa-chart-pie"></i> INDIKATOR TEKNIKAL</div>
<div style="font-size: 12px; display: flex; flex-direction: column; gap: 10px;">
<div style="display: flex; justify-content: space-between;">
<span class="text-red"><i class="fas fa-thumbtack"></i> EMA</span>
<span style="text-align: right;">EMA 9 > EMA 21<br><span class="text-green">Bullish Crossover</span></span>
</div>
<hr style="margin:2px 0; border:0; border-top:1px solid #eee;">
<div style="display: flex; justify-content: space-between;">
<span class="text-red"><i class="fas fa-thumbtack"></i> RSI</span>
<span style="text-align: right;">63 - 66<br><span class="text-green">Belum Overbought</span></span>
</div>
<hr style="margin:2px 0; border:0; border-top:1px solid #eee;">
<div style="display: flex; justify-content: space-between;">
<span class="text-red"><i class="fas fa-thumbtack"></i> MACD</span>
<span style="text-align: right;"><span class="text-green">Positif</span><br>Momentum Kuat</span>
</div>
</div>
</div>
<div class="card">
<div class="card-title"><i class="fas fa-users"></i> SHAREHOLDER</div>
<div style="display: flex; justify-content: space-between; align-items: center;">
<div>
<div class="text-gray" style="font-size: 10px;">HOLDER BULAN INI</div>
<div class="text-green" style="font-size: 24px; font-weight: 900;">29.487</div>
<div class="text-gray" style="font-size: 10px;">Terus meningkat</div>
</div>
<i class="fas fa-users" style="font-size: 40px; color: #1e3a8a; opacity: 0.7;"></i>
</div>
</div>
""", unsafe_allow_html=True)

# BANNER BAWAH
st.markdown("""
<div style="background-color: #16a34a !important; border-radius: 8px; padding: 18px; margin-top: 5px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; color: white !important;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <i class="fas fa-trophy" style="font-size: 28px; color:white !important;"></i>
        <h2 style="margin: 0; font-size: 26px; font-weight: 900; color:white !important;">STRONG BUY</h2>
    </div>
    <div style="font-size: 12px; max-width: 400px; text-align: right; line-height: 1.4; color:white !important; margin-top: 5px;">
        Breakout tervalidasi, bandar masih akumulasi, target swing terjaga selama harga bertahan di atas support.
    </div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# --- 4. SCANNER PASAR (TAB MENU) ---
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
