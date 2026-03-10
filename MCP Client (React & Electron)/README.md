# 🖥️ MCP Client (React & Electron)

This is a modern, cross-platform client for interacting with any MCP (Model Context Protocol) server. It provides both a web-based chat interface and a standalone Electron desktop application.

## ✨ Features

- **Web Interface**: A clean React-based chat UI built with Vite.
- **Desktop App**: A standalone Electron application for a native experience.
- **FastAPI Backend**: A robust Python backend that bridges the Gemini AI with MCP servers.
- **Real-time Interaction**: Watch as Gemini calls tools and processes results in real-time.

## 🚀 Getting Started

### 1. Prerequisites

- [Python 3.10+](https://python.org)
- [Node.js 18+](https://nodejs.org)
- [uv](https://github.com/astral-sh/uv) (recommended for Python package management)

### 2. Setup

1. Rename `.env.example` to `.env`.
2. Add your `GEMINI_API_KEY` to the `.env` file.
3. Install dependencies:

   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend && npm install
   
   # Electron
   cd electron && npm install
   ```

### 3. Running the App

1. **Start the Backend**:

   ```bash
   python backend.py
   ```

2. **Start the Frontend** (Development):

   ```bash
   cd frontend && npm run dev
   ```

3. **Start Electron**:

   ```bash
   cd electron && npm start
   ```

## 🛠️ Project Structure

- `backend.py`: The FastAPI server handling AI logic and MCP connections.
- `client.py`: The core MCP client logic utilizing Google's Gen AI SDK.
- `frontend/`: The React application source code.
- `electron/`: The Electron wrapper for the desktop experience.
