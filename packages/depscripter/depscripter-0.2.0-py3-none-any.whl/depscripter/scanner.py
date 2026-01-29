import ast
from typing import Set

def scan_imports(source_code: str) -> Set[str]:
    """
    Scans the source code for import statements and returns a set of top-level
    module names.
    
    Handles:
    - import x
    - import x.y
    - from x import y
    - from x.y import z
    
    Ignores relative imports (e.g., from . import y).
    """
    tree = ast.parse(source_code)
    modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # import x.y -> x
                name = alias.name.split('.')[0]
                modules.add(name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # Relative import, skip
                continue
            if node.module:
                # from x.y import z -> x
                name = node.module.split('.')[0]
                modules.add(name)
    
    return modules
