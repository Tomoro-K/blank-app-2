import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from newsapi import NewsApiClient
from datetime import datetime, timedelta

# --- 1. 設定 ---
st.set_page_config(page_title="Pro Investor Dashboard v9", layout="wide")

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

# --- 2. 銘柄データ ---
BONDS = [
    {"C": "📉 Bonds/Yields", "T": "^TNX", "N": "US 10Y Yield (米国10年債)"},
    {"C": "📉 Bonds/Yields", "T": "TLT", "N": "20+ Year Treasury Bond ETF"},
    {"C": "📉 Bonds/Yields", "T": "AGG", "N": "US Aggregate Bond ETF"},
]
FOREX = [
    {"C": "💱 Forex", "T": "USDJPY=X", "N": "USD/JPY (ドル円)"},
    {"C": "💱 Forex", "T": "EURUSD=X", "N": "EUR/USD (ユーロドル)"},
    {"C": "💱 Forex", "T": "DX-Y.NYB", "N": "Dollar Index (ドル指数)"},
]
US_TECH = [
    {"C": "🇺🇸 US Tech", "T": "AAPL", "N": "Apple"}, {"C": "🇺🇸 US Tech", "T": "MSFT", "N": "Microsoft"},
    {"C": "🇺🇸 US Tech", "T": "NVDA", "N": "NVIDIA"}, {"C": "🇺🇸 US Tech", "T": "GOOGL", "N": "Alphabet"},
    {"C": "🇺🇸 US Tech", "T": "AMZN", "N": "Amazon"}, {"C": "🇺🇸 US Tech", "T": "META", "N": "Meta"},
    {"C": "🇺🇸 US Tech", "T": "TSLA", "N": "Tesla"}
]
US_MAJOR = [
    {"C": "🇺🇸 US Major", "T": "JPM", "N": "JPMorgan"}, {"C": "🇺🇸 US Major", "T": "V", "N": "Visa"},
    {"C": "🇺🇸 US Major", "T": "KO", "N": "Coca-Cola"}, {"C": "🇺🇸 US Major", "T": "MCD", "N": "McDonald's"},
    {"C": "🇺🇸 US Major", "T": "COST", "N": "Costco"}
]
JAPAN = [
    {"C": "🇯🇵 Japan", "T": "7203.T", "N": "トヨタ自動車"}, {"C": "🇯🇵 Japan", "T": "6758.T", "N": "ソニーG"},
    {"C": "🇯🇵 Japan", "T": "8306.T", "N": "三菱UFJ"}, {"C": "🇯🇵 Japan", "T": "9984.T", "N": "ソフトバンクG"},
    {"C": "🇯🇵 Japan", "T": "8035.T", "N": "東京エレクトロン"}, {"C": "🇯🇵 Japan", "T": "7974.T", "N": "任天堂"}
]
ETF = [
    {"C": "📊 ETF/Index", "T": "^GSPC", "N": "S&P 500"}, {"C": "📊 ETF/Index", "T": "^N225", "N": "日経平均"},
    {"C": "📊 ETF/Index", "T": "VOO", "N": "Vanguard S&P 500"}, {"C": "📊 ETF/Index", "T": "QQQ", "N": "Nasdaq-100"},
    {"C": "📊 ETF/Index", "T": "VT", "N": "Total World"}, {"C": "📊 ETF/Index", "T": "VYM", "N": "High Dividend"},
    {"C": "📊 ETF/Index", "T": "GLD", "N": "Gold"}, {"C": "📊 ETF/Index", "T": "EPI", "N": "India (Earnings)"}
]
CRYPTO = [
    {"C": "🪙 Crypto", "T": "BTC-USD", "N": "Bitcoin"}, {"C": "🪙 Crypto", "T": "ETH-USD", "N": "Ethereum"},
    {"C": "🪙 Crypto", "T": "SOL-USD", "N": "Solana"}, {"C": "🪙 Crypto", "T": "XRP-USD", "N": "XRP"}
]

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
    if not ticker: return None, None
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
        return df, stock, stock.info # stockオブジェクトも返すように変更
    except:
        return None, None, None

@st.cache_data(ttl=600)
def get_massive_news(search_queries):
    if not search_queries: return []
    try:
        valid_queries = [q for q in search_queries if q and len(q) > 1][:20]
        if not valid_queries: return []
        query_string = " OR ".join(valid_queries)
        
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

st.title("📈 Pro Investor Dashboard v9")

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

# 新機能: タブに「相関分析」を追加
tab_chart, tab_corr, tab_news, tab_db = st.tabs(["📊 チャート詳細", "🔢 相関マトリクス (New)", "📰 関連ニュース", "📋 銘柄DB"])

# --- タブ1: チャート詳細 ---
with tab_chart:
    if not current_tickers:
        st.info("👈 銘柄を選択してください")
    
    elif len(current_tickers) == 1:
        # 単体モード (業績表示機能付き)
        ticker = current_tickers[0]
        with st.spinner(f"{ticker} 分析中..."):
            df, stock_obj, info = get_stock_data(ticker, period_label)
        
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

            # --- 新機能: 企業業績 (Fundamentals) ---
            # 債券や為替には業績がないので、株式(Equity)のみ表示
            if info and info.get('quoteType') == 'EQUITY':
                st.markdown("### 🏢 企業業績 (Annual Financials)")
                try:
                    # 財務データの取得
                    financials = stock_obj.financials.T # 年次データ
                    if not financials.empty:
                        # 日付を文字列に変換して扱いやすくする
                        financials.index = financials.index.strftime('%Y-%m-%d')
                        fin_df = financials.sort_index()
                        
                        # 主要項目があるかチェック
                        target_cols = ['Total Revenue', 'Net Income']
                        existing_cols = [c for c in target_cols if c in fin_df.columns]
                        
                        if existing_cols:
                            # 棒グラフで表示
                            fig_fin = px.bar(
                                fin_df, 
                                y=existing_cols, 
                                barmode='group',
                                title=f"{short_name} - 売上高 & 純利益",
                                labels={"value": "Amount (Currency)", "index": "Year", "variable": "Metric"}
                            )
                            st.plotly_chart(fig_fin, use_container_width=True)
                        else:
                            st.info("財務データの一部が取得できませんでした")
                    else:
                        st.info("財務データが見つかりませんでした")
                except:
                    st.caption("※ 財務データの取得に失敗しました (ETFや指数などの可能性があります)")

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

# --- タブ2: 相関マトリクス (New) ---
with tab_corr:
    st.header("🔢 相関分析 (Correlation Matrix)")
    st.info("選択された銘柄間の「連動性」を分析します。1に近いほど同じ動き、-1に近いほど逆の動きをします。")
    
    if len(current_tickers) >= 2:
        with st.spinner("相関データを計算中..."):
            # Close価格だけのDataFrameを作成
            close_data = {}
            for t in current_tickers:
                df, _, _ = get_stock_data(t, period_label)
                if df is not None:
                    close_data[t] = df['Close']
            
            if close_data:
                df_corr = pd.DataFrame(close_data)
                # 相関係数を計算
                corr_matrix = df_corr.corr()
                
                # ヒートマップ描画
                fig_heatmap = px.imshow(
                    corr_matrix,
                    text_auto=".2f",
                    aspect="auto",
                    color_continuous_scale="RdBu_r", # 赤=正の相関, 青=負の相関
                    range_color=[-1, 1],
                    title=f"相関係数ヒートマップ (期間: {period_label})"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                st.markdown("""
                **見方:**
                * **赤色 (1.0に近い):** 正の相関。片方が上がれば、もう片方も上がる傾向。
                * **青色 (-1.0に近い):** 負の相関。片方が上がれば、もう片方は下がる傾向（分散投資に有効）。
                * **白色 (0に近い):** 無相関。互いに影響しない。
                """)
            else:
                st.error("データが不足しており計算できません")
    else:
        st.warning("相関分析には、左のボタンで **2つ以上の銘柄** を選択してください。")

# --- タブ3: ニュース ---
with tab_news:
    st.header("📰 関連ニュース")
    if current_tickers:
        search_terms = []
        if not w_df.empty:
            selected_rows = w_df[w_df['ticker'].isin(current_tickers)]
            search_terms = [row['note'] if row['note'] else row['ticker'] for _, row in selected_rows.iterrows()]
        if not search_terms: search_terms = current_tickers
        
        st.caption(f"Keywords: {', '.join(search_terms)}")
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
