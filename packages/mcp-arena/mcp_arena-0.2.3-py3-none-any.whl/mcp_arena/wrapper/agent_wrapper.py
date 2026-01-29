from typing import List, Dict, Any, Callable, Optional, Union
from dataclasses import dataclass
import json
import inspect
from typing import get_type_hints

@dataclass
class AgentTool:
    """Represents a tool that can be used by an AI agent."""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable

class MCPAgentWrapper:
    """Wraps MCP server tools into agent-compatible tools."""
    
    def __init__(self, mcp_server):
        self.mcp_server = mcp_server
        self.tools: List[AgentTool] = self._wrap_tools()
        self.tool_map: Dict[str, AgentTool] = {tool.name: tool for tool in self.tools}
    
    def _wrap_tools(self) -> List[AgentTool]:
        """Wrap all registered MCP tools into agent tools."""
        agent_tools = []
        
        # For each tool in the MCP server, create an agent tool
        for tool_name, tool_func in self._get_mcp_tools():
            # Extract description and parameters from tool metadata
            description = self._extract_description(tool_func)
            parameters = self._extract_parameters(tool_func)
            
            # Create the agent tool
            agent_tool = AgentTool(
                name=tool_name,
                description=description,
                parameters=parameters,
                function=self._create_wrapper(tool_func)
            )
            agent_tools.append(agent_tool)
        
        return agent_tools
    
    def _get_mcp_tools(self) -> List[tuple]:
        """Get all tools from the MCP server.
        This needs to be implemented based on your MCP server structure.
        """
        tools = []
        
        # Check standard locations for tools
        if hasattr(self.mcp_server, '_registered_tools') and isinstance(self.mcp_server._registered_tools, dict):
            # If your MCP server stores tools in a registry
            for tool_name, tool_info in self.mcp_server._registered_tools.items():
                if isinstance(tool_info, dict) and 'function' in tool_info:
                    tools.append((tool_name, tool_info['function']))
                else:
                    tools.append((tool_name, tool_info))
        
        elif hasattr(self.mcp_server, 'mcp_server') and hasattr(self.mcp_server.mcp_server, '_tools'):
             # Support nested mcp_server object
            for tool_name, tool_func in self.mcp_server.mcp_server._tools.items():
                tools.append((tool_name, tool_func))
                
        elif hasattr(self.mcp_server, 'list_tools'):
             # Support list_tools method if available (returns list of tool names usually, might need fetch)
             # This is a placeholder for better MCP protocol support
             pass
        
        return tools
    
    def _extract_description(self, tool_func: Callable) -> str:
        """Extract description from tool function."""
        if hasattr(tool_func, '__doc__') and tool_func.__doc__:
            return tool_func.__doc__.strip().split('\n')[0]
        return f"Tool: {tool_func.__name__}"
    
    def _extract_parameters(self, tool_func: Callable) -> Dict[str, Any]:
        """Extract parameter schema from tool function.
        This uses type hints to generate a JSON Schema.
        """
        
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Get function signature
        try:
            sig = inspect.signature(tool_func)
            type_hints = get_type_hints(tool_func)
        except Exception:
            # Fallback for when signature cannot be inspected
            return schema
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Skip var positional/keyword args for now
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
                
            param_type = type_hints.get(param_name, str)
            param_info = {
                "type": self._python_type_to_json_type(param_type),
                "description": f"Parameter: {param_name}"
            }
            
            # Add default value if exists
            if param.default != inspect.Parameter.empty:
                param_info["default"] = str(param.default) # Convert to str for safety
            else:
                schema["required"].append(param_name)
            
            schema["properties"][param_name] = param_info
        
        return schema
    
    def _python_type_to_json_type(self, python_type):
        """Convert Python type to JSON Schema type."""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null"
        }
        
        # Handle simple types
        if python_type in type_map:
            return type_map[python_type]
            
        # Handle typing module types
        if hasattr(python_type, '__origin__'):
            if python_type.__origin__ is list or python_type.__origin__ is List:
                return "array"
            elif python_type.__origin__ is dict or python_type.__origin__ is Dict:
                return "object"
            elif python_type.__origin__ is Union:
                 # simple handling for Optional (Union[T, NoneType])
                 args = python_type.__args__
                 non_none_args = [arg for arg in args if arg is not type(None)]
                 if non_none_args:
                     return self._python_type_to_json_type(non_none_args[0])
        
        # Default to string
        return "string"
    
    def _create_wrapper(self, tool_func: Callable) -> Callable:
        """Create a wrapper function that formats output for agents."""
        def wrapper(**kwargs):
            try:
                # Call the original MCP tool
                result = tool_func(**kwargs)
                
                # Format the result for agent consumption
                return self._format_result(result)
            except Exception as e:
                return json.dumps({
                    "error": str(e),
                    "success": False
                })
        
        # Preserve the original function name and docstring
        try:
            wrapper.__name__ = tool_func.__name__
            wrapper.__doc__ = tool_func.__doc__
        except AttributeError:
            pass
            
        return wrapper
    
    def _format_result(self, result: Any) -> str:
        """Format tool result for agent consumption."""
        if isinstance(result, dict) or isinstance(result, list):
             return json.dumps(result, indent=2, default=str)
        return str(result)
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tools in OpenAI-compatible format."""
        openai_tools = []
        
        for tool in self.tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        
        return openai_tools
    
    def run_tool(self, tool_name: str, **kwargs) -> str:
        """Run a specific tool by name."""
        tool = self.tool_map.get(tool_name)
        if tool:
            return tool.function(**kwargs)
        return f"Error: Tool '{tool_name}' not found"
