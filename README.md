AI-Mentor-Study-Assistant-main is a GitHub repository for an intelligent AI-powered study companion that helps students with personalized learning plans, exam prep, progress tracking, and interactive Q&A across subjects.

Overview
This repository builds a full-stack web app acting as your personal AI mentor. It generates dynamic study schedules based on exam dates and subjects, analyzes uploaded PDFs for key insights, curates resources, and tracks your performance with visual analytics. Designed for students in Coimbatore or anywhere, it adapts to your pace using modern AI APIs for fast, accurate guidance.

Key Features
Smart Study Planner: Custom weekly/daily tasks optimized for deadlines and subjects.

PDF Analyzer: Extracts text, summarizes content, and suggests focus areas.

Progress Dashboard: Charts completion rates, weak spots, and motivational streaks.

AI Chat Tutor: Real-time answers, quizzes, and explanations via natural language.

Resource Finder: Pulls relevant articles, videos, and notes from trusted sources.

Tech Stack
Component	Technologies
Frontend	Next.js 14 (TypeScript), Tailwind CSS, Shadcn UI, Zustand, React Query
Backend	Node.js/Express, MongoDB (Mongoose), JWT auth
AI/ML	Groq API (plans/Q&A), HuggingFace (embeddings), Tavily (resources)
Other	Docker Compose, PDF.js for processing, rate limiting
Quick Setup
Clone: git clone https://github.com/yourusername/AI-Mentor-Study-Assistant-main.git && cd AI-Mentor-Study-Assistant-main

Install: npm install (frontend/backend)

Env vars: Add .env with OPEN_API_KEY, MONGODB_URI, etc.

Run: docker compose up -d – Access at localhost:3000.

Usage Example
Upload a physics PDF, set exam date, get a 2-week plan with daily quizzes. AI flags weak topics like thermodynamics and links Khan Academy videos.
