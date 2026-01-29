import datetime

print(f"{datetime.datetime.now()} Starting mcp verification...", flush=True)

try:
    print(f"{datetime.datetime.now()} Importing mcp.server.fastmcp...", flush=True)
    from mcp.server.fastmcp import FastMCP
    print(f"{datetime.datetime.now()} mcp.server.fastmcp imported.", flush=True)
except Exception as e:
    print(f"Error: {e}", flush=True)

print(f"{datetime.datetime.now()} Done.", flush=True)
