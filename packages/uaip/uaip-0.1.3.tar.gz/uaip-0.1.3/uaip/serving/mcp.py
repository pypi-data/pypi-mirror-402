from typing import Any, Dict, Optional
from fastmcp import FastMCP, Context

from uaip.core.state import State


def create_mcp_server(workflow) -> FastMCP:
    mcp = FastMCP(workflow.name)
    
    for stage_name, stage in workflow.stages.items():
        for task_name, task in stage.tasks.items():
            _register_tool(mcp, stage_name, task_name, task)
    
    return mcp


def _register_tool(mcp: FastMCP, stage_name: str, task_name: str, task) -> None:
    schema = task.to_schema()
    input_schema = schema.get("input_schema", {})
    properties = input_schema.get("properties", {})
    
    # Build parameter string for dynamic function
    params = []
    for param_name, param_info in properties.items():
        param_type = param_info.get("type", "string")
        default = param_info.get("default")
        if default is not None:
            params.append(f"{param_name}: {_py_type(param_type)} = {repr(default)}")
        else:
            params.append(f"{param_name}: {_py_type(param_type)} = None")
    
    param_str = ", ".join(params)
    param_names = list(properties.keys())
    
    # Create closure to capture task and stage_name
    def make_tool(task, stage_name, param_names):
        async def tool_func(ctx: Context, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            try:
                state_dict = ctx.get_state(stage_name) or {}
                state = State(state_dict)
                
                result = await task.execute(state, **(args or {}))
                
                ctx.set_state(stage_name, state.data)
                
                return result or {"status": "ok"}
            except Exception as e:
                return {"error": str(e)}
        return tool_func
    
    tool_fn = make_tool(task, stage_name, param_names)
    
    # Register with schema override
    mcp.tool(
        name=f"{stage_name}_{task_name}",
        description=task.description
    )(tool_fn)


def _py_type(json_type: str) -> str:
    return {
        "string": "str",
        "integer": "int", 
        "number": "float",
        "boolean": "bool",
        "object": "dict",
        "array": "list"
    }.get(json_type, "Any")
