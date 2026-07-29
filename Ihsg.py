import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="Dashboard Analisis Teknikal God-Tier", layout="wide")

st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# --- PANEL KONTROL (GOD-TIER VERSION) ---
# ==========================================
st.markdown("### ⚙️ PANEL KONTROL (GOD-TIER VERSION)")

# Dibagi menjadi 3 kolom agar rapi di HP maupun PC
col_in1, col_in2, col_in3 = st.columns(3)

with col_in1:
    ticker_input = st.text_input("🔍 1. Kode Saham:", "BBCA", help="Ketik kode lalu Enter").upper().strip()

with col_in2:
    status_bandar = st.selectbox(
        "🕵️‍♂️ 2. Bandarmology (Manual):", 
        ["Akumulasi (Net Buy)", "Netral / Sepi", "Distribusi (Net Sell)"]
    )

with col_in3:
    status_bidoffer = st.selectbox(
        "⚖️ 3. Bid & Offer (Manual):", 
        ["Dominan BID (Demand Kuat)", "Berimbang (Normal)", "Dominan OFFER (Supply Kuat)"]
    )

ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"
st.markdown("---")


# ==========================================
# --- MESIN KALKULASI DEWA (5 DIMENSI) ---
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
        
        # RSI 14
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi_val = rsi_series.iloc[-1]
        
        if rsi_val >= 70: rsi_status = "Overbought"
        elif rsi_val <= 30: rsi_status = "Oversold"
        else: rsi_status = "Netral"
        
        # SUPPORT & RESISTANCE (20 Days)
        res_terdekat = hist['High'].tail(20).max()
        sup_terdekat = hist['Low'].tail(20).min()
        
        # FIBONACCI RETRACEMENT LOGIC (60 Days Swing)
        swing_high = hist['High'].tail(60).max()
        swing_low = hist['Low'].tail(60).min()
        diff = swing_high - swing_low
        
        fibo_236 = swing_high - (0.236 * diff)
        fibo_382 = swing_high - (0.382 * diff)
        fibo_618 = swing_high - (0.618 * diff) # Golden Ratio
        
        if latest_price >= fibo_382:
            fibo_stat = "Bullish (> Fibo 38.2%)"
            fibo_score = 2
        elif latest_price >= fibo_618:
            fibo_stat = "Golden Pocket (> 61.8%)"
            fibo_score = 1
        else:
            fibo_stat = "Bearish (< Fibo 61.8%)"
            fibo_score = 0

        return {
            'price': latest_price, 'change': change_pct, 'div': dividend_yield, 'name': company_name,
            'ema_cross': ema_cross, 'trend': trend_status, 'rsi_val': rsi_val, 'rsi_status': rsi_status,
            'res': res_terdekat, 'sup': sup_terdekat, 'shares': shares,
            'swing_high': swing_high, 'fibo_382': fibo_382, 'fibo_618': fibo_618,
            'fibo_stat': fibo_stat, 'fibo_score': fibo_score
        }
    except:
        return None

data = get_stock_data(ticker_yf)
if data is None:
    st.error(f"❌ Saham **{ticker_input}** tidak valid atau data kurang. Coba saham Bluechip/Liquid.")
    st.stop()


# ==========================================
# --- ALGORITMA PENILAIAN 5 DIMENSI (MAX 10) ---
# ==========================================
score = 0
# 1. Tren Teknikal (Max 2)
if data['trend'] == "Bullish": score += 2

# 2. RSI Momentum (Max 1)
if data['rsi_status'] in ["Netral", "Oversold"]: score += 1

# 3. Fibonacci (Max 2)
score += data['fibo_score']

# 4. Bandarmology Manual (Max 3)
if "Akumulasi" in status_bandar: score += 3
elif "Netral" in status_bandar: score += 1

# 5. Orderbook Bid/Offer Manual (Max 2)
if "BID" in status_bidoffer: score += 2
elif "Berimbang" in status_bidoffer: score += 1


# ==========================================
# --- 1. HEADER DASHBOARD ---
# ==========================================
arrow = "▼" if data['change'] < 0 else "▲"
color = "#dc2626" if data['change'] < 0 else "#16a34a"
today_date = datetime.datetime.now().strftime("%d %B %Y")

col_h1, col_h2, col_h3 = st.columns([2, 1.2, 1.3])

with col_h1:
    st.markdown(f"📊 **ANALISIS TEKNIKAL PRO**")
    st.markdown(f"<h1 style='font-size: 3.2rem; margin-bottom: 0;'>{ticker_input}</h1>", unsafe_allow_html=True)
    st.markdown(f"**{data['name']}**")
    st.caption("AI + Fibo + Bandar + Orderbook (5D System)")
    st.info(f"Update {today_date} | Close Rp{int(data['price'])}")

with col_h2:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if score >= 8:
        st.success("**STRONG BUY**")
        st.markdown("⭐⭐⭐⭐⭐")
    elif score >= 5:
        st.warning("**HOLD / WAIT**")
        st.markdown("⭐⭐⭐")
    else:
        st.error("**SELL / AVOID**")
        st.markdown("⭐")
    st.markdown(f"### 🌟 {score}.0 <span style='font-size:14px; color:gray;'>/10</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_h3:
    st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
    st.caption("HARGA PENUTUPAN")
    st.markdown(f"## **Rp{int(data['price'])}**")
    st.markdown(f"<span style='color: {color}; font-weight: bold;'>{arrow} {data['change']:.2f}%</span>", unsafe_allow_html=True)
    st.caption("DIVIDEND YIELD")
    st.markdown(f"**{round(data['div'], 2) if isinstance(data['div'], (int, float)) else 'N/A'}%**")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()


# ==========================================
# --- 2. CHART & TRADE PLAN ---
# ==========================================
col_chart, col_plan = st.columns([2, 1])

with col_chart:
    tradingview_html = f"""
    <div style="border-radius: 8px; border: 1px solid #374151; overflow: hidden; background: #111827;">
        <div class="tradingview-widget-container" style="height: 400px; width: 100%;">
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
            "studies": ["Moving Average@tv-basicstudies"]
          }});
          </script>
        </div>
    </div>
    """
    components.html(tradingview_html, height=410)

with col_plan:
    with st.container(border=True):
        st.markdown("💰 **TRADE PLAN (God-Tier Signal)**")
        if score >= 8:
            st.markdown(f"🟢 **Entry:** Hajar Beli / HK di harga saat ini")
        elif score >= 5:
            st.markdown(f"🟡 **Entry:** Antre Beli di Support (Rp{int(data['sup'])})")
        else:
            st.markdown("🔴 **Entry:** JANGAN BELI (Sinyal Buruk)")
            
        st.markdown(f"🔴 **Stop Loss:** Jika jebol Rp{int(data['sup'])}")
        st.divider()
        st.markdown("🎯 **TARGET HARGA**")
        st.markdown(f"🥇 **TP 1 (Resist):** Rp{int(data['res'])}")
        st.markdown(f"🚀 **TP 2 (Swing Fibo):** Rp{int(data['swing_high'])}")
        
        reward = int(data['res']) - int(data['price'])
        risk = int(data['price']) - int(data['sup'])
        if risk > 0 and reward > 0:
            rr_ratio = round(reward / risk, 1)
            st.info(f"⚖️ Risk : Reward = 1 : {rr_ratio}")
        else:
            st.info("⚖️ Risk : Reward = Terlalu Ekstrem")


# ==========================================
# --- 3. INDIKATOR OTOMATIS & MANUAL ---
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    with st.container(border=True):
        st.markdown("📈 **TREND HARGA**")
        if data['trend'] == "Bullish":
            st.success(f"Status: **{data['trend']}**")
        else:
            st.error(f"Status: **{data['trend']}**")
    
    with st.container(border=True):
        st.markdown("🏦 **BANDAR & ORDERBOOK**")
        st.caption("Hasil Pantauan Manual Anda:")
        
        # Bandar
        if "Akumulasi" in status_bandar: st.success(f"✔️ Bandar: **Akumulasi**")
        elif "Distribusi" in status_bandar: st.error(f"❌ Bandar: **Distribusi**")
        else: st.warning(f"➖ Bandar: **Netral**")
        
        # Bid Offer
        if "BID" in status_bidoffer: st.success(f"✔️ Orderbook: **Dominan BID** (Antrean Beli Tebal)")
        elif "OFFER" in status_bidoffer: st.error(f"❌ Orderbook: **Dominan OFFER** (Antrean Jual Tebal)")
        else: st.warning(f"➖ Orderbook: **Berimbang**")

with col_b2:
    with st.container(border=True):
        st.markdown("📐 **LEVEL FIBONACCI (60D)**")
        col_f1, col_f2 = st.columns(2)
        col_f1.markdown(f"🔵 **Fibo 38.2%**\n- **Rp{int(data['fibo_382'])}**")
        col_f2.markdown(f"🟡 **Fibo 61.8%**\n- **Rp{int(data['fibo_618'])}**\n*(Golden Ratio)*")
    
    with st.container(border=True):
        st.markdown("⭐ **KESIMPULAN SINYAL BESOK**")
        if score >= 8:
            st.info(f"🔥 **{ticker_input} SIAP TERBANG**")
            st.markdown("Teknikal Bullish, Bandar Akumulasi, dan Demand (Bid) sangat kuat!")
        elif score >= 5 and "BID" in status_bidoffer:
            st.success(f"🎣 **POTENSI REBOUND {ticker_input}**")
            st.markdown("Meski tertahan, antrean Beli (Bid) tebal. Bandar mulai serok bawah.")
        elif score >= 5:
            st.warning(f"⚠️ **PANTAU KETAT {ticker_input}**")
            st.markdown("Sinyal belum bulat. Pantau reaksi harga di Golden Ratio Fibo besok.")
        else:
            st.error(f"💀 **JAUHI {ticker_input} SEMENTARA**")
            st.markdown("Trend patah, Bandar buang barang, Offer tebal. Awas nyangkut!")

with col_b3:
    with st.container(border=True):
        st.markdown("📊 **INDIKATOR TEKNIKAL**")
        st.markdown(f"📌 **EMA Cross:** {data['ema_cross']}")
        st.markdown(f"📌 **RSI (14):** {data['rsi_val']:.1f} - **{data['rsi_status']}**")
        st.markdown(f"📌 **Posisi Fibo:** {data['fibo_stat']}")
    
    with st.container(border=True):
        st.markdown("👥 **INFO PERUSAHAAN**")
        st.caption("JUMLAH SAHAM BEREDAR")
        if data['shares'] != "N/A":
            shares_fmt = f"{data['shares'] / 1e9:.2f} Miliar Lembar"
        else:
            shares_fmt = "Tidak diketahui"
        st.markdown(f"### **{shares_fmt}**")


# ==========================================
# --- 4. PUSAT DATA PASAR ELEGAN (DARK MODE) ---
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📊 Pusat Data Pasar (IHSG)")
tab_movers, tab_screener = st.tabs(["🔥 Top Movers & Trending", "🔎 Advanced Stock Scanner"])

with tab_movers:
    # PERBAIKAN TAMPILAN: colorTheme diset ke "dark", isTransparent "true", showChart "false"
    components.html("""
    <div class="tradingview-widget-container" style="height: 500px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>
      {
      "colorTheme": "dark",
      "dateRange": "12M",
      "exchange": "IDX",
      "showChart": false,
      "locale": "id",
      "width": "100%",
      "height": "100%",
      "isTransparent": true
      }
      </script>
    </div>
    """, height=500)

with tab_screener:
    components.html("""
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
      "colorTheme": "dark",
      "locale": "id",
      "isTransparent": true
      }
      </script>
    </div>
    """, height=600)
