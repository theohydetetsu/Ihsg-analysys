import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import math
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="HOLY GRAIL ULTIMATE - Quant Sniper", layout="wide")

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
# --- PANEL KONTROL ---
# ==========================================
st.markdown("### ⚙️ PANEL KONTROL (ULTIMATE QUANT SNIPER)")

col_in1, col_in2, col_in3, col_in4 = st.columns(4)
with col_in1:
    ticker_input = st.text_input("🔍 1. Kode Saham:", "BBCA").upper().strip()
with col_in2:
    manual_price_input = st.number_input("🎯 2. Harga Manual (Darurat):", min_value=0, value=0, step=1, help="Isi hanya jika YF web juga ngawur.")
with col_in3:
    status_bandar = st.selectbox("🕵️‍♂️ 3. Bandar:", ["Akumulasi (Net Buy)", "Netral / Sepi", "Distribusi (Net Sell)"])
with col_in4:
    status_bidoffer = st.selectbox("⚖️ 4. Bid & Offer:", ["Dominan BID (Demand Kuat)", "Berimbang (Normal)", "Dominan OFFER (Supply Kuat)"])

col_cf1, col_cf2, col_cf3 = st.columns(3)
with col_cf1:
    status_asing = st.selectbox("🦅 5. Asing (Foreign Flow):", ["Asing NET BUY (Masuk Besar)", "Asing Netral / Mixed", "Asing NET SELL (Keluar)"])
with col_cf2:
    modal_input = st.number_input("💰 6. Modal Trading (Rp):", min_value=100000, value=10000000, step=1000000)
with col_cf3:
    risiko_input = st.selectbox("🛡️ 7. Toleransi Risiko (Cutloss):", ["1% dari Modal (Sangat Konservatif)", "2% dari Modal (Standar Pro)", "3% dari Modal (Agresif)", "5% dari Modal (Sangat Agresif)"], index=1)

ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"
st.markdown("---")

# ==========================================
# --- MESIN KALKULASI DEWA V11 ---
# ==========================================
@st.cache_data(ttl=60)
def get_stock_data(ticker_symbol, manual_price=0):
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        hist = stock.history(period="6mo")
        hist = hist.dropna(subset=['Close', 'High', 'Low', 'Volume'])
        
        if hist.empty or len(hist) < 60: return None
        
        # LOGIKA V11: TARIK HARGA WEB FRONTEND DULU!
        api_live_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        api_prev_close = info.get('previousClose', 0)
        
        hist_latest_price = hist['Close'].iloc[-1]
        
        if manual_price > 0:
            latest_price = float(manual_price)
            prev_price = hist['Close'].iloc[-1] if hist['Close'].iloc[-1] != latest_price else hist['Close'].iloc[-2]
            change_pct = ((latest_price - prev_price) / prev_price) * 100
            hist.loc[hist.index[-1], 'Close'] = latest_price
            
        # V11 AUTO-SYNC: Kalau harga web beda sama history (history lemot)
        elif api_live_price > 0 and api_live_price != hist_latest_price:
            latest_price = float(api_live_price)
            prev_price = float(api_prev_close) if api_prev_close > 0 else hist_latest_price
            change_pct = ((latest_price - prev_price) / prev_price) * 100
            
            # Paksa update lilin (candle) terakhir di kalkulator AI
            hist.loc[hist.index[-1], 'Close'] = latest_price
            if latest_price > hist['High'].iloc[-1]: hist.loc[hist.index[-1], 'High'] = latest_price
            if latest_price < hist['Low'].iloc[-1]: hist.loc[hist.index[-1], 'Low'] = latest_price
        else:
            latest_price = hist_latest_price
            prev_price = hist['Close'].iloc[-2]
            change_pct = ((latest_price - prev_price) / prev_price) * 100
            
        company_name = info.get('longName', f"PT {ticker_symbol.replace('.JK', '')} Tbk")
        
        def safe_pct(val): return val if val is not None else 0
        def safe_num(val): return val if val is not None else 0
        
        pe_raw = safe_num(info.get('trailingPE'))
        pbv_raw = safe_num(info.get('priceToBook'))
        roe_raw = safe_pct(info.get('returnOnEquity'))
        npm_raw = safe_pct(info.get('profitMargins'))
        eps_g_raw = safe_pct(info.get('earningsQuarterlyGrowth'))
        
        pe_str = f"{pe_raw:.2f}x" if pe_raw > 0 else "N/A"
        pbv_str = f"{pbv_raw:.2f}x" if pbv_raw > 0 else "N/A"
        roe_str = f"{roe_raw * 100:.1f}%" if roe_raw != 0 else "N/A"
        npm_str = f"{npm_raw * 100:.1f}%" if npm_raw != 0 else "N/A"
        eps_g_str = f"{eps_g_raw * 100:.1f}%" if eps_g_raw != 0 else "N/A"
        
        def get_color(val, threshold, mode="high_good"):
            if val == 0 or val == "N/A": return "#9ca3af"
            if mode == "high_good": return "#4ade80" if val > threshold else "#f87171"
            else: return "#4ade80" if val < threshold else "#f87171"

        pe_col = get_color(pe_raw, 20, "low_good")
        pbv_col = get_color(pbv_raw, 2, "low_good")
        roe_col = get_color(roe_raw, 0.1, "high_good")
        npm_col = get_color(npm_raw, 0.05, "high_good")
        eps_g_col = get_color(eps_g_raw, 0, "high_good")

        f_score = sum([pe_raw>0 and pe_raw<20, pbv_raw>0 and pbv_raw<2, roe_raw>0.1, npm_raw>0.05, eps_g_raw>0])
        if f_score >= 3: stat_funda = "<span style='color:#4ade80;'>BAGUS</span>"
        elif f_score >= 1: stat_funda = "<span style='color:#fbbf24;'>STABIL</span>"
        else: stat_funda = "<span style='color:#f87171;'>JELEK</span>"

        mc_raw = info.get('marketCap', 0)
        mc_str = f"{mc_raw / 1e12:.2f} T" if mc_raw > 0 else "N/A"
        eps_ttm = safe_num(info.get('trailingEps'))
        ps_ratio = safe_num(info.get('priceToSalesTrailing12Months'))
        
        officers = info.get('companyOfficers', [])
        ceo_name = "N/A"
        for officer in officers:
            if 'CEO' in officer.get('title', '').upper():
                ceo_name = officer.get('name', 'N/A')
                break
        if ceo_name == "N/A" and officers: ceo_name = officers[0].get('name', 'N/A')
        
        if mc_raw >= 10e12: stat_stat = "<span style='color:#4ade80;'>BAGUS (Bluechip)</span>"
        elif mc_raw >= 1e12: stat_stat = "<span style='color:#fbbf24;'>STABIL (Midcap)</span>"
        else: stat_stat = "<span style='color:#f87171;'>JELEK (Smallcap)</span>"

        close_prices = hist['Close']
        ema9 = close_prices.ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = close_prices.ewm(span=21, adjust=False).mean().iloc[-1]
        ema_cross = "Bullish" if latest_price > ema21 else "Bearish"
        trend_status = "Bullish" if latest_price > ema21 else "Bearish"
        
        sma5 = close_prices.rolling(5).mean().iloc[-1]
        sma20 = close_prices.rolling(20).mean().iloc[-1]
        sma60 = close_prices.rolling(60).mean().iloc[-1]
        
        if latest_price > sma5 and latest_price > sma20 and latest_price > sma60: mtf_status, mtf_score = "ALIGNMENT BULLISH", 2
        elif latest_price > sma20: mtf_status, mtf_score = "MODERATE (Campur)", 1
        else: mtf_status, mtf_score = "DEAD CROSS (Bearish)", 0

        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_val = (100 - (100 / (1 + rs))).iloc[-1]
        if pd.isna(rsi_val): rsi_val = 50
        
        if rsi_val >= 70: rsi_status = "Overbought"
        elif rsi_val <= 30: rsi_status = "Oversold"
        else: rsi_status = "Netral"
        
        res_terdekat = hist['High'].tail(20).max()
        if latest_price > res_terdekat: res_terdekat = latest_price * 1.05
        sup_terdekat = hist['Low'].tail(20).min()
        if latest_price < sup_terdekat: sup_terdekat = latest_price * 0.95
        
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
        if pd.isna(vol_ratio): vol_ratio = 0
        
        if vol_ratio > 150: vpa_stat, vpa_score = f"Ledakan Vol ({int(vol_ratio)}%)", 1
        elif vol_ratio < 80: vpa_stat, vpa_score = f"Volume Kering ({int(vol_ratio)}%)", 0
        else: vpa_stat, vpa_score = f"Volume Normal ({int(vol_ratio)}%)", 0

        daily_range = hist['High'] - hist['Low']
        atr_20 = daily_range.rolling(20).mean().iloc[-1]
        atr_5 = daily_range.rolling(5).mean().iloc[-1]
        vol_5 = hist['Volume'].rolling(5).mean().iloc[-1]
        if atr_5 < (atr_20 * 0.8) and vol_5 < vol_ma20 and latest_price > sma60: vcp_stat, vcp_score = "Terdeteksi (Breakout)", 1
        elif atr_5 < atr_20: vcp_stat, vcp_score = "Menyempit (Formasi)", 0
        else: vcp_stat, vcp_score = "Melebar (Bukan VCP)", 0

        try:
            intraday = stock.history(period="1d", interval="5m").dropna(subset=['Close', 'Volume'])
            if not intraday.empty and intraday['Volume'].sum() > 0:
                typical_price = (intraday['High'] + intraday['Low'] + intraday['Close']) / 3
                vwap_kalkulasi = (typical_price * intraday['Volume']).cumsum() / intraday['Volume'].cumsum()
                vwap_val = vwap_kalkulasi.iloc[-1]
                if pd.isna(vwap_val): vwap_val = 0
                
                if latest_price > (vwap_val * 1.005): vwap_stat, vwap_score = "Atas VWAP (Bullish)", 1
                elif latest_price < (vwap_val * 0.995): vwap_stat, vwap_score = "Bawah VWAP (Lemah)", 0
                else: vwap_stat, vwap_score = "Area VWAP", 1
            else: vwap_val, vwap_stat, vwap_score = 0, "Tertunda", 0
        except: vwap_val, vwap_stat, vwap_score = 0, "Error", 0

        return {
            'price': latest_price, 'change': change_pct, 'name': company_name,
            'res': res_terdekat, 'sup': sup_terdekat, 'swing_high': swing_high,
            'fibo_618': fibo_618, 'fibo_stat': fibo_stat, 'fibo_score': fibo_score, 
            'ema_cross': ema_cross, 'trend': trend_status, 'rsi_val': rsi_val, 'rsi_status': rsi_status,
            'vpa_stat': vpa_stat, 'vpa_score': vpa_score,
            'mtf_status': mtf_status, 'mtf_score': mtf_score, 'vwap_val': vwap_val, 'vwap_stat': vwap_stat, 'vwap_score': vwap_score,
            'vcp_stat': vcp_stat, 'vcp_score': vcp_score,
            'pe_str': pe_str, 'pbv_str': pbv_str, 'roe_str': roe_str, 'npm_str': npm_str, 'eps_g_str': eps_g_str,
            'pe_col': pe_col, 'pbv_col': pbv_col, 'roe_col': roe_col, 'npm_col': npm_col, 'eps_g_col': eps_g_col,
            'stat_funda': stat_funda, 'mc_str': mc_str, 'eps_ttm': f"{eps_ttm:.2f}", 'ps_ratio': f"{ps_ratio:.2f}x", 
            'ceo': ceo_name, 'stat_stat': stat_stat
        }
    except:
        return None

data = get_stock_data(ticker_yf, manual_price_input)
if data is None:
    st.error(f"❌ Saham **{ticker_input}** tidak valid atau data kurang.")
    st.stop()

def s_int(val):
    try: return int(val) if pd.notna(val) else 0
    except: return 0

p_val = s_int(data['price'])
r_val = s_int(data['res'])
s_val = s_int(data['sup'])
sh_val = s_int(data['swing_high'])
f_val = s_int(data['fibo_618'])
vw_val = s_int(data['vwap_val'])


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
risk_per_share = p_val - s_val
if risk_per_share <= 0: risk_per_share = p_val * 0.02 

try:
    max_shares = max_loss_rp / risk_per_share
    max_lot = int(max_shares / 100) if pd.notna(max_shares) else 0
except:
    max_lot = 0
if max_lot < 1: max_lot = 0

if score >= 9: entry_val = f"<span style='color:#4ade80; font-weight:bold;'>Rp{p_val} (HK)</span>"
elif score >= 5: entry_val = f"<span style='color:#fbbf24; font-weight:bold;'>Rp{s_val} (Antre)</span>"
else: entry_val = "<span style='color:#f87171; font-weight:bold;'>Wait & See</span>"


# ==========================================
# --- 1. HEADER DASHBOARD ---
# ==========================================
arrow = "▼" if data['change'] < 0 else "▲"
color = "#f87171" if data['change'] < 0 else "#4ade80" 

now_wib = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
today_time_str = now_wib.strftime("%d %B %Y, %H:%M WIB") 
logo_url = f"https://assets.parqet.com/logos/symbol/{ticker_input}.JK?format=png"

col_h1, col_h2, col_h3, col_h4 = st.columns([1.5, 1.6, 1.1, 1.0])

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
    if score >= 13: st.markdown("<div style='color:#4ade80; font-size: 1.3rem; font-weight:900;'>GOD MODE &nbsp;<span style='font-size: 1rem;'>⭐⭐⭐⭐⭐</span></div>", unsafe_allow_html=True)
    elif score >= 9: st.markdown("<div style='color:#4ade80; font-size: 1.3rem; font-weight:900;'>STRONG BUY &nbsp;<span style='font-size: 1rem;'>⭐⭐⭐⭐</span></div>", unsafe_allow_html=True)
    elif score >= 5: st.markdown("<div style='color:#fbbf24; font-size: 1.3rem; font-weight:900;'>HOLD / WAIT &nbsp;<span style='font-size: 1rem;'>⭐⭐⭐</span></div>", unsafe_allow_html=True)
    else: st.markdown("<div style='color:#f87171; font-size: 1.3rem; font-weight:900;'>SELL / AVOID &nbsp;<span style='font-size: 1rem;'>⭐</span></div>", unsafe_allow_html=True)
    
    st.markdown(f"<div style='color:#fbbf24; font-size: 2.5rem; font-weight: 900; line-height:1.2;'>🌟 {score}.0<span style='font-size:1.2rem; color:#9ca3af;'>/16</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size: 0.95rem; color:#9ca3af;'>Win: <strong style='color:{wr_color};'>{win_rate}</strong></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_h3:
    st.markdown("<div style='text-align: right; margin-top: 15px;'>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9ca3af; font-size:0.95rem; font-weight:bold; white-space: nowrap;'>HARGA PENUTUPAN</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#f3f4f6; font-size: clamp(2.2rem, 4.5vw, 3.5rem); font-weight: 900; line-height: 1.1; white-space: nowrap;'>Rp{p_val}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color: {color}; font-size: 1.2rem; font-weight: bold; white-space: nowrap;'>{arrow} {data['change']:.2f}%</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_h4:
    reward = r_val - p_val
    rr_html = f"<div style='background:#1e3a8a; color:white; padding:4px; border-radius:4px; text-align:center; font-weight:bold; font-size:0.75rem; margin-top: 6px;'>⚖️ R:R = 1 : {round(reward / risk_per_share, 1) if risk_per_share > 0 else 0}</div>"
    
    st.markdown(f"""
    <div style='background: linear-gradient(145deg, #1f2937, #111827); border: 1px solid #374151; padding: 10px; border-radius: 10px; margin-top: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);'>
        <div style='color:#9ca3af; font-size:0.75rem; font-weight:bold; letter-spacing:1px; margin-bottom: 6px; white-space: nowrap;'>🎯 TRADE PLAN & SNIPER</div>
        <div style='display:flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 2px;'>
            <span style='color:#d1d5db;'>Entry:</span> <span>{entry_val}</span>
        </div>
        <div style='display:flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 2px;'>
            <span style='color:#d1d5db;'>Target:</span> <span style='color:#4ade80; font-weight:bold;'>Rp{r_val}</span>
        </div>
        <div style='display:flex; justify-content: space-between; font-size: 0.85rem;'>
            <span style='color:#d1d5db;'>Stop Loss:</span> <span style='color:#f87171; font-weight:bold;'>Rp{s_val}</span>
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
# --- 3. KOTAK ANALISA (COMPACT 180px) ---
# ==========================================
if max_lot > 0: stat_mm = "<span style='color:#4ade80;'>BAGUS</span>"
else: stat_mm = "<span style='color:#f87171;'>JELEK</span>"

if score >= 11: stat_flow = "<span style='color:#4ade80;'>BAGUS (Akumulasi Kuat)</span>"
elif score >= 6: stat_flow = "<span style='color:#fbbf24;'>STABIL (Netral)</span>"
else: stat_flow = "<span style='color:#f87171;'>JELEK (Distribusi)</span>"

if "ALIGNMENT BULLISH" in data['mtf_status'] and data['vpa_score'] == 1: stat_mtf = "<span style='color:#4ade80;'>BAGUS</span>"
elif "BEARISH" in data['mtf_status']: stat_mtf = "<span style='color:#f87171;'>JELEK</span>"
else: stat_mtf = "<span style='color:#fbbf24;'>STABIL</span>"

if "Bullish" in data['ema_cross'] and data['vcp_score'] == 1: stat_tech = "<span style='color:#4ade80;'>BAGUS (Breakout)</span>"
elif "Bearish" in data['ema_cross']: stat_tech = "<span style='color:#f87171;'>JELEK (Downtrend)</span>"
else: stat_tech = "<span style='color:#fbbf24;'>STABIL (Konsolidasi)</span>"

vcp_color = "#4ade80" if data['vcp_score'] == 1 else ("#fbbf24" if "Menyempit" in data['vcp_stat'] else "#9ca3af")
vwap_color = "#4ade80" if data['vwap_score'] == 1 else "#f87171"
vpa_color = "#4ade80" if data['vpa_score'] == 1 else "#fbbf24"

asing_html = f"<span style='color:#4ade80;'>NET BUY</span>" if "NET BUY" in status_asing else (f"<span style='color:#f87171;'>NET SELL</span>" if "NET SELL" in status_asing else f"<span style='color:#fbbf24;'>Netral</span>")
bandar_html = f"<span style='color:#4ade80;'>Akumulasi</span>" if "Akumulasi" in status_bandar else (f"<span style='color:#f87171;'>Distribusi</span>" if "Distribusi" in status_bandar else f"<span style='color:#fbbf24;'>Netral</span>")

box1 = f"""<div style='height: 180px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>💼 FUNDAMENTAL & GROWTH</span><br><hr style='margin: 4px 0; border-color:#374151;'>
<div style='display:flex; justify-content: space-between;'><span>PER:</span> <strong style='color:{data['pe_col']};'>{data['pe_str']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span>PBV:</span> <strong style='color:{data['pbv_col']};'>{data['pbv_str']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span>ROE:</span> <strong style='color:{data['roe_col']};'>{data['roe_str']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span>NPM:</span> <strong style='color:{data['npm_col']};'>{data['npm_str']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span>EPS (QoQ):</span> <strong style='color:{data['eps_g_col']};'>{data['eps_g_str']}</strong></div>
</div>
<div style='margin-top: auto;'><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{data['stat_funda']}</strong></div>
</div>""".replace('\n', '')

box2 = f"""<div style='height: 180px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>🛡️ MONEY MANAGEMENT</span><br><hr style='margin: 4px 0; border-color:#374151;'>
<span style='color:#9ca3af;'>Modal:</span> <strong>Rp{modal_input:,.0f}</strong><br>
<span style='color:#9ca3af;'>Risiko ({risk_pct*100}%):</span> <span style='color:#f87171;'>-Rp{max_loss_rp:,.0f}</span><br>
<br>✔️ Maksimal Beli: <strong style='color:#4ade80;'>{max_lot} LOT</strong>
</div>
<div style='margin-top: auto;'><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{stat_mm}</strong></div>
</div>""".replace('\n', '')

box3 = f"""<div style='height: 180px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>📊 STATISTIC SAAT INI</span><br><hr style='margin: 4px 0; border-color:#374151;'>
<div style='display:flex; justify-content: space-between;'><span>Market Cap:</span> <strong style='color:#f3f4f6;'>{data['mc_str']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span>Ratio Harga:</span> <strong style='color:#f3f4f6;'>{data['ps_ratio']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span>EPS Dasar(TTM):</span> <strong style='color:#f3f4f6;'>{data['eps_ttm']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span>CEO:</span> <strong style='color:#f3f4f6;'>{data['ceo'][:15]}</strong></div>
</div>
<div style='margin-top: auto;'><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{data['stat_stat']}</strong></div>
</div>""".replace('\n', '')

box4 = f"""<div style='height: 180px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>🦅 INSTITUTIONAL FLOW</span><br><hr style='margin: 4px 0; border-color:#374151;'>
✔️ Asing: {asing_html}<br>
✔️ Bandar: {bandar_html}<br>
✔️ VWAP: <strong style='color:{vwap_color};'>{data['vwap_stat']}</strong>
</div>
<div style='margin-top: auto;'><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{stat_flow}</strong></div>
</div>""".replace('\n', '')

box5 = f"""<div style='height: 180px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>⏳ MULTI-TIMEFRAME MATRIX</span><br><hr style='margin: 4px 0; border-color:#374151;'>
<span style='color:#9ca3af;'>Matrix:</span> <strong style='color:#4ade80;'>{data['mtf_status']}</strong><br>
<span style='color:#9ca3af;'>Fibo:</span> <strong style='color:#f3f4f6;'>{data['fibo_stat']}</strong><br>
<br>✔️ VPA: <strong style='color:{vpa_color};'>{data['vpa_stat']}</strong>
</div>
<div style='margin-top: auto;'><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{stat_mtf}</strong></div>
</div>""".replace('\n', '')

box6 = f"""<div style='height: 180px; display: flex; flex-direction: column;'>
<div><span style='font-size: 0.95rem; font-weight: bold;'>📈 TEKNIKAL & PRICE ACTION</span><br><hr style='margin: 4px 0; border-color:#374151;'>
📌 <span style='color:#9ca3af;'>EMA:</span> <strong>{data['ema_cross']}</strong><br>
📌 <span style='color:#9ca3af;'>VCP:</span> <strong style='color:{vcp_color};'>{data['vcp_stat']}</strong><br>
📌 <span style='color:#9ca3af;'>RSI:</span> <strong>{data['rsi_val']:.1f} ({data['rsi_status']})</strong>
</div>
<div style='margin-top: auto;'><hr style='margin: 4px 0; border-color:#374151;'>Status: <strong>{stat_tech}</strong></div>
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
