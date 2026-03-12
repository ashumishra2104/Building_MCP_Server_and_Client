from mcp.server.fastmcp import FastMCP
from src.job_api import fetch_linkedin_jobs, fetch_naukri_jobs

mcp = FastMCP("Job Recommender MCP")

@mcp.tool()
def get_linkedin_jobs(search_query: str, location: str = "india", rows: int = 60):
    """Get job recommendations from Linkedin"""
    return fetch_linkedin_jobs(search_query, location, rows)

@mcp.tool()
def get_naukri_jobs(search_query: str, location: str = "india", rows: int = 60):
    """Get job recommendations from Naukri"""
    return fetch_naukri_jobs(search_query, location, rows)

if __name__ == "__main__":
    mcp.run()