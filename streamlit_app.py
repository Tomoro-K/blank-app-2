import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from supabase import create_client, Client
import datetime

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

# --- 2. 関数群 ---

# (A) 株価データ取得 (キャッシュして高速化)
@st.cache_data(ttl=300) # 5分間データを保存
def get_stock_data(ticker, period="1y", interval="1d"):
    try:
        stock = yf.Ticker(ticker)
        # 履歴データの取得
        df = stock.history(period=period, interval=interval)
        return df, stock.info
    except Exception as e:
        return None, None

# (B) ウォッチリスト操作
def fetch_watchlist():
    response = supabase.table("watchlist").select("*").order("created_at", desc=True).execute()
    return pd.DataFrame(response.data)

def add_to_watchlist(ticker, note):
    # 重複チェックは簡易的に省略（同じ銘柄も登録可とする）
    data = {"ticker": ticker, "note": note}
    supabase.table("watchlist").insert(data).execute()

def delete_from_watchlist(item_id):
    supabase.table("watchlist").delete().eq("id", item_id).execute()

# --- 3. アプリ画面 ---

st.title("📈 Market Data Analyst")
st.caption("Powered by Yahoo Finance & Supabase")

# === サイドバー：ウォッチリスト管理 ===
st.sidebar.header("⭐ ウォッチリスト")

# 新規追加フォーム
with st.sidebar.expander("＋ 銘柄を追加"):
    with st.form("add_form", clear_on_submit=True):
        new_ticker = st.text_input("銘柄コード (例: AAPL, BTC-USD)").upper()
        new_note = st.text_input("メモ (例: Apple, ビットコイン)")
        if st.form_submit_button("追加"):
            if new_ticker:
                add_to_watchlist(new_ticker, new_note)
                st.success("追加しました")
                st.rerun()

# リスト表示 & 選択
watchlist_df = fetch_watchlist()
selected_ticker = "AAPL" # デフォルト

if not watchlist_df.empty:
    st.sidebar.markdown("---")
    # ラジオボタンで銘柄を選択させる
    # 表示名を作成: "AAPL (Apple)" のように見やすくする
    watchlist_df['label'] = watchlist_df['ticker'] + " - " + watchlist_df['note'].fillna("")
    
    # 選択ウィジェット
    selection = st.sidebar.radio("分析する銘柄を選択:", watchlist_df['label'])
    
    # 選択された行のデータを取得
    selected_row = watchlist_df[watchlist_df['label'] == selection].iloc[0]
    selected_ticker = selected_row['ticker']
    
    # 削除ボタン
    if st.sidebar.button("この銘柄を削除", key="del_btn"):
        delete_from_watchlist(int(selected_row['id']))
        st.rerun()
else:
    st.sidebar.info("まだ登録がありません。銘柄を追加してください。")
    # ウォッチリストが空のときは手入力欄を出す
    selected_ticker = st.sidebar.text_input("銘柄コードを入力", "AAPL").upper()


# === メインエリア：分析ダッシュボード ===

if selected_ticker:
    st.header(f"📊 {selected_ticker} の分析")
    
    # 期間選択
    col_per, col_int = st.columns(2)
    period = col_per.selectbox("期間", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)
    interval = col_int.selectbox("足の間隔", ["1d", "1wk", "1mo"], index=0)
    
    # データ取得
    with st.spinner("データを取得中..."):
        df, info = get_stock_data(selected_ticker, period, interval)
    
    if df is not None and not df.empty:
        # 最新価格の表示
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        change = latest['Close'] - prev['Close']
        pct_change = (change / prev['Close']) * 100
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("現在値 (Close)", f"${latest['Close']:,.2f}")
        col_m2.metric("前日比", f"{change:,.2f}", f"{pct_change:.2f}%")
        col_m3.metric("出来高", f"{latest['Volume']:,}")
        
        # --- グラフ描画 (Plotly) ---
        st.subheader("プライスアクション")
        
        # タブ切り替え
        tab_chart, tab_data = st.tabs(["🕯️ チャート", "🔢 生データ"])
        
        with tab_chart:
            # 移動平均線の計算（データサイエンス要素）
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # グラフ作成
            fig = go.Figure()
            
            # ローソク足
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name='Price'
            ))
            
            # 移動平均線 (オプション)
            show_sma = st.checkbox("移動平均線を表示 (20日/50日)", value=True)
            if show_sma:
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], mode='lines', name='SMA 20', line=dict(color='orange', width=1)))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50', line=dict(color='blue', width=1)))

            fig.update_layout(
                title=f"{selected_ticker} 株価推移",
                yaxis_title="株価 (USD)",
                xaxis_rangeslider_visible=False, # スライダーを消してすっきりさせる
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with tab_data:
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
            
    else:
        st.error(f"データが見つかりませんでした。銘柄コード '{selected_ticker}' が正しいか確認してください。")
