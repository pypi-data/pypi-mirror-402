"""Advanced refactoring operations for code transformation."""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from .editor import CodeEditor
from .intellisense import IntelliSense
from .parser import MultiLanguageParser


class RefactorEngine:
    """Advanced refactoring engine with multi-file support."""

    def __init__(self):
        self.editor = CodeEditor()
        self.intellisense = IntelliSense()
        self.parser = MultiLanguageParser()

    def rename_symbol(
        self,
        file_path: Path,
        line: int,
        column: int,
        new_name: str,
        scope: str = "project",
    ) -> Dict[str, Any]:
        """
        Rename symbol across multiple files.

        Args:
            file_path: File containing symbol
            line: Line number (1-indexed)
            column: Column number (0-indexed)
            new_name: New name for symbol
            scope: Scope of rename (file/project)

        Returns:
            Dict with rename results
        """
        try:
            # Get symbol information
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            # Try LSP rename first for supported languages
            ext = file_path.suffix.lower()
            lsp_languages = {".ts", ".tsx", ".js", ".jsx", ".java", ".cpp", ".cxx", ".cc", ".c", ".h", ".hpp", ".go", ".rs"}
            
            if ext in lsp_languages:
                # Use LSP rename if available
                from .lsp_client import LSPClient
                lsp_client = LSPClient()
                result = lsp_client.rename_symbol(file_path, line, column, new_name)
                if result.get("success"):
                    return result

            # Fallback to Python AST-based rename
            if ext == ".py":
                return self._rename_python_symbol(file_path, line, column, new_name, scope)

            return {"success": False, "error": f"Rename not supported for {ext}"}

        except Exception as e:
            logger.error(f"Rename symbol error: {e}")
            return {"success": False, "error": str(e)}

    def _rename_python_symbol(
        self,
        file_path: Path,
        line: int,
        column: int,
        new_name: str,
        scope: str,
    ) -> Dict[str, Any]:
        """Rename Python symbol using AST."""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Find symbol at position
            result = self.intellisense.goto_definition(file_path, line, column, content)
            if not result.get("success"):
                return {"success": False, "error": "Could not find symbol definition"}

            definitions = result.get("definitions", [])
            if not definitions:
                return {"success": False, "error": "No definition found"}

            old_name = definitions[0].get("name")
            if not old_name:
                return {"success": False, "error": "Could not determine symbol name"}

            # Parse AST
            tree = ast.parse(content)
            
            # Rename in current file
            from ..languages.python import rename_symbol
            new_tree = rename_symbol(tree, old_name, new_name, "all")
            new_content = ast.unparse(new_tree)
            
            changes = []
            if new_content != content:
                file_path.write_text(new_content, encoding="utf-8")
                changes.append({"file": str(file_path), "changes": 1})

            # Find references if scope is project
            if scope == "project":
                refs_result = self.intellisense.find_references(file_path, line, column, content)
                if refs_result.get("success"):
                    references = refs_result.get("references", [])
                    # Group by file
                    files_to_update = {}
                    for ref in references:
                        ref_file = ref["file"]
                        if ref_file not in files_to_update:
                            files_to_update[ref_file] = []
                        files_to_update[ref_file].append(ref)

                    # Update each file
                    for ref_file, refs in files_to_update.items():
                        ref_path = Path(ref_file)
                        if ref_path.exists() and ref_path != file_path:
                            ref_content = ref_path.read_text(encoding="utf-8")
                            ref_tree = ast.parse(ref_content)
                            ref_new_tree = rename_symbol(ref_tree, old_name, new_name, "all")
                            ref_new_content = ast.unparse(ref_new_tree)
                            if ref_new_content != ref_content:
                                ref_path.write_text(ref_new_content, encoding="utf-8")
                                changes.append({"file": ref_file, "changes": len(refs)})

            return {
                "success": True,
                "old_name": old_name,
                "new_name": new_name,
                "files_changed": len(changes),
                "changes": changes,
            }

        except Exception as e:
            logger.error(f"Python rename error: {e}")
            return {"success": False, "error": str(e)}

    def extract_method(
        self,
        file_path: Path,
        start_line: int,
        end_line: int,
        method_name: str,
    ) -> Dict[str, Any]:
        """
        Extract code block to new method.

        Args:
            file_path: File containing code block
            start_line: Start line (1-indexed)
            end_line: End line (1-indexed)
            method_name: Name for new method

        Returns:
            Dict with extraction results
        """
        try:
            if file_path.suffix.lower() != ".py":
                return {"success": False, "error": "Extract method only supported for Python"}

            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            if start_line < 1 or end_line > len(lines) or start_line > end_line:
                return {"success": False, "error": "Invalid line range"}

            # Extract code block (convert to 0-indexed)
            code_block = "\n".join(lines[start_line - 1 : end_line])
            
            # Determine indentation
            first_line = lines[start_line - 1]
            indent = len(first_line) - len(first_line.lstrip())
            
            # Create method signature
            method_signature = f"def {method_name}():"
            new_method = f"{' ' * indent}{method_signature}\n{' ' * (indent + 4)}{code_block.strip()}\n"

            # Insert method before start_line
            new_lines = lines[:start_line - 1] + [new_method] + lines[end_line:]
            new_content = "\n".join(new_lines)

            # Replace code block with method call
            call_line = f"{' ' * indent}{method_name}()"
            final_lines = new_lines[:start_line] + [call_line] + new_lines[start_line:]
            final_content = "\n".join(final_lines)

            file_path.write_text(final_content, encoding="utf-8")

            return {
                "success": True,
                "method_name": method_name,
                "lines_extracted": end_line - start_line + 1,
                "file": str(file_path),
            }

        except Exception as e:
            logger.error(f"Extract method error: {e}")
            return {"success": False, "error": str(e)}

    def extract_variable(
        self,
        file_path: Path,
        line: int,
        column: int,
        variable_name: str,
    ) -> Dict[str, Any]:
        """
        Extract expression to variable.

        Args:
            file_path: File containing expression
            line: Line number (1-indexed)
            column: Column number (0-indexed)
            variable_name: Name for new variable

        Returns:
            Dict with extraction results
        """
        try:
            if file_path.suffix.lower() != ".py":
                return {"success": False, "error": "Extract variable only supported for Python"}

            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            if line < 1 or line > len(lines):
                return {"success": False, "error": "Invalid line number"}

            # For now, simple implementation - extract entire line as variable
            target_line = lines[line - 1]
            indent = len(target_line) - len(target_line.lstrip())
            
            # Create variable assignment
            var_line = f"{' ' * indent}{variable_name} = {target_line.strip()}"
            
            # Replace line with variable reference
            new_lines = lines[:line - 1] + [var_line, target_line] + lines[line:]
            new_content = "\n".join(new_lines)

            file_path.write_text(new_content, encoding="utf-8")

            return {
                "success": True,
                "variable_name": variable_name,
                "file": str(file_path),
            }

        except Exception as e:
            logger.error(f"Extract variable error: {e}")
            return {"success": False, "error": str(e)}

    def inline_symbol(
        self,
        file_path: Path,
        line: int,
        column: int,
    ) -> Dict[str, Any]:
        """
        Inline variable or method call.

        Args:
            file_path: File containing symbol
            line: Line number (1-indexed)
            column: Column number (0-indexed)

        Returns:
            Dict with inlining results
        """
        try:
            if file_path.suffix.lower() != ".py":
                return {"success": False, "error": "Inline symbol only supported for Python"}

            content = file_path.read_text(encoding="utf-8")
            
            # Find definition
            result = self.intellisense.goto_definition(file_path, line, column, content)
            if not result.get("success"):
                return {"success": False, "error": "Could not find symbol definition"}

            # For now, return not implemented
            return {"success": False, "error": "Inline symbol not yet fully implemented"}

        except Exception as e:
            logger.error(f"Inline symbol error: {e}")
            return {"success": False, "error": str(e)}

    def move_symbol(
        self,
        file_path: Path,
        line: int,
        column: int,
        target_file: Path,
    ) -> Dict[str, Any]:
        """
        Move symbol to different file.

        Args:
            file_path: Source file
            line: Line number (1-indexed)
            column: Column number (0-indexed)
            target_file: Target file path

        Returns:
            Dict with move results
        """
        try:
            if file_path.suffix.lower() != ".py" or target_file.suffix.lower() != ".py":
                return {"success": False, "error": "Move symbol only supported for Python"}

            # Find definition
            result = self.intellisense.goto_definition(file_path, line, column)
            if not result.get("success"):
                return {"success": False, "error": "Could not find symbol definition"}

            # For now, return not implemented
            return {"success": False, "error": "Move symbol not yet fully implemented"}

        except Exception as e:
            logger.error(f"Move symbol error: {e}")
            return {"success": False, "error": str(e)}

