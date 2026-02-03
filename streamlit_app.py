import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from supabase import create_client, Client

# --- 1. 設定とSupabase接続 ---
st.set_page_config(page_title="My Asset Dashboard", layout="wide")

# StreamlitのSecretsからURLとKeyを読み込む
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. 外部API関数（為替レート取得） ---
@st.cache_data(ttl=3600) # 1時間キャッシュしてAPI負荷を減らす
def get_usd_jpy_rate():
    try:
        # 一般的な無料APIを使用
        api_url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(api_url)
        data = response.json()
        return data["rates"]["JPY"]
    except:
        return 150.0 # エラー時は仮のレート

# --- 3. データ取得・保存関数 ---
def fetch_data():
    response = supabase.table("assets").select("*").execute()
    return pd.DataFrame(response.data)

def add_asset(name, category, amount, currency):
    data = {
        "name": name,
        "category": category,
        "amount": amount,
        "currency": currency
    }
    supabase.table("assets").insert(data).execute()

def delete_asset(asset_id):
    supabase.table("assets").delete().eq("id", asset_id).execute()

# --- 4. アプリケーション本体 ---
st.title("💰 My Asset Dashboard")
st.markdown("すべての資産を一元管理・可視化するアプリ")

# サイドバー：資産の追加
with st.sidebar:
    st.header("資産の追加")
    with st.form("add_form", clear_on_submit=True):
        name_input = st.text_input("資産名", placeholder="例：三菱UFJ銀行, S&P500")
        category_input = st.selectbox("カテゴリ", ["預金・現金", "株式・投資信託", "ポイント", "その他"])
        amount_input = st.number_input("金額", min_value=0.0, step=100.0)
        currency_input = st.radio("通貨", ["JPY", "USD"])
        
        submitted = st.form_submit_button("追加する")
        if submitted:
            add_asset(name_input, category_input, amount_input, currency_input)
            st.success(f"{name_input} を追加しました！")
            st.rerun() # 画面更新

# メイン画面処理
df = fetch_data()

if not df.empty:
    # 現在のレート取得
    rate = get_usd_jpy_rate()
    st.caption(f"現在の為替レート: 1 USD = {rate} JPY")

    # --- データ加工（Data Science的な部分） ---
    # 日本円換算カラムを作成
    df['amount_jpy'] = df.apply(
        lambda x: x['amount'] if x['currency'] == 'JPY' else x['amount'] * rate, 
        axis=1
    )

    # --- 総資産表示 ---
    total_assets = df['amount_jpy'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="総資産額 (JPY)", value=f"¥{total_assets:,.0f}")
    with col2:
        usd_total = df[df['currency']=='USD']['amount_jpy'].sum()
        st.metric(label="うちドル建て資産 (円換算)", value=f"¥{usd_total:,.0f}")
    with col3:
        jpy_total = df[df['currency']=='JPY']['amount_jpy'].sum()
        st.metric(label="うち円建て資産", value=f"¥{jpy_total:,.0f}")

    st.divider()

    # --- グラフ描画 (Plotly) ---
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("ポートフォリオ割合")
        # カテゴリごとの集計
        category_sum = df.groupby('category')['amount_jpy'].sum().reset_index()
        fig_pie = px.pie(category_sum, values='amount_jpy', names='category', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("資産内訳")
        fig_bar = px.bar(df, x='name', y='amount_jpy', color='category', text_auto='.2s')
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- データ一覧と削除 ---
    st.subheader("登録資産リスト")
    
    # 表示用データフレーム（見やすく整形）
    display_df = df[['id', 'name', 'category', 'amount', 'currency', 'amount_jpy']].copy()
    display_df['amount_jpy'] = display_df['amount_jpy'].apply(lambda x: f"¥{x:,.0f}")
    
    st.dataframe(display_df, hide_index=True, use_container_width=True)

    # 削除機能
    with st.expander("資産データを削除する"):
        del_id = st.number_input("削除するIDを入力", min_value=0, step=1)
        if st.button("削除実行"):
            delete_asset(del_id)
            st.success(f"ID: {del_id} を削除しました")
            st.rerun()

else:
    st.info("👈 サイドバーから資産を追加してください")
