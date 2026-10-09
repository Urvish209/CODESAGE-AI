import os
import json
import re
from typing import Dict

from groq import Groq


class AIFixService:

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

    # --------------------------------------------------
    # Clean AI JSON response
    # --------------------------------------------------

    def clean_json(self, text: str) -> str:

        text = text.strip()

        # Remove markdown code fences
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        )

        text = text.strip()

        # Find JSON object if AI added extra text
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:
            text = text[start:end + 1]

        return text

    # --------------------------------------------------
    # Generate Fix
    # --------------------------------------------------

    def generate_fix(
        self,
        file_path: str,
        code: str,
        issue: str,
        line: int | None = None
    ) -> Dict:

        # Keep request reasonably small
        code = code[:6000]

        prompt = f"""
You are Code Sage AI Auto Fix.

You are an expert software engineer.

Analyze the source code and fix the reported issue.

FILE:
{file_path}

LINE:
{line if line else "Not specified"}

ISSUE:
{issue}

SOURCE CODE:
{code}

IMPORTANT RULES:

1. Return ONLY one valid JSON object.
2. Do NOT use Markdown.
3. Do NOT use ```json.
4. Do NOT add explanations outside the JSON.
5. Preserve the original programming language.
6. Make the smallest reasonable change.
7. Do not change unrelated code.
8. Do not invent missing code.
9. If you cannot safely fix the issue, set "fixed"
   to false and explain why.

Return exactly this structure:

{{
    "fixed": true,
    "original_code": "original relevant code",
    "fixed_code": "corrected relevant code",
    "explanation": "explain the fix",
    "changes": [
        "change 1",
        "change 2"
    ]
}}
"""

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.1,

            max_tokens=1800
        )

        raw = response.choices[0].message.content

        if not raw:
            raise ValueError(
                "AI returned an empty response."
            )

        # Clean response
        cleaned = self.clean_json(raw)

        try:

            result = json.loads(cleaned)

        except json.JSONDecodeError as e:

            # Helpful error for debugging
            raise ValueError(
                f"AI returned invalid JSON: "
                f"{raw[:1000]}"
            ) from e

        # Validate expected fields
        return {
            "fixed": result.get(
                "fixed",
                False
            ),

            "original_code": result.get(
                "original_code",
                ""
            ),

            "fixed_code": result.get(
                "fixed_code",
                ""
            ),

            "explanation": result.get(
                "explanation",
                ""
            ),

            "changes": result.get(
                "changes",
                []
            )
        }