"""Error parsing and analysis."""

import re
from typing import Any, Dict, List, Optional

from loguru import logger


class ErrorParser:
    """Parse and structure error messages from code execution."""

    # Python traceback patterns
    PYTHON_TRACEBACK_PATTERN = re.compile(
        r"File\s+[\"']([^\"']+)[\"'],\s+line\s+(\d+).*?\n\s*([A-Za-z]+(?:Error|Exception|Warning)):\s*(.+)",
        re.MULTILINE | re.DOTALL,
    )

    # Python simple error pattern
    PYTHON_SIMPLE_ERROR = re.compile(
        r"([A-Za-z]+(?:Error|Exception|Warning)):\s*(.+)"
    )

    # JavaScript/TypeScript error patterns
    JS_ERROR_PATTERN = re.compile(
        r"([A-Za-z]+Error):\s*(.+?)\s+at\s+(.+?):(\d+):(\d+)", re.MULTILINE
    )

    # Java compiler error pattern
    JAVA_ERROR_PATTERN = re.compile(
        r"([^:]+):(\d+):\s+error:\s*(.+)", re.MULTILINE
    )

    # C++ compiler error pattern
    CPP_ERROR_PATTERN = re.compile(
        r"([^:]+):(\d+):(\d+):\s+(error|warning):\s*(.+)", re.MULTILINE
    )

    def parse_errors(
        self, error_output: str, file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse error output and extract structured information.

        Args:
            error_output: Error message string (from stderr or stdout)
            file_path: Optional file path for context

        Returns:
            Dict with errors[], summary{}, suggestions[]
        """
        try:
            if not error_output or not error_output.strip():
                return {
                    "success": False,
                    "error": "Empty error output",
                }

            errors = []
            language = self._detect_language(error_output, file_path)

            # Parse based on language
            if language == "python":
                errors = self._parse_python_errors(error_output)
            elif language in ["javascript", "typescript"]:
                errors = self._parse_js_errors(error_output)
            elif language == "java":
                errors = self._parse_java_errors(error_output)
            elif language in ["cpp", "c"]:
                errors = self._parse_cpp_errors(error_output)
            else:
                # Generic parsing
                errors = self._parse_generic_errors(error_output)

            # Generate summary
            summary = self._generate_summary(errors)

            # Generate suggestions
            suggestions = self._generate_suggestions(errors, language)

            return {
                "success": True,
                "language": language,
                "errors": errors,
                "summary": summary,
                "suggestions": suggestions,
                "total_errors": len(errors),
            }

        except Exception as e:
            logger.error(f"Error parsing failed: {e}")
            return {"success": False, "error": str(e)}

    def _detect_language(
        self, error_output: str, file_path: Optional[str]
    ) -> str:
        """Detect language from error output or file path."""
        if file_path:
            from pathlib import Path
            ext = Path(file_path).suffix.lower()
            lang_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".java": "java",
                ".cpp": "cpp",
                ".cxx": "cpp",
                ".cc": "cpp",
                ".c": "c",
            }
            if ext in lang_map:
                return lang_map[ext]

        # Detect from error patterns
        if "Traceback" in error_output or ("File" in error_output and "line" in error_output):
            return "python"
        elif "SyntaxError" in error_output or "ReferenceError" in error_output:
            return "javascript"
        elif "error:" in error_output and ".java:" in error_output:
            return "java"
        elif "error:" in error_output and (".cpp:" in error_output or ".c:" in error_output):
            return "cpp"

        return "unknown"

    def _parse_python_errors(self, error_output: str) -> List[Dict[str, Any]]:
        """Parse Python traceback errors."""
        errors = []

        # Try full traceback pattern
        matches = self.PYTHON_TRACEBACK_PATTERN.finditer(error_output)
        for match in matches:
            errors.append(
                {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "error_type": match.group(3),
                    "message": match.group(4).strip(),
                    "language": "python",
                }
            )

        # If no matches, try simple error pattern
        if not errors:
            match = self.PYTHON_SIMPLE_ERROR.search(error_output)
            if match:
                errors.append(
                    {
                        "file": None,
                        "line": None,
                        "error_type": match.group(1),
                        "message": match.group(2).strip(),
                        "language": "python",
                    }
                )

        return errors

    def _parse_js_errors(self, error_output: str) -> List[Dict[str, Any]]:
        """Parse JavaScript/TypeScript errors."""
        errors = []
        matches = self.JS_ERROR_PATTERN.finditer(error_output)

        for match in matches:
            errors.append(
                {
                    "file": match.group(3),
                    "line": int(match.group(4)),
                    "column": int(match.group(5)),
                    "error_type": match.group(1),
                    "message": match.group(2).strip(),
                    "language": "javascript",
                }
            )

        return errors

    def _parse_java_errors(self, error_output: str) -> List[Dict[str, Any]]:
        """Parse Java compiler errors."""
        errors = []
        matches = self.JAVA_ERROR_PATTERN.finditer(error_output)

        for match in matches:
            errors.append(
                {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "error_type": "compilation error",
                    "message": match.group(3).strip(),
                    "language": "java",
                }
            )

        return errors

    def _parse_cpp_errors(self, error_output: str) -> List[Dict[str, Any]]:
        """Parse C++ compiler errors."""
        errors = []
        matches = self.CPP_ERROR_PATTERN.finditer(error_output)

        for match in matches:
            errors.append(
                {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "column": int(match.group(3)),
                    "error_type": match.group(4),
                    "message": match.group(5).strip(),
                    "language": "cpp",
                }
            )

        return errors

    def _parse_generic_errors(self, error_output: str) -> List[Dict[str, Any]]:
        """Parse generic errors (fallback)."""
        # Look for common error patterns
        lines = error_output.splitlines()
        errors = []

        for i, line in enumerate(lines):
            # Look for lines with "error" or "Error"
            if "error" in line.lower() or "Error" in line:
                errors.append(
                    {
                        "file": None,
                        "line": i + 1,
                        "error_type": "error",
                        "message": line.strip(),
                        "language": "unknown",
                    }
                )

        return errors[:10]  # Limit to 10 generic errors

    def _generate_summary(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate error summary."""
        if not errors:
            return {"total": 0, "by_type": {}, "by_file": {}}

        by_type = {}
        by_file = {}

        for error in errors:
            error_type = error.get("error_type", "unknown")
            by_type[error_type] = by_type.get(error_type, 0) + 1

            file_path = error.get("file")
            if file_path:
                by_file[file_path] = by_file.get(file_path, 0) + 1

        return {
            "total": len(errors),
            "by_type": by_type,
            "by_file": by_file,
        }

    def _generate_suggestions(
        self, errors: List[Dict[str, Any]], language: str
    ) -> List[str]:
        """Generate fix suggestions based on errors."""
        suggestions = []

        if not errors:
            return suggestions

        # Common error suggestions
        error_messages = " ".join([e.get("message", "").lower() for e in errors])

        if language == "python":
            if "indentationerror" in error_messages or "indentation" in error_messages:
                suggestions.append("Check indentation - Python is indentation-sensitive")
            if "nameerror" in error_messages or "name" in error_messages:
                suggestions.append("Check variable/function names - may be undefined or typo")
            if "syntaxerror" in error_messages:
                suggestions.append("Check syntax - missing colon, parenthesis, or quote?")
            if "importerror" in error_messages or "modulenotfounderror" in error_messages:
                suggestions.append("Check imports - module may not be installed or path incorrect")
            if "typeerror" in error_messages:
                suggestions.append("Check types - may be passing wrong type to function")
            if "attributeerror" in error_messages:
                suggestions.append("Check object attributes - may be accessing non-existent attribute")

        elif language in ["javascript", "typescript"]:
            if "syntaxerror" in error_messages:
                suggestions.append("Check JavaScript syntax - missing semicolon, bracket, or quote?")
            if "referenceerror" in error_messages:
                suggestions.append("Check variable references - may be undefined or out of scope")
            if "typeerror" in error_messages:
                suggestions.append("Check types - may be calling method on wrong type")

        elif language == "java":
            if "cannot find symbol" in error_messages:
                suggestions.append("Check imports and class names - symbol may not be imported")
            if "cannot resolve symbol" in error_messages:
                suggestions.append("Check variable/class names - may be typo or missing declaration")

        elif language in ["cpp", "c"]:
            if "undefined reference" in error_messages:
                suggestions.append("Check linking - may need to link library or check function signatures")
            if "expected" in error_messages:
                suggestions.append("Check syntax - may be missing semicolon, bracket, or parenthesis")

        # Generic suggestions
        if not suggestions:
            suggestions.append("Review error messages carefully - check file paths and line numbers")
            suggestions.append("Ensure all required dependencies are installed")
            suggestions.append("Check for typos in variable/function names")

        return suggestions

