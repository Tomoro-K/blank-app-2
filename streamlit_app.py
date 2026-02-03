import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import yfinance as yf
from supabase import create_client, Client
import datetime
from datetime import timedelta

# --- 1. 設定とSupabase接続 ---
st.set_page_config(page_title="Ultimate Asset Manager", layout="wide")

# シークレット管理
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except:
    st.error("SupabaseのURLとKEYが設定されていません。Secretsを設定してください。")
    st.stop()

supabase: Client = create_client(url, key)

# --- 2. データ取得・計算API ---

# (A) 市場指標（大幅増量）
@st.cache_data(ttl=300)
def get_market_indices():
    tickers = {
        "🇺🇸 S&P 500": "^GSPC",
        "🇯🇵 日経平均": "^N225",
        "🇺🇸 NASDAQ": "^IXIC",
        "💴 USD/JPY": "JPY=X",
        "🥇 金 (Gold)": "GC=F",
        "🛢️ 原油 (WTI)": "CL=F",
        "😨 VIX指数": "^VIX",
        "₿ BTC/USD": "BTC-USD",
        "🏦 米10年国債": "^TNX"
    }
    data = {}
    try:
        # yfinanceでまとめて取得
        for name, ticker in tickers.items():
            stock = yf.Ticker(ticker)
            # 2日分のデータを取って前日比を計算
            hist = stock.history(period="5d") # 休日またぎ対応のため少し長めに
            if len(hist) > 1:
                latest = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = latest - prev
                pct = (change / prev) * 100
                data[name] = {"price": latest, "change": change, "pct": pct}
    except Exception as e:
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

def fetch_transactions():
    return pd.DataFrame(supabase.table("transactions").select("*").order("date", desc=True).limit(100).execute().data)

# 資産残高の更新（存在しなければ新規作成、あれば更新）
def upsert_asset(name, category, amount_change, currency="JPY", ticker=None):
    # 既存チェック
    existing = supabase.table("assets").select("*").eq("name", name).execute()
    
    if existing.data:
        # 更新
        rec_id = existing.data[0]['id']
        current_amount = existing.data[0]['amount']
        new_amount = current_amount + amount_change
        # マイナスにならないよう制御（オプション）
        if new_amount < 0 and category != "クレジットカード":
            st.warning(f"注意: {name} の残高がマイナスになります")
        
        supabase.table("assets").update({"amount": new_amount}).eq("id", rec_id).execute()
    else:
        # 新規作成（収入入力時など）
        data = {
            "name": name, 
            "category": category, 
            "amount": amount_change, # 初期額
            "currency": currency, 
            "ticker": ticker
        }
        supabase.table("assets").insert(data).execute()

def add_transaction(date, type_, category, amount, memo):
    data = {"date": str(date), "type": type_, "category": category, "amount": amount, "memo": memo}
    supabase.table("transactions").insert(data).execute()

def delete_transaction(trans_id):
    # 本当はトランザクション削除時に資産残高も戻すべきだが、今回は簡易実装のためログ削除のみ
    supabase.table("transactions").delete().eq("id", trans_id).execute()

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


# --- 4. アプリケーション本体 ---

# ■ サイドバー：マーケット指標（リアルタイム）
st.sidebar.markdown("### 🌏 Market Watch")
indices = get_market_indices()
if indices:
    for name, info in indices.items():
        color = "normal" if info['change'] >= 0 else "inverse"
        # 価格のフォーマット調整
        if "USD" in name or "国債" in name or "VIX" in name:
            fmt = "{:,.2f}"
        else:
            fmt = "{:,.0f}"
        
        st.sidebar.metric(
            label=name,
            value=fmt.format(info['price']),
            delta=f"{info['pct']:.2f}%",
            delta_color=color
        )
else:
    st.sidebar.info("指標データを取得中...")

# ■ メイン画面
st.title("📊 Asset & Budget Dashboard")

# 共通データ取得
df_assets = fetch_assets()
usd_rate = indices["USD/JPY"]["price"] if (indices and "USD/JPY" in indices) else 150.0
btc_price = get_crypto_price("bitcoin")

# 資産評価額の計算（時価）
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
    save_daily_snapshot(total_assets_jpy)

# トップKPI
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("現在の総資産額", f"¥{total_assets_jpy:,.0f}", delta="Real-time Valuation")
# 現金比率計算
cash_assets = df_assets[df_assets['category'].str.contains('現金|預金|銀行')]['current_val_jpy'].sum() if not df_assets.empty else 0
risk_assets = total_assets_jpy - cash_assets
kpi2.metric("リスク資産", f"¥{risk_assets:,.0f}")
kpi3.metric("安全資産 (現金等)", f"¥{cash_assets:,.0f}")

st.divider()

# ■ グラフエリア（3列構成）
st.subheader("📈 資産と収支の分析")
g_col1, g_col2, g_col3 = st.columns(3)

# 1. 資産推移（折れ線）
with g_col1:
    st.markdown("**資産推移**")
    period = st.select_slider("期間", options=["1週間", "1ヶ月", "3ヶ月", "1年", "全期間"], value="1ヶ月")
    days_map = {"1週間": 7, "1ヶ月": 30, "3ヶ月": 90, "1年": 365, "全期間": 3650}
    df_hist = fetch_history(days_map[period])
    if not df_hist.empty:
        df_hist['date'] = pd.to_datetime(df_hist['date'])
        fig_line = px.line(df_hist, x='date', y='total_value', markers=True)
        fig_line.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=250)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("データ収集中...")

# 2. ポートフォリオ（円グラフ）
with g_col2:
    st.markdown("**ポートフォリオ**")
    if not df_assets.empty and total_assets_jpy > 0:
        fig_pie = px.pie(df_assets, values='current_val_jpy', names='category', hole=0.4)
        fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0), height=250)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("資産データがありません")

# 3. カテゴリ別収支（棒グラフ）
with g_col3:
    st.markdown("**カテゴリ別支出 (直近)**")
    df_trans = fetch_transactions()
    if not df_trans.empty:
        # 支出のみフィルタリング
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

# ■ 入力エリア（ここですべて完結させる）
st.subheader("📝 入出金・資産管理")

with st.container(border=True):
    # 入力タイプの選択
    input_type = st.radio("アクション", ["支出 (支払)", "収入 (給与・残高追加)", "資産購入・振替 (株購入など)"], horizontal=True)
    
    date_in = st.date_input("日付", datetime.date.today())
    
    # --- A. 支出 (資産が減る) ---
    if input_type == "支出 (支払)":
        c1, c2 = st.columns(2)
        cat_in = c1.selectbox("カテゴリ", ["食費", "日用品", "交通費", "交際費", "住居費", "光熱費", "通信費", "医療費", "教育費", "その他"])
        memo_in = c2.text_input("メモ (店名など)")
        
        c3, c4 = st.columns(2)
        amt_in = c3.number_input("金額 (円)", min_value=0, step=100)
        
        # 支払元資産を選ぶ
        if not df_assets.empty:
            asset_opts = {f"{r['name']} (残: {r['amount']:,.0f})": r['name'] for _, r in df_assets.iterrows()}
            pay_source = c4.selectbox("支払元資産", list(asset_opts.keys()))
            source_name = asset_opts[pay_source]
        else:
            c4.warning("資産がありません。先に「収入」で資産を登録してください")
            source_name = None

        if st.button("支出を記録", type="primary"):
            if source_name:
                add_transaction(date_in, "支出", cat_in, amt_in, memo_in)
                upsert_asset(source_name, "不明", -amt_in) # 残高を減らす
                st.success("記録しました！")
                st.rerun()

    # --- B. 収入 (資産が増える / 新規作成) ---
    elif input_type == "収入 (給与・残高追加)":
        c1, c2 = st.columns(2)
        cat_in = c1.selectbox("カテゴリ", ["給与", "賞与", "副業", "お小遣い", "初期残高", "臨時収入", "配当金"])
        memo_in = c2.text_input("メモ")
        
        c3, c4 = st.columns(2)
        amt_in = c3.number_input("金額 (円)", min_value=0, step=1000)
        
        # 入金先（既存から選ぶ or 新規入力）
        asset_mode = c4.radio("入金先", ["既存の資産", "新しい資産を作成"], horizontal=True)
        target_name = None
        target_cat = "現金・預金" # デフォルト
        
        if asset_mode == "既存の資産":
            if not df_assets.empty:
                asset_opts = {f"{r['name']}": r['name'] for _, r in df_assets.iterrows()}
                sel = st.selectbox("資産を選択", list(asset_opts.keys()))
                target_name = asset_opts[sel]
            else:
                st.warning("資産がありません。「新しい資産」を選んでください")
        else:
            n1, n2 = st.columns(2)
            target_name = n1.text_input("資産名 (例: 三井住友銀行, 財布)")
            target_cat = n2.selectbox("資産カテゴリ", ["現金・預金", "電子マネー", "その他"])
        
        if st.button("収入を記録", type="primary"):
            if target_name:
                add_transaction(date_in, "収入", cat_in, amt_in, memo_in)
                upsert_asset(target_name, target_cat, amt_in) # 残高を増やす/作成
                st.success(f"{target_name} に入金しました！")
                st.rerun()

    # --- C. 資産購入・振替 (資産Aが減り、資産Bが増える) ---
    elif input_type == "資産購入・振替 (株購入など)":
        st.info("💡 銀行口座などから資金を移動して、投資商品を購入します")
        
        col_pay, col_buy = st.columns(2)
        
        with col_pay:
            st.markdown("**1. 資金元 (減る資産)**")
            if not df_assets.empty:
                pay_opts = {f"{r['name']}": r['name'] for _, r in df_assets.iterrows()}
                pay_sel = st.selectbox("支払元", list(pay_opts.keys()), key="pay_src")
                pay_name = pay_opts[pay_sel]
            else:
                st.warning("資産がありません")
                pay_name = None
            pay_amt = st.number_input("支払金額 (円)", min_value=0, step=1000)
        
        with col_buy:
            st.markdown("**2. 購入先 (増える資産)**")
            buy_mode = st.radio("購入対象", ["既存の資産に追加入金", "新規銘柄を購入"], horizontal=True)
            
            buy_name = None
            buy_ticker = None
            buy_qty = 0
            buy_curr = "JPY"
            buy_cat = "株式"
            
            if buy_mode == "既存の資産に追加入金":
                if not df_assets.empty:
                    buy_opts = {f"{r['name']}": r['name'] for _, r in df_assets.iterrows()}
                    buy_sel = st.selectbox("入金先", list(buy_opts.keys()), key="buy_target")
                    buy_name = buy_opts[buy_sel]
                    # 既存の場合は通貨などは既存データを引き継ぐため入力不要、数量だけ聞く
                    # ただし今回は簡易化のため金額ベースの移動とみなすか、数量を聞くか
                    buy_qty = st.number_input("追加数量 (株数など)", min_value=0.0)
                else:
                    st.warning("資産なし")
            else:
                buy_name = st.text_input("銘柄名 (例: Tesla)")
                buy_ticker = st.text_input("銘柄コード (例: TSLA)")
                c_b1, c_b2, c_b3 = st.columns(3)
                buy_qty = c_b1.number_input("購入数量", min_value=0.0)
                buy_curr = c_b2.selectbox("通貨", ["USD", "JPY", "BTC"])
                buy_cat = c_b3.selectbox("カテゴリ", ["株式", "投資信託", "暗号資産", "債券"])

        if st.button("振替・購入を実行", type="primary"):
            if pay_name and (buy_name or buy_mode == "既存"):
                # 1. 支払元を減らす
                upsert_asset(pay_name, "不明", -pay_amt)
                
                # 2. 購入先を増やす
                # 既存資産への追加の場合、名前解決が必要
                target_asset_name = buy_name if buy_name else buy_name # 既存ロジック要調整
                
                if buy_mode == "新規銘柄を購入":
                    upsert_asset(buy_name, buy_cat, buy_qty, buy_curr, buy_ticker)
                else:
                    # 既存資産の数量を増やす (通貨判定などが複雑だが、簡易的に数量を加算)
                    upsert_asset(buy_name, "不明", buy_qty)
                
                # 3. 履歴に残す
                memo_txt = f"{pay_name}から{buy_name}を購入"
                add_transaction(date_in, "振替", "資産運用", pay_amt, memo_txt)
                
                st.success("資産移動が完了しました！")
                st.rerun()

st.divider()

# ■ 直近の履歴表示
st.markdown("##### 📜 直近の履歴")
if not df_trans.empty:
    st.dataframe(df_trans[['date', 'type', 'category', 'amount', 'memo']], use_container_width=True, hide_index=True)
