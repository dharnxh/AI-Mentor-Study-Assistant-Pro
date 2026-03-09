import os
import io
import json
import pickle
import sqlite3
import time
from io import BytesIO
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import streamlit as st
import pdfplumber
from gtts import gTTS
import httpx, certifi
from dotenv import load_dotenv
import numpy as np

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except:
    PLOTLY_AVAILABLE = False

try:
    import pypdfium2 as pdfium
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

st.set_page_config(page_title="AI Generated Study Assistant", layout="centered")
load_dotenv()
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

try:
    from openai import OpenAI
    _openai_key = os.environ.get("OPENAI_API_KEY") or (st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None)
    client = OpenAI(api_key=_openai_key) if _openai_key else None
except Exception:
    client = None

st.markdown("""
<style>
.status-badge {
    display: inline-block;
    padding: 8px 12px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.9rem;
}
.status-badge.done {
    background-color: #10b981;
    color: white;
}
.status-badge.pending {
    background-color: #fbbf24;
    color: #1a1a1a;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div style="text-align:center; padding: 32px 0;"><h1 style="margin:0;"><span style="color:#6366f1;">AI Mentor Study Assistant</span></h1><p>Upload notes • Get summaries • Create quizzes • Find resources</p></div>""", unsafe_allow_html=True)

st.markdown("---")

def fetch_videos_for_topics(topics):
    results = {}
    for t in topics:
        q = quote_plus(f"{t} tutorial")
        url = f"https://www.youtube.com/results?search_query={q}"
        results[t] = [{"title": f"📺 {t}", "url": url, "note": "YouTube search"}]
    return results

def build_sim_search_links(topic: str):
    """Generate interactive learning resource links for a topic"""
    items = []
    q = quote_plus(topic)
    
    # PhET Interactive Simulations
    items.append({
        "title": "🔬 PhET Simulations",
        "url": f"https://phet.colorado.edu/en/simulations?subjects=physics,chemistry,math,biology&type=html,prototype",
        "note": "Physics, Chemistry, Math, Biology simulations"
    })
    
    # Khan Academy
    items.append({
        "title": "🎓 Khan Academy",
        "url": f"https://www.khanacademy.org/search?page_search_query={q}",
        "note": "Video lessons & practice exercises"
    })
    
    # Desmos (Math)
    items.append({
        "title": "📊 Desmos Graphing",
        "url": f"https://www.desmos.com/calculator",
        "note": "Interactive graphing & math tools"
    })
    
    # GeoGebra (Math & Science)
    items.append({
        "title": "🧮 GeoGebra",
        "url": f"https://www.geogebra.org/search/{q}",
        "note": "Interactive math & science applets"
    })
    
    # Wolfram Alpha
    items.append({
        "title": "⚙️ Wolfram Alpha",
        "url": f"https://www.wolframalpha.com/input?i={q}",
        "note": "Computational answers & visualizations"
    })
    
    # YouTube Educational
    items.append({
        "title": "🎬 Educational Videos",
        "url": f"https://www.youtube.com/results?search_query={q}+tutorial+explained",
        "note": "YouTube educational content"
    })
    
    return items

def truncate_chars(s: str, max_chars: int = 12000) -> str:
    return s[:max_chars] if s else ""

@st.cache_data(show_spinner=False)
def extract_pdf_text(uploaded_file, use_ocr=False) -> str:
    if not uploaded_file:
        return ""
    raw = uploaded_file.getvalue()
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                if t:
                    text += t + "\n"
    except Exception:
        pass
    return text.strip()

def openai_complete(prompt: str, temperature=0.25, max_tokens=900) -> str:
    if not client:
        st.error("⚠️ OpenAI API key not configured!\n\nPlease set OPENAI_API_KEY in:\n1. Environment variable\n2. .env file\n3. Streamlit secrets.toml")
        return None
    try:
        resp = client.chat.completions.create(
            model=st.session_state.get("model", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return None

def ai_extract_topics(text: str) -> list:
    if not text:
        return []
    prompt = f'Extract 3-5 study topics from this text as JSON list. Return only: ["topic1","topic2"]\n\nText:\n{truncate_chars(text, 4000)}'
    try:
        response = openai_complete(prompt, temperature=0.2, max_tokens=200)
        if not response:
            return []
        topics = json.loads(response.replace("```json", "").replace("```", "").strip())
        return [str(t).strip()[:50] for t in topics if t][:6]
    except Exception as e:
        st.error(f"Topic extraction failed: {e}")
        return []

def ai_summarize(text: str) -> str:
    if not text:
        return ""
    prompt = f"Summarize these notes in 300 words, with key concepts and one example:\n\n{truncate_chars(text, 6000)}"
    return openai_complete(prompt, temperature=0.25, max_tokens=500)

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if "model" not in st.session_state:
        st.session_state.model = "gpt-4o-mini"
    model = st.selectbox("Model:", ["gpt-4o-mini", "gpt-4o"], index=0, label_visibility="collapsed")
    st.session_state.model = model
    st.divider()
    st.caption("v1.0 | Powered by OpenAI")

if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = None

st.markdown("### 📄 Upload PDF")
uploaded = st.file_uploader("Choose PDF", type="pdf", label_visibility="collapsed")

if uploaded:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.session_state.extracted_text:
            st.markdown('<div class="status-badge done">✅ PDF</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-badge pending">⏳ Upload</div>', unsafe_allow_html=True)
    with col2:
        topics = st.session_state.get("topics", [])
        st.markdown(f'<div class="status-badge {"done" if topics else "pending"}">{"✅ Topics" if topics else "⏳ Topics"}</div>', unsafe_allow_html=True)
    with col3:
        summary = st.session_state.get("summary")
        st.markdown(f'<div class="status-badge {"done" if summary else "pending"}">{"✅ Summary" if summary else "⏳ Summary"}</div>', unsafe_allow_html=True)
    with col4:
        quiz = st.session_state.get("quiz")
        st.markdown(f'<div class="status-badge {"done" if quiz else "pending"}">{"✅ Quiz" if quiz else "⏳ Quiz"}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("⚡ Process PDF", use_container_width=True):
        if not client:
            st.error("🔑 **OpenAI API Key Missing!**\n\n### Setup Instructions:\n\n**Option 1: Environment Variable (Recommended)**\n```\nset OPENAI_API_KEY=sk-your-key-here\n```\n\n**Option 2: .env File**\nCreate a `.env` file in the project folder:\n```\nOPENAI_API_KEY=sk-your-key-here\n```\n\n**Option 3: Streamlit Secrets**\nCreate `.streamlit/secrets.toml`:\n```\nOPENAI_API_KEY=\"sk-your-key-here\"\n```\n\n👉 Get your API key from: https://platform.openai.com/api-keys")
        else:
            with st.spinner("📄 Extracting text..."):
                text = extract_pdf_text(uploaded)
                if not text:
                    st.error("❌ No text extracted from PDF. Try another file.")
                else:
                    st.session_state.extracted_text = text
                    st.success("✅ Text extracted successfully")
            
            if st.session_state.extracted_text:
                with st.spinner("🎯 Detecting topics..."):
                    topics = ai_extract_topics(st.session_state.extracted_text)
                    st.session_state.topics = topics
                    if topics:
                        st.success(f"✅ Found {len(topics)} topics: {', '.join(topics)}")
                    else:
                        st.warning("⚠️ Could not detect topics")
                
                with st.spinner("📝 Generating summary..."):
                    summary = ai_summarize(st.session_state.extracted_text) if st.session_state.extracted_text else ""
                    st.session_state.summary = summary
                    if summary:
                        st.success("✅ Summary generated")
                    else:
                        st.warning("⚠️ Could not generate summary")
            
            st.rerun()
    
    st.markdown("---")
    
    tabs = st.tabs(["📝 Summary", "🎥 Videos", "🧪 Labs", "❓ Quiz", "📦 Export"])
    
    with tabs[0]:
        st.subheader("Summary")
        if st.session_state.get("summary"):
            st.markdown(st.session_state["summary"])
            st.download_button("⬇️ Download", data=st.session_state["summary"], file_name="summary.md", mime="text/markdown")
        else:
            st.info("Click **Process PDF** above to generate")
    
    with tabs[1]:
        st.subheader("Video Resources")
        if st.session_state.get("topics"):
            videos = fetch_videos_for_topics(st.session_state["topics"])
            for topic, items in videos.items():
                st.markdown(f"**{topic}**")
                for v in items:
                    st.markdown(f"[{v['title']}]({v['url']})")
        else:
            st.info("Process PDF to detect topics")
    
    with tabs[2]:
        st.subheader("Interactive Resources")
        if st.session_state.get("topics"):
            for topic in st.session_state["topics"]:
                st.markdown(f"**{topic}**")
                for link in build_sim_search_links(topic):
                    st.markdown(f"[{link['title']}]({link['url']})")
        else:
            st.info("Process PDF to detect topics")
    
    with tabs[3]:
        st.subheader("Quiz")
        text = st.session_state.get("extracted_text", "")
        num_q = st.slider("Questions:", 3, 15, 5)
        
        if st.button("Generate Quiz"):
            if not text:
                st.error("No text extracted")
            else:
                prompt = f'''Create {num_q} multiple-choice questions from this text.
Format as JSON array: [{{"question":"Q?","choices":["A","B","C","D"],"answer_index":0,"explanation":"..."}}]
Return ONLY JSON.

Text: {truncate_chars(text, 5000)}'''
                response = openai_complete(prompt, temperature=0.2, max_tokens=1200)
                try:
                    quiz = json.loads(response.replace("```json","").replace("```","").strip())
                    st.session_state.quiz = quiz
                except:
                    st.error("Failed to generate quiz")
        
        if st.session_state.get("quiz"):
            for i, q in enumerate(st.session_state["quiz"], 1):
                st.markdown(f"**Q{i}. {q['question']}**")
                ans = st.radio(f"Q{i}", q["choices"], key=f"q_{i}", label_visibility="collapsed")
                if st.button("Check", key=f"btn_{i}"):
                    correct = q["choices"][q["answer_index"]]
                    if ans == correct:
                        st.success("✅")
                    else:
                        st.error(f"❌ Correct: {correct}")
                    st.info(q.get("explanation", ""))
    
    with tabs[4]:
        st.subheader("Export")
        all_data = {
            "topics": st.session_state.get("topics", []),
            "summary": st.session_state.get("summary", ""),
            "quiz": st.session_state.get("quiz", []),
        }
        st.download_button(
            "📥 Download All",
            data=json.dumps(all_data, indent=2),
            file_name="study_pack.json"
        )
else:
    st.info("👆 Upload a PDF to start")

st.markdown("---")
st.caption("🚀 AI Mentor v1.0 | Powered by OpenAI")
