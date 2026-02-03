import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client
from newsapi import NewsApiClient # ニュース用
import datetime

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

# --- 2. 銘柄データ (プリセット) ---
TICKER_DATA = [
    {"Category": "US Tech", "Ticker": "AAPL", "Name": "Apple"},
    {"Category": "US Tech", "Ticker": "NVDA", "Name": "NVIDIA"},
    {"Category": "US Tech", "Ticker": "MSFT", "Name": "Microsoft"},
    {"Category": "US Tech", "Ticker": "AMZN", "Name": "Amazon"},
    {"Category": "US Tech", "Ticker": "TSLA", "Name": "Tesla"},
    {"Category": "US Tech", "Ticker": "GOOGL", "Name": "Google"},
    {"Category": "Index", "Ticker": "^GSPC", "Name": "S&P 500"},
    {"Category": "Crypto", "Ticker": "BTC-USD", "Name": "Bitcoin"},
    {"Category": "Crypto", "Ticker": "ETH-USD", "Name": "Ethereum"},
    {"Category": "Japan", "Ticker": "7203.T", "Name": "Toyota"},
    {"Category": "Japan", "Ticker": "6758.T", "Name": "Sony"},
]

# --- 3. 関数群 ---

# (A) テクニカル指標の計算 (データサイエンス要素)
def calculate_technicals(df):
    # RSI (相対力指数)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD (移動平均収束拡散)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

# (B) 株価データ取得
@st.cache_data(ttl=300)
def get_stock_data(ticker, period="1y", interval="1d"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if not df.empty:
            df = calculate_technicals(df) # テクニカル計算を追加
        return df, stock.info
    except:
        return None, None

# (C) ニュース取得 (NewsAPI)
@st.cache_data(ttl=600)
def get_market_news(query):
    try:
        # 英語ニュースを取得 (情報の質が高いため)
        # 日本語がいい場合は language='jp' に変更
        all_articles = newsapi.get_everything(
            q=query,
            language='en',
            sort_by='publishedAt',
            page_size=10
        )
        return all_articles['articles']
    except Exception as e:
        return []

# (D) ウォッチリスト操作
def fetch_watchlist():
    return pd.DataFrame(supabase.table("watchlist").select("*").order("created_at", desc=True).execute().data)

def add_to_watchlist(ticker, note):
    supabase.table("watchlist").insert({"ticker": ticker, "note": note}).execute()

def delete_from_watchlist(item_id):
    supabase.table("watchlist").delete().eq("id", item_id).execute()

# --- 4. アプリ画面構築 ---

st.title("📈 Pro Investor Dashboard")

# タブ構成
tab_chart, tab_news, tab_list = st.tabs(["📊 分析・チャート", "📰 関連ニュース", "📋 銘柄リスト"])

# ==========================================
# タブ1：チャート分析 (高機能版)
# ==========================================
with tab_chart:
    # サイドバー：銘柄選択
    st.sidebar.header("設定パネル")
    
    # ウォッチリスト機能
    with st.sidebar.expander("⭐ ウォッチリスト", expanded=True):
        w_df = fetch_watchlist()
        if not w_df.empty:
            w_options = w_df['ticker'] + " - " + w_df['note'].fillna("")
            w_sel = st.radio("保存済み銘柄", w_options)
            sel_ticker = w_df[w_options == w_sel].iloc[0]['ticker']
            
            if st.button("削除", key="del"):
                delete_from_watchlist(w_df[w_options == w_sel].iloc[0]['id'])
                st.rerun()
        else:
            sel_ticker = "AAPL" # デフォルト

    # 手動入力上書き
    ticker_input = st.sidebar.text_input("コード直接入力", value=sel_ticker).upper()
    
    # チャート設定
    period = st.sidebar.selectbox("期間", ["3mo", "6mo", "1y", "2y", "5y"], index=2)
    
    # データ取得
    df, info = get_stock_data(ticker_input, period=period)

    if df is not None and not df.empty:
        # --- ファンダメンタルズ情報 ---
        st.subheader(f"{info.get('shortName', ticker_input)} ({ticker_input})")
        
        m1, m2, m3, m4 = st.columns(4)
        curr_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        delta = curr_price - prev_price
        
        m1.metric("現在値", f"${curr_price:,.2f}", f"{delta:,.2f}")
        m2.metric("時価総額", f"${info.get('marketCap', 0)/1e9:,.1f} B" if info.get('marketCap') else "-")
        m3.metric("PER (株価収益率)", f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "-")
        m4.metric("配当利回り", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "-")
        
        # --- メインチャート (ローソク足 + 移動平均) ---
        fig = go.Figure()
        
        # ローソク足
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
        
        # 移動平均線
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], mode='lines', name='SMA 20', line=dict(color='orange', width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], mode='lines', name='SMA 50', line=dict(color='blue', width=1)))
        
        fig.update_layout(title="株価チャート (Price Action)", height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # --- テクニカル指標 (サブチャート) ---
        c_tech1, c_tech2 = st.columns(2)
        
        with c_tech1:
            # MACDチャート
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='purple')))
            fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal', line=dict(color='orange')))
            fig_macd.update_layout(title="MACD (トレンド転換)", height=300, showlegend=True)
            st.plotly_chart(fig_macd, use_container_width=True)
            
        with c_tech2:
            # RSIチャート
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='green')))
            # 買われすぎ/売られすぎライン
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="blue", annotation_text="Oversold (30)")
            fig_rsi.update_layout(title="RSI (過熱感)", height=300, yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig_rsi, use_container_width=True)

    else:
        st.error("データを取得できませんでした。コードを確認してください。")

# ==========================================
# タブ2：関連ニュース (NewsAPI活用)
# ==========================================
with tab_news:
    st.header(f"📰 {ticker_input} 関連ニュース")
    
    # 検索クエリの作成 (社名があれば社名で、なければコードで)
    query_name = info.get('shortName', ticker_input) if 'info' in locals() and info else ticker_input
    # シンプルにするためコードと名前を組み合わせて検索
    search_q = f"{ticker_input} OR {query_name.split()[0]}"
    
    with st.spinner("世界中のニュースを探しています..."):
        articles = get_market_news(search_q)
        
    if articles:
        for art in articles:
            with st.container(border=True):
                col_img, col_txt = st.columns([1, 3])
                with col_img:
                    if art.get('urlToImage'):
                        st.image(art['urlToImage'], use_container_width=True)
                    else:
                        st.text("No Image")
                with col_txt:
                    st.subheader(art['title'])
                    st.caption(f"Source: {art['source']['name']} | {art['publishedAt'][:10]}")
                    st.write(art['description'])
                    st.markdown(f"[記事を読む]({art['url']})")
    else:
        st.info("関連ニュースが見つかりませんでした。")

# ==========================================
# タブ3：銘柄リスト (コピペ用)
# ==========================================
with tab_list:
    st.header("銘柄コード一覧")
    st.info("クリックしてコピー → サイドバーで「銘柄を追加」してください")
    
    # ウォッチリストへの追加フォーム
    with st.expander("＋ ウォッチリストに新規登録", expanded=True):
        with st.form("add_watch"):
            c1, c2 = st.columns(2)
            n_tick = c1.text_input("コード (例: NVDA)")
            n_memo = c2.text_input("メモ (例: NVIDIA)")
            if st.form_submit_button("登録"):
                add_to_watchlist(n_tick, n_memo)
                st.success("登録しました！")
                st.rerun()

    t_df = pd.DataFrame(TICKER_DATA)
    st.dataframe(t_df, use_container_width=True, hide_index=True)
