# StoryForge MCP

An AI-powered video script generator with D-ID video creation, exposed both as a Streamlit web app and an MCP (Model Context Protocol) server for use directly inside Claude Desktop.

---

## Features

- **Real-time research** on any topic via Tavily search
- **AI script generation** using OpenAI GPT-4o-mini (100–120 word short video scripts)
- **AI video creation** using D-ID (talking-head avatar videos)
- **MCP server** — use the tools directly from Claude Desktop
- **Streamlit UI** — browser-based interface for non-technical users

---

## Architecture

```mermaid
flowchart TD
    User(["👤 User"])

    subgraph Interfaces["Access Interfaces"]
        Streamlit["🖥️ Streamlit App\napp.py"]
        MCP["🤖 MCP Server\nmcp_server.py"]
    end

    subgraph Core["Core Logic — logic.py"]
        Tavily["🔍 get_realtime_info()\nTavily Web Search + GPT-4o-mini Summary"]
        Script["✍️ generate_video_script()\nOpenAI GPT-4o-mini"]
        Video["🎬 create_did_video()\nD-ID REST API"]
    end

    subgraph External["External APIs"]
        TavilyAPI["Tavily Search API"]
        OpenAI["OpenAI API\ngpt-4o-mini"]
        DID["D-ID API\nTalking-head Video"]
    end

    User -->|"enters topic"| Streamlit
    User -->|"calls tool"| MCP

    Streamlit --> Tavily
    Streamlit --> Script
    Streamlit --> Video

    MCP -->|"search_insights tool"| Tavily
    MCP -->|"write_script tool"| Tavily
    MCP -->|"write_script tool"| Script

    Tavily --> TavilyAPI
    Tavily --> OpenAI
    Script --> OpenAI
    Video --> DID

    TavilyAPI -->|"search results"| Tavily
    OpenAI -->|"summary / script"| Streamlit
    DID -->|"video URL"| Streamlit
```

---

## User Flow

```mermaid
flowchart TD
    Start([🚀 Open Streamlit App]) --> EnterTopic[Enter a Topic]
    EnterTopic --> ClickGenerate[Click Generate Insight & Script]
    ClickGenerate --> Searching[🔍 Searching web via Tavily...]
    Searching --> InsightReady{Insights found?}

    InsightReady -->|No| Warn1[⚠️ Show warning]
    Warn1 --> EnterTopic

    InsightReady -->|Yes| ShowInsight[📚 Display AI Summary]
    ShowInsight --> ScriptPrompt{Generate script?}

    ScriptPrompt -->|No| EnterTopic
    ScriptPrompt -->|Yes| Scripting[✍️ Generating script via OpenAI...]
    Scripting --> ScriptReady{Script generated?}

    ScriptReady -->|No| Warn2[⚠️ Show warning]
    ScriptReady -->|Yes| ShowScript[🎥 Display Script + Download button]
    ShowScript --> VideoPrompt{Generate AI video?}

    VideoPrompt -->|No| EnterTopic
    VideoPrompt -->|Yes| VideoGen[🎬 Creating video via D-ID API...]
    VideoGen --> VideoReady{Video ready?}

    VideoReady -->|Error| Warn3[❌ Show error]
    VideoReady -->|Yes| PlayVideo[▶️ Display Video in Browser]
    PlayVideo --> EnterTopic
```

---

## Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant App as Streamlit App
    participant Logic as logic.py
    participant Tavily as Tavily Search API
    participant OpenAI as OpenAI API
    participant DID as D-ID API

    User->>App: Enter topic & click Generate
    App->>Logic: get_realtime_info(topic)
    Logic->>Tavily: search(query, depth=advanced)
    Tavily-->>Logic: top 5 search results
    Logic->>OpenAI: Summarise results (gpt-4o-mini)
    OpenAI-->>Logic: AI summary
    Logic-->>App: refined_info
    App-->>User: Display AI Summary

    User->>App: Select Yes for script
    App->>Logic: generate_video_script(topic, refined_info)
    Logic->>OpenAI: Write 100-120 word video script
    OpenAI-->>Logic: video script
    Logic-->>App: script text
    App-->>User: Display Script + Download button

    User->>App: Select Yes for video
    App->>Logic: create_did_video(script)
    Logic->>DID: POST /talks (source_url + script text)
    DID-->>Logic: talk_id
    loop Poll every 3s (max 30x)
        Logic->>DID: GET /talks/{talk_id}
        DID-->>Logic: status (created / started / done)
    end
    DID-->>Logic: result_url (video URL)
    Logic-->>App: video URL
    App-->>User: Play AI talking-head video
```

---

## Project Structure

```text
Storyforge-mcp/
├── app.py            # Streamlit web UI
├── mcp_server.py     # FastMCP server (Claude Desktop integration)
├── logic.py          # Core functions: search, script, video
├── main.py           # Entry point placeholder
├── pyproject.toml    # Project dependencies
└── requirements.txt  # pip-compatible dependency list
```

---

## Setup

### 1. Install dependencies

```bash
uv sync
# or
pip install -r requirements.txt
```

### 2. Set environment variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
DID_API_KEY=your_did_api_key
```

### 3. Run the Streamlit app

```bash
streamlit run app.py
```

### 4. Use as an MCP server in Claude Desktop

Add to your `claude_desktop_config.json`:

```json
"StoryForge": {
  "command": "/path/to/.venv/bin/python",
  "args": ["/path/to/Storyforge-mcp/mcp_server.py"],
  "env": {
    "OPENAI_API_KEY": "your_openai_key",
    "TAVILY_API_KEY": "your_tavily_key"
  },
  "cwd": "/path/to/Storyforge-mcp"
}
```

---

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_insights(query)` | Research any topic and return an AI-summarised brief |
| `write_script(topic)` | Research a topic and generate a 100–120 word video script |

---

## Tech Stack

| Layer             | Technology                  |
|-------------------|-----------------------------|
| UI                | Streamlit                   |
| MCP Framework     | FastMCP (via `mcp` package) |
| Research          | Tavily Search API           |
| Script Generation | OpenAI GPT-4o-mini          |
| Video Generation  | D-ID API                    |
| Runtime           | Python 3.12 + uv            |
