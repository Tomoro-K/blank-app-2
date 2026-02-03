import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client

# --- 1. 設定 ---
st.set_page_config(page_title="Market Dashboard", layout="wide")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("Secrets (SupabaseのURLとKEY) が設定されていません。")
    st.stop()

# Supabaseクライアント
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. データ準備 (銘柄リスト用) ---
# コピペ用に主要銘柄のリストを定義
TICKER_DATA = [
    # 米国株 (M7 + Major)
    {"Category": "US Tech", "Ticker": "AAPL", "Name": "Apple"},
    {"Category": "US Tech", "Ticker": "MSFT", "Name": "Microsoft"},
    {"Category": "US Tech", "Ticker": "GOOGL", "Name": "Alphabet (Google)"},
    {"Category": "US Tech", "Ticker": "AMZN", "Name": "Amazon"},
    {"Category": "US Tech", "Ticker": "NVDA", "Name": "NVIDIA"},
    {"Category": "US Tech", "Ticker": "TSLA", "Name": "Tesla"},
    {"Category": "US Tech", "Ticker": "META", "Name": "Meta Platforms"},
    {"Category": "US Major", "Ticker": "NFLX", "Name": "Netflix"},
    {"Category": "US Major", "Ticker": "AMD", "Name": "AMD"},
    {"Category": "US Major", "Ticker": "INTC", "Name": "Intel"},
    {"Category": "US Major", "Ticker": "CRM", "Name": "Salesforce"},
    {"Category": "US Major", "Ticker": "KO", "Name": "Coca-Cola"},
    {"Category": "US Major", "Ticker": "PEP", "Name": "PepsiCo"},
    {"Category": "US Major", "Ticker": "MCD", "Name": "McDonald's"},
    {"Category": "US Major", "Ticker": "DIS", "Name": "Disney"},
    {"Category": "US Major", "Ticker": "NKE", "Name": "Nike"},
    {"Category": "US Major", "Ticker": "JPM", "Name": "JPMorgan Chase"},
    {"Category": "US Major", "Ticker": "V", "Name": "Visa"},
    
    # 指数・ETF
    {"Category": "Index/ETF", "Ticker": "^GSPC", "Name": "S&P 500"},
    {"Category": "Index/ETF", "Ticker": "^DJI", "Name": "Dow Jones 30"},
    {"Category": "Index/ETF", "Ticker": "^IXIC", "Name": "NASDAQ Composite"},
    {"Category": "Index/ETF", "Ticker": "VOO", "Name": "Vanguard S&P 500 ETF"},
    {"Category": "Index/ETF", "Ticker": "QQQ", "Name": "Invesco QQQ (Nasdaq-100)"},
    {"Category": "Index/ETF", "Ticker": "VTI", "Name": "Vanguard Total Stock Market"},
    {"Category": "Index/ETF", "Ticker": "VT", "Name": "Vanguard Total World Stock"},
    {"Category": "Index/ETF", "Ticker": "GLD", "Name": "SPDR Gold Shares"},

    # 暗号資産
    {"Category": "Crypto", "Ticker": "BTC-USD", "Name": "Bitcoin"},
    {"Category": "Crypto", "Ticker": "ETH-USD", "Name": "Ethereum"},
    {"Category": "Crypto", "Ticker": "XRP-USD", "Name": "XRP"},
    {"Category": "Crypto", "Ticker": "SOL-USD", "Name": "Solana"},
    {"Category": "Crypto", "Ticker": "BNB-USD", "Name": "BNB"},
    {"Category": "Crypto", "Ticker": "DOGE-USD", "Name": "Dogecoin"},

    # 日本株 (参考: .Tが必要)
    {"Category": "Japan", "Ticker": "7203.T", "Name": "トヨタ自動車"},
    {"Category": "Japan", "Ticker": "6758.T", "Name": "ソニーグループ"},
    {"Category": "Japan", "Ticker": "9984.T", "Name": "ソフトバンクグループ"},
    {"Category": "Japan", "Ticker": "8306.T", "Name": "三菱UFJフィナンシャル"},
    {"Category": "Japan", "Ticker": "7974.T", "Name": "任天堂"},
    {"Category": "Japan", "Ticker": "6861.T", "Name": "キーエンス"},
    {"Category": "Japan", "Ticker": "6098.T", "Name": "リクルート"},
    {"Category": "Japan", "Ticker": "9983.T", "Name": "ファーストリテイリング"},
]

# --- 3. 関数群 ---

@st.cache_data(ttl=300)
def get_stock_data(ticker, period="1y", interval="1d"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        return df, stock.info
    except Exception as e:
        return None, None

def fetch_watchlist():
    response = supabase.table("watchlist").select("*").order("created_at", desc=True).execute()
    return pd.DataFrame(response.data)

def add_to_watchlist(ticker, note):
    data = {"ticker": ticker, "note": note}
    supabase.table("watchlist").insert(data).execute()

def delete_from_watchlist(item_id):
    supabase.table("watchlist").delete().eq("id", item_id).execute()

# --- 4. アプリ画面 ---

st.title("📈 Market Dashboard")

# === メインタブの作成 ===
tab_analysis, tab_list = st.tabs(["📈 チャート分析", "📋 銘柄リスト (コピペ用)"])

# ---------------------------------------------------------
# タブ1：チャート分析 (以前のメイン機能)
# ---------------------------------------------------------
with tab_analysis:
    # サイドバー：ウォッチリスト管理 (分析タブのときだけ使うイメージだが、サイドバーは常時表示)
    st.sidebar.header("⭐ ウォッチリスト")

    with st.sidebar.expander("＋ 銘柄を追加"):
        with st.form("add_form", clear_on_submit=True):
            new_ticker = st.text_input("銘柄コード (例: AAPL)").upper()
            new_note = st.text_input("メモ (例: Apple)")
            if st.form_submit_button("追加"):
                if new_ticker:
                    add_to_watchlist(new_ticker, new_note)
                    st.success("追加しました")
                    st.rerun()

    watchlist_df = fetch_watchlist()
    selected_ticker = "AAPL"

    if not watchlist_df.empty:
        st.sidebar.markdown("---")
        watchlist_df['label'] = watchlist_df['ticker'] + " - " + watchlist_df['note'].fillna("")
        selection = st.sidebar.radio("分析する銘柄を選択:", watchlist_df['label'])
        selected_row = watchlist_df[watchlist_df['label'] == selection].iloc[0]
        selected_ticker = selected_row['ticker']
        
        if st.sidebar.button("この銘柄を削除", key="del_btn"):
            delete_from_watchlist(int(selected_row['id']))
            st.rerun()
    else:
        st.sidebar.info("リストが空です。")
        selected_ticker = st.sidebar.text_input("分析したいコードを入力", "AAPL").upper()

    # --- 分析表示 ---
    if selected_ticker:
        st.subheader(f"{selected_ticker} のチャート")
        
        # 期間設定
        c1, c2 = st.columns(2)
        p = c1.selectbox("期間", ["1mo", "3mo", "6mo", "1y", "5y"], index=3)
        i = c2.selectbox("足", ["1d", "1wk", "1mo"], index=0)
        
        with st.spinner("Loading..."):
            df, info = get_stock_data(selected_ticker, p, i)
        
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            chg = latest['Close'] - prev['Close']
            pct = (chg / prev['Close']) * 100
            
            m1, m2, m3 = st.columns(3)
            m1.metric("価格", f"{latest['Close']:,.2f}")
            m2.metric("前日比", f"{chg:,.2f}", f"{pct:.2f}%")
            m3.metric("出来高", f"{latest['Volume']:,}")
            
            # チャート
            df['SMA20'] = df['Close'].rolling(20).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], mode='lines', name='SMA 20', line=dict(color='orange')))
            fig.update_layout(height=500, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("データが見つかりません。")

# ---------------------------------------------------------
# タブ2：銘柄リスト (新機能)
# ---------------------------------------------------------
with tab_list:
    st.header("銘柄コード一覧")
    st.info("💡 表のセルをクリックしてコピーし、サイドバーの「銘柄を追加」に貼り付けてください。")
    
    # データをDataFrame化
    ticker_df = pd.DataFrame(TICKER_DATA)
    
    # 検索フィルター
    search_query = st.text_input("🔍 名前やコードで検索 (例: Amazon, BTC)", "")
    
    if search_query:
        # 大文字小文字区別なく検索
        mask = ticker_df.apply(lambda x: x.astype(str).str.contains(search_query, case=False).any(), axis=1)
        display_df = ticker_df[mask]
    else:
        display_df = ticker_df
    
    # カテゴリごとの表示
    categories = display_df['Category'].unique()
    
    for cat in categories:
        st.subheader(f"📌 {cat}")
        cat_df = display_df[display_df['Category'] == cat][['Ticker', 'Name']]
        # データフレームを表示 (use_container_width=Trueできれいに)
        st.dataframe(
            cat_df, 
            hide_index=True, 
            use_container_width=True
        )
