"""Jedi-based IntelliSense for Python code with LSP fallback."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import jedi
from loguru import logger

from .lsp_client import LSPClient


class IntelliSense:
    """Intelligent code completion and navigation using Jedi and LSP."""

    def __init__(self):
        self.jedi_env = jedi.create_environment(sys.executable)
        self.lsp_client = LSPClient()

    def _should_use_lsp(self, file_path: Path) -> bool:
        """Determine if LSP should be used for this file."""
        ext = file_path.suffix.lower()
        lsp_languages = {".ts", ".tsx", ".js", ".jsx", ".java", ".cpp", ".cxx", ".cc", ".c", ".h", ".hpp", ".go", ".rs"}
        return ext in lsp_languages

    def _should_use_jedi(self, file_path: Path) -> bool:
        """Determine if Jedi should be used for this file."""
        return file_path.suffix.lower() == ".py"

    def complete(
        self,
        file_path: Path,
        line: int,
        column: int,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get code completions at cursor position.

        Args:
            file_path: Path to file
            line: Line number (1-indexed)
            column: Column number (0-indexed)
            content: Optional file content (reads from disk if None)

        Returns:
            Dict with completions list
        """
        # Try LSP first for supported languages
        if self._should_use_lsp(file_path):
            lsp_result = self.lsp_client.complete(file_path, line, column, content)
            if lsp_result.get("success"):
                return lsp_result
            # Fallback to tree-sitter if LSP fails

        # Use Jedi for Python
        if self._should_use_jedi(file_path):
            return self._jedi_complete(file_path, line, column, content)

        # Fallback: return error
        return {"success": False, "error": f"Completion not supported for {file_path.suffix}"}

    def _jedi_complete(
        self,
        file_path: Path,
        line: int,
        column: int,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Jedi-based completion (Python only)."""

        try:
            if not content:
                if not file_path.exists():
                    return {"success": False, "error": f"File not found: {file_path}"}
                content = file_path.read_text(encoding="utf-8")

            # Create Jedi script
            script = jedi.Script(
                code=content,
                path=str(file_path),
                environment=self.jedi_env,
            )

            # Get completions
            completions = script.complete(line, column)

            # Format results (limit to top 20 for token efficiency)
            MAX_COMPLETIONS = 20
            results = []

            for comp in completions[:MAX_COMPLETIONS]:
                results.append(
                    {
                        "name": comp.name,
                        "type": comp.type,
                        "description": comp.description or "",
                        "complete": comp.complete,
                        "signature": self._get_signature(comp),
                    }
                )

            return {
                "success": True,
                "completions": results,
                "total": len(completions),
                "showing": len(results),
                "truncated": len(completions) > MAX_COMPLETIONS,
            }

        except Exception as e:
            logger.error(f"Completion error: {e}")
            return {"success": False, "error": str(e)}

    def goto_definition(
        self,
        file_path: Path,
        line: int,
        column: int,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find definition of symbol at cursor.

        Args:
            file_path: Path to file
            line: Line number (1-indexed)
            column: Column number (0-indexed)
            content: Optional file content

        Returns:
            Dict with definition locations
        """
        # Try LSP first for supported languages
        if self._should_use_lsp(file_path):
            lsp_result = self.lsp_client.goto_definition(file_path, line, column, content)
            if lsp_result.get("success"):
                return lsp_result

        # Use Jedi for Python
        if self._should_use_jedi(file_path):
            return self._jedi_goto_definition(file_path, line, column, content)

        return {"success": False, "error": f"Goto definition not supported for {file_path.suffix}"}

    def _jedi_goto_definition(
        self,
        file_path: Path,
        line: int,
        column: int,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Jedi-based goto definition (Python only)."""

        try:
            if not content:
                if not file_path.exists():
                    return {"success": False, "error": f"File not found: {file_path}"}
                content = file_path.read_text(encoding="utf-8")

            script = jedi.Script(
                code=content,
                path=str(file_path),
                environment=self.jedi_env,
            )

            # Get definitions
            definitions = script.goto(line, column)

            results = []
            for defn in definitions:
                # Skip if no location
                if not defn.module_path:
                    continue

                results.append(
                    {
                        "file": str(defn.module_path),
                        "line": defn.line or 0,
                        "column": defn.column or 0,
                        "name": defn.name,
                        "type": defn.type,
                        "description": defn.description or "",
                        "full_name": defn.full_name or "",
                    }
                )

            if not results:
                return {
                    "success": False,
                    "error": "No definition found",
                }

            return {
                "success": True,
                "definitions": results,
                "count": len(results),
            }

        except Exception as e:
            logger.error(f"Goto definition error: {e}")
            return {"success": False, "error": str(e)}

    def find_references(
        self,
        file_path: Path,
        line: int,
        column: int,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find all references to symbol at cursor.

        Args:
            file_path: Path to file
            line: Line number (1-indexed)
            column: Column number (0-indexed)
            content: Optional file content

        Returns:
            Dict with reference locations
        """
        # Try LSP first for supported languages
        if self._should_use_lsp(file_path):
            lsp_result = self.lsp_client.find_references(file_path, line, column, content)
            if lsp_result.get("success"):
                return lsp_result

        # Use Jedi for Python
        if self._should_use_jedi(file_path):
            return self._jedi_find_references(file_path, line, column, content)

        return {"success": False, "error": f"Find references not supported for {file_path.suffix}"}

    def _jedi_find_references(
        self,
        file_path: Path,
        line: int,
        column: int,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Jedi-based find references (Python only)."""
        try:
            if not content:
                if not file_path.exists():
                    return {"success": False, "error": f"File not found: {file_path}"}
                content = file_path.read_text(encoding="utf-8")

            script = jedi.Script(
                code=content,
                path=str(file_path),
                environment=self.jedi_env,
            )

            # Get references (limit to 50 for performance)
            references = script.get_references(line, column)

            MAX_REFERENCES = 50
            results = []

            for ref in references[:MAX_REFERENCES]:
                if not ref.module_path:
                    continue

                results.append(
                    {
                        "file": str(ref.module_path),
                        "line": ref.line or 0,
                        "column": ref.column or 0,
                        "name": ref.name,
                        "type": ref.type,
                    }
                )

            if not results:
                return {
                    "success": False,
                    "error": "No references found",
                }

            return {
                "success": True,
                "references": results,
                "count": len(results),
                "truncated": len(references) > MAX_REFERENCES,
            }

        except Exception as e:
            logger.error(f"Find references error: {e}")
            return {"success": False, "error": str(e)}

    def signature_help(
        self,
        file_path: Path,
        line: int,
        column: int,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get function signature help at cursor.

        Args:
            file_path: Path to file
            line: Line number (1-indexed)
            column: Column number (0-indexed)
            content: Optional file content

        Returns:
            Dict with signature information
        """
        try:
            if not content:
                if not file_path.exists():
                    return {"success": False, "error": f"File not found: {file_path}"}
                content = file_path.read_text(encoding="utf-8")

            script = jedi.Script(
                code=content,
                path=str(file_path),
                environment=self.jedi_env,
            )

            # Get signatures
            signatures = script.get_signatures(line, column)

            if not signatures:
                return {
                    "success": False,
                    "error": "No signature found",
                }

            results = []
            for sig in signatures:
                params = []
                for param in sig.params:
                    params.append(
                        {
                            "name": param.name,
                            "description": param.description or "",
                            "kind": param.kind,
                            "default": getattr(param, "default", None),
                        }
                    )

                results.append(
                    {
                        "name": sig.name,
                        "description": sig.description or "",
                        "params": params,
                        "index": sig.index or 0,
                        "bracket_start": getattr(sig, "bracket_start", None),
                    }
                )

            return {
                "success": True,
                "signatures": results,
                "count": len(results),
            }

        except Exception as e:
            logger.error(f"Signature help error: {e}")
            return {"success": False, "error": str(e)}

        try:
            if not content:
                if not file_path.exists():
                    return {"success": False, "error": f"File not found: {file_path}"}
                content = file_path.read_text(encoding="utf-8")

            script = jedi.Script(
                code=content,
                path=str(file_path),
                environment=self.jedi_env,
            )

            # Get references (limit to 50 for performance)
            references = script.get_references(line, column)

            MAX_REFERENCES = 50
            results = []

            for ref in references[:MAX_REFERENCES]:
                if not ref.module_path:
                    continue

                results.append(
                    {
                        "file": str(ref.module_path),
                        "line": ref.line or 0,
                        "column": ref.column or 0,
                        "name": ref.name,
                        "type": ref.type,
                    }
                )

            if not results:
                return {
                    "success": False,
                    "error": "No references found",
                }

            return {
                "success": True,
                "references": results,
                "count": len(results),
                "truncated": len(references) > MAX_REFERENCES,
            }

        except Exception as e:
            logger.error(f"Find references error: {e}")
            return {"success": False, "error": str(e)}

    def hover(
        self,
        file_path: Path,
        line: int,
        column: int,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get hover information (docstring + signature).

        Args:
            file_path: Path to file
            line: Line number (1-indexed)
            column: Column number (0-indexed)
            content: Optional file content

        Returns:
            Dict with hover information
        """
        # Try LSP first for supported languages
        if self._should_use_lsp(file_path):
            lsp_result = self.lsp_client.hover(file_path, line, column, content)
            if lsp_result.get("success"):
                return lsp_result

        # Use Jedi for Python
        if self._should_use_jedi(file_path):
            return self._jedi_hover(file_path, line, column, content)

        return {"success": False, "error": f"Hover not supported for {file_path.suffix}"}

    def _jedi_hover(
        self,
        file_path: Path,
        line: int,
        column: int,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Jedi-based hover (Python only)."""
        try:
            if not content:
                if not file_path.exists():
                    return {"success": False, "error": f"File not found: {file_path}"}
                content = file_path.read_text(encoding="utf-8")

            script = jedi.Script(
                code=content,
                path=str(file_path),
                environment=self.jedi_env,
            )

            # Get help at position
            names = script.help(line, column)

            if not names:
                return {
                    "success": False,
                    "error": "No hover information available",
                }

            # Get first result
            name = names[0]

            docstring = name.docstring() if hasattr(name, "docstring") else ""
            signature = self._get_signature(name)

            return {
                "success": True,
                "name": name.name,
                "type": name.type,
                "signature": signature,
                "docstring": docstring,
                "full_name": name.full_name or "",
            }

        except Exception as e:
            logger.error(f"Hover error: {e}")
            return {"success": False, "error": str(e)}

    def _get_signature(self, completion) -> Optional[str]:
        """Extract signature from Jedi completion."""
        try:
            if hasattr(completion, "get_signatures"):
                sigs = completion.get_signatures()
                if sigs:
                    return sigs[0].to_string()
            return None
        except Exception:
            return None
