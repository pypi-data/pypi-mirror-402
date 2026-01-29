from typing import List, Callable
from .agent_tool import BaseTool

class SearchTool(BaseTool):
    """Tool for performing searches"""
    
    def __init__(self, search_function: Callable[[str], List[str]]):
        super().__init__(
            name="search",
            description="Search for information using the provided query",
            schema={"query": "string", "type": "search query"}
        )
        self.search_function = search_function
    
    def execute(self, query: str, **kwargs) -> List[str]:
        """Execute search with the given query"""
        try:
            results = self.search_function(query)
            return results if isinstance(results, list) else [str(results)]
        except Exception as e:
            return [f"Search error: {str(e)}"]
