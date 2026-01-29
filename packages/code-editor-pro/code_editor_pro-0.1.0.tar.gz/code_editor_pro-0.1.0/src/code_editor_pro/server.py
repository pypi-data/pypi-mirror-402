"""Code Editor MCP Server - Clean, optimized for Sonnet 4.5."""

from pathlib import Path
from typing import Any, Dict, List

from loguru import logger
from mcp.server.fastmcp import FastMCP

from .core.analyzer import CodeAnalyzer
from .core.cache import get_cache
from .core.editor import CodeEditor, EditOperation
from .core.error_parser import ErrorParser
from .core.executor import CodeExecutor
from .core.generator import CodeGenerator
from .core.git_client import GitClient
from .core.intellisense import IntelliSense
from .core.lsp_client import LSPClient
from .core.parser import MultiLanguageParser
from .core.refactor import RefactorEngine
from .core.searcher import CodeSearcher
from .languages.python import apply_transformations
from .project.manager import ProjectManager

# Initialize MCP server
mcp = FastMCP("code-editor")

# Initialize components
editor = CodeEditor()
analyzer = CodeAnalyzer()
parser = MultiLanguageParser()
project_manager = ProjectManager()
intellisense = IntelliSense()
cache = get_cache()
git_client = GitClient()
executor = CodeExecutor()
lsp_client = LSPClient()
refactor_engine = RefactorEngine()
code_generator = CodeGenerator()
searcher = CodeSearcher()
error_parser = ErrorParser()


# ============================================================================
# CORE EDITING TOOLS
# ============================================================================


@mcp.tool()
def edit(
    file_path: str,
    old: str,
    new: str,
    mode: str = "auto",
    replace_all: bool = False,
) -> str:
    """
    Edit code with automatic mode selection.

    Modes: auto (smart), string (exact), ast (semantic)
    """
    try:
        result = editor.edit(
            Path(file_path), old, new, mode=mode, replace_all=replace_all
        )

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        cache.invalidate(Path(file_path))
        return f"✅ {result['changes']} change(s) applied ({result['mode']} mode)"

    except Exception as e:
        logger.error(f"Edit failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def apply_edits(file_path: str, edits: List[Dict[str, str]]) -> str:
    """
    Apply multiple edits atomically.

    edits: [{"old": "...", "new": "...", "replace_all": false}, ...]
    """
    try:
        operations = [
            EditOperation(
                e["old"], e["new"], e.get("replace_all", False)
            )
            for e in edits
        ]

        result = editor.apply(Path(file_path), operations)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        cache.invalidate(Path(file_path))
        return f"✅ {result['changes']} change(s) applied ({result['operations']} operations)"

    except Exception as e:
        logger.error(f"Apply failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def undo(file_path: str) -> str:
    """Undo last edit."""
    try:
        result = editor.undo(Path(file_path))

        if not result["success"]:
            return f"❌ {result.get('error', 'No undo history')}"

        cache.invalidate(Path(file_path))
        return f"✅ Undo successful"

    except Exception as e:
        logger.error(f"Undo failed: {e}")
        return f"❌ Error: {e}"


# ============================================================================
# ANALYSIS TOOLS
# ============================================================================


@mcp.tool()
def inspect(file_path: str) -> str:
    """
    Analyze code structure (functions, classes, imports).
    Auto-detects: Python/JS/TS/Go/Rust/Java/C++
    """
    try:
        path = Path(file_path)

        # Check cache
        cached = cache.get(path, "inspect")
        if cached:
            result = cached
        else:
            result = analyzer.inspect(path)
            if result.get("success"):
                cache.set(path, "inspect", result)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        summary = result["summary"]
        details = result["details"]

        output = f"""# {summary['file']} ({summary['language']})

Lines: {summary['line_count']}
Functions: {summary['functions']}
Classes: {summary['classes']}
Imports: {summary['imports']}

## Functions ({len(details['functions'])})
"""
        for func in details["functions"][:20]:
            output += f"- {func['name']} (line {func['line']})\n"

        if details.get("functions_truncated"):
            output += f"... +{details['functions_truncated']} more\n"

        return output

    except Exception as e:
        logger.error(f"Inspect failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def analyze(file_path: str) -> str:
    """
    Deep quality analysis (complexity, smells, metrics).
    """
    try:
        path = Path(file_path)

        # Check cache
        cached = cache.get(path, "analyze")
        if cached:
            result = cached
        else:
            result = analyzer.analyze(path)
            if result.get("success"):
                cache.set(path, "analyze", result)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        summary = result["summary"]

        output = f"""# Quality Analysis: {summary['file']}

Complexity: {summary['complexity']}
Functions: {summary['function_count']}
Code Smells: {summary['smell_count']}

Issues:
- High complexity: {summary['high_complexity_functions']} functions
- Missing docstrings: {summary['missing_docstrings']} functions
- Missing type hints: {summary['missing_type_hints']} functions
"""

        if result["details"]["top_smells"]:
            output += "\n## Top Code Smells\n"
            for smell in result["details"]["top_smells"][:10]:
                output += f"- Line {smell['line']}: {smell['type']} ({smell['severity']})\n"

        return output

    except Exception as e:
        logger.error(f"Analyze failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def dependencies(file_path: str) -> str:
    """Analyze imports and dependencies."""
    try:
        path = Path(file_path)

        # Check cache
        cached = cache.get(path, "dependencies")
        if cached:
            result = cached
        else:
            result = analyzer.dependencies(path)
            if result.get("success"):
                cache.set(path, "dependencies", result)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        summary = result["summary"]

        output = f"""# Dependencies: {summary['file']}

Total: {summary['total_imports']}
- Standard library: {summary['stdlib']}
- Third-party: {summary['third_party']}
- Local: {summary['local']}
"""
        return output

    except Exception as e:
        logger.error(f"Dependencies failed: {e}")
        return f"❌ Error: {e}"


# ============================================================================
# CODE TRANSFORMATION TOOLS
# ============================================================================


@mcp.tool()
def transform(file_path: str, operations: List[str]) -> str:
    """
    Apply AST transformations (Python only).

    Operations: add_type_hints, clean_unused_imports, remove_dead_code, optimize_code
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return f"❌ File not found: {file_path}"

        content = path.read_text(encoding="utf-8")

        # Apply transformations
        new_content = apply_transformations(content, operations)

        # Write back
        path.write_text(new_content, encoding="utf-8")
        cache.invalidate(path)

        return f"✅ Applied transformations: {', '.join(operations)}"

    except Exception as e:
        logger.error(f"Transform failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def lint(file_path: str, linter: str = "ruff") -> str:
    """
    Lint code (ruff for Python, auto-detect for others).
    """
    try:
        import subprocess

        path = Path(file_path)

        if not path.exists():
            return f"❌ File not found: {file_path}"

        # Run linter
        if linter == "ruff":
            result = subprocess.run(
                ["ruff", "check", str(path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        else:
            return f"❌ Unsupported linter: {linter}"

        if result.returncode == 0:
            return "✅ No issues found"
        else:
            return f"Issues found:\n{result.stdout}"

    except FileNotFoundError:
        return f"❌ Linter '{linter}' not installed"
    except Exception as e:
        logger.error(f"Lint failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def format_code(file_path: str, formatter: str = "auto") -> str:
    """
    Format code (auto-detects: black for Python, LSP for TS/Java/C++/Go/Rust).
    
    Args:
        file_path: Path to file
        formatter: "auto" (default) | "black" | "lsp"
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return f"❌ File not found: {file_path}"

        ext = path.suffix.lower()
        lsp_languages = {".ts", ".tsx", ".js", ".jsx", ".java", ".cpp", ".cxx", ".cc", ".c", ".h", ".hpp", ".go", ".rs"}

        # Try LSP formatting first for supported languages
        if formatter == "auto" and ext in lsp_languages:
            result = lsp_client.format_document(path)
            if result.get("success") and result.get("formatted"):
                path.write_text(result["formatted"], encoding="utf-8")
                cache.invalidate(path)
                return "✅ Code formatted via LSP"

        # Fallback to black for Python
        if ext == ".py" or formatter == "black":
            import black

            content = path.read_text(encoding="utf-8")
            formatted = black.format_str(content, mode=black.Mode())
            path.write_text(formatted, encoding="utf-8")

            cache.invalidate(path)
            return "✅ Code formatted"

        return "❌ Formatting not supported for this file type"

    except Exception as e:
        logger.error(f"Format failed: {e}")
        return f"❌ Error: {e}"


# ============================================================================
# PROJECT MANAGEMENT TOOLS
# ============================================================================


@mcp.tool()
def project_create(name: str, path: str, language: str = "python") -> str:
    """Create project workspace."""
    try:
        project = project_manager.create_project(name, path, language)
        return f"✅ Project created: {project.project_name} ({project.project_id})"

    except Exception as e:
        logger.error(f"Project creation failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def project_add_file(project_id: str, file_path: str) -> str:
    """Add file to project."""
    try:
        file_info = project_manager.add_file(file_path, project_id)
        return f"✅ File added: {file_info.file_name}"

    except Exception as e:
        logger.error(f"Add file failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def project_stats(project_id: str) -> str:
    """Get project statistics."""
    try:
        stats = project_manager.get_project_stats(project_id)
        return f"""# Project Stats

Files: {stats.total_files}
Lines: {stats.total_lines}
Size: {stats.total_size_mb:.2f} MB

Languages: {', '.join(f"{k}({v})" for k, v in stats.language_distribution.items())}
"""

    except Exception as e:
        logger.error(f"Project stats failed: {e}")
        return f"❌ Error: {e}"


# ============================================================================
# IDE FEATURES (JEDI-BASED + AUTO-LSP)
# ============================================================================


@mcp.tool()
def complete(file_path: str, line: int, column: int) -> str:
    """
    Get code completions at cursor position (auto-uses LSP for TS/Java/C++/Go/Rust).

    Args:
        file_path: Path to file
        line: 1-indexed line number
        column: 0-indexed column number
    """
    try:
        result = intellisense.complete(Path(file_path), line, column)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        output = f"# Completions ({result['showing']}/{result['total']})\n\n"

        for comp in result["completions"]:
            sig = f" {comp['signature']}" if comp["signature"] else ""
            output += f"- {comp['name']} ({comp['type']}){sig}\n"

        if result.get("truncated"):
            output += f"\n... +{result['total'] - result['showing']} more"

        return output

    except Exception as e:
        logger.error(f"Complete failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def goto_definition(file_path: str, line: int, column: int) -> str:
    """
    Jump to definition of symbol at cursor (auto-uses LSP for TS/Java/C++/Go/Rust).

    Args:
        file_path: Path to file
        line: 1-indexed line number
        column: 0-indexed column number
    """
    try:
        result = intellisense.goto_definition(Path(file_path), line, column)

        if not result["success"]:
            return f"❌ {result.get('error', 'No definition found')}"

        output = f"# Definitions ({result['count']})\n\n"

        for defn in result["definitions"]:
            output += f"- {defn['name']} ({defn['type']})\n"
            output += f"  {defn['file']}:{defn['line']}:{defn['column']}\n"
            if defn['description']:
                output += f"  {defn['description']}\n"

        return output

    except Exception as e:
        logger.error(f"Goto definition failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def find_references(file_path: str, line: int, column: int) -> str:
    """
    Find all references to symbol at cursor (auto-uses LSP for TS/Java/C++/Go/Rust).

    Args:
        file_path: Path to file
        line: 1-indexed line number
        column: 0-indexed column number
    """
    try:
        result = intellisense.find_references(Path(file_path), line, column)

        if not result["success"]:
            return f"❌ {result.get('error', 'No references found')}"

        output = f"# References ({result['count']})\n\n"

        # Group by file
        by_file = {}
        for ref in result["references"]:
            file = ref["file"]
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(ref)

        for file, refs in by_file.items():
            output += f"## {file}\n"
            for ref in refs:
                output += f"- Line {ref['line']}: {ref['name']}\n"
            output += "\n"

        if result.get("truncated"):
            output += "... (truncated, showing first 50)"

        return output

    except Exception as e:
        logger.error(f"Find references failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def signature_help(file_path: str, line: int, column: int) -> str:
    """
    Get function signature help at cursor (Python only).

    Args:
        file_path: Path to file
        line: 1-indexed line number
        column: 0-indexed column number
    """
    try:
        result = intellisense.signature_help(Path(file_path), line, column)

        if not result["success"]:
            return f"❌ {result.get('error', 'No signature found')}"

        output = f"# Signatures ({result['count']})\n\n"

        for sig in result["signatures"]:
            output += f"## {sig['name']}\n"
            if sig["description"]:
                output += f"{sig['description']}\n\n"

            output += "**Parameters:**\n"
            for param in sig["params"]:
                default = f" = {param['default']}" if param.get("default") else ""
                output += f"- {param['name']}{default} ({param['kind']})\n"
                if param["description"]:
                    output += f"  {param['description']}\n"

        return output

    except Exception as e:
        logger.error(f"Signature help failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def hover(file_path: str, line: int, column: int) -> str:
    """
    Get hover information (docstring + signature, auto-uses LSP for TS/Java/C++/Go/Rust).

    Args:
        file_path: Path to file
        line: 1-indexed line number
        column: 0-indexed column number
    """
    try:
        result = intellisense.hover(Path(file_path), line, column)

        if not result["success"]:
            return f"❌ {result.get('error', 'No hover info available')}"

        output = f"# {result['name']} ({result['type']})\n\n"

        if result.get("signature"):
            output += f"```python\n{result['signature']}\n```\n\n"

        if result.get("docstring"):
            output += f"{result['docstring']}\n\n"

        if result.get("full_name"):
            output += f"**Full name:** `{result['full_name']}`"

        return output

    except Exception as e:
        logger.error(f"Hover failed: {e}")
        return f"❌ Error: {e}"


# ============================================================================
# CODE EXECUTION & TESTING TOOLS
# ============================================================================


@mcp.tool()
def execute_code(
    file_path: str,
    args: List[str] = None,
    env: Dict[str, str] = None,
    timeout: int = 30,
) -> str:
    """
    Execute code file.

    Args:
        file_path: Path to code file
        args: Command line arguments
        env: Environment variables
        timeout: Execution timeout in seconds (default: 30)
    """
    try:
        result = executor.execute_code(file_path, args or [], env or {}, timeout)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        output = f"""# Execution Result: {file_path}

Language: {result['language']}
Return Code: {result['returncode']}

## Output
```
{result['stdout']}
```

"""
        if result.get("stderr"):
            output += f"""## Errors
```
{result['stderr']}
```
"""

        return output

    except Exception as e:
        logger.error(f"Code execution failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def run_tests(
    project_path: str,
    test_pattern: str = "",
    framework: str = "auto",
) -> str:
    """
    Run tests in project.

    Args:
        project_path: Project directory path
        test_pattern: Test pattern/filter
        framework: Test framework (auto/pytest/jest/junit)
    """
    try:
        result = executor.run_tests(project_path, test_pattern, framework)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        output = f"""# Test Results: {project_path}

Framework: {result['framework']}
Status: {status}
Return Code: {result['returncode']}

## Output
```
{result['stdout']}
```

"""
        if result.get("stderr"):
            output += f"""## Errors
```
{result['stderr']}
```
"""

        return output

    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def check_coverage(file_path: str = "", project_path: str = "") -> str:
    """
    Check test coverage.

    Args:
        file_path: Optional specific file path
        project_path: Project directory path
    """
    try:
        result = executor.check_coverage(file_path, project_path)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        output = f"""# Coverage Report

{result['coverage_output']}

"""
        if result.get("stderr"):
            output += f"""## Warnings
```
{result['stderr']}
```
"""

        return output

    except Exception as e:
        logger.error(f"Coverage check failed: {e}")
        return f"❌ Error: {e}"


# ============================================================================
# GIT INTEGRATION TOOLS
# ============================================================================


@mcp.tool()
def git(
    operation: str,
    project_path: str = "",
    file_path: str = "",
    message: str = "",
    files: List[str] = None,
    limit: int = 10,
) -> str:
    """
    Git operations: status, diff, commit, log, branches.

    Args:
        operation: "status" | "diff" | "commit" | "log" | "branches"
        project_path: Project directory path
        file_path: Optional specific file path (for diff)
        message: Commit message (for commit)
        files: Optional list of files to commit (for commit)
        limit: Number of commits to return (for log)
    """
    try:
        if operation == "status":
            result = git_client.status(project_path)

            if not result["success"]:
                return f"❌ {result.get('error', 'Unknown error')}"

            if not result.get("is_repo"):
                return "❌ Not a git repository"

            output = f"""# Git Status: {project_path}

Branch: {result['branch']}
Dirty: {result['dirty']}

"""
            if result.get("staged_files"):
                output += f"## Staged Files ({len(result['staged_files'])})\n"
                for f in result["staged_files"][:10]:
                    output += f"- {f}\n"
                if len(result["staged_files"]) > 10:
                    output += f"... +{len(result['staged_files']) - 10} more\n"

            if result.get("modified_files"):
                output += f"\n## Modified Files ({len(result['modified_files'])})\n"
                for f in result["modified_files"][:10]:
                    output += f"- {f}\n"
                if len(result["modified_files"]) > 10:
                    output += f"... +{len(result['modified_files']) - 10} more\n"

            if result.get("untracked_files"):
                output += f"\n## Untracked Files ({len(result['untracked_files'])})\n"
                for f in result["untracked_files"][:10]:
                    output += f"- {f}\n"
                if len(result["untracked_files"]) > 10:
                    output += f"... +{len(result['untracked_files']) - 10} more\n"

            return output

        elif operation == "diff":
            result = git_client.diff(file_path if file_path else None, project_path if project_path else None)

            if not result["success"]:
                return f"❌ {result.get('error', 'Unknown error')}"

            if not result.get("diff"):
                return f"✅ No changes for {result.get('file', 'project')}"

            return f"# Git Diff: {result.get('file', 'project')}\n\n```diff\n{result['diff']}\n```"

        elif operation == "commit":
            if not project_path:
                return "❌ project_path is required"

            result = git_client.commit(message, files, project_path)

            if not result["success"]:
                return f"❌ {result.get('error', 'Unknown error')}"

            files_str = ", ".join(result["files"]) if isinstance(result["files"], list) else result["files"]
            return f"✅ Commit created: {result['commit_hash'][:8]}\nMessage: {result['message']}\nFiles: {files_str}"

        elif operation == "log":
            result = git_client.log(limit, file_path if file_path else None, project_path if project_path else None)

            if not result["success"]:
                return f"❌ {result.get('error', 'Unknown error')}"

            output = f"# Git Log ({result['count']} commits)\n\n"
            for commit in result["commits"]:
                output += f"## {commit['hash']} - {commit['message']}\n"
                output += f"Author: {commit['author']}\n"
                output += f"Date: {commit['date']}\n\n"

            return output

        elif operation == "branches":
            result = git_client.branches(project_path)

            if not result["success"]:
                return f"❌ {result.get('error', 'Unknown error')}"

            output = f"# Git Branches\n\nCurrent: **{result['current']}**\n\n"
            output += "## All Branches\n"
            for branch in result["branches"]:
                marker = "←" if branch == result["current"] else ""
                output += f"- {branch} {marker}\n"

            return output

        else:
            return f"❌ Unknown git operation: {operation}. Use: status, diff, commit, log, branches"

    except Exception as e:
        logger.error(f"Git {operation} failed: {e}")
        return f"❌ Error: {e}"


# ============================================================================
# REFACTORING TOOLS
# ============================================================================


@mcp.tool()
def rename_symbol(
    file_path: str,
    line: int,
    column: int,
    new_name: str,
    scope: str = "project",
) -> str:
    """
    Rename symbol across multiple files.

    Args:
        file_path: File containing symbol
        line: 1-indexed line number
        column: 0-indexed column number
        new_name: New name for symbol
        scope: Scope of rename (file/project)
    """
    try:
        result = refactor_engine.rename_symbol(Path(file_path), line, column, new_name, scope)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        output = f"""# Rename Symbol

Old Name: {result['old_name']}
New Name: {result['new_name']}
Files Changed: {result['files_changed']}

"""
        for change in result.get("changes", []):
            output += f"- {change['file']}: {change['changes']} change(s)\n"

        return output

    except Exception as e:
        logger.error(f"Rename symbol failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def extract_method(
    file_path: str,
    start_line: int,
    end_line: int,
    method_name: str,
) -> str:
    """
    Extract code block to new method.

    Args:
        file_path: File containing code block
        start_line: Start line (1-indexed)
        end_line: End line (1-indexed)
        method_name: Name for new method
    """
    try:
        result = refactor_engine.extract_method(Path(file_path), start_line, end_line, method_name)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        return f"""✅ Method Extracted

Method Name: {result['method_name']}
Lines Extracted: {result['lines_extracted']}
File: {result['file']}
"""

    except Exception as e:
        logger.error(f"Extract method failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def extract_variable(
    file_path: str,
    line: int,
    column: int,
    variable_name: str,
) -> str:
    """
    Extract expression to variable.

    Args:
        file_path: File containing expression
        line: 1-indexed line number
        column: 0-indexed column number
        variable_name: Name for new variable
    """
    try:
        result = refactor_engine.extract_variable(Path(file_path), line, column, variable_name)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        return f"""✅ Variable Extracted

Variable Name: {result['variable_name']}
File: {result['file']}
"""

    except Exception as e:
        logger.error(f"Extract variable failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def inline_symbol(file_path: str, line: int, column: int) -> str:
    """
    Inline variable or method call.

    Args:
        file_path: File containing symbol
        line: 1-indexed line number
        column: 0-indexed column number
    """
    try:
        result = refactor_engine.inline_symbol(Path(file_path), line, column)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        return "✅ Symbol inlined"

    except Exception as e:
        logger.error(f"Inline symbol failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def move_symbol(
    file_path: str,
    line: int,
    column: int,
    target_file: str,
) -> str:
    """
    Move symbol to different file.

    Args:
        file_path: Source file
        line: 1-indexed line number
        column: 0-indexed column number
        target_file: Target file path
    """
    try:
        result = refactor_engine.move_symbol(Path(file_path), line, column, Path(target_file))

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        return "✅ Symbol moved"

    except Exception as e:
        logger.error(f"Move symbol failed: {e}")
        return f"❌ Error: {e}"


# ============================================================================
# CODE GENERATION TOOLS
# ============================================================================


@mcp.tool()
def generate_code(
    type: str,
    output_path: str,
    template: str = "",
    variables: Dict[str, str] = None,
    file_path: str = "",
    test_framework: str = "auto",
    language: str = "",
    name: str = "",
) -> str:
    """
    Generate code: template, test, or boilerplate.

    Args:
        type: "template" | "test" | "boilerplate"
        output_path: Output file path
        template: Template file name (for type="template")
        variables: Template variables dict (for type="template")
        file_path: Source file path (for type="test")
        test_framework: Test framework (for type="test")
        language: Programming language (for type="boilerplate")
        name: Name for generated code (for type="boilerplate")
    """
    try:
        if type == "template":
            if not template:
                return "❌ template parameter required for type='template'"
            result = code_generator.generate_code(
                template,
                Path(output_path),
                variables or {},
            )
        elif type == "test":
            if not file_path:
                return "❌ file_path parameter required for type='test'"
            result = code_generator.generate_test(Path(file_path), test_framework)
            if result["success"]:
                return f"""✅ Test Generated

Test File: {result['test_file']}
Framework: {result['framework']}
"""
        elif type == "boilerplate":
            if not language or not name:
                return "❌ language and name parameters required for type='boilerplate'"
            # Determine boilerplate type from output_path extension
            ext = Path(output_path).suffix.lower()
            boilerplate_type = "struct" if ext in [".go", ".rs"] else ("component" if ext == ".tsx" else ("class" if ext == ".py" else "function"))
            result = code_generator.generate_boilerplate(
                language,
                boilerplate_type,
                name,
                Path(output_path),
            )
        else:
            return f"❌ Unknown type: {type}. Use: template, test, boilerplate"

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        if type == "template":
            return f"""✅ Code Generated

Template: {result['template']}
Output: {result['output_path']}
"""
        elif type == "boilerplate":
            return f"""✅ Boilerplate Generated

Language: {result['language']}
Type: {result['type']}
Output: {result['output_path']}
"""
        else:
            return "✅ Code generated"

    except Exception as e:
        logger.error(f"Code generation failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def scaffold_project(
    project_type: str,
    path: str,
    options: Dict[str, Any] = None,
) -> str:
    """
    Scaffold project structure.

    Args:
        project_type: Type of project (python/ts/go/rust)
        path: Project root path
        options: Project options (name, description, etc.)
    """
    try:
        result = code_generator.scaffold_project(
            project_type,
            Path(path),
            options or {},
        )

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        output = f"""✅ Project Scaffolded

Type: {result['project_type']}
Path: {result['project_path']}

Files Created:
"""
        for file in result.get("files_created", []):
            output += f"- {file}\n"

        return output

    except Exception as e:
        logger.error(f"Project scaffolding failed: {e}")
        return f"❌ Error: {e}"


# ============================================================================
# SEARCH & CONTEXT TOOLS
# ============================================================================


@mcp.tool()
def search_across_files(
    pattern: str,
    project_path: str,
    file_extensions: List[str] = None,
    use_regex: bool = False,
) -> str:
    """
    Search for pattern across multiple files in project.

    Args:
        pattern: Search pattern (regex or plain text)
        project_path: Root directory to search
        file_extensions: Optional list of file extensions to filter (e.g., [".py", ".js"])
        use_regex: If True, treat pattern as regex; otherwise plain text search
    """
    try:
        result = searcher.search_across_files(
            pattern, project_path, file_extensions, use_regex
        )

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        output = f"""# Search Results: "{pattern}"

Total Matches: {result['total_matches']}
Files Searched: {result['files_searched']}
Files with Matches: {result['files_with_matches']}
"""

        if result.get("truncated"):
            output += "\n⚠️ Results truncated (limit: 500 matches)\n"

        output += "\n## Matches by File\n\n"

        # Show top matches per file
        for file_path, matches in list(result["matches_by_file"].items())[:20]:
            output += f"### {file_path} ({len(matches)} matches)\n\n"
            for match in matches[:10]:  # Top 10 per file
                output += f"Line {match['line_number']}: {match['line_content']}\n"
            if len(matches) > 10:
                output += f"... +{len(matches) - 10} more matches\n"
            output += "\n"

        if len(result["matches_by_file"]) > 20:
            output += f"... +{len(result['matches_by_file']) - 20} more files\n"

        return output

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def get_file_context(
    file_path: str,
    line: int,
    context_lines: int = 5,
) -> str:
    """
    Get surrounding lines around a specific line in a file.

    Args:
        file_path: Path to file
        line: 1-indexed line number
        context_lines: Number of lines before and after (default: 5)
    """
    try:
        result = editor.get_file_context(Path(file_path), line, context_lines)

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        output = f"""# File Context: {result['file_path']}

Line {result['target_line_number']} of {result['total_lines']}

```python
"""

        # Before lines
        for line_num, line_content in zip(
            result["before_line_numbers"], result["before_lines"]
        ):
            output += f"{line_num:4d} | {line_content}\n"

        # Target line (highlighted)
        target_line = result["target_line_content"]
        target_num = result["target_line_number"]
        output += f"{target_num:4d} | {target_line}  ← Target line\n"

        # After lines
        for line_num, line_content in zip(
            result["after_line_numbers"], result["after_lines"]
        ):
            output += f"{line_num:4d} | {line_content}\n"

        output += "```\n"

        return output

    except Exception as e:
        logger.error(f"Get file context failed: {e}")
        return f"❌ Error: {e}"


@mcp.tool()
def parse_errors(
    error_output: str,
    file_path: str = "",
) -> str:
    """
    Parse and structure error messages from code execution or tests.

    Args:
        error_output: Error message string (from stderr or stdout)
        file_path: Optional file path for context
    """
    try:
        result = error_parser.parse_errors(
            error_output, file_path if file_path else None
        )

        if not result["success"]:
            return f"❌ {result.get('error', 'Unknown error')}"

        output = f"""# Error Analysis

Language: {result['language']}
Total Errors: {result['total_errors']}

## Summary
"""

        summary = result["summary"]
        if summary.get("by_type"):
            output += "\nBy Type:\n"
            for error_type, count in summary["by_type"].items():
                output += f"- {error_type}: {count}\n"

        if summary.get("by_file"):
            output += "\nBy File:\n"
            for file_path, count in list(summary["by_file"].items())[:10]:
                output += f"- {file_path}: {count}\n"

        output += "\n## Errors\n\n"

        # Show errors
        for i, error in enumerate(result["errors"][:20], 1):
            output += f"### Error {i}\n"
            if error.get("file"):
                output += f"File: {error['file']}\n"
            if error.get("line"):
                output += f"Line: {error['line']}\n"
            if error.get("column"):
                output += f"Column: {error['column']}\n"
            output += f"Type: {error.get('error_type', 'unknown')}\n"
            output += f"Message: {error.get('message', 'N/A')}\n\n"

        if len(result["errors"]) > 20:
            output += f"... +{len(result['errors']) - 20} more errors\n\n"

        # Suggestions
        if result.get("suggestions"):
            output += "## Suggestions\n\n"
            for suggestion in result["suggestions"]:
                output += f"- {suggestion}\n"

        return output

    except Exception as e:
        logger.error(f"Error parsing failed: {e}")
        return f"❌ Error: {e}"


if __name__ == "__main__":
    mcp.run()
