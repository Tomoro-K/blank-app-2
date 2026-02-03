import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client
from newsapi import NewsApiClient
from datetime import datetime, timedelta

# --- 1. 設定 ---
st.set_page_config(page_title="Pro Investor Dashboard v8", layout="wide")

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

# --- 2. 銘柄データ (検索用プリセット) ---
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
    {"C": "💱 Forex", "T": "DX-Y.NYB", "N": "Dollar Index (ドル指数)"},
]

US_TECH = [
    {"C": "🇺🇸 US Tech", "T": "AAPL", "N": "Apple"}, {"C": "🇺🇸 US Tech", "T": "MSFT", "N": "Microsoft"},
    {"C": "🇺🇸 US Tech", "T": "NVDA", "N": "NVIDIA"}, {"C": "🇺🇸 US Tech", "T": "GOOGL", "N": "Alphabet"},
    {"C": "🇺🇸 US Tech", "T": "AMZN", "N": "Amazon"}, {"C": "🇺🇸 US Tech", "T": "META", "N": "Meta"},
    {"C": "🇺🇸 US Tech", "T": "TSLA", "N": "Tesla"}, {"C": "🇺🇸 US Tech", "T": "AMD", "N": "AMD"},
    {"C": "🇺🇸 US Tech", "T": "NFLX", "N": "Netflix"}, {"C": "🇺🇸 US Tech", "T": "PLTR", "N": "Palantir"}
]
US_MAJOR = [
    {"C": "🇺🇸 US Major", "T": "JPM", "N": "JPMorgan"}, {"C": "🇺🇸 US Major", "T": "V", "N": "Visa"},
    {"C": "🇺🇸 US Major", "T": "LLY", "N": "Eli Lilly"}, {"C": "🇺🇸 US Major", "T": "XOM", "N": "Exxon Mobil"},
    {"C": "🇺🇸 US Major", "T": "KO", "N": "Coca-Cola"}, {"C": "🇺🇸 US Major", "T": "MCD", "N": "McDonald's"},
    {"C": "🇺🇸 US Major", "T": "DIS", "N": "Disney"}, {"C": "🇺🇸 US Major", "T": "COST", "N": "Costco"}
]
JAPAN = [
    {"C": "🇯🇵 Japan", "T": "7203.T", "N": "トヨタ自動車"}, {"C": "🇯🇵 Japan", "T": "6758.T", "N": "ソニーG"},
    {"C": "🇯🇵 Japan", "T": "8306.T", "N": "三菱UFJ"}, {"C": "🇯🇵 Japan", "T": "9984.T", "N": "ソフトバンクG"},
    {"C": "🇯🇵 Japan", "T": "9432.T", "N": "NTT"}, {"C": "🇯🇵 Japan", "T": "8035.T", "N": "東京エレクトロン"},
    {"C": "🇯🇵 Japan", "T": "6861.T", "N": "キーエンス"}, {"C": "🇯🇵 Japan", "T": "9983.T", "N": "ファーストリテイリング"},
    {"C": "🇯🇵 Japan", "T": "7974.T", "N": "任天堂"}, {"C": "🇯🇵 Japan", "T": "8001.T", "N": "伊藤忠商事"}
]
ETF = [
    {"C": "📊 ETF/Index", "T": "^GSPC", "N": "S&P 500"}, {"C": "📊 ETF/Index", "T": "^DJI", "N": "Dow 30"},
    {"C": "📊 ETF/Index", "T": "^IXIC", "N": "NASDAQ"}, {"C": "📊 ETF/Index", "T": "^N225", "N": "日経平均"},
    {"C": "📊 ETF/Index", "T": "VOO", "N": "Vanguard S&P 500"}, {"C": "📊 ETF/Index", "T": "QQQ", "N": "Nasdaq-100"},
    {"C": "📊 ETF/Index", "T": "VT", "N": "Total World"}, {"C": "📊 ETF/Index", "T": "VYM", "N": "High Dividend"},
    {"C": "📊 ETF/Index", "T": "SPYD", "N": "High Div (SP500)"}, {"C": "📊 ETF/Index", "T": "GLD", "N": "Gold"},
    {"C": "📊 ETF/Index", "T": "EPI", "N": "India (Earnings)"}
]
CRYPTO = [
    {"C": "🪙 Crypto", "T": "BTC-USD", "N": "Bitcoin"}, {"C": "🪙 Crypto", "T": "ETH-USD", "N": "Ethereum"},
    {"C": "🪙 Crypto", "T": "SOL-USD", "N": "Solana"}, {"C": "🪙 Crypto", "T": "XRP-USD", "N": "XRP"}
]

# リスト結合
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
        return df, stock.info
    except:
        return None, None

@st.cache_data(ttl=600)
def get_massive_news(search_queries):
    """
    ウォッチリストの「メモ（名称）」を使ってニュースを検索します。
    """
    if not search_queries: return []
    
    try:
        # 空文字やNoneを除去し、最大20件に制限
        valid_queries = [q for q in search_queries if q and len(q) > 1][:20]
        if not valid_queries: return []

        # "Toyota OR Bitcoin OR ..." の形にする (OR検索 = いずれかを含む)
        query_string = " OR ".join(valid_queries)
        
        # 1. 英語ニュース
        en_articles = []
        try:
            en_res = newsapi.get_everything(
                q=query_string,
                language='en',
                sort_by='publishedAt',
                page_size=100
            )
            en_articles = en_res.get('articles', [])
        except:
            pass
            
        # 2. 日本語ニュース
        jp_articles = []
        try:
            jp_res = newsapi.get_everything(
                q=query_string,
                language='jp',
                sort_by='publishedAt',
                page_size=100
            )
            jp_articles = jp_res.get('articles', [])
        except:
            pass

        # 結合して新しい順にソート
        all_articles = en_articles + jp_articles
        # 日付情報がないものは除外してソート
        all_articles = sorted(
            [a for a in all_articles if a.get('publishedAt')], 
            key=lambda x: x['publishedAt'], 
            reverse=True
        )
        
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

st.title("📈 Pro Investor Dashboard v8")

if 'selected_tickers' not in st.session_state:
    st.session_state.selected_tickers = ["AAPL"]

w_df = fetch_watchlist()

# ==========================================
# サイドバー
# ==========================================
st.sidebar.header("🕹️ 管理パネル")

# 追加フォーム (メモ必須)
with st.sidebar.expander("➕ 新規追加 (任意コード)", expanded=False):
    st.caption("ニュース検索のため、メモも必ず入力してください")
    with st.form("sb_add"):
        t_in = st.text_input("コード (例: ^TNX, 7203.T)").upper().strip()
        n_in = st.text_input("メモ (例: 米10年債, トヨタ)").strip()
        if st.form_submit_button("追加"):
            if t_in and n_in:
                add_to_watchlist(t_in, n_in)
                st.success(f"{t_in} ({n_in}) を追加しました")
                st.rerun()
            else:
                st.error("⚠️ コードとメモの両方を入力してください。")

# 削除機能
with st.sidebar.expander("🗑️ 登録銘柄の削除", expanded=False):
    if not w_df.empty:
        w_df['del_label'] = w_df['ticker'] + " - " + w_df['note'].fillna("")
        to_delete = st.multiselect("削除する銘柄を選択:", w_df['del_label'])
        if st.button("選択した銘柄を削除", type="primary"):
            if to_delete:
                ids = w_df[w_df['del_label'].isin(to_delete)]['id'].tolist()
                for i in ids:
                    delete_from_watchlist(i)
                st.success("削除しました")
                st.rerun()
            else:
                st.warning("銘柄を選択してください")
    else:
        st.info("登録銘柄がありません")

st.sidebar.markdown("---")
period_label = st.sidebar.selectbox("期間設定", list(PERIOD_OPTIONS.keys()), index=5)
st.sidebar.markdown("---")

# Pills選択 (ボタン形式)
st.sidebar.subheader("📊 分析・比較する銘柄")
available_options = []
default_sel = []

if not w_df.empty:
    w_df['display'] = w_df['ticker'] + " - " + w_df['note'].fillna("")
    available_options = w_df['display'].tolist()
    
    valid_selected = [s for s in st.session_state.selected_tickers if any(s == op.split(" - ")[0] for op in available_options)]
    
    if not valid_selected and available_options:
        valid_selected = [available_options[0].split(" - ")[0]]
    
    default_options = [op for op in available_options if op.split(" - ")[0] in valid_selected]

    selected_displays = st.sidebar.pills(
        "タップして選択 (複数可)",
        options=available_options,
        default=default_options,
        selection_mode="multi"
    )
    
    if selected_displays:
        current_tickers = [x.split(" - ")[0] for x in selected_displays]
    else:
        current_tickers = []
        
    st.session_state.selected_tickers = current_tickers

else:
    st.sidebar.info("ウォッチリストが空です。")
    current_tickers = []


# ==========================================
# メインコンテンツ
# ==========================================

tab_chart, tab_news, tab_db = st.tabs(["📊 チャート分析", "📰 関連ニュース (Max 200)", "📋 銘柄DB"])

# --- タブ1: チャート ---
with tab_chart:
    if not current_tickers:
        st.info("👈 左のボタンで銘柄を選んでください。")
    
    elif len(current_tickers) == 1:
        # 単体モード
        ticker = current_tickers[0]
        with st.spinner(f"{ticker} データ取得中..."):
            df, info = get_stock_data(ticker, period_label)
        
        if df is not None and not df.empty:
            short_name = info.get('shortName', ticker) if info else ticker
            st.subheader(f"{short_name} ({ticker})")
            
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            chg = latest['Close'] - prev['Close']
            pct = (chg / prev['Close']) * 100
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Current", f"{latest['Close']:,.2f}", f"{chg:,.2f} ({pct:.2f}%)")
            c2.metric("Period", period_label)
            c3.metric("High", f"${df['High'].max():,.2f}")
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price/Yield"))
            if 'SMA20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1), name='SMA 20'))
            if 'SMA50' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='blue', width=1), name='SMA 50'))
            fig.update_layout(height=500, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            if period_label not in ["1日", "1週間"]:
                c_t1, c_t2 = st.columns(2)
                with c_t1:
                    fig_m = go.Figure()
                    fig_m.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD'))
                    fig_m.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal'))
                    fig_m.update_layout(height=300, title="MACD")
                    st.plotly_chart(fig_m, use_container_width=True)
                with c_t2:
                    fig_r = go.Figure()
                    fig_r.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')))
                    fig_r.add_hline(y=70, line_dash="dash", line_color="red")
                    fig_r.add_hline(y=30, line_dash="dash", line_color="blue")
                    fig_r.update_layout(height=300, title="RSI", yaxis=dict(range=[0, 100]))
                    st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.error("データ取得エラー。")

    else:
        # 比較モード
        st.subheader("📊 パフォーマンス比較 (正規化)")
        st.caption("※ 開始時点を 0% として変化率を表示。")
        fig_comp = go.Figure()
        
        for t in current_tickers:
            df, _ = get_stock_data(t, period_label)
            if df is not None and not df.empty:
                start_price = df['Close'].iloc[0]
                if start_price > 0:
                    norm = ((df['Close'] / start_price) - 1) * 100
                    fig_comp.add_trace(go.Scatter(x=df.index, y=norm, mode='lines', name=f"{t} ({norm.iloc[-1]:+.2f}%)"))
        
        fig_comp.update_layout(height=600, yaxis_title="変化率 (%)", hovermode="x unified")
        fig_comp.add_hline(y=0, line_dash="solid", line_color="white", opacity=0.3)
        st.plotly_chart(fig_comp, use_container_width=True)

# --- タブ2: ニュース (メモ検索版) ---
with tab_news:
    st.header("📰 関連ニュース (日/英・OR検索)")
    
    if current_tickers:
        # 選択された銘柄の「メモ」を取得して検索
        search_terms = []
        if not w_df.empty:
            selected_rows = w_df[w_df['ticker'].isin(current_tickers)]
            search_terms = [row['note'] if row['note'] else row['ticker'] for _, row in selected_rows.iterrows()]
        
        if not search_terms: search_terms = current_tickers

        st.caption(f"検索キーワード: {', '.join(search_terms)}")
        
        with st.spinner("ニュースを収集中..."):
            arts = get_massive_news(search_terms)
        
        if arts:
            st.success(f"{len(arts)} 件の記事が見つかりました")
            for a in arts:
                with st.container(border=True):
                    c_img, c_txt = st.columns([1, 3])
                    if a.get('urlToImage'): 
                        try:
                            c_img.image(a['urlToImage'], use_container_width=True)
                        except:
                            c_img.text("No Image")
                    c_txt.subheader(a.get('title', 'No Title'))
                    date_str = a['publishedAt'][:10] + " " + a['publishedAt'][11:16]
                    c_txt.caption(f"{a['source']['name']} | {date_str}")
                    c_txt.write(a.get('description', ''))
                    c_txt.markdown(f"[記事を読む]({a['url']})")
        else:
            st.warning("ニュースが見つかりませんでした。")
            st.markdown("メモ欄が記号（コード）のままだとニュースが出にくい場合があります。")
    else:
        st.warning("銘柄を選択してください")

# --- タブ3: 銘柄DB ---
with tab_db:
    st.header("📋 銘柄データベース")
    st.info("コードをコピーして、サイドバーの「新規追加」へ貼り付けてください。")
    search_q = st.text_input("検索", placeholder="例: Yield, Bond, トヨタ...")
    
    df_db = ticker_df_master
    if search_q:
        mask = df_db.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)
        df_db = df_db[mask]
    
    for cat in df_db['Category'].unique():
        with st.expander(f"📂 {cat}", expanded=False):
            st.dataframe(df_db[df_db['Category']==cat][['Ticker', 'Name']], use_container_width=True, hide_index=True)
