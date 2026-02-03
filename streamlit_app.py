import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json
import time

# --- 1. 設定 ---
st.set_page_config(page_title="Smart Lecture Mate", layout="wide")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Secrets（APIキーなど）が設定されていません。")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# --- 2. Gemini AI関数 (JSONモード) ---
def analyze_lecture(text):
    # AIにJSON形式での出力を強制する強力なプロンプト
    prompt = f"""
    あなたは大学の優秀なチューターです。
    以下の講義メモをもとに、学習用の「要約」と「4択クイズ」を作成してください。
    
    【重要】必ず以下のJSONフォーマット（schema）のみを出力してください。Markdownのコードブロック(```json)は不要です。
    
    {{
        "summary": "ここに要約文（マークダウン記法使用可）を記述",
        "quiz": [
            {{
                "question": "問題文1",
                "options": ["選択肢A", "選択肢B", "選択肢C", "選択肢D"],
                "answer_index": 0,
                "explanation": "解説文"
            }},
            {{
                "question": "問題文2",
                "options": ["選択肢A", "選択肢B", "選択肢C", "選択肢D"],
                "answer_index": 2,
                "explanation": "解説文"
            }}
        ]
    }}

    --- 講義メモ ---
    {text}
    """
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        # JSON文字列をPythonの辞書型に変換
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        return data
    except Exception as e:
        return {"error": f"AIの生成エラー: {e}"}

# --- 3. データベース操作 ---
def save_smart_note(subject, topic, json_data):
    data = {
        "subject": subject,
        "topic": topic,
        "content_json": json_data # JSONをそのまま保存
    }
    supabase.table("smart_notes").insert(data).execute()

def fetch_smart_notes():
    return supabase.table("smart_notes").select("*").order("created_at", desc=True).execute().data

def delete_smart_note(note_id):
    supabase.table("smart_notes").delete().eq("id", note_id).execute()

# --- 4. アプリ本体 ---
st.title("🎓 Smart Lecture Mate")
st.caption("AIが「要約」と「クイズ」を自動生成する学習支援アプリ")

tab1, tab2 = st.tabs(["📝 ノート登録 & 生成", "📚 復習モード (クイズ)"])

# === タブ1：生成モード ===
with tab1:
    st.header("新しいノートを作成")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        subject_in = col1.text_input("科目名", placeholder="データサイエンス概論")
        topic_in = col2.text_input("テーマ", placeholder="第3回 機械学習の基礎")
        text_in = st.text_area("講義メモ・資料テキスト", height=150, placeholder="ここに講義の内容を貼り付けてください...")
        
        if st.button("🚀 AI分析スタート", type="primary"):
            if text_in and subject_in:
                with st.spinner("Gemini先生が分析中...（約10秒）"):
                    result_json = analyze_lecture(text_in)
                    
                    if "error" in result_json:
                        st.error("生成に失敗しました。もう一度試してください。")
                    else:
                        st.session_state['generated_data'] = result_json
                        st.session_state['meta_data'] = {"subject": subject_in, "topic": topic_in}
                        st.success("生成完了！ 下で確認して保存してください。")
            else:
                st.warning("科目名とテキストを入力してください")

    # 生成結果のプレビュー
    if 'generated_data' in st.session_state:
        data = st.session_state['generated_data']
        meta = st.session_state['meta_data']
        
        st.divider()
        st.subheader(f"📄 {meta['subject']} - {meta['topic']}")
        
        # 要約表示
        st.info(data.get("summary", "要約なし"))
        
        # クイズプレビュー
        st.markdown("##### 🎲 生成されたクイズ")
        for i, q in enumerate(data.get("quiz", [])):
            with st.expander(f"Q{i+1}: {q['question']}"):
                st.write(f"正解: {q['options'][q['answer_index']]}")
                st.caption(f"解説: {q['explanation']}")
        
        # 保存ボタン
        if st.button("💾 データベースに保存する"):
            save_smart_note(meta['subject'], meta['topic'], data)
            st.toast("保存しました！復習タブで確認できます", icon="✅")
            time.sleep(2)
            del st.session_state['generated_data'] # クリア
            st.rerun()

# === タブ2：復習モード (ここが進化ポイント！) ===
with tab2:
    st.header("復習・クイズ挑戦")
    
    notes = fetch_smart_notes()
    if notes:
        # ノート選択
        note_options = {f"{n['subject']} : {n['topic']} ({n['created_at'][:10]})": n for n in notes}
        selected_label = st.selectbox("復習するノートを選択", list(note_options.keys()))
        selected_note = note_options[selected_label]
        
        content = selected_note['content_json']
        
        st.divider()
        
        # 要約を見る
        with st.expander("📖 要約を確認する", expanded=True):
            st.markdown(content.get("summary", "No summary"))
        
        # インタラクティブ・クイズ
        st.subheader("🔥 実践クイズ")
        
        if "quiz" in content:
            for i, q in enumerate(content["quiz"]):
                st.markdown(f"**Q{i+1}. {q['question']}**")
                
                # ユーザーの回答選択
                # keyを一意にしないとエラーになるため工夫
                user_choice = st.radio(
                    "選択肢:", 
                    q['options'], 
                    key=f"q_{selected_note['id']}_{i}",
                    index=None # 初期状態は未選択
                )
                
                # 答え合わせボタン（選択直後に判定が出ると使いにくいのでボタン式に）
                if st.button(f"答え合わせ (Q{i+1})", key=f"btn_{selected_note['id']}_{i}"):
                    if user_choice:
                        correct_option = q['options'][q['answer_index']]
                        if user_choice == correct_option:
                            st.success("🙆‍♀️ 正解！")
                        else:
                            st.error(f"🙅‍♂️ 残念... 正解は「{correct_option}」です")
                        st.info(f"💡 解説: {q['explanation']}")
                    else:
                        st.warning("選択肢を選んでください")
                st.divider()
        
        # 削除ボタン
        with st.popover("🗑️ このノートを削除"):
            st.write("本当に削除しますか？")
            if st.button("削除実行"):
                delete_smart_note(selected_note['id'])
                st.rerun()

    else:
        st.info("まだノートがありません。「ノート登録」タブで作ってみましょう！")
