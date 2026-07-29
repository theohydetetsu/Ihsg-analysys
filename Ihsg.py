import streamlit as st
import yfinance as yf
import datetime
import pandas as pd
import streamlit.components.v1 as components

# ==========================================
# --- KONFIGURASI HALAMAN ---
# ==========================================
st.set_page_config(page_title="Dashboard Analisis Teknikal", layout="wide")

st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# --- SIDEBAR: INPUT DATA & BANDARMOLOGY ---
# ==========================================
st.sidebar.markdown("### 🔍 1. Pilih Emiten")
ticker_input = st.sidebar.text_input("Ketik Kode Saham & Enter:", "BBCA").upper().strip()
ticker_yf = f"{ticker_input}.JK"
ticker_tv = f"IDX:{ticker_input}"

st.sidebar.markdown("---")
st.sidebar.markdown("### 🕵️‍♂️ 2. Input Bandarmology")
st.sidebar.caption("Karena data Broker tidak tersedia publik, Anda bisa memasukkan hasil pantauan bandar (Broker Summary) Anda secara manual di sini untuk dikalkulasi oleh sistem.")
# Input Manual Bandarmology
status_bandar = st.sidebar.selectbox(
    "Bagaimana pergerakan Bandar hari ini?", 
    ["Akumulasi (Net Buy)", "Netral / Sepi", "Distribusi (Net Sell)"]
)


# ==========================================
# --- FUNGSI AMBIL DATA & KALKULATOR ---
# ==========================================
@st.cache_data(ttl=300)
def get_stock_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="6mo")
        if hist.empty or len(hist) < 30: return None
            
        latest_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change_pct = ((latest_price - prev_price) / prev_price) * 100
        info = stock.info
        dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
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
        
        return {
            'price': latest_price, 'change': change_pct, 'div': dividend_yield, 'name': company_name,
            'ema_cross': ema_cross, 'trend': trend_status, 'rsi_val': rsi_val, 'rsi_status': rsi_status,
            'res': res_terdekat, 'sup': sup_terdekat, 'shares': shares
        }
    except:
        return None

data = get_stock_data(ticker_yf)
if data is None:
    st.error(f"❌ Saham **{ticker_input}** tidak ditemukan. Pastikan mengetik kode dengan benar di Sidebar.")
    st.stop()


# ==========================================
# --- ALGORITMA PENILAIAN HIBRIDA (SCORE) ---
# ==========================================
# Skor Maksimal 10. Dibagi: Trend (Max 4), RSI (Max 2), Bandar (Max 4)
score = 0
if data['trend'] == "Bullish": score += 4
if data['rsi_status'] == "Netral": score += 2
elif data['rsi_status'] == "Oversold": score += 2

if "Akumulasi" in status_bandar: score += 4
elif "Netral" in status_bandar: score += 2


# ==========================================
# --- 1. HEADER DASHBOARD ---
# ==========================================
arrow = "▼" if data['change'] < 0 else "▲"
color = "#dc2626" if data['change'] < 0 else "#16a34a"
today_date = datetime.datetime.now().strftime("%d %B %Y")

col_h1, col_h2, col_h3 = st.columns([2, 1.2, 1.3])

with col_h1:
    st.markdown(f"📊 **ANALISIS TEKNIKAL**")
    st.markdown(f"# **{ticker_input}**")
    st.markdown(f"**{data['name']}**")
    st.caption("AI + Teknikal + Manual Bandarmology")
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
    <div style="border-radius: 8px; border: 1px solid #e5e7eb; overflow: hidden; background: white;">
        <div class="tradingview-widget-container" style="height: 400px; width: 100%;">
          <div id="tradingview_chart" style="height: 100%; width: 100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "autosize": true,
            "symbol": "{ticker_tv}",
            "interval": "D",
            "timezone": "Asia/Jakarta",
            "theme": "light",
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
        st.markdown("💰 **TRADE PLAN (Sistem Sinyal)**")
        if score >= 8:
            st.markdown(f"🟢 **Entry:** Beli bertahap di Rp{int(data['price'])}")
        elif score >= 5:
            st.markdown(f"🟡 **Entry:** Tunggu re-test Support di Rp{int(data['sup'])}")
        else:
            st.markdown("🔴 **Entry:** JANGAN BELI SEKARANG")
            
        st.markdown(f"🔴 **Stop Loss:** Jika break Rp{int(data['sup'])}")
        st.divider()
        st.markdown("🎯 **TARGET HARGA**")
        st.markdown(f"🥇 **Target 1:** Rp{int(data['res'])}")
        
        reward = int(data['res']) - int(data['price'])
        risk = int(data['price']) - int(data['sup'])
        if risk > 0 and reward > 0:
            rr_ratio = round(reward / risk, 1)
            st.info(f"⚖️ Risk : Reward = 1 : {rr_ratio}")
        else:
            st.info("⚖️ Risk : Reward = Sulit Dihitung")


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
        st.markdown("🏛️ **BANDARMOLOGY (MANUAL)**")
        st.caption("Hasil Input Sidebar Anda:")
        if "Akumulasi" in status_bandar:
            st.success(f"✔️ Bandar **{status_bandar}**")
        elif "Distribusi" in status_bandar:
            st.error(f"❌ Bandar **{status_bandar}**")
        else:
            st.warning(f"➖ Bandar **{status_bandar}**")

with col_b2:
    with st.container(border=True):
        st.markdown("↕️ **SUPPORT & RESISTANCE**")
        col_s1, col_s2 = st.columns(2)
        col_s1.markdown(f"🟢 **SUPPORT**\n- **Rp{int(data['sup'])}**")
        col_s2.markdown(f"🔴 **RESIST**\n- **Rp{int(data['res'])}**")
    
    with st.container(border=True):
        st.markdown("⭐ **KESIMPULAN SINYAL BESOK**")
        
        # Logika Gabungan Teknikal + Bandar
        if data['trend'] == "Bullish" and "Akumulasi" in status_bandar:
            st.info(f"🔥 **{ticker_input} SANGAT POTENSIAL**")
            st.markdown("Teknikal Naik + Bandar Akumulasi. Beli saat Open atau koreksi wajar.")
        elif data['trend'] == "Bullish" and "Distribusi" in status_bandar:
            st.warning(f"⚠️ **HATI-HATI GUYURAN PADA {ticker_input}**")
            st.markdown("Trend Naik TAPI Bandar Distribusi. Trading cepat saja / rawan jebol.")
        elif data['trend'] == "Bearish" and "Akumulasi" in status_bandar:
            st.success(f"🎣 **POTENSI REVERSAL {ticker_input}**")
            st.markdown("Harga turun TAPI Bandar Akumulasi diam-diam. Boleh mulai cicil beli di support.")
        else:
            st.error(f"💀 **HINDARI {ticker_input} SEMENTARA**")
            st.markdown("Trend Turun & Bandar Distribusi. Risiko nyangkut tinggi.")

with col_b3:
    with st.container(border=True):
        st.markdown("📊 **INDIKATOR TEKNIKAL**")
        st.markdown(f"📌 **EMA Crossover:**\n{data['ema_cross']}")
        st.markdown(f"📌 **RSI (14):**\n{data['rsi_val']:.1f} - **{data['rsi_status']}**")
    
    with st.container(border=True):
        st.markdown("👥 **INFO PERUSAHAAN**")
        st.caption("JUMLAH SAHAM BEREDAR")
        if data['shares'] != "N/A":
            shares_fmt = f"{data['shares'] / 1e9:.2f} Miliar Lembar"
        else:
            shares_fmt = "Tidak diketahui"
        st.markdown(f"### **{shares_fmt}**")


# ==========================================
# --- 4. PUSAT DATA PASAR (SCANNER) ---
# ==========================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📊 Pusat Data Pasar (IHSG)")
tab_movers, tab_screener = st.tabs(["🔥 Top Movers & Trending", "🔎 Advanced Stock Scanner"])

with tab_movers:
    components.html("""
    <div class="tradingview-widget-container" style="height: 500px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-hotlists.js" async>
      { "colorTheme": "light", "dateRange": "12M", "exchange": "IDX", "showChart": true, "locale": "id", "width": "100%", "height": "100%" }
      </script>
    </div>
    """, height=500)

with tab_screener:
    components.html("""
    <div class="tradingview-widget-container" style="height: 600px; width: 100%;">
      <div class="tradingview-widget-container__widget" style="height: 100%; width: 100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
      { "width": "100%", "height": "100%", "defaultColumn": "overview", "defaultScreen": "general", "market": "indonesia", "showToolbar": true, "colorTheme": "light", "locale": "id" }
      </script>
    </div>
    """, height=600)
