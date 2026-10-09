import os
import re
from typing import Dict

from groq import Groq

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Preformatted
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm


class DocumentationService:

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

    # ==================================================
    # BUILD PDF
    # ==================================================

    def create_pdf(
        self,
        report: str,
        output_path: str,
        title: str
    ):

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm
        )

        styles = getSampleStyleSheet()

        title_style = styles["Title"]
        title_style.alignment = TA_LEFT

        heading_style = styles["Heading2"]
        heading3_style = styles["Heading3"]
        body_style = styles["BodyText"]

        story = []

        story.append(
            Paragraph(
                title,
                title_style
            )
        )

        story.append(
            Spacer(1, 12)
        )

        lines = report.split("\n")

        for line in lines:

            line = line.strip()

            if not line:

                story.append(
                    Spacer(1, 6)
                )

                continue

            # ==========================================
            # CODE BLOCK
            # ==========================================

            if line.startswith("```"):

                continue

            # ==========================================
            # H3
            # ==========================================

            if line.startswith("### "):

                text = line[4:]

                story.append(
                    Paragraph(
                        text,
                        heading3_style
                    )
                )

            # ==========================================
            # H2
            # ==========================================

            elif line.startswith("## "):

                text = line[3:]

                story.append(
                    Paragraph(
                        text,
                        heading_style
                    )
                )

            # ==========================================
            # H1
            # ==========================================

            elif line.startswith("# "):

                text = line[2:]

                story.append(
                    Paragraph(
                        text,
                        title_style
                    )
                )

            # ==========================================
            # BULLET
            # ==========================================

            elif line.startswith("- "):

                text = line[2:]

                story.append(
                    Paragraph(
                        "• " + text,
                        body_style
                    )
                )

            # ==========================================
            # NORMAL TEXT
            # ==========================================

            else:

                text = line

                # Bold markdown
                text = re.sub(
                    r"\*\*(.*?)\*\*",
                    r"<b>\1</b>",
                    text
                )

                # Inline code
                text = text.replace(
                    "`",
                    ""
                )

                story.append(
                    Paragraph(
                        text,
                        body_style
                    )
                )

        doc.build(story)

    # ==================================================
    # BUILD REPOSITORY CONTEXT
    # ==================================================

    def build_context(
        self,
        repository: Dict,
        max_files: int = 8,
        max_chars_per_file: int = 1800
    ) -> str:

        parts = []

        parts.append(
            f"Repository: "
            f"{repository.get('owner')}/"
            f"{repository.get('repository')}"
        )

        parts.append(
            f"Branch: {repository.get('branch')}"
        )

        parts.append(
            f"Language: {repository.get('language')}"
        )

        parts.append(
            "\nSOURCE FILES:\n"
        )

        files = repository.get(
            "files",
            []
        )

        count = 0

        for file in files:

            if count >= max_files:
                break

            path = file.get(
                "path",
                ""
            )

            content = file.get(
                "content",
                ""
            )

            if not content:
                continue

            parts.append(
                f"\n===== FILE: {path} =====\n"
            )

            parts.append(
                content[:max_chars_per_file]
            )

            count += 1

        return "\n".join(parts)

    # ==================================================
    # GENERATE DOCUMENTATION
    # ==================================================

    def generate(
        self,
        report_type: str,
        repository: Dict
    ) -> str:

        context = self.build_context(
            repository
        )

        # ==========================================
        # SRS
        # ==========================================

        if report_type == "srs":

            instructions = """

Generate a professional Software Requirements Specification (SRS).

Include:

1. Introduction
2. Purpose
3. Scope
4. Project Overview
5. User Types / Actors
6. Functional Requirements
7. Non-Functional Requirements
8. System Features
9. Technology Requirements
10. External Interfaces
11. Security Requirements
12. Performance Requirements
13. Constraints
14. Assumptions
15. Future Scope

Use information that can actually be determined from the repository.

Clearly mark anything that cannot be determined.

Do not invent functionality.

"""

        # ==========================================
        # PROJECT SNAPSHOT
        # ==========================================

        elif report_type == "snapshot":

            instructions = """

Generate a concise ONE-PAGE PROJECT SNAPSHOT.

Include:

# Project Name

## What This Project Does

Explain the repository in very simple language.

## Problem It Solves

## How It Works

Give a short processing flow.

## Technology Stack

## Main Components

## Key Features

## Project Health

Give a simple qualitative assessment of:

- Security
- Code Quality
- Performance
- Architecture

## In One Sentence

Finish with one simple sentence describing the entire project.

Keep this concise enough for a one-page report.

"""

        # ==========================================
        # EVOLUTION
        # ==========================================

        elif report_type == "evolution":

            instructions = """

Generate an Evolution & Fix Plan for this repository.

Include:

# Current Project State

# Current Problems

Identify problems that can actually be supported by the provided source code.

For every important problem include:

- Problem
- Location
- Why it matters
- Priority

# Recommended Fixes

Give practical improvements.

# Future Features

Suggest useful future functionality.

# Security Improvements

# Performance Improvements

# Architecture Improvements

# Testing Improvements

# Development Roadmap

Divide the roadmap into:

1. Immediate
2. Short Term
3. Long Term

IMPORTANT:

Clearly distinguish between:

EXISTING FUNCTIONALITY

and

RECOMMENDED FUTURE IMPROVEMENTS.

Do not claim a future feature already exists.

"""

        else:

            raise ValueError(
                "Invalid report type."
            )

        # ==========================================
        # PROMPT
        # ==========================================

        prompt = f"""

You are Code Sage AI Repository Documentation Generator.

Repository:

{context}

TASK:

{instructions}

RULES:

1. Use only the repository information provided.
2. Do not invent files or features.
3. Do not claim that unseen files were inspected.
4. Use Markdown.
5. Be professional and technically accurate.
6. Use clear headings.
7. Do not include conversational text before or after the report.

Generate the report now.

"""

        # ==========================================
        # GROQ
        # ==========================================

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.2,

            max_tokens=3000
        )

        result = (
            response
            .choices[0]
            .message
            .content
        )

        if not result:

            raise ValueError(
                "AI returned an empty documentation report."
            )

        return result