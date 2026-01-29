"""Core code editing with hybrid string/AST approach."""

import difflib
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from loguru import logger


class EditOperation:
    """Represents a single edit operation."""

    def __init__(
        self,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
        line_range: Optional[Tuple[int, int]] = None,
    ):
        self.old_string = old_string
        self.new_string = new_string
        self.replace_all = replace_all
        self.line_range = line_range


class CodeEditor:
    """Hybrid code editor with string and AST-based editing."""

    def __init__(self):
        self.undo_stack: List[Tuple[Path, str]] = []
        self.max_undo_stack = 50

    def edit(
        self,
        file_path: Path,
        old_string: str,
        new_string: str,
        mode: Literal["auto", "string", "ast"] = "auto",
        replace_all: bool = False,
    ) -> Dict[str, Any]:
        """
        Edit code with automatic mode selection.

        Args:
            file_path: Path to file
            old_string: String to replace
            new_string: Replacement string
            mode: Edit mode (auto/string/ast)
            replace_all: Replace all occurrences

        Returns:
            Result dict with success status and details
        """
        try:
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            # Read file
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="latin-1")

            # Save to undo stack
            self._push_undo(file_path, content)

            # Auto-detect mode
            if mode == "auto":
                mode = self._detect_mode(file_path, content, old_string)

            # Execute edit
            if mode == "string":
                new_content, changes = self._string_edit(
                    content, old_string, new_string, replace_all
                )
            elif mode == "ast":
                new_content, changes = self._ast_edit(
                    content, old_string, new_string, file_path
                )
            else:
                return {"success": False, "error": f"Unknown mode: {mode}"}

            # Validate edit
            if not changes:
                return {
                    "success": False,
                    "error": "No matches found",
                    "old_string": old_string,
                }

            # Write file
            file_path.write_text(new_content, encoding="utf-8")

            return {
                "success": True,
                "mode": mode,
                "changes": changes,
                "file_path": str(file_path),
            }

        except Exception as e:
            logger.error(f"Edit failed: {e}")
            return {"success": False, "error": str(e)}

    def preview(
        self,
        file_path: Path,
        operations: List[EditOperation],
    ) -> Dict[str, Any]:
        """
        Preview changes before applying.

        Args:
            file_path: Path to file
            operations: List of edit operations

        Returns:
            Unified diff and metadata
        """
        try:
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            content = file_path.read_text(encoding="utf-8")
            new_content = content

            # Apply all operations
            for op in operations:
                if op.replace_all:
                    new_content = new_content.replace(op.old_string, op.new_string)
                else:
                    new_content = new_content.replace(
                        op.old_string, op.new_string, 1
                    )

            # Generate diff
            diff = list(
                difflib.unified_diff(
                    content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=str(file_path),
                    tofile=f"{file_path} (modified)",
                    lineterm="",
                )
            )

            return {
                "success": True,
                "diff": "".join(diff),
                "operations_count": len(operations),
                "lines_changed": len([line for line in diff if line.startswith(("+", "-"))]),
            }

        except Exception as e:
            logger.error(f"Preview failed: {e}")
            return {"success": False, "error": str(e)}

    def apply(
        self,
        file_path: Path,
        operations: List[EditOperation],
    ) -> Dict[str, Any]:
        """
        Apply multiple edit operations atomically.

        Args:
            file_path: Path to file
            operations: List of edit operations

        Returns:
            Result with success status
        """
        try:
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            content = file_path.read_text(encoding="utf-8")
            self._push_undo(file_path, content)

            new_content = content
            changes_count = 0

            # Apply all operations
            for op in operations:
                if op.replace_all:
                    count = new_content.count(op.old_string)
                    new_content = new_content.replace(op.old_string, op.new_string)
                    changes_count += count
                else:
                    if op.old_string in new_content:
                        new_content = new_content.replace(
                            op.old_string, op.new_string, 1
                        )
                        changes_count += 1

            # Write file
            file_path.write_text(new_content, encoding="utf-8")

            return {
                "success": True,
                "changes": changes_count,
                "operations": len(operations),
                "file_path": str(file_path),
            }

        except Exception as e:
            logger.error(f"Apply failed: {e}")
            return {"success": False, "error": str(e)}

    def undo(self, file_path: Path) -> Dict[str, Any]:
        """
        Undo last edit on file.

        Args:
            file_path: Path to file

        Returns:
            Result with success status
        """
        try:
            # Find last undo entry for this file
            for i in range(len(self.undo_stack) - 1, -1, -1):
                path, content = self.undo_stack[i]
                if path == file_path:
                    file_path.write_text(content, encoding="utf-8")
                    self.undo_stack.pop(i)
                    return {"success": True, "file_path": str(file_path)}

            return {"success": False, "error": "No undo history found"}

        except Exception as e:
            logger.error(f"Undo failed: {e}")
            return {"success": False, "error": str(e)}

    def get_file_context(
        self,
        file_path: Path,
        line: int,
        context_lines: int = 5,
    ) -> Dict[str, Any]:
        """
        Get surrounding lines around a specific line.

        Args:
            file_path: Path to file
            line: 1-indexed line number
            context_lines: Number of lines before and after (default: 5)

        Returns:
            Dict with before_lines, target_line, after_lines, line_numbers
        """
        try:
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            # Read file
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = file_path.read_text(encoding="latin-1")

            lines = content.splitlines()
            total_lines = len(lines)

            # Validate line number
            if line < 1 or line > total_lines:
                return {
                    "success": False,
                    "error": f"Line {line} out of range (1-{total_lines})",
                }

            # Calculate line ranges (0-indexed)
            start_line = max(0, line - 1 - context_lines)
            end_line = min(total_lines, line - 1 + context_lines + 1)

            # Extract context
            before_lines = lines[start_line : line - 1]
            target_line = lines[line - 1] if line - 1 < total_lines else ""
            after_lines = lines[line:end_line]

            # Generate line numbers
            before_line_numbers = list(range(start_line + 1, line))
            target_line_number = line
            after_line_numbers = list(range(line + 1, end_line + 1))

            return {
                "success": True,
                "file_path": str(file_path),
                "target_line": line,
                "before_lines": before_lines,
                "target_line_content": target_line,
                "after_lines": after_lines,
                "before_line_numbers": before_line_numbers,
                "target_line_number": target_line_number,
                "after_line_numbers": after_line_numbers,
                "total_lines": total_lines,
            }

        except Exception as e:
            logger.error(f"Get file context failed: {e}")
            return {"success": False, "error": str(e)}

    def _detect_mode(
        self, file_path: Path, content: str, old_string: str
    ) -> Literal["string", "ast"]:
        """Auto-detect best edit mode."""
        # Non-Python files → string mode
        if file_path.suffix != ".py":
            return "string"

        # Try AST parsing
        try:
            import ast

            ast.parse(content)
            # Valid Python → use AST if old_string looks like code
            if any(
                keyword in old_string
                for keyword in ["def ", "class ", "import ", "from "]
            ):
                return "ast"
        except SyntaxError:
            pass

        # Default to string mode
        return "string"

    def _string_edit(
        self, content: str, old_string: str, new_string: str, replace_all: bool
    ) -> Tuple[str, int]:
        """Exact string replacement."""
        if replace_all:
            count = content.count(old_string)
            new_content = content.replace(old_string, new_string)
            return new_content, count
        else:
            if old_string in content:
                # Check uniqueness
                count = content.count(old_string)
                if count > 1:
                    raise ValueError(
                        f"old_string appears {count} times. Use replace_all=True or provide more context."
                    )
                new_content = content.replace(old_string, new_string, 1)
                return new_content, 1
            return content, 0

    def _ast_edit(
        self, content: str, old_string: str, new_string: str, file_path: Path
    ) -> Tuple[str, int]:
        """AST-based semantic editing."""
        try:
            import ast

            from ..languages.python import PythonEditor

            editor = PythonEditor()
            tree = ast.parse(content)

            # Try to detect edit type from old_string
            if old_string.startswith("def "):
                # Function rename/modification
                func_name = old_string.split("(")[0].replace("def ", "").strip()
                new_func_name = new_string.split("(")[0].replace("def ", "").strip()

                # Rename function
                from ..languages.python import rename_symbol

                new_tree = rename_symbol(tree, func_name, new_func_name, "function")
                new_content = ast.unparse(new_tree)
                return new_content, 1

            elif old_string.startswith("class "):
                # Class rename
                class_name = old_string.split(":")[0].replace("class ", "").strip()
                new_class_name = new_string.split(":")[0].replace("class ", "").strip()

                from ..languages.python import rename_symbol

                new_tree = rename_symbol(tree, class_name, new_class_name, "class")
                new_content = ast.unparse(new_tree)
                return new_content, 1

            else:
                # Fallback to string edit
                return self._string_edit(content, old_string, new_string, False)

        except Exception as e:
            logger.warning(f"AST edit failed, falling back to string: {e}")
            return self._string_edit(content, old_string, new_string, False)

    def _push_undo(self, file_path: Path, content: str):
        """Push to undo stack."""
        self.undo_stack.append((file_path, content))
        if len(self.undo_stack) > self.max_undo_stack:
            self.undo_stack.pop(0)
