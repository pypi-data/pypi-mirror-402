from typing import List
from autodg.modules.core.models import RouteInfo
from autodg.modules.core.llm import LLMClient


class FeatureAnalyzer:
    """
    Groups routes into high-level features and generates User Stories.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate_feature_docs(self, routes: List[RouteInfo]) -> str:
        """
        Groups routes by their base path and generates a feature-wise summary with user stories.
        """
        # Group by first part of path (e.g. /auth/login -> auth)
        groups = {}
        for r in routes:
            parts = r.path.strip("/").split("/")
            feature = parts[0] if parts else "root"
            if feature not in groups:
                groups[feature] = []
            groups[feature].append(r)

        summary = ["# Feature-Wise Documentation & User Stories\n"]

        for feature, feature_routes in groups.items():
            route_details = "\n".join(
                [f"- {r.methods} {r.path} ({r.handler_name})" for r in feature_routes]
            )

            prompt = f"""
Given the following API routes for the feature '{feature}':
{route_details}

Generate:
1. **Feature Description**: A concise explanation of what this feature does for the business.
2. **User Stories**: A list of user stories in the format 'As a [role], I want to [action], so that [value]'.
3. **Acceptance Criteria**: Key validations or outcomes needed for this feature.

Format as Markdown for a technical documentation.
"""
            if self.llm_client and self.llm_client.is_available():
                ai_content = self.llm_client.generate(prompt)
                summary.append(f"## Feature: {feature.capitalize()}")
                summary.append(ai_content)
                summary.append("\n---\n")
            else:
                summary.append(
                    f"## Feature: {feature.capitalize()} (AI Summary Unavailable)"
                )

        return "\n".join(summary)
