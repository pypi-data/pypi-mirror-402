"""
Entry point for running Xenfra MCP Server.

Usage:
    python -m xenfra_mcp_server
"""

import sys
import os

# Ensure XENFRA_TOKEN is set
if not os.getenv("XENFRA_TOKEN"):
    print("Error: XENFRA_TOKEN environment variable is required.", file=sys.stderr)
    print("Get your token by running: xenfra auth login", file=sys.stderr)
    sys.exit(1)

# Import and run the server
from .server import mcp, initialize_client

if __name__ == "__main__":
    # Initialize client
    initialize_client()

    # Run MCP server with stdio transport
    mcp.run()
