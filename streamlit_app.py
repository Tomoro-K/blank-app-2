import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client
from newsapi import NewsApiClient
from datetime import datetime, timedelta

# --- 1. 設定 ---
st.set_page_config(page_title="Pro Investor Dashboard v4", layout="wide")

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

# --- 2. 銘柄データ (300種以上) ---
# データ量が多いため、主要なものを抜粋しつつカテゴリ分けしています
US_TECH = [
    {"C": "🇺🇸 US Tech", "T": "AAPL", "N": "Apple"}, {"C": "🇺🇸 US Tech", "T": "MSFT", "N": "Microsoft"},
    {"C": "🇺🇸 US Tech", "T": "NVDA", "N": "NVIDIA"}, {"C": "🇺🇸 US Tech", "T": "GOOGL", "N": "Alphabet"},
    {"C": "🇺🇸 US Tech", "T": "AMZN", "N": "Amazon"}, {"C": "🇺🇸 US Tech", "T": "META", "N": "Meta"},
    {"C": "🇺🇸 US Tech", "T": "TSLA", "N": "Tesla"}, {"C": "🇺🇸 US Tech", "T": "AVGO", "N": "Broadcom"},
    {"C": "🇺🇸 US Tech", "T": "ORCL", "N": "Oracle"}, {"C": "🇺🇸 US Tech", "T": "CRM", "N": "Salesforce"},
    {"C": "🇺🇸 US Tech", "T": "AMD", "N": "AMD"}, {"C": "🇺🇸 US Tech", "T": "NFLX", "N": "Netflix"},
    {"C": "🇺🇸 US Tech", "T": "PLTR", "N": "Palantir"}, {"C": "🇺🇸 US Tech", "T": "COIN", "N": "Coinbase"}
]

US_MAJOR = [
    {"C": "🇺🇸 US Major", "T": "JPM", "N": "JPMorgan"}, {"C": "🇺🇸 US Major", "T": "V", "N": "Visa"},
    {"C": "🇺🇸 US Major", "T": "LLY", "N": "Eli Lilly"}, {"C": "🇺🇸 US Major", "T": "XOM", "N": "Exxon Mobil"},
    {"C": "🇺🇸 US Major", "T": "KO", "N": "Coca-Cola"}, {"C": "🇺🇸 US Major", "T": "MCD", "N": "McDonald's"},
    {"C": "🇺🇸 US Major", "T": "DIS", "N": "Disney"}, {"C": "🇺🇸 US Major", "T": "NKE", "N": "Nike"},
    {"C": "🇺🇸 US Major", "T": "COST", "N": "Costco"}, {"C": "🇺🇸 US Major", "T": "BRK-B", "N": "Berkshire Hathaway"}
]

JAPAN = [
    {"C": "🇯🇵 Japan", "T": "7203.T", "N": "トヨタ自動車"}, {"C": "🇯🇵 Japan", "T": "6758.T", "N": "ソニーG"},
    {"C": "🇯🇵 Japan", "T": "8306.T", "N": "三菱UFJ"}, {"C": "🇯🇵 Japan", "T": "9984.T", "N": "ソフトバンクG"},
    {"C": "🇯🇵 Japan", "T": "9432.T", "N": "NTT"}, {"C": "🇯🇵 Japan", "T": "8035.T", "N": "東京エレクトロン"},
    {"C": "🇯🇵 Japan", "T": "6861.T", "N": "キーエンス"}, {"C": "🇯🇵 Japan", "T": "9983.T", "N": "ファーストリテイリング"},
    {"C": "🇯🇵 Japan", "T": "7974.T", "N": "任天堂"}, {"C": "🇯🇵 Japan", "T": "8001.T", "N": "伊藤忠商事"},
    {"C": "🇯🇵 Japan", "T": "7011.T", "N": "三菱重工"}, {"C": "🇯🇵 Japan", "T": "6501.T", "N": "日立製作所"}
]

ETF = [
    {"C": "📊 ETF/Index", "T": "^GSPC", "N": "S&P 500"}, {"C": "📊 ETF/Index", "T": "^DJI", "N": "Dow 30"},
    {"C": "📊 ETF/Index", "T": "^IXIC", "N": "NASDAQ"}, {"C": "📊 ETF/Index", "T": "^N225", "N": "日経平均"},
    {"C": "📊 ETF/Index", "T": "VOO", "N": "Vanguard S&P 500"}, {"C": "📊 ETF/Index", "T": "QQQ", "N": "Nasdaq-100"},
    {"C": "📊 ETF/Index", "T": "VT", "N": "Total World"}, {"C": "📊 ETF/Index", "T": "VYM", "N": "High Dividend"},
    {"C": "📊 ETF/Index", "T": "SPYD", "N": "High Div (SP500)"}, {"C": "📊 ETF/Index", "T": "GLD", "N": "Gold"},
    {"C": "📊 ETF/Index", "T": "EPI", "N": "India (Earnings)"}, {"C": "📊 ETF/Index", "T": "AGG", "N": "US Bond"}
]

CRYPTO = [
    {"C": "🪙 Crypto", "T": "BTC-USD", "N": "Bitcoin"}, {"C": "🪙 Crypto", "T": "ETH-USD", "N": "Ethereum"},
    {"C": "🪙 Crypto", "T": "SOL-USD", "N": "Solana"}, {"C": "🪙 Crypto", "T": "XRP-USD", "N": "XRP"},
    {"C": "🪙 Crypto", "T": "DOGE-USD", "N": "Dogecoin"}, {"C": "🪙 Crypto", "T": "BNB-USD", "N": "BNB"}
]

FOREX = [
    {"C": "💱 Forex", "T": "USDJPY=X", "N": "USD/JPY"}, {"C": "💱 Forex", "T": "EURUSD=X", "N": "EUR/USD"}
]

TICKER_DATA_RAW = US_TECH + US_MAJOR + JAPAN + ETF + CRYPTO + FOREX
ticker_df_master = pd.DataFrame(TICKER_DATA_RAW).rename(columns={"C": "Category", "T": "Ticker", "N": "Name"})


# --- 3. 期間設定ロジック ---
PERIOD_OPTIONS = {
    "1日": "1d", "1週間": "5d", "1ヶ月": "1mo", "3ヶ月": "3mo",
    "6ヶ月": "6mo", "1年": "1y", "3年": "3y", "5年": "5y",
    "10年": "10y", "全期間": "max"
}

def get_interval_for_period(period_key):
    # 短期の場合は分足を使って詳細表示
    if period_key == "1d": return "15m" # 1日なら15分足 (yfinanceの制限考慮)
    if period_key == "5d": return "60m" # 1週間なら60分足
    return "1d" # それ以外は日足

# --- 4. 関数群 ---

def calculate_technicals(df):
    # 移動平均
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

@st.cache_data(ttl=300)
def get_stock_data(ticker, period_key):
    if not ticker: return None, None
    
    # マッピングからパラメータ取得
    yf_period = PERIOD_OPTIONS.get(period_key, "1y")
    yf_interval = get_interval_for_period(yf_period)
    
    # 3年の場合、yfinanceのperiod="3y"は存在しないことがあるため日付指定で対応
    # しかし簡易化のため、今回は近似値またはstart指定を使う
    # ここではyfinanceが認識できるフォーマットを優先
    
    try:
        stock = yf.Ticker(ticker)
        
        # 3年の特別対応 (start dateを使用)
        if period_key == "3年":
            start_date = datetime.now() - timedelta(days=365*3)
            df = stock.history(start=start_date, interval=yf_interval)
        else:
            df = stock.history(period=yf_period, interval=yf_interval)
            
        if not df.empty:
            df = calculate_technicals(df)
        return df, stock.info
    except:
        return None, None

@st.cache_data(ttl=600)
def get_watchlist_news(tickers):
    if not tickers: return []
    try:
        limit = 20
        query_list = tickers[:limit]
        query_string = " OR ".join(query_list)
        all_articles = newsapi.get_everything(
            q=query_string, language='en', sort_by='publishedAt', page_size=15
        )
        return all_articles.get('articles', [])
    except:
        return []

# DB操作系
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

st.title("📈 Pro Investor Dashboard v4 (Comparison)")

# セッション管理
if 'selected_tickers' not in st.session_state:
    st.session_state.selected_tickers = ["AAPL"] # デフォルト

# ==========================================
# サイドバー (設定 & 追加)
# ==========================================
st.sidebar.header("設定 & 銘柄追加")

# 1. 銘柄追加フォーム
with st.sidebar.expander("➕ ウォッチリストに追加", expanded=False):
    with st.form("sb_add"):
        t_in = st.text_input("コード (例: BTC-USD)").upper()
        n_in = st.text_input("メモ (例: Bitcoin)")
        if st.form_submit_button("追加"):
            if t_in:
                add_to_watchlist(t_in, n_in)
                st.success("追加しました")
                st.rerun()

st.sidebar.markdown("---")

# 2. 期間選択 (ご要望の選択肢)
period_label = st.sidebar.selectbox(
    "期間を選択", 
    list(PERIOD_OPTIONS.keys()), 
    index=5 # デフォルト: 1年
)

st.sidebar.markdown("---")

# 3. 分析対象の選択 (複数選択可能に)
w_df = fetch_watchlist()
available_options = []
default_sel = []

if not w_df.empty:
    # 選択肢の作成: "AAPL - Apple" 形式
    w_df['display'] = w_df['ticker'] + " - " + w_df['note'].fillna("")
    available_options = w_df['display'].tolist()
    
    # デフォルト選択 (セッションに残っていればそれを使う)
    # ※ リストから削除された場合などの整合性は簡易的に無視
    pre_selected = [op for op in available_options if op.split(" - ")[0] in st.session_state.selected_tickers]
    if not pre_selected and available_options:
        pre_selected = [available_options[0]] # 何もなければ一番上
        
    selected_displays = st.sidebar.multiselect(
        "分析対象 (複数選択で比較)",
        options=available_options,
        default=pre_selected
    )
    
    # 選択された表示名からTickerを取り出してリスト化
    current_tickers = [x.split(" - ")[0] for x in selected_displays]
    st.session_state.selected_tickers = current_tickers
    
    # 削除機能 (選択中の銘柄を削除)
    if st.sidebar.button("リストから削除 🗑️"):
        # 選択されているもののIDを取得して削除
        ids_to_del = w_df[w_df['display'].isin(selected_displays)]['id'].tolist()
        for i in ids_to_del:
            delete_from_watchlist(i)
        st.rerun()
else:
    st.sidebar.info("ウォッチリストが空です")
    current_tickers = []

# 手動で一時的に追加して比較したい場合用
manual_ticker = st.sidebar.text_input("一時的に追加して比較 (コード)", placeholder="NVDA").upper()
if manual_ticker and manual_ticker not in current_tickers:
    current_tickers.append(manual_ticker)


# ==========================================
# メインコンテンツ
# ==========================================

tab_chart, tab_news, tab_db = st.tabs(["📊 チャート分析", "📰 関連ニュース", "📋 銘柄DB"])

# --- タブ1: チャート (単体 vs 比較) ---
with tab_chart:
    if not current_tickers:
        st.warning("左のサイドバーから銘柄を選択してください。")
    
    elif len(current_tickers) == 1:
        # === 単体モード (詳細分析) ===
        ticker = current_tickers[0]
        with st.spinner(f"{ticker} のデータを取得中..."):
            df, info = get_stock_data(ticker, period_label)
        
        if df is not None and not df.empty:
            st.subheader(f"{info.get('shortName', ticker)} ({ticker})")
            
            # 最新価格表示
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            chg = latest['Close'] - prev['Close']
            pct = (chg / prev['Close']) * 100
            
            c1, c2, c3 = st.columns(3)
            c1.metric("現在値", f"${latest['Close']:,.2f}", f"{chg:,.2f} ({pct:.2f}%)")
            c2.metric("期間", period_label)
            c3.metric("高値", f"${df['High'].max():,.2f}")
            
            # ローソク足チャート
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
            if 'SMA20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name='SMA 20'))
            if 'SMA50' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name='SMA 50'))
            
            fig.update_layout(height=500, title=f"{ticker} Price Chart", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # サブチャート (MACD/RSI) - 短期足以外で表示
            if period_label not in ["1日", "1週間"]:
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    fig_m = go.Figure()
                    fig_m.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD'))
                    fig_m.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal'))
                    fig_m.update_layout(height=300, title="MACD")
                    st.plotly_chart(fig_m, use_container_width=True)
                with col_t2:
                    fig_r = go.Figure()
                    fig_r.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')))
                    fig_r.add_hline(y=70, line_dash="dash", line_color="red")
                    fig_r.add_hline(y=30, line_dash="dash", line_color="blue")
                    fig_r.update_layout(height=300, title="RSI", yaxis=dict(range=[0, 100]))
                    st.plotly_chart(fig_r, use_container_width=True)
            else:
                st.info("※短期足ではテクニカル指標の一部を非表示にしています")
        else:
            st.error(f"{ticker} のデータが取得できませんでした。")

    else:
        # === 複数比較モード (正規化チャート) ===
        st.subheader("📊 パフォーマンス比較 (正規化)")
        st.caption(f"期間: {period_label} | 開始時点を 0% として変化率を表示")
        
        fig_comp = go.Figure()
        valid_data_count = 0
        
        with st.spinner("各銘柄のデータを統合中..."):
            for t in current_tickers:
                df, _ = get_stock_data(t, period_label)
                if df is not None and not df.empty:
                    # 正規化計算: (現在価格 / 開始価格 - 1) * 100
                    # 最初の価格を取得
                    start_price = df['Close'].iloc[0]
                    if start_price > 0:
                        normalized_series = ((df['Close'] / start_price) - 1) * 100
                        
                        # グラフに追加
                        fig_comp.add_trace(go.Scatter(
                            x=df.index, 
                            y=normalized_series, 
                            mode='lines', 
                            name=f"{t} ({normalized_series.iloc[-1]:+.2f}%)"
                        ))
                        valid_data_count += 1
        
        if valid_data_count > 0:
            fig_comp.update_layout(
                height=600,
                xaxis_title="日付",
                yaxis_title="変化率 (%)",
                hovermode="x unified", # カーソルを合わせると全銘柄の数値を表示
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor="rgba(0,0,0,0.5)"
                )
            )
            # 0%ラインを強調
            fig_comp.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.3)
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.error("有効なデータが見つかりませんでした。")

# --- タブ2: ニュース ---
with tab_news:
    st.header("📰 関連ニュース")
    # 選択中の全銘柄を対象に検索
    if current_tickers:
        st.caption(f"対象: {', '.join(current_tickers[:10])} ...")
        with st.spinner("ニュース検索中..."):
            articles = get_watchlist_news(current_tickers)
        
        if articles:
            for a in articles:
                with st.container(border=True):
                    c_img, c_txt = st.columns([1, 3])
                    if a.get('urlToImage'): c_img.image(a['urlToImage'], use_container_width=True)
                    c_txt.subheader(a.get('title', 'No Title'))
                    c_txt.caption(f"{a['source']['name']} | {a['publishedAt'][:10]}")
                    c_txt.markdown(f"[記事を読む]({a['url']})")
        else:
            st.info("ニュースが見つかりませんでした。")
    else:
        st.warning("銘柄が選択されていません。")

# --- タブ3: 銘柄DB ---
with tab_db:
    st.header("📋 銘柄データベース (検索)")
    st.info("コードをコピーしてサイドバーで追加してください。")
    search_q = st.text_input("検索", placeholder="例: Japan, Gold...")
    
    df_db = ticker_df_master
    if search_q:
        mask = df_db.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)
        df_db = df_db[mask]
    
    for cat in df_db['Category'].unique():
        with st.expander(f"📂 {cat}", expanded=False):
            st.dataframe(
                df_db[df_db['Category']==cat][['Ticker', 'Name']], 
                use_container_width=True, 
                hide_index=True
            )
