from typing import Any
from .agent_tool import BaseTool

class DataAnalysisTool(BaseTool):
    """Tool for data analysis operations"""
    
    def __init__(self):
        super().__init__(
            name="data_analysis",
            description="Perform basic data analysis on provided data",
            schema={"data": "string/list", "operation": "string"}
        )
    
    def execute(self, operation: str, data: Any, **kwargs) -> str:
        """Execute data analysis operation"""
        try:
            if operation == "summarize":
                if isinstance(data, str):
                    # Text summary
                    words = len(data.split())
                    chars = len(data)
                    lines = len(data.split('\n'))
                    return f"Text summary: {words} words, {chars} characters, {lines} lines"
                
                elif isinstance(data, list):
                    # List summary
                    return f"List summary: {len(data)} items"
                
                else:
                    return f"Data type: {type(data).__name__}"
            
            elif operation == "statistics":
                if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
                    import statistics
                    return {
                        "count": len(data),
                        "mean": statistics.mean(data),
                        "median": statistics.median(data),
                        "min": min(data),
                        "max": max(data)
                    }
                else:
                    return "Statistics only available for numeric lists"
            
            else:
                return f"Unsupported data operation: {operation}"
        
        except Exception as e:
            return f"Data analysis error: {str(e)}"
