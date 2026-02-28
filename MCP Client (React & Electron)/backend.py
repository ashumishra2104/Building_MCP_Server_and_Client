import os
import asyncio
import json
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import existing logic from client
from client import MCPClient

app = FastAPI(title="MCP Web Client Interface")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for the MCP Client
state = {
    "client": None,
    "connected": False,
    "tools": [],
    "server_path": ""
}

class ConnectRequest(BaseModel):
    server_path: str

class QueryRequest(BaseModel):
    query: str

class ChatMessage(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[Dict]] = None

chat_history: List[ChatMessage] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    yield
    # Cleanup
    if state["client"]:
        await state["client"].exit_stack.aclose()

@app.post("/connect")
async def connect(request: ConnectRequest):
    try:
        if state["client"]:
            await state["client"].exit_stack.aclose()
        
        client = MCPClient()
        await client.connect_to_server(request.server_path)
        
        state["client"] = client
        state["connected"] = True
        state["server_path"] = request.server_path
        
        # Get tool names
        response = await client.session.list_tools()
        state["tools"] = [tool.name for tool in response.tools]
        
        return {"status": "connected", "tools": state["tools"]}
    except Exception as e:
        state["connected"] = False
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def process_query(request: QueryRequest):
    if not state["client"] or not state["connected"]:
        raise HTTPException(status_code=400, detail="Client not connected to any server.")
    
    try:
        # We'll wrap the client's process_query to capture tool calls for the UI
        # For simplicity, we'll use the existing process_query and maybe enhance it later
        response_text = await state["client"].process_query(request.query)
        
        msg = ChatMessage(role="assistant", content=response_text)
        chat_history.append(ChatMessage(role="user", content=request.query))
        chat_history.append(msg)
        
        return msg
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    return {
        "connected": state["connected"],
        "server_path": state["server_path"],
        "tools": state["tools"]
    }

@app.get("/history")
async def get_history():
    return chat_history

# Serve the React build — must come AFTER API routes
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
