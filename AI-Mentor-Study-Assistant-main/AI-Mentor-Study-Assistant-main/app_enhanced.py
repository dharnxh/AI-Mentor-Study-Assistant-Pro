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

st.set_page_config(page_title="AI Mentor Study Assistant Pro", layout="wide")
load_dotenv()
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

try:
    from openai import OpenAI
    _openai_key = os.environ.get("OPENAI_API_KEY") or (st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None)
    client = OpenAI(api_key=_openai_key) if _openai_key else None
except Exception:
    client = None

# ============== DATABASE SETUP ==============
DB_FILE = "study_sessions.db"

def init_db():
    """Initialize SQLite database for tracking progress"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_scores
                 (id INTEGER PRIMARY KEY, session_name TEXT, topic TEXT, score REAL, total INTEGER, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS study_sessions
                 (id INTEGER PRIMARY KEY, name TEXT, topics TEXT, summary TEXT, created_at TEXT, updated_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS achievements
                 (id INTEGER PRIMARY KEY, session_id INTEGER, badge_name TEXT, achieved_at TEXT)''')
    conn.commit()
    conn.close()

def add_quiz_score(session_name, topic, score, total):
    """Save quiz score to database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO quiz_scores (session_name, topic, score, total, timestamp) VALUES (?, ?, ?, ?, ?)",
              (session_name, topic, score, total, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_quiz_history(session_name=None):
    """Retrieve quiz history"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if session_name:
        c.execute("SELECT * FROM quiz_scores WHERE session_name = ? ORDER BY timestamp DESC", (session_name,))
    else:
        c.execute("SELECT * FROM quiz_scores ORDER BY timestamp DESC")
    results = c.fetchall()
    conn.close()
    return results

# ============== STYLING ==============
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
.flashcard {
    border: 2px solid #6366f1;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-size: 18px;
    font-weight: bold;
}
.achievement {
    display: inline-block;
    padding: 12px;
    margin: 5px;
    border-radius: 8px;
    background-color: #fbbf24;
    color: #1a1a1a;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div style="text-align:center; padding: 32px 0;">
<h1 style="margin:0;">🎓 <span style="color:#6366f1;">AI Mentor Study Assistant Pro</span></h1>
<p style="color:#666;">Smart Learning • Flashcards • Progress Tracking • Q&A • Exams • Achievements</p>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ============== HELPER FUNCTIONS ==============
def fetch_videos_for_topics(topics):
    """Generate video resource links"""
    results = {}
    for t in topics:
        q = quote_plus(f"{t} tutorial")
        url = f"https://www.youtube.com/results?search_query={q}"
        results[t] = [{"title": f"📺 {t}", "url": url, "note": "YouTube search"}]
    return results

def build_sim_search_links(topic: str):
    """Generate interactive learning resource links"""
    items = []
    q = quote_plus(topic)
    
    items.append({
        "title": "🔬 PhET Simulations",
        "url": f"https://phet.colorado.edu/en/simulations?subjects=physics,chemistry,math,biology&type=html,prototype",
        "note": "Physics, Chemistry, Math, Biology simulations"
    })
    
    items.append({
        "title": "🎓 Khan Academy",
        "url": f"https://www.khanacademy.org/search?page_search_query={q}",
        "note": "Video lessons & practice exercises"
    })
    
    items.append({
        "title": "📊 Desmos Graphing",
        "url": f"https://www.desmos.com/calculator",
        "note": "Interactive graphing & math tools"
    })
    
    items.append({
        "title": "🧮 GeoGebra",
        "url": f"https://www.geogebra.org/search/{q}",
        "note": "Interactive math & science applets"
    })
    
    items.append({
        "title": "⚙️ Wolfram Alpha",
        "url": f"https://www.wolframalpha.com/input?i={q}",
        "note": "Computational answers & visualizations"
    })
    
    items.append({
        "title": "🎬 Educational Videos",
        "url": f"https://www.youtube.com/results?search_query={q}+tutorial+explained",
        "note": "YouTube educational content"
    })
    
    return items

def truncate_chars(s: str, max_chars: int = 12000) -> str:
    """Truncate text to max length"""
    return s[:max_chars] if s else ""

@st.cache_data(show_spinner=False)
def extract_pdf_text(uploaded_file, use_ocr=False) -> str:
    """Extract text from PDF"""
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
    """Call OpenAI API"""
    if not client:
        st.error("⚠️ OpenAI API key not configured!")
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
    """Extract topics from text"""
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
    """Generate summary"""
    if not text:
        return ""
    prompt = f"Summarize these notes in 300 words, with key concepts and one example:\n\n{truncate_chars(text, 6000)}"
    return openai_complete(prompt, temperature=0.25, max_tokens=500)

# ============== TIER 1: FLASHCARD GENERATOR ==============
def generate_flashcards(text: str, num_cards=10):
    """Generate flashcards from text"""
    if not text:
        return []
    prompt = f'''Create {num_cards} flashcard pairs (front/back) from this text.
Format as JSON array: [{{"front":"Question?","back":"Answer..."}}]
Return ONLY JSON.

Text: {truncate_chars(text, 5000)}'''
    response = openai_complete(prompt, temperature=0.2, max_tokens=1500)
    try:
        if response:
            flashcards = json.loads(response.replace("```json","").replace("```","").strip())
            return flashcards
    except:
        st.error("Failed to generate flashcards")
    return []

def export_anki_format(flashcards):
    """Export flashcards as Anki format (TSV)"""
    if not flashcards:
        return ""
    lines = []
    for fc in flashcards:
        lines.append(f"{fc['front']}\t{fc['back']}")
    return "\n".join(lines)

# ============== TIER 1: AUDIO STUDY NOTES ==============
def generate_audio(text: str, voice_speed=1.0):
    """Convert text to audio using gTTS"""
    if not text:
        return None
    try:
        tts = gTTS(text=text, lang='en', slow=(voice_speed < 1.0))
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except Exception as e:
        st.error(f"Audio generation failed: {e}")
        return None

# ============== TIER 2: SEMANTIC SEARCH (Q&A) ==============
def generate_embeddings(text: str):
    """Generate embeddings for semantic search"""
    if not client:
        return None
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        st.error(f"Embedding generation failed: {e}")
        return None

def answer_question(context: str, question: str):
    """Answer a question based on document context"""
    if not context or not question:
        return ""
    prompt = f'''Answer this question based ONLY on the provided context. 
If the answer is not in the context, say "Not found in the provided text".
Include the relevant section from the context in your answer.

Context:
{truncate_chars(context, 3000)}

Question: {question}'''
    return openai_complete(prompt, temperature=0.3, max_tokens=500)

# ============== TIER 2: PRACTICE EXAM MODE ==============
def generate_timed_quiz(text: str, num_q=10, difficulty="medium"):
    """Generate timed quiz with difficulty levels"""
    if not text:
        return []
    
    difficulty_prompts = {
        "easy": "Create simple, basic questions",
        "medium": "Create moderate difficulty questions",
        "hard": "Create challenging, detailed questions"
    }
    
    prompt = f'''{difficulty_prompts.get(difficulty, "Create moderate difficulty questions")} from this text.
Create {num_q} multiple-choice questions.
Format as JSON array: [{{"question":"Q?","choices":["A","B","C","D"],"answer_index":0,"explanation":"..."}}]
Return ONLY JSON.

Text: {truncate_chars(text, 5000)}'''
    
    response = openai_complete(prompt, temperature=0.3, max_tokens=1500)
    try:
        if response:
            quiz = json.loads(response.replace("```json","").replace("```","").strip())
            return quiz
    except:
        st.error("Failed to generate exam")
    return []

# ============== TIER 3: GAMIFICATION ==============
def check_achievement(score_percentage):
    """Determine achievements based on score"""
    achievements = []
    if score_percentage == 100:
        achievements.append(("🏆 Perfect Score!", "Scored 100%!"))
    if score_percentage >= 80:
        achievements.append(("⭐ Star Student", "80% or higher"))
    if score_percentage >= 50:
        achievements.append(("📚 Learner", "Completed quiz"))
    return achievements

# ============== SESSION STATE ==============
init_db()

if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = None
if "topics" not in st.session_state:
    st.session_state.topics = []
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "quiz" not in st.session_state:
    st.session_state.quiz = []
if "flashcards" not in st.session_state:
    st.session_state.flashcards = []
if "streak" not in st.session_state:
    st.session_state.streak = 0
if "achievements" not in st.session_state:
    st.session_state.achievements = []
if "session_name" not in st.session_state:
    st.session_state.session_name = f"Study_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ============== SIDEBAR ==============
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if "model" not in st.session_state:
        st.session_state.model = "gpt-4o-mini"
    model = st.selectbox("Model:", ["gpt-4o-mini", "gpt-4o"], index=0)
    st.session_state.model = model
    
    st.divider()
    
    st.markdown("### 📊 Progress Dashboard")
    history = get_quiz_history()
    if history:
        scores = [h[3]/h[4]*100 for h in history]
        avg_score = sum(scores) / len(scores) if scores else 0
        st.metric("Average Score", f"{avg_score:.1f}%")
        st.metric("Total Quizzes", len(history))
        
        if st.button("📈 View Progress Chart"):
            if PLOTLY_AVAILABLE:
                fig = px.bar(x=list(range(len(scores))), y=scores, title="Quiz Score History")
                st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    if st.session_state.achievements:
        st.markdown("### 🏆 Achievements Unlocked")
        for badge, desc in st.session_state.achievements:
            st.markdown(f'<div class="achievement">{badge}</div>', unsafe_allow_html=True)
    
    st.divider()
    st.caption("v2.0 Pro | Powered by OpenAI")

# ============== MAIN APP ==============
st.markdown("### 📄 Upload PDF")
uploaded = st.file_uploader("Choose PDF", type="pdf", label_visibility="collapsed")

if uploaded:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="status-badge done">✅ PDF</div>' if st.session_state.extracted_text else '<div class="status-badge pending">⏳ PDF</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="status-badge done">✅ Topics</div>' if st.session_state.topics else '<div class="status-badge pending">⏳ Topics</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="status-badge done">✅ Summary</div>' if st.session_state.summary else '<div class="status-badge pending">⏳ Summary</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="status-badge done">✅ Resources</div>' if st.session_state.topics else '<div class="status-badge pending">⏳ Resources</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("⚡ Process PDF", use_container_width=True):
        if not client:
            st.error("🔑 OpenAI API Key Missing! Configure in Settings.")
        else:
            with st.spinner("📄 Extracting text..."):
                text = extract_pdf_text(uploaded)
                if text:
                    st.session_state.extracted_text = text
                    st.success("✅ Text extracted successfully")
                else:
                    st.error("❌ No text extracted")
            
            if st.session_state.extracted_text:
                with st.spinner("🎯 Detecting topics..."):
                    topics = ai_extract_topics(st.session_state.extracted_text)
                    st.session_state.topics = topics
                    if topics:
                        st.success(f"✅ Found {len(topics)} topics")
                
                with st.spinner("📝 Generating summary..."):
                    summary = ai_summarize(st.session_state.extracted_text)
                    st.session_state.summary = summary
                    if summary:
                        st.success("✅ Summary generated")
            
            st.rerun()
    
    st.markdown("---")
    
    # ============== ENHANCED TABS ==============
    tabs = st.tabs(["📝 Summary", "🎥 Videos", "🧪 Labs", "❓ Quiz", "🎴 Flashcards", "🎤 Audio", "❔ Q&A", "🎯 Exam", "📊 Progress", "📦 Export"])
    
    # TAB 0: Summary
    with tabs[0]:
        st.subheader("📝 Summary")
        if st.session_state.summary:
            st.markdown(st.session_state.summary)
            st.download_button("⬇️ Download MD", data=st.session_state.summary, file_name="summary.md", mime="text/markdown")
        else:
            st.info("Click **Process PDF** to generate summary")
    
    # TAB 1: Videos
    with tabs[1]:
        st.subheader("🎥 Video Resources")
        if st.session_state.topics:
            videos = fetch_videos_for_topics(st.session_state.topics)
            for topic, items in videos.items():
                st.markdown(f"**{topic}**")
                for v in items:
                    st.markdown(f"[{v['title']}]({v['url']})")
        else:
            st.info("Process PDF to detect topics")
    
    # TAB 2: Interactive Labs
    with tabs[2]:
        st.subheader("🧪 Interactive Resources")
        if st.session_state.topics:
            for topic in st.session_state.topics:
                st.markdown(f"**{topic}**")
                for link in build_sim_search_links(topic):
                    st.markdown(f"[{link['title']}]({link['url']})")
        else:
            st.info("Process PDF to detect topics")
    
    # TAB 3: Regular Quiz
    with tabs[3]:
        st.subheader("❓ Practice Quiz")
        if st.session_state.extracted_text:
            num_q = st.slider("Questions:", 3, 15, 5)
            if st.button("🎲 Generate Quiz"):
                with st.spinner("Generating quiz..."):
                    prompt = f'''Create {num_q} multiple-choice questions from this text.
Format as JSON array: [{{"question":"Q?","choices":["A","B","C","D"],"answer_index":0,"explanation":"..."}}]
Return ONLY JSON.

Text: {truncate_chars(st.session_state.extracted_text, 5000)}'''
                    response = openai_complete(prompt, temperature=0.2, max_tokens=1500)
                    try:
                        quiz = json.loads(response.replace("```json","").replace("```","").strip())
                        st.session_state.quiz = quiz
                    except:
                        st.error("Failed to generate quiz")
            
            if st.session_state.quiz:
                score = 0
                total = len(st.session_state.quiz)
                for i, q in enumerate(st.session_state.quiz, 1):
                    st.markdown(f"**Q{i}. {q['question']}**")
                    ans = st.radio(f"Q{i}", q["choices"], key=f"q_{i}", label_visibility="collapsed")
                    if st.button("Check", key=f"btn_{i}"):
                        correct = q["choices"][q["answer_index"]]
                        if ans == correct:
                            st.success("✅ Correct!")
                            score += 1
                        else:
                            st.error(f"❌ Correct answer: {correct}")
                        st.info(f"**Explanation:** {q.get('explanation', 'N/A')}")
        else:
            st.info("Process PDF first")
    
    # TAB 4: TIER 1 - Flashcards
    with tabs[4]:
        st.subheader("🎴 Flashcard Generator")
        if st.session_state.extracted_text:
            num_cards = st.slider("Number of flashcards:", 5, 30, 10)
            if st.button("📚 Generate Flashcards"):
                with st.spinner("Creating flashcards..."):
                    cards = generate_flashcards(st.session_state.extracted_text, num_cards)
                    if cards:
                        st.session_state.flashcards = cards
                        st.success(f"✅ Created {len(cards)} flashcards")
            
            if st.session_state.flashcards:
                st.markdown("### Study Your Flashcards")
                if "card_index" not in st.session_state:
                    st.session_state.card_index = 0
                if "card_flipped" not in st.session_state:
                    st.session_state.card_flipped = False
                
                card = st.session_state.flashcards[st.session_state.card_index]
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    if st.button("⬅️ Previous"):
                        st.session_state.card_index = max(0, st.session_state.card_index - 1)
                        st.session_state.card_flipped = False
                        st.rerun()
                with col2:
                    st.markdown(f"<div class='flashcard'>{card['front'] if not st.session_state.card_flipped else card['back']}</div>", unsafe_allow_html=True)
                with col3:
                    if st.button("Next ➡️"):
                        st.session_state.card_index = min(len(st.session_state.flashcards) - 1, st.session_state.card_index + 1)
                        st.session_state.card_flipped = False
                        st.rerun()
                
                st.button("🔄 Flip Card", key="flip", on_click=lambda: st.session_state.update({"card_flipped": not st.session_state.card_flipped}))
                st.caption(f"Card {st.session_state.card_index + 1} of {len(st.session_state.flashcards)}")
                
                # Export flashcards
                anki_format = export_anki_format(st.session_state.flashcards)
                st.download_button("📥 Download (Anki Format)", data=anki_format, file_name="flashcards.txt", mime="text/plain")
        else:
            st.info("Process PDF first")
    
    # TAB 5: TIER 1 - Audio Notes
    with tabs[5]:
        st.subheader("🎤 Audio Study Notes")
        if st.session_state.summary:
            st.markdown("Convert your summary to audio for listening on-the-go!")
            voice_speed = st.slider("Speed:", 0.5, 2.0, 1.0)
            
            if st.button("🎙️ Generate Audio"):
                with st.spinner("Generating audio..."):
                    audio = generate_audio(st.session_state.summary, voice_speed)
                    if audio:
                        st.audio(audio, format="audio/mp3")
                        st.download_button("⬇️ Download MP3", data=audio, file_name="study_notes.mp3", mime="audio/mp3")
        else:
            st.info("Generate summary first")
    
    # TAB 6: TIER 2 - Q&A (Semantic Search)
    with tabs[6]:
        st.subheader("❔ Ask Questions About Your Notes")
        if st.session_state.extracted_text:
            question = st.text_input("💭 Ask a question about the content...")
            if question and st.button("🔍 Search"):
                with st.spinner("Finding answer..."):
                    answer = answer_question(st.session_state.extracted_text, question)
                    if answer:
                        st.markdown(f"**Answer:**\n{answer}")
        else:
            st.info("Process PDF first")
    
    # TAB 7: TIER 2 - Practice Exam
    with tabs[7]:
        st.subheader("🎯 Practice Exam Mode")
        if st.session_state.extracted_text:
            col1, col2, col3 = st.columns(3)
            with col1:
                num_exam_q = st.slider("Questions:", 5, 20, 10)
            with col2:
                difficulty = st.selectbox("Difficulty:", ["easy", "medium", "hard"])
            with col3:
                time_limit = st.slider("Time (min):", 5, 60, 15)
            
            if st.button("🚀 Start Exam"):
                with st.spinner("Generating exam..."):
                    exam_quiz = generate_timed_quiz(st.session_state.extracted_text, num_exam_q, difficulty)
                    if exam_quiz:
                        st.session_state.exam_quiz = exam_quiz
                        st.session_state.exam_start_time = time.time()
                        st.session_state.time_limit = time_limit * 60
                        st.success("Exam started! Answer all questions.")
            
            if "exam_quiz" in st.session_state:
                elapsed = time.time() - st.session_state.exam_start_time
                remaining = max(0, st.session_state.time_limit - elapsed)
                st.info(f"⏱️ Time remaining: {int(remaining//60)}:{int(remaining%60):02d}")
                
                if remaining <= 0:
                    st.error("⏰ Time's up!")
                else:
                    score = 0
                    for i, q in enumerate(st.session_state.exam_quiz, 1):
                        st.markdown(f"**Q{i}. {q['question']}**")
                        ans = st.radio(f"Q{i}", q["choices"], key=f"exam_q_{i}", label_visibility="collapsed")
                        correct = q["choices"][q["answer_index"]]
                        if ans == correct:
                            score += 1
                    
                    if st.button("📊 Submit Exam"):
                        percentage = (score / len(st.session_state.exam_quiz)) * 100
                        st.success(f"✅ Score: {score}/{len(st.session_state.exam_quiz)} ({percentage:.1f}%)")
                        
                        # Check achievements
                        achievements = check_achievement(percentage)
                        for badge, desc in achievements:
                            if badge not in [a[0] for a in st.session_state.achievements]:
                                st.session_state.achievements.append((badge, desc))
                                st.balloons()
                        
                        add_quiz_score(st.session_state.session_name, "Exam", score, len(st.session_state.exam_quiz))
        else:
            st.info("Process PDF first")
    
    # TAB 8: TIER 3 - Progress Dashboard
    with tabs[8]:
        st.subheader("📊 Your Learning Progress")
        history = get_quiz_history()
        if history:
            scores = [h[3]/h[4]*100 for h in history]
            
            # Show metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Quizzes", len(history))
            with col2:
                st.metric("Average Score", f"{sum(scores)/len(scores):.1f}%")
            with col3:
                st.metric("Best Score", f"{max(scores):.1f}%")
            with col4:
                st.metric("Streak", st.session_state.streak)
            
            # Show chart
            if PLOTLY_AVAILABLE:
                fig = go.Figure()
                fig.add_trace(go.Scatter(y=scores, mode='lines+markers', name='Score', line=dict(color='#6366f1')))
                fig.update_layout(title="Quiz Score Progress", xaxis_title="Quiz #", yaxis_title="Score %")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart(scores)
            
            # Show achievements
            if st.session_state.achievements:
                st.markdown("### 🏆 Achievements")
                for badge, desc in st.session_state.achievements:
                    st.markdown(f'<div class="achievement">{badge}</div>', unsafe_allow_html=True)
        else:
            st.info("No quiz history yet. Take some quizzes to see progress!")
    
    # TAB 9: Export
    with tabs[9]:
        st.subheader("📦 Export Study Pack")
        
        export_data = {
            "session_name": st.session_state.session_name,
            "topics": st.session_state.topics,
            "summary": st.session_state.summary,
            "flashcards": st.session_state.flashcards,
            "quiz": st.session_state.quiz,
            "created_at": datetime.now().isoformat(),
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 JSON Export",
                data=json.dumps(export_data, indent=2),
                file_name="study_pack.json"
            )
        with col2:
            if st.session_state.flashcards:
                anki = export_anki_format(st.session_state.flashcards)
                st.download_button(
                    "📚 Anki Flashcards",
                    data=anki,
                    file_name="flashcards.txt"
                )

else:
    st.info("👆 Upload a PDF to start learning!")

st.markdown("---")
st.caption("🚀 AI Mentor v2.0 Pro | All Tier Features Included | Powered by OpenAI")
