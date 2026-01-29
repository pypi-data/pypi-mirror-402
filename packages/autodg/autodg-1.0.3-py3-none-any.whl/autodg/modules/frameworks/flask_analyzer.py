import ast
import os
from typing import List, Optional
from autodg.modules.core.scanner import FrameworkAnalyzer
from autodg.modules.core.models import RouteInfo
from autodg.modules.core.utils import find_files, parse_ast, read_file
from autodg.modules.core.ast_parser import ASTParser


class FlaskAnalyzer(FrameworkAnalyzer):
    def detect(self, project_root: str) -> bool:
        files = find_files(project_root)
        for file in files:
            content = parse_ast(file)
            if not content:
                continue
            for node in ast.walk(content):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if "flask" in alias.name.lower():
                            return True
        return False

    def extract_routes(self, project_root: str) -> List[RouteInfo]:
        self.project_root = project_root
        self.blueprint_local_prefixes = {}  # file_path -> { var_name -> prefix }
        self.blueprint_global_prefixes = (
            {}
        )  # file_path -> prefix (from register_blueprint)
        routes = []
        files = find_files(project_root)

        # 1. First pass: Find Blueprint definitions
        for file_path in files:
            try:
                tree = parse_ast(file_path)
                if not tree:
                    continue
                self.blueprint_local_prefixes[file_path] = {}
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign) and isinstance(
                        node.value, ast.Call
                    ):
                        is_bp = False
                        if (
                            isinstance(node.value.func, ast.Name)
                            and node.value.func.id == "Blueprint"
                        ):
                            is_bp = True
                        elif (
                            isinstance(node.value.func, ast.Attribute)
                            and node.value.func.attr == "Blueprint"
                        ):
                            is_bp = True

                        if is_bp:
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    var_name = target.id
                                    prefix = ""
                                    for kw in node.value.keywords:
                                        if kw.arg == "url_prefix" and isinstance(
                                            kw.value, (ast.Constant, ast.Str)
                                        ):
                                            prefix = (
                                                kw.value.value
                                                if isinstance(kw.value, ast.Constant)
                                                else kw.value.s
                                            )
                                    self.blueprint_local_prefixes[file_path][
                                        var_name
                                    ] = prefix
            except Exception:
                continue

        # 2. Second pass: Trace register_blueprint calls
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
                        and node.func.attr == "register_blueprint"
                    ):
                        if node.args:
                            bp_node = node.args[0]
                            module_name = None

                            if isinstance(bp_node, ast.Attribute) and isinstance(
                                bp_node.value, ast.Name
                            ):
                                module_local_name = bp_node.value.id
                                module_name = imports.get(
                                    module_local_name, module_local_name
                                )
                            elif isinstance(bp_node, ast.Name):
                                module_name = imports.get(bp_node.id, bp_node.id)

                            if module_name:
                                target_file = self._resolve_module_to_file(module_name)
                                if target_file:
                                    prefix = ""
                                    for kw in node.keywords:
                                        if kw.arg == "url_prefix" and isinstance(
                                            kw.value, (ast.Constant, ast.Str)
                                        ):
                                            prefix = (
                                                kw.value.value
                                                if isinstance(kw.value, ast.Constant)
                                                else kw.value.s
                                            )
                                    # Flask prepends. If BP has /auth and registration has /api, it's /api/auth
                                    self.blueprint_global_prefixes[target_file] = prefix
            except Exception:
                continue

        # 3. Third pass: Extract routes
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

                    if (
                        isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "add_url_rule"
                    ):
                        route = self._process_add_url_rule(
                            node, file_path, file_content
                        )
                        if route:
                            routes.append(route)
            except Exception:
                continue
        return routes

    def _process_function(
        self, node: ast.FunctionDef, file_path: str, file_content: str
    ) -> Optional[RouteInfo]:
        decorators = node.decorator_list
        for decorator in decorators:
            if isinstance(decorator, ast.Call):
                # Handle @app.route('/path') or @bp.route('/path')
                if (
                    isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr == "route"
                ):
                    if decorator.args:
                        path_part = (
                            decorator.args[0].value
                            if isinstance(decorator.args[0], ast.Constant)
                            else "unknown"
                        )

                        prefix = ""
                        if isinstance(decorator.func.value, ast.Name):
                            var_name = decorator.func.value.id
                            prefix = self.blueprint_local_prefixes.get(
                                file_path, {}
                            ).get(var_name, "")

                        global_prefix = self.blueprint_global_prefixes.get(
                            file_path, ""
                        )

                        full_path = self.normalize_path(
                            global_prefix + "/" + prefix + "/" + path_part
                        )
                        methods = ["GET"]  # Default

                        # Extract methods from keywords
                        for keyword in decorator.keywords:
                            if keyword.arg == "methods" and isinstance(
                                keyword.value, ast.List
                            ):
                                methods = [
                                    elt.value
                                    for elt in keyword.value.elts
                                    if isinstance(elt, ast.Constant)
                                ]

                        return RouteInfo(
                            path=full_path,
                            methods=methods,
                            handler_name=node.name,
                            handler_node=node,
                            module=file_path,
                            framework="Flask",
                            line_number=node.lineno,
                            source_code=ASTParser.get_function_source(
                                node, file_content
                            ),
                            docstring=ASTParser.get_docstring(node),
                            parameters=ASTParser.extract_parameters(node),
                        )

                # Handle @app.get('/path'), @app.post('/path') etc.
                elif isinstance(
                    decorator.func, ast.Attribute
                ) and decorator.func.attr in ["get", "post", "put", "delete", "patch"]:
                    if decorator.args:
                        path_part = (
                            decorator.args[0].value
                            if isinstance(decorator.args[0], ast.Constant)
                            else "unknown"
                        )

                        prefix = ""
                        if isinstance(decorator.func.value, ast.Name):
                            var_name = decorator.func.value.id
                            prefix = self.blueprint_local_prefixes.get(
                                file_path, {}
                            ).get(var_name, "")

                        global_prefix = self.blueprint_global_prefixes.get(
                            file_path, ""
                        )
                        full_path = self.normalize_path(
                            global_prefix + "/" + prefix + "/" + path_part
                        )
                        method = decorator.func.attr.upper()
                        return RouteInfo(
                            path=full_path,
                            methods=[method],
                            handler_name=node.name,
                            handler_node=node,
                            module=file_path,
                            framework="Flask",
                            line_number=node.lineno,
                            source_code=ASTParser.get_function_source(
                                node, file_content
                            ),
                            docstring=ASTParser.get_docstring(node),
                            parameters=ASTParser.extract_parameters(node),
                        )
        return None

    def _process_add_url_rule(
        self, node: ast.Call, file_path: str, file_content: str
    ) -> Optional[RouteInfo]:
        # Handle app.add_url_rule('/path', 'endpoint', view_func)
        if len(node.args) >= 3:
            path_part = (
                node.args[0].value
                if isinstance(node.args[0], ast.Constant)
                else "unknown"
            )
            view_func = node.args[2]

            prefix = ""
            if isinstance(node.func, ast.Attribute) and isinstance(
                node.func.value, ast.Name
            ):
                var_name = node.func.value.id
                prefix = self.blueprint_local_prefixes.get(file_path, {}).get(
                    var_name, ""
                )

            global_prefix = self.blueprint_global_prefixes.get(file_path, "")
            full_path = self.normalize_path(
                global_prefix + "/" + prefix + "/" + path_part
            )

            handler_name = "unknown"
            if isinstance(view_func, ast.Name):
                handler_name = view_func.id
            elif isinstance(view_func, ast.Attribute):
                handler_name = view_func.attr

            methods = ["GET"]
            for keyword in node.keywords:
                if keyword.arg == "methods" and isinstance(keyword.value, ast.List):
                    methods = [
                        elt.value
                        for elt in keyword.value.elts
                        if isinstance(elt, ast.Constant)
                    ]

            return RouteInfo(
                path=full_path,
                methods=methods,
                handler_name=handler_name,
                handler_node=node,
                module=file_path,
                framework="Flask",
                line_number=node.lineno,
                source_code=ast.get_source_segment(file_content, node) or "",
                docstring="",
                parameters=[],
            )
        return None

    def _resolve_module_to_file(self, module_name: str) -> Optional[str]:
        """Try to find the file corresponding to a module name."""
        rel_module_path = module_name.replace(".", "/")
        extensions = [".py", "/__init__.py"]
        bases = [self.project_root, os.path.dirname(self.project_root), os.getcwd()]
        unique_bases = []
        for b in bases:
            if b and b not in unique_bases:
                unique_bases.append(b)

        for base in unique_bases:
            for ext in extensions:
                p = os.path.normpath(os.path.join(base, rel_module_path + ext))
                if os.path.exists(p):
                    return p

        parts = rel_module_path.split("/")
        if len(parts) > 1:
            subpath = "/".join(parts[1:])
            for base in unique_bases:
                for ext in extensions:
                    p = os.path.normpath(os.path.join(base, subpath + ext))
                    if os.path.exists(p):
                        return p
        return None
