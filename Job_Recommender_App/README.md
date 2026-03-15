# 💼 AI Job Recommender App

> An AI-powered job recommendation and resume tailoring system — built using **Google Antigravity** as part of an AI Product Management course.

---

## 📋 Want to Build This Yourself?

A complete **Step-by-Step Creation Guide** is available with:
- ✅ Exact prompts to paste into any AI IDE (Cursor / Antigravity / VS Code)
- ✅ Plain English explanation for every section
- ✅ Checkpoint prompts to test your work at each stage
- ✅ Setup guides for all APIs and accounts needed

👉 **[Open the Step-by-Step Creation Guide](./video_guide/Step_By_Step_Creation_Guide.md)**

---

## 🚀 What This App Does

| Feature | Description |
|---------|-------------|
| 📄 Resume Analysis | Upload a PDF — GPT-4o-mini summarises your resume, finds skill gaps, and builds a career roadmap |
| 🔍 Live Job Search | Searches LinkedIn and Naukri in real-time using Apify web scrapers |
| ✍️ Resume Tailoring | GPT-4o rewrites your resume to match any specific job description |
| 📥 PDF Export | Downloads the tailored resume as a formatted PDF via WeasyPrint |
| 🗄️ Job Caching | Saves all fetched jobs to Supabase (cloud) with SQLite as local fallback |
| 🔌 MCP Server | Exposes job search as tools for AI agents via FastMCP |

---

## 🏗️ Project Structure

```
Job_Recommender_App/
│
├── app.py                    ← Streamlit web app (main entry point)
├── mcp_server.py             ← FastMCP server — exposes job search to AI agents
├── resume_template.html      ← HTML template used for tailored resume PDF
├── requirements.txt          ← Python dependencies
├── packages.txt              ← System dependencies (for Streamlit Cloud)
├── .gitignore                ← Excludes .env, *.db, tailored PDFs
│
├── src/
│   ├── helper.py             ← PDF reader + OpenAI GPT + WeasyPrint PDF export
│   ├── job_api.py            ← Apify scrapers for LinkedIn and Naukri
│   └── database.py           ← Supabase (primary) + SQLite (fallback) storage
│
└── video_guide/
    └── Step_By_Step_Creation_Guide.md  ← Full guide to recreate this project
```

---

## ⚙️ Tech Stack

`Streamlit` · `OpenAI GPT-4o / GPT-4o-mini` · `Apify` · `Supabase` · `SQLite` · `WeasyPrint` · `FastMCP` · `PyMuPDF` · `Python 3.11`

---

## 🔑 Environment Variables Required

Create a `.env` file in this folder with:

```env
OPENAI_API_KEY=your_openai_api_key
APIFY_API_TOKEN=your_apify_api_token
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

> ⚠️ Never commit your `.env` file — it is already listed in `.gitignore`

---

## ▶️ Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web app
streamlit run app.py

# Run the MCP server (for AI agents)
python mcp_server.py
```

---

## 📖 Full Guide

For a complete walkthrough — including how every file was built, what prompts were used, and how to deploy on Streamlit Cloud:

👉 **[Step_By_Step_Creation_Guide.md](./video_guide/Step_By_Step_Creation_Guide.md)**

---

> Built with [Google Antigravity](https://antigravity.google) · Part of the [Building MCP Servers and Clients](../) repository by [Ashu Mishra](https://github.com/ashumishra2104)
