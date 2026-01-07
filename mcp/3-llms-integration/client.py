import asyncio
import json
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

import nest_asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from google.genai import types

# Apply nest_asyncio to allow nested event loops (needed for Jupyter/IPython)
nest_asyncio.apply()

# Load environment variables
load_dotenv("../.env")


class MCPGeminiClient:
    """Client for interacting with Gemini models using MCP tools."""

    def __init__(self, model: str = "gemini-2.5-flash"):
        """Initialize the Gemini MCP client.

        Args:
            model: The Gemini model to use.
        """
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.gemini_client = genai.Client()
        self.model = model
        self.stdio: Optional[Any] = None
        self.write: Optional[Any] = None

    async def connect_to_server(self, server_script_path: str = "server.py"):
        """Connect to an MCP server.

        Args:
            server_script_path: Path to the server script.
        """
        # Server configuration
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
        )

        # Connect to the server
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        # Initialize the connection
        await self.session.initialize()

        # List available tools
        tools_result = await self.session.list_tools()
        print("\nConnected to server with tools:")
        for tool in tools_result.tools:
            print(f"  - {tool.name}: {tool.description}")

    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from the MCP server in Gemini format.

        Returns:
            A list of function declarations for Gemini.
        """
        tools_result = await self.session.list_tools()
        
        # Convert to Gemini function declarations format
        function_declarations = []
        for tool in tools_result.tools:
            func_decl = types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.inputSchema,
            )
            function_declarations.append(func_decl)
        
        return function_declarations

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available MCP tools.

        Args:
            query: The user query.

        Returns:
            The response from Gemini.
        """
        # Get available tools
        function_declarations = await self.get_mcp_tools()
        
        # Configure tools
        tools = types.Tool(function_declarations=function_declarations)
        config = types.GenerateContentConfig(tools=[tools])

        # Initial Gemini API call
        response = await self.gemini_client.aio.models.generate_content(
            model=self.model,
            contents=query,
            config=config,
        )

        # Check if there are function calls in the response
        if response.candidates and response.candidates[0].content.parts:
            function_calls = [
                part.function_call
                for part in response.candidates[0].content.parts
                if part.function_call
            ]

            if function_calls:
                # Process each function call
                function_responses = []
                
                for fc in function_calls:
                    # Execute tool call via MCP
                    result = await self.session.call_tool(
                        fc.name,
                        arguments=dict(fc.args),
                    )
                    
                    # Create function response
                    function_response = types.FunctionResponse(
                        name=fc.name,
                        response={"result": result.content[0].text}
                    )
                    function_responses.append(function_response)
                
                # Build the conversation history
                # Include the original query, the model's function call, and the function responses
                contents = [
                    types.Content(
                        role="user",
                        parts=[types.Part(text=query)]
                    ),
                    response.candidates[0].content,  # The function call from model
                    types.Content(
                        role="user",
                        parts=[types.Part(function_response=fr) for fr in function_responses]
                    )
                ]
                
                # Get final response from Gemini with function results
                final_response = await self.gemini_client.aio.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
                
                return final_response.text

        # No function calls, just return the direct response
        return response.text

    async def cleanup(self):
        """Clean up resources."""
        await self.exit_stack.aclose()


async def main():
    """Main entry point for the client."""
    client = MCPGeminiClient()
    await client.connect_to_server("server.py")

    # Example: Ask about company vacation policy
    query = "What is our company's vacation policy?"
    print(f"\nQuery: {query}")

    response = await client.process_query(query)
    print(f"\nResponse: {response}")

    # Cleanup
    await client.cleanup()
    

if __name__ == "__main__":
    asyncio.run(main())
