import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="HOLY GRAIL - Technical Dashboard", layout="wide")

# CSS PREMIUM (BEBAS KOMENTAR AGAR TIDAK BOCOR)
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
header {visibility: hidden;}
div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #111827 !important; border: 1px solid #374151 !important; border-radius: 10px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important; padding: 0.8rem !important; height: 100% !important;}
p, span, li, div.stMarkdown, .stText {font-size: 0.8rem !important; line-height: 1.5 !important;}
h1 {font-size: 2.5rem !important; margin-bottom: 0.2rem !important;}
h2 {font-size: 1.8rem !important; margin-bottom: 0.2rem !important;}
h3 {font-size: 1.2rem !important; margin-bottom: 0.5rem !important;}
hr {margin-top: 0.8rem; margin-bottom: 0.8rem; border-color: #374151;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# --- PANEL KONTROL (GOD-TIER VERSION) ---
# ==========================================
st.markdown("### ⚙️ PANEL KONTROL (HOLY GRAIL SYSTEM)")

col_in1, col_in2, col_in3 = st.columns(3)
with col_in1:
    ticker_input = st.text_input("🔍 1. Kode Saham (Ketik & Enter):", "BBCA").upper().strip()
with col_in2:
    status_bandar = st.selectbox("🕵️‍♂️ 2. Bandarmology (Manual):", ["Akumulasi (Net Buy)", "Netral / Sepi", "Distribusi (Net Sell)"])
with col_in3:
    status_bidoffer = st.selectbox("⚖️ 3. Bid & Offer (Manual):", ["Dominan BID (Demand Kuat)", "Berimbang (Normal)", "Dominan OFFER (Supply Kuat)"])

col_mm1, col_mm2 = st.columns(2)
with col_mm1:
    modal_input = st.number_input("💰 4. Modal Trading Anda (Rp):", min_value=100000, value=10000000, step=1000000)
with col_mm2:
    risiko_input = st.selectbox("🛡️ 5. Toleransi Risiko (Cutloss):", ["1% dari Modal (Sangat Konservatif)", "2% dari Modal (Standar Pro)", "3% dari Modal (Agresif)", "5% dari Modal (Sangat Agresif)"], index=1)

ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"
st.markdown("---")


# ==========================================
# --- MESIN KALKULASI DEWA (7 DIMENSI) ---
# ==========================================
@st.cache_data(ttl=300)
def get_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="6mo")
        if hist.empty or len(hist) < 60: return None
            
        latest_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change_pct = ((latest_price - prev_price) / prev_price) * 100
        info = stock.info
        
        div_yield_raw = info.get('dividendYield', 0)
        dividend_yield = div_yield_raw * 100 if div_yield_raw and div_yield_raw < 1 else div_yield_raw
        
        company_name = info.get('longName', f"PT {ticker_symbol.replace('.JK', '')} Tbk")
        shares = info.get('sharesOutstanding', "N/A")
        
        close_prices = hist['Close']
        
        ema9 = close_prices.ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = close_prices.ewm(span=21, adjust=False).mean().iloc[-1]
        ema_cross = "Bullish (EMA9 > EMA21)" if ema9 > ema21 else "Bearish (EMA9 < EMA21)"
        trend_status = "Bullish" if latest_price > ema21 else "Bearish"
        
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi_val = rsi_series.iloc[-1]
        if rsi_val >= 70: rsi_status = "Overbought"
        elif rsi_val <= 30: rsi_status = "Oversold"
        else: rsi_status = "Netral"
        
        res_terdekat = hist['High'].tail(20).max()
        sup_terdekat = hist['Low'].tail(20).min()
        
        swing_high = hist['High'].tail(60).max()
        swing_low = hist['Low'].tail(60).min()
        diff = swing_high - swing_low
        fibo_382 = swing_high - (0.382 * diff)
        fibo_618 = swing_high - (0.618 * diff)
        if latest_price >= fibo_382: fibo_stat, fibo_score = "Aman (> Fibo 38.2%)", 1
        elif latest_price >= fibo_618: fibo_stat, fibo_score = "Golden Pocket (> 61.8%)", 1
        else: fibo_stat, fibo_score = "Jebol (< Fibo 61.8%)", 0

        vol_latest = hist['Volume'].iloc[-1]
        vol_ma20 = hist['Volume'].rolling(20).mean().iloc[-1]
        vol_ratio = (vol_latest / vol_ma20) * 100 if vol_ma20 > 0 else 0
        if vol_ratio > 150: vpa_stat, vpa_score = f"Ledakan Volume ({int(vol_ratio)}%)", 1
        elif vol_ratio < 80: vpa_stat, vpa_score = f"Volume Kering ({int(vol_ratio)}%)", 0
        else: vpa_stat, vpa_score = f"Volume Normal ({int(vol_ratio)}%)", 0

        sma20 = close_prices.rolling(20).mean()
        std20 = close_prices.rolling(20).std()
        bandwidth = ( (sma20 + (2 * std20)) - (sma20 - (2 * std20)) ) / sma20
        bw_latest = bandwidth.iloc[-1]
        bw_120_min = bandwidth.tail(120).min()
        
        if bw_latest <= (bw_120_min * 1.25):
            bb_stat = "🔥 SQUEEZE (Siaga Meledak)"
        else:
            bb_stat = "Normal / Ekspansi"

        return {
            'price': latest_price, 'change': change_pct, 'div': dividend_yield, 'name': company_name,
            'ema_cross': ema_cross, 'trend': trend_status, 'rsi_val': rsi_val, 'rsi_status': rsi_status,
            'res': res_terdekat, 'sup': sup_terdekat, 'shares': shares,
            'swing_high': swing_high, 'fibo_382': fibo_382, 'fibo_618': fibo_618,
            'fibo_stat': fibo_stat, 'fibo_score': fibo_score,
            'vpa_stat': vpa_stat, 'vpa_score': vpa_score, 'bb_stat': bb_stat
        }
    except:
        return None

data = get_stock_data(ticker_yf)
if data is None:
    st.error(f"❌ Saham **{ticker_input}** tidak valid atau data kurang. Coba saham Bluechip/Liquid (misal: BBCA, ASII).")
    st.stop()


# ==========================================
# --- ALGORITMA PENILAIAN SKOR SEMPURNA (MAX 10) ---
# ==========================================
score = 0
if data['trend'] == "Bullish": score += 2
if "Akumulasi" in status_bandar: score += 3
elif "Netral" in status_bandar: score += 1
if "BID" in status_bidoffer: score += 2
elif "Berimbang" in status_bidoffer: score += 1
if data['rsi_status'] in ["Netral", "Oversold"]: score += 1
score += data['fibo_score']
score += data['vpa_score']


# ==========================================
# --- CALCULATOR MONEY MANAGEMENT ---
# ==========================================
risk_pct = float(risiko_input.split('%')[0]) / 100
max_loss_rp = modal_input * risk_pct
risk_per_share = data['price'] - data['sup']
if risk_per_share <= 0: risk_per_share = data['price'] * 0.02 
max_shares = max_loss_rp / risk_per_share
max_lot = int(max_shares / 100)
if max_lot < 1: max_lot = 0


# ==========================================
# --- 1. HEADER DASHBOARD ---
# ==========================================
arrow = "▼" if data['change'] < 0 else "▲"
color = "#f87171" if data['change'] < 0 else "#4ade80" 
today_date = datetime.datetime.now().strftime("%d %B %Y")

col_h1, col_h2, col_h3 = st.columns([2, 1.2, 1.3])

with col_h1:
    st.markdown(f"**HOLY GRAIL SYSTEM**")
    st.markdown(f"<h1 style='color:#f3f4f6;'>{ticker_input}</h1>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#9ca3af; font-weight:bold;'>{data['name']}</span>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.75rem; color:#60a5fa;'>Update {today_date} | Close Rp{int(data['price'])}</div>", unsafe_allow_html=True)

with col_h2:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if score >= 8:
        st.markdown("<span style='color:#4ade80; font-weight:bold;'>STRONG BUY</span>", unsafe_allow_html=True)
        st.markdown("⭐⭐⭐⭐⭐")
    elif score >= 5:
        st.markdown("<span style='color:#fbbf24; font-weight:bold;'>HOLD / WAIT</span>", unsafe_allow_html=True)
        st.markdown("⭐⭐⭐")
    else:
        st.markdown("<span style='color:#f87171; font-weight:bold;'>SELL / AVOID</span>", unsafe_allow_html=True)
        st.markdown("⭐")
    st.markdown(f"### 🌟 {score}.0 <span style='font-size:0.8rem; color:#9ca3af;'>/10</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_h3:
    st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
    st.markdown("<span style='color:#9ca3af; font-size:0.75rem;'>HARGA PENUTUPAN</span>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#f3f4f6;'>Rp{int(data['price'])}</h2>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: {color}; font-weight: bold;'>{arrow} {data['change']:.2f}%</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#9ca3af; font-size:0.75rem;'>DIVIDEND YIELD</span><br><span style='color:#9ca3af; font-weight:bold;'>{round(data['div'], 2) if isinstance(data['div'], (int, float)) else 'N/A'}%</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()


# ==========================================
# --- 2. CHART & TRADE PLAN ---
# ==========================================
col_chart, col_plan = st.columns([2.2, 1.2])

with col_chart:
    tradingview_html = f"""
    <div style="border-radius: 10px; border: 1px solid #374151; overflow: hidden; background: #111827;">
        <div class="tradingview-widget-container" style="height: 480px; width: 100%;">
          <div id="tradingview_chart" style="height: 100%; width: 100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "autosize": true,
            "symbol": "{ticker_tv}",
            "interval": "D",
            "timezone": "Asia/Jakarta",
            "theme": "dark",
            "style": "1",
            "locale": "id",
            "enable_publishing": false,
            "hide_top_toolbar": true,
            "hide_legend": false,
            "save_image": false,
            "container_id": "tradingview_chart",
            "studies": ["Moving Average@tv-basicstudies", "Volume@tv-basicstudies"]
          }});
          </script>
        </div>
    </div>
    """
    components.html(tradingview_html, height=490)

with col_plan:
    with st.container(border=True):
        st.markdown("💰 <strong>TRADE PLAN (God-Tier)</strong>", unsafe_allow_html=True)
        if score >= 8: st.markdown(f"<span style='color:#4ade80;'><strong>Entry:</strong> Hajar Beli di Rp{int(data['price'])}</span>", unsafe_allow_html=True)
        elif score >= 5: st.markdown(f"<span style='color:#fbbf24;'><strong>Entry:</strong> Antre di Support Rp{int(data['sup'])}</span>", unsafe_allow_html=True)
        else: st.markdown("<span style='color:#f87171;'><strong>Entry:</strong> JANGAN BELI (Wait & See)</span>", unsafe_allow_html=True)
            
        st.markdown(f"<span style='color:#f87171;'><strong>Stop Loss:</strong> Jika jebol Rp{int(data['sup'])}</span>", unsafe_allow_html=True)
        
        st.markdown("<br>🎯 <strong>TARGET HARGA</strong>", unsafe_allow_html=True)
        st.markdown(f"🥇 <strong>TP 1 (Resist):</strong> Rp{int(data['res'])}", unsafe_allow_html=True)
        st.markdown(f"🚀 <strong>TP 2 (Fibo Swing):</strong> Rp{int(data['swing_high'])}", unsafe_allow_html=True)
        
        reward = int(data['res']) - int(data['price'])
        if risk_per_share > 0 and reward > 0:
            st.markdown(f"<div style='background:#1e3a8a; color:white; padding:8px; border-radius:6px; text-align:center; font-weight:bold; margin: 10px 0;'>⚖️ Risk : Reward = 1 : {round(reward / risk_per_share, 1)}</div>", unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 15px 0; border-color:#374151;'>🛡️ <strong>MONEY MANAGEMENT</strong>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:#9ca3af;'>Berdasarkan Modal Rp{modal_input:,.0f} & Risiko {risk_pct*100}%</span>", unsafe_allow_html=True)
        if max_lot > 0 and score >= 5:
            st.markdown(f"<div style='background:#065f46; color:#a7f3d0; padding:10px; border-radius:6px; text-align:center; margin-top:5px;'>🛒 MAKSIMAL BELI:<br><span style='font-size:1.4rem; font-weight:bold;'>{max_lot} LOT</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color:#9ca3af; font-style:italic; text-align:center; margin-top:5px;'>(Jika kena Stop Loss, Anda hanya rugi maksimal Rp{max_loss_rp:,.0f})</div>", unsafe_allow_html=True)
        elif score < 5:
            st.error("🚫 Sinyal Buruk. Jangan Beli.")
        else:
            st.warning("⚠️ Risiko Terlalu Besar (Modal tidak cukup untuk 1 Lot).")


# ==========================================
# --- 3. INDIKATOR OTOMATIS & MANUAL ---
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    with st.container(border=True):
        st.markdown("📈 <strong>TREND & SQUEEZE</strong>", unsafe_allow_html=True)
        st.markdown(f"<strong>Tren Utama:</strong> {data['trend']}", unsafe_allow_html=True)
        if "SQUEEZE" in data['bb_stat']: st.markdown(f"<span style='color:#f87171; font-weight:bold;'>{data['bb_stat']}</span>", unsafe_allow_html=True)
        else: st.markdown(f"<span style='color:#4ade80;'>{data['bb_stat']}</span>", unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 15px 0; border-color:#374151;'>🏦 <strong>BANDAR & ORDERBOOK</strong>", unsafe_allow_html=True)
        if "Akumulasi" in status_bandar: st.markdown("✔️ Bandar: <strong><span style='color:#4ade80;'>Akumulasi</span></strong>", unsafe_allow_html=True)
        elif "Distribusi" in status_bandar: st.markdown("❌ Bandar: <strong><span style='color:#f87171;'>Distribusi</span></strong>", unsafe_allow_html=True)
        else: st.markdown("➖ Bandar: <strong><span style='color:#fbbf24;'>Netral</span></strong>", unsafe_allow_html=True)
        
        if "BID" in status_bidoffer: st.markdown("✔️ Bid/Offer: <strong><span style='color:#4ade80;'>Dominan BID</span></strong>", unsafe_allow_html=True)
        elif "OFFER" in status_bidoffer: st.markdown("❌ Bid/Offer: <strong><span style='color:#f87171;'>Dominan OFFER</span></strong>", unsafe_allow_html=True)
        else: st.markdown("➖ Bid/Offer: <strong><span style='color:#fbbf24;'>Berimbang</span></strong>", unsafe_allow_html=True)

with col_b2:
    with st.container(border=True):
        st.markdown("📐 <strong>FIBO & VOLUME (VPA)</strong>", unsafe_allow_html=True)
        st.markdown(f"<strong>Posisi Fibo:</strong> {data['fibo_stat']}", unsafe_allow_html=True)
        st.markdown(f"<strong>Golden Ratio (61.8%):</strong> Rp{int(data['fibo_618'])}", unsafe_allow_html=True)
        if data['vpa_score'] == 1: st.markdown(f"<div style='background:#065f46; color:#a7f3d0; padding:4px 8px; border-radius:4px; margin-top:5px;'>📊 VPA: {data['vpa_stat']}</div>", unsafe_allow_html=True)
        else: st.markdown(f"<div style='background:#78350f; color:#fde68a; padding:4px 8px; border-radius:4px; margin-top:5px;'>📊 VPA: {data['vpa_stat']}</div>", unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 15px 0; border-color:#374151;'>⭐ <strong>KESIMPULAN SINYAL</strong>", unsafe_allow_html=True)
        if score >= 8 and "SQUEEZE" in data['bb_stat']:
            st.info(f"🌋 **JACKPOT! {ticker_input} SIAP MELEDAK** - Sinyal Sempurna. Hajar Kanan sekarang!")
        elif score >= 8:
            st.success(f"🔥 **{ticker_input} SANGAT POTENSIAL** - Teknikal Bullish, Bandar Akumulasi, Demand Kuat!")
        elif score >= 5:
            st.warning(f"⚠️ **PANTAU KETAT {ticker_input}** - Beli cicil di area Support / Fibo 61.8%.")
        else:
            st.error(f"💀 **JAUHI {ticker_input} SEMENTARA** - Distribusi kuat / Trend hancur.")

with col_b3:
    with st.container(border=True):
        st.markdown("📊 <strong>INDIKATOR TEKNIKAL</strong>", unsafe_allow_html=True)
        st.markdown(f"📌 <strong>EMA Cross:</strong> {data['ema_cross']}", unsafe_allow_html=True)
        st.markdown(f"📌 <strong>RSI (14):</strong> {data['rsi_val']:.1f} - <strong>{data['rsi_status']}</strong>", unsafe_allow_html=True)
        st.markdown(f"🟢 <strong>Support:</strong> Rp{int(data['sup'])}", unsafe_allow_html=True)
        st.markdown(f"🔴 <strong>Resistance:</strong> Rp{int(data['res'])}", unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 15px 0; border-color:#374151;'>👥 <strong>INFO PERUSAHAAN</strong>", unsafe_allow_html=True)
        st.markdown("<span style='color:#9ca3af;'>JUMLAH SAHAM BEREDAR</span>", unsafe_allow_html=True)
        if data['shares'] != "N/A":
            st.markdown(f"<strong>{data['shares'] / 1e9:.2f} Miliar Lembar</strong>", unsafe_allow_html=True)
        else:
            st.markdown("<strong>Tidak diketahui</strong>", unsafe_allow_html=True)


# ==========================================
# --- 4. PUSAT DATA PASAR ELEGAN (FIXED HEIGHT) ---
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📊 Pusat Data Pasar (IHSG)")
tab_movers, tab_screener = st.tabs(["🔥 Top Movers & Trending", "🔎 Advanced Stock Scanner"])

with tab_movers:
    components.html("""
    <div class="tradingview-widget-container" style="height: 700px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>
      { "colorTheme": "dark", "dateRange": "12M", "exchange": "IDX", "showChart": false, "locale": "id", "width": "100%", "height": "700", "isTransparent": true }
      </script>
    </div>
    """, height=700)

with tab_screener:
    components.html("""
    <div class="tradingview-widget-container" style="height: 700px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
      { "width": "100%", "height": "700", "defaultColumn": "overview", "defaultScreen": "general", "market": "indonesia", "showToolbar": true, "colorTheme": "dark", "locale": "id", "isTransparent": true }
      </script>
    </div>
    """, height=700)
