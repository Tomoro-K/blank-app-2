import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client
from newsapi import NewsApiClient

# --- 1. 設定 ---
st.set_page_config(page_title="Pro Investor Dashboard", layout="wide")

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

# --- 2. 銘柄データ (大幅増量版) ---
TICKER_DATA = [
    # 米国株 - ハイテク/マグニフィセント7
    {"Category": "🇺🇸 US Tech (M7)", "Ticker": "AAPL", "Name": "Apple"},
    {"Category": "🇺🇸 US Tech (M7)", "Ticker": "NVDA", "Name": "NVIDIA"},
    {"Category": "🇺🇸 US Tech (M7)", "Ticker": "MSFT", "Name": "Microsoft"},
    {"Category": "🇺🇸 US Tech (M7)", "Ticker": "AMZN", "Name": "Amazon"},
    {"Category": "🇺🇸 US Tech (M7)", "Ticker": "GOOGL", "Name": "Alphabet (Google)"},
    {"Category": "🇺🇸 US Tech (M7)", "Ticker": "META", "Name": "Meta Platforms"},
    {"Category": "🇺🇸 US Tech (M7)", "Ticker": "TSLA", "Name": "Tesla"},
    
    # 米国株 - 有名企業
    {"Category": "🇺🇸 US Major", "Ticker": "NFLX", "Name": "Netflix"},
    {"Category": "🇺🇸 US Major", "Ticker": "AMD", "Name": "AMD"},
    {"Category": "🇺🇸 US Major", "Ticker": "INTC", "Name": "Intel"},
    {"Category": "🇺🇸 US Major", "Ticker": "CRM", "Name": "Salesforce"},
    {"Category": "🇺🇸 US Major", "Ticker": "KO", "Name": "Coca-Cola"},
    {"Category": "🇺🇸 US Major", "Ticker": "PEP", "Name": "PepsiCo"},
    {"Category": "🇺🇸 US Major", "Ticker": "MCD", "Name": "McDonald's"},
    {"Category": "🇺🇸 US Major", "Ticker": "DIS", "Name": "Disney"},
    {"Category": "🇺🇸 US Major", "Ticker": "NKE", "Name": "Nike"},
    {"Category": "🇺🇸 US Major", "Ticker": "JPM", "Name": "JPMorgan Chase"},
    {"Category": "🇺🇸 US Major", "Ticker": "V", "Name": "Visa"},
    {"Category": "🇺🇸 US Major", "Ticker": "PG", "Name": "Procter & Gamble"},
    {"Category": "🇺🇸 US Major", "Ticker": "JNJ", "Name": "Johnson & Johnson"},
    {"Category": "🇺🇸 US Major", "Ticker": "XOM", "Name": "Exxon Mobil"},

    # ETF (指数・高配当)
    {"Category": "📊 ETF/Index", "Ticker": "^GSPC", "Name": "S&P 500 Index"},
    {"Category": "📊 ETF/Index", "Ticker": "^DJI", "Name": "Dow Jones 30"},
    {"Category": "📊 ETF/Index", "Ticker": "^IXIC", "Name": "NASDAQ Composite"},
    {"Category": "📊 ETF/Index", "Ticker": "VOO", "Name": "Vanguard S&P 500"},
    {"Category": "📊 ETF/Index", "Ticker": "QQQ", "Name": "Invesco QQQ (Nasdaq-100)"},
    {"Category": "📊 ETF/Index", "Ticker": "VTI", "Name": "Total Stock Market"},
    {"Category": "📊 ETF/Index", "Ticker": "VT", "Name": "Total World Stock"},
    {"Category": "📊 ETF/Index", "Ticker": "VYM", "Name": "High Dividend Yield"},
    {"Category": "📊 ETF/Index", "Ticker": "SPYD", "Name": "S&P 500 High Dividend"},
    {"Category": "📊 ETF/Index", "Ticker": "AGG", "Name": "US Aggregate Bond"},
    {"Category": "📊 ETF/Index", "Ticker": "GLD", "Name": "Gold"},
    {"Category": "📊 ETF/Index", "Ticker": "EPI", "Name": "India Earnings (インド株)"},

    # 日本株 (時価総額上位・人気)
    {"Category": "🇯🇵 Japan", "Ticker": "7203.T", "Name": "トヨタ自動車"},
    {"Category": "🇯🇵 Japan", "Ticker": "6758.T", "Name": "ソニーグループ"},
    {"Category": "🇯🇵 Japan", "Ticker": "8306.T", "Name": "三菱UFJ"},
    {"Category": "🇯🇵 Japan", "Ticker": "9984.T", "Name": "ソフトバンクG"},
    {"Category": "🇯🇵 Japan", "Ticker": "9432.T", "Name": "NTT"},
    {"Category": "🇯🇵 Japan", "Ticker": "7974.T", "Name": "任天堂"},
    {"Category": "🇯🇵 Japan", "Ticker": "6861.T", "Name": "キーエンス"},
    {"Category": "🇯🇵 Japan", "Ticker": "6098.T", "Name": "リクルート"},
    {"Category": "🇯🇵 Japan", "Ticker": "9983.T", "Name": "ファーストリテイリング"},
    {"Category": "🇯🇵 Japan", "Ticker": "4063.T", "Name": "信越化学"},
    {"Category": "🇯🇵 Japan", "Ticker": "8001.T", "Name": "伊藤忠商事"},
    {"Category": "🇯🇵 Japan", "Ticker": "8035.T", "Name": "東京エレクトロン"},
    {"Category": "🇯🇵 Japan", "Ticker": "7011.T", "Name": "三菱重工"},
    {"Category": "🇯🇵 Japan", "Ticker": "2914.T", "Name": "JT (日本たばこ)"},

    # 暗号資産
    {"Category": "🪙 Crypto", "Ticker": "BTC-USD", "Name": "Bitcoin"},
    {"Category": "🪙 Crypto", "Ticker": "ETH-USD", "Name": "Ethereum"},
    {"Category": "🪙 Crypto", "Ticker": "XRP-USD", "Name": "XRP"},
    {"Category": "🪙 Crypto", "Ticker": "SOL-USD", "Name": "Solana"},
    {"Category": "🪙 Crypto", "Ticker": "BNB-USD", "Name": "BNB"},
    {"Category": "🪙 Crypto", "Ticker": "DOGE-USD", "Name": "Dogecoin"},
]

# --- 3. 関数群 ---

def calculate_technicals(df):
    # SMA (KeyError対策で先に計算)
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
def get_market_news(query):
    if not query or len(query) < 2: return []
    try:
        all_articles = newsapi.get_everything(q=query, language='en', sort_by='publishedAt', page_size=8)
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
        # 重複チェックは簡易的に省略
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

st.title("📈 Pro Investor Dashboard")

# セッション状態の管理（選択中の銘柄を保持）
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "AAPL"

# ==========================================
# サイドバー (設定 & ウォッチリスト連携)
# ==========================================
st.sidebar.header("設定パネル")

# ウォッチリスト表示
with st.sidebar.expander("⭐ ウォッチリスト", expanded=True):
    w_df = fetch_watchlist()
    if not w_df.empty:
        # 表示用ラベル作成
        w_df['label'] = w_df['ticker'] + " - " + w_df['note'].fillna("")
        
        # ラジオボタンで選択 (keyを指定して状態管理)
        selected_label = st.radio(
            "銘柄を選択:", 
            w_df['label'], 
            index=0,
            key="watchlist_radio"
        )
        
        # 選択されたらメインのtickerを更新するロジック
        # (ラジオボタンの変更を検知して更新)
        selected_row = w_df[w_df['label'] == selected_label].iloc[0]
        
        # ボタンで削除
        if st.button("選択中の銘柄を削除", key="del_btn"):
            delete_from_watchlist(int(selected_row['id']))
            st.rerun() # 即座に反映
            
        # ★ここが重要: リスト選択をチャートに反映させるためのボタン
        # ラジオボタンだけでは変数が同期しないことがあるため、明示的なボタンか、
        # あるいは「ラジオボタンの値が変わったら代入」する
        if st.sidebar.button("この銘柄を分析する ▶", type="primary"):
             st.session_state.current_ticker = selected_row['ticker']
             st.rerun()
    else:
        st.info("リストは空です")

st.sidebar.markdown("---")
st.sidebar.caption("コード手動入力")
# 入力欄のデフォルト値をセッションから取得
ticker_input = st.sidebar.text_input("Ticker", value=st.session_state.current_ticker).upper().strip()
# 入力されたらセッションも更新
if ticker_input != st.session_state.current_ticker:
    st.session_state.current_ticker = ticker_input

period = st.sidebar.selectbox("期間", ["3mo", "6mo", "1y", "2y", "5y"], index=2)

# ==========================================
# メインコンテンツ
# ==========================================

# データ取得
with st.spinner(f"{ticker_input} のデータを取得中..."):
    df, info = get_stock_data(ticker_input, period=period)

tab_chart, tab_news, tab_list = st.tabs(["📊 チャート分析", "📰 関連ニュース", "📋 銘柄リスト (検索・追加)"])

# --- タブ1: チャート ---
with tab_chart:
    if df is not None and not df.empty:
        short_name = info.get('shortName', ticker_input) if info else ticker_input
        st.subheader(f"{short_name} ({ticker_input})")
        
        # 指標
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        delta = latest['Close'] - prev['Close']
        pct = (delta / prev['Close']) * 100
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("現在値", f"${latest['Close']:,.2f}", f"{delta:,.2f} ({pct:.2f}%)")
        m2.metric("時価総額", f"${info.get('marketCap', 0)/1e9:,.1f} B" if info else "-")
        m3.metric("PER", f"{info.get('trailingPE', 0):.2f}" if info else "-")
        m4.metric("高値(期間内)", f"${df['High'].max():,.2f}")

        # チャート
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
        if 'SMA20' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name='SMA 20'))
        if 'SMA50' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name='SMA 50'))
        fig.update_layout(height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # テクニカル
        c1, c2 = st.columns(2)
        with c1:
            fig_m = go.Figure()
            if 'MACD' in df.columns:
                fig_m.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD'))
                fig_m.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal'))
            fig_m.update_layout(height=300, title="MACD", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_m, use_container_width=True)
        with c2:
            fig_r = go.Figure()
            if 'RSI' in df.columns:
                fig_r.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')))
            fig_r.add_hline(y=70, line_dash="dash", line_color="red")
            fig_r.add_hline(y=30, line_dash="dash", line_color="blue")
            fig_r.update_layout(height=300, title="RSI", margin=dict(l=20, r=20, t=40, b=20), yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.error("データを取得できませんでした。コードを確認してください。")

# --- タブ2: ニュース ---
with tab_news:
    st.header(f"📰 {ticker_input} News")
    # 検索クエリ生成
    q_words = [ticker_input]
    if info and isinstance(info.get('shortName'), str):
        q_words.append(info['shortName'].split()[0]) # Apple Inc -> Apple
    
    search_q = " OR ".join(list(set(q_words)))
    
    with st.spinner("ニュース検索中..."):
        arts = get_market_news(search_q)
    
    if arts:
        for a in arts:
            with st.container(border=True):
                c_img, c_txt = st.columns([1, 3])
                if a.get('urlToImage'): c_img.image(a['urlToImage'], use_container_width=True)
                c_txt.subheader(a.get('title', 'No Title'))
                c_txt.caption(f"{a['source']['name']} | {a['publishedAt'][:10]}")
                c_txt.markdown(f"[記事を読む]({a['url']})")
    else:
        st.info("ニュースが見つかりませんでした")

# --- タブ3: 銘柄リスト & 追加 ---
with tab_list:
    st.header("銘柄リスト (検索 & 追加)")
    
    # 追加フォームをトップに配置
    st.markdown("##### ➕ ウォッチリストに追加")
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        # session_stateを使ってフォームの値を制御するテクニックも使えるが
        # シンプルにフォームで実装
        with st.form("add_ticker_form", clear_on_submit=True):
            f_ticker = c1.text_input("コード (例: VOO)")
            f_note = c2.text_input("メモ (例: S&P500 ETF)")
            submitted = st.form_submit_button("リストに追加", type="primary")
            
            if submitted:
                if f_ticker:
                    res = add_to_watchlist(f_ticker.upper(), f_note)
                    if res:
                        st.success(f"{f_ticker} を追加しました！")
                        st.rerun() # 追加したら即再読み込みしてサイドバーに反映
                    else:
                        st.error("追加に失敗しました")
                else:
                    st.warning("コードを入力してください")

    st.markdown("---")
    
    # 銘柄一覧表示
    t_df = pd.DataFrame(TICKER_DATA)
    
    # 検索機能
    search_w = st.text_input("🔍 リスト内を検索", placeholder="Japan, Apple, BTC...")
    if search_w:
        mask = t_df.astype(str).apply(lambda x: x.str.contains(search_w, case=False)).any(axis=1)
        t_df = t_df[mask]

    # カテゴリごとに表示
    cats = t_df['Category'].unique()
    for cat in cats:
        st.caption(f"📌 {cat}")
        sub_df = t_df[t_df['Category'] == cat][['Ticker', 'Name']]
        st.dataframe(sub_df, use_container_width=True, hide_index=True)
