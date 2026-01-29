"""Check if an If node is a main guard."""

import ast


def is_main_guard(node: ast.If) -> bool:
    """Check if an If node is an if __name__ == '__main__': guard."""
    test = node.test
    if not isinstance(test, ast.Compare):
        return False
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    if len(test.comparators) != 1:
        return False

    # Check for __name__ == "__main__" or "__main__" == __name__
    left = test.left
    right = test.comparators[0]

    def is_name_dunder(n: ast.expr) -> bool:
        return isinstance(n, ast.Name) and n.id == "__name__"

    def is_main_str(n: ast.expr) -> bool:
        return isinstance(n, ast.Constant) and n.value == "__main__"

    return (is_name_dunder(left) and is_main_str(right)) or (
        is_main_str(left) and is_name_dunder(right)
    )
