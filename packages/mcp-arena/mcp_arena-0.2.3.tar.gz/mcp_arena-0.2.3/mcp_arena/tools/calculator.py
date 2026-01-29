from .agent_tool import BaseTool

class CalculatorTool(BaseTool):
    """Tool for performing calculations"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations",
            schema={"expression": "string", "type": "mathematical expression"}
        )
    
    def execute(self, expression: str, **kwargs) -> str:
        """Execute mathematical calculation"""
        try:
            # Safe evaluation of mathematical expressions
            import ast
            import operator
            
            # Define safe operators
            operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.Mod: operator.mod,
                ast.USub: operator.neg,
            }
            
            def eval_node(node):
                if isinstance(node, ast.Num):
                    return node.n
                elif isinstance(node, ast.Expression):
                    return eval_node(node.body)
                elif isinstance(node, ast.BinOp):
                    left = eval_node(node.left)
                    right = eval_node(node.right)
                    op_type = type(node.op)
                    if op_type in operators:
                        return operators[op_type](left, right)
                    else:
                        raise ValueError(f"Unsupported operator: {op_type}")
                elif isinstance(node, ast.UnaryOp):
                    operand = eval_node(node.operand)
                    op_type = type(node.op)
                    if op_type in operators:
                        return operators[op_type](operand)
                    else:
                        raise ValueError(f"Unsupported unary operator: {op_type}")
                else:
                    raise ValueError(f"Unsupported expression type: {type(node)}")
            
            # Parse and evaluate the expression
            tree = ast.parse(expression, mode='eval')
            result = eval_node(tree)
            
            return str(result)
        except Exception as e:
            return f"Calculation error: {str(e)}"
