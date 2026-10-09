import re
from pathlib import Path


class RuleScanner:

    def scan_file(self, file_path: str, code: str):

        findings = []

        extension = Path(file_path).suffix.lower()

        findings.extend(
            self.security_rules(
                file_path,
                code,
                extension
            )
        )

        findings.extend(
            self.quality_rules(
                file_path,
                code,
                extension
            )
        )

        findings.extend(
            self.performance_rules(
                file_path,
                code,
                extension
            )
        )

        return findings

    # ==================================================
    # SECURITY
    # ==================================================

    def security_rules(
        self,
        file_path,
        code,
        extension
    ):

        findings = []

        # -----------------------------
        # Hardcoded passwords
        # -----------------------------

        password_pattern = re.compile(
            r'(?i)(password|passwd|pwd)'
            r'\s*=\s*["\'][^"\']+["\']'
        )

        for match in password_pattern.finditer(code):

            line = code[:match.start()].count("\n") + 1

            findings.append({
                "rule_id": "SEC001",
                "category": "Security",
                "severity": "HIGH",
                "title": "Hardcoded password",
                "file": file_path,
                "line": line,
                "description": (
                    "A password appears to be hardcoded "
                    "directly in source code."
                ),
                "recommendation": (
                    "Use environment variables or a "
                    "secret-management system."
                )
            })

        # -----------------------------
        # API keys / secrets
        # -----------------------------

        secret_pattern = re.compile(
            r'(?i)(api[_-]?key|secret|token)'
            r'\s*=\s*["\'][^"\']{8,}["\']'
        )

        for match in secret_pattern.finditer(code):

            line = code[:match.start()].count("\n") + 1

            findings.append({
                "rule_id": "SEC002",
                "category": "Security",
                "severity": "CRITICAL",
                "title": "Possible hardcoded secret",
                "file": file_path,
                "line": line,
                "description": (
                    "A possible API key, token or secret "
                    "is directly embedded in the source."
                ),
                "recommendation": (
                    "Move credentials to environment "
                    "variables or a secret manager."
                )
            })

        # -----------------------------
        # SQL SELECT *
        # -----------------------------

        for match in re.finditer(
            r"SELECT\s+\*",
            code,
            re.IGNORECASE
        ):

            line = code[:match.start()].count("\n") + 1

            findings.append({
                "rule_id": "QUAL001",
                "category": "Quality",
                "severity": "LOW",
                "title": "SELECT * detected",
                "file": file_path,
                "line": line,
                "description": (
                    "SELECT * retrieves every column "
                    "from the table."
                ),
                "recommendation": (
                    "Select only the columns required."
                )
            })

        # -----------------------------
        # Dangerous eval
        # -----------------------------

        if extension in {".py", ".js", ".ts"}:

            for match in re.finditer(
                r"\beval\s*\(",
                code
            ):

                line = code[:match.start()].count("\n") + 1

                findings.append({
                    "rule_id": "SEC003",
                    "category": "Security",
                    "severity": "HIGH",
                    "title": "Dangerous eval() usage",
                    "file": file_path,
                    "line": line,
                    "description": (
                        "eval() can execute dynamically "
                        "provided code."
                    ),
                    "recommendation": (
                        "Avoid eval() and use safer parsing "
                        "or execution mechanisms."
                    )
                })

        return findings

    # ==================================================
    # QUALITY
    # ==================================================

    def quality_rules(
        self,
        file_path,
        code,
        extension
    ):

        findings = []

        # -----------------------------
        # Debug print
        # -----------------------------

        if extension == ".py":

            for match in re.finditer(
                r"\bprint\s*\(",
                code
            ):

                line = code[:match.start()].count("\n") + 1

                findings.append({
                    "rule_id": "QUAL002",
                    "category": "Quality",
                    "severity": "LOW",
                    "title": "Debug print statement",
                    "file": file_path,
                    "line": line,
                    "description": (
                        "A print statement may be "
                        "leftover debugging code."
                    ),
                    "recommendation": (
                        "Use a proper logging framework."
                    )
                })

        # -----------------------------
        # Bare except
        # -----------------------------

        if extension == ".py":

            for match in re.finditer(
                r"\bexcept\s*:",
                code
            ):

                line = code[:match.start()].count("\n") + 1

                findings.append({
                    "rule_id": "QUAL003",
                    "category": "Quality",
                    "severity": "MEDIUM",
                    "title": "Bare except block",
                    "file": file_path,
                    "line": line,
                    "description": (
                        "Bare except catches every exception "
                        "and may hide programming errors."
                    ),
                    "recommendation": (
                        "Catch specific exception types."
                    )
                })

        # -----------------------------
        # TODO
        # -----------------------------

        for match in re.finditer(
            r"\bTODO\b",
            code,
            re.IGNORECASE
        ):

            line = code[:match.start()].count("\n") + 1

            findings.append({
                "rule_id": "QUAL004",
                "category": "Quality",
                "severity": "INFO",
                "title": "TODO comment",
                "file": file_path,
                "line": line,
                "description": (
                    "This code contains an unfinished "
                    "TODO item."
                ),
                "recommendation": (
                    "Resolve or track the TODO item."
                )
            })

        return findings

    # ==================================================
    # PERFORMANCE
    # ==================================================

    def performance_rules(
        self,
        file_path,
        code,
        extension
    ):

        findings = []

        # -----------------------------
        # Python nested loops
        # -----------------------------

        if extension == ".py":

            lines = code.splitlines()

            for index, line in enumerate(lines):

                if line.strip().startswith("for "):

                    indentation = len(line) - len(line.lstrip())

                    for next_line in lines[index + 1:index + 15]:

                        next_indent = (
                            len(next_line)
                            - len(next_line.lstrip())
                        )

                        if (
                            next_indent > indentation
                            and next_line.strip().startswith("for ")
                        ):

                            findings.append({
                                "rule_id": "PERF001",
                                "category": "Performance",
                                "severity": "MEDIUM",
                                "title": "Nested loop detected",
                                "file": file_path,
                                "line": index + 1,
                                "description": (
                                    "Nested loops can increase "
                                    "algorithmic complexity."
                                ),
                                "recommendation": (
                                    "Check whether the nested "
                                    "iteration can be optimized."
                                )
                            })

                            break

        return findings

    # ==================================================
    # WHOLE REPOSITORY
    # ==================================================

    def scan_repository(self, files):

        all_findings = []

        for file in files:

            findings = self.scan_file(
                file["path"],
                file["content"]
            )

            all_findings.extend(findings)

        return all_findings