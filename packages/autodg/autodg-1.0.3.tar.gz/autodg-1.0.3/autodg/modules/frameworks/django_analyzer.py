import ast
import os
from typing import List, Optional
from autodg.modules.core.scanner import FrameworkAnalyzer
from autodg.modules.core.models import RouteInfo
from autodg.modules.core.utils import find_files, parse_ast, read_file


class DjangoAnalyzer(FrameworkAnalyzer):
    def detect(self, project_root: str) -> bool:
        files = find_files(project_root)
        for file in files:
            content = parse_ast(file)
            if not content:
                continue
            for node in ast.walk(content):
                if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if "django" in alias.name.lower():
                            return True
        return False

    def extract_routes(self, project_root: str) -> List[RouteInfo]:
        self.project_root = project_root
        self.processed_files = set()
        routes = []
        files = find_files(project_root)

        # Try to find the root urls.py (usually in a folder with settings.py)
        root_urls = None
        for file_path in files:
            if file_path.endswith("urls.py"):
                # Heuristic: the one with 'wsgi.py' or 'settings.py' in the same dir is likely root
                parent = os.path.dirname(file_path)
                if os.path.exists(
                    os.path.join(parent, "settings.py")
                ) or os.path.exists(os.path.join(parent, "wsgi.py")):
                    root_urls = file_path
                    break

        if root_urls:
            routes.extend(self._process_urls_file(root_urls, ""))
        else:
            # Fallback: process all urls.py independently if root not found
            for file_path in files:
                if "urls.py" in file_path:
                    routes.extend(self._process_urls_file(file_path, ""))

        return routes

    def _process_urls_file(self, file_path: str, prefix: str) -> List[RouteInfo]:
        if file_path in self.processed_files:
            return []
        self.processed_files.add(file_path)

        routes = []
        try:
            source_code = read_file(file_path)
            if not source_code:
                return []
            tree = ast.parse(source_code, filename=file_path)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "urlpatterns":
                        routes.extend(
                            self._process_urlpatterns(
                                node.value, file_path, prefix, source_code
                            )
                        )
        return routes

    def _process_urlpatterns(
        self, node: ast.AST, file_path: str, prefix: str, source_code: str
    ) -> List[RouteInfo]:
        routes = []
        if isinstance(node, ast.List):
            for item in node.elts:
                if isinstance(item, ast.Call):
                    # Handle path('route', view, name='name') or re_path(...)
                    func_name = ""
                    if isinstance(item.func, ast.Name):
                        func_name = item.func.id
                    elif isinstance(item.func, ast.Attribute):
                        func_name = item.func.attr

                    if func_name in ["path", "re_path"]:
                        if len(item.args) >= 2:
                            route_part_node = item.args[0]
                            route_part = ""
                            if isinstance(route_part_node, ast.Constant):
                                route_part = str(route_part_node.value)
                            elif isinstance(
                                route_part_node, ast.Str
                            ):  # For older python versions
                                route_part = route_part_node.s

                            full_path = self.normalize_path(prefix + route_part)

                            view_arg = item.args[1]

                            # Check if it's an include()
                            if isinstance(view_arg, ast.Call) and (
                                (
                                    isinstance(view_arg.func, ast.Name)
                                    and view_arg.func.id == "include"
                                )
                                or (
                                    isinstance(view_arg.func, ast.Attribute)
                                    and view_arg.func.attr == "include"
                                )
                            ):
                                # It's an include('myapp.urls')
                                if view_arg.args and isinstance(
                                    view_arg.args[0], (ast.Constant, ast.Str)
                                ):
                                    included_module = (
                                        view_arg.args[0].value
                                        if isinstance(view_arg.args[0], ast.Constant)
                                        else view_arg.args[0].s
                                    )

                                    # Resolve module to file path
                                    potential_path = self._resolve_module_to_file(
                                        included_module
                                    )
                                    if potential_path:
                                        routes.extend(
                                            self._process_urls_file(
                                                potential_path, full_path
                                            )
                                        )
                            else:
                                # It's a view
                                handler_name = "unknown"
                                if isinstance(view_arg, ast.Name):
                                    handler_name = view_arg.id
                                elif isinstance(view_arg, ast.Attribute):
                                    handler_name = view_arg.attr
                                elif isinstance(view_arg, ast.Call):
                                    # Handle Class.as_view()
                                    if (
                                        isinstance(view_arg.func, ast.Attribute)
                                        and view_arg.func.attr == "as_view"
                                    ):
                                        val = view_arg.func.value
                                        if isinstance(val, ast.Name):
                                            handler_name = val.id
                                        elif isinstance(val, ast.Attribute):
                                            handler_name = val.attr

                                routes.append(
                                    RouteInfo(
                                        path=full_path,
                                        methods=[
                                            "GET",
                                            "POST",
                                            "PUT",
                                            "DELETE",
                                            "PATCH",
                                        ],
                                        handler_name=handler_name,
                                        handler_node=view_arg,
                                        module=file_path,
                                        framework="Django",
                                        line_number=item.lineno,
                                        source_code=ast.get_source_segment(
                                            source_code, item
                                        )
                                        or "",
                                        docstring="",
                                    )
                                )
        return routes

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
        return None
