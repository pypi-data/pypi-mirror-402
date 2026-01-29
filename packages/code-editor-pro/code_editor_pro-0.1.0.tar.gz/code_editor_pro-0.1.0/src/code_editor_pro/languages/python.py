"""Python-specific AST operations (refactored from ast_transforms.py)."""

import ast
from typing import Any, Dict, List, Literal, Optional

from loguru import logger


class PythonEditor:
    """Python AST-based editing operations."""

    @staticmethod
    def add_type_hints(code: str) -> str:
        """Add type hints to functions."""
        try:
            tree = ast.parse(code)

            class TypeHintAdder(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    if not node.returns:
                        node.returns = ast.Name(id="Any", ctx=ast.Load())
                    for arg in node.args.args:
                        if not arg.annotation:
                            arg.annotation = ast.Name(id="Any", ctx=ast.Load())
                    return self.generic_visit(node)

                def visit_AsyncFunctionDef(self, node):
                    if not node.returns:
                        node.returns = ast.Name(id="Any", ctx=ast.Load())
                    for arg in node.args.args:
                        if not arg.annotation:
                            arg.annotation = ast.Name(id="Any", ctx=ast.Load())
                    return self.generic_visit(node)

            transformer = TypeHintAdder()
            new_tree = transformer.visit(tree)
            return ast.unparse(new_tree)

        except Exception as e:
            logger.error(f"Type hint addition failed: {e}")
            raise

    @staticmethod
    def clean_unused_imports(code: str) -> str:
        """Remove unused imports."""
        try:
            tree = ast.parse(code)
            used_names = set()

            # Collect used names
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    used_names.add(node.attr)

            # Filter imports
            class ImportCleaner(ast.NodeTransformer):
                def visit_Module(self, node):
                    new_body = []
                    for item in node.body:
                        if isinstance(item, ast.Import):
                            # Keep if any alias is used
                            if any(
                                alias.name in used_names
                                or (alias.asname and alias.asname in used_names)
                                for alias in item.names
                            ):
                                new_body.append(item)
                        elif isinstance(item, ast.ImportFrom):
                            # Keep if any import is used
                            if any(
                                alias.name in used_names
                                or (alias.asname and alias.asname in used_names)
                                for alias in item.names
                            ):
                                new_body.append(item)
                        else:
                            new_body.append(item)
                    node.body = new_body
                    return node

            transformer = ImportCleaner()
            new_tree = transformer.visit(tree)
            return ast.unparse(new_tree)

        except Exception as e:
            logger.error(f"Import cleaning failed: {e}")
            raise

    @staticmethod
    def remove_dead_code(code: str) -> str:
        """Remove unused functions and classes."""
        try:
            tree = ast.parse(code)
            used_functions = set()
            used_classes = set()

            # Collect used names
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        used_functions.add(node.func.id)
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_classes.add(node.id)

            # Remove unused
            class DeadCodeRemover(ast.NodeTransformer):
                def visit_Module(self, node):
                    new_body = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            # Keep if used or starts with _
                            if item.name in used_functions or item.name.startswith("_"):
                                new_body.append(item)
                        elif isinstance(item, ast.ClassDef):
                            # Keep if used or starts with _
                            if item.name in used_classes or item.name.startswith("_"):
                                new_body.append(item)
                        else:
                            new_body.append(item)
                    node.body = new_body
                    return node

            transformer = DeadCodeRemover()
            new_tree = transformer.visit(tree)
            return ast.unparse(new_tree)

        except Exception as e:
            logger.error(f"Dead code removal failed: {e}")
            raise

    @staticmethod
    def optimize_code(code: str) -> str:
        """Optimize code (sort imports, etc.)."""
        try:
            tree = ast.parse(code)

            class CodeOptimizer(ast.NodeTransformer):
                def visit_Module(self, node):
                    # Separate imports from other code
                    imports = []
                    other = []

                    for item in node.body:
                        if isinstance(item, (ast.Import, ast.ImportFrom)):
                            imports.append(item)
                        else:
                            other.append(item)

                    # Sort imports by module name
                    imports.sort(
                        key=lambda x: (
                            isinstance(x, ast.ImportFrom),
                            getattr(x, "module", None) or "",
                        )
                    )

                    # Rebuild module
                    node.body = imports + other
                    return node

            transformer = CodeOptimizer()
            new_tree = transformer.visit(tree)
            return ast.unparse(new_tree)

        except Exception as e:
            logger.error(f"Code optimization failed: {e}")
            raise

    @staticmethod
    def get_complexity(code: str) -> int:
        """Calculate cyclomatic complexity."""
        try:
            tree = ast.parse(code)
            complexity = 1

            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            return complexity

        except SyntaxError:
            return 1

    @staticmethod
    def get_function_metrics(code: str) -> List[Dict[str, Any]]:
        """Get metrics for all functions."""
        try:
            tree = ast.parse(code)
            metrics = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    metrics.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "end_line": node.end_lineno or node.lineno,
                            "args_count": len(node.args.args),
                            "complexity": PythonEditor._node_complexity(node),
                            "has_docstring": bool(ast.get_docstring(node)),
                            "has_type_hints": bool(
                                node.returns
                                or any(arg.annotation for arg in node.args.args)
                            ),
                        }
                    )

            return metrics

        except SyntaxError:
            return []

    @staticmethod
    def _node_complexity(node: ast.AST) -> int:
        """Calculate complexity for a node."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        return complexity

    @staticmethod
    def find_code_smells(code: str) -> List[Dict[str, Any]]:
        """Find code smells."""
        try:
            tree = ast.parse(code)
            smells = []

            for node in ast.walk(tree):
                # Long parameter lists
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if len(node.args.args) > 5:
                        smells.append(
                            {
                                "type": "long_parameter_list",
                                "line": node.lineno,
                                "function": node.name,
                                "parameter_count": len(node.args.args),
                                "severity": "warning",
                            }
                        )

                    # Missing docstring
                    if not ast.get_docstring(node) and not node.name.startswith("_"):
                        smells.append(
                            {
                                "type": "missing_docstring",
                                "line": node.lineno,
                                "function": node.name,
                                "severity": "info",
                            }
                        )

                    # High complexity
                    complexity = PythonEditor._node_complexity(node)
                    if complexity > 10:
                        smells.append(
                            {
                                "type": "high_complexity",
                                "line": node.lineno,
                                "function": node.name,
                                "complexity": complexity,
                                "severity": "warning",
                            }
                        )

            return smells

        except SyntaxError:
            return []


def rename_symbol(
    tree: ast.AST,
    old_name: str,
    new_name: str,
    symbol_type: Literal["function", "class", "variable", "all"] = "all",
) -> ast.AST:
    """Rename a symbol in the AST."""

    class Renamer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if symbol_type in ["function", "all"] and node.name == old_name:
                node.name = new_name
            return self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            if symbol_type in ["function", "all"] and node.name == old_name:
                node.name = new_name
            return self.generic_visit(node)

        def visit_ClassDef(self, node):
            if symbol_type in ["class", "all"] and node.name == old_name:
                node.name = new_name
            return self.generic_visit(node)

        def visit_Name(self, node):
            if symbol_type in ["variable", "all"] and node.id == old_name:
                node.id = new_name
            return node

    transformer = Renamer()
    return transformer.visit(tree)


def apply_transformations(code: str, transformations: List[str]) -> str:
    """Apply multiple transformations to code."""
    current_code = code
    editor = PythonEditor()

    for transform in transformations:
        try:
            if transform == "add_type_hints":
                current_code = editor.add_type_hints(current_code)
            elif transform == "clean_unused_imports":
                current_code = editor.clean_unused_imports(current_code)
            elif transform == "remove_dead_code":
                current_code = editor.remove_dead_code(current_code)
            elif transform == "optimize_code":
                current_code = editor.optimize_code(current_code)
            else:
                logger.warning(f"Unknown transformation: {transform}")

        except Exception as e:
            logger.error(f"Transformation {transform} failed: {e}")
            # Continue with other transformations

    return current_code
