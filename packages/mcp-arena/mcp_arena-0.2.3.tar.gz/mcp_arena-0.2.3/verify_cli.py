import sys
import os
import time

print("Starting verification...", flush=True)

try:
    print("Importing typer...", flush=True)
    import typer
    print("Importing rich...", flush=True)
    import rich
    print("Dependencies imported.", flush=True)
except ImportError as e:
    print(f"Missing dependency: {e}", flush=True)
    sys.exit(1)

# Add current directory to path
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"sys.path: {sys.path}", flush=True)

print("Attempting to import mcp_arena...", flush=True)
try:
    import mcp_arena
    print(f"mcp_arena imported: {mcp_arena}", flush=True)
except Exception as e:
    print(f"Error importing mcp_arena: {e}", flush=True)

print("Attempting to import mcp_arena.cli...", flush=True)
try:
    from mcp_arena import cli
    print(f"mcp_arena.cli imported: {cli}", flush=True)
except Exception as e:
    print(f"Error importing mcp_arena.cli: {e}", flush=True)

print("Testing _get_available_presets...", flush=True)
try:
    presets = cli._get_available_presets()
    print(f"Presets found: {presets}", flush=True)
except Exception as e:
    print(f"Error getting presets: {e}", flush=True)

print("Verification complete.", flush=True)
