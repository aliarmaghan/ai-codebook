from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv


load_dotenv()


# create a MCP server
mcp = FastMCP(
    name ="calculator",
    host="0.0.0.0",  # Only used for SSE transport(localhost)
    port=8050,   # only used for SSE transport(set this to any port)
    stateless_http=True,  # Enable stateless HTTP transport

)

# Add a simple calculator tool
@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b


# Start the server
if __name__ == "__main__":
    transport = "streamable-http"  # Change to "sse" or "streamable-http" as needed
    if transport == "stdio":
        print("Running server with stdio transport")
        mcp.run(transport="stdio")
    elif transport == "sse":
        print("Running server with SSE transport")
        mcp.run(transport="sse")
    elif transport == "streamable-http":
        print("Running server with Streamable HTTP transport")
        mcp.run(transport="streamable-http")
    else:
        raise ValueError(f"Unknown transport: {transport}")