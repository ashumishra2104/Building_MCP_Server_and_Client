# Weather MCP Server 🌦️

A high-performance Model Context Protocol (MCP) server built with Python that provides real-time weather data for any location globally. This server uses the **Open-Meteo API** (reliable, no API key required) to fetch live conditions, temperatures, and wind speeds.

## 🚀 Features
- **Global Coverage**: Get weather for any city or coordinate.
- **Zero Configuration**: Uses Open-Meteo, so no API keys are needed to start.
- **FastMCP**: Built using the modern FastMCP framework for speed and type safety.
- **Claude Integration**: Ready to be plugged directly into Claude Desktop.

## 📁 Structure
- `main.py`: The entry point for the MCP server.
- `tools/weather.py`: Core logic for fetching and processing weather data.
- `.venv_final/`: Pre-configured Python virtual environment.
- `pyproject.toml`: Project metadata and dependencies.

## 🛠️ Installation for Claude Desktop

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ashumishra2104/Building_MCP_Server_and_Client.git
   cd Building_MCP_Server_and_Client
   ```

2. **Configure Claude**:
   Open your Claude Desktop configuration file:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

3. **Add the Server**:
   Add the following entry to the `mcpServers` object:
   ```json
   {
     "mcpServers": {
       "weather": {
         "command": "C:\\path\\to\\your\\project\\.venv_final\\Scripts\\python.exe",
         "args": ["C:\\path\\to\\your\\project\\main.py"]
       }
     }
   }
   ```
   *(Note: Replace `C:\\path\\to\\your\\project\\` with the actual absolute path to your folder.)*

4. **Restart Claude**: Fully quit and relaunch the Claude Desktop app.

## 🧪 Testing Locally
You can test the weather logic directly without running the full MCP server:
```powershell
.\.venv_final\Scripts\python -c "from tools.weather import get_weather; print(get_weather('New Delhi'))"
```

## 📜 License
MIT
