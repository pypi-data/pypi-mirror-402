import json
from typing import List, Dict, Any
from autodg.modules.core.llm import LLMClient


class CodeReviewer:
    """
    Analyzes code for Security, Efficiency, and Quality improvements using AI.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def review_route(
        self, source_code: str, context_code: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Sends code to LLM to get a JSON list of line-by-line improvements.
        """
        context_str = "\n".join(
            [f"Function {name}:\n{code}" for name, code in context_code.items()]
        )

        prompt = f"""
Analyze the following Python web handler and its dependencies for:
1. **Security**: Identify vulnerabilities (SQLi, XSS, CSRF, insecure authentication, data leaks).
2. **Efficiency**: Suggest performance improvements (N+1 queries, heavy computations, caching).
3. **Quality**: Suggest better patterns, naming, or readability (Clean Code).

SOURCE CODE:
{source_code}

CONTEXT (Called functions):
{context_str}

### INSTRUCTIONS:
Return ONLY a valid JSON list of objects. No preamble, no explanation.
Each object MUST have:
- "line": (integer) The line number in the SOURCE CODE.
- "type": (string) "security", "efficiency", or "quality".
- "issue": (string) Short description of the problem.
- "suggestion": (string) Specific code or logical fix.

If no issues found, return [].
Example: [{{"line": 5, "type": "security", "issue": "Plaintext storage", "suggestion": "Use passlib to hash this"}}]
"""

        try:
            response = self.llm_client.generate(prompt)
            return self._parse_json_list(response)
        except Exception as e:
            print(f"Error during AI code review: {e}")

        return []

    def _parse_json_list(self, response: str) -> List[Dict[str, Any]]:
        """
        Robustly extract and parse a JSON list from LLM response.
        """
        import re

        # 1. Try to find markdown code block
        code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
        content = code_block.group(1) if code_block else response

        # 2. Find the largest [...] part
        start = content.find("[")
        end = content.rfind("]") + 1
        if start == -1 or end == 0:
            return []

        json_str = content[start:end].strip()

        # 3. Basic cleaning for common LLM errors (like trailing commas before closing braces/brackets)
        json_str = re.sub(r",\s*([\]}])", r"\1", json_str)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: try ast.literal_eval for single quote handling
            try:
                import ast

                val = ast.literal_eval(json_str)
                if isinstance(val, list):
                    return val
            except Exception:
                pass

            print(f"Failed to decode JSON from AI response: {json_str[:100]}...")
            return []
