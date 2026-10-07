import asyncio
import sys

# To demonstrate MCP client integration, we will import the fastmcp server
# and directly invoke the tool programmatically, bypassing HTTP.
# In a real environment, Claude Desktop or Cursor invokes this via stdio streams.
from docguard.mcp.server import query_docguard


async def main():
    print("\n" + "="*50)
    print("[+] DEMO G: MCP fastMCP Client Invocation")
    print("="*50)
    print("This script demonstrates invoking the `query_docguard` MCP tool locally.")
    print("Note: In production, Claude Desktop or Cursor communicates with this over stdio.")

    # Ensure dependencies like DB exist if running direct
    print("\nRunning MCP tool: query_docguard(query='When is the Project Alpha deadline?')")

    try:
        response = await query_docguard("When is the Project Alpha deadline?")
        print("\n--- MCP Tool Response ---")
        print(response)
        print("-------------------------")
    except Exception as e:
        print(f"\n[!] Failed to execute MCP tool: {e}")
        print("Make sure your PostgreSQL and Redis instances are running locally or via docker-compose.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
