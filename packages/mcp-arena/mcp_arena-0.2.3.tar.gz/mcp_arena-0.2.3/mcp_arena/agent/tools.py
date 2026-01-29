from typing import Any, Dict, List, Optional
from .interfaces import IAgentTool

# Import tools from new location
from mcp_arena.tools.agent_tool import BaseTool
from mcp_arena.tools.search import SearchTool
from mcp_arena.tools.calculator import CalculatorTool
from mcp_arena.tools.filesystem import FileSystemTool
from mcp_arena.tools.web import WebTool
from mcp_arena.tools.data_analysis import DataAnalysisTool
from mcp_arena.tools.time_tool import TimeTool

class ToolRegistry:
    """Registry for managing available tools"""
    
    def __init__(self):
        self._tools: Dict[str, type] = {}
        self._instances: Dict[str, IAgentTool] = {}
    
    def register_tool(self, name: str, tool_class: type) -> None:
        """Register a tool class"""
        self._tools[name] = tool_class
    
    def create_tool(self, name: str, **kwargs) -> IAgentTool:
        """Create an instance of a registered tool"""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not registered")
        
        tool_instance = self._tools[name](**kwargs)
        self._instances[name] = tool_instance
        return tool_instance
    
    def get_tool(self, name: str) -> Optional[IAgentTool]:
        """Get an existing tool instance"""
        return self._instances.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())
    
    def create_default_tools(self) -> List[IAgentTool]:
        """Create a set of default tools"""
        tools = [
            CalculatorTool(),
            FileSystemTool(),
            WebTool(),
            DataAnalysisTool(),
            TimeTool()
        ]
        
        # Store instances
        for tool in tools:
            self._instances[tool.name] = tool
        
        return tools


# Global tool registry instance
tool_registry = ToolRegistry()

# Register default tools
tool_registry.register_tool("calculator", CalculatorTool)
tool_registry.register_tool("filesystem", FileSystemTool)
tool_registry.register_tool("web", WebTool)
tool_registry.register_tool("data_analysis", DataAnalysisTool)
tool_registry.register_tool("time", TimeTool)
