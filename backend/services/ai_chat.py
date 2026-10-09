import os
from typing import List, Dict, Optional

from groq import Groq


class AIChatService:

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
    # Build small repository context
    # --------------------------------------------------

    def build_context(
        self,
        repository: Dict,
        max_files: int = 5,
        max_chars_per_file: int = 1500
    ) -> str:

        parts = []

        owner = repository.get("owner", "")
        repo = repository.get("repository", "")
        branch = repository.get("branch", "")

        parts.append(
            f"Repository: {owner}/{repo}"
        )

        parts.append(
            f"Branch: {branch}"
        )

        parts.append(
            "\nRepository source code:\n"
        )

        files = repository.get("files", [])

        files_added = 0

        for file in files:

            if files_added >= max_files:
                break

            path = file.get("path", "")
            content = file.get("content", "")

            if not content:
                continue

            # Keep each file very small
            content = content[:max_chars_per_file]

            parts.append(
                f"\n--- FILE: {path} ---\n"
            )

            parts.append(content)

            files_added += 1

        return "\n".join(parts)

    # --------------------------------------------------
    # Ask AI
    # --------------------------------------------------

    def ask(
        self,
        question: str,
        repository: Dict,
        conversation_history: Optional[List[Dict]] = None
    ):

        # Limit repository context
        context = self.build_context(
            repository,
            max_files=5,
            max_chars_per_file=1500
        )

        system_prompt = f"""
You are Code Sage AI.

You are an AI software developer assistant
analyzing a GitHub repository.

Repository:
{repository.get("owner", "")}/{repository.get("repository", "")}

Branch:
{repository.get("branch", "")}

Answer the user's question using the provided
repository code.

Rules:

- Do not invent files or functions.
- Do not claim to have seen code that was not provided.
- Mention file names when relevant.
- If the available code is insufficient, say so.
- Give practical programming explanations.
- For bugs, explain the problem and possible fix.
- For code changes, provide useful code.

Repository context:

{context}
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        # --------------------------------------------------
        # Add only a small amount of chat history
        # --------------------------------------------------

        if conversation_history:

            for message in conversation_history[-2:]:

                role = message.get("role")

                if role not in {"user", "assistant"}:
                    continue

                content = message.get(
                    "content",
                    ""
                )

                # Keep history small
                content = content[:800]

                messages.append(
                    {
                        "role": role,
                        "content": content
                    }
                )

        # --------------------------------------------------
        # Current question
        # --------------------------------------------------

        messages.append(
            {
                "role": "user",
                "content": question[:1500]
            }
        )

        # --------------------------------------------------
        # Groq request
        # --------------------------------------------------

        response = self.client.chat.completions.create(

            model=self.model,

            messages=messages,

            temperature=0.2,

            max_tokens=800
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer,
            "model": self.model,
            "repository": (
                f"{repository.get('owner', '')}/"
                f"{repository.get('repository', '')}"
            )
        }