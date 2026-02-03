import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import yfinance as yf
from supabase import create_client, Client
import datetime
from datetime import timedelta

# --- 1. 設定とSupabase接続 ---
st.set_page_config(page_title="Asset Master", layout="wide")

# シークレット管理
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. データ取得・計算関数 ---

# (A) 市場の主要指標を取得 (S&P500, 日経平均, ドル円)
@st.cache_data(ttl=300) # 5分キャッシュ
def get_market_indices():
    tickers = {
        "S&P 500": "^GSPC",
        "日経平均": "^N225",
        "NASDAQ": "^IXIC",
        "USD/JPY": "JPY=X"
    }
    data = {}
    try:
        for name, ticker in tickers.items():
            stock = yf.Ticker(ticker)
            # 直近のデータを取得
            hist = stock.history(period="2d")
            if len(hist) > 0:
                latest = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else latest
                change = latest - prev
                pct_change = (change / prev) * 100
                data[name] = {"price": latest, "change": change, "pct": pct_change}
    except Exception as e:
        st.error(f"指標取得エラー: {e}")
    return data

# (B) 個別株価取得
@st.cache_data(ttl=3600)
def get_stock_price(ticker):
    if not ticker or ticker == "-": return None
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
    except:
        return None
    return None

# (C) 仮想通貨取得
@st.cache_data(ttl=600)
def get_crypto_price(coin_id):
    try:
        api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=jpy"
        return requests.get(api_url).json()[coin_id]["jpy"]
    except:
        return 0.0

# --- 3. データベース操作 ---
def fetch_assets():
    return pd.DataFrame(supabase.table("assets").select("*").execute().data)

def add_asset(name, category, amount, currency, ticker=None):
    data = {"name": name, "category": category, "amount": amount, "currency": currency, "ticker": ticker}
    supabase.table("assets").insert(data).execute()

def delete_asset(asset_id):
    supabase.table("assets").delete().eq("id", asset_id).execute()

# --- 4. 履歴(推移)管理ロジック ---
def save_daily_snapshot(total_value):
    today = datetime.date.today()
    # 今日のデータが既にあるか確認
    existing = supabase.table("asset_history").select("*").eq("date", str(today)).execute()
    
    if not existing.data:
        # なければ新規保存
        supabase.table("asset_history").insert({"date": str(today), "total_value": total_value}).execute()
    else:
        # あれば更新 (Update)
        rec_id = existing.data[0]['id']
        supabase.table("asset_history").update({"total_value": total_value}).eq("id", rec_id).execute()

def fetch_history(days):
    # 指定した日数分のデータを取得
    start_date = datetime.date.today() - timedelta(days=days)
    response = supabase.table("asset_history").select("*").gte("date", str(start_date)).order("date").execute()
    return pd.DataFrame(response.data)

# --- 5. アプリケーション本体 ---

# サイドバー：主要指標の表示
st.sidebar.title("📊 Market Indicators")
indices = get_market_indices()
if indices:
    for name, info in indices.items():
        # 色分け
        color = "normal" if info['change'] >= 0 else "inverse"
        st.sidebar.metric(
            label=name,
            value=f"{info['price']:,.2f}",
            delta=f"{info['pct']:.2f}%",
            delta_color=color
        )
else:
    st.sidebar.warning("指標データの取得に失敗しました")

st.title("💰 Smart Asset Manager")

# タブ構成
tab1, tab2, tab3 = st.tabs(["📈 ダッシュボード (分析)", "📝 資産管理 (登録)", "📒 家計簿 (収支)"])

# 共通データ計算（全タブで使うためここで実行）
df_assets = fetch_assets()
total_assets_jpy = 0
usd_rate = indices["USD/JPY"]["price"] if "USD/JPY" in indices else 150.0
btc_price = get_crypto_price("bitcoin")

if not df_assets.empty:
    # 現在価値計算ロジック
    current_vals = []
    for index, row in df_assets.iterrows():
        val = 0
        price_info = 1 # デフォルト倍率
        
        # 株価・API連携
        if row['ticker']:
            p = get_stock_price(row['ticker'])
            if p:
                price_info = p
                # ドル建て株の場合
                if row['currency'] == 'USD':
                    val = row['amount'] * p * usd_rate
                else:
                    val = row['amount'] * p
            else:
                # 取得失敗時は手入力額ベース
                val = row['amount'] * usd_rate if row['currency'] == 'USD' else row['amount']
        
        # 仮想通貨
        elif row['currency'] == 'BTC':
            val = row['amount'] * btc_price
        
        # 通常通貨
        elif row['currency'] == 'USD':
            val = row['amount'] * usd_rate
        else:
            val = row['amount']
            
        current_vals.append(val)

    df_assets['current_val_jpy'] = current_vals
    total_assets_jpy = df_assets['current_val_jpy'].sum()

    # ★ここで履歴テーブルに今日の分を自動保存
    save_daily_snapshot(total_assets_jpy)


# ==========================================
# タブ1：ダッシュボード (推移グラフ & 円グラフ)
# ==========================================
with tab1:
    # 1. 総資産表示
    st.metric("現在の総資産額", f"¥{total_assets_jpy:,.0f}", delta="Real-time Update")
    
    col_g1, col_g2 = st.columns([2, 1])

    # 2. 資産推移グラフ
    with col_g1:
        st.subheader("資産推移チャート")
        
        # 期間選択ボタン
        period = st.radio("表示期間", ["1週間", "1ヶ月", "1年", "全期間"], horizontal=True)
        
        days_map = {"1週間": 7, "1ヶ月": 30, "1年": 365, "全期間": 3650}
        days = days_map[period]
        
        # 履歴データ取得
        df_hist = fetch_history(days)
        
        if not df_hist.empty:
            df_hist['date'] = pd.to_datetime(df_hist['date'])
            fig_line = px.line(df_hist, x='date', y='total_value', markers=True, title="資産総額の推移")
            fig_line.update_layout(yaxis_tickformat=",.0f") # 軸を円表示に
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("📊 まだ履歴データがありません。明日以降、グラフが描画されます。")

    # 3. ポートフォリオ (円グラフ) - バグ修正済み
    with col_g2:
        st.subheader("ポートフォリオ")
        if not df_assets.empty and total_assets_jpy > 0:
            # カテゴリごとに集計
            df_pie = df_assets.groupby('category')['current_val_jpy'].sum().reset_index()
            fig_pie = px.pie(df_pie, values='current_val_jpy', names='category', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("データがないか、総資産が0円です")

# ==========================================
# タブ2：資産管理 (登録・削除)
# ==========================================
with tab2:
    st.header("資産リスト")
    
    # 登録フォーム
    with st.expander("➕ 資産を追加する"):
        with st.form("add_asset_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            name_in = c1.text_input("資産名 (例: Apple)")
            amt_in = c2.number_input("保有数 (株数/金額)", min_value=0.0)
            curr_in = c3.selectbox("通貨", ["JPY", "USD", "BTC"])
            
            c4, c5 = st.columns(2)
            cat_in = c4.selectbox("カテゴリ", ["株式", "投資信託", "預金", "仮想通貨"])
            ticker_in = c5.text_input("銘柄コード (例: AAPL, VOO)", help="Yahoo FinanceのTicker")
            
            if st.form_submit_button("追加"):
                t_val = ticker_in if ticker_in.strip() else None
                add_asset(name_in, cat_in, amt_in, curr_in, t_val)
                st.success("追加しました！")
                st.rerun()

    # リスト表示
    if not df_assets.empty:
        # 表示用に整形
        show_df = df_assets[['name', 'category', 'amount', 'ticker', 'current_val_jpy']].copy()
        show_df['current_val_jpy'] = show_df['current_val_jpy'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(show_df, use_container_width=True)
        
        # 削除
        d_id = st.number_input("削除するID", min_value=0)
        if st.button("削除実行"):
            delete_asset(d_id)
            st.rerun()

# ==========================================
# タブ3：家計簿 (簡易版)
# ==========================================
with tab3:
    st.header("家計簿入力")
    # ここに以前の家計簿コードを入れることも可能ですが
    # 今回は資産推移にフォーカスするためシンプルに資産へのリンクだけ案内
    st.info("家計簿データは資産推移グラフには直接反映されませんが、資産額の増減を通じて間接的に反映されます。")
    # 必要であればここに家計簿コードを追加してください
