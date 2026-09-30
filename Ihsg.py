import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import numpy as np
import io
import math
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="HOLY GRAIL V31 - Scalper & Backtest", layout="wide")

st.markdown("""<style>
.stApp, [data-testid="stAppViewContainer"] {background-color: #030712 !important;}
[data-testid="stHeader"] {background-color: rgba(0,0,0,0) !important;}
h1, h2, h3, h4, h5, h6, p, span, li, label, div.stMarkdown, .stText {color: #f3f4f6 !important;}
[data-baseweb="base-input"] input, [data-baseweb="select"] div {background-color: #0f172a !important; color: white !important; border-color: #334155 !important;}
.block-container {padding-top: 0.5rem !important; padding-bottom: 0.5rem !important;} /* SLIMMER TOP/BOTTOM */
header {visibility: hidden;}

/* KOTAK LUXURY SLIM (PRESISI SAMA BESAR) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(145deg, #0f172a = 0%, #020617 = 100%) !important; 
    border: 1px solid #1e293b !important; 
    border-top: 2px solid #3b82f6 !important;
    border-radius: 12px !important; 
    box-shadow: 0 8px 12px -3px rgba(0, 0, 0, 0.5) !important; 
    padding: 0.8rem !important;
}
p, span, li, div.stMarkdown, .stText {font-size: 0.85rem !important; line-height: 1.4 !important;}
hr {margin-top: 0.3rem; margin-bottom: 0.3rem; border-color: #1e293b;}
.dataframe {background-color: #0f172a !important; color: #f3f4f6 !important; border-color: #334155 !important;}
</style>""", unsafe_allow_html=True)
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">', unsafe_allow_html=True)

# ==========================================
# --- PANEL KONTROL V31 (5 KOLOM) ---
# ==========================================
st.markdown("### ⚙ PANEL KONTROL (V31 - SCALPING & BACKTEST)")

col_in1, col_in2, col_in3, col_in4, col_in5 = st.columns(5)
with col_in1:
    ticker_input = st.text_input("🔍 1. Kode Saham:", "BBCA").upper().strip()
with col_in2:
    status_asing = st.selectbox("🦅 2. Asing Flow:", ["Asing NET BUY (Masuk Besar)", "Asing Netral / Mixed", "Asing NET SELL (Keluar)"])
with col_in3:
    modal_input = st.number_input("💰 3. Modal Trading (Rp):", min_value=100000, value=10000000, step=1000000)
with col_in4:
    risiko_input = st.selectbox("🛡️ 4. Toleransi Risiko:", ["1% dari Modal", "2% dari Modal", "3% dari Modal", "5% dari Modal"], index=1)
with col_in5:
    timeframe_input = st.selectbox("⏱️ 5. Mode Trading:", ["Swing (Harian)", "Scalping (15 Menit)"])

ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"
st.markdown("---")

is_scalping = "Scalping" in timeframe_input
yf_interval = "15m" if is_scalping else "1d"
tv_interval = "15" if is_scalping else "D"

if "NET BUY" in status_asing: asing_label = "<span style='color:#4ade80; font-weight:bold;'>NET BUY 🟢</span>"
elif "NET SELL" in status_asing: asing_label = "<span style='color:#f87171; font-weight:bold;'>NET SELL 🔴</span>"
else: asing_label = "<span style='color:#fbbf24; font-weight:bold;'>MIXED 🟡</span>"

def safe_num(val):
    try: return float(val) if val is not None and not pd.isna(val) else 0.0
    except: return 0.0

def safe_int(val):
    try: return int(float(val)) if val is not None and not pd.isna(val) else 0
    except: return 0

LOCAL_SECTOR_DB = {
    "BBCA": ("Financials", "Banks"), "BBRI": ("Financials", "Banks"), "BMRI": ("Financials", "Banks"), "BBNI": ("Financials", "Banks"),
    "TLKM": ("Communication Services", "Telecom"), "GOTO": ("Technology", "Software"), "ASII": ("Consumer Cyclicals", "Auto"),
    "ADRO": ("Energy", "Coal"), "PTBA": ("Energy", "Coal"), "ITMG": ("Energy", "Coal"), "UNTR": ("Industrials", "Heavy Mach"),
    "ICBP": ("Consumer Defensive", "Food"), "INDF": ("Consumer Defensive", "Food"), "UNVR": ("Consumer Defensive", "Household"),
    "AMMN": ("Basic Materials", "Copper/Gold"), "BREN": ("Utilities", "Renewable"), "BRPT": ("Basic Materials", "Chemicals"),
    "PGEO": ("Utilities", "Renewable"), "CUAN": ("Energy", "Coal"), "VIVA": ("Communication Services", "Media"),
    "DWGL": ("Energy", "Oil & Gas"), "IATA": ("Energy", "Coal")
}

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
        return "⚪ IHSG OFFLINE", "#94a3b8"
    except: return "⚪ IHSG ERROR", "#94a3b8"

ihsg_text, ihsg_color = get_ihsg_status()

# ==========================================
# --- MESIN KALKULASI DEWA V31 ---
# ==========================================
@st.cache_data(ttl=60)
def get_stock_data(ticker_symbol, is_screener=False, interval="1d"):
    try:
        period_yf = "60d" if interval == "15m" else ("3mo" if is_screener else "1y")
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period=period_yf, interval=interval) 
        if hist.empty or len(hist) < 60: return None
        
        hist_6m = hist.tail(130).copy()
        hist_latest_price = hist['Close'].iloc[-1]
        try: info = stock.info
        except: info = {}
        
        clean_ticker = ticker_symbol.replace('.JK', '')
        sector = info.get('sector')
        industry = info.get('industry')
        
        if (sector is None or sector == 'N/A' or sector == '') and clean_ticker in LOCAL_SECTOR_DB:
            sector, industry = LOCAL_SECTOR_DB[clean_ticker]
        else:
            sector = sector if sector else "Market"
            industry = industry if industry else "Indonesia"
            
        div_warning = False
        if not is_screener and interval == "1d":
            try:
                divs = stock.dividends
                if not divs.empty:
                    last_div_naive = divs.index[-1].tz_localize(None)
                    now_naive = datetime.datetime.utcnow()
                    if abs((now_naive - last_div_naive).days) <= 14: div_warning = True
            except: pass
        
        api_live_price = safe_num(info.get('currentPrice') or info.get('regularMarketPrice'))
        api_prev_close = safe_num(info.get('previousClose'))
        
        if api_prev_close <= 0 and len(hist) > 1: api_prev_close = hist['Close'].iloc[-2]
        if api_prev_close <= 0: api_prev_close = hist_latest_price
        
        latest_price = api_live_price if (api_live_price > 0 and api_live_price != hist_latest_price and interval == "1d") else hist_latest_price
        hist_6m.loc[hist_6m.index[-1], 'Close'] = latest_price
        
        if latest_price <= 0: latest_price = 1 
        change_pct = ((latest_price - api_prev_close) / api_prev_close) * 100
        company_name = info.get('longName', f"PT {clean_ticker} Tbk")
        
        limit_pct = 0.35 if api_prev_close < 200 else (0.25 if 200 <= api_prev_close <= 5000 else 0.20)
        ara_price, arb_price = safe_int(api_prev_close * (1 + limit_pct)), safe_int(api_prev_close * (1 - limit_pct))
        
        close, low, high, vol = hist_6m['Close'], hist_6m['Low'], hist_6m['High'], hist_6m['Volume']
        
        # --- TEKNIKAL ---
        sma20, sma60 = close.rolling(20).mean().iloc[-1], close.rolling(60).mean().iloc[-1]
        if latest_price > sma20 and latest_price > sma60: mtf_status, mtf_score, trend_col = "FASE MARKUP (Uptrend)", 2, "#4ade80"
        elif latest_price < sma20 and latest_price < sma60: mtf_status, mtf_score, trend_col = "FASE MARKDOWN (Downtrend)", 0, "#f87171"
        else: mtf_status, mtf_score, trend_col = "KONSOLIDASI (Sideways)", 1, "#fbbf24"

        delta = close.diff()
        rs = (delta.where(delta > 0, 0)).rolling(window=14).mean() / (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi_val = (100 - (100 / (1 + rs))).iloc[-1]
        if pd.isna(rsi_val): rsi_val = 50
        rsi_color = "#f87171" if rsi_val >= 70 else ("#4ade80" if rsi_val <= 30 else "#f3f4f6")

        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        if macd.iloc[-1] > macd_signal.iloc[-1]: macd_str, macd_score = "<strong style='color:#4ade80;'>Golden Cross 🟢</strong>", 1
        elif macd.iloc[-1] < macd_signal.iloc[-1]: macd_str, macd_score = "<strong style='color:#f87171;'>Dead Cross 🔴</strong>", 0
        else: macd_str, macd_score = "<strong style='color:#fbbf24;'>Netral 🟡</strong>", 0

        std20 = close.rolling(20).std().iloc[-1]
        upper_bb, lower_bb = sma20 + (2 * std20), sma20 - (2 * std20)
        if latest_price > upper_bb: bb_stat, bb_score = "Breakout Atas (Kuat)", 2
        elif latest_price < lower_bb: bb_stat, bb_score = "Jebol Bawah (Lemah)", 0
        else: bb_stat, bb_score = "Di Dalam Bands (Normal)", 1
        
        res_terdekat = hist_6m['High'].tail(20).max()
        if latest_price > res_terdekat: res_terdekat = latest_price * 1.05
        sup_terdekat = hist_6m['Low'].tail(20).min()
        if latest_price < sup_terdekat: sup_terdekat = latest_price * 0.95
        
        swing_high, swing_low = safe_num(hist_6m['High'].tail(60).max()), safe_num(hist_6m['Low'].tail(60).min())
        if swing_high == 0: swing_high = latest_price
        if swing_low == 0: swing_low = latest_price
        diff = swing_high - swing_low
        fibo_382, fibo_500, fibo_618 = swing_high - (0.382 * diff), swing_high - (0.500 * diff), swing_high - (0.618 * diff)
        if latest_price >= fibo_382: fibo_stat, fibo_score = "Aman (> 38.2%)", 1
        elif latest_price >= fibo_618: fibo_stat, fibo_score = "Golden Pocket Area", 1
        else: fibo_stat, fibo_score = "Jebol Support Mayor", 0

        daily_range = high - low
        atr_20 = daily_range.rolling(20).mean().iloc[-1]
        trailing_stop = latest_price - (1.5 * atr_20)
        if pd.isna(trailing_stop) or trailing_stop < sup_terdekat: trailing_stop = sup_terdekat

        # --- BANDARMOLOGY ---
        obv = (np.sign(close.diff()) * vol).fillna(0).cumsum()
        obv_sma = obv.rolling(20).mean().iloc[-1]
        obv_latest = obv.iloc[-1]
        mfm = ((close - low) - (high - close)) / (high - low)
        mfm = mfm.replace([np.inf, -np.inf], 0).fillna(0)
        cmf = (mfm * vol).rolling(20).sum() / vol.rolling(20).sum()
        cmf_latest = cmf.iloc[-1]
        
        if cmf_latest > 0.05 and obv_latest > obv_sma: auto_bandar, bandar_score, bandar_color = "Akumulasi Kuat (AI)", 3, "#4ade80"
        elif cmf_latest < -0.05: auto_bandar, bandar_score, bandar_color = "Distribusi Besar", 0, "#f87171"
        else: auto_bandar, bandar_score, bandar_color = "Netral / Sepi", 1, "#fbbf24"
        
        vol_ma20 = vol.rolling(20).mean().iloc[-1]
        vol_ratio = (vol.iloc[-1] / vol_ma20) * 100 if vol_ma20 > 0 else 0
        vpa_stat, vpa_score = (f"Ledakan Vol ({int(vol_ratio)}%)", 1) if vol_ratio > 150 else (f"Volume Normal", 0)
        
        if is_screener:
            return {
                "Ticker": clean_ticker, "Harga": safe_int(latest_price), "Bandar_Flow": auto_bandar, 
                "Asing_Flow": "N/A", "Fase": mtf_status, "RSI": round(rsi_val, 1)
            }

        high_52, low_52 = safe_num(hist['High'].max()), safe_num(hist['Low'].min())
        rentang_52 = f"<strong style='color:#f3f4f6;'>Rp{safe_int(low_52)} - Rp{safe_int(high_52)}</strong>"

        pe_raw = safe_num(info.get('trailingPE'))
        pbv_raw = safe_num(info.get('priceToBook'))
        roe_raw = safe_num(info.get('returnOnEquity'))
        eps_raw = safe_num(info.get('trailingEps')) 
        
        pe_color = "#4ade80" if 0 < pe_raw <= 15 else ("#fbbf24" if 15 < pe_raw <= 25 else ("#f87171" if pe_raw > 25 else "#94a3b8"))
        pbv_color = "#4ade80" if 0 < pbv_raw <= 1.5 else ("#fbbf24" if 1.5 < pbv_raw <= 3 else ("#f87171" if pbv_raw > 3 else "#94a3b8"))
        roe_color = "#4ade80" if roe_raw >= 0.15 else ("#fbbf24" if 0.05 <= roe_raw < 0.15 else ("#f87171" if roe_raw > 0 else "#94a3b8"))
        
        pe_str = f"<strong style='color:{pe_color};'>{pe_raw:.2f}x</strong>" if pe_raw > 0 else "<strong style='color:#94a3b8;'>N/A</strong>"
        pbv_str = f"<strong style='color:{pbv_color};'>{pbv_raw:.2f}x</strong>" if pbv_raw > 0 else "<strong style='color:#94a3b8;'>N/A</strong>"
        roe_str = f"<strong style='color:{roe_color};'>{roe_raw * 100:.1f}%</strong>" if roe_raw != 0 else "<strong style='color:#94a3b8;'>N/A</strong>"
        eps_str = f"<strong style='color:#f3f4f6;'>Rp{eps_raw:,.0f}</strong>" if eps_raw > 0 else "<strong style='color:#94a3b8;'>N/A</strong>"

        if pe_raw == 0 and pbv_raw == 0: 
            stat_funda, funda_bg = "MURNI TEKNIKAL / GORENGAN", "rgba(251, 191, 36, 0.15); border: 1px solid #fbbf24; color: #fbbf24;"
        else:
            f_score = sum([pe_raw>0 and pe_raw<25, pbv_raw>0 and pbv_raw<4, roe_raw>0.05])
            if f_score >= 2: stat_funda, funda_bg = "SEHAT / LAYAK INVEST", "rgba(74, 222, 128, 0.15); border: 1px solid #4ade80; color: #4ade80;"
            else: stat_funda, funda_bg = "BERISIKO / MAHAL", "rgba(248, 113, 113, 0.15); border: 1px solid #f87171; color: #f87171;"
        
        if rsi_val >= 70: stat_tech, tech_bg = "AWAS PUCUK (Rawan Guyur)", "rgba(248, 113, 113, 0.15); border: 1px solid #f87171; color: #f87171;"
        elif rsi_val <= 30: stat_tech, tech_bg = "Oversold Extreme (Area Pantul)", "rgba(74, 222, 128, 0.15); border: 1px solid #4ade80; color: #4ade80;"
        elif bb_score == 2 or macd_score == 1: stat_tech, tech_bg = "Tren Breakout / Momentum Kuat", "rgba(74, 222, 128, 0.15); border: 1px solid #4ade80; color: #4ade80;"
        else: stat_tech, tech_bg = "Konsolidasi / Momentum Wajar", "rgba(251, 191, 36, 0.15); border: 1px solid #fbbf24; color: #fbbf24;"
        
        if bandar_score == 3: stat_flow, flow_bg = "Akumulasi Masif (Institusi Masuk)", "rgba(74, 222, 128, 0.15); border: 1px solid #4ade80; color: #4ade80;"
        elif bandar_score == 0: stat_flow, flow_bg = "Awas Guyuran Bandar Besar", "rgba(248, 113, 113, 0.15); border: 1px solid #f87171; color: #f87171;"
        else: stat_flow, flow_bg = "Tarik Ulur (Market Mixed)", "rgba(251, 191, 36, 0.15); border: 1px solid #fbbf24; color: #fbbf24;"

        return {
            'price': latest_price, 'change': change_pct, 'name': company_name, 'res': res_terdekat, 'sup': sup_terdekat, 'ts': trailing_stop,
            'sector': sector, 'industry': industry, 'fibo_stat': fibo_stat, 'fibo_score': fibo_score, 'trend': mtf_status, 'trend_col': trend_col, 
            'rsi_val': rsi_val, 'macd_str': macd_str, 'vpa_stat': vpa_stat, 'vpa_score': vpa_score, 'bb_stat': bb_stat, 'bb_score': bb_score, 
            'mtf_score': mtf_score, 'pe_str': pe_str, 'pbv_str': pbv_str, 'roe_str': roe_str, 'eps_str': eps_str, 'stat_funda': stat_funda, 'funda_bg': funda_bg,
            'stat_tech': stat_tech, 'tech_bg': tech_bg, 'stat_flow': stat_flow, 'flow_bg': flow_bg, 'mc_str': f"{safe_num(info.get('marketCap')) / 1e12:.2f} T", 
            'ara_price': ara_price, 'arb_price': arb_price, 'auto_bandar': auto_bandar, 'bandar_color': bandar_color, 'bandar_score': bandar_score, 
            'div_warning': div_warning, 'rentang_52': rentang_52, 'fibo_100': swing_high, 'fibo_0': swing_low, 'fibo_618': fibo_618, 'fibo_500': fibo_500, 'fibo_382': fibo_382
        }
    except Exception as e: 
        return {"error": str(e)}

data = get_stock_data(ticker_yf, interval=yf_interval)
if data is None or isinstance(data, dict) and "error" in data:
    st.error(f"❌ Terjadi kesalahan data untuk saham {ticker_input}. Kemungkinan server Yahoo Finance sedang bermasalah.")
    st.stop()

p_val, r_val, s_val, ts_val = safe_int(data.get('price')), safe_int(data.get('res')), safe_int(data.get('sup')), safe_int(data.get('ts'))

score = 0
if data['change'] > 0: score += 2
score += data['mtf_score']                          
score += data['bandar_score'] 
if "NET BUY" in status_asing: score += 2            
elif "MIXED" in asing_label: score += 1
if data['rsi_val'] < 70: score += 2
score += data['fibo_score'] + data['vpa_score'] + data['bb_score']

if score >= 12: win_rate, wr_color = "90% (Sangat Tinggi)", "#4ade80"
elif score >= 8: win_rate, wr_color = "70% (Tinggi)", "#4ade80"
elif score >= 5: win_rate, wr_color = "50% (Spekulatif)", "#fbbf24"
else: win_rate, wr_color = "< 30% (Risiko Bahaya)", "#f87171"

risk_pct = float(risiko_input.split('%')[0]) / 100
max_loss_rp = modal_input * risk_pct
risk_per_share = p_val - s_val
if risk_per_share <= 0: risk_per_share = p_val * 0.02 
max_lot = int((max_loss_rp / risk_per_share) / 100) if pd.notna(max_loss_rp / risk_per_share) else 0
if max_lot < 1: max_lot = 0

reward = r_val - p_val
rr_ratio = round(reward / risk_per_share, 1) if risk_per_share > 0 else 0
div_html = f"<div style='color:#f87171; font-weight:900; font-size:0.75rem; text-align:center; animation: blinker 1.5s linear infinite;'>⚠️ AWAS DIVIDEND TRAP!</div><style>@keyframes blinker {{ 50% {{ opacity: 0; }} }}</style>" if data['div_warning'] else ""

if data['rsi_val'] >= 85: entry_val, border_glow, accent_color = f"<span style='color:#f87171; font-weight:bold;'>⚠️ JANGAN HK (Pucuk)</span>", "0 0 15px rgba(248, 113, 113, 0.4)", "#f87171" 
elif rr_ratio < 0.5 and score >= 8: entry_val, border_glow, accent_color = f"<span style='color:#fbbf24; font-weight:bold;'>⚠️ ANTRE! (R:R Jelek)</span>", "0 0 15px rgba(251, 191, 36, 0.4)", "#fbbf24" 
elif score >= 8: entry_val, border_glow, accent_color = f"<span style='color:#4ade80; font-weight:bold;'>Rp{p_val} (HAJAR KANAN)</span>", "0 0 15px rgba(74, 222, 128, 0.4)", "#4ade80" 
else: entry_val, border_glow, accent_color = "<span style='color:#fbbf24; font-weight:bold;'>WAIT / ANTRE BAWAH</span>", "0 0 15px rgba(251, 191, 36, 0.4)", "#fbbf24" 

# ==========================================
# --- 1. HEADER DASHBOARD ---
# ==========================================
arrow, color = ("▼", "#f87171") if data['change'] < 0 else ("▲", "#4ade80")
logo_url = f"https://assets.parqet.com/logos/symbol/{ticker_input}.JK?format=png"

col_h1, col_h2, col_h3, col_h4 = st.columns([1.6, 1.3, 1.1, 1.5])

with col_h1:
    st.markdown(f"<div style='display:inline-block; background:rgba(255,255,255,0.05); border:1px solid #334151; padding:2px 8px; border-radius:6px; margin-bottom:6px;'><span style='color:{ihsg_color}; font-size:0.75rem; font-weight:bold; letter-spacing:0.5px;'>{ihsg_text}</span></div>", unsafe_allow_html=True)
    st.markdown(f"""<div style="display: flex; align-items: center; gap: 8px; margin-top: 2px; margin-bottom: 2px;"><img src="{logo_url}" width="50" height="50" style="border-radius: 10px; background: white; padding: 3px; flex-shrink: 0;" onerror="this.style.display='none'"><div style='color:#f3f4f6; font-size: clamp(1.8rem, 3.5vw, 3.2rem); font-weight: 900; line-height: 1; letter-spacing: 1px;'>{ticker_input}</div></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div style='color:#94a3b8; font-size:0.95rem; font-weight:bold; white-space: nowrap;'>{data['name']}</div>
    <div style='margin-top: 4px; border-left: 2px solid #3b82f6; padding-left: 6px;'>
        <div style='font-size: 0.75rem; color: #64748b;'>Sector: <span style='color:#e2e8f0; font-weight:600;'>{data['sector']}</span> | Industry: <span style='color:#e2e8f0; font-weight:600;'>{data['industry']}</span></div>
    </div>""", unsafe_allow_html=True)

with col_h2:
    st.markdown("<div style='text-align: center; margin-top: 10px;'>", unsafe_allow_html=True)
    if score >= 12: st.markdown("<div style='color:#4ade80; font-size: 1.1rem; font-weight:900;'>GOD MODE ⭐⭐⭐⭐⭐</div>", unsafe_allow_html=True)
    elif score >= 8: st.markdown("<div style='color:#4ade80; font-size: 1.1rem; font-weight:900;'>STRONG BUY ⭐⭐⭐⭐</div>", unsafe_allow_html=True)
    elif score >= 5: st.markdown("<div style='color:#fbbf24; font-size: 1.1rem; font-weight:900;'>HOLD / WAIT ⭐⭐⭐</div>", unsafe_allow_html=True)
    else: st.markdown("<div style='color:#f87171; font-size: 1.1rem; font-weight:900;'>SELL / AVOID ⭐</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#fbbf24; font-size: 2.2rem; font-weight: 900; line-height:1.1;'>🌟 {score}.0<span style='font-size:1rem; color:#64748b;'>/15</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size: 0.85rem; color:#94a3b8;'>Win: <strong style='color:{wr_color};'>{win_rate}</strong></div></div>", unsafe_allow_html=True)

with col_h3:
    st.markdown(f"""<div style='display: flex; flex-direction: column; align-items: flex-end; justify-content: center; height: 100%; padding-top: 15px; padding-right: 10px;'>
        <div style='color:#94a3b8; font-size:0.8rem; font-weight:bold; letter-spacing: 1px; margin-bottom: 2px;'>HARGA SAAT INI</div>
        <div style='color:#f3f4f6; font-size: clamp(1.8rem, 3vw, 2.5rem); font-weight: 900; line-height: 1;'>Rp{p_val}</div>
        <div style='background: rgba({ '74, 222, 128' if data['change'] >= 0 else '248, 113, 113' }, 0.15); padding: 2px 6px; border-radius: 4px; color: {color}; font-size: 0.9rem; font-weight: bold; border: 1px solid {color}; margin-top: 6px; display: inline-block;'>
            {arrow} {data['change']:.2f}%
        </div></div>""", unsafe_allow_html=True)

with col_h4:
    rr_bg = "linear-gradient(90deg, #1e3a8a, #3b82f6)" if rr_ratio >= 1.5 else ("linear-gradient(90deg, #991b1b, #ef4444)" if rr_ratio < 0.5 else "linear-gradient(90deg, #78350f, #d97706)")
    html_execution = f"""<div style='background: linear-gradient(145deg, #0f172a, #020617); border: 1px solid {accent_color}; padding: 10px; border-radius: 12px; box-shadow: {border_glow}; position: relative; overflow: hidden; margin-top: 4px;'>
<div style='position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: {accent_color}; box-shadow: 0 0 10px {accent_color};'></div>
<div style='color:#e5e7eb; font-size:0.75rem; font-weight:800; letter-spacing:1px; margin-bottom: 6px; text-align: center;'>FINAL EXECUTION</div>
{div_html}
<div style='display:flex; flex-direction: column; gap: 4px; margin-top:4px;'>
<div style='display:flex; justify-content: space-between; font-size: 0.8rem; border-bottom: 1px dashed #334151; padding-bottom: 2px;'><span style='color:#94a3b8;'>Entry Point</span> <span style='text-align: right;'>{entry_val}</span></div>
<div style='display:flex; justify-content: space-between; font-size: 0.8rem; border-bottom: 1px dashed #334151; padding-bottom: 2px;'><span style='color:#94a3b8;'>Take Profit</span> <span style='color:#4ade80; font-weight:900;'>Rp{r_val}</span></div>
<div style='display:flex; justify-content: space-between; font-size: 0.8rem; border-bottom: 1px dashed #334151; padding-bottom: 2px;'><span style='color:#94a3b8;'>Stop Loss</span> <span style='color:#f87171; font-weight:900;'>Rp{s_val}</span></div>
<div style='display:flex; justify-content: space-between; font-size: 0.8rem; border-bottom: 1px dashed #334151; padding-bottom: 2px;'><span style='color:#94a3b8;'>Maks Beli</span> <span style='color:#4ade80; font-weight:900;'>{max_lot} LOT</span></div>
</div>
<div style='background: {rr_bg}; color:white; padding:2px; border-radius:4px; text-align:center; font-weight:900; font-size:0.75rem; margin-top: 6px;'>⚖️ R:R = 1 : {rr_ratio}</div>
</div>"""
    st.markdown(html_execution, unsafe_allow_html=True)

st.divider()

# ==========================================
# --- 2. CHART & TACTICAL FIBO BAR (SLIM CHART 380px) ---
# ==========================================
st.markdown(f"""
<div style='background: linear-gradient(90deg, #1e3a8a, #0f172a); border: 1px solid #3b82f6; padding: 6px 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.4);'>
    <div style='color:#93c5fd; font-weight:bold; font-size:0.8rem; text-transform:uppercase;'>🎯 Fibo Radar:</div>
    <div style='text-align:center; padding: 0 10px; border-right: 1px solid #334151;'><div style='font-size:0.65rem; color:#94a3b8;'>100% (High)</div><strong style='color:#f3f4f6; font-size:0.85rem;'>Rp{safe_int(data['fibo_100'])}</strong></div>
    <div style='text-align:center; padding: 0 10px; border-right: 1px solid #334151;'><div style='font-size:0.65rem; color:#4ade80;'>61.8% (Golden)</div><strong style='color:#4ade80; font-size:0.85rem;'>Rp{safe_int(data['fibo_618'])}</strong></div>
    <div style='text-align:center; padding: 0 10px; border-right: 1px solid #334151;'><div style='font-size:0.65rem; color:#fbbf24;'>50.0% (Mid)</div><strong style='color:#fbbf24; font-size:0.85rem;'>Rp{safe_int(data['fibo_500'])}</strong></div>
    <div style='text-align:center; padding: 0 10px; border-right: 1px solid #334151;'><div style='font-size:0.65rem; color:#f87171;'>38.2% (Support)</div><strong style='color:#f87171; font-size:0.85rem;'>Rp{safe_int(data['fibo_382'])}</strong></div>
    <div style='text-align:center; padding: 0 10px;'><div style='font-size:0.65rem; color:#94a3b8;'>0% (Low)</div><strong style='color:#f3f4f6; font-size:0.85rem;'>Rp{safe_int(data['fibo_0'])}</strong></div>
</div>
""", unsafe_allow_html=True)

components.html(f"""
<div style="border-radius: 10px; border: 1px solid #334151; overflow: hidden; background: #0f172a; margin-bottom: 10px; height: 380px;">
    <div id="tradingview_chart" style="height: 100%; width: 100%;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{
        "autosize": true,
        "symbol": "{ticker_tv}",
        "interval": "{tv_interval}",
        "timezone": "Asia/Jakarta",
        "theme": "dark",
        "style": "1",
        "locale": "id",
        "hide_top_toolbar": false,
        "container_id": "tradingview_chart",
        "studies": ["Volume@tv-basicstudies", "MACD@tv-basicstudies"]
    }});
    </script>
</div>
""", height=390)

# ==========================================
# --- 3. 3 KOTAK SENJATA UTAMA (SLIM 300px) ---
# ==========================================
st.markdown(f"""<div style='display:flex; justify-content:space-around; background:#0f172a; border: 1px solid #334151; padding:8px; border-radius:8px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
    <div style='text-align:center;'>🚀 <span style='color:#94a3b8; font-size:0.85rem;'>Batas ARA:</span> <strong style='color:#4ade80; font-size:1rem;'>Rp{data['ara_price']}</strong></div>
    <div style='text-align:center;'>🩸 <span style='color:#94a3b8; font-size:0.85rem;'>Batas ARB:</span> <strong style='color:#f87171; font-size:1rem;'>Rp{data['arb_price']}</strong></div></div>""", unsafe_allow_html=True)

def render_luxury_box(title, content, badge_text, badge_style):
    return f"""<div style='height: 300px; display: flex; flex-direction: column; justify-content: space-between;'>
    <div>
        <div style='font-size: 1rem; font-weight: 900; color:#38bdf8; letter-spacing: 0.5px;'>{title}</div>
        <hr style='margin: 4px 0; border-color:#334151;'>
        <div style='padding: 2px 0; display:flex; flex-direction: column; gap: 8px;'>{content}</div>
    </div>
    <div style='background: {badge_style}; border-radius: 6px; padding: 6px; text-align: center; margin-top: auto; font-weight: 800; font-size: 0.85rem; letter-spacing: 0.5px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
        {badge_text}
    </div>
</div>"""

c1 = f"""<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Market Cap:</span> <strong style='color:#f3f4f6;'>{data['mc_str']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Rentang 52W:</span> {data['rentang_52']}</div>
<hr style='margin: 2px 0; border: 0.5px dashed #334151;'>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>PER (Valuasi):</span> {data['pe_str']}</div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>PBV (Aset):</span> {data['pbv_str']}</div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>ROE (Kinerja):</span> {data['roe_str']}</div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>EPS (Laba):</span> {data['eps_str']}</div>"""
b1 = render_luxury_box("💼 1. FUNDAMENTAL & VALUASI", c1, f"STATUS: {data['stat_funda']}", data['funda_bg'])

c2 = f"""<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Tren Utama:</span> <strong style='color:{data['trend_col']};'>{data['trend']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Posisi Fibo:</span> <strong style='color:#f3f4f6;'>{data['fibo_stat']}</strong></div>
<hr style='margin: 2px 0; border: 0.5px dashed #334151;'>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>RSI (14):</span> <strong style='color:{data['rsi_color']}'>{data['rsi_val']:.1f}</strong></div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Sinyal MACD:</span> {data['macd_str']}</div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Bollinger Bands:</span> <strong style='color:#4ade80;'>{data['bb_stat']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Trailing Stop:</span> <strong style='color:#fbbf24;'>Rp{ts_val}</strong></div>"""
b2 = render_luxury_box("📈 2. TEKNIKAL & MOMENTUM", c2, f"KESIMPULAN: {data['stat_tech']}", data['tech_bg'])

c3 = f"""<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>AI Bandar Flow:</span> <strong style='color:{data['bandar_color']};'>{data['auto_bandar']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Asing Flow:</span> {asing_label}</div>
<hr style='margin: 2px 0; border: 0.5px dashed #334151;'>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Volume (VPA):</span> <strong style='color:#4ade80;'>{data['vpa_stat']}</strong></div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Volatilitas ATR:</span> <strong style='color:#4ade80;'>Terpantau</strong></div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Momentum Pasar:</span> <strong style='color:#f3f4f6;'>Aktif</strong></div>
<div style='display:flex; justify-content: space-between;'><span style='color:#94a3b8;'>Orderbook:</span> <strong style='color:#f3f4f6;'>Likuid</strong></div>"""
b3 = render_luxury_box("🦅 3. BANDARMOLOGY & FLOW", c3, f"FLOW: {data['stat_flow']}", data['flow_bg'])

cols = st.columns(3)
for col, box in zip(cols, [b1, b2, b3]):
    with col:
        with st.container(border=True): st.markdown(box, unsafe_allow_html=True)

# ==========================================
# --- 4. TABS BAWAH (MOVERS, SCREENER, BACKTEST) ---
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📊 Pusat Data & Operasional")
tab_movers, tab_screener, tab_backtest = st.tabs(["🔥 Top Movers", "🔎 Screener Bandar", "⏳ Simulator Backtest (NEW)"])

with tab_movers:
    components.html("""<div class="tradingview-widget-container" style="height: 600px; width: 100%;"><div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>{ "colorTheme": "dark", "dateRange": "12M", "exchange": "IDX", "showChart": false, "locale": "id", "width": "100%", "height": "600", "isTransparent": true }</script></div>""", height=600)

with tab_screener:
    st.markdown("#### 🔍 Saringan Saham Kustom: Bandarmology & Foreign Flow")
    col_sc1, col_sc2, col_sc3 = st.columns(3)
    with col_sc1: f_bandar = st.selectbox("Filter Bandar Flow:", ["Semua", "Akumulasi Kuat (AI)", "Netral / Sepi", "Distribusi Besar"])
    with col_sc2: f_asing = st.selectbox("Filter Asing Flow:", ["Semua", "Asing NET BUY (Masuk Besar)", "Asing Netral / Mixed", "Asing NET SELL (Keluar)"])
    with col_sc3: f_tren = st.selectbox("Fase Tren Saham:", ["Semua", "FASE MARKUP (Uptrend)", "KONSOLIDASI (Sideways)", "FASE MARKDOWN (Downtrend)"])
    input_watchlist = st.text_area("Daftar Pantauan (pisahkan dengan koma):", "DWGL, IATA, ADRO, BBCA, BBRI, BUMI, GOTO, TLKM, AMMN, BREN")
    
    if st.button("🚀 Jalankan Saringan Sinyal Super"):
        tickers_to_scan = [t.strip().upper() for t in input_watchlist.split(",") if t.strip()]
        hasil_scan = []
        progress_bar = st.progress(0)
        for idx, t_code in enumerate(tickers_to_scan):
            try:
                s_data = get_stock_data(f"{t_code}.JK", is_screener=True, interval="1d")
                if s_data and not "error" in s_data:
                    pass_bandar = True if f_bandar == "Semua" else (s_data["Bandar_Flow"] == f_bandar)
                    pass_tren = True if f_tren == "Semua" else (s_data["Fase"] == f_tren)
                    if pass_bandar and pass_tren:
                        hasil_scan.append({
                            "Ticker": s_data["Ticker"], "Harga": s_data["Harga"], "Bandar_Flow": s_data["Bandar_Flow"],
                            "Asing_Flow": status_asing, "Fase": s_data["Fase"], "RSI": s_data["RSI"]
                        })
            except Exception: pass
            progress_bar.progress((idx + 1) / len(tickers_to_scan))
        progress_bar.empty()
        
        if hasil_scan:
            st.success(f"Ditemukan {len(hasil_scan)} emiten yang sesuai dengan kriteria saringan! 🔥")
            st.dataframe(pd.DataFrame(hasil_scan), use_container_width=True)
        else:
            st.warning("Tidak ada emiten yang lolos filter. Coba ganti opsi 'Semua'.")

with tab_backtest:
    st.markdown("#### ⏳ Mesin Waktu Simulator (Backtest 1 Tahun)")
    st.markdown(f"Menguji strategi **Beli Saat Oversold (RSI < 40)** dan **Jual Saat Overbought (RSI > 70)** pada saham **{ticker_input}** berdasarkan data historis 1 tahun terakhir.")
    
    if st.button(f"🚀 Mulai Simulasi {ticker_input}"):
        with st.spinner('Menghitung data masa lalu...'):
            try:
                bt_data = yf.Ticker(ticker_yf).history(period="1y", interval="1d")
                if len(bt_data) > 50:
                    delta = bt_data['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    bt_data['RSI'] = 100 - (100 / (1 + rs))
                    
                    trades = []
                    in_position = False
                    buy_price = 0
                    
                    for i in range(20, len(bt_data)):
                        row = bt_data.iloc[i]
                        if not in_position and row['RSI'] < 40:
                            in_position = True
                            buy_price = row['Close']
                        elif in_position:
                            if row['RSI'] > 70 or row['Close'] < buy_price * 0.95: # 5% Cut loss
                                in_position = False
                                sell_price = row['Close']
                                profit = ((sell_price - buy_price) / buy_price) * 100
                                trades.append(profit)
                    
                    total_trades = len(trades)
                    if total_trades > 0:
                        win_trades = len([t for t in trades if t > 0])
                        win_rate_bt = (win_trades / total_trades) * 100
                        total_profit = sum(trades)
                        
                        html_bt = f"""<div style='display:flex; gap:15px; margin-top:20px; margin-bottom: 20px;'>
                           <div style='flex:1; background:#0f172a; padding:20px; border-radius:10px; border:1px solid #334151; text-align:center;'>
                               <div style='color:#94a3b8; font-size:0.9rem;'>Total Trade Eksekusi</div>
                               <div style='color:#f3f4f6; font-size:2rem; font-weight:bold;'>{total_trades}x</div>
                           </div>
                           <div style='flex:1; background:#0f172a; padding:20px; border-radius:10px; border:1px solid #334151; text-align:center;'>
                               <div style='color:#94a3b8; font-size:0.9rem;'>Akurasi Menang (Win Rate)</div>
                               <div style='color:#4ade80; font-size:2rem; font-weight:bold;'>{win_rate_bt:.1f}%</div>
                           </div>
                           <div style='flex:1; background:#0f172a; padding:20px; border-radius:10px; border:1px solid #334151; text-align:center;'>
                               <div style='color:#94a3b8; font-size:0.9rem;'>Total Akumulasi Cuan</div>
                               <div style='color:#38bdf8; font-size:2rem; font-weight:bold;'>{'+' if total_profit > 0 else ''}{total_profit:.2f}%</div>
                           </div>
                        </div>"""
                        st.markdown(html_bt, unsafe_allow_html=True)
                        st.success("✅ Simulasi Selesai! Angka di atas menunjukkan cuan/rugi bersih jika Bosku disiplin menggunakan indikator sistem pada saham ini selama setahun ke belakang.")
                    else:
                        st.warning("Tidak ada sinyal beli yang tervalidasi dalam 1 tahun terakhir.")
                else:
                    st.error("Data saham tidak cukup untuk simulasi 1 tahun.")
            except Exception as e:
                st.error(f"Gagal melakukan simulasi: {str(e)}")
