from typing import List
from autodg.modules.core.models import RouteInfo
from autodg.modules.core.llm import LLMClient


class DevOpsGenerator:
    """
    Generates Scaling and Deployment documents based on project analysis.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate_scaling_doc(self, routes: List[RouteInfo]) -> str:
        """
        Analyzes routes to suggest a scaling strategy.
        """
        # Aggregate info
        frameworks = list(set([r.framework for r in routes]))
        db_ops = []
        for r in routes:
            db_ops.extend(r.db_operations)
        db_ops = list(set(db_ops))

        prompt = f"""
Based on the following project analysis, generate a comprehensive **SCALING DOCUMENT**.
Frameworks: {", ".join(frameworks)}
Total Routes: {len(routes)}
Detected DB Operations: {", ".join(db_ops)}

Include:
1. **Vertical Scaling**: Recommended CPU/RAM for single instance.
2. **Horizontal Scaling**: Strategy for load balancing and state management.
3. **Database Scaling**: Suggestions for connection pooling, read-replicas, or sharding.
4. **Caching**: Where to implement Redis/Memcached.
5. **Concurrency**: How to handle the ASGI/WSGI workers.

Format as professional Markdown.
"""
        if self.llm_client and self.llm_client.is_available():
            return self.llm_client.generate(prompt)
        return "LLM not available for Scaling Document generation."

    def generate_deployment_doc(
        self, routes: List[RouteInfo], project_root: str
    ) -> str:
        """
        Generates a deployment guide including Docker and CI/CD suggestions.
        """
        frameworks = list(set([r.framework for r in routes]))

        prompt = f"""
Generate a **DEPLOYMENT GUIDE** for a project with the following tech stack:
Frameworks: {", ".join(frameworks)}

Include:
1. **Dockerfile**: A production-ready Dockerfile snippet.
2. **Environment Variables**: List of common variables needed (DB_URL, SECRET_KEY, etc).
3. **CI/CD Pipeline**: A brief GitHub Actions or GitLab CI snippet.
4. **Security Hardening**: Best practices for production deployment.

Format as professional Markdown.
"""
        if self.llm_client and self.llm_client.is_available():
            return self.llm_client.generate(prompt)
        return "LLM not available for Deployment Guide generation."
