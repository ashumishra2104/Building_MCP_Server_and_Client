from mcp.server.fastmcp import FastMCP
import logic

# Simplified MCP Server
mcp = FastMCP("StoryForge")

@mcp.tool()
def search_insights(query: str):
    """Get real-time research and insights on a topic."""
    return logic.get_realtime_info(query)

@mcp.tool()
def write_script(topic: str):
    """Generate a high-engagement short video script."""
    info = logic.get_realtime_info(topic)
    return logic.generate_video_script(topic, info)

if __name__ == "__main__":
    mcp.run()
