# Xenfra MCP Server (The Bridge) 🧠

[![PyPI](https://img.shields.io/pypi/v/xenfra-mcp-server)](https://pypi.org/project/xenfra-mcp-server/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **Model Context Protocol (MCP)** server that empowers AI agents (Claude Desktop, Cursor, Windsurf) to securely deploy, monitor, and debug infrastructure on Xenfra.

**Philosophy: Tools as Skills.** We expose atomic, reliable infrastructure capabilities that LLMs can orchestrate.

## 🤖 Available Tools

| Tool                   | Description                                                |
| :--------------------- | :--------------------------------------------------------- |
| `xenfra_deploy`        | Deploys the project in the current working directory.      |
| `xenfra_get_logs`      | Fetches filtered, colorized logs for a deployment.         |
| `xenfra_get_status`    | Retrieves real-time health metrics (CPU, RAM, Uptime).     |
| `xenfra_security_scan` | Scans codebase for 15+ types of secrets before deployment. |
| `xenfra_list_projects` | Lists all active deployments and their IDs.                |
| `xenfra_context`       | Dumps environment summary for "Why is it broken?" queries. |

## 📦 Installation & Configuration

### For Claude Desktop

1.  Make sure you have `uv` installed.
2.  Edit your config file:

    - **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
    - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

3.  Add Xenfra:

```json
{
  "mcpServers": {
    "xenfra": {
      "command": "uvx",
      "args": ["xenfra-mcp-server"]
    }
  }
}
```

4.  Restart Claude Desktop. Look for the 🔌 icon.

### For Custom Agents

You can run the server directly via stdio:

```bash
uvx xenfra-mcp-server
```

## 🛠️ Usage Example

**User**: "Deploy this app and check if it's healthy."

**Agent (Using Xenfra MCP)**:

1.  Calls `xenfra_security_scan` -> "No secrets found."
2.  Calls `xenfra_deploy` -> "Deployment started, ID: dep_123."
3.  Calls `xenfra_get_status` -> "Status: 🟢 Running."

## 🔗 The Xenfra Ecosystem

This MCP Server is the "Brain Connector" of the Xenfra Open Core architecture:

- **[xenfra-sdk](https://github.com/xenfracloud/xenfra-sdk)**: The Core Engine (Used by this Server).
- **[xenfra-cli](https://github.com/xenfracloud/xenfra-cli)**: The Terminal Interface.
- **xenfra-platform**: The Private SaaS Backend.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MIT © [Xenfra Cloud](https://xenfra.tech)
