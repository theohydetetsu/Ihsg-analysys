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
st.set_page_config(page_title="HOLY GRAIL V36.6 - Perfect Symphony", layout="wide")

st.markdown("""<style>
.stApp, [data-testid="stAppViewContainer"] {background-color: #030712 !important;}
[data-testid="stHeader"] {background-color: rgba(0,0,0,0) !important;}
h1, h2, h3, h4, h5, h6, p, span, li, label, div.stMarkdown, .stText {color: #f3f4f6 !important;}
[data-baseweb="base-input"] input, [data-baseweb="select"] div {background-color: #0f172a !important; color: white !important; border-color: #334155 !important;}
.block-container {padding-top: 0.5rem !important; padding-bottom: 0.5rem !important;}
header {visibility: hidden;}

/* KOTAK LUXURY RESPONSIVE */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(145deg, #0f172a = 0%, #020617 = 100%) !important; 
    border: 1px solid #1e293b !important; 
    border-top: 2px solid #3b82f6 !important;
    border-radius: 12px !important; 
    box-shadow: 0 8px 12px -3px rgba(0, 0, 0, 0.5) !important; 
    padding: 0.8rem !important;
    height: 100% !important; 
}
p, span, li, div.stMarkdown, .stText {font-size: 0.85rem !important; line-height: 1.4 !important;}
hr {margin-top: 0.4rem; margin-bottom: 0.4rem; border-color: #1e293b;}
.dataframe {background-color: #0f172a !important; color: #f3f4f6 !important; border-color: #334155 !important;}
.streamlit-expanderHeader {background-color: #1e3a8a !important; color: white !important; border-radius: 8px !important; font-weight: bold !important;}
@keyframes blinker { 50% { opacity: 0.3; } }
@keyframes pulse_green { 0% {box-shadow: 0 0 15px #4ade8040;} 50% {box-shadow: 0 0 30px #4ade8080;} 100% {box-shadow: 0 0 15px #4ade8040;} }
@keyframes pulse_red { 0% {box-shadow: 0 0 15px #f8717140;} 50% {box-shadow: 0 0 30px #f8717180;} 100% {box-shadow: 0 0 15px #f8717140;} }
@keyframes pulse_yellow { 0% {box-shadow: 0 0 15px #fbbf2440;} 50% {box-shadow: 0 0 30px #fbbf2480;} 100% {box-shadow: 0 0 15px #fbbf2440;} }
</style>""", unsafe_allow_html=True)
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">', unsafe_allow_html=True)

# ==========================================
# --- PANEL KONTROL V36.6 ---
# ==========================================
st.markdown("### ⚙ PANEL KONTROL (V36.6 - PERFECT SYMPHONY)")

col_in1, col_in2, col_in3, col_in4, col_in5 = st.columns(5)
with col_in1: ticker_input = st.text_input("🔍 1. Kode Saham:", "BBCA").upper().strip()
with col_in2: status_asing = st.selectbox("🦅 2. Asing Flow:", ["Asing NET BUY (Masuk Besar)", "Asing Netral / Mixed", "Asing NET SELL (Keluar)"])
with col_in3: modal_input = st.number_input("💰 3. Modal Trading (Rp):", min_value=100000, value=10000000, step=1000000)
with col_in4: risiko_input = st.selectbox("🛡️ 4. Toleransi Risiko:", ["1% dari Modal", "2% dari Modal", "3% dari Modal", "5% dari Modal"], index=1)
with col_in5: timeframe_input = st.selectbox("⏱️ 5. Mode Trading:", ["Swing (Harian)", "Scalping (15 Menit)"])

ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"
st.markdown("---")

is_scalping = "Scalping" in timeframe_input
yf_interval = "15m" if is_scalping else "1d"
tv_interval = "D" 

if "NET BUY" in status_asing: asing_label = "<span style='color:#4ade80; font-weight:bold;'>NET BUY 🟢</span>"
elif "NET SELL" in status_asing: asing_label = "<span style='color:#f87171; font-weight:bold;'>NET SELL 🔴</span>"
else: asing_label = "<span style='color:#fbbf24; font-weight:bold;'>MIXED 🟡</span>"

def safe_num(val):
    try: return float(val) if val is not None and not pd.isna(val) else 0.0
    except: return 0.0

def safe_int(val):
    try: return int(float(val)) if val is not None and not pd.isna(val) else 0
    except: return 0

# --- PELACAK IHSG JUMBO (V36.6) ---
@st.cache_data(ttl=300)
def get_ihsg_status():
    try:
        ihsg = yf.Ticker("^JKSE")
        hist = ihsg.history(period="5d")
        if len(hist) >= 2:
            prev_close, curr_price = hist['Close'].iloc[-2], hist['Close'].iloc[-1]
            change_pct = ((curr_price - prev_close) / prev_close) * 100
            price_str = f"{curr_price:,.2f}"
            if change_pct > 0.3: return f"IHSG AMAN (+{change_pct:.2f}%)", "#4ade80", "pulse_green", price_str
            elif change_pct < -0.3: return f"IHSG RAWAN ({change_pct:.2f}%)", "#f87171", "pulse_red", price_str
            else: return f"IHSG SIDEWAYS ({change_pct:.2f}%)", "#fbbf24", "pulse_yellow", price_str
        return "IHSG OFFLINE", "#94a3b8", "none", "0.00"
    except: return "IHSG ERROR", "#94a3b8", "none", "0.00"

ihsg_text, ihsg_color, ihsg_anim, ihsg_price = get_ihsg_status()

# TAMPILAN IHSG JUMBO DENGAN HARGA REAL-TIME
st.markdown(f"""
<div style='background: linear-gradient(145deg, #020617, #0f172a); border: 2px solid {ihsg_color}; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 25px; animation: {ihsg_anim} 2s infinite; box-shadow: 0 0 15px {ihsg_color}40;'>
    <h3 style='margin:0 0 8px 0; color:#f3f4f6; font-weight:900; letter-spacing: 1px; font-size: 1.2rem; text-transform:uppercase;'>🧭 KOMPAS PASAR UTAMA</h3>
    <div style='display:flex; justify-content:center; align-items:center; gap: 20px; flex-wrap: wrap;'>
        <span style='font-size: 2.5rem; font-weight: 900; color: #f3f4f6; letter-spacing: 1px;'>{ihsg_price}</span>
        <span style='font-size: 1.3rem; font-weight: 900; color: {ihsg_color}; background: {ihsg_color}15; padding: 6px 16px; border-radius: 8px; border: 1px solid {ihsg_color}50;'>{ihsg_text}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- DATABASE SEKTOR LOKAL ---
LOCAL_SECTOR_DB = {
    "BBCA": ("Financials", "Banks"), "BBRI": ("Financials", "Banks"), "BMRI": ("Financials", "Banks"), "BBNI": ("Financials", "Banks"),
    "TLKM": ("Communication Services", "Telecom"), "GOTO": ("Technology", "Software"), "ASII": ("Consumer Cyclicals", "Auto"),
    "ADRO": ("Energy", "Coal"), "PTBA": ("Energy", "Coal"), "ITMG": ("Energy", "Coal"), "UNTR": ("Industrials", "Heavy Mach"),
    "ICBP": ("Consumer Defensive", "Food"), "INDF": ("Consumer Defensive", "Food"), "UNVR": ("Consumer Defensive", "Household"),
    "AMMN": ("Basic Materials", "Copper/Gold"), "BREN": ("Utilities", "Renewable"), "BRPT": ("Basic Materials", "Chemicals"),
    "PGEO": ("Utilities", "Renewable"), "CUAN": ("Energy", "Coal"), "VIVA": ("Communication Services", "Media")
}

# ==========================================
# --- MESIN KALKULASI DEWA V36.6 ---
# ==========================================
@st.cache_data(ttl=60)
def get_stock_data(ticker_symbol, is_screener=False, interval="1d"):
    try:
        period_yf = "59d" if interval == "15m" else ("3mo" if is_screener else "1y")
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period=period_yf, interval=interval) 
        if hist.empty or len(hist) < 20: return None
        
        hist_6m = hist.tail(130).copy()
        hist_latest_price = hist['Close'].iloc[-1]
        
        try: info = stock.info
        except: info = {}
        if not info or len(info) < 5:
            try:
                fast = stock.fast_info
                info['marketCap'] = fast.get('market_cap', 0)
            except: pass

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
        
        # --- 🦅 MATA ELANG (CANDLESTICK AI) ---
        c_O, c_H, c_L, c_C = hist_6m['Open'].iloc[-1], hist_6m['High'].iloc[-1], hist_6m['Low'].iloc[-1], hist_6m['Close'].iloc[-1]
        p_O, p_C = hist_6m['Open'].iloc[-2], hist_6m['Close'].iloc[-2]
        
        body = abs(c_C - c_O)
        hl_range = c_H - c_L if c_H != c_L else 0.01
        u_shadow = c_H - max(c_O, c_C)
        l_shadow = min(c_O, c_C) - c_L
        
        candle_pattern = "Netral (Biasa)"
        candle_color = "#f3f4f6"
        
        if body <= hl_range * 0.1:
            candle_pattern = "Doji (Ragu/Pembalikan)"
            candle_color = "#fbbf24"
        elif l_shadow >= 2 * body and u_shadow <= 0.1 * body:
            candle_pattern = "Hammer (Nahan Bawah)"
            candle_color = "#4ade80"
        elif c_C > c_O and p_C < p_O and c_C > p_O and c_O < p_C:
            candle_pattern = "Bullish Engulfing (Kuat)"
            candle_color = "#4ade80"
        elif c_C < c_O and p_C > p_O and c_C < p_O and c_O > p_C:
            candle_pattern = "Bearish Engulfing (Awas Guyur)"
            candle_color = "#f87171"
        elif c_C > c_O and body > hl_range * 0.8:
            candle_pattern = "Marubozu Hijau (Dorongan Beli)"
            candle_color = "#4ade80"
            
        # --- 🎯 AUTO-PIVOT CAMARILLA ---
        cam_H, cam_L, cam_C_prev = hist_6m['High'].iloc[-2], hist_6m['Low'].iloc[-2], hist_6m['Close'].iloc[-2]
        cam_range = cam_H - cam_L
        if cam_range == 0: cam_range = cam_C_prev * 0.02
        cam_h4 = cam_C_prev + (cam_range * 1.1 / 2)
        cam_h3 = cam_C_prev + (cam_range * 1.1 / 4)
        cam_l3 = cam_C_prev - (cam_range * 1.1 / 4)
        cam_l4 = cam_C_prev - (cam_range * 1.1 / 2)

        # --- TEKNIKAL STANDARD ---
        sma20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else close.iloc[-1]
        sma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else sma20
        if latest_price > sma20 and latest_price > sma60: mtf_status, mtf_score, trend_col = "Uptrend (Markup)", 2, "#4ade80"
        elif latest_price < sma20 and latest_price < sma60: mtf_status, mtf_score, trend_col = "Downtrend (Markdown)", 0, "#f87171"
        else: mtf_status, mtf_score, trend_col = "Sideways", 1, "#fbbf24"

        delta = close.diff()
        rs = (delta.where(delta > 0, 0)).rolling(window=14).mean() / (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi_val = (100 - (100 / (1 + rs))).iloc[-1]
        if pd.isna(rsi_val): rsi_val = 50

        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        if macd.iloc[-1] > macd_signal.iloc[-1]: macd_str, macd_score = "<strong style='color:#4ade80;'>Golden Cross 🟢</strong>", 1
        elif macd.iloc[-1] < macd_signal.iloc[-1]: macd_str, macd_score = "<strong style='color:#f87171;'>Dead Cross 🔴</strong>", 0
        else: macd_str, macd_score = "<strong style='color:#fbbf24;'>Netral 🟡</strong>", 0

        std20 = close.rolling(20).std().iloc[-1] if len(close) >= 20 else 1.0
        upper_bb, lower_bb = sma20 + (2 * std20), sma20 - (2 * std20)
        if latest_price > upper_bb: bb_stat, bb_score = "Breakout Atas", 2
        elif latest_price < lower_bb: bb_stat, bb_score = "Jebol Bawah", 0
        else: bb_stat, bb_score = "Area Dalam Bands", 1
        
        res_terdekat = hist_6m['High'].tail(20).max() if len(hist_6m) >= 20 else latest_price * 1.05
        sup_terdekat = hist_6m['Low'].tail(20).min() if len(hist_6m) >= 20 else latest_price * 0.95
        
        swing_high, swing_low = safe_num(hist_6m['High'].tail(60).max()), safe_num(hist_6m['Low'].tail(60).min())
        diff = swing_high - swing_low
        fibo_382, fibo_500, fibo_618 = swing_high - (0.382 * diff), swing_high - (0.500 * diff), swing_high - (0.618 * diff)
        if latest_price >= fibo_382: fibo_stat, fibo_score = "Aman (>38.2%)", 1
        elif latest_price >= fibo_618: fibo_stat, fibo_score = "Golden Pocket", 1
        else: fibo_stat, fibo_score = "Jebol Mayor", 0

        atr_20 = (high - low).rolling(20).mean().iloc[-1] if len(high) >= 20 else (latest_price * 0.02)
        trailing_stop = latest_price - (1.5 * atr_20)
        if pd.isna(trailing_stop) or trailing_stop < sup_terdekat: trailing_stop = sup_terdekat

        # --- BANDARMOLOGY ---
        obv = (np.sign(close.diff()) * vol).fillna(0).cumsum()
        obv_sma = obv.rolling(20).mean().iloc[-1] if len(obv) >= 20 else obv.iloc[-1]
        
        mfm = ((close - low) - (high - close)) / (high - low)
        mfm = mfm.replace([np.inf, -np.inf], 0).fillna(0)
        cmf_vol_sum = vol.rolling(20).sum().iloc[-1]
        cmf_latest = ((mfm * vol).rolling(20).sum() / cmf_vol_sum).iloc[-1] if cmf_vol_sum > 0 else 0
        
        if cmf_latest > 0.05 and obv.iloc[-1] > obv_sma: auto_bandar, bandar_score, bandar_color = "Akumulasi AI", 3, "#4ade80"
        elif cmf_latest < -0.05: auto_bandar, bandar_score, bandar_color = "Distribusi Besar", 0, "#f87171"
        else: auto_bandar, bandar_score, bandar_color = "Netral / Sepi", 1, "#fbbf24"
        
        vol_ma20 = vol.rolling(20).mean().iloc[-1] if len(vol) >= 20 else vol.iloc[-1]
        vol_ratio = (vol.iloc[-1] / vol_ma20) * 100 if vol_ma20 > 0 else 100
        vpa_stat, vpa_score = (f"Ledakan ({int(vol_ratio)}%)", 1) if vol_ratio > 150 else (f"Volume Normal", 0)
        
        # --- PERHITUNGAN LIKUIDITAS & TURNOVER (V36.6) ---
        avg_turnover = vol_ma20 * latest_price
        if avg_turnover >= 5_000_000_000:
            liq_stat, liq_col = "Sangat Ramai (Aman)", "#4ade80"
        elif avg_turnover >= 500_000_000:
            liq_stat, liq_col = "Wajar / Standar", "#fbbf24"
        else:                            
            liq_stat, liq_col = "Sepi (Awas Guyuran)", "#f87171"
            
        if avg_turnover >= 1_000_000_000: turnover_str = f"Rp {avg_turnover/1_000_000_000:.1f} Milyar"
        else: turnover_str = f"Rp {avg_turnover/1_000_000:.1f} Juta"

        if is_screener:
            return {"Ticker": clean_ticker, "Harga": safe_int(latest_price), "Bandar_Flow": auto_bandar, "Fase": mtf_status, "RSI": round(safe_num(rsi_val), 1)}

        pe_raw = safe_num(info.get('trailingPE'))
        pbv_raw = safe_num(info.get('priceToBook'))
        roe_raw = safe_num(info.get('returnOnEquity'))
        eps_raw = safe_num(info.get('trailingEps')) 
        
        if pe_raw > 0:
            if pe_raw <= 15: pe_label, pe_col = " (Murah)", "#4ade80"
            elif pe_raw <= 25: pe_label, pe_col = " (Wajar)", "#fbbf24"
            else: pe_label, pe_col = " (Mahal)", "#f87171"
            pe_disp = f"{pe_raw:.1f}x" if pe_raw < 1000 else ">1000x"
            pe_str = f"<strong style='color:{pe_col};'>{pe_disp}{pe_label}</strong>"
        elif pe_raw < 0: pe_str = "<strong style='color:#f87171;'>Minus (Rugi)</strong>"
        else: pe_str = "<strong style='color:#94a3b8;'>N/A (Server Sibuk)</strong>"

        if pbv_raw > 0:
            if pbv_raw <= 1.5: pbv_label, pbv_col = " (Murah)", "#4ade80"
            elif pbv_raw <= 3.0: pbv_label, pbv_col = " (Wajar)", "#fbbf24"
            else: pbv_label, pbv_col = " (Mahal)", "#f87171"
            pbv_disp = f"{pbv_raw:.1f}x" if pbv_raw < 1000 else ">1000x"
            pbv_str = f"<strong style='color:{pbv_col};'>{pbv_disp}{pbv_label}</strong>"
        elif pbv_raw < 0: pbv_str = "<strong style='color:#f87171;'>Defisit Ekuitas</strong>"
        else: pbv_str = "<strong style='color:#94a3b8;'>N/A</strong>"

        if roe_raw != 0 and not pd.isna(roe_raw):
            roe_pct = roe_raw * 100
            if roe_pct >= 15: roe_label, roe_col = " (Sgt Bagus)", "#4ade80"
            elif roe_pct >= 5: roe_label, roe_col = " (Wajar)", "#fbbf24"
            else: roe_label, roe_col = " (Jelek)", "#f87171"
            roe_disp = f"{roe_pct:.1f}%" if abs(roe_pct) < 1000 else ">1000%"
            roe_str = f"<strong style='color:{roe_col};'>{roe_disp}{roe_label}</strong>"
        else: roe_str = "<strong style='color:#94a3b8;'>N/A</strong>"

        harga_wajar = 0
        if eps_raw > 0 and pbv_raw > 0:
            bvps_calc = latest_price / pbv_raw
            bvps_info = safe_num(info.get('bookValue', bvps_calc))
            if bvps_info > 0:
                harga_wajar = math.sqrt(22.5 * eps_raw * bvps_info)
        
        if harga_wajar > 0:
            margin = ((harga_wajar - latest_price) / latest_price) * 100
            if margin > 10:
                hw_str = f"<strong style='color:#4ade80;'>Rp{harga_wajar:,.0f} (Diskon {margin:.0f}%)</strong>"
            elif margin < -10:
                hw_str = f"<strong style='color:#f87171;'>Rp{harga_wajar:,.0f} (Overvalue)</strong>"
            else:
                hw_str = f"<strong style='color:#fbbf24;'>Rp{harga_wajar:,.0f} (Harga Pas)</strong>"
        else:
            hw_str = "<strong style='color:#94a3b8;'>N/A (Data EPS/PBV Kosong)</strong>"

        f_score = sum([pe_raw>0 and pe_raw<25, pbv_raw>0 and pbv_raw<4, roe_raw>0.05])
        stat_funda, funda_bg = ("SEHAT & LAYAK", "rgba(74, 222, 128, 0.15)") if f_score >= 2 else ("BERISIKO/MAHAL", "rgba(248, 113, 113, 0.15)")
        if pe_raw <= 0 and pbv_raw <= 0: stat_funda, funda_bg = "MURNI TEKNIKAL", "rgba(251, 191, 36, 0.15)"
        
        if rsi_val >= 70: stat_tech, tech_bg = "AWAS PUCUK (Rawan)", "rgba(248, 113, 113, 0.15)"
        elif rsi_val <= 30: stat_tech, tech_bg = "Oversold (Area Pantul)", "rgba(74, 222, 128, 0.15)"
        else: stat_tech, tech_bg = "Konsolidasi (Wajar)", "rgba(251, 191, 36, 0.15)"

        return {
            'price': latest_price, 'change': change_pct, 'name': company_name, 'res': res_terdekat, 'sup': sup_terdekat, 'ts': trailing_stop,
            'sector': sector, 'industry': industry, 'fibo_stat': fibo_stat, 'fibo_score': fibo_score, 'trend': mtf_status, 'trend_col': trend_col, 
            'rsi_val': safe_num(rsi_val), 'macd_str': macd_str, 'vpa_stat': vpa_stat, 'vpa_score': vpa_score, 'bb_stat': bb_stat, 'bb_score': bb_score, 
            'mtf_score': mtf_score, 'pe_str': pe_str, 'pbv_str': pbv_str, 'roe_str': roe_str, 'eps_str': f"Rp{eps_raw:,.0f}" if eps_raw>0 else "N/A", 
            'hw_str': hw_str, 'turnover_str': turnover_str,
            'stat_funda': stat_funda, 'funda_bg': funda_bg, 'stat_tech': stat_tech, 'tech_bg': tech_bg, 
            'stat_flow': "Akumulasi Masif" if bandar_score==3 else ("Distribusi" if bandar_score==0 else "Market Mixed"), 
            'flow_bg': "rgba(74, 222, 128, 0.15)" if bandar_score==3 else ("rgba(248, 113, 113, 0.15)" if bandar_score==0 else "rgba(251, 191, 36, 0.15)"),
            'mc_str': f"{safe_num(info.get('marketCap')) / 1e12:.2f} T" if safe_num(info.get('marketCap'))>0 else "N/A", 
            'ara_price': ara_price, 'arb_price': arb_price, 
            'auto_bandar': auto_bandar, 'bandar_color': bandar_color, 'bandar_score': bandar_score, 'div_warning': div_warning, 
            'fibo_100': swing_high, 'fibo_0': swing_low, 'fibo_618': fibo_618, 'fibo_500': fibo_500, 'fibo_382': fibo_382,
            'candle_pattern': candle_pattern, 'candle_color': candle_color, 'cam_h4': cam_h4, 'cam_h3': cam_h3, 'cam_c': cam_C_prev, 'cam_l3': cam_l3, 'cam_l4': cam_l4,
            'liq_stat': liq_stat, 'liq_col': liq_col
        }
    except Exception as e: return {"error": str(e)}

data = get_stock_data(ticker_yf, interval=yf_interval)
if data is None or isinstance(data, dict) and "error" in data:
    st.error(f"❌ Terjadi kesalahan: Data historis mungkin tidak tersedia di server YFinance.")
    st.stop()

p_val = safe_int(data.get('price'))
rsi_display = safe_num(data.get('rsi_val', 50))

# --- DYNAMIC EXECUTION LOGIC ---
cam_h3_val = safe_int(data.get('cam_h3', 0))
cam_l3_val = safe_int(data.get('cam_l3', 0))
cam_l4_val = safe_int(data.get('cam_l4', 0))
res_klasik = safe_int(data.get('res'))
sup_klasik = safe_int(data.get('sup'))

if is_scalping and cam_h3_val > 0:
    target_tp = cam_h3_val       
    target_sl = cam_l4_val       
    antre_ideal = cam_l3_val     
    mode_label = " (Mode Scalping)"
else:
    target_tp = res_klasik       
    target_sl = sup_klasik       
    antre_ideal = sup_klasik
    mode_label = " (Mode Swing)"

if target_tp <= p_val: target_tp = int(p_val * 1.05)
if target_sl >= p_val: target_sl = int(p_val * 0.95)

score = 0
if data.get('change', 0) > 0: score += 2
score += data.get('mtf_score', 0) + data.get('bandar_score', 0) + data.get('fibo_score', 0) + data.get('vpa_score', 0) + data.get('bb_score', 0)
if "NET BUY" in status_asing: score += 2            
elif "MIXED" in asing_label: score += 1
if rsi_display < 70: score += 2
if data.get('candle_color') == "#4ade80": score += 1 

if score >= 12: win_rate, wr_color = "90% (Sangat Tinggi)", "#4ade80"
elif score >= 8: win_rate, wr_color = "70% (Tinggi)", "#4ade80"
elif score >= 5: win_rate, wr_color = "50% (Spekulatif)", "#fbbf24"
else: win_rate, wr_color = "< 30% (Risiko Bahaya)", "#f87171"

risk_pct = float(risiko_input.split('%')[0]) / 100
max_loss_rp = modal_input * risk_pct
risk_per_share = p_val - target_sl
if risk_per_share <= 0: risk_per_share = p_val * 0.02 

max_lot = int((max_loss_rp / risk_per_share) / 100) if pd.notna(max_loss_rp / risk_per_share) else 0
if max_lot < 1: max_lot = 0
rr_ratio = round((target_tp - p_val) / risk_per_share, 1) if risk_per_share > 0 else 0

# --- SAFETY LOCK ALARMS ---
warnings_list = []
if data.get('div_warning'): warnings_list.append("⚠️ AWAS DIVIDEND TRAP!")
if data.get('bandar_score') == 0: warnings_list.append("🩸 BANDAR DISTRIBUSI (AWAS GUYURAN)")
if rsi_display >= 75: warnings_list.append("🔥 RSI OVERBOUGHT (RAWAN PUCUK)")
if data.get('stat_funda') == "MURNI TEKNIKAL" or data.get('liq_stat') == "Sepi (Awas Guyuran)": warnings_list.append("🎲 SAHAM GORENGAN / SEPI (HIGH RISK)")
if data.get('candle_color') == "#f87171": warnings_list.append("🐻 POLA BEARISH (HARGA MAU TURUN)")

warning_html = ""
if warnings_list:
    warn_str = "<br>".join(warnings_list)
    warning_html = f"<div style='background:rgba(248,113,113,0.15); border:2px solid #f87171; color:#f87171; padding:10px; border-radius:8px; font-size:1rem; font-weight:900; text-align:center; margin-bottom:12px; line-height: 1.5; animation: blinker 1.5s linear infinite; box-shadow: 0 0 10px rgba(248,113,113,0.3);'>{warn_str}</div>"

if rsi_display >= 85: 
    entry_val, border_glow, accent_color = f"<span style='color:#f87171; font-weight:bold;'>⚠️ JANGAN HK (Pucuk)</span>", "0 0 20px rgba(248, 113, 113, 0.6)", "#f87171" 
elif rr_ratio < 0.5 and score >= 8: 
    entry_val, border_glow, accent_color = f"<span style='color:#fbbf24; font-weight:bold;'>⚠ ANTRE (Rp{antre_ideal})</span>", "0 0 20px rgba(251, 191, 36, 0.6)", "#fbbf24" 
elif score >= 8: 
    if warnings_list:
        entry_val, border_glow, accent_color = f"<span style='color:#fbbf24; font-weight:bold;'>Rp{p_val} (HAJAR TAPI WASPADA)</span>", "0 0 20px rgba(251, 191, 36, 0.6)", "#fbbf24"
    else:
        bull_txt = " (Pola Bullish!)" if data.get('candle_color') == "#4ade80" else " (HAJAR)"
        entry_val, border_glow, accent_color = f"<span style='color:#4ade80; font-weight:bold;'>Rp{p_val}{bull_txt}</span>", "0 0 20px rgba(74, 222, 128, 0.6)", "#4ade80" 
else: 
    entry_val, border_glow, accent_color = "<span style='color:#fbbf24; font-weight:bold;'>WAIT / PANTAU</span>", "0 0 20px rgba(251, 191, 36, 0.6)", "#fbbf24" 

# ==========================================
# --- 1. HEADER DASHBOARD ---
# ==========================================
st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:10px;'>
    <div style='flex:1; min-width:250px;'>
        <div style="display: flex; align-items: center; gap: 8px;"><img src="https://assets.parqet.com/logos/symbol/{ticker_input}.JK?format=png" width="40" height="40" style="border-radius: 8px; background: white; padding: 2px;" onerror="this.style.display='none'"><div style='color:#f3f4f6; font-size: clamp(1.5rem, 3vw, 2.5rem); font-weight: 900; line-height: 1;'>{ticker_input}</div></div>
        <div style='color:#94a3b8; font-size:0.85rem; font-weight:bold; margin-top:2px;'>{data.get('name', '')}</div>
        <div style='font-size: 0.75rem; color: #64748b; margin-top: 4px; border-left: 2px solid #3b82f6; padding-left: 6px;'>
            Sector: <span style='color:#e2e8f0; font-weight:600;'>{data.get('sector', 'N/A')}</span><br>Industry: <span style='color:#e2e8f0; font-weight:600;'>{data.get('industry', 'N/A')}</span>
        </div>
    </div>
    <div style='flex:1; min-width:150px; text-align:center;'>
        <div style='color:#fbbf24; font-size: 2rem; font-weight: 900;'>🌟 {score}.0<span style='font-size:1rem; color:#64748b;'>/15</span></div>
        <div style='font-size: 0.8rem; color:#94a3b8;'>Win: <strong style='color:{wr_color};'>{win_rate}</strong></div>
    </div>
    <div style='flex:1; min-width:150px; text-align:right;'>
        <div style='color:#94a3b8; font-size:0.75rem; font-weight:bold;'>HARGA SAAT INI</div>
        <div style='color:#f3f4f6; font-size: clamp(1.5rem, 3vw, 2.2rem); font-weight: 900;'>Rp{p_val}</div>
        <div style='background: rgba({ '74, 222, 128' if data.get('change', 0) >= 0 else '248, 113, 113' }, 0.15); padding: 2px 6px; border-radius: 4px; color: {'#4ade80' if data.get('change', 0) >= 0 else '#f87171'}; font-size: 0.85rem; font-weight: bold; border: 1px solid {'#4ade80' if data.get('change', 0) >= 0 else '#f87171'}; display: inline-block;'>
            {('▲' if data.get('change', 0) >= 0 else '▼')} {data.get('change', 0):.2f}%
        </div>
    </div>
</div>""", unsafe_allow_html=True)

rr_bg = "linear-gradient(90deg, #1e3a8a, #3b82f6)" if rr_ratio >= 1.5 else ("linear-gradient(90deg, #991b1b, #ef4444)" if rr_ratio < 0.5 else "linear-gradient(90deg, #78350f, #d97706)")

st.markdown(f"""
<div style='background: linear-gradient(145deg, #0f172a, #020617); border: 2px solid {accent_color}; padding: 20px; border-radius: 12px; box-shadow: {border_glow}; position: relative; overflow: hidden; margin-top: 15px; margin-bottom: 15px; width: 100%;'>
<div style='position: absolute; top: 0; left: 0; width: 100%; height: 5px; background: {accent_color}; box-shadow: 0 0 15px {accent_color};'></div>
<div style='color:#e5e7eb; font-size:1.2rem; font-weight:900; letter-spacing:2px; margin-bottom: 15px; text-align: center; text-transform: uppercase;'>🎯 FINAL EXECUTION {mode_label.upper()} 🎯</div>
{warning_html}
<div style='display:flex; flex-direction: column; gap: 10px; margin-top:10px;'>
<div style='display:flex; justify-content: space-between; align-items:center; font-size: 1.1rem; border-bottom: 1px dashed #334151; padding-bottom: 6px;'><span style='color:#94a3b8; font-weight:bold;'>Entry Point</span> <span style='text-align: right; font-size:1.2rem;'>{entry_val}</span></div>
<div style='display:flex; justify-content: space-between; align-items:center; font-size: 1.1rem; border-bottom: 1px dashed #334151; padding-bottom: 6px;'><span style='color:#94a3b8; font-weight:bold;'>Take Profit Target</span> <span style='color:#4ade80; font-weight:900; font-size:1.2rem;'>Rp{target_tp}</span></div>
<div style='display:flex; justify-content: space-between; align-items:center; font-size: 1.1rem; border-bottom: 1px dashed #334151; padding-bottom: 6px;'><span style='color:#94a3b8; font-weight:bold;'>Stop Loss Limit</span> <span style='color:#f87171; font-weight:900; font-size:1.2rem;'>Rp{target_sl}</span></div>
<div style='display:flex; justify-content: space-between; align-items:center; font-size: 1.1rem; border-bottom: 1px dashed #334151; padding-bottom: 6px;'><span style='color:#94a3b8; font-weight:bold;'>Maks Beli Aman</span> <span style='color:#4ade80; font-weight:900; font-size:1.2rem;'>{max_lot} LOT</span></div>
</div>
<div style='background: {rr_bg}; color:white; padding:10px; border-radius:6px; text-align:center; font-weight:900; font-size:1.1rem; margin-top: 15px; letter-spacing: 1px;'>⚖ RISK & REWARD RATIO = 1 : {rr_ratio}</div>
</div>""", unsafe_allow_html=True)

# ==========================================
# --- 2. RADAR FIBO & CAMARILLA ---
# ==========================================
st.markdown(f"""
<div style='background: linear-gradient(90deg, #1e3a8a, #0f172a); border: 1px solid #3b82f6; padding: 10px; border-radius: 8px; margin-top: 12px; margin-bottom: 8px; display: flex; flex-wrap: wrap; gap: 5px; justify-content: space-around; align-items: center;'>
    <div style='color:#93c5fd; font-weight:bold; font-size:0.8rem; text-transform:uppercase; text-align: center; width: 100%; border-bottom: 1px dashed #334151; padding-bottom: 5px; margin-bottom: 5px;'>🎯 Radar Fibo (Tren Ayunan)</div>
    <div style='text-align:center; flex: 1; min-width: 80px;'><div style='font-size:0.65rem; color:#94a3b8;'>100% (High)</div><strong style='color:#f3f4f6; font-size:0.85rem;'>Rp{safe_int(data.get('fibo_100', 0))}</strong></div>
    <div style='text-align:center; flex: 1; min-width: 80px;'><div style='font-size:0.65rem; color:#4ade80;'>61.8% (Golden)</div><strong style='color:#4ade80; font-size:0.85rem;'>Rp{safe_int(data.get('fibo_618', 0))}</strong></div>
    <div style='text-align:center; flex: 1; min-width: 80px;'><div style='font-size:0.65rem; color:#fbbf24;'>50.0% (Mid)</div><strong style='color:#fbbf24; font-size:0.85rem;'>Rp{safe_int(data.get('fibo_500', 0))}</strong></div>
    <div style='text-align:center; flex: 1; min-width: 80px;'><div style='font-size:0.65rem; color:#f87171;'>38.2% (Support)</div><strong style='color:#f87171; font-size:0.85rem;'>Rp{safe_int(data.get('fibo_382', 0))}</strong></div>
    <div style='text-align:center; flex: 1; min-width: 80px;'><div style='font-size:0.65rem; color:#94a3b8;'>0% (Low)</div><strong style='color:#f3f4f6; font-size:0.85rem;'>Rp{safe_int(data.get('fibo_0', 0))}</strong></div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style='background: linear-gradient(90deg, #3730a3, #0f172a); border: 1px solid #6366f1; padding: 10px; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.4); display: flex; flex-wrap: wrap; gap: 5px; justify-content: space-around; align-items: center;'>
    <div style='color:#a5b4fc; font-weight:bold; font-size:0.8rem; text-transform:uppercase; text-align: center; width: 100%; border-bottom: 1px dashed #4338ca; padding-bottom: 5px; margin-bottom: 5px;'>🤖 Auto-Pivot Camarilla (Khusus Copet Scalping)</div>
    <div style='text-align:center; flex: 1; min-width: 75px;'><div style='font-size:0.65rem; color:#4ade80;'>H4 (Breakout)</div><strong style='color:#4ade80; font-size:0.85rem;'>Rp{safe_int(data.get('cam_h4', 0))}</strong></div>
    <div style='text-align:center; flex: 1; min-width: 75px;'><div style='font-size:0.65rem; color:#f87171;'>H3 (Resisten)</div><strong style='color:#f87171; font-size:0.85rem;'>Rp{safe_int(data.get('cam_h3', 0))}</strong></div>
    <div style='text-align:center; flex: 1; min-width: 75px; border-left: 1px solid #4338ca; border-right: 1px solid #4338ca;'><div style='font-size:0.65rem; color:#f3f4f6;'>Close Kemarin</div><strong style='color:#f3f4f6; font-size:0.85rem;'>Rp{safe_int(data.get('cam_c', 0))}</strong></div>
    <div style='text-align:center; flex: 1; min-width: 75px;'><div style='font-size:0.65rem; color:#4ade80;'>L3 (Support)</div><strong style='color:#4ade80; font-size:0.85rem;'>Rp{safe_int(data.get('cam_l3', 0))}</strong></div>
    <div style='text-align:center; flex: 1; min-width: 75px;'><div style='font-size:0.65rem; color:#f87171;'>L4 (Breakdown)</div><strong style='color:#f87171; font-size:0.85rem;'>Rp{safe_int(data.get('cam_l4', 0))}</strong></div>
</div>
""", unsafe_allow_html=True)

components.html(f"""
<div style="border-radius: 10px; border: 1px solid #334151; overflow: hidden; background: #0f172a; margin-bottom: 10px; height: 480px;">
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
        "studies": [
            "Volume@tv-basicstudies",
            "BB@tv-basicstudies"
        ]
    }});
    </script>
</div>
""", height=490)

# ==========================================
# --- 3. KOTAK SENJATA UTAMA (RESPONSIVE) ---
# ==========================================
st.markdown(f"""<div style='display:flex; flex-wrap: wrap; justify-content:space-around; gap: 10px; background:#0f172a; border: 1px solid #334151; padding:10px; border-radius:8px; margin-bottom: 10px;'>
    <div style='text-align:center; flex: 1; min-width: 120px;'>🚀 <span style='color:#94a3b8; font-size:0.85rem;'>Batas ARA:</span> <strong style='color:#4ade80; font-size:1rem;'>Rp{data.get('ara_price', 0)}</strong></div>
    <div style='text-align:center; flex: 1; min-width: 120px;'>🩸 <span style='color:#94a3b8; font-size:0.85rem;'>Batas ARB:</span> <strong style='color:#f87171; font-size:1rem;'>Rp{data.get('arb_price', 0)}</strong></div></div>""", unsafe_allow_html=True)

# MIN HEIGHT DITAMBAH JADI 280px AGAR SELALU PRESISI
def render_luxury_box(title, content, badge_text, badge_style):
    return f"""<div style='height: 100%; min-height: 280px; display: flex; flex-direction: column; justify-content: space-between;'>
    <div>
        <div style='font-size: 0.95rem; font-weight: 900; color:#38bdf8; letter-spacing: 0.5px;'>{title}</div>
        <hr style='margin: 6px 0; border-color:#334151;'>
        <div style='padding: 2px 0; display:flex; flex-direction: column; gap: 8px;'>{content}</div>
    </div>
    <div style='background: {badge_style}; border-radius: 6px; padding: 6px; text-align: center; margin-top: 15px; font-weight: 800; font-size: 0.8rem; letter-spacing: 0.5px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
        {badge_text}
    </div>
</div>"""

# --- SINKRONISASI JUMLAH BARIS (6 BARIS + 1 GARIS TIAP KOTAK) ---

c1 = f"""<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>Market Cap:</span> <strong style='color:#f3f4f6;'>{data.get('mc_str', 'N/A')}</strong></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>PER (Valuasi):</span> <div style='text-align:right;'>{data.get('pe_str', 'N/A')}</div></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>PBV (Aset):</span> <div style='text-align:right;'>{data.get('pbv_str', 'N/A')}</div></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>ROE (Kinerja):</span> <div style='text-align:right;'>{data.get('roe_str', 'N/A')}</div></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>EPS (Laba):</span> <strong style='color:#f3f4f6;'>{data.get('eps_str', 'N/A')}</strong></div>
<hr style='margin: 4px 0; border: 0.5px dashed #38bdf8;'>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#38bdf8; font-weight:bold;'>Harga Wajar:</span> <div style='text-align:right;'>{data.get('hw_str', 'N/A')}</div></div>"""
b1 = render_luxury_box("💼 1. FUNDAMENTAL", c1, f"STATUS: {data.get('stat_funda', 'N/A')}", data.get('funda_bg', ''))

c2 = f"""<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8; flex-shrink: 0;'>Pola Mata Elang:</span> <strong style='color:{data.get('candle_color', '#fff')}; text-align:right;'>{data.get('candle_pattern', 'N/A')}</strong></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>Tren Mayor:</span> <strong style='color:{data.get('trend_col', '#fff')}; text-align:right;'>{data.get('trend', 'N/A')}</strong></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8; flex-shrink: 0;'>Posisi Fibo:</span> <strong style='color:#f3f4f6; text-align:right;'>{data.get('fibo_stat', 'N/A')}</strong></div>
<hr style='margin: 4px 0; border: 0.5px dashed #334151;'>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>RSI (14):</span> <strong style='color:{'#4ade80' if rsi_display<=30 else ('#f87171' if rsi_display>=70 else '#f3f4f6')}; text-align:right;'>{rsi_display:.1f}</strong></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>Sinyal MACD:</span> <div>{data.get('macd_str', 'N/A')}</div></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>Bollinger B.:</span> <strong style='color:#4ade80; text-align:right;'>{data.get('bb_stat', 'N/A')}</strong></div>"""
b2 = render_luxury_box("📈 2. TEKNIKAL & AI", c2, f"KESIMPULAN: {data.get('stat_tech', 'N/A')}", data.get('tech_bg', ''))

c3 = f"""<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8; flex-shrink: 0;'>AI Bandar:</span> <strong style='color:{data.get('bandar_color', '#fff')}; text-align:right;'>{data.get('auto_bandar', 'N/A')}</strong></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8; flex-shrink: 0;'>Asing Flow:</span> <div>{asing_label}</div></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>Avg Transaksi:</span> <strong style='color:#f3f4f6; text-align:right;'>{data.get('turnover_str', 'N/A')}</strong></div>
<hr style='margin: 4px 0; border: 0.5px dashed #334151;'>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>Volume (VPA):</span> <strong style='color:#4ade80; text-align:right;'>{data.get('vpa_stat', 'N/A')}</strong></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>Volatilitas ATR:</span> <strong style='color:#4ade80; text-align:right;'>Terpantau</strong></div>
<div style='display:flex; justify-content: space-between; align-items:center;'><span style='color:#94a3b8;'>Likuiditas (Antrean):</span> <strong style='color:{data.get('liq_col', '#fff')}; text-align:right;'>{data.get('liq_stat', 'N/A')}</strong></div>"""
b3 = render_luxury_box("🦅 3. BANDARMOLOGY", c3, f"FLOW: {data.get('stat_flow', 'N/A')}", data.get('flow_bg', ''))

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
    with col_sc1: f_bandar = st.selectbox("Filter Bandar Flow:", ["Semua", "Akumulasi AI", "Netral / Sepi", "Distribusi Besar"])
    with col_sc2: f_asing = st.selectbox("Filter Asing Flow:", ["Semua", "Asing NET BUY (Masuk Besar)", "Asing Netral / Mixed", "Asing NET SELL (Keluar)"])
    with col_sc3: f_tren = st.selectbox("Fase Tren Saham:", ["Semua", "Uptrend (Markup)", "Sideways", "Downtrend (Markdown)"])
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
                        hasil_scan.append({"Ticker": s_data["Ticker"], "Harga": s_data["Harga"], "Bandar_Flow": s_data["Bandar_Flow"], "Asing_Flow": status_asing, "Fase": s_data["Fase"], "RSI": s_data["RSI"]})
            except Exception: pass
            progress_bar.progress((idx + 1) / len(tickers_to_scan))
        progress_bar.empty()
        
        if hasil_scan:
            st.success(f"Ditemukan {len(hasil_scan)} emiten yang sesuai dengan kriteria saringan! 🔥")
            st.dataframe(pd.DataFrame(hasil_scan), use_container_width=True)
        else:
            st.warning("Tidak ada emiten yang lolos filter.")

with tab_backtest:
    st.markdown("#### ⏳ Mesin Waktu Simulator (Backtest 1 Tahun)")
    if st.button(f"🚀 Mulai Simulasi {ticker_input}"):
        with st.spinner('Menghitung data masa lalu...'):
            try:
                bt_data = yf.Ticker(ticker_yf).history(period="1y", interval="1d")
                if len(bt_data) > 50:
                    delta = bt_data['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    bt_data['RSI'] = 100 - (100 / (1 + (gain/loss)))
                    trades, in_position, buy_price = [], False, 0
                    for i in range(20, len(bt_data)):
                        row = bt_data.iloc[i]
                        if not in_position and row['RSI'] < 40:
                            in_position, buy_price = True, row['Close']
                        elif in_position and (row['RSI'] > 70 or row['Close'] < buy_price * 0.95): 
                            in_position = False
                            trades.append(((row['Close'] - buy_price) / buy_price) * 100)
                    if trades:
                        win_rate_bt = (len([t for t in trades if t > 0]) / len(trades)) * 100
                        st.markdown(f"""<div style='display:flex; flex-wrap: wrap; gap:15px; margin-top:20px; margin-bottom: 20px;'>
                           <div style='flex:1; min-width: 150px; background:#0f172a; padding:20px; border-radius:10px; border:1px solid #334151; text-align:center;'><div style='color:#94a3b8; font-size:0.9rem;'>Total Trade Eksekusi</div><div style='color:#f3f4f6; font-size:2rem; font-weight:bold;'>{len(trades)}x</div></div>
                           <div style='flex:1; min-width: 150px; background:#0f172a; padding:20px; border-radius:10px; border:1px solid #334151; text-align:center;'><div style='color:#94a3b8; font-size:0.9rem;'>Akurasi Menang (Win Rate)</div><div style='color:#4ade80; font-size:2rem; font-weight:bold;'>{win_rate_bt:.1f}%</div></div>
                           <div style='flex:1; min-width: 150px; background:#0f172a; padding:20px; border-radius:10px; border:1px solid #334151; text-align:center;'><div style='color:#94a3b8; font-size:0.9rem;'>Total Akumulasi Cuan</div><div style='color:#38bdf8; font-size:2rem; font-weight:bold;'>{'+' if sum(trades) > 0 else ''}{sum(trades):.2f}%</div></div>
                        </div>""", unsafe_allow_html=True)
                    else: st.warning("Tidak ada sinyal beli tervalidasi 1 tahun terakhir.")
                else: st.error("Data saham tidak cukup untuk simulasi.")
            except Exception as e: st.error(f"Gagal melakukan simulasi: {str(e)}")
