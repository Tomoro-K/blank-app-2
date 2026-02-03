import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import yfinance as yf
from supabase import create_client, Client
import datetime
from datetime import timedelta

# --- 1. 設定とSupabase接続 ---
st.set_page_config(page_title="Asset & Budget Master", layout="wide")

# シークレット管理
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. データ取得・計算API ---

# (A) 市場指標
@st.cache_data(ttl=300)
def get_market_indices():
    tickers = {"S&P 500": "^GSPC", "日経平均": "^N225", "NASDAQ": "^IXIC", "USD/JPY": "JPY=X"}
    data = {}
    try:
        for name, ticker in tickers.items():
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if len(hist) > 0:
                latest = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else latest
                change = latest - prev
                pct = (change / prev) * 100
                data[name] = {"price": latest, "change": change, "pct": pct}
    except:
        pass
    return data

# (B) 個別株価
@st.cache_data(ttl=3600)
def get_stock_price(ticker):
    if not ticker or ticker == "-": return None
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty: return hist['Close'].iloc[-1]
    except: return None

# (C) 仮想通貨
@st.cache_data(ttl=600)
def get_crypto_price(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=jpy"
        return requests.get(url).json()[coin_id]["jpy"]
    except: return 0.0

# --- 3. データベース操作 & 連動ロジック ---

def fetch_assets():
    return pd.DataFrame(supabase.table("assets").select("*").order("amount", desc=True).execute().data)

# 資産残高を直接更新する関数（家計簿連動用）
def update_asset_balance(asset_id, amount_change):
    # 現在の額を取得
    res = supabase.table("assets").select("amount").eq("id", asset_id).execute()
    if res.data:
        current_amount = res.data[0]['amount']
        new_amount = current_amount + amount_change
        # 更新
        supabase.table("assets").update({"amount": new_amount}).eq("id", asset_id).execute()

def add_asset(name, category, amount, currency, ticker=None):
    data = {"name": name, "category": category, "amount": amount, "currency": currency, "ticker": ticker}
    supabase.table("assets").insert(data).execute()

def delete_asset(asset_id):
    supabase.table("assets").delete().eq("id", asset_id).execute()

# 履歴（推移）保存
def save_daily_snapshot(total_value):
    today = str(datetime.date.today())
    existing = supabase.table("asset_history").select("*").eq("date", today).execute()
    if not existing.data:
        supabase.table("asset_history").insert({"date": today, "total_value": total_value}).execute()
    else:
        supabase.table("asset_history").update({"total_value": total_value}).eq("id", existing.data[0]['id']).execute()

def fetch_history(days):
    start = datetime.date.today() - timedelta(days=days)
    return pd.DataFrame(supabase.table("asset_history").select("*").gte("date", str(start)).order("date").execute().data)

def fetch_transactions():
    return pd.DataFrame(supabase.table("transactions").select("*").order("date", desc=True).limit(50).execute().data)

def add_transaction(date, type_, category, amount, memo):
    data = {"date": str(date), "type": type_, "category": category, "amount": amount, "memo": memo}
    supabase.table("transactions").insert(data).execute()

def delete_transaction(trans_id):
    supabase.table("transactions").delete().eq("id", trans_id).execute()


# --- 4. アプリケーション本体 ---

# サイドバー：市場指標
st.sidebar.title("📊 Market Watch")
indices = get_market_indices()
if indices:
    for name, info in indices.items():
        color = "normal" if info['change'] >= 0 else "inverse"
        st.sidebar.metric(name, f"{info['price']:,.2f}", f"{info['pct']:.2f}%", delta_color=color)

st.title("💰 Asset & Budget Dashboard")

# 共通変数
df_assets = fetch_assets()
usd_rate = indices["USD/JPY"]["price"] if "USD/JPY" in indices else 150.0
btc_price = get_crypto_price("bitcoin")
total_assets_jpy = 0

# 資産評価額の計算
if not df_assets.empty:
    current_vals = []
    for _, row in df_assets.iterrows():
        val = 0
        p = get_stock_price(row['ticker']) if row['ticker'] else 1
        price = p if p else 1
        
        if row['currency'] == 'USD': val = row['amount'] * price * usd_rate
        elif row['currency'] == 'BTC': val = row['amount'] * btc_price
        else: val = row['amount'] * price # JPY or others
        
        current_vals.append(val)
    
    df_assets['current_val_jpy'] = current_vals
    total_assets_jpy = df_assets['current_val_jpy'].sum()
    save_daily_snapshot(total_assets_jpy)

# トップ：総資産表示
st.metric("現在の総資産額", f"¥{total_assets_jpy:,.0f}", delta="Real-time Valuation")

st.divider()

# ★★★ レイアウト統合：左＝資産(Stock) / 右＝家計(Flow) ★★★
col_left, col_right = st.columns([1, 1])

# ==========================================
# 左カラム：資産管理 & チャート
# ==========================================
with col_left:
    st.subheader("📈 資産推移 & ポートフォリオ")
    
    # グラフエリア
    period = st.radio("期間", ["1ヶ月", "1年", "全期間"], horizontal=True, key="period_select")
    days_map = {"1ヶ月": 30, "1年": 365, "全期間": 3650}
    df_hist = fetch_history(days_map[period])
    
    if not df_hist.empty:
        df_hist['date'] = pd.to_datetime(df_hist['date'])
        fig_line = px.line(df_hist, x='date', y='total_value', title="資産推移", markers=True)
        st.plotly_chart(fig_line, use_container_width=True)
    
    if not df_assets.empty and total_assets_jpy > 0:
        fig_pie = px.pie(df_assets, values='current_val_jpy', names='category', title="資産構成", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("🏦 資産リスト (手動管理)")
    
    # 資産追加
    with st.expander("➕ 新規資産を追加"):
        with st.form("add_asset"):
            c1, c2 = st.columns(2)
            nm = c1.text_input("名称 (例: 現金, S&P500)")
            cat = c2.selectbox("カテゴリ", ["現金・預金", "株式", "投資信託", "暗号資産", "その他"])
            c3, c4 = st.columns(2)
            amt = c3.number_input("数量/金額", min_value=0.0)
            cur = c4.selectbox("通貨", ["JPY", "USD", "BTC"])
            tick = st.text_input("銘柄コード (任意)", placeholder="AAPL, VOO etc.")
            if st.form_submit_button("追加"):
                t_val = tick if tick.strip() else None
                add_asset(nm, cat, amt, cur, t_val)
                st.rerun()

    # リスト表示
    if not df_assets.empty:
        show_df = df_assets[['name', 'amount', 'currency', 'current_val_jpy']].copy()
        show_df['current_val_jpy'] = show_df['current_val_jpy'].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(show_df, use_container_width=True)
        
        # 削除
        with st.popover("資産を削除"):
            del_id = st.selectbox("削除する資産", df_assets['id'].astype(str) + ": " + df_assets['name'])
            if st.button("削除実行"):
                delete_asset(int(del_id.split(":")[0]))
                st.rerun()

# ==========================================
# 右カラム：家計簿 (資産連動型)
# ==========================================
with col_right:
    st.subheader("📝 収支入力 (資産連動)")
    
    # 家計簿入力フォーム
    with st.container(border=True):
        date_in = st.date_input("日付", datetime.date.today())
        type_in = st.radio("収支", ["支出", "収入"], horizontal=True)
        
        # --- 豊富なカテゴリ ---
        if type_in == "支出":
            cats = [
                "食費", "日用品", "交通費", "交際費", "趣味・娯楽", "衣服・美容", 
                "健康・医療", "通信費", "水道・光熱費", "住居費", 
                "教育・教養", "保険", "投資・金融", "特別な支出", "その他"
            ]
        else:
            cats = ["給与", "賞与", "事業・副業", "配当・利子", "お小遣い", "臨時収入", "その他"]
        
        cat_in = st.selectbox("カテゴリ", cats)
        
        c_amt, c_memo = st.columns([1, 1.5])
        amt_in = c_amt.number_input("金額 (円)", min_value=0, step=100)
        memo_in = c_memo.text_input("メモ")

        # --- ★完全連動のキモ：決済/入金資産の選択 ---
        st.markdown("---")
        st.markdown(f"**{'支払元' if type_in=='支出' else '入金先'}の資産を選択 (残高に反映)**")
        
        if not df_assets.empty:
            # 選択肢を作成 (IDと名前の紐付け)
            asset_opts = {f"{row['name']} (残: {row['amount']:,.0f})": row['id'] for _, row in df_assets.iterrows()}
            selected_asset_label = st.selectbox("対象資産", list(asset_opts.keys()))
            selected_asset_id = asset_opts[selected_asset_label]
        else:
            st.warning("先に左側で資産（現金や銀行）を登録してください")
            selected_asset_id = None
        
        # --- 投資の場合のオプション ---
        is_investment = (cat_in == "投資・金融")
        invest_ticker = None
        invest_amount_shares = 0.0
        invest_currency = "USD"
        
        if is_investment and type_in == "支出":
            st.info("💡 投資資産（株など）をポートフォリオに追加しますか？")
            with st.expander("購入資産の詳細入力", expanded=True):
                i_c1, i_c2 = st.columns(2)
                invest_name = i_c1.text_input("資産名 (例: VOO)", value=memo_in)
                invest_ticker = i_c2.text_input("銘柄コード", placeholder="VOO")
                i_c3, i_c4 = st.columns(2)
                invest_amount_shares = i_c3.number_input("購入数量 (株数)", min_value=0.0)
                invest_currency = i_c4.selectbox("資産通貨", ["USD", "JPY", "BTC"])

        # 送信ボタン処理
        if st.button("記録して反映", type="primary"):
            if not selected_asset_id:
                st.error("資産が登録されていません")
            else:
                # 1. Transaction記録
                add_transaction(date_in, type_in, cat_in, amt_in, memo_in)
                
                # 2. 資産残高の更新 (連動)
                if type_in == "支出":
                    update_asset_balance(selected_asset_id, -amt_in) # 減らす
                else:
                    update_asset_balance(selected_asset_id, amt_in)  # 増やす
                
                # 3. 投資の場合の新規資産追加
                if is_investment and type_in == "支出" and invest_amount_shares > 0:
                    add_asset(invest_name, "株式", invest_amount_shares, invest_currency, invest_ticker)
                    st.success(f"支出を記録し、{selected_asset_label}から減算、資産{invest_name}を追加しました！")
                else:
                    st.success(f"記録しました！ {selected_asset_label}の残高を更新しました。")
                
                st.rerun()

    # 直近の履歴
    st.subheader("📜 最近の収支")
    df_trans = fetch_transactions()
    if not df_trans.empty:
        st.dataframe(df_trans[['date', 'type', 'category', 'amount', 'memo']], use_container_width=True, hide_index=True)
        if st.button("最新履歴を削除"):
            delete_transaction(df_trans.iloc[0]['id'])
            st.rerun()
