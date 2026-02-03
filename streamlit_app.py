import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client
from newsapi import NewsApiClient

# --- 1. 設定 ---
st.set_page_config(page_title="Pro Investor Dashboard v3", layout="wide")

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

# --- 2. 銘柄データ (300種類以上に拡張) ---
# メンテナンス性を考慮し、カテゴリごとにリスト化して統合
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
    {"C": "🇺🇸 US Tech", "T": "AMAT", "N": "Applied Materials"}, {"C": "🇺🇸 US Tech", "T": "LRCX", "N": "Lam Research"}
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
    {"C": "🇺🇸 US Major", "T": "VZ", "N": "Verizon"}, {"C": "🇺🇸 US Major", "T": "F", "N": "Ford"}
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

FOREX = [
    {"C": "💱 Forex", "T": "USDJPY=X", "N": "USD/JPY"}, {"C": "💱 Forex", "T": "EURUSD=X", "N": "EUR/USD"},
    {"C": "💱 Forex", "T": "GBPUSD=X", "N": "GBP/USD"}, {"C": "💱 Forex", "T": "AUDUSD=X", "N": "AUD/USD"},
    {"C": "💱 Forex", "T": "EURJPY=X", "N": "EUR/JPY"}, {"C": "💱 Forex", "T": "GBPJPY=X", "N": "GBP/JPY"}
]

# リストの結合
TICKER_DATA_RAW = US_TECH + US_MAJOR + JAPAN + ETF + CRYPTO + FOREX
# DataFrame化
ticker_df_master = pd.DataFrame(TICKER_DATA_RAW).rename(columns={"C": "Category", "T": "Ticker", "N": "Name"})


# --- 3. 関数群 ---

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
def get_stock_data(ticker, period="1y", interval="1d"):
    if not ticker: return None, None
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if not df.empty:
            df = calculate_technicals(df)
        return df, stock.info
    except:
        return None, None

@st.cache_data(ttl=600)
def get_watchlist_news(tickers):
    if not tickers: return []
    try:
        # クエリ生成: "AAPL OR MSFT OR NVDA" の形式
        # NewsAPIの文字数制限を考慮し、最大20銘柄までに制限
        limit = 20
        query_list = tickers[:limit]
        
        # 銘柄名(Ticker)で検索
        query_string = " OR ".join(query_list)
        
        all_articles = newsapi.get_everything(
            q=query_string,
            language='en',
            sort_by='publishedAt',
            page_size=15
        )
        return all_articles.get('articles', [])
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

# --- 4. アプリ画面構築 ---

st.title("📈 Pro Investor Dashboard v3")

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "AAPL"

# ==========================================
# サイドバー (統合コントロールセンター)
# ==========================================
st.sidebar.header("🕹️ コントロールパネル")

# 1. 銘柄追加フォーム (サイドバー最上部へ移動)
with st.sidebar.expander("➕ ウォッチリストに追加", expanded=False):
    with st.form("sidebar_add_form", clear_on_submit=True):
        st.write("気になる銘柄を追加")
        sb_ticker = st.text_input("コード (例: VOO, 7203.T)").upper()
        sb_note = st.text_input("メモ (例: S&P500)")
        if st.form_submit_button("追加"):
            if sb_ticker:
                if add_to_watchlist(sb_ticker, sb_note):
                    st.success("追加しました")
                    st.rerun()
                else:
                    st.error("エラー")
            else:
                st.warning("コード必須")

st.sidebar.markdown("---")

# 2. ウォッチリスト選択
w_df = fetch_watchlist()
watchlist_tickers = [] # ニュース検索用にリスト化

if not w_df.empty:
    watchlist_tickers = w_df['ticker'].tolist()
    
    st.sidebar.subheader("⭐ ウォッチリスト")
    w_df['label'] = w_df['ticker'] + " - " + w_df['note'].fillna("")
    
    # ラジオボタン
    selected_label = st.sidebar.radio(
        "分析対象を選択:", 
        w_df['label'],
        key="sb_radio"
    )
    
    selected_row = w_df[w_df['label'] == selected_label].iloc[0]
    
    col_btn1, col_btn2 = st.sidebar.columns(2)
    if col_btn1.button("分析 ▶", type="primary"):
        st.session_state.current_ticker = selected_row['ticker']
        st.rerun()
        
    if col_btn2.button("削除 🗑️"):
        delete_from_watchlist(int(selected_row['id']))
        st.rerun()
else:
    st.sidebar.info("リストは空です")

st.sidebar.markdown("---")
st.sidebar.caption("設定")
period = st.sidebar.selectbox("期間", ["3mo", "6mo", "1y", "2y", "5y"], index=2)


# ==========================================
# メインコンテンツ
# ==========================================
# データ取得
ticker_input = st.session_state.current_ticker
with st.spinner(f"{ticker_input} 分析中..."):
    df, info = get_stock_data(ticker_input, period=period)

# タブ構成
tab_chart, tab_news, tab_list = st.tabs([
    "📊 チャート分析", 
    "📰 ウォッチリストNews (All)", 
    "📋 銘柄データベース (300+)"
])

# --- タブ1: チャート ---
with tab_chart:
    if df is not None and not df.empty:
        short_name = info.get('shortName', ticker_input) if info else ticker_input
        st.subheader(f"{short_name} ({ticker_input})")
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        delta = latest['Close'] - prev['Close']
        pct = (delta / prev['Close']) * 100
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Close", f"{latest['Close']:,.2f}", f"{delta:,.2f} ({pct:.2f}%)")
        m2.metric("Market Cap", f"{info.get('marketCap', 0)/1e9:,.1f} B" if info else "-")
        m3.metric("PER", f"{info.get('trailingPE', 0):.2f}" if info else "-")
        m4.metric("High (Period)", f"{df['High'].max():,.2f}")

        # Chart
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
        if 'SMA20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name='SMA 20'))
        if 'SMA50' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name='SMA 50'))
        fig.update_layout(height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            fig_m = go.Figure()
            if 'MACD' in df.columns:
                fig_m.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD'))
                fig_m.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal'))
            fig_m.update_layout(height=300, title="MACD")
            st.plotly_chart(fig_m, use_container_width=True)
        with c2:
            fig_r = go.Figure()
            if 'RSI' in df.columns:
                fig_r.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')))
            fig_r.add_hline(y=70, line_dash="dash", line_color="red")
            fig_r.add_hline(y=30, line_dash="dash", line_color="blue")
            fig_r.update_layout(height=300, title="RSI", yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.error("データ取得エラー")

# --- タブ2: 全銘柄ニュース ---
with tab_news:
    st.header("📰 ウォッチリスト関連ニュース")
    
    if watchlist_tickers:
        # リスト化された銘柄コードを表示
        st.caption(f"検索対象: {', '.join(watchlist_tickers[:20])}" + ("..." if len(watchlist_tickers)>20 else ""))
        
        with st.spinner("登録銘柄のニュースをまとめて収集中..."):
            # ここで全銘柄検索を実行
            wl_articles = get_watchlist_news(watchlist_tickers)
        
        if wl_articles:
            for a in wl_articles:
                with st.container(border=True):
                    c_img, c_txt = st.columns([1, 3])
                    if a.get('urlToImage'): c_img.image(a['urlToImage'], use_container_width=True)
                    c_txt.subheader(a.get('title', 'No Title'))
                    c_txt.caption(f"{a['source']['name']} | {a['publishedAt'][:10]}")
                    c_txt.write(a.get('description', ''))
                    c_txt.markdown(f"[記事を読む]({a['url']})")
        else:
            st.info("ニュースが見つかりませんでした")
    else:
        st.warning("ウォッチリストが空です。サイドバーから銘柄を追加してください。")

# --- タブ3: 銘柄DB (300+) ---
with tab_list:
    st.header("📋 銘柄データベース (検索用)")
    st.info("コードをコピーして、サイドバーの「ウォッチリストに追加」へ貼り付けてください。")
    
    search_w = st.text_input("🔍 銘柄検索 (例: India, Gold, トヨタ)", "")
    
    df_disp = ticker_df_master
    if search_w:
        mask = df_disp.astype(str).apply(lambda x: x.str.contains(search_w, case=False)).any(axis=1)
        df_disp = df_disp[mask]

    # カテゴリごとにループ表示
    cats = df_disp['Category'].unique()
    for cat in cats:
        with st.expander(f"📂 {cat}", expanded=False):
            sub = df_disp[df_disp['Category'] == cat][['Ticker', 'Name']]
            st.dataframe(sub, use_container_width=True, hide_index=True)
