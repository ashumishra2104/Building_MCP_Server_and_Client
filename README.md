# 🤖 Building MCP Servers and Clients — by Ashu Mishra

> A hands-on collection of MCP (Model Context Protocol) servers, clients, and AI-powered applications — built from scratch for AI Product Management students and developers who want to give AI models real-world superpowers.

---

## 🧠 What is MCP?

**Model Context Protocol (MCP)** is an open standard that lets you connect AI models like Claude to external tools, data sources, and services.

Think of it like this:

```
Claude (Brain)  +  MCP Server (Hands)  =  Claude that can actually DO things
```

Instead of Claude just *talking* about running a command, fetching data, or searching jobs — with an MCP server, it can actually **do it**.

---

## 📂 Repository Structure

```
Building_MCP_Server_and_Client/
│
├── README.md                          ← You are here
│
├── Theory of MCP/                     ← Start here! Understand MCP first
│   ├── README.md
│   └── MCP_Comprehensive_Summary.md   ← Full theory document
│
├── First MCP Terminal Server/         ← Project 1: Your first MCP server
│   ├── README.md                      ← Step-by-step guide
│   └── main.py                        ← Server code
│
├── MCP Client (React & Electron)/     ← Project 2: Web & desktop MCP client
│   └── README.md
│
├── Weather-mcp/                       ← Project 3: Weather MCP server
│   ├── main.py                        ← MCP server entry point
│   ├── tools/                         ← Weather tool definitions
│   ├── pyproject.toml
│   └── README.md
│
└── Job_Recommender_App/               ← Project 4: Full AI-powered application
    ├── app.py                         ← Streamlit web app
    ├── mcp_server.py                  ← FastMCP server for job search
    ├── src/
    │   ├── helper.py                  ← PDF reader + GPT + WeasyPrint
    │   ├── job_api.py                 ← Apify LinkedIn + Naukri scrapers
    │   └── database.py               ← Supabase + SQLite persistence
    ├── resume_template.html           ← HTML template for tailored resumes
    ├── requirements.txt
    └── video_guide/
        └── Step_By_Step_Creation_Guide.md  ← Full coding guide
```

---

## 🗂️ Projects Overview

| # | Project | What it does | Type |
|:--|:--------|:-------------|:-----|
| 1 | [Theory of MCP](./Theory%20of%20MCP/) | Understand what MCP is, why it exists, and how it works | 📖 Theory |
| 2 | [First MCP Terminal Server](./First%20MCP%20Terminal%20Server/) | Build a server that lets Claude run real terminal commands | 🛠️ Beginner |
| 3 | [MCP Client — React & Electron](./MCP%20Client%20(React%20%26%20Electron)/) | A modern web and desktop interface for any MCP server | 🛠️ Intermediate |
| 4 | [Weather MCP Server](./Weather-mcp/) | An MCP server that fetches live weather data as a Claude tool | 🛠️ Intermediate |
| 5 | [AI Job Recommender App](./Job_Recommender_App/) | Full-stack AI app — resume analysis, job scraping, resume tailoring | 🚀 Advanced |

---

## 🚀 Project 5 — AI Job Recommender App (Featured)

The most complete project in this repo. A production-grade AI application built using **Google Antigravity** that:

- 📄 **Reads your PDF resume** using PyMuPDF
- 🧠 **Analyses it with GPT-4o-mini** — generates a summary, skill gaps, and career roadmap
- 🔍 **Searches live jobs** on LinkedIn and Naukri via Apify web scrapers
- ✍️ **Tailors your resume** to any job description using GPT-4o
- 📥 **Downloads a PDF** of the tailored resume via WeasyPrint
- 🗄️ **Caches all jobs** to Supabase (cloud) with SQLite as local fallback
- 🔌 **Exposes job search as MCP tools** via FastMCP for AI agents

### Tech Stack
`Streamlit` · `OpenAI GPT-4o` · `Apify` · `Supabase` · `SQLite` · `WeasyPrint` · `FastMCP` · `PyMuPDF`

### 📋 Step-by-Step Creation Guide
Want to build this from scratch yourself? A full video coding guide with AI prompts, checkpoints, and explanations is available here:
👉 [Step_By_Step_Creation_Guide.md](./Job_Recommender_App/video_guide/Step_By_Step_Creation_Guide.md)

---

## 🛤️ Recommended Learning Path

If you're new to MCP, follow this order:

```
1. Theory of MCP          → Understand the WHY and WHAT
        ↓
2. First MCP Terminal     → Build your first server (beginner-friendly)
        ↓
3. Weather MCP Server     → Add real data sources to your server
        ↓
4. MCP Client             → Build a UI that talks to any MCP server
        ↓
5. Job Recommender App    → Full production AI app with MCP inside
```

---

## 🛠️ Common Requirements

Before starting any project, make sure you have:

| Tool | Version | Link |
|------|---------|------|
| Python | 3.11+ | https://python.org |
| Claude Desktop | Latest | https://claude.ai/download |
| VS Code or Cursor | Latest | https://cursor.sh |
| Git | Latest | https://git-scm.com |
| `uv` package manager | Latest | `pip install uv` |

---

## 🔑 APIs Used Across Projects

| API / Service | Used In | Get it at |
|--------------|---------|-----------|
| OpenAI API | Job Recommender | https://platform.openai.com/api-keys |
| Apify | Job Recommender | https://apify.com |
| Supabase | Job Recommender | https://supabase.com |
| Streamlit Cloud | Job Recommender (deploy) | https://streamlit.io/cloud |

---

## 👨‍🏫 About This Repository

Built as part of an **AI Product Management course** by [Ashu Mishra](https://github.com/ashumishra2104) — Senior AI/ML Product Manager with 7+ years across fintech, e-commerce, and AI-driven products.

Every project is designed to be:
- ✅ Beginner-friendly with plain English explanations
- ✅ Compatible with Mac and Windows
- ✅ Visual — with diagrams and architecture breakdowns
- ✅ Practical — real tools, real APIs, real deployments

---

## 📬 Connect

- GitHub: [@ashumishra2104](https://github.com/ashumishra2104)

---

*⭐ Star this repo if you find it helpful — it helps other students discover it!*
