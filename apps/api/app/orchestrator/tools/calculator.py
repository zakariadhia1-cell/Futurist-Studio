"""Safe arithmetic evaluator - parses with `ast` and only ever calls a fixed whitelist
of operator functions, so it can't execute arbitrary code (unlike eval())."""
import ast
import operator

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("Nur Zahlen sind in Ausdruecken erlaubt.")
    if isinstance(node, ast.BinOp):
        op_fn = _ALLOWED_OPERATORS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Operator nicht erlaubt: {type(node.op).__name__}")
        return op_fn(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op_fn = _ALLOWED_OPERATORS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Operator nicht erlaubt: {type(node.op).__name__}")
        return op_fn(_eval_node(node.operand))
    raise ValueError(f"Ausdruck nicht erlaubt: {type(node).__name__}")


def safe_eval(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)
