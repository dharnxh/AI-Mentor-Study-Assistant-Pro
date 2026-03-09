# 🎓 AI Mentor Study Assistant PRO v2.0

Turn any lecture PDF into **10 powerful learning modes**:

**Tier 1 (Core):** Flashcards • Audio Notes  
**Tier 2 (Advanced):** Semantic Q&A • Practice Exams  
**Tier 3 (Gamification):** Progress Dashboard • Achievement Badges  
**Original:** Summaries • Videos • Labs • Quizzes • Exports

Transform any PDF into a complete AI-powered study system!

> **Live Demo:**
![ezgif com-video-to-gif-converter (1)](https://github.com/user-attachments/assets/3220b1de-0d94-4fd4-802f-404565e1b0e4)

 
> **Browser Link:** [https://ai-mentor-study-assistant-tvv5bhksyvyderelpq8pmh.streamlit.app/](https://ai-mentor-study-assistant-tvv5bhksyvyderelpq8pmh.streamlit.app/)

-----

## 🚀 What's New in v2.0?

| Feature | Type | What it Does |
|---------|------|-------------|
| 🎴 **Flashcard Generator** | Tier 1 | Auto-generate & study flashcards (Anki compatible) |
| 🎤 **Audio Study Notes** | Tier 1 | Convert summaries to MP3 (0.5x-2.0x speed) |
| ❔ **Q&A / Semantic Search** | Tier 2 | Ask questions about your PDF content |
| 🎯 **Practice Exam Mode** | Tier 2 | Timed exams with 3 difficulty levels |
| 📊 **Progress Dashboard** | Tier 3 | Track scores, view charts, see trends |
| 🏆 **Achievement Badges** | Tier 3 | Unlock badges for reaching milestones |
| 📝 **Summary** | Original | AI-powered study summaries |
| 🎥 **Video Resources** | Original | YouTube tutorials for each topic |
| 🧪 **Interactive Labs** | Original | PhET, Khan Academy, Desmos, GeoGebra, Wolfram |
| ❓ **Practice Quizzes** | Original | Regular AI-generated quizzes |
| 📦 **Data Export** | Original | JSON, Anki format downloads |

**Total: 11 Features | 10 Tabs | 3 Tiers | Production Ready**

-----

## 🛠️ Tech Stack

  * **Language:** Python 3.13.5
  * **Frameworks:** Streamlit, OpenAI
  * **Core Libraries:** pdfplumber, gTTS, plotly, numpy
  * **Database:** SQLite3
  * **Visualization:** Plotly Interactive Charts
  * **API:** OpenAI GPT-4o-mini & GPT-4o

-----

## 📦 Installation

To get started, follow these steps:

1.  **Clone the repository and navigate into the directory:**
    ```bash
    git clone https://github.com/<your-username>/AI-Mentor-Study-Assistant.git
    cd AI-Mentor-Study-Assistant
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Mac/Linux
    source venv/bin/activate
    # Windows (PowerShell)
    venv\Scripts\Activate.ps1
    ```
3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚡ 30-Second Quick Start

```bash
# 1. Set API Key
export OPENAI_API_KEY="sk-your-key-here"

# 2. Run the app
streamlit run app.py

# 3. Open browser
http://localhost:8501

# 4. Upload PDF & Start Learning!
```

-----

## ▶ Run Locally

1.  **Set up your API key:**
    Create a `.env` file in the project root and add your OpenAI key:
    ```
    OPENAI_API_KEY=sk-...
    ```
2.  **Start the application:**
    ```bash
    streamlit run app.py
    ```
    This will open the app in your browser.

-----

## 💡 How to Use

1.  **Upload a PDF** (lecture slides, notes, or an article).
2.  **Select your learning modes**: Choose from videos, a summary, a voiceover, or practice questions.
3.  **Export your study materials**: Click **Export** to save a `.md` file with the summary, links, and notes.

-----

## 📂 Project Structure

```
AI-Mentor-Study-Assistant/
├─ app.py                # Main Streamlit application
├─ requirements.txt      # Python dependencies
├─ README.md             # README
├─ .env                  # API keys (not shown)
├─ src/
│  ├─ audio.py           # Text-to-speech helpers
│  ├─ quiz.py            # Quiz generation logic
│  ├─ summarizer.py      # OpenAI summary helpers
│  ├─ utils.py           # Shared helper functions
│  └─ videos.py          # YouTube video fetchers
└─ data/
   ├─ uploads/           # Uploaded PDFs
   └─ exports/           # Exported study materials
```

-----

## 🛣️ Roadmap

  * Additional voice models.
  * Richer simulations and spaced-repetition scheduling.
  * Per-topic flashcards.

-----

---

## 🛣️ Roadmap

**Completed (v2.0):**
- ✅ Flashcard generator with Anki export
- ✅ Audio notes with adjustable speed
- ✅ Semantic Q&A search
- ✅ Timed practice exams
- ✅ Progress dashboard with charts
- ✅ Achievement badges
- ✅ SQLite data persistence

**Future (v3.0):**
- ☁️ Cloud sync (Google Drive, Dropbox)
- 👥 Collaborative study groups
- 📱 Mobile app
- 🔐 User authentication
- 📊 Advanced analytics
- 🌍 Multi-language support

---

## 🎓 Learning Tips

### For Maximum Retention:
1. **Start with Summary** - Get the big picture
2. **Create Flashcards** - Active recall
3. **Listen to Audio** - Multi-modal learning
4. **Ask Q&A** - Fill knowledge gaps
5. **Take Exams** - Test-style practice
6. **Track Progress** - Stay motivated
7. **Unlock Badges** - Gamified motivation

### Recommended Study Plan:
- **Day 1-2:** Read summary + Create flashcards
- **Day 3-5:** Review flashcards + Listen to audio
- **Day 6:** Ask Q&A questions + Take practice quiz
- **Day 7:** Timed practice exam + Review progress

---

## 🙋 FAQ

**Q: Do I need an OpenAI key?**  
A: Yes, to use AI features. Get a free API key at https://platform.openai.com

**Q: Does it work with scanned PDFs?**  
A: Text-based PDFs work best. Scanned PDFs may require OCR (optional).

**Q: Can I export my data?**  
A: Yes! Export as JSON or Anki format from Tab 10.

**Q: Is my data safe?**  
A: All data stored locally. No cloud sync without your permission.

**Q: What's the cost?**  
A: Free to use + minimal OpenAI API costs (~$0.01-0.10 per PDF)

**Q: How many tabs are there?**  
A: 10 powerful tabs with 11 total features!

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **QUICKSTART.md** | 📖 Quick-start guide (30 min) |
| **FEATURES_GUIDE.md** | 📖 Complete feature documentation |
| **IMPLEMENTATION_SUMMARY.md** | 📖 Technical details |

---

## 📦 Project Structure

```
AI-Mentor-Study-Assistant-main/
├─ app.py                    # Main app (722 lines, all features)
├─ requirements.txt          # Dependencies (updated with plotly)
├─ README.md                 # This file
├─ QUICKSTART.md             # Quick start guide
├─ FEATURES_GUIDE.md         # Comprehensive feature docs
├─ IMPLEMENTATION_SUMMARY.md # Technical implementation
├─ study_sessions.db         # SQLite database (auto-created)
├─ .env                      # API keys
└─ .streamlit/
   └─ secrets.toml           # Alternative key storage
```

-----

## 🤝 Contributing

Please open an issue to discuss any significant changes before submitting a pull request.

-----

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

-----

## 🙏 Acknowledgments

  * **OpenAI** for the summarization APIs.
  * **Streamlit** for the rapid UI development.
  * **pdfplumber** for PDF text extraction.
  * **gTTS** for text-to-speech functionality.
