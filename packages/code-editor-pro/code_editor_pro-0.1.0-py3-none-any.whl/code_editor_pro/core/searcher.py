"""Multi-file code search functionality."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class CodeSearcher:
    """Search across multiple files in a project."""

    # Common ignore patterns
    IGNORE_PATTERNS = [
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".egg-info",
    ]

    # Binary file extensions to skip
    BINARY_EXTENSIONS = {
        ".pyc",
        ".pyo",
        ".so",
        ".dll",
        ".exe",
        ".bin",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
    }

    def search_across_files(
        self,
        pattern: str,
        project_path: str,
        file_extensions: Optional[List[str]] = None,
        use_regex: bool = False,
    ) -> Dict[str, Any]:
        """
        Search for pattern across multiple files.

        Args:
            pattern: Search pattern (regex or plain text)
            project_path: Root directory to search
            file_extensions: Optional list of file extensions to filter (e.g., [".py", ".js"])
            use_regex: If True, treat pattern as regex; otherwise plain text search

        Returns:
            Dict with matches grouped by file
        """
        try:
            project_dir = Path(project_path)

            if not project_dir.exists() or not project_dir.is_dir():
                return {
                    "success": False,
                    "error": f"Project path not found or not a directory: {project_path}",
                }

            # Compile regex if needed
            if use_regex:
                try:
                    regex = re.compile(pattern, re.IGNORECASE)
                except re.error as e:
                    return {"success": False, "error": f"Invalid regex pattern: {e}"}
            else:
                # Escape special regex characters for plain text search
                escaped_pattern = re.escape(pattern)
                regex = re.compile(escaped_pattern, re.IGNORECASE)

            matches_by_file: Dict[str, List[Dict[str, Any]]] = {}
            total_matches = 0
            files_searched = 0
            MAX_MATCHES_PER_FILE = 100
            MAX_TOTAL_MATCHES = 500

            # Walk directory tree
            for file_path in project_dir.rglob("*"):
                # Skip directories
                if file_path.is_dir():
                    continue

                # Skip ignored patterns
                if self._should_ignore(file_path, project_dir):
                    continue

                # Filter by extension if specified
                if file_extensions:
                    ext_lower = file_path.suffix.lower()
                    if ext_lower not in [e.lower() for e in file_extensions]:
                        continue

                # Skip binary files
                if file_path.suffix.lower() in self.BINARY_EXTENSIONS:
                    continue

                # Search in file
                try:
                    file_matches = self._search_in_file(file_path, regex)
                    if file_matches:
                        matches_by_file[str(file_path)] = file_matches
                        total_matches += len(file_matches)
                        files_searched += 1

                        # Stop if we hit total limit
                        if total_matches >= MAX_TOTAL_MATCHES:
                            break

                except Exception as e:
                    logger.debug(f"Error searching {file_path}: {e}")
                    continue

            # Limit matches per file and format results
            formatted_matches = {}
            remaining_total = MAX_TOTAL_MATCHES

            for file_path_str, file_matches in matches_by_file.items():
                limited_matches = file_matches[: min(MAX_MATCHES_PER_FILE, remaining_total)]
                formatted_matches[file_path_str] = limited_matches
                remaining_total -= len(limited_matches)

                if remaining_total <= 0:
                    break

            return {
                "success": True,
                "pattern": pattern,
                "matches_by_file": formatted_matches,
                "total_matches": min(total_matches, MAX_TOTAL_MATCHES),
                "files_searched": files_searched,
                "files_with_matches": len(formatted_matches),
                "truncated": total_matches > MAX_TOTAL_MATCHES,
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"success": False, "error": str(e)}

    def _should_ignore(self, file_path: Path, project_root: Path) -> bool:
        """Check if file should be ignored."""
        # Check if any part of the path matches ignore patterns
        relative_path = file_path.relative_to(project_root)
        path_parts = relative_path.parts

        for part in path_parts:
            if part in self.IGNORE_PATTERNS:
                return True

        return False

    def _search_in_file(
        self, file_path: Path, regex: re.Pattern
    ) -> List[Dict[str, Any]]:
        """Search for pattern in a single file."""
        try:
            # Try to read as text
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Skip binary files
                return []

            matches = []
            lines = content.splitlines()

            for line_num, line in enumerate(lines, start=1):
                for match in regex.finditer(line):
                    # Get context (surrounding characters)
                    start = max(0, match.start() - 20)
                    end = min(len(line), match.end() + 20)
                    context = line[start:end]

                    matches.append(
                        {
                            "line_number": line_num,
                            "line_content": line,
                            "match_start": match.start(),
                            "match_end": match.end(),
                            "match_text": match.group(),
                            "context": context,
                        }
                    )

            return matches

        except Exception as e:
            logger.debug(f"Error reading {file_path}: {e}")
            return []

