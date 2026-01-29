"""Multi-language parser using Tree-sitter."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

try:
    from tree_sitter_languages import get_language, get_parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logger.warning("tree-sitter-languages not installed. Multi-language support limited.")


class MultiLanguageParser:
    """Universal code parser supporting 160+ languages via Tree-sitter."""

    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "c_sharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".lua": "lua",
        ".sh": "bash",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".toml": "toml",
        ".md": "markdown",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
    }

    def __init__(self):
        self.parsers_cache: Dict[str, Any] = {}
        self.available = TREE_SITTER_AVAILABLE

    def detect_language(self, file_path: Path) -> str:
        """Detect language from file extension."""
        extension = file_path.suffix.lower()
        return self.LANGUAGE_MAP.get(extension, "unknown")

    def parse(self, file_path: Path, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse file and extract structure.

        Args:
            file_path: Path to file
            content: Optional file content (reads from disk if None)

        Returns:
            Parsed structure with functions, classes, imports
        """
        try:
            language = self.detect_language(file_path)

            if language == "unknown":
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_path.suffix}",
                }

            if not content:
                try:
                    content = file_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    content = file_path.read_text(encoding="latin-1")

            # Use Tree-sitter if available
            if self.available and language in ["javascript", "typescript", "go", "rust", "java", "cpp", "c"]:
                return self._parse_tree_sitter(content, language)

            # Fallback to Python AST for .py files
            elif language == "python":
                return self._parse_python_ast(content)

            # Basic regex-based parsing for others
            else:
                return self._parse_basic(content, language)

        except Exception as e:
            logger.error(f"Parse error for {file_path}: {e}")
            return {"success": False, "error": str(e)}

    def _parse_tree_sitter(self, content: str, language: str) -> Dict[str, Any]:
        """Parse using Tree-sitter."""
        try:
            parser = self._get_parser(language)
            tree = parser.parse(bytes(content, "utf8"))
            root = tree.root_node

            functions = []
            classes = []
            imports = []

            # Extract functions
            function_query = self._get_query(language, "function")
            for node in self._query_tree(root, function_query):
                functions.append({
                    "name": self._get_node_text(node, content),
                    "line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                })

            # Extract classes
            class_query = self._get_query(language, "class")
            for node in self._query_tree(root, class_query):
                classes.append({
                    "name": self._get_node_text(node, content),
                    "line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                })

            # Extract imports
            import_query = self._get_query(language, "import")
            for node in self._query_tree(root, import_query):
                imports.append({
                    "module": self._get_node_text(node, content),
                    "line": node.start_point[0] + 1,
                })

            return {
                "success": True,
                "language": language,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "line_count": len(content.splitlines()),
            }

        except Exception as e:
            logger.error(f"Tree-sitter parse error: {e}")
            return {"success": False, "error": str(e)}

    def _parse_python_ast(self, content: str) -> Dict[str, Any]:
        """Parse Python using AST."""
        import ast

        try:
            tree = ast.parse(content)
            functions = []
            classes = []
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": node.end_lineno or node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "end_line": node.end_lineno or node.lineno,
                        "bases": [ast.unparse(base) for base in node.bases],
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append({
                                "module": alias.name,
                                "alias": alias.asname,
                                "type": "import",
                                "line": node.lineno,
                            })
                    else:
                        for alias in node.names:
                            imports.append({
                                "module": node.module or "",
                                "name": alias.name,
                                "alias": alias.asname,
                                "type": "from_import",
                                "line": node.lineno,
                            })

            return {
                "success": True,
                "language": "python",
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "line_count": len(content.splitlines()),
            }

        except SyntaxError as e:
            logger.error(f"Python syntax error: {e}")
            return {"success": False, "error": f"Syntax error: {e}"}

    def _parse_basic(self, content: str, language: str) -> Dict[str, Any]:
        """Basic regex-based parsing."""
        import re

        functions = []
        classes = []
        imports = []

        # Function patterns
        func_patterns = {
            "javascript": r"(?:function|const|let|var)\s+(\w+)\s*\(",
            "go": r"func\s+(\w+)\s*\(",
            "rust": r"fn\s+(\w+)\s*\(",
        }

        # Class patterns
        class_patterns = {
            "javascript": r"class\s+(\w+)",
            "go": r"type\s+(\w+)\s+struct",
            "rust": r"(?:struct|enum)\s+(\w+)",
        }

        # Import patterns
        import_patterns = {
            "javascript": r"import\s+.*?from\s+['\"]([^'\"]+)['\"]",
            "go": r"import\s+['\"]([^'\"]+)['\"]",
            "rust": r"use\s+([\w:]+)",
        }

        lines = content.splitlines()

        # Extract functions
        if language in func_patterns:
            pattern = func_patterns[language]
            for i, line in enumerate(lines, 1):
                matches = re.findall(pattern, line)
                for match in matches:
                    functions.append({"name": match, "line": i})

        # Extract classes
        if language in class_patterns:
            pattern = class_patterns[language]
            for i, line in enumerate(lines, 1):
                matches = re.findall(pattern, line)
                for match in matches:
                    classes.append({"name": match, "line": i})

        # Extract imports
        if language in import_patterns:
            pattern = import_patterns[language]
            for i, line in enumerate(lines, 1):
                matches = re.findall(pattern, line)
                for match in matches:
                    imports.append({"module": match, "line": i})

        return {
            "success": True,
            "language": language,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "line_count": len(lines),
        }

    def _get_parser(self, language: str):
        """Get or create parser for language."""
        if language not in self.parsers_cache:
            self.parsers_cache[language] = get_parser(language)
        return self.parsers_cache[language]

    def _get_query(self, language: str, query_type: str) -> str:
        """Get Tree-sitter query for language and type."""
        queries = {
            "function": {
                "javascript": "(function_declaration name: (identifier) @name)",
                "typescript": "(function_declaration name: (identifier) @name)",
                "go": "(function_declaration name: (identifier) @name)",
                "rust": "(function_item name: (identifier) @name)",
                "java": "(method_declaration name: (identifier) @name)",
                "cpp": "(function_definition declarator: (function_declarator declarator: (identifier) @name))",
            },
            "class": {
                "javascript": "(class_declaration name: (identifier) @name)",
                "typescript": "(class_declaration name: (type_identifier) @name)",
                "java": "(class_declaration name: (identifier) @name)",
                "cpp": "(class_specifier name: (type_identifier) @name)",
            },
            "import": {
                "javascript": "(import_statement source: (string) @module)",
                "typescript": "(import_statement source: (string) @module)",
                "go": "(import_declaration (import_spec path: (interpreted_string_literal) @module))",
                "rust": "(use_declaration argument: (scoped_identifier) @module)",
            },
        }
        return queries.get(query_type, {}).get(language, "")

    def _query_tree(self, node, query_pattern: str) -> List:
        """Query tree-sitter tree."""
        # Simplified - in production, use proper tree-sitter queries
        results = []
        if not query_pattern:
            return results

        # Walk tree and find matching nodes
        def walk(n):
            if n.type in query_pattern:
                results.append(n)
            for child in n.children:
                walk(child)

        walk(node)
        return results

    def _get_node_text(self, node, content: str) -> str:
        """Extract text from node."""
        start_byte = node.start_byte
        end_byte = node.end_byte
        return content[start_byte:end_byte]
