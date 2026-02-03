import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from supabase import create_client, Client
import datetime

# --- 1. 設定とSupabase接続 ---
st.set_page_config(page_title="My Asset & Budget App", layout="wide")

# Secretsから読み込み
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. 外部API関数 ---
@st.cache_data(ttl=3600)
def get_usd_jpy_rate():
    try:
        api_url = "https://api.exchangerate-api.com/v4/latest/USD"
        return requests.get(api_url).json()["rates"]["JPY"]
    except:
        return 150.0

@st.cache_data(ttl=600)
def get_crypto_price(coin_id):
    try:
        api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=jpy"
        return requests.get(api_url).json()[coin_id]["jpy"]
    except:
        return 0.0

# --- 3. データベース操作関数 ---

# (A) 資産関連
def fetch_assets():
    response = supabase.table("assets").select("*").execute()
    return pd.DataFrame(response.data)

def add_asset(name, category, amount, currency):
    data = {"name": name, "category": category, "amount": amount, "currency": currency}
    supabase.table("assets").insert(data).execute()

def delete_asset(asset_id):
    supabase.table("assets").delete().eq("id", asset_id).execute()

# (B) 家計簿関連（New!）
def fetch_transactions():
    # 日付の新しい順に取得
    response = supabase.table("transactions").select("*").order("date", desc=True).execute()
    return pd.DataFrame(response.data)

def add_transaction(date, type_, category, amount, memo):
    data = {
        "date": str(date),
        "type": type_,
        "category": category,
        "amount": amount,
        "memo": memo
    }
    supabase.table("transactions").insert(data).execute()

def delete_transaction(trans_id):
    supabase.table("transactions").delete().eq("id", trans_id).execute()

# --- 4. アプリケーション本体 ---
st.title("💰 My Asset & Budget")

# APIデータ取得
usd_rate = get_usd_jpy_rate()
btc_price = get_crypto_price("bitcoin")

# ★★★ タブで画面を切り替え ★★★
tab1, tab2 = st.tabs(["🏦 資産管理 (Stock)", "📒 家計簿 (Flow)"])

# ==========================================
# タブ1：資産管理機能（以前の機能）
# ==========================================
with tab1:
    st.header("資産ポートフォリオ")
    
    # 資産入力フォーム（Expanderに収納してスッキリさせる）
    with st.expander("➕ 新しい資産を追加する"):
        with st.form("asset_form", clear_on_submit=True):
            col_a, col_b, col_c, col_d = st.columns(4)
            name_in = col_a.text_input("資産名", "S&P500")
            cat_in = col_b.selectbox("カテゴリ", ["現金", "株式", "投資信託", "暗号資産"])
            amt_in = col_c.number_input("金額/数量", min_value=0.0)
            curr_in = col_d.selectbox("通貨", ["JPY", "USD", "BTC"])
            if st.form_submit_button("追加"):
                add_asset(name_in, cat_in, amt_in, curr_in)
                st.success("追加しました")
                st.rerun()

    # 資産データ表示・計算
    df_assets = fetch_assets()
    if not df_assets.empty:
        # 円換算ロジック
        def convert(row):
            if row['currency'] == 'USD': return row['amount'] * usd_rate
            if row['currency'] == 'BTC': return row['amount'] * btc_price
            return row['amount']
        
        df_assets['amount_jpy'] = df_assets.apply(convert, axis=1)
        
        # 総資産表示
        total = df_assets['amount_jpy'].sum()
        st.metric("総資産額", f"¥{total:,.0f}", delta=f"1USD = {usd_rate}円")
        
        # グラフ
        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(df_assets, values='amount_jpy', names='category', title="資産比率")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.dataframe(df_assets[['name', 'amount_jpy', 'currency']], use_container_width=True)
            
            # 削除機能
            del_id = st.number_input("削除する資産ID", 0)
            if st.button("資産を削除"):
                delete_asset(del_id)
                st.rerun()
    else:
        st.info("資産データがありません。追加してください。")

# ==========================================
# タブ2：家計簿機能（新機能！）
# ==========================================
with tab2:
    st.header("家計簿・収支ログ")

    # 家計簿入力フォーム
    with st.container(): # デザイン枠
        st.markdown("#### 📝 今日の入出金を記録")
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
        date_in = c1.date_input("日付", datetime.date.today())
        type_in = c2.radio("収支", ["支出", "収入"], horizontal=True)
        
        # 収支によってカテゴリ選択肢を変える工夫
        if type_in == "支出":
            cat_list = ["食費", "日用品", "交通費", "交際費", "趣味", "家賃", "投資入金"]
        else:
            cat_list = ["給与", "お小遣い", "配当金", "その他"]
        category_in = c3.selectbox("カテゴリ", cat_list)
        
        amount_in = c4.number_input("金額 (円)", min_value=0, step=100)
        memo_in = c5.text_input("メモ")
        
        if st.button("記録する", type="primary"):
            add_transaction(date_in, type_in, category_in, amount_in, memo_in)
            st.success("記録しました！")
            st.rerun()

    st.divider()

    # データ分析と表示
    df_trans = fetch_transactions()
    
    if not df_trans.empty:
        # データ型変換
        df_trans["date"] = pd.to_datetime(df_trans["date"])
        
        # 今月のデータだけ抽出するフィルター
        current_month = datetime.date.today().strftime("%Y-%m")
        st.caption(f"全データ表示中（データ数: {len(df_trans)}件）")

        # 集計：収入と支出の合計
        income = df_trans[df_trans['type'] == '収入']['amount'].sum()
        expense = df_trans[df_trans['type'] == '支出']['amount'].sum()
        balance = income - expense

        # 3つの数字を並べて表示
        m1, m2, m3 = st.columns(3)
        m1.metric("総収入", f"¥{income:,.0f}", border=True)
        m2.metric("総支出", f"¥{expense:,.0f}", border=True)
        m3.metric("収支バランス", f"¥{balance:,.0f}", 
                  delta_color="normal" if balance >= 0 else "inverse")

        # グラフエリア
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("支出の内訳")
            # 支出データのみフィルタリング
            df_expense = df_trans[df_trans['type'] == '支出']
            if not df_expense.empty:
                fig_exp = px.pie(df_expense, values='amount', names='category', hole=0.4)
                st.plotly_chart(fig_exp, use_container_width=True)
            else:
                st.write("支出データがありません")

        with g2:
            st.subheader("日別の推移")
            # 日付ごとの集計
            daily_sum = df_trans.groupby(['date', 'type'])['amount'].sum().reset_index()
            fig_bar = px.bar(daily_sum, x='date', y='amount', color='type', barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)

        # 履歴リスト
        st.subheader("履歴一覧")
        st.dataframe(df_trans[['date', 'type', 'category', 'amount', 'memo']], 
                     use_container_width=True, hide_index=True)
        
        # 削除
        if st.button("最新の1件を削除"):
            # ID順で一番新しいものを削除する簡易実装
            latest_id = df_trans.iloc[0]['id']
            delete_transaction(latest_id)
            st.rerun()

    else:
        st.info("まだ記録がありません。上のフォームから入力してください。")
