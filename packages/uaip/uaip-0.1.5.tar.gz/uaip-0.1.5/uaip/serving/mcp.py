from typing import Any, Dict, Optional
from fastmcp import FastMCP, Context

from uaip.core.state import State


def create_mcp_server(workflow) -> FastMCP:
    mcp = FastMCP(workflow.name, stateless_http=True)
    
    for stage_name, stage in workflow.stages.items():
        for task_name, task in stage.tasks.items():
            _register_tool(mcp, stage_name, task_name, task)
    
    return mcp


def _register_tool(mcp: FastMCP, stage_name: str, task_name: str, task) -> None:
    schema = task.to_schema()
    input_schema = schema.get("input_schema", {})
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])
    
    # Get the underlying function to extract its signature
    fn = task.fn
    
    # Create wrapper that extracts kwargs and passes to task
    async def tool_wrapper(**kwargs) -> Dict[str, Any]:
        try:
            # Filter out 'ctx' if present (FastMCP injects it)
            task_kwargs = {k: v for k, v in kwargs.items() if k != 'ctx' and v is not None}
            
            # For stateless mode, use simple dict for state
            state = State({})
            
            result = await task.execute(state, **task_kwargs)
            
            return result or {"status": "ok"}
        except Exception as e:
            return {"error": str(e)}
    
    # Copy signature info from original function for FastMCP introspection
    import inspect
    import functools
    
    # Get original function's signature (skip 'self' and 'state')
    orig_sig = inspect.signature(fn)
    orig_params = list(orig_sig.parameters.values())
    
    # Filter out 'self' and 'state' parameters
    filtered_params = [p for p in orig_params if p.name not in ('self', 'state')]
    
    # Create new signature
    new_sig = orig_sig.replace(parameters=filtered_params)
    tool_wrapper.__signature__ = new_sig
    tool_wrapper.__name__ = f"{stage_name}_{task_name}"
    tool_wrapper.__doc__ = task.description
    
    # Register tool
    mcp.tool(
        name=f"{stage_name}_{task_name}",
        description=task.description
    )(tool_wrapper)
