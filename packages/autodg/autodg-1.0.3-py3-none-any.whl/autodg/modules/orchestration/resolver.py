import ast
from loguru import logger
from tqdm import tqdm
from typing import List, Optional, Any
from autodg.modules.core.models import RouteInfo
from autodg.modules.core.call_graph import CallGraphBuilder
from autodg.modules.core.db_detector import DBDetector
from autodg.modules.core.indexer import FunctionIndexer
from autodg.modules.analysis.code_reviewer import CodeReviewer
from autodg.modules.analysis.validation_extractor import ValidationExtractor


class Resolver:
    @staticmethod
    def resolve(
        routes: List[RouteInfo], project_root: str, llm_client: Optional[Any] = None
    ):
        """
        Enrich routes with Call Graph, DB Operation analysis, Context Code, Validations, and AI Review.
        """
        # 1. Build Function Index
        indexer = FunctionIndexer(project_root)
        indexer.build_index()

        reviewer = CodeReviewer(llm_client) if llm_client else None

        print("Resolving call graphs, DB operations, context, and AI reviews...")
        for route in tqdm(routes, desc="Analyzing Routes", unit="route"):
            logger.info(f"Analyzing Route: {route.path} {route.methods}")
            if route.handler_node:
                # Build Call Graph
                calls = CallGraphBuilder.build_graph(route.handler_node)
                route.call_graph = {"direct_calls": calls}

                # Detect DB Operations
                route.db_operations = DBDetector.detect(route.handler_node)

                # Try to resolve actual handler source code (especially for Django where source is just path())
                # If we find the handler in the index, we replace the source code with the actual implementation
                # This gives the LLM the real logic to explain.
                if route.handler_name and route.handler_name != "unknown":
                    handler_source = indexer.get_source(route.handler_name)
                    if handler_source:
                        route.source_code = handler_source
                        # If we swapped the source, re-run DB detection on the new source?
                        # Ideally yes, but DBDetector works on AST. We'd need to re-parse.
                        # For now, let's just update the source for LLM/Docs.
                        # To be thorough, let's try to re-parse and re-detect DB ops if we have time,
                        # but for now the user asked for "proper content" which implies LLM explanation.

                        try:
                            new_ast = ast.parse(handler_source)
                            route.db_operations.extend(DBDetector.detect(new_ast))
                            route.db_operations = list(
                                set(route.db_operations)
                            )  # Unique

                            # Also update call graph based on new source
                            new_calls = CallGraphBuilder.build_graph(new_ast)
                            route.call_graph["direct_calls"] = list(
                                set(route.call_graph["direct_calls"] + new_calls)
                            )
                        except Exception:
                            pass

                # Fetch Context Code for called functions
                for call in route.call_graph.get("direct_calls", []):
                    source = indexer.get_source(call)
                    if source:
                        route.context_code[call] = source

                # Extract Validations
                route.validations = ValidationExtractor.extract(route.handler_node)

                # Perform AI Audit
                if reviewer:
                    route.code_suggestions = reviewer.review_route(
                        route.source_code, route.context_code
                    )
