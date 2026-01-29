import os
import ast
from typing import Optional, List


def read_file(file_path: str) -> str:
    """
    Read file content safely, replacing invalid characters.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""


def parse_ast(file_path: str) -> Optional[ast.AST]:
    """
    Parse a Python file into an AST.
    """
    content = read_file(file_path)
    if not content:
        return None
    try:
        return ast.parse(content, filename=file_path)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return None


def find_files(
    root_dir: str, extension: str = ".py", exclude_dirs: Optional[List[str]] = None
) -> List[str]:
    """
    Recursively find all files with a specific extension, skipping excluded directories.
    """
    if exclude_dirs is None:
        exclude_dirs = [
            "env",
            "venv",
            ".env",
            ".venv",
            "node_modules",
            "site-packages",
            "__pycache__",
            ".git",
            "media",
            "uploads",
            "static",
            "templates",
        ]

    matches = []
    for root, dirs, files in os.walk(root_dir):
        # Filter directories
        dirs[:] = [
            d
            for d in dirs
            if not any(d.startswith(ex) for ex in exclude_dirs)
            and "site-packages" not in d
        ]

        for file in files:
            if file.endswith(extension):
                path = os.path.join(root, file)
                matches.append(path)

    return matches
