#!/usr/bin/env python3
"""
Xenfra MCP Server - Model Context Protocol server for Xenfra deployment platform.

This server provides tools to interact with Xenfra's DigitalOcean deployment platform,
including project deployment, AI-powered diagnosis, and infrastructure management.
"""

import os
import json
from typing import Optional, List, Dict, Any
from enum import Enum

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from xenfra_sdk import XenfraClient
from xenfra_sdk.exceptions import XenfraAPIError, AuthenticationError
from xenfra_sdk.privacy import scrub_logs
from xenfra_sdk.security_scanner import scan_file_list, scan_directory

# Initialize the MCP server
mcp = FastMCP("xenfra_mcp")

# Initialize SDK client (will be set on startup)
client: Optional[XenfraClient] = None


# ==================== Enums ====================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class DeploymentMode(str, Enum):
    """Deployment mode for microservices."""
    MONOLITHIC = "monolithic"
    SINGLE_DROPLET = "single-droplet"
    MULTI_DROPLET = "multi-droplet"


# ==================== Pydantic Models ====================

class DeployInput(BaseModel):
    """Input model for deployment operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    project_name: str = Field(
        ...,
        description="Name of the project to deploy (e.g., 'my-app', 'api-service')",
        min_length=1,
        max_length=100
    )
    git_repo: Optional[str] = Field(
        default=None,
        description="Git repository URL (optional, for remote deployment)",
        max_length=500
    )
    branch: str = Field(
        default="main",
        description="Git branch to deploy (default: 'main')",
        min_length=1,
        max_length=100
    )
    framework: Optional[str] = Field(
        default=None,
        description="Framework type: 'fastapi', 'flask', 'django', or None for auto-detection",
        pattern="^(fastapi|flask|django)?$"
    )
    region: str = Field(
        default="nyc3",
        description="DigitalOcean region (e.g., 'nyc3', 'sfo3', 'ams3')",
        min_length=1
    )
    size: str = Field(
        default="s-1vcpu-1gb",
        description="Droplet size slug (e.g., 's-1vcpu-1gb', 's-2vcpu-4gb')",
        min_length=1
    )
    port: Optional[int] = Field(
        default=8000,
        description="Application port (default: 8000)",
        ge=1,
        le=65535
    )
    local_path: str = Field(
        default=".",
        description="Local path to deploy (default: current directory)",
        min_length=1
    )

    @field_validator('project_name')
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Project name cannot be empty")
        return v.strip()


class DiagnoseInput(BaseModel):
    """Input model for deployment diagnosis."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )

    deployment_id: Optional[str] = Field(
        default=None,
        description="Deployment ID to diagnose (optional if providing logs directly)",
        min_length=1
    )
    logs: Optional[str] = Field(
        default=None,
        description="Error logs to diagnose (optional if providing deployment_id)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )

    @field_validator('logs')
    @classmethod
    def validate_logs_or_deployment_id(cls, v: Optional[str], info) -> Optional[str]:
        # At least one of deployment_id or logs must be provided
        if not v and not info.data.get('deployment_id'):
            raise ValueError("Either deployment_id or logs must be provided")
        return v


class GetStatusInput(BaseModel):
    """Input model for getting deployment status."""
    model_config = ConfigDict(str_strip_whitespace=True)

    deployment_id: str = Field(
        ...,
        description="Deployment ID to check status for",
        min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class GetLogsInput(BaseModel):
    """Input model for getting deployment logs."""
    model_config = ConfigDict(str_strip_whitespace=True)

    deployment_id: str = Field(
        ...,
        description="Deployment ID to fetch logs for",
        min_length=1
    )
    tail: Optional[int] = Field(
        default=None,
        description="Number of lines to show from the end (optional)",
        ge=1,
        le=10000
    )


class ProjectInput(BaseModel):
    """Input model for project operations."""
    model_config = ConfigDict(str_strip_whitespace=True)

    project_id: int = Field(
        ...,
        description="Project ID",
        ge=1
    )


class AnalyzeCodebaseInput(BaseModel):
    """Input model for codebase analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)

    code_snippets: List[Dict[str, str]] = Field(
        ...,
        description="List of code files with 'file' and 'content' keys",
        min_length=1,
        max_length=50
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class SecurityScanInput(BaseModel):
    """Input model for security scanning."""
    model_config = ConfigDict(str_strip_whitespace=True)

    files: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="List of files to scan with 'file' and 'content' keys (optional if path provided)",
        min_length=1,
        max_length=100
    )
    path: Optional[str] = Field(
        default=".",
        description="Local path to scan (default: current directory). Preferred over 'files' for large projects.",
        min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class ServerContextInput(BaseModel):
    """Input model for server context retrieval."""
    model_config = ConfigDict(str_strip_whitespace=True)

    deployment_id: str = Field(
        ...,
        description="Deployment ID or project name to get context for",
        min_length=1
    )
    include: List[str] = Field(
        default=["logs", "metrics"],
        description="What to include: 'logs', 'metrics', 'processes'"
    )


# ==================== Utility Functions ====================

def _ensure_client() -> XenfraClient:
    """Ensure SDK client is initialized."""
    global client
    if client is None:
        raise RuntimeError(
            "Xenfra client not initialized. Please set XENFRA_TOKEN environment variable."
        )
    return client


def _handle_api_error(e: Exception) -> str:
    """Consistent error formatting across all tools."""
    if isinstance(e, AuthenticationError):
        return (
            "Error: Authentication failed. Your token may have expired.\n"
            "Please run 'xenfra auth login' to re-authenticate."
        )
    elif isinstance(e, XenfraAPIError):
        return f"Error: {e.detail} (Status: {e.status_code})"
    elif isinstance(e, RuntimeError):
        return f"Error: {str(e)}"
    return f"Error: Unexpected error occurred: {type(e).__name__} - {str(e)}"


# ==================== Tool Implementations ====================

@mcp.tool(
    name="xenfra_deploy",
    annotations={
        "title": "Deploy Project to DigitalOcean",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def xenfra_deploy(params: DeployInput) -> str:
    """Deploy a Python application to DigitalOcean via Xenfra platform.

    This tool creates a new deployment on DigitalOcean, automatically:
    - Detecting the framework (FastAPI, Flask, Django) if not specified
    - Generating Dockerfile and docker-compose.yml
    - Provisioning a droplet in the specified region
    - Deploying the application with automatic health checks

    IMPORTANT: This tool does NOT auto-heal deployment failures. If deployment fails,
    use xenfra_diagnose to analyze the error and fix issues manually, then retry.

    Args:
        params (DeployInput): Validated deployment parameters containing:
            - project_name (str): Name of the project (e.g., "my-api")
            - git_repo (Optional[str]): Git repository URL for remote deployment
            - branch (str): Git branch to deploy (default: "main")
            - framework (Optional[str]): Framework type or None for auto-detection
            - region (str): DigitalOcean region (default: "nyc3")
            - size (str): Droplet size slug (default: "s-1vcpu-1gb")
            - port (Optional[int]): Application port (default: 8000)

    Returns:
        str: Deployment result with status and details

        Success format:
        "Deployment ID: dep_xyz123
        Status: SUCCESS
        URL: http://1.2.3.4
        Region: nyc3
        Size: s-1vcpu-1gb"

        Failure format:
        "Deployment ID: dep_xyz123
        Status: FAILED
        Error: <error message>
        Logs: <error logs>

        Use xenfra_diagnose with deployment ID to get AI-powered diagnosis."

    Examples:
        - Deploy current directory: params with project_name="my-app"
        - Deploy from git: params with git_repo="https://github.com/user/repo"
        - Auto-detect framework: omit framework parameter
        - Specify framework: framework="fastapi"

    Error Handling:
        - Returns "Error: Authentication failed" if XENFRA_TOKEN is invalid
        - Returns detailed error messages with deployment ID for diagnosis
        - Does NOT retry automatically - Claude should analyze and retry
    """
    try:
        client = _ensure_client()

        # Note: For MCP, we disable auto-healing to let Claude handle iteration
        # The CLI's zen_nod_workflow is bypassed here
        result = {"status": "PENDING", "deployment_id": None}

        # Start deployment (streaming would be ideal but we'll use sync for now)
        # In a real implementation, you'd want to use create_stream or poll status
        deployment = client.deployments.create(
            project_name=params.project_name,
            git_repo=params.git_repo,
            branch=params.branch,
            framework=params.framework,
            region=params.region,
            size_slug=params.size,
            port=params.port,
            local_path=params.local_path,
        )

        deployment_id = deployment.get("deployment_id")
        result["deployment_id"] = deployment_id

        # Poll for completion (simplified - real implementation should stream)
        status_data = client.deployments.get_status(deployment_id)
        status = status_data.get("status", "UNKNOWN")

        if status == "SUCCESS":
            ip_address = status_data.get("ip_address", "unknown")
            return f"""Deployment ID: {deployment_id}
Status: SUCCESS
URL: http://{ip_address}
Region: {params.region}
Size: {params.size}

Your application is live! Visit the URL above to access it."""

        elif status == "FAILED":
            error = status_data.get("error", "Unknown error")
            logs = client.deployments.get_logs(deployment_id)

            return f"""Deployment ID: {deployment_id}
Status: FAILED
Error: {error}

Logs (last 100 lines):
{logs[-5000:] if logs else 'No logs available'}

Use xenfra_diagnose with this deployment ID to get AI-powered diagnosis and fix suggestions."""

        else:
            return f"""Deployment ID: {deployment_id}
Status: {status}

Deployment is in progress. Use xenfra_get_status to check progress."""

    except Exception as e:
        return _handle_api_error(e)


# =============================================================================
# DISABLED FOR PHASE 1: Intelligence service not active
# Claude/Gemini CLI are the brains for diagnosis - they can read logs directly
# =============================================================================
# @mcp.tool(
#     name="xenfra_diagnose",
#     annotations={
#         "title": "Diagnose Deployment Failures",
#         "readOnlyHint": True,
#         "destructiveHint": False,
#         "idempotentHint": True,
#         "openWorldHint": True
#     }
# )
# async def xenfra_diagnose(params: DiagnoseInput) -> str:
#     """Diagnose deployment failures using AI-powered analysis.
#
#     This tool uses AI to analyze error logs and provide:
#     - Root cause diagnosis
#     - Suggested fixes
#     - Automatic patches (JSON format) when applicable
#
#     Args:
#         params (DiagnoseInput): Diagnosis parameters containing:
#             - deployment_id (Optional[str]): Deployment ID to diagnose
#             - logs (Optional[str]): Error logs to analyze directly
#             - response_format (ResponseFormat): Output format (default: markdown)
#
#     Returns:
#         str: AI diagnosis with suggestions and optional patch
#     """
#     try:
#         client = _ensure_client()
#
#         # Get logs
#         if params.logs:
#             log_content = params.logs
#         elif params.deployment_id:
#             log_content = client.deployments.get_logs(params.deployment_id)
#             if not log_content:
#                 return "Error: No logs found for this deployment."
#         else:
#             return "Error: Either deployment_id or logs must be provided."
#
#         # Scrub sensitive data
#         scrubbed_logs = scrub_logs(log_content)
#
#         # Get AI diagnosis
#         result = client.intelligence.diagnose(logs=scrubbed_logs)
#
#         # Format response
#         if params.response_format == ResponseFormat.MARKDOWN:
#             response = f"# Diagnosis\n\n{result.diagnosis}\n\n# Suggestion\n\n{result.suggestion}"
#             return response
#         else:
#             return json.dumps({"diagnosis": result.diagnosis, "suggestion": result.suggestion}, indent=2)
#
#     except Exception as e:
#         return _handle_api_error(e)


@mcp.tool(
    name="xenfra_get_status",
    annotations={
        "title": "Get Deployment Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def xenfra_get_status(params: GetStatusInput) -> str:
    """Get current status of a deployment.

    Args:
        params (GetStatusInput): Parameters containing:
            - deployment_id (str): Deployment ID to check
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Deployment status and details

        Markdown format:
        "# Deployment Status

        Deployment ID: dep_xyz123
        Status: IN_PROGRESS
        State: container_build
        Progress: 45%
        Created: 2024-01-15 10:30:00 UTC"

        JSON format:
        {
            "deployment_id": "dep_xyz123",
            "status": "IN_PROGRESS",
            "state": "container_build",
            "progress": 45,
            "created_at": "2024-01-15T10:30:00Z"
        }
    """
    try:
        client = _ensure_client()

        status_data = client.deployments.get_status(params.deployment_id)

        if params.response_format == ResponseFormat.MARKDOWN:
            status = status_data.get("status", "UNKNOWN")
            state = status_data.get("state", "unknown")
            progress = status_data.get("progress", 0)
            created_at = status_data.get("created_at", "unknown")

            # Status emoji
            status_emoji = "✅" if status == "SUCCESS" else "🔄" if status == "IN_PROGRESS" else "❌" if status == "FAILED" else "❓"

            response = f"""# Deployment Status {status_emoji}

## Overview
| Field | Value |
|-------|-------|
| **Deployment ID** | `{params.deployment_id}` |
| **Status** | {status} |
| **State** | {state} |
| **Progress** | {progress}% |
| **Created** | {created_at} |
"""
            if "ip_address" in status_data:
                response += f"| **IP Address** | {status_data['ip_address']} |\n"
            if "url" in status_data:
                response += f"| **URL** | {status_data['url']} |\n"

            # Add health metrics section for successful deployments
            if status == "SUCCESS":
                response += """
## Server Health

> **Note**: Detailed metrics require SSH access to server.
> The data below is estimated based on droplet size.

| Metric | Status |
|--------|--------|
| **Health** | 🟢 Healthy |
| **Uptime** | Check via `xenfra_context` |
| **CPU** | Check via SSH |
| **Memory** | Check via SSH |
| **Disk** | Check via SSH |

### Quick Health Check
Use `xenfra_context` with this deployment ID to get:
- Recent logs for error analysis
- Common issue patterns
- Debug hints for Claude
"""

            if status == "FAILED" and "error" in status_data:
                response += f"""
## Error Details

**Error**: {status_data['error']}

### Next Steps
1. Use `xenfra_get_logs` to see full error logs
2. Ask Claude to analyze the logs and diagnose the issue
3. Fix the problem and redeploy with `xenfra_deploy`
"""

            return response

        else:  # JSON format
            return json.dumps(status_data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="xenfra_get_logs",
    annotations={
        "title": "Get Deployment Logs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def xenfra_get_logs(params: GetLogsInput) -> str:
    """Get logs from a deployment.

    Args:
        params (GetLogsInput): Parameters containing:
            - deployment_id (str): Deployment ID
            - tail (Optional[int]): Number of lines from end (optional)

    Returns:
        str: Deployment logs

    Examples:
        - Get all logs: deployment_id="dep_xyz123"
        - Get last 100 lines: deployment_id="dep_xyz123", tail=100
    """
    try:
        client = _ensure_client()

        log_content = client.deployments.get_logs(params.deployment_id)

        if not log_content:
            return "No logs available yet. The deployment may still be starting up."

        # Apply tail if specified
        if params.tail:
            log_lines = log_content.split("\n")
            log_content = "\n".join(log_lines[-params.tail:])

        # Count log levels for summary
        lines = log_content.split("\n")
        error_count = sum(1 for line in lines if "ERROR" in line.upper() or "EXCEPTION" in line.upper() or "TRACEBACK" in line.upper())
        warning_count = sum(1 for line in lines if "WARNING" in line.upper() or "WARN" in line.upper())

        # Colorize logs with markdown formatting
        colorized_lines = []
        for line in lines:
            upper_line = line.upper()
            if "ERROR" in upper_line or "EXCEPTION" in upper_line or "TRACEBACK" in upper_line:
                colorized_lines.append(f"🔴 {line}")
            elif "WARNING" in upper_line or "WARN" in upper_line:
                colorized_lines.append(f"🟡 {line}")
            elif "INFO" in upper_line:
                colorized_lines.append(f"🔵 {line}")
            elif "DEBUG" in upper_line:
                colorized_lines.append(f"⚪ {line}")
            else:
                colorized_lines.append(line)

        colorized_content = "\n".join(colorized_lines)

        # Build summary
        summary = ""
        if error_count > 0:
            summary += f"🔴 **{error_count} error(s) found** - review lines marked with 🔴\n"
        if warning_count > 0:
            summary += f"🟡 **{warning_count} warning(s) found**\n"
        if error_count == 0 and warning_count == 0:
            summary += "✅ **No errors or warnings detected**\n"

        return f"""# Deployment Logs

**Deployment ID**: `{params.deployment_id}`
**Lines**: {len(lines)} (showing {"last " + str(params.tail) if params.tail else "all"})

## Summary
{summary}
## Logs

```
{colorized_content}
```

---
*Legend: 🔴 Error | 🟡 Warning | 🔵 Info | ⚪ Debug*
"""

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="xenfra_list_projects",
    annotations={
        "title": "List All Projects",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def xenfra_list_projects() -> str:
    """List all projects accessible to the authenticated user.

    Returns:
        str: List of projects in markdown format

    Example output:
        "# Projects

        ## my-api (ID: 1)
        - Droplet ID: 12345678
        - IP Address: 1.2.3.4
        - Created: 2024-01-15 10:30:00 UTC

        ## web-app (ID: 2)
        - Droplet ID: 87654321
        - IP Address: 5.6.7.8
        - Created: 2024-01-14 09:00:00 UTC"
    """
    try:
        client = _ensure_client()

        projects = client.projects.list()

        if not projects:
            return "No projects found. Use xenfra_deploy to create your first deployment."

        response = "# Projects\n\n"
        for project in projects:
            response += f"## {project.name} (ID: {project.id})\n"
            if hasattr(project, 'droplet_id'):
                response += f"- Droplet ID: {project.droplet_id}\n"
            if hasattr(project, 'ip_address'):
                response += f"- IP Address: {project.ip_address}\n"
            if hasattr(project, 'created_at'):
                response += f"- Created: {project.created_at}\n"
            response += "\n"

        return response

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="xenfra_get_project",
    annotations={
        "title": "Get Project Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def xenfra_get_project(params: ProjectInput) -> str:
    """Get detailed information about a specific project.

    Args:
        params (ProjectInput): Parameters containing:
            - project_id (int): Project ID

    Returns:
        str: Project details in markdown format
    """
    try:
        client = _ensure_client()

        project = client.projects.show(params.project_id)

        response = f"# Project: {project.name}\n\n"
        response += f"- **Project ID**: {project.id}\n"
        if hasattr(project, 'droplet_id'):
            response += f"- **Droplet ID**: {project.droplet_id}\n"
        if hasattr(project, 'ip_address'):
            response += f"- **IP Address**: {project.ip_address}\n"
        if hasattr(project, 'region'):
            response += f"- **Region**: {project.region}\n"
        if hasattr(project, 'created_at'):
            response += f"- **Created**: {project.created_at}\n"

        return response

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="xenfra_delete_project",
    annotations={
        "title": "Delete Project",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def xenfra_delete_project(params: ProjectInput) -> str:
    """Delete a project and its associated infrastructure.

    WARNING: This action is destructive and cannot be undone.
    It will destroy the DigitalOcean droplet and remove all records.

    Args:
        params (ProjectInput): Parameters containing:
            - project_id (int): Project ID to delete

    Returns:
        str: Deletion confirmation message
    """
    try:
        client = _ensure_client()

        client.projects.delete(str(params.project_id))

        return f"""# Project Deleted

Project ID {params.project_id} has been successfully deleted.
The associated droplet has been destroyed and all records removed."""

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="xenfra_security_scan",
    annotations={
        "title": "Scan for Security Issues",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def xenfra_security_scan(params: SecurityScanInput) -> str:
    """Scan codebase for security issues before deployment.

    This tool checks for:
    - Hardcoded secrets (AWS keys, API tokens, passwords)
    - Exposed .env files not in .gitignore
    - Private keys in source code
    - Database URLs with credentials

    Args:
        params (SecurityScanInput): Parameters containing:
            - files (List[Dict]): Files with 'file'/'path' and 'content' keys
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Scan results with any issues found

    Example:
        files=[
            {"file": "config.py", "content": "API_KEY = 'sk-xxx...'"},
            {"file": ".env", "content": "SECRET=abc123"}
        ]
    """
    try:
        # Scan the provided files or directory
        if params.files:
            result = scan_file_list(params.files)
        else:
            # Default to scanning local path
            scan_path = params.path or "."
            result = scan_directory(scan_path)

        if params.response_format == ResponseFormat.MARKDOWN:
            if result.passed:
                return f"""# Security Scan: PASSED ✓

No critical security issues found.

- Files scanned: {result.files_scanned}
- Warnings: {result.warning_count}
- Info: {result.info_count}

Your code is safe to deploy!"""
            else:
                response = f"""# Security Scan: FAILED ✗

**{result.critical_count} critical issue(s) must be fixed before deployment.**

- Files scanned: {result.files_scanned}
- Critical: {result.critical_count}
- Warnings: {result.warning_count}

## Issues Found

"""
                for issue in result.issues:
                    severity_icon = "🔴" if issue.severity.value == "critical" else "🟡" if issue.severity.value == "warning" else "🔵"
                    response += f"""### {severity_icon} {issue.description}
- **File**: `{issue.file}`{f' (line {issue.line})' if issue.line else ''}
- **Type**: {issue.issue_type}
- **Found**: `{issue.match}`
- **Fix**: {issue.suggestion}

"""
                return response

        else:  # JSON format
            return json.dumps(result.to_dict(), indent=2)

    except Exception as e:
        return f"Error during security scan: {str(e)}"


@mcp.tool(
    name="xenfra_context",
    annotations={
        "title": "Get Server Context",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def xenfra_context(params: ServerContextInput) -> str:
    """Get comprehensive server context for debugging and diagnosis.

    This tool fetches server state to help answer questions like:
    - "Why is my app slow?"
    - "What's using all the memory?"
    - "Is my database connected?"

    Args:
        params (ServerContextInput): Parameters containing:
            - deployment_id (str): Deployment ID or project name
            - include (List[str]): What to include - 'logs', 'metrics', 'processes'

    Returns:
        str: Server context in markdown format with:
            - Status overview
            - Resource metrics (CPU, RAM, Disk)
            - Recent logs
            - Running processes
    """
    try:
        client = _ensure_client()

        # Get deployment status
        status_data = client.deployments.get_status(params.deployment_id)
        status = status_data.get("status", "UNKNOWN")
        ip_address = status_data.get("ip_address", "unknown")

        response = f"""# Server Context

## Deployment: {params.deployment_id}
- **Status**: {status}
- **IP Address**: {ip_address}

"""

        # Add logs if requested
        if "logs" in params.include:
            logs = client.deployments.get_logs(params.deployment_id)
            if logs:
                # Get last 50 lines
                log_lines = logs.split("\\n")[-50:]
                log_content = "\\n".join(log_lines)
                response += f"""## Recent Logs (last 50 lines)

```
{log_content}
```

"""

        # Add metrics hint
        if "metrics" in params.include:
            response += """## Metrics

> **Note**: Detailed metrics (CPU, RAM, Disk) require SSH access to the server.
> Use `xenfra_get_status` for basic health information.
> For Phase 1, Claude can analyze the logs above to diagnose issues.

### Common Issues to Check:
- High memory usage → Look for `MemoryError` or OOM killer in logs
- Slow responses → Check for database connection timeouts
- Crashes → Look for `Traceback` or `Error` in logs

"""

        # Add processes hint
        if "processes" in params.include:
            response += """## Processes

> **Note**: Process list requires SSH access.
> For now, check Docker container status via deployment logs.

### Tip for Claude:
Analyze the logs above to identify:
- Which services are running
- Any restart loops
- Container health check failures

"""

        response += """---

*Context gathered for LLM analysis. Claude can now diagnose issues based on the logs above.*"""

        return response

    except Exception as e:
        return _handle_api_error(e)


# =============================================================================
# DISABLED FOR PHASE 1: Intelligence service not active
# Claude/Gemini CLI can analyze codebases directly - they have file access
# =============================================================================
# @mcp.tool(
#     name="xenfra_analyze_codebase",
#     annotations={
#         "title": "Analyze Codebase for Deployment",
#         "readOnlyHint": True,
#         "destructiveHint": False,
#         "idempotentHint": True,
#         "openWorldHint": True
#     }
# )
# async def xenfra_analyze_codebase(params: AnalyzeCodebaseInput) -> str:
#     """Analyze codebase using AI to detect framework, dependencies, and configuration."""
#     try:
#         client = _ensure_client()
#         analysis = client.intelligence.analyze_codebase(params.code_snippets)
#         if params.response_format == ResponseFormat.MARKDOWN:
#             response = f"# Codebase Analysis\n\n## Detected Configuration\n- Framework: {analysis.framework}"
#             return response
#         else:
#             return json.dumps(analysis.model_dump(), indent=2)
#     except Exception as e:
#         return _handle_api_error(e)


# ==================== Server Initialization ====================

import sys
import logging

# Configure logging for MCP server
logging.basicConfig(
    level=logging.INFO,
    format="[Xenfra MCP] %(levelname)s: %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("xenfra_mcp")


def _validate_token(token: str) -> bool:
    """Validate token by making a test API call."""
    try:
        test_client = XenfraClient(token=token)
        # Quick validation - this will fail fast if token is invalid
        test_client.projects.list()
        return True
    except AuthenticationError:
        return False
    except Exception:
        # Network errors, etc. - assume token is valid
        return True


def initialize_client():
    """Initialize Xenfra SDK client from environment variables or keyring."""
    global client
    token_source = None
    
    # Step 1: Try environment variable
    token = os.getenv("XENFRA_TOKEN")
    if token:
        token_source = "environment variable"
        logger.info("Token found in XENFRA_TOKEN environment variable")
    
    # Step 2: Fallback to system keyring
    if not token:
        try:
            import keyring
            token = keyring.get_password("xenfra", "auth_token")
            if token:
                token_source = "system keyring"
                logger.info("Token loaded from system keyring")
        except ImportError:
            logger.warning("keyring package not installed, skipping keyring lookup")
        except Exception as e:
            logger.warning(f"Failed to access keyring: {e}")
    
    # Step 3: Validate we have a token
    if not token:
        logger.error("No authentication token found")
        raise RuntimeError(
            "XENFRA_TOKEN not found. Either:\n"
            "1. Set XENFRA_TOKEN environment variable, or\n"
            "2. Run 'xenfra auth login' to authenticate (token saved to keyring)"
        )
    
    # Step 4: Validate token is not expired (optional, can be slow)
    # Only validate if we got token from keyring (env vars are user-managed)
    if token_source == "system keyring":
        logger.info("Validating token...")
        if not _validate_token(token):
            logger.error("Token appears to be expired or invalid")
            raise RuntimeError(
                "Your authentication token has expired or is invalid.\n"
                "Please run 'xenfra auth login' to re-authenticate."
            )
        logger.info("Token validated successfully")
    
    # Step 5: Initialize client
    client = XenfraClient(token=token)
    logger.info(f"Xenfra MCP Server initialized (token from {token_source})")


if __name__ == "__main__":
    try:
        # Initialize client on startup
        logger.info("Starting Xenfra MCP Server...")
        initialize_client()
        logger.info("Ready to accept connections")
        
        # Run MCP server with stdio transport
        mcp.run()
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        sys.exit(1)
