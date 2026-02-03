import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import json
import time
from PIL import Image
import PyPDF2
import io

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

# --- 2. ファイル処理関数 ---
def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return None

# --- 3. Gemini AI関数 (マルチモーダル対応) ---
def analyze_content(text_input, image_input=None):
    # プロンプトの準備
    base_prompt = """
    あなたは大学の優秀なチューターです。
    提供された講義資料（テキストまたは画像）をもとに、学習用の「要約」と「4択クイズ」を作成してください。
    
    【重要】必ず以下のJSONフォーマット（schema）のみを出力してください。Markdownのコードブロックは不要です。
    
    {
        "summary": "ここに要約文（マークダウン記法使用可）を記述",
        "quiz": [
            {
                "question": "問題文",
                "options": ["選択肢A", "選択肢B", "選択肢C", "選択肢D"],
                "answer_index": 0,
                "explanation": "解説文"
            }
        ]
    }
    """

    try:
        # 画像対応モデルに変更 (gemini-pro)
        model = genai.GenerativeModel('gemini-pro')
        
        content = [base_prompt]
        
        # 画像がある場合
        if image_input:
            content.append("以下の講義ノート画像を解析してください：")
            content.append(image_input)
            if text_input:
                content.append(f"補足メモ: {text_input}")
        # テキストのみの場合
        else:
            content.append(f"--- 講義メモ ---\n{text_input}")

        # AIに送信
        response = model.generate_content(content)
        
        # JSONクリーニング
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        return data
    except Exception as e:
        return {"error": f"AI生成エラー: {e}"}

# --- 4. データベース操作 ---
def save_smart_note(subject, topic, json_data):
    data = {"subject": subject, "topic": topic, "content_json": json_data}
    supabase.table("smart_notes").insert(data).execute()

def fetch_smart_notes():
    return supabase.table("smart_notes").select("*").order("created_at", desc=True).execute().data

def delete_smart_note(note_id):
    supabase.table("smart_notes").delete().eq("id", note_id).execute()

# --- 5. アプリ本体 ---
st.title("🎓 Smart Lecture Mate (Pro)")
st.caption("講義ノート画像・PDF・テキストからクイズを自動生成")

tab1, tab2 = st.tabs(["📝 資料アップロード & 生成", "📚 復習モード"])

# === タブ1：生成モード ===
with tab1:
    st.header("資料からノートを作成")
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        subject_in = c1.text_input("科目名", placeholder="データサイエンス概論")
        topic_in = c2.text_input("テーマ", placeholder="第4回 統計基礎")
        
        # 入力タイプの切り替え
        input_type = st.radio("入力データを選択", ["テキスト直接入力", "画像アップロード (ノート写真)", "PDFアップロード (資料)"], horizontal=True)
        
        user_text = ""
        user_image = None
        ready_to_submit = False

        if input_type == "テキスト直接入力":
            user_text = st.text_area("講義メモを入力", height=150)
            if user_text: ready_to_submit = True
            
        elif input_type == "画像アップロード (ノート写真)":
            uploaded_img = st.file_uploader("ノートの画像をアップロード", type=["jpg", "png", "jpeg"])
            if uploaded_img:
                user_image = Image.open(uploaded_img)
                st.image(user_image, caption="アップロードされた画像", width=300)
                ready_to_submit = True
                
        elif input_type == "PDFアップロード (資料)":
            uploaded_pdf = st.file_uploader("講義資料PDFをアップロード", type=["pdf"])
            if uploaded_pdf:
                with st.spinner("PDFからテキストを読み取っています..."):
                    extracted_text = extract_text_from_pdf(uploaded_pdf)
                    if extracted_text:
                        st.success(f"読み取り成功: {len(extracted_text)}文字")
                        with st.expander("読み取った内容を確認"):
                            st.text(extracted_text[:500] + "...")
                        user_text = extracted_text
                        ready_to_submit = True
                    else:
                        st.error("PDFからテキストを読み取れませんでした（画像化されたPDFの可能性があります）")

        st.markdown("---")
        
        if st.button("🚀 AI分析スタート", type="primary", disabled=not ready_to_submit):
            if subject_in:
                with st.spinner("Gemini先生が資料を分析中...（画像の場合は少し時間がかかります）"):
                    # 画像またはテキストを渡して解析
                    result_json = analyze_content(user_text, user_image)
                    
                    if "error" in result_json:
                        st.error(f"失敗しました: {result_json['error']}")
                    else:
                        st.session_state['gen_data'] = result_json
                        st.session_state['gen_meta'] = {"subject": subject_in, "topic": topic_in}
                        st.success("生成完了！")
            else:
                st.warning("科目名を入力してください")

    # 生成結果プレビュー
    if 'gen_data' in st.session_state:
        data = st.session_state['gen_data']
        meta = st.session_state['gen_meta']
        
        st.divider()
        st.subheader(f"📄 分析結果: {meta['subject']}")
        st.info(data.get("summary", "要約なし"))
        
        if st.button("💾 データベースに保存する"):
            save_smart_note(meta['subject'], meta['topic'], data)
            st.toast("保存しました！", icon="✅")
            time.sleep(1)
            del st.session_state['gen_data']
            st.rerun()

# === タブ2：復習モード (変更なし) ===
with tab2:
    st.header("復習・クイズ挑戦")
    notes = fetch_smart_notes()
    if notes:
        opts = {f"{n['subject']} - {n['topic']}": n for n in notes}
        sel = st.selectbox("ノートを選択", list(opts.keys()))
        note = opts[sel]
        content = note['content_json']
        
        with st.expander("要約を見る", expanded=True):
            st.markdown(content.get("summary"))
            
        st.subheader("クイズ")
        if "quiz" in content:
            for i, q in enumerate(content["quiz"]):
                st.markdown(f"**Q{i+1}. {q['question']}**")
                choice = st.radio("選択肢", q['options'], key=f"q_{note['id']}_{i}", index=None)
                if st.button(f"答え合わせ Q{i+1}", key=f"b_{note['id']}_{i}"):
                    if choice == q['options'][q['answer_index']]:
                        st.success("正解！")
                    else:
                        st.error(f"不正解... 正解は {q['options'][q['answer_index']]}")
                    st.info(q['explanation'])
                st.divider()
        
        if st.button("削除する"):
            delete_smart_note(note['id'])
            st.rerun()
    else:
        st.info("データがありません")
