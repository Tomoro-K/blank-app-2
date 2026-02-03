import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import yfinance as yf
from supabase import create_client, Client
import datetime

# --- 1. 設定とSupabase接続 ---
st.set_page_config(page_title="Real-time Asset Tracker", layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. 外部API & 株価取得関数 ---

# (A) 為替 (USD -> JPY)
@st.cache_data(ttl=3600)
def get_usd_jpy_rate():
    try:
        api_url = "https://api.exchangerate-api.com/v4/latest/USD"
        return requests.get(api_url).json()["rates"]["JPY"]
    except:
        return 150.0

# (B) 仮想通貨 (CoinGecko)
@st.cache_data(ttl=600)
def get_crypto_price(coin_id):
    try:
        api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=jpy"
        return requests.get(api_url).json()[coin_id]["jpy"]
    except:
        return 0.0

# (C) 株価取得 (yfinance) ★New!
@st.cache_data(ttl=3600)
def get_stock_price(ticker):
    if not ticker or ticker == "-":
        return None
    try:
        # 1日分のデータを取得して最新の終値または現在値を取得
        stock = yf.Ticker(ticker)
        history = stock.history(period="1d")
        if not history.empty:
            return history['Close'].iloc[-1]
        return None
    except:
        return None

# --- 3. データベース操作 ---
def fetch_assets():
    response = supabase.table("assets").select("*").execute()
    return pd.DataFrame(response.data)

def add_asset(name, category, amount, currency, ticker=None):
    data = {
        "name": name,
        "category": category,
        "amount": amount,
        "currency": currency,
        "ticker": ticker # 銘柄コードも保存
    }
    supabase.table("assets").insert(data).execute()

def delete_asset(asset_id):
    supabase.table("assets").delete().eq("id", asset_id).execute()

def fetch_transactions():
    response = supabase.table("transactions").select("*").order("date", desc=True).execute()
    return pd.DataFrame(response.data)

def add_transaction(date, type_, category, amount, memo):
    data = {"date": str(date), "type": type_, "category": category, "amount": amount, "memo": memo}
    supabase.table("transactions").insert(data).execute()

def delete_transaction(trans_id):
    supabase.table("transactions").delete().eq("id", trans_id).execute()

# --- 4. アプリ本体 ---
st.title("📈 Real-time Asset Dashboard")

# 各種レート取得
usd_rate = get_usd_jpy_rate()
btc_price = get_crypto_price("bitcoin")

tab1, tab2 = st.tabs(["🏦 資産ポートフォリオ", "📒 家計簿 (収支)"])

# ==========================================
# タブ1：資産管理 (株価自動更新)
# ==========================================
with tab1:
    st.header("資産一覧 (時価評価)")
    
    # 資産追加フォーム
    with st.expander("➕ 資産を手動追加"):
        with st.form("asset_form"):
            c1, c2, c3 = st.columns(3)
            name_in = c1.text_input("資産名", "Apple株式")
            # 株式の場合は「金額」ではなく「株数」を入力させる
            amt_in = c2.number_input("数量 (株数 or 金額)", min_value=0.0)
            curr_in = c3.selectbox("通貨", ["USD", "JPY", "BTC"])
            
            c4, c5 = st.columns(2)
            cat_in = c4.selectbox("カテゴリ", ["米国株", "投資信託", "現金", "仮想通貨"])
            # ★ 銘柄コード入力欄
            ticker_in = c5.text_input("銘柄コード (米国株なら入力)", placeholder="例: AAPL, TSLA, VOO")
            st.caption("※Tickerを入れると、数量×最新株価で計算します。入れないと入力数値をそのまま金額として扱います。")

            if st.form_submit_button("追加"):
                # 空文字ならNoneにする
                ticker_val = ticker_in if ticker_in.strip() != "" else None
                add_asset(name_in, cat_in, amt_in, curr_in, ticker_val)
                st.success("追加しました")
                st.rerun()

    # データ表示ロジック
    df_assets = fetch_assets()
    
    if not df_assets.empty:
        # --- 計算ロジック（ここが心臓部） ---
        current_prices = {} # キャッシュ用
        
        def calculate_value(row):
            qty = row['amount']
            currency = row['currency']
            ticker = row['ticker']
            
            # 1. 銘柄コードがある場合（株価 × 株数）
            if ticker and currency == 'USD':
                # 同じ銘柄を何度もAPIで叩かないようにキャッシュ確認
                if ticker not in current_prices:
                    price = get_stock_price(ticker)
                    current_prices[ticker] = price if price else 0
                
                stock_price = current_prices[ticker]
                # 株価(ドル) × 株数 × ドル円レート
                return qty * stock_price * usd_rate
            
            # 2. 仮想通貨の場合
            elif currency == 'BTC':
                return qty * btc_price
            
            # 3. ただのドルの場合
            elif currency == 'USD':
                return qty * usd_rate
            
            # 4. 円の場合
            else:
                return qty

        # 計算実行
        with st.spinner('最新株価を取得して計算中...'):
            df_assets['current_val_jpy'] = df_assets.apply(calculate_value, axis=1)

        # 総資産
        total_val = df_assets['current_val_jpy'].sum()
        st.metric("総資産評価額 (リアルタイム)", f"¥{total_val:,.0f}", delta=f"1USD = {usd_rate}円")

        # グラフ
        col1, col2 = st.columns([1, 1])
        with col1:
            fig = px.pie(df_assets, values='current_val_jpy', names='category', title="ポートフォリオ割合")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            # 表示用データフレーム整形
            show_df = df_assets[['name', 'amount', 'ticker', 'current_val_jpy']].copy()
            show_df['current_val_jpy'] = show_df['current_val_jpy'].apply(lambda x: f"¥{x:,.0f}")
            st.dataframe(show_df, use_container_width=True)
            
            del_id = st.number_input("削除ID", 0)
            if st.button("削除"):
                delete_asset(del_id)
                st.rerun()
    else:
        st.info("データがありません")

# ==========================================
# タブ2：家計簿機能 (変更なしだが連携維持)
# ==========================================
with tab2:
    st.header("家計簿入力")
    with st.form("budget_form"):
        d1, d2 = st.columns(2)
        date_in = d1.date_input("日付", datetime.date.today())
        type_in = d2.radio("収支", ["支出", "収入"], horizontal=True)
        
        c1, c2, c3 = st.columns(3)
        cat_in = c1.selectbox("カテゴリ", ["食費", "投資", "給与", "その他"])
        amt_in = c2.number_input("金額 (円)", min_value=0)
        memo_in = c3.text_input("メモ")
        
        # 資産連携オプション
        st.markdown("---")
        is_link = st.checkbox("資産としても追加する (株購入など)")
        l1, l2, l3 = st.columns(3)
        l_curr = l1.selectbox("資産通貨", ["USD", "JPY", "BTC"])
        l_qty = l2.number_input("購入数量 (株数)", min_value=0.0)
        l_ticker = l3.text_input("銘柄コード (例: AAPL)", help="入力すると株価連動します")

        if st.form_submit_button("記録する"):
            # 家計簿保存
            add_transaction(date_in, type_in, cat_in, amt_in, memo_in)
            # 資産保存（連携時）
            if is_link:
                t_val = l_ticker if l_ticker.strip() != "" else None
                add_asset(memo_in, "新規購入", l_qty, l_curr, t_val)
                st.success("家計簿と資産の両方に記録しました！")
            else:
                st.success("記録しました")
            st.rerun()
            
    # 家計簿履歴表示
    df_trans = fetch_transactions()
    if not df_trans.empty:
        st.dataframe(df_trans, hide_index=True)
