# Job Recommender & MCP Server

An AI-powered Job Recommendation platform and Model Context Protocol (MCP) server that analyzes a user's resume, suggests necessary skill improvements, and automatically fetches relevant real-time job listings from LinkedIn and Naukri using Apify.

## Features

- **Resume Analysis**: Upload a PDF resume to get an AI-generated summary.
- **Skill Gap Detection**: AI identifies missing skills and certifications based on current industry standards.
- **Future Roadmap**: Get an actionable roadmap to level up your career.
- **Live Job Search**: Automatically extracts search keywords from your resume to fetch actual job listings from LinkedIn and Naukri.
- **MCP Server**: Exposes job search functions (`get_linkedin_jobs` and `get_naukri_jobs`) to compatible AI clients (like Claude Desktop) through the Model Context Protocol (MCP).

## Architecture

- **Frontend**: Streamlit (`app.py`) for the web interface.
- **AI Processing**: OpenAI (`gpt-4o-mini`) is used for text summarization, skill gap analysis, and keyword extraction.
- **Scraping**: Apify Actors are used to dynamically scrape job listings from LinkedIn and Naukri.
- **MCP Backend**: FastMCP (`mcp_server.py`) powers the MCP integration.

## Installation & Setup

1. **Clone the repository** (or navigate to this folder).
2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**: Allow the app to authenticate to API services by creating a `.env` file in the root of the project with your API keys:

   ```env
   OPENAI_API_KEY=your_openai_api_key
   APIFY_API_TOKEN=your_apify_api_token
   ```

## Usage

### Run the Web Interface (Streamlit)

Start the Streamlit web application:

```bash
streamlit run app.py
```

### Run the MCP Server

To start the Model Context Protocol (MCP) server so that AI clients can use your job search capabilities:

```bash
npx -y @modelcontextprotocol/inspector ./venv/bin/python mcp_server.py
```

## Disclaimer

Note: Ensure your Apify and OpenAI accounts have sufficient credits or a valid billing tier, as scraping and LLM generation consumes API credits.
