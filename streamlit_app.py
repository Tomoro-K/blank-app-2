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

# 初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# --- 2. 関数群 ---
def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except:
        return None

def analyze_content(text_input, image_input=None):
    # ★修正：最もエラーが出にくい "gemini-1.5-flash" を指定
    target_model = 'gemini-1.5-flash'
    
    base_prompt = """
    あなたは大学の優秀なチューターです。講義資料をもとに、学習用「要約」と「4択クイズ」を作成してください。
    【重要】必ず以下のJSONフォーマットのみを出力してください。Markdown記法は不要です。
    {
        "summary": "要約文",
        "quiz": [
            {"question": "問題", "options": ["A","B","C","D"], "answer_index": 0, "explanation": "解説"}
        ]
    }
    """
    try:
        model = genai.GenerativeModel(target_model)
        
        content = [base_prompt]
        if image_input:
            content.append("以下の講義ノート画像を解析してください：")
            content.append(image_input)
        if text_input:
            content.append(f"補足テキスト: {text_input}")

        response = model.generate_content(content)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    
    except Exception as e:
        # エラー発生時、使えるモデル一覧を表示するデバッグ機能
        error_msg = f"エラー: {e}\n\n"
        error_msg += "▼ あなたのAPIキーで利用可能なモデル一覧:\n"
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    error_msg += f"- {m.name}\n"
        except:
            error_msg += "モデル一覧の取得にも失敗しました。"
            
        return {"error": error_msg}

# --- 3. データベース保存 ---
def save_smart_note(subject, topic, json_data):
    data = {"subject": subject, "topic": topic, "content_json": json_data}
    supabase.table("smart_notes").insert(data).execute()

def fetch_smart_notes():
    return supabase.table("smart_notes").select("*").order("created_at", desc=True).execute().data

def delete_smart_note(note_id):
    supabase.table("smart_notes").delete().eq("id", note_id).execute()

# --- 4. アプリ画面 ---
st.title("🎓 Smart Lecture Mate")
st.caption("Powered by Gemini 1.5 Flash")

tab1, tab2 = st.tabs(["📝 作成", "📚 復習"])

with tab1:
    st.header("資料からノート作成")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        subject_in = c1.text_input("科目名")
        topic_in = c2.text_input("テーマ")
        
        input_type = st.radio("入力形式", ["テキスト", "画像", "PDF"], horizontal=True)
        user_text, user_image = "", None
        
        if input_type == "テキスト":
            user_text = st.text_area("メモ入力")
        elif input_type == "画像":
            img = st.file_uploader("画像", type=["jpg","png"])
            if img: user_image = Image.open(img)
        elif input_type == "PDF":
            pdf = st.file_uploader("PDF", type=["pdf"])
            if pdf: user_text = extract_text_from_pdf(pdf)
            if user_text: st.success(f"{len(user_text)}文字 読み込み成功")

        if st.button("🚀 分析開始", type="primary"):
            if subject_in:
                with st.spinner("Gemini 1.5 Flashが分析中..."):
                    res = analyze_content(user_text, user_image)
                    if "error" in res:
                        # エラー詳細を表示
                        st.error("AI分析に失敗しました")
                        with st.expander("エラー詳細と利用可能なモデル"):
                            st.text(res['error'])
                    else:
                        st.session_state['res'] = res
                        st.session_state['meta'] = {"sub": subject_in, "top": topic_in}
                        st.success("完了！")

    if 'res' in st.session_state:
        data = st.session_state['res']
        st.info(data.get("summary"))
        if st.button("💾 保存"):
            save_smart_note(st.session_state['meta']['sub'], st.session_state['meta']['top'], data)
            st.toast("保存しました")
            del st.session_state['res']
            st.rerun()

with tab2:
    st.header("復習モード")
    notes = fetch_smart_notes()
    if notes:
        sel = st.selectbox("ノート選択", [f"{n['subject']}-{n['topic']}" for n in notes])
        target = next(n for n in notes if f"{n['subject']}-{n['topic']}" == sel)
        content = target['content_json']
        
        st.markdown(content.get("summary"))
        for i, q in enumerate(content.get("quiz", [])):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            ch = st.radio("選択肢", q['options'], key=f"q{target['id']}{i}", index=None)
            if st.button(f"答え合わせ {i+1}", key=f"b{target['id']}{i}"):
                if ch == q['options'][q['answer_index']]: st.success("正解！")
                else: st.error("不正解")
                st.info(q['explanation'])
        
        if st.button("削除"):
            delete_smart_note(target['id'])
            st.rerun()
