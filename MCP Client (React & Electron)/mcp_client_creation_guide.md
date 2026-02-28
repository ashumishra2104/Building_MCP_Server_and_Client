# 🚀 Step-by-Step Guide: Building MCP Client (React & Electron)

This guide walks you through creating a modern MCP client from scratch, including a Python backend, a React frontend, and an Electron desktop wrapper.

---

## 🛠️ Phase 1: Backend Setup (FastAPI & MCP Logic)

The backend acts as the bridge between the Gemini AI and any MCP server.

### 1. Initialize the Project

Create a new directory and set up a virtual environment:

```bash
mkdir mcp-client && cd mcp-client
uv init  # Or use: python -m venv .venv && source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install fastapi uvicorn google-genai mcp python-dotenv
```

### 3. Create `client.py` (The Brain)

This file handles the connection to MCP servers and manages tool calls using Gemini.

- Use `google.genai` for the AI client.
- Implement `MCPClient` class with `connect_to_server` and `process_query` methods.

### 4. Create `backend.py` (The API)

Expose the client logic via FastAPI:

- Setup **CORS** middleware (essential for React).
- Create `/connect` (POST) and `/query` (POST) endpoints.

### 5. Setup Environment Variables

Create a `.env` file:

```text
GEMINI_API_KEY="YOUR_ACTUAL_KEY_HERE"
```

---

## 💻 Phase 2: Frontend Setup (React + Vite)

### 1. Create the React App

Inside your project root:

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install axios
```

### 2. Build the UI (`App.jsx`)

- Create a simple chat interface.
- Use `axios` to send user queries to the FastAPI backend (`http://localhost:8000/query`).
- Add a field to input the MCP server script path.

---

## 🖥️ Phase 3: Desktop App (Electron)

### 1. Initialize Electron

In the root directory:

```bash
mkdir electron && cd electron
npm init -y
npm install electron --save-dev
```

### 2. Create `main.js`

Configure Electron to open a window and load the local React dev server (usually `http://localhost:5173`) or the built `index.html`.

---

## 🧹 Phase 4: Cleanup & Security

**CRITICAL: Never push your API keys to GitHub.**

1. **Secure `.env`**:
   - Create a copy called `.env.example` with placeholders.
   - Ensure `.env` is in your `.gitignore`.
2. **Create `.gitignore`**:
   Add the following to a `.gitignore` file in your root:

   ```text
   .env
   .venv/
   node_modules/
   __pycache__/
   dist/
   .DS_Store
   ```

---

## 📤 Phase 5: Push to GitHub

### 1. Initialize Git

```bash
git init
git add .
git commit -m "Initial commit: MCP Client React & Electron"
```

### 2. Create Remote and Push

1. Go to GitHub and create a new repository.
2. Copy the URL and run:

   ```bash
   git remote add origin https://github.com/USERNAME/REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

---

## 🚀 Success

Your project is now live on GitHub and ready for other developers to explore.
