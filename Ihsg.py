import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="HOLY GRAIL - Technical Dashboard", layout="wide")

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
st.markdown("### ⚙️ PANEL KONTROL (HOLY GRAIL SYSTEM)")

# Baris 1: Input Saham & Manual Bandar
col_in1, col_in2, col_in3 = st.columns(3)
with col_in1:
    ticker_input = st.text_input("🔍 1. Kode Saham (Ketik & Enter):", "BBCA").upper().strip()
with col_in2:
    status_bandar = st.selectbox("🕵️‍♂️ 2. Bandarmology (Manual):", ["Akumulasi (Net Buy)", "Netral / Sepi", "Distribusi (Net Sell)"])
with col_in3:
    status_bidoffer = st.selectbox("⚖️ 3. Bid & Offer (Manual):", ["Dominan BID (Demand Kuat)", "Berimbang (Normal)", "Dominan OFFER (Supply Kuat)"])

# Baris 2: Money Management
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
        
        # 1. EMA
        ema9 = close_prices.ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = close_prices.ewm(span=21, adjust=False).mean().iloc[-1]
        ema_cross = "Bullish (EMA9 > EMA21)" if ema9 > ema21 else "Bearish (EMA9 < EMA21)"
        trend_status = "Bullish" if latest_price > ema21 else "Bearish"
        
        # 2. RSI 14
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi_val = rsi_series.iloc[-1]
        if rsi_val >= 70: rsi_status = "Overbought"
        elif rsi_val <= 30: rsi_status = "Oversold"
        else: rsi_status = "Netral"
        
        # 3. SUPPORT & RESISTANCE (20 Days)
        res_terdekat = hist['High'].tail(20).max()
        sup_terdekat = hist['Low'].tail(20).min()
        
        # 4. FIBONACCI RETRACEMENT
        swing_high = hist['High'].tail(60).max()
        swing_low = hist['Low'].tail(60).min()
        diff = swing_high - swing_low
        fibo_382 = swing_high - (0.382 * diff)
        fibo_618 = swing_high - (0.618 * diff) # Golden Ratio
        if latest_price >= fibo_382: fibo_stat, fibo_score = "Aman (> Fibo 38.2%)", 1
        elif latest_price >= fibo_618: fibo_stat, fibo_score = "Golden Pocket (> 61.8%)", 1
        else: fibo_stat, fibo_score = "Jebol (< Fibo 61.8%)", 0

        # 5. VOLUME PRICE ANALYSIS (VPA)
        vol_latest = hist['Volume'].iloc[-1]
        vol_ma20 = hist['Volume'].rolling(20).mean().iloc[-1]
        vol_ratio = (vol_latest / vol_ma20) * 100 if vol_ma20 > 0 else 0
        if vol_ratio > 150: vpa_stat, vpa_score = f"Ledakan Volume ({int(vol_ratio)}%)", 1
        elif vol_ratio < 80: vpa_stat, vpa_score = f"Volume Kering ({int(vol_ratio)}%)", 0
        else: vpa_stat, vpa_score = f"Volume Normal ({int(vol_ratio)}%)", 0

        # 6. BOLLINGER BANDS SQUEEZE
        sma20 = close_prices.rolling(20).mean()
        std20 = close_prices.rolling(20).std()
        bandwidth = ( (sma20 + (2 * std20)) - (sma20 - (2 * std20)) ) / sma20
        bw_latest = bandwidth.iloc[-1]
        bw_120_min = bandwidth.tail(120).min()
        
        if bw_latest <= (bw_120_min * 1.25): # Jarak pita sangat sempit mendekati rekor 6 bulan
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
    st.error(f"❌ Saham **{ticker_input}** tidak valid atau data kurang. Coba saham lain.")
    st.stop()


# ==========================================
# --- ALGORITMA PENILAIAN SKOR SEMPURNA (MAX 10) ---
# ==========================================
score = 0
if data['trend'] == "Bullish": score += 2           # Trend (Max 2)
if "Akumulasi" in status_bandar: score += 3         # Bandar (Max 3)
elif "Netral" in status_bandar: score += 1
if "BID" in status_bidoffer: score += 2             # BidOffer (Max 2)
elif "Berimbang" in status_bidoffer: score += 1
if data['rsi_status'] in ["Netral", "Oversold"]: score += 1 # RSI (Max 1)
score += data['fibo_score']                         # Fibo (Max 1)
score += data['vpa_score']                          # VPA/Volume (Max 1)


# ==========================================
# --- CALCULATOR MONEY MANAGEMENT ---
# ==========================================
risk_pct = float(risiko_input.split('%')[0]) / 100
max_loss_rp = modal_input * risk_pct
risk_per_share = data['price'] - data['sup']
# Jika harga dekat/di bawah support, set risiko minimal 2% agar tidak error bagi 0
if risk_per_share <= 0: risk_per_share = data['price'] * 0.02 
max_shares = max_loss_rp / risk_per_share
max_lot = int(max_shares / 100)
if max_lot < 1: max_lot = 0 # Modal tidak cukup untuk 1 lot sesuai profil risiko


# ==========================================
# --- 1. HEADER DASHBOARD ---
# ==========================================
arrow = "▼" if data['change'] < 0 else "▲"
color = "#dc2626" if data['change'] < 0 else "#16a34a"
today_date = datetime.datetime.now().strftime("%d %B %Y")

col_h1, col_h2, col_h3 = st.columns([2, 1.2, 1.3])

with col_h1:
    st.markdown(f"📊 **HOLY GRAIL SYSTEM**")
    st.markdown(f"<h1 style='font-size: 3.5rem; margin-bottom: 0;'>{ticker_input}</h1>", unsafe_allow_html=True)
    st.markdown(f"**{data['name']}**")
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
col_chart, col_plan = st.columns([2.2, 1.2])

with col_chart:
    tradingview_html = f"""
    <div style="border-radius: 8px; border: 1px solid #374151; overflow: hidden; background: #111827;">
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
        st.markdown("💰 **TRADE PLAN (God-Tier)**")
        if score >= 8: st.markdown(f"🟢 **Entry:** Hajar Beli di Rp{int(data['price'])}")
        elif score >= 5: st.markdown(f"🟡 **Entry:** Antre di Support Rp{int(data['sup'])}")
        else: st.markdown("🔴 **Entry:** JANGAN BELI (Wait & See)")
            
        st.markdown(f"🔴 **Stop Loss:** Jika jebol Rp{int(data['sup'])}")
        
        st.markdown("🎯 **TARGET HARGA**")
        st.markdown(f"🥇 **TP 1 (Resist):** Rp{int(data['res'])}")
        st.markdown(f"🚀 **TP 2 (Fibo Swing):** Rp{int(data['swing_high'])}")
        
        reward = int(data['res']) - int(data['price'])
        if risk_per_share > 0 and reward > 0:
            st.info(f"⚖️ Risk : Reward = 1 : {round(reward / risk_per_share, 1)}")
        else:
            st.info("⚖️ Risk : Reward = Negatif/Ekstrem")

    with st.container(border=True):
        st.markdown("🛡️ **MONEY MANAGEMENT**")
        st.caption(f"Berdasarkan Modal Rp{modal_input:,.0f} & Risiko {risk_pct*100}%")
        if max_lot > 0 and score >= 5:
            st.success(f"🛒 **MAKSIMAL BELI:**\n### **{max_lot} LOT**")
            st.markdown(f"*(Jika kena Stop Loss, Anda hanya rugi maksimal Rp{max_loss_rp:,.0f})*")
        elif score < 5:
            st.error("🚫 **Sinyal Buruk. Jangan Beli.**")
        else:
            st.warning("⚠️ **Risiko Terlalu Besar** (Modal tidak cukup untuk 1 Lot pada jarak Stop Loss ini).")


# ==========================================
# --- 3. INDIKATOR OTOMATIS & MANUAL ---
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    with st.container(border=True):
        st.markdown("📈 **TREND & SQUEEZE**")
        st.markdown(f"**Tren Utama:** {data['trend']}")
        if "SQUEEZE" in data['bb_stat']:
            st.error(f"{data['bb_stat']}")
            st.caption("Pita BB sangat sempit. Bandar sedang mengompres harga sebelum diledakkan!")
        else:
            st.success(f"{data['bb_stat']}")
            
    with st.container(border=True):
        st.markdown("🏦 **BANDAR & ORDERBOOK**")
        if "Akumulasi" in status_bandar: st.success(f"✔️ Bandar: **Akumulasi**")
        elif "Distribusi" in status_bandar: st.error(f"❌ Bandar: **Distribusi**")
        else: st.warning(f"➖ Bandar: **Netral**")
        
        if "BID" in status_bidoffer: st.success(f"✔️ Bid/Offer: **Dominan BID**")
        elif "OFFER" in status_bidoffer: st.error(f"❌ Bid/Offer: **Dominan OFFER**")
        else: st.warning(f"➖ Bid/Offer: **Berimbang**")

with col_b2:
    with st.container(border=True):
        st.markdown("📐 **FIBO & VOLUME (VPA)**")
        st.markdown(f"**Posisi Fibo:** {data['fibo_stat']}")
        st.markdown(f"**Golden Ratio (61.8%):** Rp{int(data['fibo_618'])}")
        st.divider()
        if data['vpa_score'] == 1:
            st.success(f"📊 **VPA:** {data['vpa_stat']}")
        else:
            st.warning(f"📊 **VPA:** {data['vpa_stat']}")
            if data['trend'] == "Bullish": st.caption("Waspada Fakeout, kenaikan harga tidak didukung volume.")
    
    with st.container(border=True):
        st.markdown("⭐ **KESIMPULAN SINYAL**")
        if score >= 8 and "SQUEEZE" in data['bb_stat']:
            st.info(f"🌋 **JACKPOT! {ticker_input} SIAP MELEDAK**")
            st.markdown("Sinyal Sempurna + Fase Squeeze. Hajar Kanan sekarang!")
        elif score >= 8:
            st.info(f"🔥 **{ticker_input} SANGAT POTENSIAL**")
            st.markdown("Teknikal Bullish, Bandar Akumulasi, Demand Kuat, Volume Valid!")
        elif score >= 5:
            st.warning(f"⚠️ **PANTAU KETAT {ticker_input}**")
            st.markdown("Sinyal bercampur. Disarankan beli cicil di area Support / Fibo 61.8%.")
        else:
            st.error(f"💀 **JAUHI {ticker_input} SEMENTARA**")
            st.markdown("Distribusi kuat / Trend hancur. Dilarang menangkap pisau jatuh!")

with col_b3:
    with st.container(border=True):
        st.markdown("📊 **INDIKATOR TEKNIKAL**")
        st.markdown(f"📌 **EMA Cross:** {data['ema_cross']}")
        st.markdown(f"📌 **RSI (14):** {data['rsi_val']:.1f} - **{data['rsi_status']}**")
        st.markdown(f"🟢 **Support:** Rp{int(data['sup'])}")
        st.markdown(f"🔴 **Resistance:** Rp{int(data['res'])}")
    
    with st.container(border=True):
        st.markdown("👥 **INFO PERUSAHAAN**")
        st.caption("JUMLAH SAHAM BEREDAR")
        if data['shares'] != "N/A":
            st.markdown(f"### **{data['shares'] / 1e9:.2f} Miliar Lembar**")
        else:
            st.markdown("### **Tidak diketahui**")


# ==========================================
# --- 4. PUSAT DATA PASAR ELEGAN (DARK MODE) ---
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📊 Pusat Data Pasar (IHSG)")
tab_movers, tab_screener = st.tabs(["🔥 Top Movers & Trending", "🔎 Advanced Stock Scanner"])

with tab_movers:
    components.html("""
    <div class="tradingview-widget-container" style="height: 500px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>
      { "colorTheme": "dark", "dateRange": "12M", "exchange": "IDX", "showChart": false, "locale": "id", "width": "100%", "height": "100%", "isTransparent": true }
      </script>
    </div>
    """, height=500)

with tab_screener:
    components.html("""
    <div class="tradingview-widget-container" style="height: 600px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
      { "width": "100%", "height": "100%", "defaultColumn": "overview", "defaultScreen": "general", "market": "indonesia", "showToolbar": true, "colorTheme": "dark", "locale": "id", "isTransparent": true }
      </script>
    </div>
    """, height=600)
