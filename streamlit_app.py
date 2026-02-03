import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from newsapi import NewsApiClient
from datetime import datetime, timedelta

# --- 1. 設定 ---
st.set_page_config(page_title="Pro Investor Dashboard v10", layout="wide")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
except:
    st.error("Secrets (SupabaseまたはNewsAPIのキー) が設定されていません。")
    st.stop()

# クライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# ==============================================================================
# 2. 銘柄データマスター (約350銘柄 固定リスト)
# ==============================================================================

# --- 債券・金利 (Bonds & Yields) ---
BONDS = [
    {"C": "📉 Bonds", "T": "^TNX", "N": "US 10Y Yield (米国10年債)"},
    {"C": "📉 Bonds", "T": "^FVX", "N": "US 5Y Yield (米国5年債)"},
    {"C": "📉 Bonds", "T": "^IRX", "N": "US 3 Month Bill"},
    {"C": "📉 Bonds", "T": "^TYX", "N": "US 30Y Yield (米国30年債)"},
    {"C": "📉 Bonds", "T": "TLT", "N": "iShares 20+ Year Treasury Bond"},
    {"C": "📉 Bonds", "T": "IEF", "N": "iShares 7-10 Year Treasury Bond"},
    {"C": "📉 Bonds", "T": "SHY", "N": "iShares 1-3 Year Treasury Bond"},
    {"C": "📉 Bonds", "T": "LQD", "N": "Investment Grade Corporate Bond"},
    {"C": "📉 Bonds", "T": "HYG", "N": "High Yield Corporate Bond"},
    {"C": "📉 Bonds", "T": "JNK", "N": "SPDR Bloomberg High Yield Bond"},
    {"C": "📉 Bonds", "T": "AGG", "N": "Core U.S. Aggregate Bond"},
    {"C": "📉 Bonds", "T": "BND", "N": "Total Bond Market"},
    {"C": "📉 Bonds", "T": "BNDX", "N": "Total International Bond"},
    {"C": "📉 Bonds", "T": "TIP", "N": "TIPS Bond (物価連動国債)"},
]

# --- 為替 (Forex) ---
FOREX = [
    {"C": "💱 Forex", "T": "USDJPY=X", "N": "USD/JPY (ドル円)"},
    {"C": "💱 Forex", "T": "EURJPY=X", "N": "EUR/JPY (ユーロ円)"},
    {"C": "💱 Forex", "T": "GBPJPY=X", "N": "GBP/JPY (ポンド円)"},
    {"C": "💱 Forex", "T": "AUDJPY=X", "N": "AUD/JPY (豪ドル円)"},
    {"C": "💱 Forex", "T": "CHFJPY=X", "N": "CHF/JPY (フラン円)"},
    {"C": "💱 Forex", "T": "EURUSD=X", "N": "EUR/USD (ユーロドル)"},
    {"C": "💱 Forex", "T": "GBPUSD=X", "N": "GBP/USD (ポンドドル)"},
    {"C": "💱 Forex", "T": "AUDUSD=X", "N": "AUD/USD (豪ドル米ドル)"},
    {"C": "💱 Forex", "T": "NZDUSD=X", "N": "NZD/USD (NZドル米ドル)"},
    {"C": "💱 Forex", "T": "USDCAD=X", "N": "USD/CAD (ドルカナダ)"},
    {"C": "💱 Forex", "T": "USDCHF=X", "N": "USD/CHF (ドルフラン)"},
    {"C": "💱 Forex", "T": "CNY=X", "N": "USD/CNY (ドル人民元)"},
    {"C": "💱 Forex", "T": "TRY=X", "N": "USD/TRY (ドルトルコリラ)"},
    {"C": "💱 Forex", "T": "MXN=X", "N": "USD/MXN (ドルメキシコペソ)"},
    {"C": "💱 Forex", "T": "ZAR=X", "N": "USD/ZAR (ドル南アランド)"},
    {"C": "💱 Forex", "T": "DX-Y.NYB", "N": "Dollar Index (ドル指数)"},
]

# --- 米国株: ハイテク・半導体 (US Tech & Semi) ---
US_TECH = [
    {"C": "🇺🇸 Tech/Semi", "T": "AAPL", "N": "Apple"},
    {"C": "🇺🇸 Tech/Semi", "T": "MSFT", "N": "Microsoft"},
    {"C": "🇺🇸 Tech/Semi", "T": "NVDA", "N": "NVIDIA"},
    {"C": "🇺🇸 Tech/Semi", "T": "GOOGL", "N": "Google Alphabet"},
    {"C": "🇺🇸 Tech/Semi", "T": "AMZN", "N": "Amazon"},
    {"C": "🇺🇸 Tech/Semi", "T": "META", "N": "Meta Platforms"},
    {"C": "🇺🇸 Tech/Semi", "T": "TSLA", "N": "Tesla"},
    {"C": "🇺🇸 Tech/Semi", "T": "AVGO", "N": "Broadcom"},
    {"C": "🇺🇸 Tech/Semi", "T": "AMD", "N": "AMD"},
    {"C": "🇺🇸 Tech/Semi", "T": "INTC", "N": "Intel"},
    {"C": "🇺🇸 Tech/Semi", "T": "QCOM", "N": "Qualcomm"},
    {"C": "🇺🇸 Tech/Semi", "T": "TXN", "N": "Texas Instruments"},
    {"C": "🇺🇸 Tech/Semi", "T": "MU", "N": "Micron Technology"},
    {"C": "🇺🇸 Tech/Semi", "T": "AMAT", "N": "Applied Materials"},
    {"C": "🇺🇸 Tech/Semi", "T": "LRCX", "N": "Lam Research"},
    {"C": "🇺🇸 Tech/Semi", "T": "ADI", "N": "Analog Devices"},
    {"C": "🇺🇸 Tech/Semi", "T": "KLAC", "N": "KLA Corp"},
    {"C": "🇺🇸 Tech/Semi", "T": "ASML", "N": "ASML Holding"},
    {"C": "🇺🇸 Tech/Semi", "T": "TSM", "N": "TSMC"},
    {"C": "🇺🇸 Tech/Semi", "T": "ARM", "N": "Arm Holdings"},
    {"C": "🇺🇸 Tech/Semi", "T": "ORCL", "N": "Oracle"},
    {"C": "🇺🇸 Tech/Semi", "T": "CRM", "N": "Salesforce"},
    {"C": "🇺🇸 Tech/Semi", "T": "ADBE", "N": "Adobe"},
    {"C": "🇺🇸 Tech/Semi", "T": "CSCO", "N": "Cisco Systems"},
    {"C": "🇺🇸 Tech/Semi", "T": "IBM", "N": "IBM"},
    {"C": "🇺🇸 Tech/Semi", "T": "NOW", "N": "ServiceNow"},
    {"C": "🇺🇸 Tech/Semi", "T": "INTU", "N": "Intuit"},
    {"C": "🇺🇸 Tech/Semi", "T": "UBER", "N": "Uber Technologies"},
    {"C": "🇺🇸 Tech/Semi", "T": "ABNB", "N": "Airbnb"},
    {"C": "🇺🇸 Tech/Semi", "T": "PANW", "N": "Palo Alto Networks"},
    {"C": "🇺🇸 Tech/Semi", "T": "CRWD", "N": "CrowdStrike"},
    {"C": "🇺🇸 Tech/Semi", "T": "PLTR", "N": "Palantir"},
    {"C": "🇺🇸 Tech/Semi", "T": "SNOW", "N": "Snowflake"},
    {"C": "🇺🇸 Tech/Semi", "T": "SQ", "N": "Block (Square)"},
    {"C": "🇺🇸 Tech/Semi", "T": "PYPL", "N": "PayPal"},
    {"C": "🇺🇸 Tech/Semi", "T": "SHOP", "N": "Shopify"},
    {"C": "🇺🇸 Tech/Semi", "T": "COIN", "N": "Coinbase"},
    {"C": "🇺🇸 Tech/Semi", "T": "HOOD", "N": "Robinhood"},
    {"C": "🇺🇸 Tech/Semi", "T": "RBLX", "N": "Roblox"},
    {"C": "🇺🇸 Tech/Semi", "T": "U", "N": "Unity Software"},
    {"C": "🇺🇸 Tech/Semi", "T": "NET", "N": "Cloudflare"},
]

# --- 米国株: 主要セクター (US Major) ---
US_MAJOR = [
    {"C": "🇺🇸 US Major", "T": "JPM", "N": "JPMorgan Chase"},
    {"C": "🇺🇸 US Major", "T": "BAC", "N": "Bank of America"},
    {"C": "🇺🇸 US Major", "T": "WFC", "N": "Wells Fargo"},
    {"C": "🇺🇸 US Major", "T": "C", "N": "Citigroup"},
    {"C": "🇺🇸 US Major", "T": "GS", "N": "Goldman Sachs"},
    {"C": "🇺🇸 US Major", "T": "MS", "N": "Morgan Stanley"},
    {"C": "🇺🇸 US Major", "T": "BLK", "N": "BlackRock"},
    {"C": "🇺🇸 US Major", "T": "V", "N": "Visa"},
    {"C": "🇺🇸 US Major", "T": "MA", "N": "Mastercard"},
    {"C": "🇺🇸 US Major", "T": "AXP", "N": "American Express"},
    {"C": "🇺🇸 US Major", "T": "BRK-B", "N": "Berkshire Hathaway"},
    {"C": "🇺🇸 US Major", "T": "WMT", "N": "Walmart"},
    {"C": "🇺🇸 US Major", "T": "TGT", "N": "Target"},
    {"C": "🇺🇸 US Major", "T": "COST", "N": "Costco"},
    {"C": "🇺🇸 US Major", "T": "HD", "N": "Home Depot"},
    {"C": "🇺🇸 US Major", "T": "LOW", "N": "Lowe's"},
    {"C": "🇺🇸 US Major", "T": "PG", "N": "Procter & Gamble"},
    {"C": "🇺🇸 US Major", "T": "KO", "N": "Coca-Cola"},
    {"C": "🇺🇸 US Major", "T": "PEP", "N": "PepsiCo"},
    {"C": "🇺🇸 US Major", "T": "MCD", "N": "McDonald's"},
    {"C": "🇺🇸 US Major", "T": "SBUX", "N": "Starbucks"},
    {"C": "🇺🇸 US Major", "T": "NKE", "N": "Nike"},
    {"C": "🇺🇸 US Major", "T": "DIS", "N": "Disney"},
    {"C": "🇺🇸 US Major", "T": "CMCSA", "N": "Comcast"},
    {"C": "🇺🇸 US Major", "T": "NFLX", "N": "Netflix"},
    {"C": "🇺🇸 US Major", "T": "JNJ", "N": "Johnson & Johnson"},
    {"C": "🇺🇸 US Major", "T": "LLY", "N": "Eli Lilly"},
    {"C": "🇺🇸 US Major", "T": "UNH", "N": "UnitedHealth"},
    {"C": "🇺🇸 US Major", "T": "PFE", "N": "Pfizer"},
    {"C": "🇺🇸 US Major", "T": "MRK", "N": "Merck"},
    {"C": "🇺🇸 US Major", "T": "ABBV", "N": "AbbVie"},
    {"C": "🇺🇸 US Major", "T": "CVX", "N": "Chevron"},
    {"C": "🇺🇸 US Major", "T": "XOM", "N": "Exxon Mobil"},
    {"C": "🇺🇸 US Major", "T": "GE", "N": "General Electric"},
    {"C": "🇺🇸 US Major", "T": "CAT", "N": "Caterpillar"},
    {"C": "🇺🇸 US Major", "T": "DE", "N": "John Deere"},
    {"C": "🇺🇸 US Major", "T": "BA", "N": "Boeing"},
    {"C": "🇺🇸 US Major", "T": "LMT", "N": "Lockheed Martin"},
    {"C": "🇺🇸 US Major", "T": "RTX", "N": "Raytheon"},
    {"C": "🇺🇸 US Major", "T": "MMM", "N": "3M"},
    {"C": "🇺🇸 US Major", "T": "F", "N": "Ford Motor"},
    {"C": "🇺🇸 US Major", "T": "GM", "N": "General Motors"},
]

# --- 日本株 (Japan) ---
JAPAN = [
    {"C": "🇯🇵 Japan", "T": "7203.T", "N": "トヨタ自動車"},
    {"C": "🇯🇵 Japan", "T": "6758.T", "N": "ソニーグループ"},
    {"C": "🇯🇵 Japan", "T": "9984.T", "N": "ソフトバンクグループ"},
    {"C": "🇯🇵 Japan", "T": "9434.T", "N": "ソフトバンク(通信)"},
    {"C": "🇯🇵 Japan", "T": "9432.T", "N": "NTT"},
    {"C": "🇯🇵 Japan", "T": "9433.T", "N": "KDDI"},
    {"C": "🇯🇵 Japan", "T": "8306.T", "N": "三菱UFJフィナンシャル"},
    {"C": "🇯🇵 Japan", "T": "8316.T", "N": "三井住友フィナンシャル"},
    {"C": "🇯🇵 Japan", "T": "8411.T", "N": "みずほフィナンシャル"},
    {"C": "🇯🇵 Japan", "T": "8035.T", "N": "東京エレクトロン"},
    {"C": "🇯🇵 Japan", "T": "6857.T", "N": "アドバンテスト"},
    {"C": "🇯🇵 Japan", "T": "6146.T", "N": "ディスコ"},
    {"C": "🇯🇵 Japan", "T": "7735.T", "N": "SCREENホールディングス"},
    {"C": "🇯🇵 Japan", "T": "6920.T", "N": "レーザーテック"},
    {"C": "🇯🇵 Japan", "T": "6861.T", "N": "キーエンス"},
    {"C": "🇯🇵 Japan", "T": "4063.T", "N": "信越化学工業"},
    {"C": "🇯🇵 Japan", "T": "6594.T", "N": "ニデック"},
    {"C": "🇯🇵 Japan", "T": "6981.T", "N": "村田製作所"},
    {"C": "🇯🇵 Japan", "T": "6954.T", "N": "ファナック"},
    {"C": "🇯🇵 Japan", "T": "6301.T", "N": "小松製作所 (コマツ)"},
    {"C": "🇯🇵 Japan", "T": "7011.T", "N": "三菱重工業"},
    {"C": "🇯🇵 Japan", "T": "7012.T", "N": "川崎重工業"},
    {"C": "🇯🇵 Japan", "T": "7013.T", "N": "IHI"},
    {"C": "🇯🇵 Japan", "T": "6501.T", "N": "日立製作所"},
    {"C": "🇯🇵 Japan", "T": "6701.T", "N": "NEC"},
    {"C": "🇯🇵 Japan", "T": "6702.T", "N": "富士通"},
    {"C": "🇯🇵 Japan", "T": "7741.T", "N": "HOYA"},
    {"C": "🇯🇵 Japan", "T": "7751.T", "N": "キヤノン"},
    {"C": "🇯🇵 Japan", "T": "6902.T", "N": "デンソー"},
    {"C": "🇯🇵 Japan", "T": "7267.T", "N": "本田技研工業 (ホンダ)"},
    {"C": "🇯🇵 Japan", "T": "7201.T", "N": "日産自動車"},
    {"C": "🇯🇵 Japan", "T": "7270.T", "N": "SUBARU"},
    {"C": "🇯🇵 Japan", "T": "9983.T", "N": "ファーストリテイリング"},
    {"C": "🇯🇵 Japan", "T": "7974.T", "N": "任天堂"},
    {"C": "🇯🇵 Japan", "T": "9766.T", "N": "コナミグループ"},
    {"C": "🇯🇵 Japan", "T": "9684.T", "N": "スクウェア・エニックス"},
    {"C": "🇯🇵 Japan", "T": "7832.T", "N": "バンダイナムコ"},
    {"C": "🇯🇵 Japan", "T": "8001.T", "N": "伊藤忠商事"},
    {"C": "🇯🇵 Japan", "T": "8058.T", "N": "三菱商事"},
    {"C": "🇯🇵 Japan", "T": "8031.T", "N": "三井物産"},
    {"C": "🇯🇵 Japan", "T": "8002.T", "N": "丸紅"},
    {"C": "🇯🇵 Japan", "T": "8053.T", "N": "住友商事"},
    {"C": "🇯🇵 Japan", "T": "6098.T", "N": "リクルートホールディングス"},
    {"C": "🇯🇵 Japan", "T": "4661.T", "N": "オリエンタルランド"},
    {"C": "🇯🇵 Japan", "T": "2914.T", "N": "日本たばこ産業 (JT)"},
    {"C": "🇯🇵 Japan", "T": "4502.T", "N": "武田薬品工業"},
    {"C": "🇯🇵 Japan", "T": "4519.T", "N": "中外製薬"},
    {"C": "🇯🇵 Japan", "T": "4568.T", "N": "第一三共"},
    {"C": "🇯🇵 Japan", "T": "4911.T", "N": "資生堂"},
    {"C": "🇯🇵 Japan", "T": "4452.T", "N": "花王"},
    {"C": "🇯🇵 Japan", "T": "8766.T", "N": "東京海上ホールディングス"},
    {"C": "🇯🇵 Japan", "T": "8801.T", "N": "三井不動産"},
    {"C": "🇯🇵 Japan", "T": "8802.T", "N": "三菱地所"},
    {"C": "🇯🇵 Japan", "T": "9020.T", "N": "JR東日本"},
    {"C": "🇯🇵 Japan", "T": "9022.T", "N": "JR東海"},
    {"C": "🇯🇵 Japan", "T": "9201.T", "N": "日本航空 (JAL)"},
    {"C": "🇯🇵 Japan", "T": "9202.T", "N": "ANAホールディングス"},
]

# --- ETF / 指数 (Indices) ---
ETF = [
    {"C": "📊 ETF/Index", "T": "^GSPC", "N": "S&P 500 Index"},
    {"C": "📊 ETF/Index", "T": "^DJI", "N": "Dow Jones Industrial Average"},
    {"C": "📊 ETF/Index", "T": "^IXIC", "N": "NASDAQ Composite"},
    {"C": "📊 ETF/Index", "T": "^NDX", "N": "NASDAQ 100"},
    {"C": "📊 ETF/Index", "T": "^RUT", "N": "Russell 2000"},
    {"C": "📊 ETF/Index", "T": "^VIX", "N": "CBOE Volatility Index"},
    {"C": "📊 ETF/Index", "T": "^N225", "N": "Nikkei 225 (日経平均)"},
    {"C": "📊 ETF/Index", "T": "VOO", "N": "Vanguard S&P 500 ETF"},
    {"C": "📊 ETF/Index", "T": "IVV", "N": "iShares Core S&P 500 ETF"},
    {"C": "📊 ETF/Index", "T": "SPY", "N": "SPDR S&P 500 ETF Trust"},
    {"C": "📊 ETF/Index", "T": "VTI", "N": "Vanguard Total Stock Market"},
    {"C": "📊 ETF/Index", "T": "VT", "N": "Vanguard Total World Stock"},
    {"C": "📊 ETF/Index", "T": "QQQ", "N": "Invesco QQQ Trust"},
    {"C": "📊 ETF/Index", "T": "DIA", "N": "SPDR Dow Jones Industrial Average"},
    {"C": "📊 ETF/Index", "T": "IWM", "N": "iShares Russell 2000 ETF"},
    {"C": "📊 ETF/Index", "T": "VTV", "N": "Vanguard Value ETF"},
    {"C": "📊 ETF/Index", "T": "VUG", "N": "Vanguard Growth ETF"},
    {"C": "📊 ETF/Index", "T": "VYM", "N": "Vanguard High Dividend Yield"},
    {"C": "📊 ETF/Index", "T": "VIG", "N": "Vanguard Dividend Appreciation"},
    {"C": "📊 ETF/Index", "T": "SPYD", "N": "SPDR Portfolio S&P 500 High Dividend"},
    {"C": "📊 ETF/Index", "T": "HDV", "N": "iShares Core High Dividend"},
    {"C": "📊 ETF/Index", "T": "DVY", "N": "iShares Select Dividend"},
    {"C": "📊 ETF/Index", "T": "XLK", "N": "Technology Select Sector SPDR"},
    {"C": "📊 ETF/Index", "T": "XLF", "N": "Financial Select Sector SPDR"},
    {"C": "📊 ETF/Index", "T": "XLV", "N": "Health Care Select Sector SPDR"},
    {"C": "📊 ETF/Index", "T": "XLE", "N": "Energy Select Sector SPDR"},
    {"C": "📊 ETF/Index", "T": "XLI", "N": "Industrial Select Sector SPDR"},
    {"C": "📊 ETF/Index", "T": "XLP", "N": "Consumer Staples Select Sector"},
    {"C": "📊 ETF/Index", "T": "XLY", "N": "Consumer Discret Select Sector"},
    {"C": "📊 ETF/Index", "T": "XLC", "N": "Communication Services Select"},
    {"C": "📊 ETF/Index", "T": "XLB", "N": "Materials Select Sector SPDR"},
    {"C": "📊 ETF/Index", "T": "XLU", "N": "Utilities Select Sector SPDR"},
    {"C": "📊 ETF/Index", "T": "XLRE", "N": "Real Estate Select Sector SPDR"},
    {"C": "📊 ETF/Index", "T": "SMH", "N": "VanEck Semiconductor ETF"},
    {"C": "📊 ETF/Index", "T": "SOXX", "N": "iShares Semiconductor ETF"},
    {"C": "📊 ETF/Index", "T": "ARKK", "N": "ARK Innovation ETF"},
    {"C": "📊 ETF/Index", "T": "GLD", "N": "SPDR Gold Shares"},
    {"C": "📊 ETF/Index", "T": "IAU", "N": "iShares Gold Trust"},
    {"C": "📊 ETF/Index", "T": "SLV", "N": "iShares Silver Trust"},
    {"C": "📊 ETF/Index", "T": "USO", "N": "United States Oil Fund"},
    {"C": "📊 ETF/Index", "T": "VEA", "N": "Vanguard FTSE Developed Markets"},
    {"C": "📊 ETF/Index", "T": "VWO", "N": "Vanguard FTSE Emerging Markets"},
    {"C": "📊 ETF/Index", "T": "EEM", "N": "iShares MSCI Emerging Markets"},
    {"C": "📊 ETF/Index", "T": "EFA", "N": "iShares MSCI EAFE ETF"},
    {"C": "📊 ETF/Index", "T": "EWJ", "N": "iShares MSCI Japan ETF"},
    {"C": "📊 ETF/Index", "T": "FXI", "N": "iShares China Large-Cap ETF"},
    {"C": "📊 ETF/Index", "T": "INDA", "N": "iShares MSCI India ETF"},
    {"C": "📊 ETF/Index", "T": "EPI", "N": "WisdomTree India Earnings"},
    {"C": "📊 ETF/Index", "T": "VNQ", "N": "Vanguard Real Estate ETF"},
]

# --- 暗号資産 (Crypto) ---
CRYPTO = [
    {"C": "🪙 Crypto", "T": "BTC-USD", "N": "Bitcoin"},
    {"C": "🪙 Crypto", "T": "ETH-USD", "N": "Ethereum"},
    {"C": "🪙 Crypto", "T": "SOL-USD", "N": "Solana"},
    {"C": "🪙 Crypto", "T": "XRP-USD", "N": "XRP"},
    {"C": "🪙 Crypto", "T": "BNB-USD", "N": "BNB"},
    {"C": "🪙 Crypto", "T": "DOGE-USD", "N": "Dogecoin"},
    {"C": "🪙 Crypto", "T": "ADA-USD", "N": "Cardano"},
    {"C": "🪙 Crypto", "T": "AVAX-USD", "N": "Avalanche"},
    {"C": "🪙 Crypto", "T": "TRX-USD", "N": "TRON"},
    {"C": "🪙 Crypto", "T": "DOT-USD", "N": "Polkadot"},
    {"C": "🪙 Crypto", "T": "LINK-USD", "N": "Chainlink"},
    {"C": "🪙 Crypto", "T": "MATIC-USD", "N": "Polygon"},
    {"C": "🪙 Crypto", "T": "SHIB-USD", "N": "Shiba Inu"},
    {"C": "🪙 Crypto", "T": "LTC-USD", "N": "Litecoin"},
    {"C": "🪙 Crypto", "T": "BCH-USD", "N": "Bitcoin Cash"},
]

# リスト結合 (これで合計350銘柄以上)
TICKER_DATA_RAW = BONDS + FOREX + US_TECH + US_MAJOR + JAPAN + ETF + CRYPTO
ticker_df_master = pd.DataFrame(TICKER_DATA_RAW).rename(columns={"C": "Category", "T": "Ticker", "N": "Name"})

# ★辞書作成: コードから正式名称を引けるようにする
TICKER_NAME_MAP = {item['T']: item['N'] for item in TICKER_DATA_RAW}

# --- 3. 期間設定 ---
PERIOD_OPTIONS = {
    "1日": "1d", "1週間": "5d", "1ヶ月": "1mo", "3ヶ月": "3mo",
    "6ヶ月": "6mo", "1年": "1y", "3年": "3y", "5年": "5y",
    "10年": "10y", "全期間": "max"
}

def get_interval_for_period(period_key):
    if period_key == "1d": return "15m"
    if period_key == "5d": return "60m"
    return "1d"

# --- 4. 関数群 ---

def calculate_technicals(df):
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

@st.cache_data(ttl=300)
def get_stock_data(ticker, period_key):
    if not ticker: return None, None, None
    yf_period = PERIOD_OPTIONS.get(period_key, "1y")
    yf_interval = get_interval_for_period(yf_period)
    
    try:
        stock = yf.Ticker(ticker)
        if period_key == "3年":
            start_date = datetime.now() - timedelta(days=365*3)
            df = stock.history(start=start_date, interval=yf_interval)
        else:
            df = stock.history(period=yf_period, interval=yf_interval)
        
        if not df.empty:
            df = calculate_technicals(df)
        else:
            return None, None, None

        fin_df = pd.DataFrame()
        try:
            fin_df = stock.financials
        except:
            pass
            
        return df, fin_df, stock.info
    except:
        return None, None, None

def clean_search_term(text):
    if not text: return ""
    # カッコ除去
    text = text.replace('（', '(').split('(')[0].strip()
    
    # 検索ノイズになりやすい単語を削除
    stopwords = ["Inc", "Corp", "Corporation", "Ltd", "Limited", "Holdings", "Group", "Company", "Co", "plc", "S.A.", "N.V."]
    words = text.split()
    cleaned_words = [w for w in words if w.strip(',.') not in stopwords]
    
    return " ".join(cleaned_words)

@st.cache_data(ttl=600)
def get_massive_news(tickers):
    """
    【スマート検索版】
    選択されたTickerを受け取り、辞書(TICKER_NAME_MAP)またはメモから
    最適な名称を自動的に引き当て、クリーニングして検索する。
    """
    if not tickers: return []
    
    search_keywords = []
    
    # API制限考慮: 上位5銘柄に絞る
    target_tickers = tickers[:5]
    
    for t in target_tickers:
        if t in TICKER_NAME_MAP:
            # プリセットにある場合はそのきれいな名前を使う
            raw_name = TICKER_NAME_MAP[t]
        else:
            # ない場合はTickerそのまま (UI側でメモを渡すロジックと組み合わせる)
            raw_name = t
            
        # クリーニング
        clean_name = clean_search_term(raw_name)
        if clean_name and len(clean_name) >= 2:
            search_keywords.append(clean_name)
            
    # 重複削除
    unique_keywords = list(set(search_keywords))
    if not unique_keywords: return []

    # OR検索
    query_string = " OR ".join(unique_keywords)
    
    try:
        en_res = newsapi.get_everything(q=query_string, language='en', sort_by='publishedAt', page_size=50)
        jp_res = newsapi.get_everything(q=query_string, language='jp', sort_by='publishedAt', page_size=50)
        
        all_articles = en_res.get('articles', []) + jp_res.get('articles', [])
        all_articles = sorted([a for a in all_articles if a.get('publishedAt')], key=lambda x: x['publishedAt'], reverse=True)
        return all_articles
    except:
        return []

def fetch_watchlist():
    try:
        return pd.DataFrame(supabase.table("watchlist").select("*").order("created_at", desc=True).execute().data)
    except:
        return pd.DataFrame()

def add_to_watchlist(ticker, note):
    try:
        supabase.table("watchlist").insert({"ticker": ticker, "note": note}).execute()
        return True
    except:
        return False

def delete_from_watchlist(item_id):
    try:
        supabase.table("watchlist").delete().eq("id", item_id).execute()
    except:
        pass

# --- 5. アプリ画面構築 ---

st.title("📈 Pro Investor Dashboard v10")

if 'selected_tickers' not in st.session_state:
    st.session_state.selected_tickers = ["AAPL"]

w_df = fetch_watchlist()

# サイドバー
st.sidebar.header("🕹️ 管理パネル")
with st.sidebar.expander("➕ 新規追加 (任意コード)", expanded=False):
    st.caption("メモ必須")
    with st.form("sb_add"):
        t_in = st.text_input("コード").upper().strip()
        n_in = st.text_input("メモ").strip()
        if st.form_submit_button("追加"):
            if t_in and n_in:
                add_to_watchlist(t_in, n_in)
                st.success(f"追加: {t_in}")
                st.rerun()
            else:
                st.error("コードとメモを入力してください")

with st.sidebar.expander("🗑️ 削除", expanded=False):
    if not w_df.empty:
        w_df['del_label'] = w_df['ticker'] + " - " + w_df['note'].fillna("")
        to_delete = st.multiselect("選択:", w_df['del_label'])
        if st.button("削除実行", type="primary"):
            if to_delete:
                ids = w_df[w_df['del_label'].isin(to_delete)]['id'].tolist()
                for i in ids: delete_from_watchlist(i)
                st.rerun()
    else:
        st.info("リストは空です")

st.sidebar.markdown("---")
period_label = st.sidebar.selectbox("期間", list(PERIOD_OPTIONS.keys()), index=5)
st.sidebar.markdown("---")

st.sidebar.subheader("📊 分析・比較する銘柄")
available_options = []
default_sel = []

if not w_df.empty:
    w_df['display'] = w_df['ticker'] + " - " + w_df['note'].fillna("")
    available_options = w_df['display'].tolist()
    valid_selected = [s for s in st.session_state.selected_tickers if any(s == op.split(" - ")[0] for op in available_options)]
    if not valid_selected and available_options: valid_selected = [available_options[0].split(" - ")[0]]
    default_options = [op for op in available_options if op.split(" - ")[0] in valid_selected]

    selected_displays = st.sidebar.pills("タップして選択", options=available_options, default=default_options, selection_mode="multi")
    current_tickers = [x.split(" - ")[0] for x in selected_displays] if selected_displays else []
    st.session_state.selected_tickers = current_tickers
else:
    st.sidebar.info("ウォッチリストが空です")
    current_tickers = []


# ==========================================
# メインコンテンツ
# ==========================================

tab_chart, tab_corr, tab_news, tab_db = st.tabs(["📊 チャート詳細", "🔢 相関マトリクス", "📰 関連ニュース", "📋 銘柄DB"])

# --- タブ1: チャート詳細 ---
with tab_chart:
    if not current_tickers:
        st.info("👈 銘柄を選択してください")
    
    elif len(current_tickers) == 1:
        ticker = current_tickers[0]
        with st.spinner(f"{ticker} 分析中..."):
            df, fin_df, info = get_stock_data(ticker, period_label)
        
        if df is not None:
            short_name = info.get('shortName', ticker) if info else ticker
            st.subheader(f"{short_name} ({ticker})")
            
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            chg = latest['Close'] - prev['Close']
            pct = (chg / prev['Close']) * 100
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Current", f"${latest['Close']:,.2f}", f"{chg:,.2f} ({pct:.2f}%)")
            c2.metric("Period", period_label)
            c3.metric("High", f"${df['High'].max():,.2f}")
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
            if 'SMA20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name='SMA 20'))
            if 'SMA50' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name='SMA 50'))
            fig.update_layout(height=500, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            if info and info.get('quoteType') == 'EQUITY':
                st.markdown("### 🏢 企業業績 (Annual)")
                if fin_df is not None and not fin_df.empty:
                    try:
                        financials = fin_df.T 
                        financials.index = pd.to_datetime(financials.index).strftime('%Y-%m-%d')
                        fin_view = financials.sort_index()
                        target = ['Total Revenue', 'Net Income']
                        cols = [c for c in target if c in fin_view.columns]
                        if cols:
                            fig_fin = px.bar(fin_view, y=cols, barmode='group')
                            st.plotly_chart(fig_fin, use_container_width=True)
                    except: pass
    else:
        st.subheader("📊 パフォーマンス比較 (正規化)")
        fig_comp = go.Figure()
        for t in current_tickers:
            df, _, _ = get_stock_data(t, period_label)
            if df is not None:
                start = df['Close'].iloc[0]
                if start > 0:
                    norm = ((df['Close'] / start) - 1) * 100
                    fig_comp.add_trace(go.Scatter(x=df.index, y=norm, mode='lines', name=f"{t} ({norm.iloc[-1]:+.2f}%)"))
        fig_comp.update_layout(height=600, hovermode="x unified")
        fig_comp.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.3)
        st.plotly_chart(fig_comp, use_container_width=True)

# --- タブ2: 相関 ---
with tab_corr:
    st.header("🔢 相関分析")
    if len(current_tickers) >= 2:
        with st.spinner("計算中..."):
            close_data = {}
            for t in current_tickers:
                df, _, _ = get_stock_data(t, period_label)
                if df is not None: close_data[t] = df['Close']
            
            if close_data:
                df_corr = pd.DataFrame(close_data)
                fig_heatmap = px.imshow(df_corr.corr(), text_auto=".2f", color_continuous_scale="RdBu_r", range_color=[-1, 1])
                st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.error("データ不足")
    else:
        st.warning("2つ以上選択してください")

# --- タブ3: ニュース (AI検索) ---
with tab_news:
    st.header("📰 関連ニュース (AI自動検索)")
    if current_tickers:
        # ロジック: Tickerリストを渡し、関数内で辞書を使って名前解決＆検索
        search_candidates = []
        for t in current_tickers:
            if t in TICKER_NAME_MAP:
                search_candidates.append(TICKER_NAME_MAP[t])
            else:
                # 辞書にない場合はDBのメモを使う
                row = w_df[w_df['ticker'] == t]
                if not row.empty:
                    note = row.iloc[0]['note']
                    search_candidates.append(note if note else t)
                else:
                    search_candidates.append(t)
        
        clean_display = [clean_search_term(q) for q in search_candidates]
        st.caption(f"検索ワード: {', '.join(clean_display[:5])} ...")
        
        with st.spinner("ニュース収集中..."):
            # 文字列リストを渡す
            arts = get_massive_news(search_candidates)
        
        if arts:
            for a in arts:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 3])
                    if a.get('urlToImage'): 
                        try: c1.image(a['urlToImage'], use_container_width=True)
                        except: c1.text("No Img")
                    c2.subheader(a.get('title', ''))
                    c2.caption(f"{a['source']['name']} | {a['publishedAt'][:10]}")
                    c2.markdown(f"[Link]({a['url']})")
        else:
            st.warning("ニュースが見つかりませんでした")
            st.info("メモ欄に「Toyota」のように単純な英語名を入れるとヒットしやすくなります。")
    else:
        st.warning("銘柄を選択してください")

# --- タブ4: DB ---
with tab_db:
    st.header("📋 銘柄DB")
    search_q = st.text_input("検索", placeholder="Bond, トヨタ...")
    df_db = ticker_df_master
    if search_q:
        mask = df_db.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)
        df_db = df_db[mask]
    for cat in df_db['Category'].unique():
        with st.expander(f"{cat}", expanded=False):
            st.dataframe(df_db[df_db['Category']==cat][['Ticker', 'Name']], use_container_width=True, hide_index=True)
