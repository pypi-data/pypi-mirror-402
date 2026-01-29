"""
Xenfra MCP Server - Model Context Protocol server for Xenfra deployment platform.

This package provides MCP tools for deploying Python applications to DigitalOcean
with AI-powered diagnosis and infrastructure management.

Tools provided:
- xenfra_deploy: Deploy projects to DigitalOcean
- xenfra_diagnose: AI-powered failure diagnosis
- xenfra_get_status: Get deployment status
- xenfra_get_logs: Get deployment logs
- xenfra_list_projects: List all projects
- xenfra_get_project: Get project details
- xenfra_delete_project: Delete a project
- xenfra_analyze_codebase: AI codebase analysis

Configuration:
    Set XENFRA_TOKEN environment variable with your Xenfra API token.
    Get a token by running: xenfra auth login

Usage:
    # In claude_desktop_config.json or ~/.config/claude/config.json:
    {
        "mcpServers": {
            "xenfra": {
                "command": "python",
                "args": ["-m", "xenfra_mcp_server"],
                "env": {
                    "XENFRA_TOKEN": "your-token-here"
                }
            }
        }
    }
"""

__version__ = "0.2.0"

from .server import mcp

__all__ = ["mcp"]
