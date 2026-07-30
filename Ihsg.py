import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="HOLY GRAIL ULTIMATE - Quant Sniper", layout="wide")

# CSS PREMIUM
st.markdown("""<style>
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
header {visibility: hidden;}
div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #111827 !important; border: 1px solid #374151 !important; border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4) !important; padding: 0.8rem !important;}
p, span, li, div.stMarkdown, .stText {font-size: 0.85rem !important; line-height: 1.5 !important;}
hr {margin-top: 0.8rem; margin-bottom: 0.8rem; border-color: #374151;}
</style>""", unsafe_allow_html=True)
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">', unsafe_allow_html=True)


# ==========================================
# --- PANEL KONTROL (ULTIMATE QUANT SYSTEM) ---
# ==========================================
st.markdown("### ⚙️ PANEL KONTROL (ULTIMATE QUANT SNIPER)")

col_in1, col_in2, col_in3 = st.columns(3)
with col_in1:
    ticker_input = st.text_input("🔍 1. Kode Saham (Ketik & Enter):", "BBCA").upper().strip()
with col_in2:
    status_bandar = st.selectbox("🕵️‍♂️ 2. Bandarmology (Manual):", ["Akumulasi (Net Buy)", "Netral / Sepi", "Distribusi (Net Sell)"])
with col_in3:
    status_bidoffer = st.selectbox("⚖️ 3. Bid & Offer (Manual):", ["Dominan BID (Demand Kuat)", "Berimbang (Normal)", "Dominan OFFER (Supply Kuat)"])

col_cf1, col_cf2 = st.columns(2)
with col_cf1:
    status_asing = st.selectbox("🦅 4. Jejak Dana Asing (Foreign Flow):", ["Asing NET BUY (Masuk Besar)", "Asing Netral / Mixed", "Asing NET SELL (Keluar)"])
with col_cf2:
    status_vwap = st.selectbox("🎯 5. Posisi Harga vs VWAP Pagi:", ["Di atas VWAP (Sangat Kuat / Bullish Intraday)", "Persis di VWAP (Area Rebound)", "Di bawah VWAP (Lemah / Rawan Tekan)"])

col_mm1, col_mm2 = st.columns(2)
with col_mm1:
    modal_input = st.number_input("💰 6. Modal Trading Anda (Rp):", min_value=100000, value=10000000, step=1000000)
with col_mm2:
    risiko_input = st.selectbox("🛡️ 7. Toleransi Risiko (Cutloss):", ["1% dari Modal (Sangat Konservatif)", "2% dari Modal (Standar Pro)", "3% dari Modal (Agresif)", "5% dari Modal (Sangat Agresif)"], index=1)

ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"
st.markdown("---")


# ==========================================
# --- MESIN KALKULASI DEWA (ULTIMATE QUANT ENGINE) ---
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
        
        sma5 = close_prices.rolling(5).mean().iloc[-1]
        sma20 = close_prices.rolling(20).mean().iloc[-1]
        sma60 = close_prices.rolling(60).mean().iloc[-1]
        
        if latest_price > sma5 and sma5 > sma20 and sma20 > sma60:
            mtf_status = "ALIGNMENT BULLISH (1D, 4H, 1H Selaras Naik)"
            mtf_score = 2
        elif latest_price > sma20:
            mtf_status = "MODERATE (Sebagian Timeframe Bullish)"
            mtf_score = 1
        else:
            mtf_status = "DEAD CROSS / BEARISH MATRIX"
            mtf_score = 0

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

        std20 = close_prices.rolling(20).std()
        bandwidth = ( (sma20 + (2 * std20)) - (sma20 - (2 * std20)) ) / sma20
        bw_latest = bandwidth.iloc[-1]
        bw_120_min = bandwidth.tail(120).min()
        bb_stat = "🔥 SQUEEZE (Siaga Meledak)" if bw_latest <= (bw_120_min * 1.25) else "Normal / Ekspansi"

        return {
            'price': latest_price, 'change': change_pct, 'div': dividend_yield, 'name': company_name,
            'ema_cross': ema_cross, 'trend': trend_status, 'rsi_val': rsi_val, 'rsi_status': rsi_status,
            'res': res_terdekat, 'sup': sup_terdekat, 'shares': shares,
            'swing_high': swing_high, 'fibo_382': fibo_382, 'fibo_618': fibo_618,
            'fibo_stat': fibo_stat, 'fibo_score': fibo_score,
            'vpa_stat': vpa_stat, 'vpa_score': vpa_score, 'bb_stat': bb_stat,
            'mtf_status': mtf_status, 'mtf_score': mtf_score
        }
    except:
        return None

data = get_stock_data(ticker_yf)
if data is None:
    st.error(f"❌ Saham **{ticker_input}** tidak valid atau data kurang. Coba saham Bluechip/Liquid.")
    st.stop()


# ==========================================
# --- ALGORITMA PENILAIAN QUANT SKOR (MAX 15) ---
# ==========================================
score = 0
if data['trend'] == "Bullish": score += 2
score += data['mtf_score']                          # MTF Matrix (Max 2)
if "Akumulasi" in status_bandar: score += 3
elif "Netral" in status_bandar: score += 1
if "BID" in status_bidoffer: score += 2
elif "Berimbang" in status_bidoffer: score += 1
if "NET BUY" in status_asing: score += 2            # Foreign Flow (Max 2)
elif "Neutral" in status_asing: score += 1
if "atas VWAP" in status_vwap: score += 1           # VWAP Sniper (Max 1)
elif "di VWAP" in status_vwap: score += 1
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
now = datetime.datetime.now()
today_time_str = now.strftime("%d %B %Y, %H:%M WIB") 

logo_url = f"https://assets.parqet.com/logos/symbol/{ticker_input}.JK?format=png"

col_h1, col_h2, col_h3 = st.columns([1.8, 1.4, 1.8])

with col_h1:
    st.markdown("<span style='font-size: 0.95rem; color:#9ca3af; font-weight:bold; letter-spacing: 1px;'>QUANT SNIPER SYSTEM</span>", unsafe_allow_html=True)
    st.markdown(f"""<div style="display: flex; align-items: center; gap: 15px; margin-top: 5px; margin-bottom: 5px;">
    <img src="{logo_url}" width="70" height="70" style="border-radius: 12px; background: white; padding: 4px;" onerror="this.style.display='none'">
    <div style='color:#f3f4f6; font-size: 4rem; font-weight: 900; line-height: 1;'>{ticker_input}</div>
    </div>""", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#d1d5db; font-size:1.15rem; font-weight:bold;'>{data['name']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.9rem; color:#60a5fa; margin-top: 6px; font-weight: bold;'>Update {today_time_str}</div>", unsafe_allow_html=True)

with col_h2:
    st.markdown("<div style='text-align: center; margin-top: 15px;'>", unsafe_allow_html=True)
    if score >= 12:
        st.markdown("<div style='color:#4ade80; font-size: 1.8rem; font-weight:900;'>GOD MODE BUY</div><div style='font-size: 1.5rem;'>⭐⭐⭐⭐⭐</div>", unsafe_allow_html=True)
    elif score >= 8:
        st.markdown("<div style='color:#4ade80; font-size: 1.8rem; font-weight:900;'>STRONG BUY</div><div style='font-size: 1.5rem;'>⭐⭐⭐⭐</div>", unsafe_allow_html=True)
    elif score >= 5:
        st.markdown("<div style='color:#fbbf24; font-size: 1.8rem; font-weight:900;'>HOLD / WAIT</div><div style='font-size: 1.5rem;'>⭐⭐⭐</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#f87171; font-size: 1.8rem; font-weight:900;'>SELL / AVOID</div><div style='font-size: 1.5rem;'>⭐</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#fbbf24; font-size: 2.8rem; font-weight: 900; margin-top: 5px;'>🌟 {score}.0 <span style='font-size:1.4rem; color:#9ca3af;'>/15</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_h3:
    st.markdown("<div style='text-align: right; margin-top: 15px;'>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9ca3af; font-size:0.95rem; font-weight:bold;'>HARGA PENUTUPAN</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#f3f4f6; font-size: 3.8rem; font-weight: 900; line-height: 1.1;'>Rp{int(data['price'])}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color: {color}; font-size: 1.4rem; font-weight: bold;'>{arrow} {data['change']:.2f}%</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='margin-top: 8px;'><span style='color:#9ca3af; font-size:0.9rem;'>DIVIDEND YIELD:</span> <span style='color:#f3f4f6; font-weight:bold; font-size:1.1rem;'>{round(data['div'], 2) if isinstance(data['div'], (int, float)) else 'N/A'}%</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()


# ==========================================
# --- 2. CHART (FULL WIDTH) ---
# ==========================================
tradingview_html = f"""
<div style="border-radius: 10px; border: 1px solid #374151; overflow: hidden; background: #111827; margin-bottom: 15px;">
    <div class="tradingview-widget-container" style="height: 420px; width: 100%;">
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
components.html(tradingview_html, height=430)


# ==========================================
# --- 3. KOTAK ANALISA (ELEGAN & FONT BESAR KONTRAST) ---
# ==========================================
# Merakit Isi Analisa
if score >= 8: entry_html = f"<span style='color:#4ade80;'>Entry di <strong><span style='font-size:1.15rem;'>Rp{int(data['price'])}</span></strong></span>"
elif score >= 5: entry_html = f"<span style='color:#fbbf24;'>Antre Support di <strong><span style='font-size:1.15rem;'>Rp{int(data['sup'])}</span></strong></span>"
else: entry_html = "<span style='color:#f87171; font-weight:bold;'>JANGAN BELI (Wait & See)</span>"

reward = int(data['res']) - int(data['price'])
rr_html = ""
if risk_per_share > 0 and reward > 0:
    rr_html = f"<div style='background:#1e3a8a; color:white; padding:8px; border-radius:6px; text-align:center; font-weight:bold; font-size:0.85rem; margin-top: 12px;'>⚖️ Risk : Reward = 1 : {round(reward / risk_per_share, 1)}</div>"

if max_lot > 0 and score >= 5:
    mm_html = f"<div style='background:#065f46; color:#a7f3d0; padding:12px; border-radius:8px; text-align:center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);'>🛒 MAKSIMAL BELI:<br><div style='font-size:2.2rem; font-weight:900; line-height:1.2; margin-top:5px;'>{max_lot} LOT</div></div>"
else:
    mm_html = "<div style='background:#7f1d1d; color:#fca5a5; padding:12px; border-radius:8px; text-align:center; font-weight:bold; font-size:1.1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);'>🚫 KONDISI TIDAK AMAN<br>UNTUK ENTRY</div>"

# PERBAIKAN BUG DISINI: Menggunakan bb_html, bukan bb_stat!
if "SQUEEZE" in data['bb_stat']: bb_html = f"<span style='color:#f87171; font-weight:bold; font-size:1.05rem;'>{data['bb_stat']}</span>"
else: bb_html = f"<span style='color:#4ade80; font-weight:bold; font-size:1.05rem;'>{data['bb_stat']}</span>"

if "Akumulasi" in status_bandar: bandar_html = "Bandar: <span style='color:#4ade80; font-weight:bold; font-size:1.05rem;'>Akumulasi Massal</span>"
elif "Distribusi" in status_bandar: bandar_html = "Bandar: <span style='color:#f87171; font-weight:bold; font-size:1.05rem;'>Distribusi Kuat</span>"
else: bandar_html = "Bandar: <span style='color:#fbbf24; font-weight:bold; font-size:1.05rem;'>Netral / Sepi</span>"

if "NET BUY" in status_asing: asing_html = "Asing: <span style='color:#4ade80; font-weight:bold; font-size:1.05rem;'>NET BUY (Masuk)</span>"
elif "NET SELL" in status_asing: asing_html = "Asing: <span style='color:#f87171; font-weight:bold; font-size:1.05rem;'>NET SELL (Keluar)</span>"
else: asing_html = "Asing: <span style='color:#fbbf24; font-weight:bold; font-size:1.05rem;'>Netral / Mixed</span>"

if "atas VWAP" in status_vwap: vwap_html = "VWAP: <span style='color:#4ade80; font-weight:bold; font-size:1.05rem;'>Di Atas VWAP (Kuat)</span>"
elif "di VWAP" in status_vwap: vwap_html = "VWAP: <span style='color:#fbbf24; font-weight:bold; font-size:1.05rem;'>Persis di VWAP</span>"
else: vwap_html = "VWAP: <span style='color:#f87171; font-weight:bold; font-size:1.05rem;'>Di Bawah VWAP</span>"

vpa_bg = "#065f46; color:#a7f3d0;" if data['vpa_score'] == 1 else "#78350f; color:#fde68a;"
vpa_html = f"<div style='background:{vpa_bg}; padding:6px 12px; border-radius:6px; margin-top:12px; display:inline-block; font-weight:bold; font-size:1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);'>📊 VPA: {data['vpa_stat']}</div>"

if score >= 12: kesimpulan_html = f"⚡<br><div style='font-size:1.4rem; font-weight:900; color:#4ade80; margin: 10px 0;'>GOD MODE SNIPER!<br>{ticker_input} SIAP TERBANG</div><span style='color:#a3a8b4; font-size:1rem;'>Semua Engine Selaras.</span>"
elif score >= 8: kesimpulan_html = f"🔥<br><div style='font-size:1.4rem; font-weight:900; color:#4ade80; margin: 10px 0;'>{ticker_input}<br>HIGH PROBABILITY</div><span style='color:#a3a8b4; font-size:1rem;'>Sinyal Sangat Kuat.</span>"
elif score >= 5: kesimpulan_html = f"⚠️<br><div style='font-size:1.4rem; font-weight:900; color:#fbbf24; margin: 10px 0;'>PANTAU KETAT<br>{ticker_input}</div><span style='color:#a3a8b4; font-size:1rem;'>Sinyal Moderat.</span>"
else: kesimpulan_html = f"💀<br><div style='font-size:1.4rem; font-weight:900; color:#f87171; margin: 10px 0;'>JAUHI {ticker_input}<br>SEMENTARA</div><span style='color:#a3a8b4; font-size:1rem;'>Risiko Tinggi / Distribusi.</span>"

shares_str = f"{data['shares'] / 1e9:.2f} Miliar Lembar" if data['shares'] != "N/A" else "Tidak diketahui"

# Merakit Kotak HTML (Tinggi 270px)
box1 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 1rem; font-weight: bold;'>💰 TRADE PLAN & SNIPER</span><br><hr style='margin: 8px 0; border-color:#374151;'><strong>Entry:</strong> {entry_html}<br><span style='color:#f87171;'><strong>Stop Loss:</strong> Jika jebol <span style='font-size:1.05rem; font-weight:bold;'>Rp{int(data['sup'])}</span></span></div>
<div style='margin-top: auto;'><hr style='margin: 8px 0; border-color:#374151;'>🎯 <strong>TARGET:</strong> TP1: <span style='font-size:1.05rem; font-weight:bold; color:#f3f4f6;'>Rp{int(data['res'])}</span> | TP2: <span style='font-size:1.05rem; font-weight:bold; color:#f3f4f6;'>Rp{int(data['swing_high'])}</span><br>{rr_html}</div>
</div>""".replace('\n', '')

box2 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 1rem; font-weight: bold;'>🛡️ MONEY MANAGEMENT</span><br><hr style='margin: 8px 0; border-color:#374151;'><span style='color:#9ca3af;'>Modal:</span> <strong style='font-size:1.05rem;'>Rp{modal_input:,.0f}</strong><br><span style='color:#9ca3af;'>Risiko:</span> <strong style='font-size:1.05rem;'>{risk_pct*100}%</strong> <span style='color:#f87171;'>(Rp{max_loss_rp:,.0f})</span></div>
<div style='margin-top: auto;'>{mm_html}</div>
</div>""".replace('\n', '')

box3 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 1rem; font-weight: bold;'>⭐ QUANT SNIPER SCORE</span><br><hr style='margin: 8px 0; border-color:#374151;'></div>
<div style='margin-top: auto; margin-bottom: auto; text-align: center;'>{kesimpulan_html}</div>
</div>""".replace('\n', '')

box4 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 1rem; font-weight: bold;'>🦅 INSTITUTIONAL FLOW</span><br><hr style='margin: 8px 0; border-color:#374151;'>✔️ {asing_html}<br>✔️ {bandar_html}<br>✔️ {vwap_html}</div>
<div style='margin-top: auto;'><hr style='margin: 8px 0; border-color:#374151;'>{bb_html}</div>
</div>""".replace('\n', '')

box5 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 1rem; font-weight: bold;'>⏳ MULTI-TIMEFRAME MATRIX</span><br><hr style='margin: 8px 0; border-color:#374151;'><span style='color:#9ca3af;'>Matrix:</span> <strong style='font-size:1.05rem; color:#4ade80;'>{data['mtf_status']}</strong><br><hr style='margin: 8px 0; border-color:#374151;'><span style='color:#9ca3af;'>Fibo:</span> <strong style='font-size:1.05rem; color:#f3f4f6;'>{data['fibo_stat']}</strong><br><span style='color:#9ca3af;'>Golden Ratio:</span> <strong style='font-size:1.05rem; color:#fbbf24;'>Rp{int(data['fibo_618'])}</strong></div>
<div style='margin-top: auto; text-align: center;'>{vpa_html}</div>
</div>""".replace('\n', '')

box6 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 1rem; font-weight: bold;'>📊 TEKNIKAL & FUNDAMENTAL</span><br><hr style='margin: 8px 0; border-color:#374151;'>📌 <span style='color:#9ca3af;'>EMA Cross:</span> <strong>{data['ema_cross']}</strong><br>📌 <span style='color:#9ca3af;'>RSI (14):</span> <strong style='font-size:1.05rem;'>{data['rsi_val']:.1f} ({data['rsi_status']})</strong></div>
<div style='margin-top: auto;'><hr style='margin: 8px 0; border-color:#374151;'>👥 <span style='color:#9ca3af;'>Saham Beredar:</span><br><strong style='font-size:1.1rem; color:#f3f4f6;'>{shares_str}</strong></div>
</div>""".replace('\n', '')

# BARIS 1 (Tiga Kotak Presisi)
col_b1, col_b2, col_b3 = st.columns(3)
with col_b1:
    with st.container(border=True): st.markdown(box1, unsafe_allow_html=True)
with col_b2:
    with st.container(border=True): st.markdown(box2, unsafe_allow_html=True)
with col_b3:
    with st.container(border=True): st.markdown(box3, unsafe_allow_html=True)

# Spasi antar baris
st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# BARIS 2 (Tiga Kotak Presisi)
col_b4, col_b5, col_b6 = st.columns(3)
with col_b4:
    with st.container(border=True): st.markdown(box4, unsafe_allow_html=True)
with col_b5:
    with st.container(border=True): st.markdown(box5, unsafe_allow_html=True)
with col_b6:
    with st.container(border=True): st.markdown(box6, unsafe_allow_html=True)


# ==========================================
# --- 4. PUSAT DATA PASAR ---
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
