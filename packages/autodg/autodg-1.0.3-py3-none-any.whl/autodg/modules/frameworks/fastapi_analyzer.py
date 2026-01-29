import ast
import os
from typing import List, Optional
from autodg.modules.core.scanner import FrameworkAnalyzer
from autodg.modules.core.models import RouteInfo
from autodg.modules.core.utils import find_files, parse_ast, read_file
from autodg.modules.core.ast_parser import ASTParser


class FastAPIAnalyzer(FrameworkAnalyzer):
    def detect(self, project_root: str) -> bool:
        files = find_files(project_root)
        for file in files:
            content = parse_ast(file)
            if not content:
                continue
            for node in ast.walk(content):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if "fastapi" in alias.name.lower():
                            return True
        return False

    def extract_routes(self, project_root: str) -> List[RouteInfo]:
        self.project_root = project_root
        self.local_router_prefixes = {}  # file_path -> { var_name -> prefix }
        self.global_router_prefixes = {}  # file_path -> prefix (from include_router)
        routes = []
        files = find_files(project_root)

        # 1. First pass: Find APIRouter definitions in every file
        for file_path in files:
            try:
                tree = parse_ast(file_path)
                if not tree:
                    continue
                self.local_router_prefixes[file_path] = {}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign) and isinstance(
                        node.value, ast.Call
                    ):
                        is_api_router = False
                        if (
                            isinstance(node.value.func, ast.Name)
                            and node.value.func.id == "APIRouter"
                        ):
                            is_api_router = True
                        elif (
                            isinstance(node.value.func, ast.Attribute)
                            and node.value.func.attr == "APIRouter"
                        ):
                            is_api_router = True

                        if is_api_router:
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    var_name = target.id
                                    prefix = ""
                                    for kw in node.value.keywords:
                                        if kw.arg == "prefix" and isinstance(
                                            kw.value, (ast.Constant, ast.Str)
                                        ):
                                            prefix = (
                                                kw.value.value
                                                if isinstance(kw.value, ast.Constant)
                                                else kw.value.s
                                            )
                                    self.local_router_prefixes[file_path][
                                        var_name
                                    ] = prefix
            except Exception:
                continue

        # 2. Second pass: Trace include_router calls
        for file_path in files:
            try:
                tree = parse_ast(file_path)
                if not tree:
                    continue

                imports = {}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports[alias.asname or alias.name] = alias.name
                    elif isinstance(node, ast.ImportFrom):
                        module_base = node.module or ""
                        for alias in node.names:
                            full_name = (
                                f"{module_base}.{alias.name}"
                                if module_base
                                else alias.name
                            )
                            imports[alias.asname or alias.name] = full_name

                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "include_router"
                    ):
                        if node.args:
                            router_node = node.args[0]
                            module_name = None

                            if isinstance(router_node, ast.Attribute) and isinstance(
                                router_node.value, ast.Name
                            ):
                                module_local_name = router_node.value.id
                                module_name = imports.get(
                                    module_local_name, module_local_name
                                )
                            elif isinstance(router_node, ast.Name):
                                module_name = imports.get(
                                    router_node.id, router_node.id
                                )

                            if module_name:
                                target_file = self._resolve_module_to_file(module_name)
                                if target_file:
                                    prefix = ""
                                    for kw in node.keywords:
                                        if kw.arg == "prefix" and isinstance(
                                            kw.value, (ast.Constant, ast.Str)
                                        ):
                                            prefix = (
                                                kw.value.value
                                                if isinstance(kw.value, ast.Constant)
                                                else kw.value.s
                                            )
                                    self.global_router_prefixes[target_file] = prefix
            except Exception:
                continue

        # 3. Third pass: Extract actual routes
        for file_path in files:
            try:
                tree = parse_ast(file_path)
                if not tree:
                    continue

                file_content = read_file(file_path)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        route = self._process_function(node, file_path, file_content)
                        if route:
                            routes.append(route)
            except Exception:
                continue

        return routes

    def _resolve_module_to_file(self, module_name: str) -> Optional[str]:
        """Try to find the file corresponding to a module name."""
        rel_module_path = module_name.replace(".", "/")
        extensions = [".py", "/__init__.py"]

        # Bases to search in:
        # 1. project_root (e.g. app/)
        # 2. project_root's parent (e.g. code/ where app/ is a package)
        # 3. current directory (where autodg is running)
        bases = [self.project_root, os.path.dirname(self.project_root), os.getcwd()]

        # Remove any duplicates and keep order
        unique_bases = []
        for b in bases:
            if b and b not in unique_bases:
                unique_bases.append(b)

        for base in unique_bases:
            for ext in extensions:
                p = os.path.normpath(os.path.join(base, rel_module_path + ext))
                if os.path.exists(p):
                    return p

        # Try stripping the first part (e.g. 'app.routers.hr' -> 'routers/hr.py' if the root is 'app/')
        parts = rel_module_path.split("/")
        if len(parts) > 1:
            subpath = "/".join(parts[1:])
            for base in unique_bases:
                for ext in extensions:
                    p = os.path.normpath(os.path.join(base, subpath + ext))
                    if os.path.exists(p):
                        return p
        return None

    def _process_function(
        self, node: ast.AST, file_path: str, file_content: str
    ) -> Optional[RouteInfo]:
        decorators = getattr(node, "decorator_list", [])
        for decorator in decorators:
            if isinstance(decorator, ast.Call):
                # Check for standard FastAPI methods
                methods_map = {
                    "get": "GET",
                    "post": "POST",
                    "put": "PUT",
                    "delete": "DELETE",
                    "patch": "PATCH",
                    "options": "OPTIONS",
                    "head": "HEAD",
                    "trace": "TRACE",
                }

                func_attr = ""
                if isinstance(decorator.func, ast.Attribute):
                    func_attr = decorator.func.attr
                elif isinstance(decorator.func, ast.Name):
                    # Handle @get("/") if imported
                    func_attr = decorator.func.id

                if func_attr.lower() in methods_map:
                    # Check if it has a path argument
                    path_part = ""
                    if decorator.args:
                        arg = decorator.args[0]
                        if isinstance(arg, ast.Constant):
                            path_part = str(arg.value)
                        elif isinstance(arg, (ast.Str, ast.Bytes)):
                            path_part = str(
                                getattr(arg, "s", getattr(arg, "value", ""))
                            )
                    else:
                        for kw in decorator.keywords:
                            if kw.arg == "path" and isinstance(
                                kw.value, (ast.Constant, ast.Str)
                            ):
                                path_part = (
                                    kw.value.value
                                    if isinstance(kw.value, ast.Constant)
                                    else kw.value.s
                                )
                                break

                    if path_part or not decorator.args:  # path="" is possible
                        # Resolve prefixes
                        local_prefix = ""
                        var_name = ""
                        if isinstance(decorator.func, ast.Attribute) and isinstance(
                            decorator.func.value, ast.Name
                        ):
                            var_name = decorator.func.value.id
                            local_prefix = self.local_router_prefixes.get(
                                file_path, {}
                            ).get(var_name, "")

                        global_prefix = self.global_router_prefixes.get(file_path, "")

                        full_path = self.normalize_path(
                            global_prefix + "/" + local_prefix + "/" + path_part
                        )
                        # Remove double slashes
                        while "//" in full_path:
                            full_path = full_path.replace("//", "/")

                        method = methods_map.get(func_attr.lower(), func_attr.upper())

                        extra_meta = {}
                        for keyword in decorator.keywords:
                            if keyword.arg in ["tags", "summary", "response_model"]:
                                extra_meta[keyword.arg] = "extracted"

                        return RouteInfo(
                            path=full_path,
                            methods=[method],
                            handler_name=getattr(node, "name", "unknown"),
                            handler_node=node,
                            module=file_path,
                            framework="FastAPI",
                            line_number=node.lineno,
                            source_code=ASTParser.get_function_source(
                                node, file_content
                            ),
                            docstring=ASTParser.get_docstring(node),
                            parameters=ASTParser.extract_parameters(node),
                            extra_meta=extra_meta,
                        )
        return None
