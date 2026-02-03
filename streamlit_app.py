import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
import feedparser # 新しいニュース取得ライブラリ
import urllib.parse
from datetime import datetime, timedelta

# --- 1. 設定 ---
st.set_page_config(page_title="Pro Investor Dashboard v11", layout="wide")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    # NEWS_API_KEY は不要になりました
except:
    st.error("Secrets (Supabase URL/KEY) が設定されていません。")
    st.stop()

# クライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================================================================
# 2. 銘柄データマスター (300種以上 固定)
# ==============================================================================
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
US_TECH = [
    {"C": "🇺🇸 Tech", "T": "AAPL", "N": "Apple"}, {"C": "🇺🇸 Tech", "T": "MSFT", "N": "Microsoft"},
    {"C": "🇺🇸 Tech", "T": "NVDA", "N": "NVIDIA"}, {"C": "🇺🇸 Tech", "T": "GOOGL", "N": "Google"},
    {"C": "🇺🇸 Tech", "T": "AMZN", "N": "Amazon"}, {"C": "🇺🇸 Tech", "T": "META", "N": "Meta"},
    {"C": "🇺🇸 Tech", "T": "TSLA", "N": "Tesla"}, {"C": "🇺🇸 Tech", "T": "AVGO", "N": "Broadcom"},
    {"C": "🇺🇸 Tech", "T": "AMD", "N": "AMD"}, {"C": "🇺🇸 Tech", "T": "INTC", "N": "Intel"},
    {"C": "🇺🇸 Tech", "T": "QCOM", "N": "Qualcomm"}, {"C": "🇺🇸 Tech", "T": "TXN", "N": "Texas Instruments"},
    {"C": "🇺🇸 Tech", "T": "MU", "N": "Micron"}, {"C": "🇺🇸 Tech", "T": "AMAT", "N": "Applied Materials"},
    {"C": "🇺🇸 Tech", "T": "LRCX", "N": "Lam Research"}, {"C": "🇺🇸 Tech", "T": "ADI", "N": "Analog Devices"},
    {"C": "🇺🇸 Tech", "T": "KLAC", "N": "KLA Corp"}, {"C": "🇺🇸 Tech", "T": "ASML", "N": "ASML"},
    {"C": "🇺🇸 Tech", "T": "TSM", "N": "TSMC"}, {"C": "🇺🇸 Tech", "T": "ARM", "N": "Arm"},
    {"C": "🇺🇸 Tech", "T": "ORCL", "N": "Oracle"}, {"C": "🇺🇸 Tech", "T": "CRM", "N": "Salesforce"},
    {"C": "🇺🇸 Tech", "T": "ADBE", "N": "Adobe"}, {"C": "🇺🇸 Tech", "T": "CSCO", "N": "Cisco"},
    {"C": "🇺🇸 Tech", "T": "IBM", "N": "IBM"}, {"C": "🇺🇸 Tech", "T": "NOW", "N": "ServiceNow"},
    {"C": "🇺🇸 Tech", "T": "INTU", "N": "Intuit"}, {"C": "🇺🇸 Tech", "T": "UBER", "N": "Uber"},
    {"C": "🇺🇸 Tech", "T": "ABNB", "N": "Airbnb"}, {"C": "🇺🇸 Tech", "T": "PANW", "N": "Palo Alto"},
    {"C": "🇺🇸 Tech", "T": "CRWD", "N": "CrowdStrike"}, {"C": "🇺🇸 Tech", "T": "PLTR", "N": "Palantir"},
    {"C": "🇺🇸 Tech", "T": "SNOW", "N": "Snowflake"}, {"C": "🇺🇸 Tech", "T": "SQ", "N": "Block"},
    {"C": "🇺🇸 Tech", "T": "PYPL", "N": "PayPal"}, {"C": "🇺🇸 Tech", "T": "SHOP", "N": "Shopify"},
    {"C": "🇺🇸 Tech", "T": "COIN", "N": "Coinbase"}, {"C": "🇺🇸 Tech", "T": "HOOD", "N": "Robinhood"},
    {"C": "🇺🇸 Tech", "T": "RBLX", "N": "Roblox"}, {"C": "🇺🇸 Tech", "T": "U", "N": "Unity"},
    {"C": "🇺🇸 Tech", "T": "NET", "N": "Cloudflare"},
]
US_MAJOR = [
    {"C": "🇺🇸 Major", "T": "JPM", "N": "JPMorgan"}, {"C": "🇺🇸 Major", "T": "BAC", "N": "Bank of America"},
    {"C": "🇺🇸 Major", "T": "WFC", "N": "Wells Fargo"}, {"C": "🇺🇸 Major", "T": "C", "N": "Citigroup"},
    {"C": "🇺🇸 Major", "T": "GS", "N": "Goldman Sachs"}, {"C": "🇺🇸 Major", "T": "MS", "N": "Morgan Stanley"},
    {"C": "🇺🇸 Major", "T": "BLK", "N": "BlackRock"}, {"C": "🇺🇸 Major", "T": "V", "N": "Visa"},
    {"C": "🇺🇸 Major", "T": "MA", "N": "Mastercard"}, {"C": "🇺🇸 Major", "T": "AXP", "N": "American Express"},
    {"C": "🇺🇸 Major", "T": "BRK-B", "N": "Berkshire Hathaway"}, {"C": "🇺🇸 Major", "T": "WMT", "N": "Walmart"},
    {"C": "🇺🇸 Major", "T": "TGT", "N": "Target"}, {"C": "🇺🇸 Major", "T": "COST", "N": "Costco"},
    {"C": "🇺🇸 Major", "T": "HD", "N": "Home Depot"}, {"C": "🇺🇸 Major", "T": "LOW", "N": "Lowe's"},
    {"C": "🇺🇸 Major", "T": "PG", "N": "P&G"}, {"C": "🇺🇸 Major", "T": "KO", "N": "Coca-Cola"},
    {"C": "🇺🇸 Major", "T": "PEP", "N": "PepsiCo"}, {"C": "🇺🇸 Major", "T": "MCD", "N": "McDonald's"},
    {"C": "🇺🇸 Major", "T": "SBUX", "N": "Starbucks"}, {"C": "🇺🇸 Major", "T": "NKE", "N": "Nike"},
    {"C": "🇺🇸 Major", "T": "DIS", "N": "Disney"}, {"C": "🇺🇸 Major", "T": "CMCSA", "N": "Comcast"},
    {"C": "🇺🇸 Major", "T": "NFLX", "N": "Netflix"}, {"C": "🇺🇸 Major", "T": "JNJ", "N": "J&J"},
    {"C": "🇺🇸 Major", "T": "LLY", "N": "Eli Lilly"}, {"C": "🇺🇸 Major", "T": "UNH", "N": "UnitedHealth"},
    {"C": "🇺🇸 Major", "T": "PFE", "N": "Pfizer"}, {"C": "🇺🇸 Major", "T": "MRK", "N": "Merck"},
    {"C": "🇺🇸 Major", "T": "ABBV", "N": "AbbVie"}, {"C": "🇺🇸 Major", "T": "CVX", "N": "Chevron"},
    {"C": "🇺🇸 Major", "T": "XOM", "N": "Exxon Mobil"}, {"C": "🇺🇸 Major", "T": "GE", "N": "General Electric"},
    {"C": "🇺🇸 Major", "T": "CAT", "N": "Caterpillar"}, {"C": "🇺🇸 Major", "T": "DE", "N": "John Deere"},
    {"C": "🇺🇸 Major", "T": "BA", "N": "Boeing"}, {"C": "🇺🇸 Major", "T": "LMT", "N": "Lockheed Martin"},
    {"C": "🇺🇸 Major", "T": "RTX", "N": "Raytheon"}, {"C": "🇺🇸 Major", "T": "MMM", "N": "3M"},
    {"C": "🇺🇸 Major", "T": "F", "N": "Ford"}, {"C": "🇺🇸 Major", "T": "GM", "N": "GM"},
]
JAPAN = [
    {"C": "🇯🇵 Japan", "T": "7203.T", "N": "トヨタ自動車"}, {"C": "🇯🇵 Japan", "T": "6758.T", "N": "ソニーG"},
    {"C": "🇯🇵 Japan", "T": "9984.T", "N": "ソフトバンクG"}, {"C": "🇯🇵 Japan", "T": "9434.T", "N": "ソフトバンク"},
    {"C": "🇯🇵 Japan", "T": "9432.T", "N": "NTT"}, {"C": "🇯🇵 Japan", "T": "9433.T", "N": "KDDI"},
    {"C": "🇯🇵 Japan", "T": "8306.T", "N": "三菱UFJ"}, {"C": "🇯🇵 Japan", "T": "8316.T", "N": "三井住友FG"},
    {"C": "🇯🇵 Japan", "T": "8411.T", "N": "みずほFG"}, {"C": "🇯🇵 Japan", "T": "8035.T", "N": "東京エレクトロン"},
    {"C": "🇯🇵 Japan", "T": "6857.T", "N": "アドバンテスト"}, {"C": "🇯🇵 Japan", "T": "6146.T", "N": "ディスコ"},
    {"C": "🇯🇵 Japan", "T": "7735.T", "N": "SCREEN"}, {"C": "🇯🇵 Japan", "T": "6920.T", "N": "レーザーテック"},
    {"C": "🇯🇵 Japan", "T": "6861.T", "N": "キーエンス"}, {"C": "🇯🇵 Japan", "T": "4063.T", "N": "信越化学"},
    {"C": "🇯🇵 Japan", "T": "6594.T", "N": "ニデック"}, {"C": "🇯🇵 Japan", "T": "6981.T", "N": "村田製作所"},
    {"C": "🇯🇵 Japan", "T": "6954.T", "N": "ファナック"}, {"C": "🇯🇵 Japan", "T": "6301.T", "N": "コマツ"},
    {"C": "🇯🇵 Japan", "T": "7011.T", "N": "三菱重工"}, {"C": "🇯🇵 Japan", "T": "7012.T", "N": "川崎重工"},
    {"C": "🇯🇵 Japan", "T": "7013.T", "N": "IHI"}, {"C": "🇯🇵 Japan", "T": "6501.T", "N": "日立製作所"},
    {"C": "🇯🇵 Japan", "T": "6701.T", "N": "NEC"}, {"C": "🇯🇵 Japan", "T": "6702.T", "N": "富士通"},
    {"C": "🇯🇵 Japan", "T": "7741.T", "N": "HOYA"}, {"C": "🇯🇵 Japan", "T": "7751.T", "N": "キヤノン"},
    {"C": "🇯🇵 Japan", "T": "6902.T", "N": "デンソー"}, {"C": "🇯🇵 Japan", "T": "7267.T", "N": "ホンダ"},
    {"C": "🇯🇵 Japan", "T": "7201.T", "N": "日産自動車"}, {"C": "🇯🇵 Japan", "T": "7270.T", "N": "SUBARU"},
    {"C": "🇯🇵 Japan", "T": "9983.T", "N": "ファーストリテイリング"}, {"C": "🇯🇵 Japan", "T": "7974.T", "N": "任天堂"},
    {"C": "🇯🇵 Japan", "T": "9766.T", "N": "コナミ"}, {"C": "🇯🇵 Japan", "T": "9684.T", "N": "スクエニ"},
    {"C": "🇯🇵 Japan", "T": "7832.T", "N": "バンダイナムコ"}, {"C": "🇯🇵 Japan", "T": "8001.T", "N": "伊藤忠商事"},
    {"C": "🇯🇵 Japan", "T": "8058.T", "N": "三菱商事"}, {"C": "🇯🇵 Japan", "T": "8031.T", "N": "三井物産"},
    {"C": "🇯🇵 Japan", "T": "8002.T", "N": "丸紅"}, {"C": "🇯🇵 Japan", "T": "8053.T", "N": "住友商事"},
    {"C": "🇯🇵 Japan", "T": "6098.T", "N": "リクルート"}, {"C": "🇯🇵 Japan", "T": "4661.T", "N": "オリエンタルランド"},
    {"C": "🇯🇵 Japan", "T": "2914.T", "N": "JT"}, {"C": "🇯🇵 Japan", "T": "4502.T", "N": "武田薬品"},
    {"C": "🇯🇵 Japan", "T": "4519.T", "N": "中外製薬"}, {"C": "🇯🇵 Japan", "T": "4568.T", "N": "第一三共"},
    {"C": "🇯🇵 Japan", "T": "4911.T", "N": "資生堂"}, {"C": "🇯🇵 Japan", "T": "4452.T", "N": "花王"},
    {"C": "🇯🇵 Japan", "T": "8766.T", "N": "東京海上"}, {"C": "🇯🇵 Japan", "T": "8801.T", "N": "三井不動産"},
    {"C": "🇯🇵 Japan", "T": "8802.T", "N": "三菱地所"}, {"C": "🇯🇵 Japan", "T": "9020.T", "N": "JR東日本"},
    {"C": "🇯🇵 Japan", "T": "9022.T", "N": "JR東海"}, {"C": "🇯🇵 Japan", "T": "9201.T", "N": "JAL"},
    {"C": "🇯🇵 Japan", "T": "9202.T", "N": "ANA"},
]
ETF = [
    {"C": "📊 ETF", "T": "^GSPC", "N": "S&P 500"}, {"C": "📊 ETF", "T": "^DJI", "N": "Dow Jones"},
    {"C": "📊 ETF", "T": "^IXIC", "N": "NASDAQ"}, {"C": "📊 ETF", "T": "^NDX", "N": "NASDAQ 100"},
    {"C": "📊 ETF", "T": "^RUT", "N": "Russell 2000"}, {"C": "📊 ETF", "T": "^VIX", "N": "VIX"},
    {"C": "📊 ETF", "T": "^N225", "N": "Nikkei 225"},
    {"C": "📊 ETF", "T": "VOO", "N": "Vanguard S&P 500"}, {"C": "📊 ETF", "T": "IVV", "N": "iShares S&P 500"},
    {"C": "📊 ETF", "T": "SPY", "N": "SPDR S&P 500"}, {"C": "📊 ETF", "T": "VTI", "N": "Vanguard Total Market"},
    {"C": "📊 ETF", "T": "VT", "N": "Vanguard World"}, {"C": "📊 ETF", "T": "QQQ", "N": "Invesco QQQ"},
    {"C": "📊 ETF", "T": "DIA", "N": "SPDR Dow Jones"}, {"C": "📊 ETF", "T": "IWM", "N": "Russell 2000 ETF"},
    {"C": "📊 ETF", "T": "VTV", "N": "Vanguard Value"}, {"C": "📊 ETF", "T": "VUG", "N": "Vanguard Growth"},
    {"C": "📊 ETF", "T": "VYM", "N": "High Dividend"}, {"C": "📊 ETF", "T": "VIG", "N": "Dividend Appreciation"},
    {"C": "📊 ETF", "T": "SPYD", "N": "SPDR High Dividend"}, {"C": "📊 ETF", "T": "HDV", "N": "Core High Dividend"},
    {"C": "📊 ETF", "T": "DVY", "N": "Select Dividend"},
    {"C": "📊 ETF", "T": "XLK", "N": "Tech Sector"}, {"C": "📊 ETF", "T": "XLF", "N": "Financial Sector"},
    {"C": "📊 ETF", "T": "XLV", "N": "Health Care Sector"}, {"C": "📊 ETF", "T": "XLE", "N": "Energy Sector"},
    {"C": "📊 ETF", "T": "SMH", "N": "Semiconductor"}, {"C": "📊 ETF", "T": "SOXX", "N": "iShares Semi"},
    {"C": "📊 ETF", "T": "ARKK", "N": "ARK Innovation"},
    {"C": "📊 ETF", "T": "GLD", "N": "Gold"}, {"C": "📊 ETF", "T": "IAU", "N": "iShares Gold"},
    {"C": "📊 ETF", "T": "SLV", "N": "Silver"}, {"C": "📊 ETF", "T": "USO", "N": "Oil Fund"},
    {"C": "📊 ETF", "T": "VEA", "N": "Developed Markets"}, {"C": "📊 ETF", "T": "VWO", "N": "Emerging Markets"},
    {"C": "📊 ETF", "T": "EEM", "N": "MSCI Emerging"}, {"C": "📊 ETF", "T": "EWJ", "N": "MSCI Japan"},
    {"C": "📊 ETF", "T": "FXI", "N": "China Large-Cap"}, {"C": "📊 ETF", "T": "INDA", "N": "MSCI India"},
    {"C": "📊 ETF", "T": "EPI", "N": "India Earnings"}, {"C": "📊 ETF", "T": "VNQ", "N": "Real Estate"},
]
CRYPTO = [
    {"C": "🪙 Crypto", "T": "BTC-USD", "N": "Bitcoin"}, {"C": "🪙 Crypto", "T": "ETH-USD", "N": "Ethereum"},
    {"C": "🪙 Crypto", "T": "SOL-USD", "N": "Solana"}, {"C": "🪙 Crypto", "T": "XRP-USD", "N": "XRP"},
    {"C": "🪙 Crypto", "T": "BNB-USD", "N": "BNB"}, {"C": "🪙 Crypto", "T": "DOGE-USD", "N": "Dogecoin"},
    {"C": "🪙 Crypto", "T": "ADA-USD", "N": "Cardano"}, {"C": "🪙 Crypto", "T": "AVAX-USD", "N": "Avalanche"},
    {"C": "🪙 Crypto", "T": "TRX-USD", "N": "TRON"}, {"C": "🪙 Crypto", "T": "DOT-USD", "N": "Polkadot"},
    {"C": "🪙 Crypto", "T": "LINK-USD", "N": "Chainlink"}, {"C": "🪙 Crypto", "T": "MATIC-USD", "N": "Polygon"},
    {"C": "🪙 Crypto", "T": "SHIB-USD", "N": "Shiba Inu"}, {"C": "🪙 Crypto", "T": "LTC-USD", "N": "Litecoin"},
    {"C": "🪙 Crypto", "T": "BCH-USD", "N": "Bitcoin Cash"},
]

TICKER_DATA_RAW = BONDS + FOREX + US_TECH + US_MAJOR + JAPAN + ETF + CRYPTO
ticker_df_master = pd.DataFrame(TICKER_DATA_RAW).rename(columns={"C": "Category", "T": "Ticker", "N": "Name"})
TICKER_NAME_MAP = {item['T']: item['N'] for item in TICKER_DATA_RAW}

# --- 3. 関数群 ---

# RSSニュース取得 (根本解決策)
@st.cache_data(ttl=300)
def fetch_rss_news(ticker, name):
    """
    Yahoo Finance (US) のRSSフィードと
    Google News (JP) のRSSフィードを併用してニュースを取得
    """
    news_items = []
    
    # 1. Yahoo Finance RSS (英語・Ticker直結)
    try:
        yf_url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        feed_yf = feedparser.parse(yf_url)
        for entry in feed_yf.entries[:5]: # 各5件
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "source": "Yahoo Finance (US)"
            })
    except:
        pass

    # 2. Google News RSS (日本語・キーワード検索)
    # Tickerではなく「名前」で検索する (例: 7203.T -> トヨタ自動車)
    try:
        query = urllib.parse.quote(name)
        # Google News RSS (日本語)
        gl_url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja"
        feed_gl = feedparser.parse(gl_url)
        for entry in feed_gl.entries[:5]:
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "source": "Google News (JP)"
            })
    except:
        pass
        
    return news_items

@st.cache_data(ttl=300)
def get_stock_data(ticker, period_key):
    if not ticker: return None, None, None
    
    # 期間マップ
    p_map = {
        "1日": "1d", "1週間": "5d", "1ヶ月": "1mo", "3ヶ月": "3mo",
        "6ヶ月": "6mo", "1年": "1y", "3年": "3y", "5年": "5y",
        "10年": "10y", "全期間": "max"
    }
    i_map = {"1日": "15m", "1週間": "60m"} # 短期は分足
    
    yf_p = p_map.get(period_key, "1y")
    yf_i = i_map.get(period_key, "1d")
    
    try:
        stock = yf.Ticker(ticker)
        
        # 3年の特殊処理
        if period_key == "3年":
            start = datetime.now() - timedelta(days=365*3)
            df = stock.history(start=start, interval=yf_i)
        else:
            df = stock.history(period=yf_p, interval=yf_i)
            
        if df.empty: return None, None, None
        
        # テクニカル計算
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta>0, 0)).rolling(14).mean()
        loss = (-delta.where(delta<0, 0)).rolling(14).mean()
        rs = gain/loss
        df['RSI'] = 100 - (100/(1+rs))
        e12 = df['Close'].ewm(span=12).mean()
        e26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = e12 - e26
        df['Signal'] = df['MACD'].ewm(span=9).mean()
        
        # 財務データ
        fin_df = pd.DataFrame()
        try: fin_df = stock.financials
        except: pass
        
        return df, fin_df, stock.info
    except:
        return None, None, None

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

# --- 5. UI ---
st.title("📈 Pro Investor Dashboard v11")

if 'selected_tickers' not in st.session_state:
    st.session_state.selected_tickers = ["AAPL"]

w_df = fetch_watchlist()

# サイドバー
st.sidebar.header("🕹️ 管理パネル")
with st.sidebar.expander("➕ 新規追加 (任意)", expanded=False):
    st.caption("メモ必須")
    with st.form("add"):
        t = st.text_input("コード").upper().strip()
        n = st.text_input("メモ").strip()
        if st.form_submit_button("追加"):
            if t and n:
                add_to_watchlist(t, n)
                st.success("追加しました")
                st.rerun()
            else:
                st.error("入力してください")

with st.sidebar.expander("🗑️ 削除", expanded=False):
    if not w_df.empty:
        w_df['lbl'] = w_df['ticker'] + " - " + w_df['note'].fillna("")
        dels = st.multiselect("選択:", w_df['lbl'])
        if st.button("削除実行"):
            ids = w_df[w_df['lbl'].isin(dels)]['id'].tolist()
            for i in ids: delete_from_watchlist(i)
            st.rerun()

st.sidebar.markdown("---")
period = st.sidebar.selectbox("期間", ["1日","1週間","1ヶ月","3ヶ月","6ヶ月","1年","3年","5年","10年","全期間"], index=5)
st.sidebar.markdown("---")

st.sidebar.subheader("📊 分析対象")
opts = []
defs = []
if not w_df.empty:
    w_df['lbl'] = w_df['ticker'] + " - " + w_df['note'].fillna("")
    opts = w_df['lbl'].tolist()
    # セッション復元
    valid = [s for s in st.session_state.selected_tickers if any(s == o.split(" - ")[0] for o in opts)]
    if not valid and opts: valid = [opts[0].split(" - ")[0]]
    defs = [o for o in opts if o.split(" - ")[0] in valid]
    
    sels = st.sidebar.pills("選択 (複数可)", opts, default=defs, selection_mode="multi")
    current_tickers = [x.split(" - ")[0] for x in sels] if sels else []
    st.session_state.selected_tickers = current_tickers
else:
    st.sidebar.info("リストが空です")
    current_tickers = []

# メイン
t1, t2, t3, t4 = st.tabs(["📊 チャート", "🔢 相関", "📰 ニュース (RSS)", "📋 DB"])

with t1:
    if not current_tickers:
        st.info("銘柄を選択してください")
    elif len(current_tickers) == 1:
        tk = current_tickers[0]
        with st.spinner(f"{tk} データ取得中..."):
            df, fin, info = get_stock_data(tk, period)
        if df is not None:
            nm = info.get('shortName', tk) if info else tk
            st.subheader(f"{nm} ({tk})")
            
            cur = df['Close'].iloc[-1]
            pre = df['Close'].iloc[-2]
            chg = cur - pre
            pct = (chg/pre)*100
            
            c1,c2,c3 = st.columns(3)
            c1.metric("Current", f"{cur:,.2f}", f"{chg:,.2f} ({pct:.2f}%)")
            c2.metric("Period", period)
            c3.metric("High", f"{df['High'].max():,.2f}")
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
            if 'SMA20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name="SMA20"))
            if 'SMA50' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name="SMA50"))
            fig.update_layout(height=500, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            if fin is not None and not fin.empty:
                st.markdown("### 🏢 業績")
                try:
                    f = fin.T
                    f.index = pd.to_datetime(f.index).strftime('%Y-%m-%d')
                    fv = f.sort_index()
                    cols = [c for c in ['Total Revenue', 'Net Income'] if c in fv.columns]
                    if cols: st.plotly_chart(px.bar(fv, y=cols, barmode='group'), use_container_width=True)
                except: pass
    else:
        st.subheader("📊 比較チャート (正規化)")
        fig = go.Figure()
        for tk in current_tickers:
            df, _, _ = get_stock_data(tk, period)
            if df is not None:
                st0 = df['Close'].iloc[0]
                if st0>0:
                    norm = ((df['Close']/st0)-1)*100
                    fig.add_trace(go.Scatter(x=df.index, y=norm, mode='lines', name=f"{tk}"))
        fig.update_layout(height=600, hovermode="x unified")
        fig.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.3)
        st.plotly_chart(fig, use_container_width=True)

with t2:
    st.header("🔢 相関分析")
    if len(current_tickers) >= 2:
        with st.spinner("計算中..."):
            d = {}
            for tk in current_tickers:
                df, _, _ = get_stock_data(tk, period)
                if df is not None: d[tk] = df['Close']
            if d:
                corr = pd.DataFrame(d).corr()
                st.plotly_chart(px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", range_color=[-1,1]), use_container_width=True)
    else:
        st.warning("2つ以上選択してください")

with t3:
    st.header("📰 関連ニュース (RSS直読み)")
    st.caption("Yahoo Finance (US/英語) と Google News (JP/日本語) から直接取得")
    
    if current_tickers:
        for tk in current_tickers:
            # 表示名を取得 (辞書 or DB)
            name = tk
            if tk in TICKER_NAME_MAP:
                name = TICKER_NAME_MAP[tk]
            else:
                row = w_df[w_df['ticker']==tk]
                if not row.empty: name = row.iloc[0]['note']
            
            with st.expander(f"📡 {name} ({tk}) のニュース", expanded=True):
                news = fetch_rss_news(tk, name)
                if news:
                    for n in news:
                        st.markdown(f"**[{n['title']}]({n['link']})**")
                        st.caption(f"{n['source']} - {n['published']}")
                        st.markdown("---")
                else:
                    st.info("ニュースが見つかりませんでした")
    else:
        st.warning("銘柄を選択してください")

with t4:
    st.header("📋 銘柄DB")
    q = st.text_input("検索", placeholder="Toyota, Bond...")
    df = ticker_df_master
    if q: df = df[df.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)]
    for c in df['Category'].unique():
        with st.expander(c, expanded=False):
            st.dataframe(df[df['Category']==c][['Ticker','Name']], use_container_width=True, hide_index=True)
