import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import yfinance as yf
from supabase import create_client, Client
import datetime
from datetime import timedelta
import random # デモデータ生成用

# --- 1. 設定とSupabase接続 ---
st.set_page_config(page_title="Ultimate Asset Manager", layout="wide")

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except:
    st.error("SupabaseのURLとKEYが設定されていません。")
    st.stop()

supabase: Client = create_client(url, key)

# --- 2. データ取得・計算API ---
@st.cache_data(ttl=300)
def get_market_indices():
    tickers = {
        "🇺🇸 S&P 500": "^GSPC", "🇯🇵 日経平均": "^N225", "💴 USD/JPY": "JPY=X",
        "🥇 金 (Gold)": "GC=F", "₿ BTC/USD": "BTC-USD"
    }
    data = {}
    try:
        for name, ticker in tickers.items():
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) > 1:
                latest = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = latest - prev
                pct = (change / prev) * 100
                data[name] = {"price": latest, "change": change, "pct": pct}
    except: pass
    return data

@st.cache_data(ttl=3600)
def get_stock_price(ticker):
    if not ticker or ticker == "-": return None
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty: return hist['Close'].iloc[-1]
    except: return None

@st.cache_data(ttl=600)
def get_crypto_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=jpy"
        return requests.get(url).json()[coin_id]["jpy"]
    except: return 0.0

# --- 3. データベース操作 ---
def fetch_assets():
    try:
        return pd.DataFrame(supabase.table("assets").select("*").execute().data)
    except: return pd.DataFrame()

def fetch_transactions():
    try:
        return pd.DataFrame(supabase.table("transactions").select("*").order("date", desc=True).limit(50).execute().data)
    except: return pd.DataFrame()

def upsert_asset(name, category, amount_change, currency="JPY", ticker=None):
    existing = supabase.table("assets").select("*").eq("name", name).execute()
    if existing.data:
        rec_id = existing.data[0]['id']
        new_amount = existing.data[0]['amount'] + amount_change
        supabase.table("assets").update({"amount": new_amount}).eq("id", rec_id).execute()
    else:
        data = {"name": name, "category": category, "amount": amount_change, "currency": currency, "ticker": ticker}
        supabase.table("assets").insert(data).execute()

def add_transaction(date, type_, category, amount, memo):
    data = {"date": str(date), "type": type_, "category": category, "amount": amount, "memo": memo}
    supabase.table("transactions").insert(data).execute()

# 履歴保存
def save_daily_snapshot(total_value):
    try:
        today = str(datetime.date.today())
        existing = supabase.table("asset_history").select("*").eq("date", today).execute()
        if not existing.data:
            supabase.table("asset_history").insert({"date": today, "total_value": total_value}).execute()
        else:
            supabase.table("asset_history").update({"total_value": total_value}).eq("id", existing.data[0]['id']).execute()
    except Exception as e:
        st.sidebar.error(f"履歴保存エラー: {e}")

def fetch_history(days):
    try:
        start = datetime.date.today() - timedelta(days=days)
        return pd.DataFrame(supabase.table("asset_history").select("*").gte("date", str(start)).order("date").execute().data)
    except: return pd.DataFrame()

# ★ デモデータ生成機能（グラフ表示用） ★
def generate_demo_data():
    # 過去30日分のダミーデータを作成
    base_val = 1000000 # 100万円からスタート
    for i in range(30):
        d = datetime.date.today() - timedelta(days=30-i)
        val = base_val * (1 + (random.random() - 0.4) * 0.1) # ランダム変動
        # 存在チェックせずにインサート（簡易実装）
        try:
            supabase.table("asset_history").insert({"date": str(d), "total_value": int(val)}).execute()
        except: pass
    st.toast("デモデータを生成しました！")

# --- 4. アプリ本体 ---

# サイドバー
st.sidebar.markdown("### 🌏 Market Watch")
indices = get_market_indices()
if indices:
    for name, info in indices.items():
        color = "normal" if info['change'] >= 0 else "inverse"
        st.sidebar.metric(name, f"{info['price']:,.0f}", f"{info['pct']:.2f}%", delta_color=color)

# ★ここにデモボタンを追加★
st.sidebar.divider()
if st.sidebar.button("🛠️ グラフ用デモデータ生成"):
    generate_demo_data()
    st.rerun()

st.title("📊 Asset & Budget Dashboard")

# 共通データ処理
df_assets = fetch_assets()
usd_rate = indices["USD/JPY"]["price"] if (indices and "USD/JPY" in indices) else 150.0
btc_price = get_crypto_price("bitcoin")

total_assets_jpy = 0
if not df_assets.empty:
    current_vals = []
    for _, row in df_assets.iterrows():
        val = 0
        p = get_stock_price(row['ticker']) if row['ticker'] else 1
        price = p if p else 1
        
        if row['currency'] == 'USD': val = row['amount'] * price * usd_rate
        elif row['currency'] == 'BTC': val = row['amount'] * btc_price
        else: val = row['amount'] * price
        current_vals.append(val)
    
    df_assets['current_val_jpy'] = current_vals
    total_assets_jpy = df_assets['current_val_jpy'].sum()
    
    # 履歴保存（エラーが出ても止まらないようにtry-except）
    save_daily_snapshot(total_assets_jpy)

# トップKPI
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("現在の総資産額", f"¥{total_assets_jpy:,.0f}")
cash_assets = df_assets[df_assets['category'].str.contains('現金|預金|銀行')]['current_val_jpy'].sum() if not df_assets.empty else 0
kpi2.metric("リスク資産", f"¥{total_assets_jpy - cash_assets:,.0f}")
kpi3.metric("安全資産", f"¥{cash_assets:,.0f}")

st.divider()

# グラフエリア
st.subheader("📈 資産と収支の分析")
g_col1, g_col2, g_col3 = st.columns(3)

# 1. 資産推移
with g_col1:
    st.markdown("**資産推移**")
    df_hist = fetch_history(365)
    if not df_hist.empty:
        df_hist['date'] = pd.to_datetime(df_hist['date'])
        # データが1点だけでも表示できるようにmarkers=True
        fig_line = px.line(df_hist, x='date', y='total_value', markers=True)
        fig_line.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=250)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("👈 サイドバーの「デモデータ生成」を押すとグラフが出ます")

# 2. ポートフォリオ
with g_col2:
    st.markdown("**ポートフォリオ**")
    if not df_assets.empty and total_assets_jpy > 0:
        fig_pie = px.pie(df_assets, values='current_val_jpy', names='category', hole=0.4)
        fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=250)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("資産データがありません")

# 3. カテゴリ別収支
with g_col3:
    st.markdown("**支出内訳 (最新50件)**")
    df_trans = fetch_transactions()
    if not df_trans.empty:
        df_exp = df_trans[df_trans['type'] == '支出']
        if not df_exp.empty:
            df_cat = df_exp.groupby('category')['amount'].sum().reset_index()
            fig_bar = px.bar(df_cat, x='category', y='amount', color='category')
            fig_bar.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=250)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("支出データがありません")
    else:
        st.info("家計簿データがありません")

st.divider()

# 入力フォーム（簡易版）
st.subheader("📝 入出金入力")
with st.container(border=True):
    date_in = st.date_input("日付", datetime.date.today())
    type_in = st.radio("収支", ["支出", "収入"], horizontal=True)
    cat_in = st.text_input("カテゴリ (食費, 給与など)", "食費")
    amt_in = st.number_input("金額", min_value=0)
    memo_in = st.text_input("メモ")
    
    # 資産更新用（簡易）
    asset_name = st.text_input("対象資産名 (例: 現金, 銀行)", "現金")
    
    if st.button("記録"):
        # トランザクション
        add_transaction(date_in, type_in, cat_in, amt_in, memo_in)
        # 資産更新
        change = amt_in if type_in == "収入" else -amt_in
        upsert_asset(asset_name, "流動資産", change)
        st.success("記録しました")
        st.rerun()
