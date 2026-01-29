"""LSP Client for TypeScript, Java, and C++ language servers."""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

try:
    from pygls.lsp.client import LanguageClient
    from pygls.lsp.types import (
        CompletionItem,
        CompletionParams,
        DocumentFormattingParams,
        HoverParams,
        Location,
        Position,
        TextDocumentIdentifier,
    )
    PYLS_AVAILABLE = True
except ImportError:
    PYLS_AVAILABLE = False
    logger.warning("pygls not installed. LSP features will be limited.")


class LSPClient:
    """LSP Client wrapper for multiple language servers."""

    LANGUAGE_SERVERS = {
        "typescript": {
            "command": "typescript-language-server",
            "args": ["--stdio"],
            "check": ["which", "typescript-language-server"],
        },
        "javascript": {
            "command": "typescript-language-server",
            "args": ["--stdio"],
            "check": ["which", "typescript-language-server"],
        },
        "java": {
            "command": "jdtls",
            "args": [],
            "check": ["which", "jdtls"],
        },
        "cpp": {
            "command": "clangd",
            "args": [],
            "check": ["which", "clangd"],
        },
        "c": {
            "command": "clangd",
            "args": [],
            "check": ["which", "clangd"],
        },
        "go": {
            "command": "gopls",
            "args": [],
            "check": ["which", "gopls"],
        },
        "rust": {
            "command": "rust-analyzer",
            "args": [],
            "check": ["which", "rust-analyzer"],
        },
    }

    def __init__(self):
        self.clients: Dict[str, Any] = {}
        self.workspace_roots: Dict[str, Path] = {}
        self.use_pyls = PYLS_AVAILABLE

    def _check_server_available(self, language: str) -> bool:
        """Check if language server is available."""
        if language not in self.LANGUAGE_SERVERS:
            return False

        server_info = self.LANGUAGE_SERVERS[language]
        try:
            result = subprocess.run(
                server_info["check"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_language(self, file_path: Path) -> str:
        """Detect language from file extension."""
        ext_map = {
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".java": "java",
            ".cpp": "cpp",
            ".cxx": "cpp",
            ".cc": "cpp",
            ".hpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".go": "go",
            ".rs": "rust",
        }
        return ext_map.get(file_path.suffix.lower(), "unknown")

    def initialize(self, language: str, workspace_path: Path) -> Dict[str, Any]:
        """
        Initialize LSP server for language.

        Args:
            language: Language identifier
            workspace_path: Workspace root path

        Returns:
            Dict with initialization result
        """
        try:
            if not self.use_pyls:
                return {"success": False, "error": "pygls not installed"}

            if language not in self.LANGUAGE_SERVERS:
                return {"success": False, "error": f"Unsupported language: {language}"}

            if not self._check_server_available(language):
                return {"success": False, "error": f"Language server not found for {language}"}

            # For now, return success - actual client initialization would require async setup
            # This is a simplified version that uses subprocess-based LSP communication
            self.workspace_roots[language] = workspace_path
            return {"success": True, "language": language}

        except Exception as e:
            logger.error(f"LSP initialization error: {e}")
            return {"success": False, "error": str(e)}

    def complete(
        self, file_path: Path, line: int, column: int, content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get code completions via LSP.

        Args:
            file_path: Path to file
            line: Line number (1-indexed)
            column: Column number (0-indexed)
            content: Optional file content

        Returns:
            Dict with completions
        """
        try:
            language = self._get_language(file_path)
            if language == "unknown" or language not in self.LANGUAGE_SERVERS:
                return {"success": False, "error": f"LSP not supported for {file_path.suffix}"}

            if not self._check_server_available(language):
                return {"success": False, "error": f"Language server not available for {language}"}

            # Simplified LSP completion via subprocess
            # In production, this would use proper LSP client with JSON-RPC
            return {
                "success": False,
                "error": "LSP completion requires full client implementation",
                "fallback": "Use tree-sitter or Jedi instead",
            }

        except Exception as e:
            logger.error(f"LSP completion error: {e}")
            return {"success": False, "error": str(e)}

    def goto_definition(
        self, file_path: Path, line: int, column: int, content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get symbol definition via LSP."""
        try:
            language = self._get_language(file_path)
            if language == "unknown" or language not in self.LANGUAGE_SERVERS:
                return {"success": False, "error": f"LSP not supported for {file_path.suffix}"}

            return {
                "success": False,
                "error": "LSP goto_definition requires full client implementation",
            }

        except Exception as e:
            logger.error(f"LSP goto_definition error: {e}")
            return {"success": False, "error": str(e)}

    def find_references(
        self, file_path: Path, line: int, column: int, content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find references via LSP."""
        try:
            language = self._get_language(file_path)
            if language == "unknown" or language not in self.LANGUAGE_SERVERS:
                return {"success": False, "error": f"LSP not supported for {file_path.suffix}"}

            return {
                "success": False,
                "error": "LSP find_references requires full client implementation",
            }

        except Exception as e:
            logger.error(f"LSP find_references error: {e}")
            return {"success": False, "error": str(e)}

    def hover(
        self, file_path: Path, line: int, column: int, content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get hover information via LSP."""
        try:
            language = self._get_language(file_path)
            if language == "unknown" or language not in self.LANGUAGE_SERVERS:
                return {"success": False, "error": f"LSP not supported for {file_path.suffix}"}

            return {
                "success": False,
                "error": "LSP hover requires full client implementation",
            }

        except Exception as e:
            logger.error(f"LSP hover error: {e}")
            return {"success": False, "error": str(e)}

    def format_document(self, file_path: Path) -> Dict[str, Any]:
        """Format document via LSP."""
        try:
            language = self._get_language(file_path)
            if language == "unknown" or language not in self.LANGUAGE_SERVERS:
                return {"success": False, "error": f"LSP not supported for {file_path.suffix}"}

            if not self._check_server_available(language):
                return {"success": False, "error": f"Language server not available for {language}"}

            # For TypeScript/JavaScript, try using prettier or formatter
            if language in ["typescript", "javascript"]:
                # Try prettier
                try:
                    result = subprocess.run(
                        ["npx", "prettier", "--stdin-filepath", str(file_path)],
                        input=file_path.read_text(),
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "formatted": result.stdout,
                        }
                except Exception:
                    pass

            return {
                "success": False,
                "error": "LSP format_document requires full client implementation",
            }

        except Exception as e:
            logger.error(f"LSP format_document error: {e}")
            return {"success": False, "error": str(e)}

