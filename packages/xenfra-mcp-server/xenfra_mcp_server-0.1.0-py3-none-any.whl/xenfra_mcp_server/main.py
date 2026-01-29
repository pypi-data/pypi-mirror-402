import inspect
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from xenfra_sdk import XenfraClient
from xenfra_sdk.exceptions import AuthenticationError, XenfraAPIError

# --- FastAPI App Setup ---
app = FastAPI(
    title="Xenfra Model Context Protocol (MCP) Server",
    description="Exposes Xenfra SDK methods as OpenAI-compatible function-calling tools.",
    version="0.1.0",
)


# --- Xenfra Client Dependency ---
def get_xenfra_client() -> XenfraClient:
    """
    Dependency to provide an authenticated XenfraClient instance.
    The MCP server must be configured with a XENFRA_TOKEN.
    """
    try:
        # Client will automatically pick up XENFRA_TOKEN from environment
        return XenfraClient()
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Xenfra SDK Authentication Error: {e}"
        )


# --- Tool Schema Generation Logic ---
class ToolParameter(BaseModel):
    type: str = "object"
    properties: Dict[str, Any]
    required: List[str]


class FunctionTool(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: ToolParameter


class ToolDefinition(BaseModel):
    type: str = "function"
    function: FunctionTool


class ToolExecutionRequest(BaseModel):
    tool_name: str = Field(
        ..., description="The name of the tool to execute, e.g., 'xenfra_list_projects'"
    )
    tool_arguments: Dict[str, Any] = Field(
        ..., description="A dictionary of arguments for the tool."
    )


def generate_tool_schema(
    sdk_method: Callable, method_name: str, description: str
) -> ToolDefinition:
    """
    Generates an OpenAI-compatible tool schema from an SDK method.
    Assumes SDK methods use Pydantic models for request/response.
    """
    # Inspect the method's signature to find its parameters
    sig = inspect.signature(sdk_method)
    parameters_schema = {"type": "object", "properties": {}, "required": []}

    for name, param in sig.parameters.items():
        if name == "self":  # Skip 'self' parameter
            continue

        # If the parameter has a Pydantic model as its type annotation
        if hasattr(param.annotation, "model_json_schema"):
            # This is a Pydantic model, use its schema directly
            param_schema = param.annotation.model_json_schema()
            parameters_schema["properties"].update(param_schema["properties"])
            parameters_schema["required"].extend(param_schema.get("required", []))
        else:
            # Handle primitive types, simple fields
            # This part needs to be more robust for complex types,
            # but for simple cases like str, int, etc.
            type_map = {str: "string", int: "integer", bool: "boolean", float: "number"}
            parameters_schema["properties"][name] = {
                "type": type_map.get(param.annotation, "string"),  # Default to string
                "description": f"Parameter '{name}' for {method_name}",  # Placeholder description
            }
            if param.default is inspect.Parameter.empty:
                parameters_schema["required"].append(name)

    # Clean up duplicate required fields
    parameters_schema["required"] = list(set(parameters_schema["required"]))

    return ToolDefinition(
        function=FunctionTool(
            name=method_name, description=description, parameters=ToolParameter(**parameters_schema)
        )
    )


# --- MCP Router ---
mcp_router = APIRouter(prefix="/mcp", tags=["Model Context Protocol"])


@mcp_router.get("/tools", response_model=List[ToolDefinition])
async def list_tools(client: XenfraClient = Depends(get_xenfra_client)):
    """
    Returns a list of all Xenfra SDK methods exposed as OpenAI-compatible tools.
    """
    tools = []

    # Example: Expose client.projects.list()
    tools.append(
        generate_tool_schema(
            sdk_method=client.projects.list,
            method_name="xenfra_list_projects",
            description="Lists all projects accessible to the authenticated user.",
        )
    )

    # Add more tools here for other SDK methods (e.g., create_deployment, delete_project)

    return tools


@mcp_router.post("/execute")
async def execute_tool(
    request: ToolExecutionRequest, client: XenfraClient = Depends(get_xenfra_client)
):
    """
    Executes a specified Xenfra SDK method (tool) with the given arguments.
    """
    # This is a simplified dispatcher. In a real scenario, you'd have a mapping
    # from tool_name to actual SDK method and more robust argument validation.
    if request.tool_name == "xenfra_list_projects":
        try:
            result = client.projects.list(**request.tool_arguments)
            return JSONResponse(content={"result": [r.model_dump() for r in result]})
        except XenfraAPIError as e:
            raise HTTPException(status_code=e.status_code, detail=f"Xenfra API Error: {e.detail}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Tool execution failed: {e}")
    else:
        raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found.")


# --- Root Endpoint (No Change) ---
@app.get("/")
async def root():
    return {"message": "Xenfra MCP Server is running!"}


# --- Include Router ---
app.include_router(mcp_router)
