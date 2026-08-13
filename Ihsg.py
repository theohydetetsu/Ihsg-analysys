import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import numpy as np
import io
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="HOLY GRAIL V21 - God Tier", layout="wide")

st.markdown("""<style>
.stApp, [data-testid="stAppViewContainer"] {background-color: #020617 !important;}
[data-testid="stHeader"] {background-color: rgba(0,0,0,0) !important;}
h1, h2, h3, h4, h5, h6, p, span, li, label, div.stMarkdown, .stText {color: #f3f4f6 !important;}
[data-baseweb="base-input"] input, [data-baseweb="select"] div {background-color: #111827 !important; color: white !important; border-color: #374151 !important;}
.block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
header {visibility: hidden;}
div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #111827 !important; border: 1px solid #374151 !important; border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4) !important; padding: 0.6rem !important;}
p, span, li, div.stMarkdown, .stText {font-size: 0.8rem !important; line-height: 1.3 !important;}
hr {margin-top: 0.4rem; margin-bottom: 0.4rem; border-color: #374151;}
</style>""", unsafe_allow_html=True)
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">', unsafe_allow_html=True)

# ==========================================
# --- PANEL KONTROL V21 (CLEAN 4 KOLOM) ---
# ==========================================
st.markdown("### ⚙️ PANEL KONTROL (ULTIMATE V21 - GOD TIER)")

col_in1, col_in2, col_in3, col_in4 = st.columns(4)
with col_in1:
    ticker_input = st.text_input("🔍 1. Kode Saham:", "BBCA").upper().strip()
with col_in2:
    status_asing = st.selectbox("🦅 2. Asing Flow:", ["Asing NET BUY (Masuk Besar)", "Asing Netral / Mixed", "Asing NET SELL (Keluar)"])
with col_in3:
    modal_input = st.number_input("💰 3. Modal Trading (Rp):", min_value=100000, value=10000000, step=1000000)
with col_in4:
    risiko_input = st.selectbox("🛡️ 4. Toleransi Risiko:", ["1% dari Modal (Konservatif)", "2% dari Modal (Standar Pro)", "3% dari Modal (Agresif)", "5% dari Modal (Sangat Agresif)"], index=1)

ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"
st.markdown("---")

# ==========================================
# --- MESIN KALKULASI IHSG TRAFFIC LIGHT ---
# ==========================================
@st.cache_data(ttl=300)
def get_ihsg_status():
    try:
        ihsg = yf.Ticker("^JKSE")
        hist = ihsg.history(period="5d")
        if len(hist) >= 2:
            prev_close, curr_price = hist['Close'].iloc[-2], hist['Close'].iloc[-1]
            change_pct = ((curr_price - prev_close) / prev_close) * 100
            if change_pct > 0.3: return f"🟢 IHSG AMAN (+{change_pct:.2f}%)", "#4ade80"
            elif change_pct < -0.3: return f"🔴 IHSG RAWAN ({change_pct:.2f}%)", "#f87171"
            else: return f"🟡 IHSG SIDEWAYS ({change_pct:.2f}%)", "#fbbf24"
        return "⚪ IHSG OFFLINE", "#9ca3af"
    except: return "⚪ IHSG ERROR", "#9ca3af"

ihsg_text, ihsg_color = get_ihsg_status()

# ==========================================
# --- MESIN KALKULASI DEWA V21 ---
# ==========================================
@st.cache_data(ttl=60)
def get_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="6mo")
        hist = hist.dropna(subset=['Close', 'High', 'Low', 'Volume'])
        if hist.empty or len(hist) < 60: return None
            
        hist_latest_price = hist['Close'].iloc[-1]
        try: info = stock.info
        except: info = {}
        
        # 1. DIVIDEND TRAP RADAR
        div_warning = False
        try:
            divs = stock.dividends
            if not divs.empty:
                last_div_date = divs.index[-1]
                now_tz = datetime.datetime.now(last_div_date.tzinfo) if last_div_date.tzinfo else datetime.datetime.now()
                if abs((now_tz - last_div_date).days) <= 14:
                    div_warning = True
        except: pass
        
        api_live_price, api_prev_close = info.get('currentPrice', info.get('regularMarketPrice', 0)), info.get('previousClose', 0)
        if api_prev_close <= 0 and len(hist) > 1: api_prev_close = hist['Close'].iloc[-2]
        
        latest_price = hist_latest_price
        if api_live_price > 0 and api_live_price != hist_latest_price: 
            latest_price = float(api_live_price)
            
        hist.loc[hist.index[-1], 'Close'] = latest_price
        if latest_price > hist['High'].iloc[-1]: hist.loc[hist.index[-1], 'High'] = latest_price
        if latest_price < hist['Low'].iloc[-1]: hist.loc[hist.index[-1], 'Low'] = latest_price
            
        if latest_price <= 0: latest_price = 1 
        change_pct = ((latest_price - float(api_prev_close)) / float(api_prev_close)) * 100
        company_name = info.get('longName', f"PT {ticker_symbol.replace('.JK', '')} Tbk")
        
        limit_pct = 0.35 if api_prev_close < 200 else (0.25 if 200 <= api_prev_close <= 5000 else 0.20)
        ara_price, arb_price = int(api_prev_close * (1 + limit_pct)), int(api_prev_close * (1 - limit_pct))
        jarak_ara, jarak_arb = ((ara_price - latest_price) / latest_price) * 100, ((latest_price - arb_price) / latest_price) * 100

        close, low, high, vol = hist['Close'], hist['Low'], hist['High'], hist['Volume']
        
        # 2. AUTO BANDAR DETECTOR (OBV & CMF)
        obv = (np.sign(close.diff()) * vol).fillna(0).cumsum()
        obv_sma = obv.rolling(20).mean().iloc[-1]
        obv_latest = obv.iloc[-1]
        
        mfm = ((close - low) - (high - close)) / (high - low)
        mfm = mfm.replace([np.inf, -np.inf], 0).fillna(0)
        cmf = (mfm * vol).rolling(20).sum() / vol.rolling(20).sum()
        cmf_latest = cmf.iloc[-1]
        
        if cmf_latest > 0.05 and obv_latest > obv_sma:
            auto_bandar, bandar_score = "Akumulasi Kuat (AI)", 3
            obv_score = 2
        elif cmf_latest < -0.05:
            auto_bandar, bandar_score = "Distribusi Besar (AI)", 0
            obv_score = 0
        else:
            auto_bandar, bandar_score = "Netral / Sepi", 1
            obv_score = 1

        # Fundamental
        def safe_num(val): return val if val is not None else 0
        pe_raw, pbv_raw = safe_num(info.get('trailingPE')), safe_num(info.get('priceToBook'))
        roe_raw, npm_raw = safe_num(info.get('returnOnEquity')), safe_num(info.get('profitMargins'))
        pe_str = f"{pe_raw:.2f}x" if pe_raw > 0 else "N/A"
        pbv_str = f"{pbv_raw:.2f}x" if pbv_raw > 0 else "N/A"
        roe_str = f"{roe_raw * 100:.1f}%" if roe_raw != 0 else "N/A"

        f_score = sum([pe_raw>0 and pe_raw<20, pbv_raw>0 and pbv_raw<2, roe_raw>0.1, npm_raw>0.05])
        stat_funda = "<span style='color:#4ade80;'>BAGUS</span>" if f_score >= 3 else ("<span style='color:#fbbf24;'>STABIL</span>" if f_score >= 1 else "<span style='color:#f87171;'>JELEK</span>")

        # Teknikal
        sma20, sma60 = close.rolling(20).mean().iloc[-1], close.rolling(60).mean().iloc[-1]
        ema21 = close.ewm(span=21, adjust=False).mean().iloc[-1]
        ema_cross = trend_status = "Bullish" if latest_price > ema21 else "Bearish"
        
        if latest_price > sma20 and latest_price > sma60: mtf_status, mtf_score = "ALIGNMENT BULLISH", 2
        elif latest_price > sma20: mtf_status, mtf_score = "MODERATE (Campur)", 1
        else: mtf_status, mtf_score = "DEAD CROSS (Bearish)", 0

        std20 = close.rolling(20).std().iloc[-1]
        upper_bb, lower_bb = sma20 + (2 * std20), sma20 - (2 * std20)
        if latest_price > upper_bb: bb_stat, bb_score = "Breakout Atas (Kuat)", 2
        elif latest_price < lower_bb: bb_stat, bb_score = "Breakout Bawah (Lemah)", 0
        else: bb_stat, bb_score = "Di Dalam Bands (Normal)", 1

        delta = close.diff()
        rs = (delta.where(delta > 0, 0)).rolling(window=14).mean() / (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi_val = (100 - (100 / (1 + rs))).iloc[-1]
        if pd.isna(rsi_val): rsi_val = 50
        rsi_status = "Overbought" if rsi_val >= 70 else ("Oversold" if rsi_val <= 30 else "Netral")
        
        res_terdekat = hist['High'].tail(20).max()
        if latest_price > res_terdekat: res_terdekat = latest_price * 1.05
        sup_terdekat = hist['Low'].tail(20).min()
        if latest_price < sup_terdekat: sup_terdekat = latest_price * 0.95
        
        swing_high, swing_low = hist['High'].tail(60).max(), hist['Low'].tail(60).min()
        diff = swing_high - swing_low
        fibo_382, fibo_618 = swing_high - (0.382 * diff), swing_high - (0.618 * diff)
        if latest_price >= fibo_382: fibo_stat, fibo_score = "Aman (> 38.2%)", 1
        elif latest_price >= fibo_618: fibo_stat, fibo_score = "Golden Pocket", 1
        else: fibo_stat, fibo_score = "Jebol (< 61.8%)", 0

        vol_ma20 = vol.rolling(20).mean().iloc[-1]
        vol_ratio = (vol.iloc[-1] / vol_ma20) * 100 if vol_ma20 > 0 else 0
        vpa_stat, vpa_score = (f"Ledakan Vol ({int(vol_ratio)}%)", 1) if vol_ratio > 150 else (f"Volume Normal", 0)

        daily_range = high - low
        atr_20 = daily_range.rolling(20).mean().iloc[-1]
        
        # 3. DYNAMIC TRAILING STOP
        trailing_stop = latest_price - (1.5 * atr_20)
        if trailing_stop < sup_terdekat: trailing_stop = sup_terdekat

        if daily_range.rolling(5).mean().iloc[-1] < (atr_20 * 0.8) and latest_price > sma60: vcp_stat, vcp_score = "Terdeteksi (Breakout)", 1
        else: vcp_stat, vcp_score = "Bukan VCP", 0

        try:
            vwap_val = ((high + low + close) / 3 * vol).cumsum().iloc[-1] / vol.cumsum().iloc[-1]
            vwap_stat, vwap_score = ("Atas VWAP (Bullish)", 1) if latest_price > (vwap_val * 1.005) else ("Bawah VWAP", 0)
        except: vwap_val, vwap_stat, vwap_score = 0, "Error", 0

        return {
            'price': latest_price, 'change': change_pct, 'name': company_name, 'res': res_terdekat, 'sup': sup_terdekat, 'ts': trailing_stop,
            'fibo_stat': fibo_stat, 'fibo_score': fibo_score, 'ema_cross': ema_cross, 'trend': trend_status, 'rsi_val': rsi_val, 'rsi_status': rsi_status,
            'vpa_stat': vpa_stat, 'vpa_score': vpa_score, 'bb_stat': bb_stat, 'bb_score': bb_score, 'mtf_status': mtf_status, 'mtf_score': mtf_score, 
            'vwap_val': vwap_val, 'vwap_stat': vwap_stat, 'vwap_score': vwap_score, 'vcp_stat': vcp_stat, 'vcp_score': vcp_score,
            'pe_str': pe_str, 'pbv_str': pbv_str, 'roe_str': roe_str, 'stat_funda': stat_funda, 'mc_str': f"{info.get('marketCap', 0) / 1e12:.2f} T",
            'ara_price': ara_price, 'arb_price': arb_price, 'jarak_ara': jarak_ara, 'jarak_arb': jarak_arb, 'vol_ratio': vol_ratio,
            'auto_bandar': auto_bandar, 'bandar_score': bandar_score, 'obv_score': obv_score, 'div_warning': div_warning
        }
    except Exception as e: return None

data = get_stock_data(ticker_yf)
if data is None:
    st.error(f"❌ Saham **{ticker_input}** tidak valid atau Yahoo Finance sedang membatasi akses (Rate Limit).")
    st.stop()

p_val, r_val, s_val, ts_val = int(data['price']), int(data['res']), int(data['sup']), int(data['ts'])

# ==========================================
# --- PENILAIAN SKOR & PROBABILITAS (MAX 18) ---
# ==========================================
score = 0
if data['trend'] == "Bullish": score += 2
score += data['mtf_score']                          
score += data['bandar_score'] 
score += data['obv_score']    
if "NET BUY" in status_asing: score += 2            
elif "Neutral" in status_asing: score += 1
score += data['vwap_score']                         
if data['rsi_status'] in ["Netral", "Oversold"]: score += 1
score += data['fibo_score'] + data['vpa_score'] + data['vcp_score'] + data['bb_score']

if score >= 16: win_rate, wr_color = "95% (Sangat Tinggi)", "#4ade80"
elif score >= 12: win_rate, wr_color = "75% (Tinggi)", "#4ade80"
elif score >= 8: win_rate, wr_color = "50% (Spekulatif)", "#fbbf24"
else: win_rate, wr_color = "< 30% (Risiko Bahaya)", "#f87171"

risk_pct = float(risiko_input.split('%')[0]) / 100
max_loss_rp = modal_input * risk_pct
risk_per_share = p_val - s_val
if risk_per_share <= 0: risk_per_share = p_val * 0.02 
max_lot = int((max_loss_rp / risk_per_share) / 100) if pd.notna(max_loss_rp / risk_per_share) else 0
if max_lot < 1: max_lot = 0

reward = r_val - p_val
rr_ratio = round(reward / risk_per_share, 1) if risk_per_share > 0 else 0

# ----------------------------------------------------
# 🛡️ ENGINE ANTI FOMO & DIVIDEND TRAP
# ----------------------------------------------------
div_html = f"<div style='color:#f87171; font-weight:900; font-size:0.8rem; text-align:center; animation: blinker 1.5s linear infinite;'>⚠️ AWAS DIVIDEND TRAP!</div><style>@keyframes blinker {{ 50% {{ opacity: 0; }} }}</style>" if data['div_warning'] else ""

if data['rsi_val'] >= 85: 
    entry_val, border_glow, accent_color = f"<span style='color:#f87171; font-weight:bold;'>⚠️ JANGAN HK! (Pucuk)</span>", "0 0 15px rgba(248, 113, 113, 0.4)", "#f87171" 
elif rr_ratio < 0.5 and score >= 10:
    entry_val, border_glow, accent_color = f"<span style='color:#fbbf24; font-weight:bold;'>⚠️ ANTRE! (R:R Jelek)</span>", "0 0 15px rgba(251, 191, 36, 0.4)", "#fbbf24" 
elif data['jarak_ara'] < 3.0: 
    entry_val, border_glow, accent_color = f"<span style='color:#f87171; font-weight:bold;'>⚠️ HINDARI! (Rawan ARA)</span>", "0 0 15px rgba(248, 113, 113, 0.4)", "#f87171" 
elif score >= 10: 
    entry_val, border_glow, accent_color = f"<span style='color:#4ade80; font-weight:bold;'>Rp{p_val} (HAJAR KANAN)</span>", "0 0 15px rgba(74, 222, 128, 0.4)", "#4ade80" 
elif score >= 6: 
    entry_val, border_glow, accent_color = f"<span style='color:#fbbf24; font-weight:bold;'>Rp{s_val} (ANTRE BELI)</span>", "0 0 15px rgba(251, 191, 36, 0.4)", "#fbbf24" 
else: 
    entry_val, border_glow, accent_color = "<span style='color:#f87171; font-weight:bold;'>WAIT & SEE</span>", "0 0 15px rgba(248, 113, 113, 0.4)", "#f87171" 

# ==========================================
# --- 1. HEADER DASHBOARD ---
# ==========================================
arrow, color = ("▼", "#f87171") if data['change'] < 0 else ("▲", "#4ade80")
now_wib = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
logo_url = f"https://assets.parqet.com/logos/symbol/{ticker_input}.JK?format=png"

col_h1, col_h2, col_h3, col_h4 = st.columns([1.5, 1.4, 1.0, 1.4])

with col_h1:
    st.markdown(f"<div style='display:inline-block; background:rgba(255,255,255,0.05); border:1px solid #374151; padding:4px 10px; border-radius:6px; margin-bottom:8px;'><span style='color:{ihsg_color}; font-size:0.8rem; font-weight:bold; letter-spacing:0.5px;'>{ihsg_text}</span></div>", unsafe_allow_html=True)
    st.markdown(f"""<div style="display: flex; align-items: center; gap: 10px; margin-top: 5px; margin-bottom: 5px;"><img src="{logo_url}" width="60" height="60" style="border-radius: 12px; background: white; padding: 4px; flex-shrink: 0;" onerror="this.style.display='none'"><div style='color:#f3f4f6; font-size: clamp(2rem, 4vw, 3.8rem); font-weight: 900; line-height: 1; letter-spacing: 1px;'>{ticker_input}</div></div>""", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#d1d5db; font-size:1.05rem; font-weight:bold; white-space: nowrap;'>{data['name']}</div>", unsafe_allow_html=True)

with col_h2:
    st.markdown("<div style='text-align: center; margin-top: 15px;'>", unsafe_allow_html=True)
    if score >= 15: st.markdown("<div style='color:#4ade80; font-size: 1.3rem; font-weight:900;'>GOD MODE ⭐⭐⭐⭐⭐</div>", unsafe_allow_html=True)
    elif score >= 11: st.markdown("<div style='color:#4ade80; font-size: 1.3rem; font-weight:900;'>STRONG BUY ⭐⭐⭐⭐</div>", unsafe_allow_html=True)
    elif score >= 7: st.markdown("<div style='color:#fbbf24; font-size: 1.3rem; font-weight:900;'>HOLD / WAIT ⭐⭐⭐</div>", unsafe_allow_html=True)
    else: st.markdown("<div style='color:#f87171; font-size: 1.3rem; font-weight:900;'>SELL / AVOID ⭐</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#fbbf24; font-size: 2.5rem; font-weight: 900; line-height:1.2;'>🌟 {score}.0<span style='font-size:1.2rem; color:#9ca3af;'>/18</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size: 0.95rem; color:#9ca3af;'>Win: <strong style='color:{wr_color};'>{win_rate}</strong></div></div>", unsafe_allow_html=True)

with col_h3:
    st.markdown("<div style='text-align: right; margin-top: 15px;'><div style='color:#9ca3af; font-size:0.95rem; font-weight:bold;'>HARGA SAAT INI</div>", unsafe_allow_html=True)
    # UKURAN FONT HARGA DIPERKECIL DISINI
    st.markdown(f"<div style='color:#f3f4f6; font-size: clamp(1.8rem, 3.5vw, 2.8rem); font-weight: 900; line-height: 1.1;'>Rp{p_val}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color: {color}; font-size: 1.2rem; font-weight: bold;'>{arrow} {data['change']:.2f}%</div></div>", unsafe_allow_html=True)

with col_h4:
    rr_bg = "linear-gradient(90deg, #1e3a8a, #3b82f6)" if rr_ratio >= 1.5 else ("linear-gradient(90deg, #991b1b, #ef4444)" if rr_ratio < 0.5 else "linear-gradient(90deg, #78350f, #d97706)")
    # PERBAIKAN HTML AGAR TIDAK BOCOR MENJADI TEKS
    html_execution = f"""<div style='background: linear-gradient(145deg, #111827, #000000); border: 1px solid {accent_color}; padding: 15px; border-radius: 12px; box-shadow: {border_glow}; position: relative; overflow: hidden; margin-top: 8px;'>
<div style='position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: {accent_color}; box-shadow: 0 0 10px {accent_color};'></div>
<div style='color:#e5e7eb; font-size:0.8rem; font-weight:800; letter-spacing:1.5px; margin-bottom: 8px; text-align: center;'>FINAL EXECUTION</div>
{div_html}
<div style='display:flex; flex-direction: column; gap: 6px; margin-top:8px;'>
<div style='display:flex; justify-content: space-between; font-size: 0.85rem; border-bottom: 1px dashed #374151; padding-bottom: 4px;'><span style='color:#9ca3af;'>Entry Point</span> <span style='text-align: right;'>{entry_val}</span></div>
<div style='display:flex; justify-content: space-between; font-size: 0.85rem; border-bottom: 1px dashed #374151; padding-bottom: 4px;'><span style='color:#9ca3af;'>Take Profit</span> <span style='color:#4ade80; font-weight:900;'>Rp{r_val}</span></div>
<div style='display:flex; justify-content: space-between; font-size: 0.85rem; border-bottom: 1px dashed #374151; padding-bottom: 4px;'><span style='color:#9ca3af;'>Stop Loss (Support)</span> <span style='color:#f87171; font-weight:900;'>Rp{s_val}</span></div>
<div style='display:flex; justify-content: space-between; font-size: 0.85rem;'><span style='color:#9ca3af;'>Trailing Stop (ATR)</span> <span style='color:#fbbf24; font-weight:900;'>Rp{ts_val}</span></div>
</div>
<div style='background: {rr_bg}; color:white; padding:4px; border-radius:6px; text-align:center; font-weight:900; font-size:0.8rem; margin-top: 8px;'>⚖️ R:R = 1 : {rr_ratio}</div>
</div>"""
    st.markdown(html_execution, unsafe_allow_html=True)

st.divider()

# ==========================================
# --- 2. CHART ---
# ==========================================
components.html(f"""
<div style="border-radius: 10px; border: 1px solid #374151; overflow: hidden; background: #111827; margin-bottom: 15px; height: 420px;">
    <div id="tradingview_chart" style="height: 100%; width: 100%;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script>new TradingView.widget({{"autosize": true, "symbol": "{ticker_tv}", "interval": "D", "timezone": "Asia/Jakarta", "theme": "dark", "style": "1", "locale": "id", "hide_top_toolbar": true, "container_id": "tradingview_chart", "studies": ["Moving Average@tv-basicstudies"] }});</script>
</div>
""", height=430)

# ==========================================
# --- 3. KOTAK ANALISA ---
# ==========================================
st.markdown(f"""<div style='display:flex; justify-content:space-around; background:#111827; border: 1px solid #374151; padding:10px; border-radius:10px; margin-bottom: 15px;'>
    <div style='text-align:center;'>🚀 <span style='color:#9ca3af; font-size:0.9rem;'>Batas ARA:</span> <strong style='color:#4ade80; font-size:1.1rem;'>Rp{data['ara_price']}</strong> <span style='color:#4ade80; font-size:0.8rem;'>(+{data['jarak_ara']:.1f}%)</span></div>
    <div style='text-align:center;'>🩸 <span style='color:#9ca3af; font-size:0.9rem;'>Batas ARB:</span> <strong style='color:#f87171; font-size:1.1rem;'>Rp{data['arb_price']}</strong> <span style='color:#f87171; font-size:0.8rem;'>(-{data['jarak_arb']:.1f}%)</span></div></div>""", unsafe_allow_html=True)

stat_mm = "<span style='color:#4ade80;'>BAGUS</span>" if max_lot > 0 else "<span style='color:#f87171;'>JELEK</span>"
stat_flow = "<span style='color:#4ade80;'>BAGUS (Akumulasi AI)</span>" if data['bandar_score'] == 3 else ("<span style='color:#fbbf24;'>STABIL (Netral)</span>" if data['bandar_score'] == 1 else "<span style='color:#f87171;'>JELEK (Distribusi)</span>")
stat_mtf = "<span style='color:#4ade80;'>BAGUS</span>" if "ALIGNMENT BULLISH" in data['mtf_status'] and data['vpa_score'] == 1 else ("<span style='color:#f87171;'>JELEK</span>" if "BEARISH" in data['mtf_status'] else "<span style='color:#fbbf24;'>STABIL</span>")
stat_tech = "<span style='color:#4ade80;'>BAGUS (Trend Kuat)</span>" if "Bullish" in data['ema_cross'] and (data['vcp_score'] == 1 or data['bb_score'] == 2) else ("<span style='color:#f87171;'>JELEK (Downtrend)</span>" if "Bearish" in data['ema_cross'] else "<span style='color:#fbbf24;'>STABIL (Konsolidasi)</span>")

vcp_color = "#4ade80" if data['vcp_score'] == 1 else ("#fbbf24" if "Menyempit" in data['vcp_stat'] else "#9ca3af")
bb_color = "#4ade80" if data['bb_score'] == 2 else ("#f87171" if data['bb_score'] == 0 else "#f3f4f6")
rsi_color = "#f87171" if data['rsi_val'] >= 85 else ("#4ade80" if data['rsi_val'] <= 40 else "#f3f4f6")
asing_html = f"<span style='color:#4ade80;'>NET BUY</span>" if "NET BUY" in status_asing else (f"<span style='color:#f87171;'>NET SELL</span>" if "NET SELL" in status_asing else f"<span style='color:#fbbf24;'>Netral</span>")
bandar_html = f"<span style='color:#4ade80;'>{data['auto_bandar']}</span>" if data['bandar_score'] == 3 else (f"<span style='color:#f87171;'>{data['auto_bandar']}</span>" if data['bandar_score'] == 0 else f"<span style='color:#fbbf24;'>{data['auto_bandar']}</span>")

b1 = f"<div><span style='font-size: 0.95rem; font-weight: bold;'>💼 FUNDAMENTAL & GROWTH</span><br><hr style='margin: 4px 0; border-color:#374151;'><div style='display:flex; justify-content: space-between;'><span>PER:</span> <strong style='color:#f3f4f6;'>{data['pe_str']}</strong></div><div style='display:flex; justify-content: space-between;'><span>PBV:</span> <strong style='color:#f3f4f6;'>{data['pbv_str']}</strong></div><div style='display:flex; justify-content: space-between;'><span>ROE:</span> <strong style='color:#f3f4f6;'>{data['roe_str']}</strong></div><br><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{data['stat_funda']}</strong></div>"
b2 = f"<div><span style='font-size: 0.95rem; font-weight: bold;'>🛡️ MONEY MANAGEMENT</span><br><hr style='margin: 4px 0; border-color:#374151;'><span style='color:#9ca3af;'>Modal:</span> <strong>Rp{modal_input:,.0f}</strong><br><span style='color:#9ca3af;'>Risiko ({risk_pct*100}%):</span> <span style='color:#f87171;'>-Rp{max_loss_rp:,.0f}</span><br><br>✔️ Maks Beli: <strong style='color:#4ade80;'>{max_lot} LOT</strong><br><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{stat_mm}</strong></div>"
b3 = f"<div><span style='font-size: 0.95rem; font-weight: bold;'>📊 STATISTIC SAAT INI</span><br><hr style='margin: 4px 0; border-color:#374151;'><div style='display:flex; justify-content: space-between;'><span>Market Cap:</span> <strong style='color:#f3f4f6;'>{data['mc_str']}</strong></div><div style='display:flex; justify-content: space-between;'><span>Rasio Harga:</span> <strong style='color:#f3f4f6;'>N/A</strong></div><div style='display:flex; justify-content: space-between;'><span>Trailing Stop:</span> <strong style='color:#fbbf24;'>Rp{ts_val}</strong></div><br><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong style='color:#4ade80;'>Aktif</strong></div>"
b4 = f"<div><span style='font-size: 0.95rem; font-weight: bold;'>🦅 AI INSTITUTIONAL FLOW</span><br><hr style='margin: 4px 0; border-color:#374151;'>✔️ AI Flow: {bandar_html}<br>✔️ Asing (Man): {asing_html}<br>✔️ VWAP: <strong style='color:#4ade80;'>{data['vwap_stat']}</strong><br><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{stat_flow}</strong></div>"
b5 = f"<div><span style='font-size: 0.95rem; font-weight: bold;'>⏳ MULTI-TIMEFRAME MATRIX</span><br><hr style='margin: 4px 0; border-color:#374151;'><span style='color:#9ca3af;'>Matrix:</span> <strong style='color:#4ade80;'>{data['mtf_status']}</strong><br><span style='color:#9ca3af;'>Fibo:</span> <strong style='color:#f3f4f6;'>{data['fibo_stat']}</strong><br>✔️ VPA: <strong style='color:#4ade80;'>{data['vpa_stat']}</strong><br><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{stat_mtf}</strong></div>"
b6 = f"<div><span style='font-size: 0.95rem; font-weight: bold;'>📈 TEKNIKAL & PRICE ACTION</span><br><hr style='margin: 4px 0; border-color:#374151;'>📌 <span style='color:#9ca3af;'>Bands:</span> <strong style='color:{bb_color};'>{data['bb_stat']}</strong><br>📌 <span style='color:#9ca3af;'>VCP:</span> <strong style='color:{vcp_color};'>{data['vcp_stat']}</strong><br>📌 <span style='color:#9ca3af;'>RSI:</span> <strong style='color:{rsi_color};'>{data['rsi_val']:.1f}</strong><br><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{stat_tech}</strong></div>"

cols = st.columns(3)
for col, box in zip(cols, [b1, b2, b3]):
    with col:
        with st.container(border=True): st.markdown(box, unsafe_allow_html=True)
st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
cols2 = st.columns(3)
for col, box in zip(cols2, [b4, b5, b6]):
    with col:
        with st.container(border=True): st.markdown(box, unsafe_allow_html=True)

# ==========================================
# --- 4. TABS BAWAH (MOVERS, SCREENER, JOURNAL) ---
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📊 Pusat Data & Operasional")
tab_movers, tab_screener, tab_journal = st.tabs(["🔥 Top Movers", "🔎 Stock Scanner", "📈 Jurnal Portofolio"])

with tab_movers:
    components.html("""<div class="tradingview-widget-container" style="height: 700px; width: 100%;"><div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>{ "colorTheme": "dark", "dateRange": "12M", "exchange": "IDX", "showChart": false, "locale": "id", "width": "100%", "height": "700", "isTransparent": true }</script></div>""", height=700)
with tab_screener:
    components.html("""<div class="tradingview-widget-container" style="height: 700px; width: 100%;"><div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>{ "width": "100%", "height": "700", "defaultColumn": "overview", "defaultScreen": "general", "market": "indonesia", "showToolbar": true, "colorTheme": "dark", "locale": "id", "isTransparent": true }</script></div>""", height=700)

with tab_journal:
    st.markdown("#### 📥 Sinkronisasi Data Jurnal")
    # PERBAIKAN FORMAT WAKTU (STRFTIME ERROR) DISINI
    export_data = {"Tanggal": now_wib.strftime("%d %B %Y"), "Ticker": ticker_input, "Harga Saat Ini": p_val, "Target Profit": r_val, "Trailing Stop": ts_val, "Skor AI": f"{score}/18", "Win Rate": win_rate.split(' ')[0], "Rekomendasi": "HK" if score >=10 else "Wait", "AI Bandar Flow": data['auto_bandar'], "Risk/Reward": f"1:{rr_ratio}", "Max Lot": max_lot}
    
    col_j1, col_j2 = st.columns(2)
    with col_j1:
        st.markdown("**1. Ekspor Radar Saat Ini**")
        df_export = pd.DataFrame([export_data])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer: df_export.to_excel(writer, index=False, sheet_name='Quant_Data')
        st.download_button(label="⬇️ Download (Saham_Premium_Ecosystem_Final.xlsx)", data=output.getvalue(), file_name=f'Saham_Premium_Ecosystem_Final.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
    with col_j2:
        st.markdown("**2. Upload File Jurnal Lama**")
        uploaded_file = st.file_uploader("Pilih file Excel...", type=['xlsx'], label_visibility="collapsed")
        
    if uploaded_file is not None:
        try:
            df_journal = pd.read_excel(uploaded_file)
            st.success(f"✅ Data berhasil ditarik! Total riwayat: {len(df_journal)} transaksi.")
            st.dataframe(df_journal, use_container_width=True)
        except:
            st.error("Gagal membaca file. Pastikan formatnya sesuai (Excel .xlsx).")
