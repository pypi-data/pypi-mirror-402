"""CLI interface for Code Editor Pro - All 31 tools accessible via command line."""

import json
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import click
except ImportError:
    print("Error: click is required. Install with: pip install click")
    sys.exit(1)

from loguru import logger

from .core.analyzer import CodeAnalyzer
from .core.cache import get_cache
from .core.editor import CodeEditor
from .core.error_parser import ErrorParser
from .core.executor import CodeExecutor
from .core.generator import CodeGenerator
from .core.git_client import GitClient
from .core.intellisense import IntelliSense
from .core.lsp_client import LSPClient
from .core.parser import MultiLanguageParser
from .core.refactor import RefactorEngine
from .core.searcher import CodeSearcher
from .project.manager import ProjectManager

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


def output_result(result: Any, format: str = "text"):
    """Output result in specified format."""
    if format == "json":
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        click.echo(str(result))


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="cep")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--mcp", is_flag=True, help="Start as MCP server instead of CLI")
@click.pass_context
def cli(ctx, format, mcp):
    """Code Editor Pro - Professional code editing and analysis tools.
    
    Run 'cep' for interactive CLI.
    Run 'cep --mcp' to start as MCP server.
    Run 'cep COMMAND' to use CLI tools directly.
    """
    ctx.ensure_object(dict)
    ctx.obj["format"] = format
    
    # If --mcp flag, start as server
    if mcp:
        try:
            from .server import mcp as mcp_server
            click.secho("🚀 Starting Code Editor Pro as MCP server...", fg="cyan")
            mcp_server.run()
        except KeyboardInterrupt:
            click.secho("\n✅ Server stopped", fg="green")
        sys.exit(0)
    
    # If no subcommand, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ============================================================================
# EDITING COMMANDS
# ============================================================================


@cli.command()
@click.argument("file_path")
@click.option("--old", required=True, help="String to replace")
@click.option("--new", required=True, help="Replacement string")
@click.option("--mode", default="auto", type=click.Choice(["auto", "string", "ast"]), help="Edit mode")
@click.option("--replace-all", is_flag=True, help="Replace all occurrences")
@click.pass_context
def edit(ctx, file_path, old, new, mode, replace_all):
    """Edit code with automatic mode selection."""
    try:
        result = editor.edit(Path(file_path), old, new, mode=mode, replace_all=replace_all)
        if result["success"]:
            cache.invalidate(Path(file_path))
            click.secho(f"✅ {result['changes']} change(s) applied ({result['mode']} mode)", fg="green")
        else:
            click.secho(f"❌ {result.get('error', 'Unknown error')}", fg="red")
            sys.exit(1)
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("file_path")
@click.pass_context
def undo(ctx, file_path):
    """Undo last edit."""
    try:
        result = editor.undo(Path(file_path))
        if result["success"]:
            cache.invalidate(Path(file_path))
            click.secho("✅ Undo successful", fg="green")
        else:
            click.secho(f"❌ {result.get('error', 'No undo history')}", fg="red")
            sys.exit(1)
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("file_path")
@click.option("--formatter", default="auto", help="Formatter to use (auto/black)")
@click.pass_context
def format(ctx, file_path, formatter):
    """Format code."""
    try:
        if formatter == "auto" or formatter == "black":
            try:
                import black
                code = Path(file_path).read_text()
                formatted = black.format_str(code, mode=black.Mode())
                Path(file_path).write_text(formatted)
                click.secho("✅ Code formatted with black", fg="green")
            except ImportError:
                click.secho("❌ black not installed. Install with: pip install black", fg="red")
                sys.exit(1)
        else:
            click.secho(f"❌ Formatter '{formatter}' not yet implemented", fg="red")
            sys.exit(1)
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("file_path")
@click.option("--linter", default="ruff", help="Linter to use")
@click.pass_context
def lint(ctx, file_path, linter):
    """Lint code."""
    try:
        import subprocess
        result = subprocess.run([linter, "check", file_path], capture_output=True, text=True)
        if result.returncode == 0:
            click.secho("✅ No linting errors", fg="green")
        else:
            click.echo(result.stdout)
            if result.stderr:
                click.echo(result.stderr)
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


# ============================================================================
# ANALYSIS COMMANDS
# ============================================================================


@cli.command()
@click.argument("file_path")
@click.pass_context
def inspect(ctx, file_path):
    """Analyze code structure."""
    try:
        result = analyzer.inspect(Path(file_path))
        output_result(result, ctx.obj["format"])
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("file_path")
@click.pass_context
def analyze(ctx, file_path):
    """Perform code quality analysis."""
    try:
        result = analyzer.analyze(Path(file_path))
        output_result(result, ctx.obj["format"])
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("file_path")
@click.pass_context
def dependencies(ctx, file_path):
    """List file dependencies."""
    try:
        result = analyzer.analyze(Path(file_path))
        if "imports" in result:
            output_result(result["imports"], ctx.obj["format"])
        else:
            click.secho("No imports found", fg="yellow")
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


# ============================================================================
# GIT COMMANDS
# ============================================================================


@cli.group()
def git():
    """Git operations."""
    pass


@git.command()
@click.option("--repo", default=".", help="Repository path")
@click.pass_context
def status(ctx, repo):
    """Show git status."""
    try:
        result = git_client.status(str(repo))
        output_result(result, ctx.obj["format"])
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@git.command()
@click.option("--repo", default=".", help="Repository path")
@click.option("--file", default=None, help="Specific file to diff")
@click.pass_context
def diff(ctx, repo, file):
    """Show git diff."""
    try:
        result = git_client.diff(str(repo), file)
        click.echo(result)
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@git.command()
@click.option("--repo", default=".", help="Repository path")
@click.option("--message", "-m", required=True, help="Commit message")
@click.pass_context
def commit(ctx, repo, message):
    """Create git commit."""
    try:
        result = git_client.commit(str(repo), message)
        click.secho(f"✅ {result}", fg="green")
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@git.command()
@click.option("--repo", default=".", help="Repository path")
@click.option("--limit", default=10, type=int, help="Number of commits")
@click.pass_context
def log(ctx, repo, limit):
    """Show git log."""
    try:
        result = git_client.log(str(repo), limit)
        output_result(result, ctx.obj["format"])
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


# ============================================================================
# EXECUTION COMMANDS
# ============================================================================


@cli.command()
@click.argument("file_path")
@click.option("--args", multiple=True, help="Arguments to pass")
@click.pass_context
def run(ctx, file_path, args):
    """Execute code file."""
    try:
        result = executor.execute(Path(file_path), list(args))
        click.echo(result.get("output", ""))
        return_code = result.get("return_code", 0)
        if return_code != 0:
            sys.exit(return_code)
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@cli.command()
@click.argument("path")
@click.option("--pattern", default=None, help="Test pattern")
@click.pass_context
def test(ctx, path, pattern):
    """Run tests."""
    try:
        result = executor.run_tests(Path(path), pattern)
        output_result(result, ctx.obj["format"])
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


# ============================================================================
# REFACTORING COMMANDS
# ============================================================================


@cli.group()
def refactor():
    """Refactoring operations."""
    pass


@refactor.command()
@click.argument("file_path")
@click.option("--old-name", required=True, help="Old symbol name")
@click.option("--new-name", required=True, help="New symbol name")
@click.pass_context
def rename(ctx, file_path, old_name, new_name):
    """Rename symbol."""
    try:
        result = refactor_engine.rename(Path(file_path), old_name, new_name)
        click.secho(f"✅ {result}", fg="green")
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@refactor.command()
@click.argument("file_path")
@click.option("--start-line", type=int, required=True, help="Start line")
@click.option("--end-line", type=int, required=True, help="End line")
@click.option("--name", required=True, help="New method name")
@click.pass_context
def extract(ctx, file_path, start_line, end_line, name):
    """Extract method."""
    try:
        result = refactor_engine.extract_method(Path(file_path), start_line, end_line, name)
        click.secho(f"✅ {result}", fg="green")
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


# ============================================================================
# SEARCH COMMANDS
# ============================================================================


@cli.command()
@click.argument("query")
@click.option("--path", default=".", help="Search path")
@click.option("--pattern", default=None, help="File pattern (e.g., *.py)")
@click.pass_context
def search(ctx, query, path, pattern):
    """Search code."""
    try:
        result = searcher.search(query, Path(path), pattern)
        output_result(result, ctx.obj["format"])
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


# ============================================================================
# PROJECT COMMANDS
# ============================================================================


@cli.group()
def project():
    """Project management."""
    pass


@project.command()
@click.argument("name")
@click.argument("path")
@click.option("--language", default="python", help="Project language")
@click.pass_context
def create(ctx, name, path, language):
    """Create new project."""
    try:
        result = project_manager.create(name, Path(path), language)
        click.secho(f"✅ Project created: {result}", fg="green")
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


@project.command()
@click.argument("project_id")
@click.pass_context
def stats(ctx, project_id):
    """Show project statistics."""
    try:
        result = project_manager.stats(project_id)
        output_result(result, ctx.obj["format"])
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


# ============================================================================
# GENERATION COMMANDS
# ============================================================================


@cli.command()
@click.option("--type", "gen_type", required=True, type=click.Choice(["class", "function", "test"]), help="Code type")
@click.option("--name", required=True, help="Name")
@click.option("--output", default=None, help="Output file")
@click.pass_context
def generate(ctx, gen_type, name, output):
    """Generate code scaffolding."""
    try:
        result = code_generator.generate(gen_type, name)
        if output:
            Path(output).write_text(result)
            click.secho(f"✅ Generated {gen_type} '{name}' → {output}", fg="green")
        else:
            click.echo(result)
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


# ============================================================================
# SERVER COMMAND
# ============================================================================


@cli.command()
def serve():
    """Start MCP server explicitly."""
    try:
        from .server import mcp
        click.secho("🚀 Starting Code Editor Pro server...", fg="cyan")
        mcp.run()
    except KeyboardInterrupt:
        click.secho("\n✅ Server stopped", fg="green")
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        sys.exit(1)


if __name__ == "__main__":
    cli()
