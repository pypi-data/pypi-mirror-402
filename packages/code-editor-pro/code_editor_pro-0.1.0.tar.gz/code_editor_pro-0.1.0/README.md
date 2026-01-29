# Code Editor Pro

**Professional code editing and analysis server, optimized for Claude Sonnet 4.5**

Multi-language support (Python/JS/TS/Go/Rust/Java/C++) with intelligent caching and hybrid string/AST editing.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](.)

## ✨ Quick Start

```bash
# Install from PyPI
pip install code-editor-pro

# CLI mode (interactive tools)
cep --help
cep edit file.py --old "x" --new "y"

# MCP server mode (for Claude/AI clients)
cep --mcp

# Or with Docker
docker-compose up -d
```

---

## 🚀 Features

### Core Editing
- **Hybrid Edit System**: Automatic mode selection (string/AST)
- **Preview Mode**: See changes before applying (unified diff)
- **Atomic Operations**: Apply multiple edits safely
- **Undo Support**: Rollback changes

### Multi-Language Analysis
- **Universal Parser**: Tree-sitter-based (160+ languages)
- **Code Inspection**: Functions, classes, imports
- **Quality Analysis**: Complexity, code smells, metrics
- **Dependency Tracking**: Import categorization

### Performance Optimizations
- **Intelligent Caching**: 15min TTL, file-change detection
- **Token Efficiency**: Reduced from 66k → 15k tokens (-77%)
- **Response Filtering**: Max 50 items per response
- **Summarization**: Key metrics instead of full dumps

---

## 📦 Installation

### Local Installation

```bash
# Using pip from PyPI (recommended)
pip install code-editor-pro

# Run as CLI (Code Editor Pro)
cep inspect file.py
cep edit file.py --old "x" --new "y"
cep --help

# Or as MCP server
cep --mcp

# Or install from source with uv
cd code_editor_pro
uv sync
uv run cep --help

# Or install from source with pip
pip install -e .
cep --mcp

# Optional: Install dev dependencies
uv sync --extra dev

# Optional: Install Redis caching
uv sync --extra cache

# Optional: Install Git support
uv sync --extra git

# Optional: Install LSP support
uv sync --extra lsp
```

### Docker Installation

```bash
# Build image
docker build -t code-editor-pro .

# Run container
docker run -d \
  --name code-editor-pro \
  -p 8000:8000 \
  -v /path/to/project:/workspace:ro \
  code-editor-pro

# Or use docker-compose
docker-compose up -d
```

See [DOCKER.md](DOCKER.md) for detailed Docker usage.

---

## 🛠️ Available Tools (31 Total)

### **Editing (5 tools)**

#### `edit`
Edit code with automatic mode selection. Use `preview=True` to see changes without applying.
```python
# Apply changes
edit(
    file_path="example.py",
    old="def old_name():",
    new="def new_name():",
    mode="auto",  # auto/string/ast
    replace_all=False
)

# Preview changes (without applying)
edit(
    file_path="example.py",
    old="def old_name():",
    new="def new_name():",
    preview=True
)
```

#### `apply_edits`
Apply multiple edits atomically.
```python
apply_edits(
    file_path="example.py",
    edits=[
        {"old": "foo", "new": "bar"},
        {"old": "x", "new": "value", "replace_all": True}
    ]
)
```

#### `undo`
Undo last edit.
```python
undo(file_path="example.py")
```

#### `format_code`
Format code (auto-detects: black for Python, LSP for TS/Java/C++/Go/Rust).
```python
format_code(file_path="example.py", formatter="auto")  # auto-detects
format_code(file_path="example.ts", formatter="auto")  # uses LSP
```

---

### **Analysis (3 tools)**

#### `inspect`
Analyze code structure. Auto-detects: Python/JS/TS/Go/Rust/Java/C++
```python
inspect(file_path="example.py")
# Returns: functions, classes, imports, line_count
```

#### `analyze`
Deep quality analysis (complexity, smells, metrics).
```python
analyze(file_path="example.py")
# Returns: complexity, code smells, function metrics
```

#### `dependencies`
Analyze imports and dependencies.
```python
dependencies(file_path="example.py")
# Returns: stdlib, third-party, local imports
```

---

### **Transformations (2 tools)**

#### `transform`
Apply AST transformations (Python only).
```python
transform(
    file_path="example.py",
    operations=[
        "add_type_hints",
        "clean_unused_imports",
        "remove_dead_code",
        "optimize_code"
    ]
)
```

#### `lint`
Lint code (ruff for Python).
```python
lint(file_path="example.py", linter="ruff")
```

---

### **Project Management (3 tools)**

#### `project_create`
Create project workspace.
```python
project_create(
    name="my-project",
    path="/path/to/project",
    language="python"
)
```

#### `project_add_file`
Add file to project.
```python
project_add_file(
    project_id="proj_123456",
    file_path="/path/to/file.py"
)
```

#### `project_stats`
Get project statistics.
```python
project_stats(project_id="proj_123456")
# Returns: files, lines, size, languages
```

---

---

### **IDE Features (5 tools - Auto-LSP)**

#### `complete`
Get code completions at cursor position (auto-uses LSP for TS/Java/C++/Go/Rust).
```python
complete(
    file_path="example.py",  # or example.ts
    line=10,
    column=5
)
```

#### `goto_definition`
Jump to definition of symbol at cursor (auto-uses LSP).
```python
goto_definition(
    file_path="example.py",
    line=10,
    column=5
)
```

#### `find_references`
Find all references to symbol at cursor (auto-uses LSP).
```python
find_references(
    file_path="example.py",
    line=10,
    column=5
)
```

#### `signature_help`
Get function signature help at cursor.
```python
signature_help(
    file_path="example.py",
    line=10,
    column=5
)
```

#### `hover`
Get hover information (docstring + signature, auto-uses LSP).
```python
hover(
    file_path="example.py",
    line=10,
    column=5
)
```

**Note:** LSP features are automatically used by `complete`, `goto_definition`, `find_references`, `hover`, and `format_code` for supported languages (TypeScript/Java/C++/Go/Rust). No separate LSP tools needed.

### **IDE Features (5 tools - Auto-LSP)**

#### `complete`
Get code completions at cursor position (auto-uses LSP for TS/Java/C++/Go/Rust).
```python
complete(
    file_path="example.py",  # or example.ts
    line=10,
    column=5
)
```

#### `goto_definition`
Jump to definition of symbol at cursor (auto-uses LSP).
```python
goto_definition(
    file_path="example.py",
    line=10,
    column=5
)
```

#### `find_references`
Find all references to symbol at cursor (auto-uses LSP).
```python
find_references(
    file_path="example.py",
    line=10,
    column=5
)
```

#### `signature_help`
Get function signature help at cursor.
```python
signature_help(
    file_path="example.py",
    line=10,
    column=5
)
```

#### `hover`
Get hover information (docstring + signature, auto-uses LSP).
```python
hover(
    file_path="example.py",
    line=10,
    column=5
)
```

### **Search & Context (3 tools)**

#### `search_across_files`
Search for pattern across multiple files in project.
```python
# Plain text search
search_across_files(
    pattern="def calculate",
    project_path="./project",
    file_extensions=[".py"]  # optional filter
)

# Regex search
search_across_files(
    pattern=r"def \w+",
    project_path="./project",
    use_regex=True
)
```

#### `get_file_context`
Get surrounding lines around a specific line.
```python
get_file_context(
    file_path="example.py",
    line=42,
    context_lines=5  # lines before/after
)
```

#### `parse_errors`
Parse and structure error messages from execution/tests.
```python
parse_errors(
    error_output=stderr_output,
    file_path="example.py"  # optional for context
)
# Returns: structured errors, summary, suggestions
```

---

#### `execute_code`
Execute code file with timeout and sandboxing.
```python
execute_code(
    file_path="script.py",
    args=["arg1", "arg2"],
    env={"VAR": "value"},
    timeout=30
)
```

#### `run_tests`
Run tests with auto-detected framework (pytest/jest/junit).
```python
run_tests(
    project_path="./project",
    test_pattern="test_*",
    framework="auto"  # auto/pytest/jest/junit
)
```

#### `check_coverage`
Check test coverage for project or file.
```python
check_coverage(
    file_path="module.py",
    project_path="./project"
)
```

### **Git Integration (1 tool)**

#### `git`
Git operations: status, diff, commit, log, branches.
```python
# Status
git(operation="status", project_path="./project")

# Diff
git(operation="diff", file_path="example.py", project_path="./project")

# Commit
git(operation="commit", message="Fix bug", files=["file1.py"], project_path="./project")

# Log
git(operation="log", limit=10, file_path="example.py", project_path="./project")

# Branches
git(operation="branches", project_path="./project")
```

### **Refactoring Tools (5 tools)**

#### `rename_symbol`
Rename symbol across multiple files.
```python
rename_symbol(
    file_path="example.py",
    line=10,
    column=5,
    new_name="new_function",
    scope="project"  # file or project
)
```

#### `extract_method`
Extract code block to new method.
```python
extract_method(
    file_path="example.py",
    start_line=5,
    end_line=10,
    method_name="new_method"
)
```

#### `extract_variable`
Extract expression to variable.
```python
extract_variable(
    file_path="example.py",
    line=10,
    column=5,
    variable_name="result"
)
```

#### `inline_symbol`
Inline variable or method call.
```python
inline_symbol(
    file_path="example.py",
    line=10,
    column=5
)
```

#### `move_symbol`
Move symbol to different file.
```python
move_symbol(
    file_path="source.py",
    line=10,
    column=5,
    target_file="target.py"
)
```

### **Code Generation Tools (2 tools)**

#### `generate_code`
Generate code: template, test, or boilerplate.
```python
# From template
generate_code(
    type="template",
    template="python_class.py.template",
    output_path="MyClass.py",
    variables={"class_name": "MyClass"}
)

# Generate test
generate_code(
    type="test",
    file_path="module.py",
    output_path="tests/test_module.py",
    test_framework="auto"
)

# Generate boilerplate
generate_code(
    type="boilerplate",
    language="python",
    name="MyClass",
    output_path="MyClass.py"
)
```

#### `scaffold_project`
Scaffold project structure.
```python
scaffold_project(
    project_type="python",  # python/ts/go/rust
    path="./new_project",
    options={"name": "my_project", "description": "Description"}
)
```

---

### LSP Integration
- **TypeScript/JavaScript**: typescript-language-server support
- **Java**: JDT Language Server support
- **C++**: clangd support
- **Go**: gopls support
- **Rust**: rust-analyzer support
- **Auto-Detection**: Automatically uses LSP for supported languages
- **Fallback**: Falls back to tree-sitter if LSP unavailable

### Code Execution & Testing
- **Multi-language Execution**: Python, Node.js, Java, C++
- **Sandboxed Execution**: Timeout protection and process isolation
- **Test Framework Support**: pytest, jest, JUnit
- **Coverage Analysis**: Test coverage reporting

### Git Integration
- **Unified Tool**: Single `git(operation=...)` tool for all operations
- **Operations**: status, diff, commit, log, branches
- **Safe Operations**: Error handling and validation
- **GitPython Support**: Uses GitPython when available, falls back to subprocess

### Refactoring Tools (Phase 2)
- **Multi-file Rename**: Rename symbols across entire project
- **Extract Method/Variable**: Extract code blocks to new functions/variables
- **Inline Symbol**: Inline variables and method calls
- **Move Symbol**: Move symbols between files
- **LSP-based Refactoring**: Uses LSP for TypeScript/Java/C++/Go/Rust

### Code Generation (Phase 2)
- **Unified Tool**: Single `generate_code(type=...)` tool for templates, tests, and boilerplate
- **Types**: template, test, boilerplate
- **Project Scaffolding**: Separate `scaffold_project` tool for project structures
- **Auto-Detection**: Automatically detects test framework and boilerplate type

## 🏗️ Architecture

```
code_editor_pro/
├── src/code_editor_pro/
│   ├── server.py              # MCP server (28 tools, optimized!)
│   ├── core/
│   │   ├── editor.py          # Hybrid editing (string/AST)
│   │   ├── parser.py          # Multi-language (tree-sitter)
│   │   ├── analyzer.py        # inspect, analyze, dependencies
│   │   ├── intellisense.py    # Jedi-based IDE features + LSP
│   │   ├── cache.py           # Intelligent caching
│   │   ├── lsp_client.py      # LSP client (TS/Java/C++/Go/Rust)
│   │   ├── executor.py        # Code execution & testing
│   │   ├── git_client.py      # Git operations
│   │   ├── refactor.py        # Refactoring engine
│   │   └── generator.py        # Code generation & scaffolding
│   ├── languages/
│   │   └── python.py          # Python-specific AST ops
│   ├── templates/              # Code generation templates
│   │   ├── python_*.template
│   │   ├── typescript_*.template
│   │   ├── go_*.template
│   │   └── rust_*.template
│   ├── project/
│   │   ├── manager.py         # Project management
│   │   └── database.py        # SQLite storage
│   └── models.py              # Pydantic models
├── pyproject.toml
└── README.md
```

---

## 📊 Dependencies (9 Core + Optional)

| Package | Purpose | Size |
|---------|---------|------|
| `mcp` | Model Context Protocol | Core |
| `tree-sitter-languages` | 160+ language parsers | 120MB |
| `jedi` | Python completions | 5MB |
| `black` | Python formatting | 2MB |
| `ruff` | Fast Python linting | 10MB |
| `pydantic` | Data models | 3MB |
| `loguru` | Logging | 0.5MB |
| `GitPython` | Git operations (optional) | 5MB |
| `psutil` | Process management | 2MB |
| `pygls` | LSP client (optional) | 3MB |

**Total:** ~150MB (core) + 10MB (optional)

**Optional Extras:**
- `redis` - Distributed caching
- `GitPython` - Enhanced Git support
- `pygls` - LSP client library

---

## 🎯 Token Optimization (Sonnet 4.5)

### Before (v1.0)
- **Tool Schemas:** 66k tokens
- **Tool Count:** 25 tools
- **Response Size:** Unlimited (crashes on large files)

### After (v0.1.0)
- **Tool Schemas:** 15k tokens (-77%)
- **Tool Count:** 31 tools
- **Response Size:** Max 50 items + truncation warnings

### Improvements
1. **Concise Descriptions:** Removed verbose examples
2. **Server-Side Filtering:** Pagination + summarization
3. **Intelligent Caching:** 95% reduction on repeated analyses
4. **Response Summarization:** Key metrics instead of full data

---

## 🚦 Usage Examples

### Basic Editing
```python
# Preview change (without applying)
edit(file_path="app.py", old="def foo():", new="def bar():", preview=True)

# Apply if satisfied
edit(file_path="app.py", old="def foo():", new="def bar()", mode="ast")

# Undo if needed
undo(file_path="app.py")
```

### Multi-File Analysis
```python
# Analyze Python file
result = inspect(file_path="app.py")
# Functions: 42, Classes: 5, Imports: 18

# Check quality
result = analyze(file_path="app.py")
# Complexity: 87, High complexity: 3 functions

# Fix issues
transform(
    file_path="app.py",
    operations=["add_type_hints", "clean_unused_imports"]
)
```

### Project Workflow
```python
# Create project
project = project_create(name="my-app", path="/workspace", language="python")

# Add files
project_add_file(project_id=project.id, file_path="/workspace/main.py")
project_add_file(project_id=project.id, file_path="/workspace/utils.py")

# Get stats
stats = project_stats(project_id=project.id)
# Files: 2, Lines: 450, Size: 0.02 MB
```

### IDE Features (IntelliSense + Auto-LSP)
```python
# Code completion (auto-uses LSP for TS/Java/C++/Go/Rust)
complete(file_path="app.ts", line=42, column=10)

# Jump to definition (auto-uses LSP)
goto_definition(file_path="app.ts", line=42, column=10)

# Find all usages (auto-uses LSP)
find_references(file_path="app.ts", line=42, column=10)

# Get signature help
signature_help(file_path="app.py", line=42, column=10)

# Hover documentation (auto-uses LSP)
hover(file_path="app.ts", line=42, column=10)
```

### Git Operations
```python
# Git status
git(operation="status", project_path="./project")

# Git diff
git(operation="diff", file_path="app.py", project_path="./project")

# Git commit
git(operation="commit", message="Fix bug", files=["app.py"], project_path="./project")
```

### Refactoring Operations
```python
# Rename symbol across project
rename_symbol(
    file_path="app.py",
    line=15,
    column=4,
    new_name="new_function",
    scope="project"
)
# Returns: Files changed: 3, Changes: 12

# Extract method from code block
extract_method(
    file_path="app.py",
    start_line=20,
    end_line=25,
    method_name="calculate_total"
)
# Returns: Method extracted, lines: 6

# Extract variable from expression
extract_variable(
    file_path="app.py",
    line=30,
    column=10,
    variable_name="result"
)
# Returns: Variable extracted
```

### Code Generation
```python
# Scaffold new project
scaffold_project(
    project_type="python",
    path="./my_project",
    options={"name": "my_project", "description": "A project"}
)

# Generate test file
generate_code(
    type="test",
    file_path="module.py",
    output_path="tests/test_module.py"
)

# Generate boilerplate
generate_code(
    type="boilerplate",
    language="python",
    name="MyClass",
    output_path="MyClass.py"
)

# Generate from template
generate_code(
    type="template",
    template="python_class.py.template",
    output_path="MyClass.py",
    variables={"class_name": "MyClass"}
)
```

---

## ⚡ Performance Benchmarks

| Operation | Old | New (v0.1.0) | Improvement |
|-----------|-----|--------------|-------------|
| First analysis | 3.2s | 2.8s | -12% |
| Cached analysis | N/A | 0.05s | **-98%** |
| Token usage (schemas) | 66k | 15k | **-77%** |
| Response size (large file) | 500k chars | 10k chars | **-98%** |
| Code completion | N/A | 0.3s | New! |
| Goto definition | N/A | 0.2s | New! |

---

## 🔧 Configuration

### MCP Client Integration (Claude Desktop)

```json
{
  "mcpServers": {
    "code-editor": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/code_editor_pro", "python", "-m", "code_editor_pro"]
    }
  }
}
```

### Cache Settings (Optional)

```python
# Adjust TTL in core/cache.py
cache = AnalysisCache(ttl_seconds=900)  # Default: 15 minutes
```

---

## 🐛 Troubleshooting

### Tree-sitter not working?
```bash
# Install manually if auto-install fails
pip install tree-sitter-languages
```

### Ruff not found?
```bash
# Install ruff
uv add ruff
# Or pip install ruff
```

### Cache too large?
```python
# Cache is handled internally and auto-expires after 15 minutes
# No manual cache clearing needed - it's automatic!
```

---

## 📝 Changelog

### v0.1.0 (2025-11-12) - Initial Release
- ✅ Multi-file search: `search_across_files()` - Search patterns across entire project
- ✅ File context: `get_file_context()` - Get surrounding lines around specific location
- ✅ Error parsing: `parse_errors()` - Parse and structure error messages with suggestions
- ✅ 31 powerful tools for code editing and analysis
- ✅ Multi-language support (Python/JS/TS/Go/Rust/Java/C++)
- ✅ LSP Integration for enhanced IDE features
- ✅ Git Integration for version control
- ✅ Code Execution & Testing tools
- ✅ Refactoring Tools (Rename, Extract, Inline, Move)
- ✅ Code Generation & Scaffolding
- ✅ Docker support with multi-stage builds
- ✅ Intelligent caching system
- ✅ Token-optimized for AI agents

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📧 Contact

- **Author**: Björn Bethge
- **Email**: bjoern.bethge@gmail.com

---

**Made with ❤️ for the AI development community**
