"""Extract assigned variable names from an assignment node."""

import ast


def get_assigned_names(node: ast.Assign | ast.AnnAssign) -> list[str]:
    """Extract assigned variable names from an assignment node."""
    names: list[str] = []

    if isinstance(node, ast.AnnAssign):
        # Annotated assignment: x: int = 5
        if isinstance(node.target, ast.Name):
            names.append(node.target.id)
    else:
        # Regular assignment: x = 5 or x, y = 1, 2
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
            elif isinstance(target, ast.Tuple | ast.List):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        names.append(elt.id)

    return names
