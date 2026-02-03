import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from supabase import create_client, Client

# --- 1. 設定とSupabase接続 ---
st.set_page_config(page_title="My Asset Dashboard", layout="wide")

# Secretsから読み込み
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. 外部WebAPI関数（ここがポイント！） ---

# 【API 1】為替レートを取得 (ExchangeRate-API)
@st.cache_data(ttl=3600)
def get_usd_jpy_rate():
    try:
        # ドルベースのレートを取得
        api_url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(api_url)
        data = response.json()
        return data["rates"]["JPY"]
    except:
        return 150.0 # エラー時の予備

# 【API 2】仮想通貨の価格を取得 (CoinGecko API)
@st.cache_data(ttl=600)
def get_crypto_price(coin_id):
    try:
        # coin_idは 'bitcoin', 'ethereum' など
        api_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=jpy"
        response = requests.get(api_url)
        data = response.json()
        return data[coin_id]["jpy"]
    except:
        return 0.0

# --- 3. データベース操作関数 ---
def fetch_data():
    response = supabase.table("assets").select("*").execute()
    return pd.DataFrame(response.data)

def add_asset(name, category, amount, currency, crypto_id=None):
    data = {
        "name": name,
        "category": category,
        "amount": amount,
        "currency": currency,
        # 仮想通貨の場合はIDをメモ欄(note)などを活用して保存も可能だが、
        # 今回はシンプルにするため金額は手入力+自動計算の構成にします
    }
    supabase.table("assets").insert(data).execute()

def delete_asset(asset_id):
    supabase.table("assets").delete().eq("id", asset_id).execute()

# --- 4. アプリケーション本体 ---
st.title("💰 My Asset Dashboard")
st.caption("為替API & 仮想通貨API 連携中")

# APIからデータを取得
usd_rate = get_usd_jpy_rate()
btc_price = get_crypto_price("bitcoin")
eth_price = get_crypto_price("ethereum")

# サイドバー：資産追加
with st.sidebar:
    st.header("📊 市場データ (API取得)")
    st.markdown(f"**USD/JPY:** ¥{usd_rate}")
    st.markdown(f"**Bitcoin:** ¥{btc_price:,.0f}")
    st.markdown(f"**Ethereum:** ¥{eth_price:,.0f}")
    st.divider()
    
    st.header("資産の追加")
    with st.form("add_form", clear_on_submit=True):
        name_input = st.text_input("資産名", placeholder="例：S&P500, ビットコイン")
        category_input = st.selectbox("カテゴリ", ["預金・現金", "株式・投資信託", "仮想通貨", "その他"])
        
        # 数量/金額の入力
        amount_label = "金額（または保有コイン数）"
        amount_input = st.number_input(amount_label, min_value=0.0, step=0.1)
        
        # 通貨タイプの選択（仮想通貨も追加）
        currency_input = st.selectbox("通貨単位", ["JPY (円)", "USD (ドル)", "BTC (ビットコイン)", "ETH (イーサ)"])
        
        submitted = st.form_submit_button("追加する")
        if submitted:
            # DBには通貨コード(JPY, USD, BTC, ETH)として保存
            currency_code = currency_input.split(" ")[0] 
            add_asset(name_input, category_input, amount_input, currency_code)
            st.success("追加しました！")
            st.rerun()

# メイン処理
df = fetch_data()

if not df.empty:
    # --- データ加工：すべての資産を「日本円」に換算する ---
    def convert_to_jpy(row):
        amt = row['amount']
        curr = row['currency']
        
        if curr == 'JPY':
            return amt
        elif curr == 'USD':
            return amt * usd_rate
        elif curr == 'BTC':
            return amt * btc_price
        elif curr == 'ETH':
            return amt * eth_price
        else:
            return amt

    df['amount_jpy'] = df.apply(convert_to_jpy, axis=1)

    # --- 総資産表示 ---
    total_assets = df['amount_jpy'].sum()
    
    # 3カラムで表示
    col1, col2, col3 = st.columns(3)
    col1.metric("総資産額 (円換算)", f"¥{total_assets:,.0f}")
    
    # カテゴリ別の割合を計算
    risk_assets = df[df['category'].isin(['株式・投資信託', '仮想通貨'])]['amount_jpy'].sum()
    safe_assets = total_assets - risk_assets
    col2.metric("リスク資産", f"¥{risk_assets:,.0f}")
    col3.metric("安全資産", f"¥{safe_assets:,.0f}")

    st.divider()

    # --- グラフ (Plotly) ---
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("ポートフォリオ内訳")
        fig_pie = px.pie(df, values='amount_jpy', names='category', 
                         title='カテゴリ別割合', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("資産構成")
        fig_bar = px.bar(df, x='category', y='amount_jpy', color='name', 
                         title='資産ごとの積み上げ', text_auto='.2s')
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- リスト表示 ---
    st.subheader("登録資産リスト")
    st.dataframe(df[['name', 'category', 'amount', 'currency', 'amount_jpy']], 
                 use_container_width=True)
    
    with st.expander("データを削除"):
        del_id = st.number_input("削除するID", min_value=0)
        if st.button("削除実行"):
            delete_asset(del_id)
            st.rerun()

else:
    st.info("👈 サイドバーから資産を追加してください")
