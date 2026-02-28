# Import necessary libraries
import asyncio  # For handling asynchronous operations
import os       # For environment variable access
import sys      # For system-specific parameters and functions
import json     # For handling JSON data (used when printing function declarations)

# Import MCP client components
from typing import Optional  # For type hinting optional values
from contextlib import AsyncExitStack  # For managing multiple async tasks
from mcp import ClientSession, StdioServerParameters  # MCP session management
from mcp.client.stdio import stdio_client  # MCP client for standard I/O communication

# Import Google's Gen AI SDK
from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration, GenerateContentConfig

from dotenv import load_dotenv  # For loading API keys from a .env file

# Load environment variables from .env file
load_dotenv()

def convert_mcp_tools_to_gemini(tools):
    """
    Convert MCP tool definitions to Gemini function declarations.
    """
    function_declarations = []
    for tool in tools:
        # Map the MCP tool schema to Gemini function declaration
        # Gemini expects 'parameters' as a schema object
        declaration = FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters=tool.inputSchema
        )
        function_declarations.append(declaration)
    return function_declarations

class MCPClient:
    def __init__(self):
        """Initialize the MCP client and configure the Gemini API."""
        self.session: Optional[ClientSession] = None # MCP session for communication
        self.exit_stack = AsyncExitStack() # Manages async resource cleanup
        
        # Retrieve the Gemini API key from environment variables
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found. Please add it to your .env file.")
            
        # Configure the Gemini AI client
        self.genai_client = genai.Client(api_key=gemini_api_key)

    async def connect_to_server(self, server_script_path: str):
        """Connect to the MCP server and list available tools."""
        
        # Determine whether the server script is written in Python or JavaScript
        # This allows us to execute the correct command to start the MCP server
        command = "python" if server_script_path.endswith('.py') else "node"
        
        # Define the parameters for connecting to the MCP server
        server_params = StdioServerParameters(command=command, args=[server_script_path])
        
        # Establish communication with the MCP server using standard input/output (stdio)
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        
        # Initialize the MCP client session, which allows interaction with the server
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        # Send an initialization request to the MCP server
        await self.session.initialize()
        
        # Request the list of available tools from the MCP server
        response = await self.session.list_tools()
        tools = response.tools  # Extract the tool list from the response
        
        # Print a message showing the names of the tools available on the server
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        
        # Convert MCP tools to Gemini format
        self.function_declarations = convert_mcp_tools_to_gemini(tools)

    async def process_query(self, query: str) -> str:
        """
        Process a user query using the Gemini API and execute tool calls if needed.
        
        Args:
            query: The user's query string.
        """
        # Create a tool definition that includes our function declarations
        tools = [Tool(function_declarations=self.function_declarations)]
        
        # Initialize a chat session with the model that includes our tools
        chat = self.genai_client.chats.create(
            model="gemini-2.5-flash",
            config=GenerateContentConfig(tools=tools)
        )
        
        # Send the user query to Gemini
        response = chat.send_message(query)
        
        # Handle the function calling loop
        # As long as the model wants to call a function, we execute it and return the result
        while response.candidates[0].content.parts[0].function_call:
            # Extract function call details
            call = response.candidates[0].content.parts[0].function_call
            tool_name = call.name
            tool_args = call.args
            
            print(f"\n[Tool Call] Executing: {tool_name} with arguments: {json.dumps(tool_args)}")
            
            # Execute the actual tool call via the MCP session
            result = await self.session.call_tool(tool_name, arguments=tool_args)
            
            # Extract the text content from the MCP tool result
            tool_output = result.content[0].text
            print(f"[Tool Result] {tool_output[:100]}...")
            
            # Send the tool output back to Gemini to continue the conversation
            response = chat.send_message(
                types.Part.from_function_response(
                    name=tool_name,
                    response={"result": tool_output}
                )
            )
            
        # Return the final text response from the model
        return response.text

async def chat_loop(client: MCPClient):
    """Simple command-line interface for chatting with the MCP-enabled Gemini."""
    print("\nMCP Client Started!")
    print("Type 'quit', 'exit', or 'q' to stop.")
    
    while True:
        try:
            query = input("\n> ").strip()
            
            if not query:
                continue
                
            if query.lower() in ["quit", "exit", "q"]:
                break
                
            response = await client.process_query(query)
            print(f"\nGemini: {response}")
            
        except Exception as e:
            print(f"\nError: {str(e)}")

async def main():
    """Main entry point for the client application."""
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    server_path = sys.argv[1]
    client = MCPClient()
    
    try:
        # Connect to the specified MCP server
        await client.connect_to_server(server_path)
        
        # Start the interactive chat loop
        await chat_loop(client)
        
    finally:
        # Ensure all resources are properly cleaned up
        await client.exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())
