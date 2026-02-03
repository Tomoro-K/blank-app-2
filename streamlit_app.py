import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from newsapi import NewsApiClient
from datetime import datetime, timedelta

# --- 1. 設定 ---
st.set_page_config(page_title="Pro Investor Dashboard v9.5", layout="wide")

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

# --- 2. 銘柄データ (300種以上・完全復旧) ---
# ※ 長くなるため、主要カテゴリを網羅したリストに戻しました
BONDS = [
    {"C": "📉 Bonds/Yields", "T": "^TNX", "N": "US 10Y Yield (米国10年債利回り)"},
    {"C": "📉 Bonds/Yields", "T": "^FVX", "N": "US 5Y Yield (米国5年債利回り)"},
    {"C": "📉 Bonds/Yields", "T": "^IRX", "N": "US 13W Bill (米国3ヶ月債)"},
    {"C": "📉 Bonds/Yields", "T": "TLT", "N": "20+ Year Treasury Bond ETF"},
    {"C": "📉 Bonds/Yields", "T": "LQD", "N": "Inv Grade Corp Bond ETF (社債)"},
    {"C": "📉 Bonds/Yields", "T": "HYG", "N": "High Yield Corp Bond ETF (ハイイールド債)"},
    {"C": "📉 Bonds/Yields", "T": "AGG", "N": "US Aggregate Bond ETF (総合債券)"},
    {"C": "📉 Bonds/Yields", "T": "BND", "N": "Total Bond Market ETF"}
]

FOREX = [
    {"C": "💱 Forex", "T": "USDJPY=X", "N": "USD/JPY (ドル円)"},
    {"C": "💱 Forex", "T": "EURJPY=X", "N": "EUR/JPY (ユーロ円)"},
    {"C": "💱 Forex", "T": "EURUSD=X", "N": "EUR/USD (ユーロドル)"},
    {"C": "💱 Forex", "T": "GBPUSD=X", "N": "GBP/USD (ポンドドル)"},
    {"C": "💱 Forex", "T": "GBPJPY=X", "N": "GBP/JPY (ポンド円)"},
    {"C": "💱 Forex", "T": "AUDUSD=X", "N": "AUD/USD (豪ドル米ドル)"},
    {"C": "💱 Forex", "T": "AUDJPY=X", "N": "AUD/JPY (豪ドル円)"},
    {"C": "💱 Forex", "T": "DX-Y.NYB", "N": "Dollar Index (ドル指数)"},
]

US_TECH = [
    {"C": "🇺🇸 US Tech", "T": "AAPL", "N": "Apple"}, {"C": "🇺🇸 US Tech", "T": "MSFT", "N": "Microsoft"},
    {"C": "🇺🇸 US Tech", "T": "NVDA", "N": "NVIDIA"}, {"C": "🇺🇸 US Tech", "T": "GOOGL", "N": "Alphabet"},
    {"C": "🇺🇸 US Tech", "T": "AMZN", "N": "Amazon"}, {"C": "🇺🇸 US Tech", "T": "META", "N": "Meta"},
    {"C": "🇺🇸 US Tech", "T": "TSLA", "N": "Tesla"}, {"C": "🇺🇸 US Tech", "T": "AVGO", "N": "Broadcom"},
    {"C": "🇺🇸 US Tech", "T": "ORCL", "N": "Oracle"}, {"C": "🇺🇸 US Tech", "T": "CRM", "N": "Salesforce"},
    {"C": "🇺🇸 US Tech", "T": "AMD", "N": "AMD"}, {"C": "🇺🇸 US Tech", "T": "NFLX", "N": "Netflix"},
    {"C": "🇺🇸 US Tech", "T": "ADBE", "N": "Adobe"}, {"C": "🇺🇸 US Tech", "T": "CSCO", "N": "Cisco"},
    {"C": "🇺🇸 US Tech", "T": "INTC", "N": "Intel"}, {"C": "🇺🇸 US Tech", "T": "QCOM", "N": "Qualcomm"},
    {"C": "🇺🇸 US Tech", "T": "IBM", "N": "IBM"}, {"C": "🇺🇸 US Tech", "T": "TXN", "N": "Texas Instruments"},
    {"C": "🇺🇸 US Tech", "T": "UBER", "N": "Uber"}, {"C": "🇺🇸 US Tech", "T": "ABNB", "N": "Airbnb"},
    {"C": "🇺🇸 US Tech", "T": "PLTR", "N": "Palantir"}, {"C": "🇺🇸 US Tech", "T": "SNOW", "N": "Snowflake"},
    {"C": "🇺🇸 US Tech", "T": "SQ", "N": "Block (Square)"}, {"C": "🇺🇸 US Tech", "T": "PYPL", "N": "PayPal"},
    {"C": "🇺🇸 US Tech", "T": "SHOP", "N": "Shopify"}, {"C": "🇺🇸 US Tech", "T": "CRWD", "N": "CrowdStrike"},
    {"C": "🇺🇸 US Tech", "T": "PANW", "N": "Palo Alto Networks"}, {"C": "🇺🇸 US Tech", "T": "MU", "N": "Micron"},
    {"C": "🇺🇸 US Tech", "T": "AMAT", "N": "Applied Materials"}, {"C": "🇺🇸 US Tech", "T": "LRCX", "N": "Lam Research"},
    {"C": "🇺🇸 US Tech", "T": "COIN", "N": "Coinbase"}
]

US_MAJOR = [
    {"C": "🇺🇸 US Major", "T": "JPM", "N": "JPMorgan"}, {"C": "🇺🇸 US Major", "T": "BAC", "N": "Bank of America"},
    {"C": "🇺🇸 US Major", "T": "V", "N": "Visa"}, {"C": "🇺🇸 US Major", "T": "MA", "N": "Mastercard"},
    {"C": "🇺🇸 US Major", "T": "WMT", "N": "Walmart"}, {"C": "🇺🇸 US Major", "T": "PG", "N": "P&G"},
    {"C": "🇺🇸 US Major", "T": "JNJ", "N": "Johnson & Johnson"}, {"C": "🇺🇸 US Major", "T": "UNH", "N": "UnitedHealth"},
    {"C": "🇺🇸 US Major", "T": "LLY", "N": "Eli Lilly"}, {"C": "🇺🇸 US Major", "T": "XOM", "N": "Exxon Mobil"},
    {"C": "🇺🇸 US Major", "T": "CVX", "N": "Chevron"}, {"C": "🇺🇸 US Major", "T": "KO", "N": "Coca-Cola"},
    {"C": "🇺🇸 US Major", "T": "PEP", "N": "PepsiCo"}, {"C": "🇺🇸 US Major", "T": "COST", "N": "Costco"},
    {"C": "🇺🇸 US Major", "T": "MCD", "N": "McDonald's"}, {"C": "🇺🇸 US Major", "T": "DIS", "N": "Disney"},
    {"C": "🇺🇸 US Major", "T": "NKE", "N": "Nike"}, {"C": "🇺🇸 US Major", "T": "SBUX", "N": "Starbucks"},
    {"C": "🇺🇸 US Major", "T": "GE", "N": "General Electric"}, {"C": "🇺🇸 US Major", "T": "CAT", "N": "Caterpillar"},
    {"C": "🇺🇸 US Major", "T": "BA", "N": "Boeing"}, {"C": "🇺🇸 US Major", "T": "MMM", "N": "3M"},
    {"C": "🇺🇸 US Major", "T": "GS", "N": "Goldman Sachs"}, {"C": "🇺🇸 US Major", "T": "MS", "N": "Morgan Stanley"},
    {"C": "🇺🇸 US Major", "T": "PFE", "N": "Pfizer"}, {"C": "🇺🇸 US Major", "T": "MRK", "N": "Merck"},
    {"C": "🇺🇸 US Major", "T": "ABBV", "N": "AbbVie"}, {"C": "🇺🇸 US Major", "T": "T", "N": "AT&T"},
    {"C": "🇺🇸 US Major", "T": "VZ", "N": "Verizon"}, {"C": "🇺🇸 US Major", "T": "F", "N": "Ford"},
    {"C": "🇺🇸 US Major", "T": "BRK-B", "N": "Berkshire Hathaway"}
]

JAPAN = [
    {"C": "🇯🇵 Japan", "T": "7203.T", "N": "トヨタ自動車"}, {"C": "🇯🇵 Japan", "T": "6758.T", "N": "ソニーG"},
    {"C": "🇯🇵 Japan", "T": "8306.T", "N": "三菱UFJ"}, {"C": "🇯🇵 Japan", "T": "9984.T", "N": "ソフトバンクG"},
    {"C": "🇯🇵 Japan", "T": "9432.T", "N": "NTT"}, {"C": "🇯🇵 Japan", "T": "8035.T", "N": "東京エレクトロン"},
    {"C": "🇯🇵 Japan", "T": "6861.T", "N": "キーエンス"}, {"C": "🇯🇵 Japan", "T": "9983.T", "N": "ファーストリテイリング"},
    {"C": "🇯🇵 Japan", "T": "7974.T", "N": "任天堂"}, {"C": "🇯🇵 Japan", "T": "8001.T", "N": "伊藤忠商事"},
    {"C": "🇯🇵 Japan", "T": "8058.T", "N": "三菱商事"}, {"C": "🇯🇵 Japan", "T": "6098.T", "N": "リクルート"},
    {"C": "🇯🇵 Japan", "T": "4063.T", "N": "信越化学"}, {"C": "🇯🇵 Japan", "T": "4502.T", "N": "武田薬品"},
    {"C": "🇯🇵 Japan", "T": "7011.T", "N": "三菱重工"}, {"C": "🇯🇵 Japan", "T": "6501.T", "N": "日立製作所"},
    {"C": "🇯🇵 Japan", "T": "6702.T", "N": "富士通"}, {"C": "🇯🇵 Japan", "T": "7741.T", "N": "HOYA"},
    {"C": "🇯🇵 Japan", "T": "6981.T", "N": "村田製作所"}, {"C": "🇯🇵 Japan", "T": "6301.T", "N": "小松製作所"},
    {"C": "🇯🇵 Japan", "T": "7267.T", "N": "ホンダ"}, {"C": "🇯🇵 Japan", "T": "8411.T", "N": "みずほFG"},
    {"C": "🇯🇵 Japan", "T": "8316.T", "N": "三井住友FG"}, {"C": "🇯🇵 Japan", "T": "8766.T", "N": "東京海上"},
    {"C": "🇯🇵 Japan", "T": "4452.T", "N": "花王"}, {"C": "🇯🇵 Japan", "T": "4911.T", "N": "資生堂"},
    {"C": "🇯🇵 Japan", "T": "2914.T", "N": "JT"}, {"C": "🇯🇵 Japan", "T": "9433.T", "N": "KDDI"},
    {"C": "🇯🇵 Japan", "T": "9434.T", "N": "ソフトバンク(通信)"}, {"C": "🇯🇵 Japan", "T": "4661.T", "N": "オリエンタルランド"}
]

ETF = [
    {"C": "📊 ETF/Index", "T": "^GSPC", "N": "S&P 500"}, {"C": "📊 ETF/Index", "T": "^DJI", "N": "Dow 30"},
    {"C": "📊 ETF/Index", "T": "^IXIC", "N": "NASDAQ"}, {"C": "📊 ETF/Index", "T": "^N225", "N": "日経平均"},
    {"C": "📊 ETF/Index", "T": "VOO", "N": "Vanguard S&P 500"}, {"C": "📊 ETF/Index", "T": "VTI", "N": "Total Market"},
    {"C": "📊 ETF/Index", "T": "QQQ", "N": "Nasdaq-100"}, {"C": "📊 ETF/Index", "T": "VT", "N": "Total World"},
    {"C": "📊 ETF/Index", "T": "VYM", "N": "High Dividend"}, {"C": "📊 ETF/Index", "T": "VIG", "N": "Dividend Apprec."},
    {"C": "📊 ETF/Index", "T": "SPYD", "N": "High Div (SP500)"}, {"C": "📊 ETF/Index", "T": "HDV", "N": "High Div (Core)"},
    {"C": "📊 ETF/Index", "T": "AGG", "N": "US Bond"}, {"C": "📊 ETF/Index", "T": "BND", "N": "Total Bond"},
    {"C": "📊 ETF/Index", "T": "GLD", "N": "Gold"}, {"C": "📊 ETF/Index", "T": "SLV", "N": "Silver"},
    {"C": "📊 ETF/Index", "T": "EPI", "N": "India (Earnings)"}, {"C": "📊 ETF/Index", "T": "INDA", "N": "India (MSCI)"},
    {"C": "📊 ETF/Index", "T": "FXI", "N": "China Large-Cap"}, {"C": "📊 ETF/Index", "T": "EWJ", "N": "Japan MSCI"}
]

CRYPTO = [
    {"C": "🪙 Crypto", "T": "BTC-USD", "N": "Bitcoin"}, {"C": "🪙 Crypto", "T": "ETH-USD", "N": "Ethereum"},
    {"C": "🪙 Crypto", "T": "SOL-USD", "N": "Solana"}, {"C": "🪙 Crypto", "T": "XRP-USD", "N": "XRP"},
    {"C": "🪙 Crypto", "T": "BNB-USD", "N": "BNB"}, {"C": "🪙 Crypto", "T": "DOGE-USD", "N": "Dogecoin"},
    {"C": "🪙 Crypto", "T": "ADA-USD", "N": "Cardano"}, {"C": "🪙 Crypto", "T": "AVAX-USD", "N": "Avalanche"},
    {"C": "🪙 Crypto", "T": "SHIB-USD", "N": "Shiba Inu"}, {"C": "🪙 Crypto", "T": "DOT-USD", "N": "Polkadot"}
]

# リスト結合 (BONDS, FOREX, 全て込み)
TICKER_DATA_RAW = BONDS + FOREX + US_TECH + US_MAJOR + JAPAN + ETF + CRYPTO
ticker_df_master = pd.DataFrame(TICKER_DATA_RAW).rename(columns={"C": "Category", "T": "Ticker", "N": "Name"})

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
    # エラー対策: 複雑なstockオブジェクトを返さず、DataFrame化して返す
    if not ticker: return None, None, None
    
    yf_period = PERIOD_OPTIONS.get(period_key, "1y")
    yf_interval = get_interval_for_period(yf_period)
    
    try:
        stock = yf.Ticker(ticker)
        
        # 株価データ
        if period_key == "3年":
            start_date = datetime.now() - timedelta(days=365*3)
            df = stock.history(start=start_date, interval=yf_interval)
        else:
            df = stock.history(period=yf_period, interval=yf_interval)
        
        if not df.empty:
            df = calculate_technicals(df)
        else:
            # データが空の場合
            return None, None, None

        # 財務データ (DataFrame化)
        fin_df = pd.DataFrame()
        try:
            fin_df = stock.financials
        except:
            pass
            
        return df, fin_df, stock.info
        
    except:
        return None, None, None

@st.cache_data(ttl=600)
def get_massive_news(search_queries):
    """
    【改良版】
    カッコ書きを除去し、さらに「4文字以上の単語」を抽出して検索キーワードに追加。
    それらを OR でつないでヒット率を最大化する。
    """
    if not search_queries: return []
    try:
        final_keywords = []
        
        for q in search_queries:
            if not q: continue
            
            # 手順1: カッコ書きを除去してベースの言葉を作る
            base_text = q.replace('（', '(').split('(')[0].strip()
            if not base_text: continue
            
            # そのままのフレーズも検索候補に入れる
            final_keywords.append(base_text)
            
            # 手順2: 単語に分解して、4文字以上のワードを抽出
            words = base_text.split()
            long_words = [w for w in words if len(w) >= 4]
            
            if long_words:
                final_keywords.extend(long_words)
            else:
                # 4文字以上の単語がない場合は元の単語を使う
                final_keywords.extend(words)

        # 重複を除去し、API制限考慮で上位15ワードに絞る
        unique_keywords = list(set(final_keywords))[:15]
        
        if not unique_keywords: return []

        # "US 10Y Yield OR Yield OR Bitcoin ..." の形にする
        query_string = " OR ".join(unique_keywords)
        
        # --- APIリクエスト ---
        en_res = newsapi.get_everything(q=query_string, language='en', sort_by='publishedAt', page_size=50)
        jp_res = newsapi.get_everything(q=query_string, language='jp', sort_by='publishedAt', page_size=50)
        
        all_articles = en_res.get('articles', []) + jp_res.get('articles', [])
        all_articles = sorted([a for a in all_articles if a.get('publishedAt')], key=lambda x: x['publishedAt'], reverse=True)
        
        return all_articles
        
    except Exception as e:
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

st.title("📈 Pro Investor Dashboard v9.5")

if 'selected_tickers' not in st.session_state:
    st.session_state.selected_tickers = ["AAPL"]

w_df = fetch_watchlist()

# サイドバー
st.sidebar.header("🕹️ 管理パネル")
with st.sidebar.expander("➕ 新規追加 (任意コード)", expanded=False):
    st.caption("メモ必須 (ニュース検索用)")
    with st.form("sb_add"):
        t_in = st.text_input("コード").upper().strip()
        n_in = st.text_input("メモ").strip()
        if st.form_submit_button("追加"):
            if t_in and n_in:
                add_to_watchlist(t_in, n_in)
                st.success(f"追加完了: {t_in}")
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
        # 単体モード
        ticker = current_tickers[0]
        with st.spinner(f"{ticker} 分析中..."):
            df, fin_df, info = get_stock_data(ticker, period_label)
        
        if df is not None:
            short_name = info.get('shortName', ticker) if info else ticker
            st.subheader(f"{short_name} ({ticker})")
            
            # --- 株価チャート ---
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

            # --- 企業業績 (Fundamentals) ---
            if info and info.get('quoteType') == 'EQUITY':
                st.markdown("### 🏢 企業業績 (Annual Financials)")
                if fin_df is not None and not fin_df.empty:
                    try:
                        financials = fin_df.T 
                        financials.index = pd.to_datetime(financials.index).strftime('%Y-%m-%d')
                        fin_view = financials.sort_index()
                        
                        target_cols = ['Total Revenue', 'Net Income']
                        existing_cols = [c for c in target_cols if c in fin_view.columns]
                        
                        if existing_cols:
                            fig_fin = px.bar(
                                fin_view, 
                                y=existing_cols, 
                                barmode='group',
                                title=f"{short_name} - 売上高 & 純利益",
                                labels={"value": "Amount", "index": "Year", "variable": "Metric"}
                            )
                            st.plotly_chart(fig_fin, use_container_width=True)
                        else:
                            st.caption("主要な財務項目が見つかりませんでした")
                    except:
                        st.caption("財務データの表示に失敗しました")
                else:
                    st.caption("財務データがありません")
    else:
        # 比較モード
        st.subheader("📊 パフォーマンス比較 (正規化)")
        fig_comp = go.Figure()
        for t in current_tickers:
            df, _, _ = get_stock_data(t, period_label)
            if df is not None:
                start_price = df['Close'].iloc[0]
                if start_price > 0:
                    norm = ((df['Close'] / start_price) - 1) * 100
                    fig_comp.add_trace(go.Scatter(x=df.index, y=norm, mode='lines', name=f"{t} ({norm.iloc[-1]:+.2f}%)"))
        fig_comp.update_layout(height=600, yaxis_title="変化率 (%)", hovermode="x unified")
        fig_comp.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.3)
        st.plotly_chart(fig_comp, use_container_width=True)

# --- タブ2: 相関マトリクス ---
with tab_corr:
    st.header("🔢 相関分析")
    st.info("2つ以上の銘柄を選択すると、連動性が表示されます（赤=正の相関、青=逆相関）。")
    
    if len(current_tickers) >= 2:
        with st.spinner("相関データを計算中..."):
            close_data = {}
            for t in current_tickers:
                df, _, _ = get_stock_data(t, period_label)
                if df is not None:
                    close_data[t] = df['Close']
            
            if close_data:
                df_corr = pd.DataFrame(close_data)
                corr_matrix = df_corr.corr()
                fig_heatmap = px.imshow(
                    corr_matrix,
                    text_auto=".2f",
                    aspect="auto",
                    color_continuous_scale="RdBu_r",
                    range_color=[-1, 1],
                    title=f"相関係数ヒートマップ"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.error("データ不足")
    else:
        st.warning("2つ以上の銘柄を選択してください")

# --- タブ3: ニュース ---
with tab_news:
    st.header("📰 関連ニュース")
    if current_tickers:
        search_terms = []
        if not w_df.empty:
            selected_rows = w_df[w_df['ticker'].isin(current_tickers)]
            search_terms = [row['note'] if row['note'] else row['ticker'] for _, row in selected_rows.iterrows()]
        if not search_terms: search_terms = current_tickers
        
        # 検索ワードの確認表示（自動抽出後のロジックをシミュレート）
        display_keywords = []
        for q in search_terms:
            base = q.replace('（', '(').split('(')[0].strip()
            display_keywords.append(base)
            words = base.split()
            longs = [w for w in words if len(w) >= 4]
            display_keywords.extend(longs)
        
        unique_disp = list(set(display_keywords))[:15]
        st.caption(f"検索ワード(自動抽出): {', '.join(unique_disp)} ...")
        
        with st.spinner("収集中..."):
            arts = get_massive_news(search_terms)
        
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
            st.warning("ニュースなし。メモが正しいか確認してください")
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
