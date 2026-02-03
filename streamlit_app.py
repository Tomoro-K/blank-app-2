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

# (A) テクニカル指標の計算
def calculate_technicals(df):
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
    
    # ★修正ポイント1: ここでSMA（移動平均）も計算しておくことでKeyErrorを防ぐ
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    return df

# (B) 株価データ取得
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

# (C) ニュース取得
@st.cache_data(ttl=600)
def get_market_news(query):
    if not query: return []
    try:
        if len(query) < 2: return [] # 短すぎるクエリはスキップ
        all_articles = newsapi.get_everything(
            q=query,
            language='en',
            sort_by='publishedAt',
            page_size=10
        )
        return all_articles.get('articles', [])
    except Exception:
        return []

# (D) ウォッチリスト操作
def fetch_watchlist():
    try:
        return pd.DataFrame(supabase.table("watchlist").select("*").order("created_at", desc=True).execute().data)
    except:
        return pd.DataFrame()

def add_to_watchlist(ticker, note):
    supabase.table("watchlist").insert({"ticker": ticker, "note": note}).execute()

def delete_from_watchlist(item_id):
    supabase.table("watchlist").delete().eq("id", item_id).execute()

# --- 4. アプリ画面構築 ---

st.title("📈 Pro Investor Dashboard")

# タブ構成
tab_chart, tab_news, tab_list = st.tabs(["📊 分析・チャート", "📰 関連ニュース", "📋 銘柄リスト"])

# サイドバー設定
st.sidebar.header("設定パネル")
with st.sidebar.expander("⭐ ウォッチリスト", expanded=True):
    w_df = fetch_watchlist()
    if not w_df.empty:
        # 銘柄選択ロジック
        w_options = w_df['ticker'] + " - " + w_df['note'].fillna("")
        w_sel = st.radio("保存済み銘柄", w_options)
        
        # 選択された行を安全に取得
        row = w_df[w_options == w_sel]
        if not row.empty:
            sel_ticker = row.iloc[0]['ticker']
            sel_id = row.iloc[0]['id']
            
            if st.button("削除", key="del"):
                delete_from_watchlist(int(sel_id))
                st.rerun()
        else:
            sel_ticker = "AAPL"
    else:
        sel_ticker = "AAPL"

ticker_input = st.sidebar.text_input("コード直接入力", value=sel_ticker).upper().strip()
period = st.sidebar.selectbox("期間", ["3mo", "6mo", "1y", "2y", "5y"], index=2)

# データ取得
df, info = get_stock_data(ticker_input, period=period)

# ==========================================
# タブ1：チャート分析
# ==========================================
with tab_chart:
    if df is not None and not df.empty:
        # 会社名の取得（安全策）
        short_name = info.get('shortName', ticker_input) if info else ticker_input
        st.subheader(f"{short_name} ({ticker_input})")
        
        m1, m2, m3, m4 = st.columns(4)
        curr_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        delta = curr_price - prev_price
        
        m1.metric("現在値", f"${curr_price:,.2f}", f"{delta:,.2f}")
        m2.metric("時価総額", f"${info.get('marketCap', 0)/1e9:,.1f} B" if info and info.get('marketCap') else "-")
        m3.metric("PER", f"{info.get('trailingPE', 0):.2f}" if info and info.get('trailingPE') else "-")
        m4.metric("配当", f"{info.get('dividendYield', 0)*100:.2f}%" if info and info.get('dividendYield') else "-")
        
        # --- メインチャート ---
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
        
        # ★修正ポイント: ここでSMA20/50を使うが、calculate_technicals関数で計算済みなのでエラーにならない
        if 'SMA20' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], mode='lines', name='SMA 20', line=dict(color='orange', width=1)))
        if 'SMA50' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], mode='lines', name='SMA 50', line=dict(color='blue', width=1)))
        
        fig.update_layout(height=500, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # --- サブチャート ---
        c1, c2 = st.columns(2)
        with c1:
            fig_macd = go.Figure()
            if 'MACD' in df.columns:
                fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='purple')))
                fig_macd.add_trace(go.Scatter(x=df.index, y=df['Signal'], name='Signal', line=dict(color='orange')))
            fig_macd.update_layout(title="MACD", height=300)
            st.plotly_chart(fig_macd, use_container_width=True)
        
        with c2:
            fig_rsi = go.Figure()
            if 'RSI' in df.columns:
                fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='green')))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="blue")
            fig_rsi.update_layout(title="RSI", height=300, yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig_rsi, use_container_width=True)
    else:
        st.warning("データが見つかりません。銘柄コードを確認してください。")

# ==========================================
# タブ2：関連ニュース (IndexError対策済み)
# ==========================================
with tab_news:
    st.header(f"📰 {ticker_input} 関連ニュース")
    
    # ★修正ポイント2: 検索ワード作成時のIndexErrorを完全に回避
    query_words = [ticker_input]
    
    # infoが存在し、かつshortNameが文字列として存在する場合のみ追加
    if info and isinstance(info.get('shortName'), str):
        name_parts = info['shortName'].split()
        if len(name_parts) > 0:
            query_words.append(name_parts[0]) # 最初の単語 (例: "Apple")
    
    # 重複を消して " OR " でつなぐ
    search_q = " OR ".join(list(set(query_words)))
    
    if search_q:
        with st.spinner("ニュース検索中..."):
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
                        st.subheader(art.get('title', 'No Title'))
                        st.caption(f"{art['source']['name']} | {art['publishedAt'][:10]}")
                        st.write(art.get('description', ''))
                        st.markdown(f"[記事を読む]({art['url']})")
        else:
            st.info("関連ニュースが見つかりませんでした。")
    else:
        st.warning("検索ワードが生成できませんでした。")

# ==========================================
# タブ3：銘柄リスト
# ==========================================
with tab_list:
    st.header("銘柄コード一覧")
    st.info("クリックしてコピー → サイドバーで「銘柄を追加」してください")
    
    with st.expander("＋ ウォッチリストに新規登録", expanded=True):
        with st.form("add_watch"):
            c1, c2 = st.columns(2)
            n_tick = c1.text_input("コード (例: NVDA)")
            n_memo = c2.text_input("メモ (例: NVIDIA)")
            if st.form_submit_button("登録"):
                if n_tick:
                    add_to_watchlist(n_tick, n_memo)
                    st.success("登録しました！")
                    st.rerun()

    t_df = pd.DataFrame(TICKER_DATA)
    st.dataframe(t_df, use_container_width=True, hide_index=True)
