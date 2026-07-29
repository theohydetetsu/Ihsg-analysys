import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="HOLY GRAIL - Technical Dashboard", layout="wide")

# CSS PREMIUM (MEMAKSA KOTAK PRESISI)
st.markdown("""<style>
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
header {visibility: hidden;}
div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #111827 !important; border: 1px solid #374151 !important; border-radius: 10px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important; padding: 0.8rem !important;}
p, span, li, div.stMarkdown, .stText {font-size: 0.8rem !important; line-height: 1.5 !important;}
hr {margin-top: 0.8rem; margin-bottom: 0.8rem; border-color: #374151;}
</style>""", unsafe_allow_html=True)
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">', unsafe_allow_html=True)


# ==========================================
# --- PANEL KONTROL ---
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
    st.error(f"❌ Saham **{ticker_input}** tidak valid atau data kurang. Coba saham Bluechip/Liquid.")
    st.stop()


# ==========================================
# --- ALGORITMA PENILAIAN SKOR SEMPURNA ---
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
# --- 1. HEADER DASHBOARD (DIPERBESAR MAKSIMAL) ---
# ==========================================
arrow = "▼" if data['change'] < 0 else "▲"
color = "#f87171" if data['change'] < 0 else "#4ade80" 
today_date = datetime.datetime.now().strftime("%d %B %Y")

logo_url = f"https://assets.parqet.com/logos/symbol/{ticker_input}.JK?format=png"

col_h1, col_h2, col_h3 = st.columns([2, 1.2, 1.3])

with col_h1:
    st.markdown("<span style='font-size: 0.95rem; color:#9ca3af; font-weight:bold; letter-spacing: 1px;'>HOLY GRAIL SYSTEM</span>", unsafe_allow_html=True)
    st.markdown(f"""<div style="display: flex; align-items: center; gap: 15px; margin-top: 5px; margin-bottom: 5px;">
    <img src="{logo_url}" width="65" height="65" style="border-radius: 12px; background: white; padding: 4px;" onerror="this.style.display='none'">
    <h1 style='color:#f3f4f6; font-size: 4.5rem !important; margin: 0; line-height: 1;'>{ticker_input}</h1>
    </div>""", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#d1d5db; font-size:1.2rem; font-weight:bold;'>{data['name']}</span>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.9rem; color:#60a5fa; margin-top: 6px;'>Update {today_date} | Close Rp{int(data['price'])}</div>", unsafe_allow_html=True)

with col_h2:
    st.markdown("<div style='text-align: center; margin-top: 10px;'>", unsafe_allow_html=True)
    if score >= 8:
        st.markdown("<span style='color:#4ade80; font-size: 1.4rem; font-weight:bold;'>STRONG BUY</span><br><span style='font-size: 1.4rem;'>⭐⭐⭐⭐⭐</span>", unsafe_allow_html=True)
    elif score >= 5:
        st.markdown("<span style='color:#fbbf24; font-size: 1.4rem; font-weight:bold;'>HOLD / WAIT</span><br><span style='font-size: 1.4rem;'>⭐⭐⭐</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#f87171; font-size: 1.4rem; font-weight:bold;'>SELL / AVOID</span><br><span style='font-size: 1.4rem;'>⭐</span>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#fbbf24; font-size: 3rem !important; margin: 5px 0 0 0;'>🌟 {score}.0 <span style='font-size:1.2rem; color:#9ca3af;'>/10</span></h2>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_h3:
    st.markdown("<div style='text-align: right; margin-top: 10px;'>", unsafe_allow_html=True)
    st.markdown("<span style='color:#9ca3af; font-size:0.95rem; font-weight:bold;'>HARGA PENUTUPAN</span>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:#f3f4f6; font-size: 3.5rem !important; margin: 0; line-height: 1.1;'>Rp{int(data['price'])}</h2>", unsafe_allow_html=True)
    st.markdown(f"<span style='color: {color}; font-size: 1.3rem; font-weight: bold;'>{arrow} {data['change']:.2f}%</span>", unsafe_allow_html=True)
    st.markdown(f"<div style='margin-top: 8px;'><span style='color:#9ca3af; font-size:0.85rem;'>DIVIDEND YIELD:</span> <span style='color:#f3f4f6; font-weight:bold; font-size:1rem;'>{round(data['div'], 2) if isinstance(data['div'], (int, float)) else 'N/A'}%</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()


# ==========================================
# --- 2. CHART (FULL WIDTH - RATA KANAN KIRI) ---
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
# --- 3. KOTAK ANALISA (6 KOTAK PRESISI TOTAL 270px) ---
# ==========================================
# Persiapan Variabel HTML agar anti-error
if score >= 8: entry_html = f"<span style='color:#4ade80;'><strong>Entry:</strong> Hajar Beli di Rp{int(data['price'])}</span>"
elif score >= 5: entry_html = f"<span style='color:#fbbf24;'><strong>Entry:</strong> Antre di Support Rp{int(data['sup'])}</span>"
else: entry_html = "<span style='color:#f87171;'><strong>Entry:</strong> JANGAN BELI (Wait & See)</span>"

reward = int(data['res']) - int(data['price'])
rr_html = ""
if risk_per_share > 0 and reward > 0:
    rr_html = f"<div style='background:#1e3a8a; color:white; padding:6px; border-radius:6px; text-align:center; font-weight:bold; font-size:0.75rem; margin-top: 8px;'>⚖️ Risk : Reward = 1 : {round(reward / risk_per_share, 1)}</div>"

if max_lot > 0 and score >= 5:
    mm_html = f"<div style='background:#065f46; color:#a7f3d0; padding:10px; border-radius:6px; text-align:center;'>🛒 MAKSIMAL BELI:<br><strong style='font-size:1.6rem;'>{max_lot} LOT</strong></div>"
else:
    mm_html = "<div style='background:#7f1d1d; color:#fca5a5; padding:10px; border-radius:6px; text-align:center;'>🚫 KONDISI TIDAK AMAN UNTUK BUY</div>"

if "SQUEEZE" in data['bb_stat']: bb_html = f"<span style='color:#f87171; font-weight:bold;'>{data['bb_stat']}</span>"
else: bb_html = f"<span style='color:#4ade80;'>{data['bb_stat']}</span>"

if "Akumulasi" in status_bandar: bandar_html = "✔️ Bandar: <strong><span style='color:#4ade80;'>Akumulasi</span></strong>"
elif "Distribusi" in status_bandar: bandar_html = "❌ Bandar: <strong><span style='color:#f87171;'>Distribusi</span></strong>"
else: bandar_html = "➖ Bandar: <strong><span style='color:#fbbf24;'>Netral</span></strong>"

if "BID" in status_bidoffer: bo_html = "✔️ Bid/Offer: <strong><span style='color:#4ade80;'>Dominan BID</span></strong>"
elif "OFFER" in status_bidoffer: bo_html = "❌ Bid/Offer: <strong><span style='color:#f87171;'>Dominan OFFER</span></strong>"
else: bo_html = "➖ Bid/Offer: <strong><span style='color:#fbbf24;'>Berimbang</span></strong>"

vpa_bg = "#065f46; color:#a7f3d0;" if data['vpa_score'] == 1 else "#78350f; color:#fde68a;"
vpa_html = f"<div style='background:{vpa_bg}; padding:5px 8px; border-radius:4px; display:inline-block;'>📊 VPA: {data['vpa_stat']}</div>"

if score >= 8 and "SQUEEZE" in data['bb_stat']: kesimpulan_html = f"🌋 <span style='font-size:1.1rem; font-weight:bold; color:#f3f4f6;'>JACKPOT! {ticker_input} SIAP MELEDAK</span><br><span style='color:#a3a8b4;'>Hajar Kanan sekarang!</span>"
elif score >= 8: kesimpulan_html = f"🔥 <span style='font-size:1.1rem; font-weight:bold; color:#f3f4f6;'>{ticker_input} SANGAT POTENSIAL</span><br><span style='color:#a3a8b4;'>Bullish & Akumulasi!</span>"
elif score >= 5: kesimpulan_html = f"⚠️ <span style='font-size:1.1rem; font-weight:bold; color:#f3f4f6;'>PANTAU KETAT {ticker_input}</span><br><span style='color:#a3a8b4;'>Cicil di area Support.</span>"
else: kesimpulan_html = f"💀 <span style='font-size:1.1rem; font-weight:bold; color:#f3f4f6;'>JAUHI {ticker_input} SEMENTARA</span><br><span style='color:#a3a8b4;'>Trend patah / Distribusi.</span>"
shares_str = f"{data['shares'] / 1e9:.2f} Miliar Lembar" if data['shares'] != "N/A" else "Tidak diketahui"

# Merakit HTML Kotak (Dipaksa Tinggi 270px persis pakai Flexbox)
box1 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>💰 TRADE PLAN</span><br><hr style='margin: 8px 0; border-color:#374151;'>{entry_html}<br><span style='color:#f87171;'><strong>Stop Loss:</strong> Jika jebol Rp{int(data['sup'])}</span></div>
<div style='margin-top: auto;'><hr style='margin: 8px 0; border-color:#374151;'>🎯 <strong>TARGET HARGA</strong><br>🥇 <strong>TP 1 (Resist):</strong> Rp{int(data['res'])}<br>🚀 <strong>TP 2 (Swing):</strong> Rp{int(data['swing_high'])}<br>{rr_html}</div>
</div>""".replace('\n', '')

box2 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>🛡️ MONEY MANAGEMENT</span><br><hr style='margin: 8px 0; border-color:#374151;'>Berdasarkan Modal: <strong>Rp{modal_input:,.0f}</strong><br>Risiko Cutloss: <strong>{risk_pct*100}%</strong> (Rp{max_loss_rp:,.0f})</div>
<div style='margin-top: auto;'>{mm_html}</div>
</div>""".replace('\n', '')

box3 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>⭐ KESIMPULAN SINYAL</span><br><hr style='margin: 8px 0; border-color:#374151;'></div>
<div style='margin-top: auto; margin-bottom: auto; text-align: center;'>{kesimpulan_html}</div>
</div>""".replace('\n', '')

box4 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>📈 TREND & BANDARMOLOGY</span><br><hr style='margin: 8px 0; border-color:#374151;'><strong>Tren Utama:</strong> {data['trend']}<br>{bb_html}</div>
<div style='margin-top: auto;'><hr style='margin: 8px 0; border-color:#374151;'>{bandar_html}<br>{bo_html}</div>
</div>""".replace('\n', '')

box5 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>📐 FIBO & VOLUME (VPA)</span><br><hr style='margin: 8px 0; border-color:#374151;'><strong>Posisi Fibo:</strong> {data['fibo_stat']}<br><strong>Golden Ratio (61.8%):</strong> Rp{int(data['fibo_618'])}</div>
<div style='margin-top: auto;'>{vpa_html}</div>
</div>""".replace('\n', '')

box6 = f"""<div style='height: 270px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>📊 INDIKATOR & INFO</span><br><hr style='margin: 8px 0; border-color:#374151;'>📌 <strong>EMA Cross:</strong> {data['ema_cross']}<br>📌 <strong>RSI (14):</strong> {data['rsi_val']:.1f} - <strong>{data['rsi_status']}</strong></div>
<div style='margin-top: auto;'><hr style='margin: 8px 0; border-color:#374151;'>👥 <strong>Saham Beredar:</strong><br><strong>{shares_str}</strong></div>
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
