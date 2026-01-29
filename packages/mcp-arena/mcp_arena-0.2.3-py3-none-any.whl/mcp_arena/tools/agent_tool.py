from typing import Any, Dict, List, Optional
from mcp_arena.agent.interfaces import IAgentTool

class BaseTool(IAgentTool):
    """Base implementation for agent tools"""
    
    def __init__(self, name: str, description: str, schema: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.schema = schema or {}
    
    def get_description(self) -> str:
        return f"{self.name}: {self.description}"
    
    def get_schema(self) -> Dict[str, Any]:
        return self.schema.copy()
