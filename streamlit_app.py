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

# (B) 家計簿関連
def fetch_transactions():
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

# タブ設定
tab1, tab2 = st.tabs(["🏦 資産管理 (Stock)", "📒 家計簿 (Flow)"])

# ==========================================
# タブ1：資産管理機能
# ==========================================
with tab1:
    st.header("資産ポートフォリオ")
    
    # 資産の手動追加（家計簿を通さずに記録したい場合用）
    with st.expander("➕ 資産を手動で追加する"):
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
        # 円換算
        def convert(row):
            if row['currency'] == 'USD': return row['amount'] * usd_rate
            if row['currency'] == 'BTC': return row['amount'] * btc_price
            return row['amount']
        
        df_assets['amount_jpy'] = df_assets.apply(convert, axis=1)
        
        # 表示
        total = df_assets['amount_jpy'].sum()
        st.metric("総資産額", f"¥{total:,.0f}", delta=f"1USD = {usd_rate}円")
        
        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(df_assets, values='amount_jpy', names='category', title="資産比率")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.dataframe(df_assets[['name', 'category', 'amount', 'currency', 'amount_jpy']], use_container_width=True)
            
            # 削除機能
            del_id = st.number_input("削除する資産ID", 0)
            if st.button("資産を削除"):
                delete_asset(del_id)
                st.rerun()
    else:
        st.info("資産データがありません。")

# ==========================================
# タブ2：家計簿機能（ここが連携の肝！）
# ==========================================
with tab2:
    st.header("家計簿・収支ログ")

    with st.container():
        st.markdown("#### 📝 入出金の記録")
        
        # 入力フォーム
        c1, c2, c3 = st.columns(3)
        date_in = c1.date_input("日付", datetime.date.today())
        type_in = c2.radio("収支", ["支出", "収入"], horizontal=True)
        
        # カテゴリ選択
        if type_in == "支出":
            cat_list = ["食費", "日用品", "投資・資産購入", "交通費", "交際費", "その他"]
        else:
            cat_list = ["給与", "お小遣い", "配当金", "その他"]
        category_in = c3.selectbox("カテゴリ", cat_list)
        
        c4, c5 = st.columns(2)
        amount_in = c4.number_input("金額 (円)", min_value=0, step=1000)
        memo_in = c5.text_input("メモ (資産名など)")

        # ★★★ 新機能：資産連携チェックボックス ★★★
        is_asset_purchase = st.checkbox("この支出を「資産(Stock)」にも追加する（株や外貨の購入など）")

        # 資産に追加する場合の追加オプション
        if is_asset_purchase:
            st.info("👇 資産管理テーブルに登録する情報を入力してください")
            ac1, ac2 = st.columns(2)
            # 家計簿は円で記録するが、資産としてはドルで持ちたい場合に対応
            asset_currency = ac1.selectbox("資産としての通貨単位", ["JPY", "USD", "BTC", "ETH"])
            asset_amount = ac2.number_input("資産としての数量 (ドル額や株数)", min_value=0.0, value=float(amount_in))
            st.caption(f"例：{amount_in}円払って、{asset_amount}ドル分を購入した")

        # 送信ボタン
        if st.button("記録する", type="primary"):
            # 1. まず家計簿に記録
            add_transaction(date_in, type_in, category_in, amount_in, memo_in)
            
            # 2. チェックが入っていたら資産にも記録
            if is_asset_purchase:
                # 資産名はメモ欄の内容を使う（空ならカテゴリ名）
                asset_name = memo_in if memo_in else category_in
                # カテゴリは自動で「投資資産」などにしてもいいが、ここでは元のカテゴリを使用
                add_asset(asset_name, category_in, asset_amount, asset_currency)
                st.success(f"家計簿に記録し、資産「{asset_name}」を追加しました！")
            else:
                st.success("家計簿に記録しました！")
            
            st.rerun()

    st.divider()

    # 以下、家計簿の表示ロジック（変更なし）
    df_trans = fetch_transactions()
    if not df_trans.empty:
        df_trans["date"] = pd.to_datetime(df_trans["date"])
        
        income = df_trans[df_trans['type'] == '収入']['amount'].sum()
        expense = df_trans[df_trans['type'] == '支出']['amount'].sum()
        balance = income - expense

        m1, m2, m3 = st.columns(3)
        m1.metric("総収入", f"¥{income:,.0f}")
        m2.metric("総支出", f"¥{expense:,.0f}")
        m3.metric("収支", f"¥{balance:,.0f}")

        st.dataframe(df_trans[['date', 'type', 'category', 'amount', 'memo']], use_container_width=True, hide_index=True)
