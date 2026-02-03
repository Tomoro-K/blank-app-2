import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from newsapi import NewsApiClient
import feedparser
from datetime import datetime, timedelta
import time

# --- 1. 設定 ---
st.set_page_config(page_title="Pro Investor Dashboard v13", layout="wide")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
except:
    st.error("Secrets (Supabase/NewsAPI) が設定されていません。")
    st.stop()

# クライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# ==============================================================================
# 2. 銘柄データマスター (350種以上・完全固定リスト)
# ==============================================================================

# --- 債券・金利 (20) ---
BONDS = [
    {"C": "📉 Bonds", "T": "^TNX", "N": "US 10Y Yield"},
    {"C": "📉 Bonds", "T": "^FVX", "N": "US 5Y Yield"},
    {"C": "📉 Bonds", "T": "^IRX", "N": "US 3 Month Bill"},
    {"C": "📉 Bonds", "T": "^TYX", "N": "US 30Y Yield"},
    {"C": "📉 Bonds", "T": "TLT", "N": "20+ Year Treasury Bond"},
    {"C": "📉 Bonds", "T": "IEF", "N": "7-10 Year Treasury Bond"},
    {"C": "📉 Bonds", "T": "SHY", "N": "1-3 Year Treasury Bond"},
    {"C": "📉 Bonds", "T": "GOVT", "N": "US Treasury Bond ETF"},
    {"C": "📉 Bonds", "T": "SHV", "N": "Short Treasury Bond"},
    {"C": "📉 Bonds", "T": "BIL", "N": "1-3 Month Treasury"},
    {"C": "📉 Bonds", "T": "LQD", "N": "Inv Grade Corporate Bond"},
    {"C": "📉 Bonds", "T": "VCIT", "N": "Interm-Term Corp Bond"},
    {"C": "📉 Bonds", "T": "VCSH", "N": "Short-Term Corp Bond"},
    {"C": "📉 Bonds", "T": "HYG", "N": "High Yield Bond"},
    {"C": "📉 Bonds", "T": "JNK", "N": "High Yield Bond SPDR"},
    {"C": "📉 Bonds", "T": "BKLN", "N": "Senior Loan ETF"},
    {"C": "📉 Bonds", "T": "AGG", "N": "US Aggregate Bond"},
    {"C": "📉 Bonds", "T": "BND", "N": "Total Bond Market"},
    {"C": "📉 Bonds", "T": "BNDX", "N": "Total International Bond"},
    {"C": "📉 Bonds", "T": "TIP", "N": "TIPS (Inflation-Protected)"},
]

# --- 為替 (25) ---
FOREX = [
    {"C": "💱 Forex", "T": "USDJPY=X", "N": "USD/JPY (ドル円)"},
    {"C": "💱 Forex", "T": "EURJPY=X", "N": "EUR/JPY (ユーロ円)"},
    {"C": "💱 Forex", "T": "GBPJPY=X", "N": "GBP/JPY (ポンド円)"},
    {"C": "💱 Forex", "T": "AUDJPY=X", "N": "AUD/JPY (豪ドル円)"},
    {"C": "💱 Forex", "T": "NZDJPY=X", "N": "NZD/JPY (NZドル円)"},
    {"C": "💱 Forex", "T": "CADJPY=X", "N": "CAD/JPY (カナダドル円)"},
    {"C": "💱 Forex", "T": "CHFJPY=X", "N": "CHF/JPY (フラン円)"},
    {"C": "💱 Forex", "T": "EURUSD=X", "N": "EUR/USD (ユーロドル)"},
    {"C": "💱 Forex", "T": "GBPUSD=X", "N": "GBP/USD (ポンドドル)"},
    {"C": "💱 Forex", "T": "AUDUSD=X", "N": "AUD/USD (豪ドル米ドル)"},
    {"C": "💱 Forex", "T": "NZDUSD=X", "N": "NZD/USD (NZドル米ドル)"},
    {"C": "💱 Forex", "T": "USDCAD=X", "N": "USD/CAD (ドルカナダ)"},
    {"C": "💱 Forex", "T": "USDCHF=X", "N": "USD/CHF (ドルフラン)"},
    {"C": "💱 Forex", "T": "CNY=X", "N": "USD/CNY (ドル人民元)"},
    {"C": "💱 Forex", "T": "HKD=X", "N": "USD/HKD (ドル香港ドル)"},
    {"C": "💱 Forex", "T": "SGD=X", "N": "USD/SGD (ドルシンガポールドル)"},
    {"C": "💱 Forex", "T": "INR=X", "N": "USD/INR (ドルルピー)"},
    {"C": "💱 Forex", "T": "MXN=X", "N": "USD/MXN (ドルメキシコペソ)"},
    {"C": "💱 Forex", "T": "BRL=X", "N": "USD/BRL (ドルレアル)"},
    {"C": "💱 Forex", "T": "TRY=X", "N": "USD/TRY (ドルトルコリラ)"},
    {"C": "💱 Forex", "T": "ZAR=X", "N": "USD/ZAR (ドルランド)"},
    {"C": "💱 Forex", "T": "RUB=X", "N": "USD/RUB (ドルルーブル)"},
    {"C": "💱 Forex", "T": "KRW=X", "N": "USD/KRW (ドルウォン)"},
    {"C": "💱 Forex", "T": "TWD=X", "N": "USD/TWD (ドル台湾ドル)"},
    {"C": "💱 Forex", "T": "DX-Y.NYB", "N": "Dollar Index (DXY)"},
]

# --- 米国株: ハイテク・半導体・通信 (60) ---
US_TECH = [
    {"C": "🇺🇸 Tech", "T": "AAPL", "N": "Apple"},
    {"C": "🇺🇸 Tech", "T": "MSFT", "N": "Microsoft"},
    {"C": "🇺🇸 Tech", "T": "NVDA", "N": "NVIDIA"},
    {"C": "🇺🇸 Tech", "T": "GOOGL", "N": "Google (Alphabet)"},
    {"C": "🇺🇸 Tech", "T": "GOOG", "N": "Google (Class C)"},
    {"C": "🇺🇸 Tech", "T": "AMZN", "N": "Amazon"},
    {"C": "🇺🇸 Tech", "T": "META", "N": "Meta Platforms"},
    {"C": "🇺🇸 Tech", "T": "TSLA", "N": "Tesla"},
    {"C": "🇺🇸 Tech", "T": "AVGO", "N": "Broadcom"},
    {"C": "🇺🇸 Tech", "T": "AMD", "N": "AMD"},
    {"C": "🇺🇸 Tech", "T": "INTC", "N": "Intel"},
    {"C": "🇺🇸 Tech", "T": "QCOM", "N": "Qualcomm"},
    {"C": "🇺🇸 Tech", "T": "TXN", "N": "Texas Instruments"},
    {"C": "🇺🇸 Tech", "T": "MU", "N": "Micron Technology"},
    {"C": "🇺🇸 Tech", "T": "AMAT", "N": "Applied Materials"},
    {"C": "🇺🇸 Tech", "T": "LRCX", "N": "Lam Research"},
    {"C": "🇺🇸 Tech", "T": "ADI", "N": "Analog Devices"},
    {"C": "🇺🇸 Tech", "T": "KLAC", "N": "KLA Corp"},
    {"C": "🇺🇸 Tech", "T": "ASML", "N": "ASML Holding"},
    {"C": "🇺🇸 Tech", "T": "TSM", "N": "TSMC"},
    {"C": "🇺🇸 Tech", "T": "ARM", "N": "Arm Holdings"},
    {"C": "🇺🇸 Tech", "T": "ORCL", "N": "Oracle"},
    {"C": "🇺🇸 Tech", "T": "CRM", "N": "Salesforce"},
    {"C": "🇺🇸 Tech", "T": "ADBE", "N": "Adobe"},
    {"C": "🇺🇸 Tech", "T": "CSCO", "N": "Cisco Systems"},
    {"C": "🇺🇸 Tech", "T": "IBM", "N": "IBM"},
    {"C": "🇺🇸 Tech", "T": "NOW", "N": "ServiceNow"},
    {"C": "🇺🇸 Tech", "T": "INTU", "N": "Intuit"},
    {"C": "🇺🇸 Tech", "T": "SAP", "N": "SAP"},
    {"C": "🇺🇸 Tech", "T": "UBER", "N": "Uber Technologies"},
    {"C": "🇺🇸 Tech", "T": "ABNB", "N": "Airbnb"},
    {"C": "🇺🇸 Tech", "T": "BKNG", "N": "Booking Holdings"},
    {"C": "🇺🇸 Tech", "T": "PANW", "N": "Palo Alto Networks"},
    {"C": "🇺🇸 Tech", "T": "CRWD", "N": "CrowdStrike"},
    {"C": "🇺🇸 Tech", "T": "FTNT", "N": "Fortinet"},
    {"C": "🇺🇸 Tech", "T": "ZS", "N": "Zscaler"},
    {"C": "🇺🇸 Tech", "T": "PLTR", "N": "Palantir"},
    {"C": "🇺🇸 Tech", "T": "SNOW", "N": "Snowflake"},
    {"C": "🇺🇸 Tech", "T": "DDOG", "N": "Datadog"},
    {"C": "🇺🇸 Tech", "T": "SQ", "N": "Block (Square)"},
    {"C": "🇺🇸 Tech", "T": "PYPL", "N": "PayPal"},
    {"C": "🇺🇸 Tech", "T": "SHOP", "N": "Shopify"},
    {"C": "🇺🇸 Tech", "T": "COIN", "N": "Coinbase"},
    {"C": "🇺🇸 Tech", "T": "HOOD", "N": "Robinhood"},
    {"C": "🇺🇸 Tech", "T": "RBLX", "N": "Roblox"},
    {"C": "🇺🇸 Tech", "T": "U", "N": "Unity Software"},
    {"C": "🇺🇸 Tech", "T": "NET", "N": "Cloudflare"},
    {"C": "🇺🇸 Tech", "T": "MDB", "N": "MongoDB"},
    {"C": "🇺🇸 Tech", "T": "TEAM", "N": "Atlassian"},
    {"C": "🇺🇸 Tech", "T": "WDAY", "N": "Workday"},
    {"C": "🇺🇸 Tech", "T": "ZM", "N": "Zoom Video"},
    {"C": "🇺🇸 Tech", "T": "DOCU", "N": "DocuSign"},
    {"C": "🇺🇸 Tech", "T": "OKTA", "N": "Okta"},
    {"C": "🇺🇸 Tech", "T": "TWLO", "N": "Twilio"},
    {"C": "🇺🇸 Tech", "T": "SPOT", "N": "Spotify"},
    {"C": "🇺🇸 Tech", "T": "SNAP", "N": "Snap"},
    {"C": "🇺🇸 Tech", "T": "PINS", "N": "Pinterest"},
    {"C": "🇺🇸 Tech", "T": "ROKU", "N": "Roku"},
    {"C": "🇺🇸 Tech", "T": "EA", "N": "Electronic Arts"},
    {"C": "🇺🇸 Tech", "T": "ATVI", "N": "Activision Blizzard"},
]

# --- 米国株: 一般・金融・ヘルスケア (60) ---
US_MAJOR = [
    {"C": "🇺🇸 Major", "T": "JPM", "N": "JPMorgan Chase"},
    {"C": "🇺🇸 Major", "T": "BAC", "N": "Bank of America"},
    {"C": "🇺🇸 Major", "T": "WFC", "N": "Wells Fargo"},
    {"C": "🇺🇸 Major", "T": "C", "N": "Citigroup"},
    {"C": "🇺🇸 Major", "T": "GS", "N": "Goldman Sachs"},
    {"C": "🇺🇸 Major", "T": "MS", "N": "Morgan Stanley"},
    {"C": "🇺🇸 Major", "T": "BLK", "N": "BlackRock"},
    {"C": "🇺🇸 Major", "T": "V", "N": "Visa"},
    {"C": "🇺🇸 Major", "T": "MA", "N": "Mastercard"},
    {"C": "🇺🇸 Major", "T": "AXP", "N": "American Express"},
    {"C": "🇺🇸 Major", "T": "BRK-B", "N": "Berkshire Hathaway"},
    {"C": "🇺🇸 Major", "T": "WMT", "N": "Walmart"},
    {"C": "🇺🇸 Major", "T": "TGT", "N": "Target"},
    {"C": "🇺🇸 Major", "T": "COST", "N": "Costco"},
    {"C": "🇺🇸 Major", "T": "HD", "N": "Home Depot"},
    {"C": "🇺🇸 Major", "T": "LOW", "N": "Lowe's"},
    {"C": "🇺🇸 Major", "T": "PG", "N": "Procter & Gamble"},
    {"C": "🇺🇸 Major", "T": "KO", "N": "Coca-Cola"},
    {"C": "🇺🇸 Major", "T": "PEP", "N": "PepsiCo"},
    {"C": "🇺🇸 Major", "T": "MCD", "N": "McDonald's"},
    {"C": "🇺🇸 Major", "T": "SBUX", "N": "Starbucks"},
    {"C": "🇺🇸 Major", "T": "CMG", "N": "Chipotle"},
    {"C": "🇺🇸 Major", "T": "YUM", "N": "Yum! Brands"},
    {"C": "🇺🇸 Major", "T": "NKE", "N": "Nike"},
    {"C": "🇺🇸 Major", "T": "LULU", "N": "Lululemon"},
    {"C": "🇺🇸 Major", "T": "DIS", "N": "Disney"},
    {"C": "🇺🇸 Major", "T": "CMCSA", "N": "Comcast"},
    {"C": "🇺🇸 Major", "T": "NFLX", "N": "Netflix"},
    {"C": "🇺🇸 Major", "T": "WBD", "N": "Warner Bros. Discovery"},
    {"C": "🇺🇸 Major", "T": "JNJ", "N": "Johnson & Johnson"},
    {"C": "🇺🇸 Major", "T": "LLY", "N": "Eli Lilly"},
    {"C": "🇺🇸 Major", "T": "UNH", "N": "UnitedHealth"},
    {"C": "🇺🇸 Major", "T": "PFE", "N": "Pfizer"},
    {"C": "🇺🇸 Major", "T": "MRK", "N": "Merck"},
    {"C": "🇺🇸 Major", "T": "ABBV", "N": "AbbVie"},
    {"C": "🇺🇸 Major", "T": "AMGN", "N": "Amgen"},
    {"C": "🇺🇸 Major", "T": "GILD", "N": "Gilead Sciences"},
    {"C": "🇺🇸 Major", "T": "CVX", "N": "Chevron"},
    {"C": "🇺🇸 Major", "T": "XOM", "N": "Exxon Mobil"},
    {"C": "🇺🇸 Major", "T": "COP", "N": "ConocoPhillips"},
    {"C": "🇺🇸 Major", "T": "SLB", "N": "Schlumberger"},
    {"C": "🇺🇸 Major", "T": "GE", "N": "General Electric"},
    {"C": "🇺🇸 Major", "T": "CAT", "N": "Caterpillar"},
    {"C": "🇺🇸 Major", "T": "DE", "N": "John Deere"},
    {"C": "🇺🇸 Major", "T": "HON", "N": "Honeywell"},
    {"C": "🇺🇸 Major", "T": "UPS", "N": "UPS"},
    {"C": "🇺🇸 Major", "T": "FDX", "N": "FedEx"},
    {"C": "🇺🇸 Major", "T": "BA", "N": "Boeing"},
    {"C": "🇺🇸 Major", "T": "LMT", "N": "Lockheed Martin"},
    {"C": "🇺🇸 Major", "T": "RTX", "N": "Raytheon"},
    {"C": "🇺🇸 Major", "T": "GD", "N": "General Dynamics"},
    {"C": "🇺🇸 Major", "T": "NOC", "N": "Northrop Grumman"},
    {"C": "🇺🇸 Major", "T": "MMM", "N": "3M"},
    {"C": "🇺🇸 Major", "T": "F", "N": "Ford Motor"},
    {"C": "🇺🇸 Major", "T": "GM", "N": "General Motors"},
    {"C": "🇺🇸 Major", "T": "TM", "N": "Toyota Motor (ADR)"},
    {"C": "🇺🇸 Major", "T": "HMC", "N": "Honda Motor (ADR)"},
    {"C": "🇺🇸 Major", "T": "T", "N": "AT&T"},
    {"C": "🇺🇸 Major", "T": "VZ", "N": "Verizon"},
    {"C": "🇺🇸 Major", "T": "TMUS", "N": "T-Mobile US"},
]

# --- 日本株 (80) ---
JAPAN = [
    {"C": "🇯🇵 Japan", "T": "7203.T", "N": "トヨタ自動車"},
    {"C": "🇯🇵 Japan", "T": "6758.T", "N": "ソニーグループ"},
    {"C": "🇯🇵 Japan", "T": "9984.T", "N": "ソフトバンクグループ"},
    {"C": "🇯🇵 Japan", "T": "9434.T", "N": "ソフトバンク"},
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
    {"C": "🇯🇵 Japan", "T": "7202.T", "N": "いすゞ自動車"},
    {"C": "🇯🇵 Japan", "T": "7269.T", "N": "スズキ"},
    {"C": "🇯🇵 Japan", "T": "9983.T", "N": "ファーストリテイリング"},
    {"C": "🇯🇵 Japan", "T": "7974.T", "N": "任天堂"},
    {"C": "🇯🇵 Japan", "T": "9766.T", "N": "コナミグループ"},
    {"C": "🇯🇵 Japan", "T": "9684.T", "N": "スクウェア・エニックス"},
    {"C": "🇯🇵 Japan", "T": "7832.T", "N": "バンダイナムコ"},
    {"C": "🇯🇵 Japan", "T": "9613.T", "N": "NTTデータ"},
    {"C": "🇯🇵 Japan", "T": "8001.T", "N": "伊藤忠商事"},
    {"C": "🇯🇵 Japan", "T": "8058.T", "N": "三菱商事"},
    {"C": "🇯🇵 Japan", "T": "8031.T", "N": "三井物産"},
    {"C": "🇯🇵 Japan", "T": "8002.T", "N": "丸紅"},
    {"C": "🇯🇵 Japan", "T": "8053.T", "N": "住友商事"},
    {"C": "🇯🇵 Japan", "T": "2768.T", "N": "双日"},
    {"C": "🇯🇵 Japan", "T": "8015.T", "N": "豊田通商"},
    {"C": "🇯🇵 Japan", "T": "6098.T", "N": "リクルートホールディングス"},
    {"C": "🇯🇵 Japan", "T": "4661.T", "N": "オリエンタルランド"},
    {"C": "🇯🇵 Japan", "T": "2914.T", "N": "日本たばこ産業 (JT)"},
    {"C": "🇯🇵 Japan", "T": "4502.T", "N": "武田薬品工業"},
    {"C": "🇯🇵 Japan", "T": "4519.T", "N": "中外製薬"},
    {"C": "🇯🇵 Japan", "T": "4568.T", "N": "第一三共"},
    {"C": "🇯🇵 Japan", "T": "4503.T", "N": "アステラス製薬"},
    {"C": "🇯🇵 Japan", "T": "4523.T", "N": "エーザイ"},
    {"C": "🇯🇵 Japan", "T": "4911.T", "N": "資生堂"},
    {"C": "🇯🇵 Japan", "T": "4452.T", "N": "花王"},
    {"C": "🇯🇵 Japan", "T": "8766.T", "N": "東京海上ホールディングス"},
    {"C": "🇯🇵 Japan", "T": "8725.T", "N": "MS&AD"},
    {"C": "🇯🇵 Japan", "T": "8630.T", "N": "SOMPO"},
    {"C": "🇯🇵 Japan", "T": "8801.T", "N": "三井不動産"},
    {"C": "🇯🇵 Japan", "T": "8802.T", "N": "三菱地所"},
    {"C": "🇯🇵 Japan", "T": "1925.T", "N": "大和ハウス工業"},
    {"C": "🇯🇵 Japan", "T": "1928.T", "N": "積水ハウス"},
    {"C": "🇯🇵 Japan", "T": "9020.T", "N": "JR東日本"},
    {"C": "🇯🇵 Japan", "T": "9022.T", "N": "JR東海"},
    {"C": "🇯🇵 Japan", "T": "9021.T", "N": "JR西日本"},
    {"C": "🇯🇵 Japan", "T": "9201.T", "N": "日本航空 (JAL)"},
    {"C": "🇯🇵 Japan", "T": "9202.T", "N": "ANAホールディングス"},
    {"C": "🇯🇵 Japan", "T": "9101.T", "N": "日本郵船"},
    {"C": "🇯🇵 Japan", "T": "9104.T", "N": "商船三井"},
    {"C": "🇯🇵 Japan", "T": "9107.T", "N": "川崎汽船"},
    {"C": "🇯🇵 Japan", "T": "1605.T", "N": "INPEX"},
    {"C": "🇯🇵 Japan", "T": "5020.T", "N": "ENEOS"},
    {"C": "🇯🇵 Japan", "T": "5401.T", "N": "日本製鉄"},
    {"C": "🇯🇵 Japan", "T": "5411.T", "N": "JFE"},
    {"C": "🇯🇵 Japan", "T": "3402.T", "N": "東レ"},
    {"C": "🇯🇵 Japan", "T": "3407.T", "N": "旭化成"},
    {"C": "🇯🇵 Japan", "T": "6367.T", "N": "ダイキン工業"},
    {"C": "🇯🇵 Japan", "T": "2802.T", "N": "味の素"},
]

# --- ETF / 指数 (60) ---
ETF = [
    {"C": "📊 ETF", "T": "^GSPC", "N": "S&P 500 Index"},
    {"C": "📊 ETF", "T": "^DJI", "N": "Dow Jones Industrial Average"},
    {"C": "📊 ETF", "T": "^IXIC", "N": "NASDAQ Composite"},
    {"C": "📊 ETF", "T": "^NDX", "N": "NASDAQ 100"},
    {"C": "📊 ETF", "T": "^RUT", "N": "Russell 2000"},
    {"C": "📊 ETF", "T": "^VIX", "N": "CBOE Volatility Index"},
    {"C": "📊 ETF", "T": "^N225", "N": "Nikkei 225"},
    {"C": "📊 ETF", "T": "^STOXX50E", "N": "Euro Stoxx 50"},
    {"C": "📊 ETF", "T": "^FTSE", "N": "FTSE 100 (UK)"},
    {"C": "📊 ETF", "T": "^GDAXI", "N": "DAX (Germany)"},
    {"C": "📊 ETF", "T": "^FCHI", "N": "CAC 40 (France)"},
    {"C": "📊 ETF", "T": "^HSI", "N": "Hang Seng Index"},
    {"C": "📊 ETF", "T": "000001.SS", "N": "SSE Composite (China)"},
    {"C": "📊 ETF", "T": "^BSESN", "N": "BSE SENSEX (India)"},
    {"C": "📊 ETF", "T": "VOO", "N": "Vanguard S&P 500 ETF"},
    {"C": "📊 ETF", "T": "IVV", "N": "iShares Core S&P 500 ETF"},
    {"C": "📊 ETF", "T": "SPY", "N": "SPDR S&P 500 ETF Trust"},
    {"C": "📊 ETF", "T": "VTI", "N": "Vanguard Total Stock Market"},
    {"C": "📊 ETF", "T": "VT", "N": "Vanguard Total World Stock"},
    {"C": "📊 ETF", "T": "QQQ", "N": "Invesco QQQ Trust"},
    {"C": "📊 ETF", "T": "DIA", "N": "SPDR Dow Jones Industrial Average"},
    {"C": "📊 ETF", "T": "IWM", "N": "iShares Russell 2000 ETF"},
    {"C": "📊 ETF", "T": "VTV", "N": "Vanguard Value ETF"},
    {"C": "📊 ETF", "T": "VUG", "N": "Vanguard Growth ETF"},
    {"C": "📊 ETF", "T": "VYM", "N": "Vanguard High Dividend Yield"},
    {"C": "📊 ETF", "T": "VIG", "N": "Vanguard Dividend Appreciation"},
    {"C": "📊 ETF", "T": "SPYD", "N": "SPDR Portfolio S&P 500 High Dividend"},
    {"C": "📊 ETF", "T": "HDV", "N": "iShares Core High Dividend"},
    {"C": "📊 ETF", "T": "DVY", "N": "iShares Select Dividend"},
    {"C": "📊 ETF", "T": "XLK", "N": "Technology Select Sector SPDR"},
    {"C": "📊 ETF", "T": "XLF", "N": "Financial Select Sector SPDR"},
    {"C": "📊 ETF", "T": "XLV", "N": "Health Care Select Sector SPDR"},
    {"C": "📊 ETF", "T": "XLE", "N": "Energy Select Sector SPDR"},
    {"C": "📊 ETF", "T": "XLI", "N": "Industrial Select Sector SPDR"},
    {"C": "📊 ETF", "T": "XLP", "N": "Consumer Staples Select Sector"},
    {"C": "📊 ETF", "T": "XLY", "N": "Consumer Discret Select Sector"},
    {"C": "📊 ETF", "T": "XLC", "N": "Communication Services Select"},
    {"C": "📊 ETF", "T": "XLB", "N": "Materials Select Sector SPDR"},
    {"C": "📊 ETF", "T": "XLU", "N": "Utilities Select Sector SPDR"},
    {"C": "📊 ETF", "T": "XLRE", "N": "Real Estate Select Sector SPDR"},
    {"C": "📊 ETF", "T": "SMH", "N": "VanEck Semiconductor ETF"},
    {"C": "📊 ETF", "T": "SOXX", "N": "iShares Semiconductor ETF"},
    {"C": "📊 ETF", "T": "ARKK", "N": "ARK Innovation ETF"},
    {"C": "📊 ETF", "T": "GLD", "N": "SPDR Gold Shares"},
    {"C": "📊 ETF", "T": "IAU", "N": "iShares Gold Trust"},
    {"C": "📊 ETF", "T": "SLV", "N": "iShares Silver Trust"},
    {"C": "📊 ETF", "T": "USO", "N": "United States Oil Fund"},
    {"C": "📊 ETF", "T": "VEA", "N": "Vanguard FTSE Developed Markets"},
    {"C": "📊 ETF", "T": "VWO", "N": "Vanguard FTSE Emerging Markets"},
    {"C": "📊 ETF", "T": "EEM", "N": "iShares MSCI Emerging Markets"},
    {"C": "📊 ETF", "T": "EFA", "N": "iShares MSCI EAFE ETF"},
    {"C": "📊 ETF", "T": "EWJ", "N": "iShares MSCI Japan ETF"},
    {"C": "📊 ETF", "T": "FXI", "N": "iShares China Large-Cap ETF"},
    {"C": "📊 ETF", "T": "INDA", "N": "iShares MSCI India ETF"},
    {"C": "📊 ETF", "T": "EPI", "N": "WisdomTree India Earnings"},
    {"C": "📊 ETF", "T": "VNQ", "N": "Vanguard Real Estate ETF"},
    {"C": "📊 ETF", "T": "AGG", "N": "iShares Core US Aggregate Bond"},
    {"C": "📊 ETF", "T": "BND", "N": "Vanguard Total Bond Market"},
    {"C": "📊 ETF", "T": "LQD", "N": "iShares iBoxx Investment Grade"},
    {"C": "📊 ETF", "T": "HYG", "N": "iShares iBoxx High Yield"},
]

# --- 暗号資産 (25) ---
CRYPTO = [
    {"C": "🪙 Crypto", "T": "BTC-USD", "N": "Bitcoin"},
    {"C": "🪙 Crypto", "T": "ETH-USD", "N": "Ethereum"},
    {"C": "🪙 Crypto", "T": "USDT-USD", "N": "Tether"},
    {"C": "🪙 Crypto", "T": "BNB-USD", "N": "BNB"},
    {"C": "🪙 Crypto", "T": "XRP-USD", "N": "XRP"},
    {"C": "🪙 Crypto", "T": "SOL-USD", "N": "Solana"},
    {"C": "🪙 Crypto", "T": "USDC-USD", "N": "USDC"},
    {"C": "🪙 Crypto", "T": "ADA-USD", "N": "Cardano"},
    {"C": "🪙 Crypto", "T": "AVAX-USD", "N": "Avalanche"},
    {"C": "🪙 Crypto", "T": "DOGE-USD", "N": "Dogecoin"},
    {"C": "🪙 Crypto", "T": "TRX-USD", "N": "TRON"},
    {"C": "🪙 Crypto", "T": "DOT-USD", "N": "Polkadot"},
    {"C": "🪙 Crypto", "T": "LINK-USD", "N": "Chainlink"},
    {"C": "🪙 Crypto", "T": "MATIC-USD", "N": "Polygon"},
    {"C": "🪙 Crypto", "T": "WBTC-USD", "N": "Wrapped Bitcoin"},
    {"C": "🪙 Crypto", "T": "LTC-USD", "N": "Litecoin"},
    {"C": "🪙 Crypto", "T": "SHIB-USD", "N": "Shiba Inu"},
    {"C": "🪙 Crypto", "T": "DAI-USD", "N": "Dai"},
    {"C": "🪙 Crypto", "T": "BCH-USD", "N": "Bitcoin Cash"},
    {"C": "🪙 Crypto", "T": "UNI7083-USD", "N": "Uniswap"},
    {"C": "🪙 Crypto", "T": "ATOM-USD", "N": "Cosmos"},
    {"C": "🪙 Crypto", "T": "XLM-USD", "N": "Stellar"},
    {"C": "🪙 Crypto", "T": "XMR-USD", "N": "Monero"},
    {"C": "🪙 Crypto", "T": "ETC-USD", "N": "Ethereum Classic"},
    {"C": "🪙 Crypto", "T": "FIL-USD", "N": "Filecoin"},
]

# --- 欧州・その他 (40) ---
GLOBAL = [
    {"C": "🇪🇺 Global", "T": "NESN.SW", "N": "Nestle (Swiss)"},
    {"C": "🇪🇺 Global", "T": "ROG.SW", "N": "Roche (Swiss)"},
    {"C": "🇪🇺 Global", "T": "NOVN.SW", "N": "Novartis (Swiss)"},
    {"C": "🇪🇺 Global", "T": "MC.PA", "N": "LVMH (France)"},
    {"C": "🇪🇺 Global", "T": "OR.PA", "N": "L'Oreal (France)"},
    {"C": "🇪🇺 Global", "T": "RMS.PA", "N": "Hermes (France)"},
    {"C": "🇪🇺 Global", "T": "TTE.PA", "N": "TotalEnergies (France)"},
    {"C": "🇪🇺 Global", "T": "SAN.PA", "N": "Sanofi (France)"},
    {"C": "🇪🇺 Global", "T": "AIR.PA", "N": "Airbus (France)"},
    {"C": "🇪🇺 Global", "T": "ASML.AS", "N": "ASML (Netherlands)"},
    {"C": "🇪🇺 Global", "T": "SIE.DE", "N": "Siemens (Germany)"},
    {"C": "🇪🇺 Global", "T": "SAP.DE", "N": "SAP (Germany)"},
    {"C": "🇪🇺 Global", "T": "DTE.DE", "N": "Deutsche Telekom (Germany)"},
    {"C": "🇪🇺 Global", "T": "ALV.DE", "N": "Allianz (Germany)"},
    {"C": "🇪🇺 Global", "T": "VOW3.DE", "N": "Volkswagen (Germany)"},
    {"C": "🇪🇺 Global", "T": "MBG.DE", "N": "Mercedes-Benz (Germany)"},
    {"C": "🇪🇺 Global", "T": "BMW.DE", "N": "BMW (Germany)"},
    {"C": "🇪🇺 Global", "T": "AZN.L", "N": "AstraZeneca (UK)"},
    {"C": "🇪🇺 Global", "T": "SHEL.L", "N": "Shell (UK)"},
    {"C": "🇪🇺 Global", "T": "HSBA.L", "N": "HSBC (UK)"},
    {"C": "🇪🇺 Global", "T": "ULVR.L", "N": "Unilever (UK)"},
    {"C": "🇪🇺 Global", "T": "BP.L", "N": "BP (UK)"},
    {"C": "🇪🇺 Global", "T": "RIO.L", "N": "Rio Tinto (UK)"},
    {"C": "🇪🇺 Global", "T": "GSK.L", "N": "GSK (UK)"},
    {"C": "🇪🇺 Global", "T": "005930.KS", "N": "Samsung Electronics (Korea)"},
    {"C": "🇪🇺 Global", "T": "000660.KS", "N": "SK Hynix (Korea)"},
    {"C": "🇪🇺 Global", "T": "2330.TW", "N": "TSMC (Taiwan)"},
    {"C": "🇪🇺 Global", "T": "BABA", "N": "Alibaba (China/ADR)"},
    {"C": "🇪🇺 Global", "T": "PDD", "N": "PDD Holdings (China/ADR)"},
    {"C": "🇪🇺 Global", "T": "JD", "N": "JD.com (China/ADR)"},
    {"C": "🇪🇺 Global", "T": "BIDU", "N": "Baidu (China/ADR)"},
    {"C": "🇪🇺 Global", "T": "NIO", "N": "NIO (China/ADR)"},
    {"C": "🇪🇺 Global", "T": "INFY", "N": "Infosys (India/ADR)"},
    {"C": "🇪🇺 Global", "T": "HDB", "N": "HDFC Bank (India/ADR)"},
    {"C": "🇪🇺 Global", "T": "VALE", "N": "Vale (Brazil/ADR)"},
    {"C": "🇪🇺 Global", "T": "PBR", "N": "Petrobras (Brazil/ADR)"},
    {"C": "🇪🇺 Global", "T": "RY", "N": "Royal Bank of Canada"},
    {"C": "🇪🇺 Global", "T": "TD", "N": "TD Bank (Canada)"},
    {"C": "🇪🇺 Global", "T": "SHOP", "N": "Shopify (Canada)"},
]

# リスト結合 (合計350銘柄以上)
TICKER_DATA_RAW = BONDS + FOREX + US_TECH + US_MAJOR + JAPAN + ETF + CRYPTO + GLOBAL
ticker_df_master = pd.DataFrame(TICKER_DATA_RAW).rename(columns={"C": "Category", "T": "Ticker", "N": "Name"})
TICKER_NAME_MAP = {item['T']: item['N'] for item in TICKER_DATA_RAW}

# --- 3. 関数群 (データ取得) ---

def calculate_technicals(df):
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
    return df

@st.cache_data(ttl=300)
def get_stock_data(ticker, period_key):
    if not ticker: return None, None, None
    p_map = {
        "1日": "1d", "1週間": "5d", "1ヶ月": "1mo", "3ヶ月": "3mo",
        "6ヶ月": "6mo", "1年": "1y", "3年": "3y", "5年": "5y",
        "10年": "10y", "全期間": "max"
    }
    i_map = {"1日": "15m", "1週間": "60m"}
    yf_p = p_map.get(period_key, "1y")
    yf_i = i_map.get(period_key, "1d")
    
    try:
        stock = yf.Ticker(ticker)
        if period_key == "3年":
            start = datetime.now() - timedelta(days=365*3)
            df = stock.history(start=start, interval=yf_i)
        else:
            df = stock.history(period=yf_p, interval=yf_i)
            
        if df.empty: return None, None, None
        df = calculate_technicals(df)
        
        fin_df = pd.DataFrame()
        try: fin_df = stock.financials
        except: pass
        
        return df, fin_df, stock.info
    except:
        return None, None, None

def clean_search_term(text):
    if not text: return ""
    text = text.replace('（', '(').split('(')[0].strip()
    stopwords = ["Inc", "Corp", "Corporation", "Ltd", "Limited", "Holdings", "Group", "Company"]
    words = text.split()
    cleaned = [w for w in words if w.strip(',.') not in stopwords]
    return " ".join(cleaned)

# --- ニュース取得ロジック (Hybrid: Yahoo RSS + NewsAPI) ---
@st.cache_data(ttl=600)
def fetch_news_hybrid(tickers):
    """
    1. NewsAPIでキーワード検索 (全体的なニュース)
    2. Yahoo Finance RSSでTicker指定 (銘柄特化ニュース)
    3. 両方を結合して返す (最強の安定性)
    """
    if not tickers: return []
    
    articles = []
    seen_links = set()
    
    target_tickers = tickers[:5] # 上位5つ
    
    # --- A. NewsAPI (Keywords) ---
    try:
        search_keywords = []
        for t in target_tickers:
            name = TICKER_NAME_MAP.get(t, t)
            clean = clean_search_term(name)
            if len(clean) >= 2: search_keywords.append(clean)
            
        unique_keywords = list(set(search_keywords))
        if unique_keywords:
            query = " OR ".join(unique_keywords)
            # NewsAPI呼び出し
            api_res = newsapi.get_everything(q=query, language='en', sort_by='publishedAt', page_size=20)
            for a in api_res.get('articles', []):
                if a['url'] not in seen_links:
                    articles.append({
                        "title": a['title'],
                        "link": a['url'],
                        "published": a['publishedAt'][:10],
                        "source": f"NewsAPI ({a['source']['name']})"
                    })
                    seen_links.add(a['url'])
    except:
        pass # NewsAPIがダメでも次へ

    # --- B. Yahoo Finance RSS (Ticker Direct) ---
    # これはAPIキー不要で、Tickerさえ合っていれば確実に出る
    for t in target_tickers:
        try:
            # RSS URL (Yahoo Finance US)
            rss_url = f"https://finance.yahoo.com/rss/headline?s={t}"
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:5]: # 各5件
                if entry.link not in seen_links:
                    pub_date = entry.published[:16] if 'published' in entry else "Recent"
                    articles.append({
                        "title": entry.title,
                        "link": entry.link,
                        "published": pub_date,
                        "source": f"Yahoo RSS ({t})"
                    })
                    seen_links.add(entry.link)
        except:
            pass

    return articles

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
st.title("📈 Pro Investor Dashboard v13 (Hybrid Stable)")

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
t1, t2, t3, t4 = st.tabs(["📊 チャート", "🔢 相関", "📰 ニュース (Hybrid)", "📋 DB"])

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
    st.header("📰 関連ニュース (Yahoo RSS + NewsAPI)")
    st.caption("APIキーを使った検索と、銘柄コード直結のRSSフィードを併用して最大限に情報を収集します")
    
    if current_tickers:
        with st.spinner("ニュース収集中..."):
            arts = fetch_news_hybrid(current_tickers)
            
        if arts:
            for n in arts:
                with st.container(border=True):
                    st.markdown(f"**[{n['title']}]({n['link']})**")
                    st.caption(f"{n['source']} - {n['published']}")
        else:
            st.info("ニュースが見つかりませんでした")
    else:
        st.warning("銘柄を選択してください")

with t4:
    st.header("📋 銘柄DB (350+)")
    q = st.text_input("検索", placeholder="Toyota, Bond...")
    df = ticker_df_master
    if q: df = df[df.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)]
    for c in df['Category'].unique():
        with st.expander(c, expanded=False):
            st.dataframe(df[df['Category']==c][['Ticker','Name']], use_container_width=True, hide_index=True)
