import ast
from typing import List, Dict, Any


class ValidationExtractor:
    """
    Statically extracts validation rules from function signatures and Pydantic models.
    """

    @staticmethod
    def extract(node: ast.AST) -> List[Dict[str, Any]]:
        validations = []

        # 1. Check Function Parameters for Type Hints
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in node.args.args:
                if arg.annotation:
                    type_name = "unknown"
                    if isinstance(arg.annotation, ast.Name):
                        type_name = arg.annotation.id
                    elif isinstance(arg.annotation, ast.Attribute):
                        type_name = arg.annotation.attr

                    # Basic documentation of the expected type
                    validations.append(
                        {
                            "field": arg.arg,
                            "location": "body/query/path",
                            "rule": f"Type: {type_name}",
                            "source": "Type Hint",
                        }
                    )

        # 2. Future expansion: Scan for Pydantic/DRF classes in the context
        # This requires traversing external files, which is partially handled by the indexer.

        return validations
