from mcp.server.fastmcp import FastMCP
from tools.weather import get_weather
from typing import Dict,Any

mcp = FastMCP("Weather Checker")

@mcp.tool()
async def check_weather(location:str) -> str:
    """Fetches the weather for a given location."""
    return get_weather(location)

if __name__ == "__main__":
    mcp.run(transport="stdio")
