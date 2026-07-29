import streamlit as st
import yfinance as yf
import datetime
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="Dashboard Analisis Teknikal", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# --- CUSTOM CSS (OPTIMASI LAYAR HP) ---
# ==========================================
# CSS ini memaksa Streamlit menghilangkan padding putih luas, 
# merapikan tampilan mobile, dan memuat FontAwesome untuk ikon.
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
    /* Menghilangkan padding bawaan Streamlit agar full screen di HP */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    header { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* Styling Dasar Card & Grid */
    .dashboard-container { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #ffffff; color: #000; }
    .v-spacer { margin-bottom: 15px; }
    .grid-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; margin-top: 12px; }
    .card { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .card-title { color: #1e3a8a; font-size: 13px; font-weight: 700; border-bottom: 2px solid #f3f4f6; padding-bottom: 6px; margin-bottom: 10px; text-transform: uppercase; display: flex; align-items: center; gap: 6px; }
    
    /* Warna Text */
    .text-blue { color: #1e3a8a; }
    .text-green { color: #16a34a; }
    .text-red { color: #dc2626; }
    .text-gray { color: #6b7280; }
    
    ul.custom-list { list-style: none; padding-left: 0; margin: 0; font-size: 11px; }
    ul.custom-list li { margin-bottom: 4px; display: flex; align-items: flex-start; gap: 6px; }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# --- SIDEBAR: FITUR PENCARIAN SAHAM ---
# ==========================================
st.sidebar.markdown("### 🔍 Cari Saham")
ticker_input = st.sidebar.text_input("Masukkan Kode Saham (Cth: BBCA, ESSA):", "ESSA").upper()
ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"


# ==========================================
# --- FUNGSI AMBIL DATA (YAHOO FINANCE) ---
# ==========================================
@st.cache_data(ttl=300)
def get_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="5d")
        if hist.empty:
            return None, None, None, None
            
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
    st.error(f"❌ Saham {ticker_input} tidak ditemukan.")
    st.stop()


# ==========================================
# --- TAMPILAN DASHBOARD UTAMA ---
# ==========================================
st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)

# 1. HEADER (Identik dengan foto)
arrow = "▼" if persen_perubahan < 0 else "▲"
color_hex = "#dc2626" if persen_perubahan < 0 else "#16a34a"
today_date = datetime.datetime.now().strftime("%d %B %Y")

header_html = f"""
<div class="card" style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px;">
    <!-- Kiri: Info Perusahaan -->
    <div style="flex: 1 1 250px;">
        <div style="background-color:#1e3a8a; color:white; display:inline-block; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:bold; margin-bottom:5px;"><i class="fas fa-chart-bar"></i> ANALISIS TEKNIKAL</div>
        <h1 style="color: #1e3a8a; font-size: 42px; font-weight: 900; margin: 0; line-height: 1;">{ticker_input}</h1>
        <div style="font-size: 13px; font-weight: bold; color: #111;">{nama_perusahaan}</div>
        <div style="font-size: 11px; color: #666;">Citadel Quant + Bandarmology</div>
        <div style="background-color:#1e3a8a; color:white; display:inline-block; padding:2px 6px; font-size:10px; margin-top:5px; border-radius:3px;">Update {today_date} | Close Rp{int(harga_sekarang)}</div>
    </div>
    
    <!-- Tengah: Rating (Tersembunyi di HP kecil agar rapi, atau menyesuaikan) -->
    <div style="flex: 1 1 150px; text-align: center; border-left: 1px solid #eee; border-right: 1px solid #eee; padding: 0 10px;">
        <div style="background-color: #16a34a; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 14px; display: inline-block;">STRONG BUY</div>
        <div style="color: #eab308; font-size: 14px; margin: 5px 0;"><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star"></i><i class="fas fa-star-half-alt"></i></div>
        <div style="margin: 0 auto; width: 60px; height: 60px; border: 2px solid #eab308; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ca8a04; font-size: 24px; font-weight: bold;">
            9,5<span style="font-size:10px; color:#666;">/10</span>
        </div>
    </div>
    
    <!-- Kanan: Harga -->
    <div style="flex: 1 1 150px; text-align: right;">
        <div style="font-size:10px; font-weight:bold; color:#666;">HARGA PENUTUPAN</div>
        <div style="color:#1e3a8a; font-size:32px; font-weight:bold; line-height:1.2;">Rp{int(harga_sekarang)}</div>
        <div style="color:{color_hex}; font-size:13px; font-weight:bold;">{arrow} {persen_perubahan:.2f}%</div>
        <div style="margin-top: 10px;">
            <div style="font-size:10px; font-weight:bold; color:#666;">DIVIDEND YIELD</div>
            <div style="color:#1e3a8a; font-size:18px; font-weight:bold;">{round(dividen, 2) if isinstance(dividen, (int, float)) else "N/A"}%</div>
        </div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)


# 2. CHART & TRADE PLAN (Responsive layout)
col_chart, col_plan = st.columns([2, 1])

with col_chart:
    st.markdown('<div class="card" style="padding:0; height:380px; overflow:hidden;">', unsafe_allow_html=True)
    tradingview_html = f"""
    <div class="tradingview-widget-container" style="height: 100%; width: 100%;">
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
    """
    components.html(tradingview_html, height=380)
    st.markdown('</div>', unsafe_allow_html=True)

with col_plan:
    trade_plan_html = """
    <div class="card" style="height:380px; font-size: 12px;">
        <div class="card-title"><i class="fas fa-money-bill-wave text-green"></i> TRADE PLAN</div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span class="text-green font-bold"><i class="fas fa-plus-circle"></i> Entry Agresif</span> <span class="font-bold">Wait & See</span></div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span class="text-green font-bold"><i class="fas fa-plus-circle"></i> Buy on Pullback</span> <span class="font-bold">Wait Setup</span></div>
        <div style="display:flex; justify-content:space-between; margin-bottom:15px;"><span class="text-red font-bold"><i class="fas fa-times-circle"></i> Stop Loss</span> <span class="text-red font-bold">Auto</span></div>
        
        <div class="card-title" style="margin-top:15px;"><i class="fas fa-bullseye text-green"></i> TARGET</div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;"><span class="font-bold">🥇 TP 1 :</span> <span>TBA</span></div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;"><span class="font-bold">🥈 TP 2 :</span> <span>TBA</span></div>
        <div style="display:flex; justify-content:space-between; margin-bottom:15px;"><span class="font-bold">🚀 Swing :</span> <span>TBA</span></div>
        
        <div style="background: #f3f4f6; padding: 8px; text-align: center; border-radius: 4px; font-weight: bold; margin-top: auto;">
            ⚖️ Risk : Reward &nbsp;&nbsp; <span class="text-green" style="font-size: 14px;">± 1 : 3</span>
        </div>
    </div>
    """
    st.markdown(trade_plan_html, unsafe_allow_html=True)


# 3. BAGIAN BAWAH (FULL CUSTOM HTML GRID - Identik dengan Poster)
bottom_grid_html = f"""
<div class="grid-container">

    <!-- Kolom 1 -->
    <div style="display: flex; flex-direction: column; gap: 12px;">
        <div class="card">
            <div class="card-title"><i class="fas fa-chart-line"></i> TREND</div>
            <div style="display: flex; justify-content: space-between; text-align: center; font-size: 10px; margin-bottom: 10px;">
                <div><div style="background:#dcfce7; color:#16a34a; padding:2px 4px; border-radius:3px; font-weight:bold; margin-bottom:3px;"><i class="fas fa-check-circle"></i> DAILY</div><span style="font-weight:bold;">Bullish</span></div>
                <div><div style="background:#dcfce7; color:#16a34a; padding:2px 4px; border-radius:3px; font-weight:bold; margin-bottom:3px;"><i class="fas fa-check-circle"></i> WEEKLY</div><span style="font-weight:bold;">Bullish</span></div>
                <div><div style="background:#dcfce7; color:#16a34a; padding:2px 4px; border-radius:3px; font-weight:bold; margin-bottom:3px;"><i class="fas fa-check-circle"></i> MONTHLY</div><span style="font-weight:bold;">Bullish</span></div>
            </div>
            <ul class="custom-list">
                <li><i class="fas fa-check text-green"></i> Higher High</li>
                <li><i class="fas fa-check text-green"></i> Higher Low</li>
                <li><i class="fas fa-check text-green"></i> Breakout Area</li>
            </ul>
        </div>
        
        <div class="card">
            <div class="card-title"><i class="fas fa-building"></i> BANDARMOLOGY</div>
            <div style="font-size: 9px; color: #666; margin-bottom: 5px; font-weight: bold;">AKUMULASI BROKER TERBESAR</div>
            <table style="width: 100%; font-size: 11px; margin-bottom: 10px; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #eee;"><td style="padding:3px 0;">🟨 LG</td><td style="text-align:right;">15,3 Juta Lot</td><td style="text-align:right; font-weight:bold;">Avg 639</td></tr>
                <tr style="border-bottom: 1px solid #eee;"><td style="padding:3px 0;">⬜ CC</td><td style="text-align:right;">2,2 Juta Lot</td><td style="text-align:right; font-weight:bold;">Avg 711</td></tr>
                <tr style="border-bottom: 1px solid #eee;"><td style="padding:3px 0;">🟧 XL</td><td style="text-align:right;">1,9 Juta Lot</td><td style="text-align:right; font-weight:bold;">Avg 708</td></tr>
            </table>
            <ul class="custom-list">
                <li><i class="fas fa-check-square text-green"></i> Mayoritas broker besar masih hold.</li>
                <li><i class="fas fa-check-square text-green"></i> Belum ada distribusi besar.</li>
            </ul>
        </div>
    </div>

    <!-- Kolom 2 -->
    <div style="display: flex; flex-direction: column; gap: 12px;">
        <div class="card">
            <div class="card-title"><i class="fas fa-arrows-alt-v"></i> SUPPORT & RESISTANCE</div>
            <div style="display: flex; gap: 10px;">
                <div style="flex: 1;">
                    <div class="text-green" style="font-size: 11px; font-weight: bold; margin-bottom: 5px;"><i class="fas fa-minus-circle"></i> SUPPORT</div>
                    <ul class="custom-list" style="color:#444;">
                        <li>• Rp637 (EMA21)</li>
                        <li>• Rp625</li>
                        <li>• Rp620</li>
                    </ul>
                </div>
                <div style="flex: 1;">
                    <div class="text-red" style="font-size: 11px; font-weight: bold; margin-bottom: 5px;"><i class="fas fa-minus-circle"></i> RESISTANCE</div>
                    <ul class="custom-list" style="color:#444;">
                        <li>• Rp650</li>
                        <li>• Rp670</li>
                        <li>• Rp700</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title"><i class="fas fa-star"></i> KESIMPULAN</div>
            <div style="background: #e0e7ff; color: #3730a3; text-align: center; font-weight: bold; font-size: 11px; padding: 5px; border-radius: 4px; margin-bottom: 8px;">{ticker_input} MEMASUKI FASE MARKUP</div>
            <div style="font-size: 11px; font-weight: bold; color: #16a34a; margin-bottom: 3px;"><i class="fas fa-check-square"></i> POSITIF</div>
            <ul class="custom-list" style="margin-bottom: 8px;">
                <li>Breakout area berhasil dikonfirmasi.</li>
                <li>EMA Bullish Crossover.</li>
            </ul>
            <div style="font-size: 11px; font-weight: bold; color: #ca8a04; margin-bottom: 3px;"><i class="fas fa-exclamation-triangle"></i> PERLU DIPANTAU</div>
            <ul class="custom-list">
                <li>Area resistance terdekat berpotensi memicu taking profit.</li>
            </ul>
        </div>
    </div>

    <!-- Kolom 3 -->
    <div style="display: flex; flex-direction: column; gap: 12px;">
        <div class="card">
            <div class="card-title"><i class="fas fa-chart-pie"></i> INDIKATOR TEKNIKAL</div>
            <div style="font-size: 11px; display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; justify-content: space-between;">
                    <span class="text-red font-bold"><i class="fas fa-thumbtack"></i> EMA</span>
                    <span style="text-align: right;">EMA 9 > EMA 21<br><span class="text-green font-bold">Bullish Crossover</span></span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span class="text-red font-bold"><i class="fas fa-thumbtack"></i> RSI</span>
                    <span style="text-align: right;">63 - 66<br><span class="text-green font-bold">Belum Overbought</span></span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span class="text-red font-bold"><i class="fas fa-thumbtack"></i> MACD</span>
                    <span style="text-align: right;"><span class="text-green font-bold">Positif</span><br>Momentum Kuat</span>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title"><i class="fas fa-users"></i> SHAREHOLDER</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 9px; font-weight: bold; color: #666;">HOLDER JUNI 2026</div>
                    <div style="color: #16a34a; font-size: 20px; font-weight: 900;">29.487</div>
                    <div style="font-size: 9px; color: #666;">Terus meningkat</div>
                </div>
                <i class="fas fa-users" style="font-size: 32px; color: #1e3a8a; opacity: 0.8;"></i>
            </div>
        </div>
    </div>

</div>

<!-- FOOTER BANNER -->
<div style="background-color: #16a34a; border-radius: 8px; padding: 15px; margin-top: 15px; display: flex; justify-content: space-between; align-items: center; color: white;">
    <div style="display: flex; align-items: center; gap: 10px;">
        <i class="fas fa-trophy" style="font-size: 24px;"></i>
        <h2 style="margin: 0; font-size: 24px; font-weight: 900;">STRONG BUY</h2>
    </div>
    <div style="font-size: 10px; max-width: 50%; text-align: right; line-height: 1.3;">
        Breakout tervalidasi, bandar masih akumulasi, target swing terjaga selama harga bertahan di atas support.
    </div>
</div>
"""
st.markdown(bottom_grid_html, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True) # Tutup dashboard container


# ==========================================
# --- BAGIAN 4: SCANNER (Tetap Tersedia di Bawah) ---
# ==========================================
st.markdown("<br><hr><h3 style='color: #1e3a8a; text-align: center;'>Pusat Data Pasar (IHSG)</h3>", unsafe_allow_html=True)
tab_movers, tab_screener = st.tabs(["🔥 Top Movers & Trending", "🔎 Advanced Stock Scanner"])

with tab_movers:
    hotlist_html = """
    <div class="tradingview-widget-container" style="height: 500px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>
      { "colorTheme": "light", "dateRange": "12M", "exchange": "IDX", "showChart": true, "locale": "id", "width": "100%", "height": "100%" }
      </script>
    </div>
    """
    components.html(hotlist_html, height=500)

with tab_screener:
    screener_html = """
    <div class="tradingview-widget-container" style="height: 600px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
      { "width": "100%", "height": "100%", "defaultColumn": "overview", "defaultScreen": "general", "market": "indonesia", "showToolbar": true, "colorTheme": "light", "locale": "id" }
      </script>
    </div>
    """
    components.html(screener_html, height=600)
