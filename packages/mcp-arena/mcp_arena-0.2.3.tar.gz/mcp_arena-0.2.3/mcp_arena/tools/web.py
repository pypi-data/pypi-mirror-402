from .agent_tool import BaseTool

class WebTool(BaseTool):
    """Tool for web operations"""
    
    def __init__(self):
        super().__init__(
            name="web",
            description="Perform web operations like fetch webpage content",
            schema={"url": "string", "operation": "string"}
        )
    
    def execute(self, operation: str, url: str, **kwargs) -> str:
        """Execute web operation"""
        try:
            if operation == "fetch":
                import requests
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response.text[:2000]  # Limit to first 2000 characters
            
            elif operation == "headers":
                import requests
                response = requests.head(url, timeout=10)
                response.raise_for_status()
                return str(dict(response.headers))
            
            else:
                return f"Unsupported web operation: {operation}"
        
        except Exception as e:
            return f"Web operation error: {str(e)}"
