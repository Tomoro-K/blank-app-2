import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json
import time
from PIL import Image
import PyPDF2

# --- 1. 設定 ---
st.set_page_config(page_title="Smart Lecture Mate", layout="wide")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("Secrets (APIキーなど) が設定されていません。")
    st.stop()

# SupabaseとGeminiの初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# --- 2. ファイル読み込み関数 ---
def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return None

# --- 3. Gemini 1.5 Pro AI関数 ---
def analyze_content(text_input, image_input=None):
    # 最新モデルを指定
    # gemini-1.5-pro: 最新かつ高性能。画像・PDF・長文すべてに対応。
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # プロンプト（命令文）
    base_prompt = """
    あなたは大学の優秀なチューターです。
    提供された講義資料（テキストまたは画像）の内容を深く理解し、学習用の「要点まとめ」と「4択クイズ」を作成してください。
    
    【重要】出力は必ず以下のJSON形式のみにしてください。Markdownの ```json 等の囲みは不要です。
    
    {
        "summary": "ここに要約文を記述（Markdown記法OK）",
        "quiz": [
            {
                "question": "クイズの問題文",
                "options": ["選択肢A", "選択肢B", "選択肢C", "選択肢D"],
                "answer_index": 0,
                "explanation": "正解の解説文"
            }
        ]
    }
    """

    try:
        # AIに渡すデータを作成
        content = [base_prompt]
        
        if image_input:
            content.append("以下の講義ノート画像を参照してください：")
            content.append(image_input)
        
        if text_input:
            content.append(f"講義の補足テキスト/PDF内容:\n{text_input}")

        # AIにリクエスト送信
        response = model.generate_content(content)
        
        # 結果の整形（JSONとして読み取れるようにクリーニング）
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)

    except Exception as e:
        return {"error": f"AI生成エラー: {e}"}

# --- 4. データベース操作関数 ---
def save_smart_note(subject, topic, json_data):
    data = {"subject": subject, "topic": topic, "content_json": json_data}
    supabase.table("smart_notes").insert(data).execute()

def fetch_smart_notes():
    # 新しい順に取得
    return supabase.table("smart_notes").select("*").order("created_at", desc=True).execute().data

def delete_smart_note(note_id):
    supabase.table("smart_notes").delete().eq("id", note_id).execute()

# --- 5. アプリケーション画面 ---
st.title("🎓 Smart Lecture Mate (Latest)")
st.caption("Powered by Gemini 1.5 Pro - 画像・PDF対応の最新AIモデル搭載")

tab1, tab2 = st.tabs(["📝 ノート作成", "📚 復習モード"])

# === タブ1：作成モード ===
with tab1:
    st.header("資料から学習ノートを生成")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        subject_in = c1.text_input("科目名", placeholder="例：データサイエンス")
        topic_in = c2.text_input("テーマ", placeholder="例：第5回 統計分析")
        
        # 入力形式の選択
        input_type = st.radio("入力データ", ["テキスト入力", "画像 (ノート写真)", "PDF (講義資料)"], horizontal=True)
        
        user_text = ""
        user_image = None
        ready = False

        if input_type == "テキスト入力":
            user_text = st.text_area("講義メモを入力", height=150)
            if user_text: ready = True
            
        elif input_type == "画像 (ノート写真)":
            img_file = st.file_uploader("画像をアップロード", type=["jpg", "png", "jpeg"])
            if img_file:
                user_image = Image.open(img_file)
                st.image(user_image, caption="アップロード画像", width=300)
                ready = True
                
        elif input_type == "PDF (講義資料)":
            pdf_file = st.file_uploader("PDFをアップロード", type=["pdf"])
            if pdf_file:
                with st.spinner("PDFを読み込み中..."):
                    extracted = extract_text_from_pdf(pdf_file)
                    if extracted:
                        st.success(f"読み取り成功: {len(extracted)}文字")
                        user_text = extracted
                        ready = True
                    else:
                        st.error("テキストを読み取れませんでした（画像PDFの可能性があります）")

        st.markdown("---")
        
        if st.button("🚀 AI分析スタート (1.5 Pro)", type="primary", disabled=not ready):
            if not subject_in:
                st.warning("科目名を入力してください")
            else:
                with st.spinner("Gemini 1.5 Pro が資料を深く分析しています..."):
                    # AI分析実行
                    result = analyze_content(user_text, user_image)
                    
                    if "error" in result:
                        st.error(result['error'])
                    else:
                        # 結果を一時保存
                        st.session_state['gen_result'] = result
                        st.session_state['gen_meta'] = {"sub": subject_in, "top": topic_in}
                        st.success("生成完了！")

    # 生成結果のプレビューと保存
    if 'gen_result' in st.session_state:
        data = st.session_state['gen_result']
        meta = st.session_state['gen_meta']
        
        st.divider()
        st.subheader(f"📄 分析結果: {meta['sub']}")
        st.info(data.get("summary", "要約なし"))
        
        # 保存ボタン
        if st.button("💾 データベースに保存"):
            save_smart_note(meta['sub'], meta['top'], data)
            st.toast("保存しました！復習タブで確認できます", icon="✅")
            time.sleep(1.5)
            del st.session_state['gen_result'] # クリア
            st.rerun()

# === タブ2：復習モード ===
with tab2:
    st.header("復習・クイズ挑戦")
    
    notes = fetch_smart_notes()
    if notes:
        # ノート選択メニュー
        options = {f"{n['subject']} - {n['topic']} ({n['created_at'][:10]})": n for n in notes}
        selected_label = st.selectbox("ノートを選択", list(options.keys()))
        target_note = options[selected_label]
        content = target_note['content_json']
        
        # 要約の表示
        with st.expander("📖 要点まとめを見る", expanded=True):
            st.markdown(content.get("summary", "要約データなし"))
            
        st.divider()
        st.subheader("🔥 実践クイズ")
        
        # クイズ表示
        if "quiz" in content:
            for i, q in enumerate(content["quiz"]):
                st.markdown(f"**Q{i+1}. {q['question']}**")
                
                # ユニークなキーを使ってラジオボタンを作成
                user_ans = st.radio(
                    "選択肢", 
                    q['options'], 
                    key=f"quiz_{target_note['id']}_{i}", 
                    index=None
                )
                
                if st.button(f"答え合わせ (Q{i+1})", key=f"btn_{target_note['id']}_{i}"):
                    correct = q['options'][q['answer_index']]
                    if user_ans == correct:
                        st.success("🙆‍♀️ 正解！")
                    else:
                        st.error(f"🙅‍♂️ 不正解... 正解は「{correct}」")
                    st.info(f"解説: {q['explanation']}")
                st.divider()
        
        # 削除ボタン
        if st.button("🗑️ このノートを削除"):
            delete_smart_note(target_note['id'])
            st.rerun()
            
    else:
        st.info("まだノートがありません。「ノート作成」タブから追加してください。")
