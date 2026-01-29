from typing import List
from autodg.modules.core.models import RouteInfo
from autodg.modules.core.llm import LLMClient


class ChangelogGenerator:
    """
    Generates a professional changelog summarizing the project state.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate(self, routes: List[RouteInfo]) -> str:
        """
        Groups routes and generates a summary changelog.
        """
        if not routes:
            return "# Automated Changelog\n\nNo routes detected to summarize."

        frameworks = list(set([r.framework for r in routes]))
        total_routes = len(routes)

        # Group by feature (top-level path)
        features = {}
        for r in routes:
            parts = r.path.strip("/").split("/")
            f = parts[0] if parts else "root"
            features[f] = features.get(f, 0) + 1

        feature_summary = ", ".join([f"{k} ({v} routes)" for k, v in features.items()])

        prompt = f"""
Generate a professional **AUTOMATED CHANGELOG** for this project.
Tech Stack: {", ".join(frameworks)}
Total API Endpoints: {total_routes}
Feature Areas Detected: {feature_summary}

Include:
1. **Executive Summary**: High-level overview of the project's current maturity.
2. **Feature Breakdown**: Summarize the major functional areas discovered.
3. **Architecture Note**: Comment on the framework usage and endpoint distribution.
4. **Maintenance Note**: Auto-generated advisory on documentation currency.

Format as clean, readable Markdown.
"""
        if self.llm_client and self.llm_client.is_available():
            return self.llm_client.generate(prompt)

        return f"# Automated Changelog\n\nProject uses {", ".join(frameworks)} with {total_routes} endpoints across features: {feature_summary}."
