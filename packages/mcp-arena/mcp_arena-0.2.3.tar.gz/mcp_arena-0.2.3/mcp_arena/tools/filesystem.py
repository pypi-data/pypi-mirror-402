from typing import Optional
from .agent_tool import BaseTool

class FileSystemTool(BaseTool):
    """Tool for file system operations"""
    
    def __init__(self, base_path: str = "."):
        super().__init__(
            name="filesystem",
            description="Perform file system operations like read, write, list files",
            schema={
                "operation": "string",
                "path": "string",
                "content": "string (optional)"
            }
        )
        self.base_path = base_path
    
    def execute(self, operation: str, path: str, content: Optional[str] = None, **kwargs) -> str:
        """Execute file system operation"""
        import os
        
        try:
            full_path = os.path.join(self.base_path, path)
            
            if operation == "read":
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        return f.read()
                else:
                    return f"File not found: {full_path}"
            
            elif operation == "write":
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content or "")
                return f"Successfully wrote to: {full_path}"
            
            elif operation == "list":
                if os.path.exists(full_path):
                    items = os.listdir(full_path)
                    return f"Contents of {full_path}:\n" + "\n".join(items)
                else:
                    return f"Directory not found: {full_path}"
            
            elif operation == "exists":
                return f"Path exists: {os.path.exists(full_path)}"
            
            else:
                return f"Unsupported operation: {operation}"
        
        except Exception as e:
            return f"File system error: {str(e)}"
