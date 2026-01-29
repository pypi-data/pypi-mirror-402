"""Code analysis tools - inspect, analyze, dependencies."""

from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from .parser import MultiLanguageParser
from ..languages.python import PythonEditor


class CodeAnalyzer:
    """Unified code analysis for all languages."""

    def __init__(self):
        self.parser = MultiLanguageParser()
        self.python_editor = PythonEditor()

    def inspect(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze code structure (functions, classes, imports).
        Auto-detects language.

        Returns:
            Dict with functions, classes, imports, line_count
        """
        try:
            result = self.parser.parse(file_path)

            if not result.get("success"):
                return result

            # Format output concisely for token efficiency
            summary = {
                "file": str(file_path),
                "language": result["language"],
                "line_count": result["line_count"],
                "functions": len(result["functions"]),
                "classes": len(result["classes"]),
                "imports": len(result["imports"]),
            }

            # Include details (limited to first 50 for token efficiency)
            MAX_ITEMS = 50
            details = {
                "functions": result["functions"][:MAX_ITEMS],
                "classes": result["classes"][:MAX_ITEMS],
                "imports": result["imports"][:MAX_ITEMS],
            }

            # Add truncation warnings
            if len(result["functions"]) > MAX_ITEMS:
                details["functions_truncated"] = len(result["functions"]) - MAX_ITEMS
            if len(result["classes"]) > MAX_ITEMS:
                details["classes_truncated"] = len(result["classes"]) - MAX_ITEMS
            if len(result["imports"]) > MAX_ITEMS:
                details["imports_truncated"] = len(result["imports"]) - MAX_ITEMS

            return {"success": True, "summary": summary, "details": details}

        except Exception as e:
            logger.error(f"Inspect failed for {file_path}: {e}")
            return {"success": False, "error": str(e)}

    def analyze(self, file_path: Path) -> Dict[str, Any]:
        """
        Deep quality analysis (complexity, smells, metrics).
        Currently Python-only, expandable to other languages.

        Returns:
            Dict with quality metrics and code smells
        """
        try:
            language = self.parser.detect_language(file_path)

            if language != "python":
                return {
                    "success": False,
                    "error": f"Deep analysis not yet supported for {language}",
                }

            content = file_path.read_text(encoding="utf-8")

            # Get metrics
            complexity = self.python_editor.get_complexity(content)
            function_metrics = self.python_editor.get_function_metrics(content)
            code_smells = self.python_editor.find_code_smells(content)

            # Summary for token efficiency
            summary = {
                "file": str(file_path),
                "language": language,
                "complexity": complexity,
                "function_count": len(function_metrics),
                "smell_count": len(code_smells),
                "high_complexity_functions": len(
                    [f for f in function_metrics if f.get("complexity", 0) > 10]
                ),
                "missing_docstrings": len(
                    [f for f in function_metrics if not f.get("has_docstring")]
                ),
                "missing_type_hints": len(
                    [f for f in function_metrics if not f.get("has_type_hints")]
                ),
            }

            # Limit details to top issues
            MAX_ITEMS = 20
            details = {
                "top_smells": code_smells[:MAX_ITEMS],
                "complex_functions": [
                    f for f in function_metrics if f.get("complexity", 0) > 5
                ][:MAX_ITEMS],
            }

            if len(code_smells) > MAX_ITEMS:
                details["smells_truncated"] = len(code_smells) - MAX_ITEMS

            return {"success": True, "summary": summary, "details": details}

        except Exception as e:
            logger.error(f"Analyze failed for {file_path}: {e}")
            return {"success": False, "error": str(e)}

    def dependencies(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze imports and dependencies.

        Returns:
            Dict with imports categorized by type
        """
        try:
            result = self.parser.parse(file_path)

            if not result.get("success"):
                return result

            imports = result.get("imports", [])

            # Categorize imports
            stdlib = []
            third_party = []
            local = []

            # Simple heuristic (can be improved with package metadata)
            for imp in imports:
                module = imp.get("module", "")
                if not module:
                    continue

                # Local imports (start with .)
                if module.startswith("."):
                    local.append(imp)
                # Common stdlib modules
                elif any(
                    module.startswith(lib)
                    for lib in [
                        "os",
                        "sys",
                        "re",
                        "json",
                        "datetime",
                        "pathlib",
                        "typing",
                        "collections",
                        "itertools",
                        "functools",
                    ]
                ):
                    stdlib.append(imp)
                else:
                    third_party.append(imp)

            summary = {
                "file": str(file_path),
                "language": result["language"],
                "total_imports": len(imports),
                "stdlib": len(stdlib),
                "third_party": len(third_party),
                "local": len(local),
            }

            # Unique modules
            unique_modules = list(set(imp.get("module", "") for imp in imports))

            return {
                "success": True,
                "summary": summary,
                "details": {
                    "stdlib": stdlib[:30],
                    "third_party": third_party[:30],
                    "local": local[:30],
                    "unique_modules": unique_modules[:50],
                },
            }

        except Exception as e:
            logger.error(f"Dependencies analysis failed for {file_path}: {e}")
            return {"success": False, "error": str(e)}

    def suggest_improvements(self, file_path: Path) -> Dict[str, Any]:
        """
        Suggest code improvements based on analysis.

        Returns:
            List of actionable suggestions
        """
        try:
            # Run analysis first
            analysis = self.analyze(file_path)

            if not analysis.get("success"):
                return analysis

            suggestions = []
            summary = analysis["summary"]

            # High complexity
            if summary["complexity"] > 20:
                suggestions.append(
                    {
                        "type": "high_complexity",
                        "severity": "warning",
                        "message": f"File has high complexity ({summary['complexity']})",
                        "suggestion": "Consider breaking down into smaller modules",
                    }
                )

            # Missing docstrings
            if summary["missing_docstrings"] > 0:
                suggestions.append(
                    {
                        "type": "missing_docstrings",
                        "severity": "info",
                        "message": f"{summary['missing_docstrings']} functions missing docstrings",
                        "suggestion": "Add docstrings for better documentation",
                    }
                )

            # Missing type hints
            if summary["missing_type_hints"] > 0:
                suggestions.append(
                    {
                        "type": "missing_type_hints",
                        "severity": "info",
                        "message": f"{summary['missing_type_hints']} functions missing type hints",
                        "suggestion": "Add type hints with: edit(mode='ast', transform='add_type_hints')",
                    }
                )

            # Code smells
            if summary["smell_count"] > 5:
                suggestions.append(
                    {
                        "type": "code_smells",
                        "severity": "warning",
                        "message": f"Found {summary['smell_count']} code smells",
                        "suggestion": "Run analyze() for details and fix top issues",
                    }
                )

            return {"success": True, "suggestions": suggestions}

        except Exception as e:
            logger.error(f"Suggestions failed for {file_path}: {e}")
            return {"success": False, "error": str(e)}
