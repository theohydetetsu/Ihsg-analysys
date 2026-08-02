import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="HOLY GRAIL ULTIMATE - Quant Sniper", layout="wide")

# CSS PREMIUM (RESPONSIVE & ANTI-WRAP)
st.markdown("""<style>
.stApp, [data-testid="stAppViewContainer"] {background-color: #020617 !important;}
[data-testid="stHeader"] {background-color: rgba(0,0,0,0) !important;}
h1, h2, h3, h4, h5, h6, p, span, li, label, div.stMarkdown, .stText {color: #f3f4f6 !important;}
[data-baseweb="base-input"] input, [data-baseweb="select"] div {background-color: #111827 !important; color: white !important; border-color: #374151 !important;}
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
header {visibility: hidden;}
div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #111827 !important; border: 1px solid #374151 !important; border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4) !important; padding: 0.6rem !important;}
p, span, li, div.stMarkdown, .stText {font-size: 0.85rem !important; line-height: 1.4 !important;}
hr {margin-top: 0.5rem; margin-bottom: 0.5rem; border-color: #374151;}
</style>""", unsafe_allow_html=True)
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">', unsafe_allow_html=True)


# ==========================================
# --- PANEL KONTROL ---
# ==========================================
st.markdown("### ⚙️ PANEL KONTROL (ULTIMATE QUANT SNIPER)")

col_in1, col_in2, col_in3 = st.columns(3)
with col_in1:
    ticker_input = st.text_input("🔍 1. Kode Saham (Ketik & Enter):", "BBCA").upper().strip()
with col_in2:
    status_bandar = st.selectbox("🕵️‍♂️ 2. Bandarmology (Manual):", ["Akumulasi (Net Buy)", "Netral / Sepi", "Distribusi (Net Sell)"])
with col_in3:
    status_bidoffer = st.selectbox("⚖️ 3. Bid & Offer (Manual):", ["Dominan BID (Demand Kuat)", "Berimbang (Normal)", "Dominan OFFER (Supply Kuat)"])

col_cf1, col_cf2, col_cf3 = st.columns(3)
with col_cf1:
    status_asing = st.selectbox("🦅 4. Jejak Dana Asing (Foreign Flow):", ["Asing NET BUY (Masuk Besar)", "Asing Netral / Mixed", "Asing NET SELL (Keluar)"])
with col_cf2:
    modal_input = st.number_input("💰 5. Modal Trading Anda (Rp):", min_value=100000, value=10000000, step=1000000)
with col_cf3:
    risiko_input = st.selectbox("🛡️ 6. Toleransi Risiko (Cutloss):", ["1% dari Modal (Sangat Konservatif)", "2% dari Modal (Standar Pro)", "3% dari Modal (Agresif)", "5% dari Modal (Sangat Agresif)"], index=1)

ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"
st.markdown("---")


# ==========================================
# --- MESIN KALKULASI DEWA ---
# ==========================================
@st.cache_data(ttl=120)
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
        
        # Ekstraksi Data Fundamental & Kuartal
        def safe_pct(val): return f"{val * 100:.1f}%" if val and val != "N/A" else "N/A"
        def safe_num(val): return f"{val:.2f}x" if val and val != "N/A" else "N/A"
        
        pe_ratio = safe_num(info.get('trailingPE'))
        pbv_ratio = safe_num(info.get('priceToBook'))
        roe = safe_pct(info.get('returnOnEquity'))
        npm = safe_pct(info.get('profitMargins'))
        
        eps_growth_raw = info.get('earningsQuarterlyGrowth')
        eps_growth = safe_pct(eps_growth_raw)
        if eps_growth_raw and eps_growth_raw > 0: eps_color = "#4ade80"
        elif eps_growth_raw and eps_growth_raw < 0: eps_color = "#f87171"
        else: eps_color = "#9ca3af"

        close_prices = hist['Close']
        
        ema9 = close_prices.ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = close_prices.ewm(span=21, adjust=False).mean().iloc[-1]
        ema_cross = "Bullish (EMA9 > EMA21)" if ema9 > ema21 else "Bearish (EMA9 < EMA21)"
        trend_status = "Bullish" if latest_price > ema21 else "Bearish"
        
        sma5 = close_prices.rolling(5).mean().iloc[-1]
        sma20 = close_prices.rolling(20).mean().iloc[-1]
        sma60 = close_prices.rolling(60).mean().iloc[-1]
        
        if latest_price > sma5 and sma5 > sma20 and sma20 > sma60:
            mtf_status = "ALIGNMENT BULLISH"
            mtf_score = 2
        elif latest_price > sma20:
            mtf_status = "MODERATE (Campur)"
            mtf_score = 1
        else:
            mtf_status = "DEAD CROSS (Bearish)"
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
        if latest_price >= fibo_382: fibo_stat, fibo_score = "Aman (> 38.2%)", 1
        elif latest_price >= fibo_618: fibo_stat, fibo_score = "Golden Pocket", 1
        else: fibo_stat, fibo_score = "Jebol (< 61.8%)", 0

        vol_latest = hist['Volume'].iloc[-1]
        vol_ma20 = hist['Volume'].rolling(20).mean().iloc[-1]
        vol_ratio = (vol_latest / vol_ma20) * 100 if vol_ma20 > 0 else 0
        if vol_ratio > 150: vpa_stat, vpa_score = f"Ledakan Vol ({int(vol_ratio)}%)", 1
        elif vol_ratio < 80: vpa_stat, vpa_score = f"Vol Kering ({int(vol_ratio)}%)", 0
        else: vpa_stat, vpa_score = f"Vol Normal ({int(vol_ratio)}%)", 0

        std20 = close_prices.rolling(20).std()
        bandwidth = ( (sma20 + (2 * std20)) - (sma20 - (2 * std20)) ) / sma20
        bw_latest = bandwidth.iloc[-1]
        bw_120_min = bandwidth.tail(120).min()
        bb_stat = "🔥 SQUEEZE (Siaga Meledak)" if bw_latest <= (bw_120_min * 1.25) else "Normal / Ekspansi"

        # --- VCP ENGINE ---
        daily_range = hist['High'] - hist['Low']
        atr_20 = daily_range.rolling(20).mean().iloc[-1]
        atr_5 = daily_range.rolling(5).mean().iloc[-1]
        vol_5 = hist['Volume'].rolling(5).mean().iloc[-1]
        
        if atr_5 < (atr_20 * 0.8) and vol_5 < vol_ma20 and latest_price > sma60:
            vcp_stat = "🎯 Terdeteksi (Siap Breakout)"
            vcp_score = 1
        elif atr_5 < atr_20:
            vcp_stat = "⏳ Menyempit (Formasi)"
            vcp_score = 0
        else:
            vcp_stat = "✖️ Melebar (Bukan VCP)"
            vcp_score = 0

        try:
            intraday = stock.history(period="1d", interval="5m")
            if not intraday.empty and intraday['Volume'].sum() > 0:
                typical_price = (intraday['High'] + intraday['Low'] + intraday['Close']) / 3
                vwap_kalkulasi = (typical_price * intraday['Volume']).cumsum() / intraday['Volume'].cumsum()
                vwap_val = vwap_kalkulasi.iloc[-1]
                
                if latest_price > (vwap_val * 1.005):
                    vwap_stat = "Di Atas VWAP (Bullish)"
                    vwap_score = 1
                elif latest_price < (vwap_val * 0.995):
                    vwap_stat = "Di Bawah VWAP (Lemah)"
                    vwap_score = 0
                else:
                    vwap_stat = "Persis Area VWAP"
                    vwap_score = 1
            else:
                vwap_val = 0
                vwap_stat = "VWAP Tertunda"
                vwap_score = 0
        except:
            vwap_val = 0
            vwap_stat = "VWAP Error"
            vwap_score = 0

        return {
            'price': latest_price, 'change': change_pct, 'div': dividend_yield, 'name': company_name,
            'ema_cross': ema_cross, 'trend': trend_status, 'rsi_val': rsi_val, 'rsi_status': rsi_status,
            'res': res_terdekat, 'sup': sup_terdekat, 'shares': shares,
            'swing_high': swing_high, 'fibo_382': fibo_382, 'fibo_618': fibo_618,
            'fibo_stat': fibo_stat, 'fibo_score': fibo_score,
            'vpa_stat': vpa_stat, 'vpa_score': vpa_score, 'bb_stat': bb_stat,
            'mtf_status': mtf_status, 'mtf_score': mtf_score,
            'vwap_val': vwap_val, 'vwap_stat': vwap_stat, 'vwap_score': vwap_score,
            'vcp_stat': vcp_stat, 'vcp_score': vcp_score,
            'pe': pe_ratio, 'pbv': pbv_ratio, 'roe': roe, 'npm': npm, 
            'eps_growth': eps_growth, 'eps_color': eps_color
        }
    except:
        return None

data = get_stock_data(ticker_yf)
if data is None:
    st.error(f"❌ Saham **{ticker_input}** tidak valid atau data kurang.")
    st.stop()


# ==========================================
# --- PENILAIAN SKOR & PROBABILITAS ---
# ==========================================
score = 0
if data['trend'] == "Bullish": score += 2
score += data['mtf_score']                          
if "Akumulasi" in status_bandar: score += 3
elif "Netral" in status_bandar: score += 1
if "BID" in status_bidoffer: score += 2
elif "Berimbang" in status_bidoffer: score += 1
if "NET BUY" in status_asing: score += 2            
elif "Neutral" in status_asing: score += 1
score += data['vwap_score']                         
if data['rsi_status'] in ["Netral", "Oversold"]: score += 1
score += data['fibo_score']
score += data['vpa_score']
score += data['vcp_score'] 

if score >= 14: win_rate, wr_color = "92% (Sangat Tinggi)", "#4ade80"
elif score >= 11: win_rate, wr_color = "75% (Tinggi)", "#4ade80"
elif score >= 7: win_rate, wr_color = "50% (Spekulatif)", "#fbbf24"
else: win_rate, wr_color = "< 30% (Risiko Bahaya)", "#f87171"

risk_pct = float(risiko_input.split('%')[0]) / 100
max_loss_rp = modal_input * risk_pct
risk_per_share = data['price'] - data['sup']
if risk_per_share <= 0: risk_per_share = data['price'] * 0.02 
max_shares = max_loss_rp / risk_per_share
max_lot = int(max_shares / 100)
if max_lot < 1: max_lot = 0

if score >= 9: 
    entry_val = f"<span style='color:#4ade80; font-weight:bold;'>Rp{int(data['price'])} (HK)</span>"
elif score >= 5: 
    entry_val = f"<span style='color:#fbbf24; font-weight:bold;'>Rp{int(data['sup'])} (Antre)</span>"
else: 
    entry_val = "<span style='color:#f87171; font-weight:bold;'>Wait & See</span>"


# ==========================================
# --- 1. HEADER DASHBOARD (ANTI-WRAP & RESPONSIVE) ---
# ==========================================
arrow = "▼" if data['change'] < 0 else "▲"
color = "#f87171" if data['change'] < 0 else "#4ade80" 

wib_timezone = datetime.timezone(datetime.timedelta(hours=7))
now_wib = datetime.datetime.now(wib_timezone)
today_time_str = now_wib.strftime("%d %B %Y, %H:%M WIB") 
logo_url = f"https://assets.parqet.com/logos/symbol/{ticker_input}.JK?format=png"

col_h1, col_h2, col_h3, col_h4 = st.columns([1.3, 1.2, 1.2, 1.6])

with col_h1:
    st.markdown("<span style='font-size: 0.95rem; color:#9ca3af; font-weight:bold; letter-spacing: 1px; white-space: nowrap;'>QUANT SNIPER SYSTEM</span>", unsafe_allow_html=True)
    st.markdown(f"""<div style="display: flex; align-items: center; gap: 10px; margin-top: 5px; margin-bottom: 5px;">
    <img src="{logo_url}" width="60" height="60" style="border-radius: 12px; background: white; padding: 4px; flex-shrink: 0;" onerror="this.style.display='none'">
    <div style='color:#f3f4f6; font-size: clamp(2rem, 4vw, 3.8rem); font-weight: 900; line-height: 1; letter-spacing: 1px;'>{ticker_input}</div>
    </div>""", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#d1d5db; font-size:1.05rem; font-weight:bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{data['name']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.85rem; color:#60a5fa; margin-top: 4px; font-weight: bold;'>Update {today_time_str}</div>", unsafe_allow_html=True)

with col_h2:
    st.markdown("<div style='text-align: center; margin-top: 15px;'>", unsafe_allow_html=True)
    if score >= 13:
        st.markdown("<div style='color:#4ade80; font-size: clamp(1.2rem, 2vw, 1.6rem); font-weight:900; white-space: nowrap;'>GOD MODE</div><div style='font-size: 1.3rem;'>⭐⭐⭐⭐⭐</div>", unsafe_allow_html=True)
    elif score >= 9:
        st.markdown("<div style='color:#4ade80; font-size: clamp(1.2rem, 2vw, 1.6rem); font-weight:900; white-space: nowrap;'>STRONG BUY</div><div style='font-size: 1.3rem;'>⭐⭐⭐⭐</div>", unsafe_allow_html=True)
    elif score >= 5:
        st.markdown("<div style='color:#fbbf24; font-size: clamp(1.2rem, 2vw, 1.6rem); font-weight:900; white-space: nowrap;'>HOLD / WAIT</div><div style='font-size: 1.3rem;'>⭐⭐⭐</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='color:#f87171; font-size: clamp(1.2rem, 2vw, 1.6rem); font-weight:900; white-space: nowrap;'>SELL / AVOID</div><div style='font-size: 1.3rem;'>⭐</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#fbbf24; font-size: 2.5rem; font-weight: 900; margin-top: 5px; white-space: nowrap;'>🌟 {score}.0 <span style='font-size:1.2rem; color:#9ca3af;'>/16</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_h3:
    st.markdown("<div style='text-align: right; margin-top: 15px;'>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9ca3af; font-size:0.95rem; font-weight:bold; white-space: nowrap;'>HARGA PENUTUPAN</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#f3f4f6; font-size: clamp(2.2rem, 4.5vw, 3.5rem); font-weight: 900; line-height: 1.1; white-space: nowrap;'>Rp{int(data['price'])}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color: {color}; font-size: 1.2rem; font-weight: bold; white-space: nowrap;'>{arrow} {data['change']:.2f}%</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_h4:
    # SATU-SATUNYA TRADE PLAN (Sekarang Fokus di Header Saja)
    reward = int(data['res']) - int(data['price'])
    rr_html = f"<div style='background:#1e3a8a; color:white; padding:4px; border-radius:4px; text-align:center; font-weight:bold; font-size:0.75rem; margin-top: 6px;'>⚖️ Risk : Reward = 1 : {round(reward / risk_per_share, 1) if risk_per_share > 0 else 0}</div>"
    
    st.markdown(f"""
    <div style='background: linear-gradient(145deg, #1f2937, #111827); border: 1px solid #374151; padding: 12px 10px; border-radius: 10px; margin-top: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);'>
        <div style='color:#9ca3af; font-size:0.75rem; font-weight:bold; letter-spacing:1px; margin-bottom: 6px; white-space: nowrap;'>🎯 TRADE PLAN & SNIPER</div>
        <div style='display:flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 3px;'>
            <span style='color:#d1d5db; white-space: nowrap;'>Entry:</span> <span style='white-space: nowrap;'>{entry_val}</span>
        </div>
        <div style='display:flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 3px;'>
            <span style='color:#d1d5db; white-space: nowrap;'>Target 1:</span> <span style='color:#4ade80; font-weight:bold; white-space: nowrap;'>Rp{int(data['res'])}</span>
        </div>
        <div style='display:flex; justify-content: space-between; font-size: 0.9rem;'>
            <span style='color:#d1d5db; white-space: nowrap;'>Stop Loss:</span> <span style='color:#f87171; font-weight:bold; white-space: nowrap;'>Rp{int(data['sup'])}</span>
        </div>
        {rr_html}
    </div>
    """, unsafe_allow_html=True)

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
# --- 3. KOTAK ANALISA (COMPACT 215px) ---
# ==========================================
if max_lot > 0 and score >= 5:
    mm_html = f"<div style='background:#065f46; color:#a7f3d0; padding:10px; border-radius:8px; text-align:center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);'>🛒 MAKSIMAL BELI:<br><div style='font-size:2rem; font-weight:900; line-height:1.2; margin-top:2px;'>{max_lot} LOT</div></div>"
else:
    mm_html = "<div style='background:#7f1d1d; color:#fca5a5; padding:10px; border-radius:8px; text-align:center; font-weight:bold; font-size:1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);'>🚫 TIDAK AMAN ENTRY</div>"

if "SQUEEZE" in data['bb_stat']: bb_html = f"<span style='color:#f87171; font-weight:bold;'>{data['bb_stat']}</span>"
else: bb_html = f"<span style='color:#4ade80; font-weight:bold;'>{data['bb_stat']}</span>"

if "Akumulasi" in status_bandar: bandar_html = "Bandar: <span style='color:#4ade80; font-weight:bold;'>Akumulasi Massal</span>"
elif "Distribusi" in status_bandar: bandar_html = "Bandar: <span style='color:#f87171; font-weight:bold;'>Distribusi Kuat</span>"
else: bandar_html = "Bandar: <span style='color:#fbbf24; font-weight:bold;'>Netral / Sepi</span>"

if "NET BUY" in status_asing: asing_html = "Asing: <span style='color:#4ade80; font-weight:bold;'>NET BUY (Masuk)</span>"
elif "NET SELL" in status_asing: asing_html = "Asing: <span style='color:#f87171; font-weight:bold;'>NET SELL (Keluar)</span>"
else: asing_html = "Asing: <span style='color:#fbbf24; font-weight:bold;'>Netral / Mixed</span>"

vwap_color = "#4ade80" if data['vwap_score'] == 1 else "#f87171"
if data['vwap_val'] > 0:
    vwap_html = f"VWAP: <span style='color:{vwap_color}; font-weight:bold;'>Rp{int(data['vwap_val'])} ({data['vwap_stat']})</span>"
else:
    vwap_html = f"VWAP: <span style='color:#9ca3af; font-weight:bold;'>Tunggu Data...</span>"

vpa_bg = "#065f46; color:#a7f3d0;" if data['vpa_score'] == 1 else "#78350f; color:#fde68a;"
vpa_html = f"<div style='background:{vpa_bg}; padding:4px 10px; border-radius:6px; margin-top:8px; display:inline-block; font-weight:bold; font-size:0.9rem;'>📊 VPA: {data['vpa_stat']}</div>"

if data['vcp_score'] == 1: vcp_color = "#4ade80"
elif "Menyempit" in data['vcp_stat']: vcp_color = "#fbbf24"
else: vcp_color = "#9ca3af"

if score >= 13: kesimpulan_html = f"⚡<br><div style='font-size:1.2rem; font-weight:900; color:#4ade80; margin: 4px 0;'>GOD MODE SNIPER!<br>{ticker_input} SIAP TERBANG</div>"
elif score >= 9: kesimpulan_html = f"🔥<br><div style='font-size:1.2rem; font-weight:900; color:#4ade80; margin: 4px 0;'>{ticker_input}<br>HIGH PROBABILITY</div>"
elif score >= 5: kesimpulan_html = f"⚠️<br><div style='font-size:1.2rem; font-weight:900; color:#fbbf24; margin: 4px 0;'>PANTAU KETAT<br>{ticker_input}</div>"
else: kesimpulan_html = f"💀<br><div style='font-size:1.2rem; font-weight:900; color:#f87171; margin: 4px 0;'>JAUHI {ticker_input}<br>SEMENTARA</div>"

shares_str = f"{data['shares'] / 1e9:.2f} Miliar Lembar" if data['shares'] != "N/A" else "Tidak diketahui"


# BOX 1 BARU: FUNDAMENTAL & GROWTH KUARTAL
box1 = f"""<div style='height: 215px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>💼 FUNDAMENTAL & Q-GROWTH</span><br><hr style='margin: 6px 0; border-color:#374151;'>
📌 <span style='color:#9ca3af;'>Valuasi (PER / PBV):</span> <strong style='color:#f3f4f6;'>{data['pe']} / {data['pbv']}</strong><br>
📌 <span style='color:#9ca3af;'>Profit (ROE / NPM):</span> <strong style='color:#f3f4f6;'>{data['roe']} / {data['npm']}</strong></div>
<div style='margin-top: auto;'><hr style='margin: 6px 0; border-color:#374151;'>📈 <span style='color:#9ca3af;'>EPS Growth (QoQ):</span> <strong style='color:{data['eps_color']}; font-size: 1.05rem;'>{data['eps_growth']}</strong></div>
</div>""".replace('\n', '')

box2 = f"""<div style='height: 215px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>🛡️ MONEY MANAGEMENT</span><br><hr style='margin: 6px 0; border-color:#374151;'><span style='color:#9ca3af;'>Modal:</span> <strong>Rp{modal_input:,.0f}</strong><br><span style='color:#9ca3af;'>Risiko:</span> <strong>{risk_pct*100}%</strong> <span style='color:#f87171;'>(Rp{max_loss_rp:,.0f})</span></div>
<div style='margin-top: auto;'>{mm_html}</div>
</div>""".replace('\n', '')

box3 = f"""<div style='height: 215px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>⭐ QUANT SNIPER SCORE</span><br><hr style='margin: 6px 0; border-color:#374151;'></div>
<div style='margin-top: auto; margin-bottom: auto; text-align: center;'>{kesimpulan_html}<div style='margin-top:8px; font-size:0.9rem; color:#9ca3af;'>Probabilitas Win: <strong style='color:{wr_color};'>{win_rate}</strong></div></div>
</div>""".replace('\n', '')

box4 = f"""<div style='height: 215px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>🦅 INSTITUTIONAL FLOW</span><br><hr style='margin: 6px 0; border-color:#374151;'>✔️ {asing_html}<br>✔️ {bandar_html}<br>✔️ {vwap_html}</div>
<div style='margin-top: auto;'><hr style='margin: 6px 0; border-color:#374151;'>{bb_html}</div>
</div>""".replace('\n', '')

box5 = f"""<div style='height: 215px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>⏳ MULTI-TIMEFRAME MATRIX</span><br><hr style='margin: 6px 0; border-color:#374151;'><span style='color:#9ca3af;'>Matrix:</span> <strong style='color:#4ade80;'>{data['mtf_status']}</strong><br><hr style='margin: 6px 0; border-color:#374151;'><span style='color:#9ca3af;'>Fibo:</span> <strong style='color:#f3f4f6;'>{data['fibo_stat']}</strong> | <span style='color:#fbbf24;'>GR: Rp{int(data['fibo_618'])}</span></div>
<div style='margin-top: auto; text-align: center;'>{vpa_html}</div>
</div>""".replace('\n', '')

box6 = f"""<div style='height: 215px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>📊 TEKNIKAL & PRICE ACTION</span><br><hr style='margin: 6px 0; border-color:#374151;'>📌 <span style='color:#9ca3af;'>EMA:</span> <strong>{data['ema_cross']}</strong><br>📌 <span style='color:#9ca3af;'>VCP:</span> <strong style='color:{vcp_color};'>{data['vcp_stat']}</strong><br>📌 <span style='color:#9ca3af;'>RSI:</span> <strong>{data['rsi_val']:.1f} ({data['rsi_status']})</strong></div>
<div style='margin-top: auto;'><hr style='margin: 6px 0; border-color:#374151;'>👥 <span style='color:#9ca3af;'>Saham Beredar:</span> <strong style='color:#f3f4f6;'>{shares_str}</strong></div>
</div>""".replace('\n', '')

col_b1, col_b2, col_b3 = st.columns(3)
with col_b1:
    with st.container(border=True): st.markdown(box1, unsafe_allow_html=True)
with col_b2:
    with st.container(border=True): st.markdown(box2, unsafe_allow_html=True)
with col_b3:
    with st.container(border=True): st.markdown(box3, unsafe_allow_html=True)

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

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
