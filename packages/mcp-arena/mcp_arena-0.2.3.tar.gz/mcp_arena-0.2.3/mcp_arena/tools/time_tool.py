from datetime import datetime
from .agent_tool import BaseTool

class TimeTool(BaseTool):
    """Tool for getting current time"""
    
    def __init__(self):
        super().__init__(
            name="time",
            description="Get the current time",
            schema={}
        )
    
    def execute(self, **kwargs) -> str:
        """Execute time operation"""
        return datetime.now().isoformat()
