"""Code generation and scaffolding tools."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class CodeGenerator:
    """Code generation and scaffolding engine."""

    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"

    def _load_template(self, template_name: str) -> Optional[str]:
        """Load template file."""
        try:
            template_path = self.template_dir / template_name
            if template_path.exists():
                return template_path.read_text(encoding="utf-8")
            return None
        except Exception as e:
            logger.error(f"Template load error: {e}")
            return None

    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    def generate_code(
        self,
        template_name: str,
        output_path: Path,
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate code from template.

        Args:
            template_name: Name of template file
            output_path: Output file path
            variables: Template variables

        Returns:
            Dict with generation results
        """
        try:
            template = self._load_template(template_name)
            if not template:
                return {"success": False, "error": f"Template not found: {template_name}"}

            content = self._render_template(template, variables)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            output_path.write_text(content, encoding="utf-8")

            return {
                "success": True,
                "output_path": str(output_path),
                "template": template_name,
            }

        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return {"success": False, "error": str(e)}

    def scaffold_project(
        self,
        project_type: str,
        path: Path,
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Scaffold project structure.

        Args:
            project_type: Type of project (python/ts/go/rust)
            path: Project root path
            options: Project options (name, description, etc.)

        Returns:
            Dict with scaffolding results
        """
        try:
            path.mkdir(parents=True, exist_ok=True)

            created_files = []

            if project_type == "python":
                # Create Python project structure
                (path / "README.md").write_text(f"# {options.get('name', 'Project')}\n\n{options.get('description', '')}\n")
                created_files.append("README.md")

                (path / "requirements.txt").write_text("")
                created_files.append("requirements.txt")

                main_file = path / options.get("main_file", "main.py")
                main_file.write_text('"""Main module."""\n\n\ndef main():\n    """Main function."""\n    pass\n\n\nif __name__ == "__main__":\n    main()\n')
                created_files.append(main_file.name)

                if options.get("create_tests", True):
                    test_dir = path / "tests"
                    test_dir.mkdir(exist_ok=True)
                    (test_dir / "__init__.py").write_text("")
                    (test_dir / "test_main.py").write_text('"""Tests for main module."""\n\n\ndef test_main():\n    """Test main function."""\n    pass\n')
                    created_files.append("tests/test_main.py")

            elif project_type == "typescript":
                # Create TypeScript project structure
                package_json = {
                    "name": options.get("name", "project"),
                    "version": "1.0.0",
                    "description": options.get("description", ""),
                    "main": "index.js",
                    "scripts": {
                        "build": "tsc",
                        "start": "node dist/index.js",
                    },
                }
                import json
                (path / "package.json").write_text(json.dumps(package_json, indent=2))
                created_files.append("package.json")

                (path / "tsconfig.json").write_text('{\n  "compilerOptions": {\n    "target": "ES2020",\n    "module": "commonjs",\n    "outDir": "./dist",\n    "rootDir": "./src"\n  }\n}\n')
                created_files.append("tsconfig.json")

                src_dir = path / "src"
                src_dir.mkdir(exist_ok=True)
                (src_dir / "index.ts").write_text('// Main entry point\n\nconsole.log("Hello, World!");\n')
                created_files.append("src/index.ts")

            elif project_type == "go":
                # Create Go project structure
                module_name = options.get("module_name", "project")
                (path / "go.mod").write_text(f"module {module_name}\n\ngo 1.21\n")
                created_files.append("go.mod")

                main_file = path / options.get("main_file", "main.go")
                main_file.write_text(f"package main\n\nimport \"fmt\"\n\nfunc main() {{\n    fmt.Println(\"Hello, World!\")\n}}\n")
                created_files.append(main_file.name)

            elif project_type == "rust":
                # Create Rust project structure
                cargo_toml = f"""[package]
name = "{options.get('name', 'project')}"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
                (path / "Cargo.toml").write_text(cargo_toml)
                created_files.append("Cargo.toml")

                src_dir = path / "src"
                src_dir.mkdir(exist_ok=True)
                (src_dir / "main.rs").write_text('fn main() {\n    println!("Hello, World!");\n}\n')
                created_files.append("src/main.rs")

            else:
                return {"success": False, "error": f"Unknown project type: {project_type}"}

            return {
                "success": True,
                "project_path": str(path),
                "project_type": project_type,
                "files_created": created_files,
            }

        except Exception as e:
            logger.error(f"Project scaffolding error: {e}")
            return {"success": False, "error": str(e)}

    def generate_test(
        self,
        file_path: Path,
        test_framework: str = "auto",
    ) -> Dict[str, Any]:
        """
        Generate test file for source file.

        Args:
            file_path: Source file path
            test_framework: Test framework (auto/pytest/jest)

        Returns:
            Dict with generation results
        """
        try:
            ext = file_path.suffix.lower()
            file_name = file_path.stem

            if ext == ".py":
                # Python test
                test_dir = file_path.parent / "tests"
                test_dir.mkdir(exist_ok=True)

                test_file = test_dir / f"test_{file_name}.py"
                test_content = f'''"""Tests for {file_name} module."""

import pytest

from {file_path.parent.name}.{file_name} import *


def test_example():
    """Example test."""
    assert True
'''
                test_file.write_text(test_content, encoding="utf-8")

                return {
                    "success": True,
                    "test_file": str(test_file),
                    "framework": "pytest",
                }

            elif ext in [".ts", ".tsx", ".js", ".jsx"]:
                # TypeScript/JavaScript test
                test_file = file_path.parent / f"{file_name}.test{ext}"
                test_content = f'''// Tests for {file_name}

describe("{file_name}", () => {{
    it("should work", () => {{
        expect(true).toBe(true);
    }});
}});
'''
                test_file.write_text(test_content, encoding="utf-8")

                return {
                    "success": True,
                    "test_file": str(test_file),
                    "framework": "jest",
                }

            else:
                return {"success": False, "error": f"Test generation not supported for {ext}"}

        except Exception as e:
            logger.error(f"Test generation error: {e}")
            return {"success": False, "error": str(e)}

    def generate_boilerplate(
        self,
        language: str,
        type: str,
        name: str,
        output_path: Path,
    ) -> Dict[str, Any]:
        """
        Generate boilerplate code.

        Args:
            language: Programming language
            type: Type of boilerplate (class/function/component)
            name: Name for generated code
            output_path: Output file path

        Returns:
            Dict with generation results
        """
        try:
            content = ""

            if language == "python":
                if type == "class":
                    content = f'''class {name}:
    """{name} class."""

    def __init__(self):
        """Initialize {name}."""
        pass
'''
                elif type == "function":
                    content = f'''def {name}():
    """{name} function."""
    pass
'''

            elif language == "typescript":
                if type == "class":
                    class_name = name
                    content = (
                        f"export class {class_name} {{\n"
                        "    constructor() {\n    }\n}\n"
                    )
                elif type == "component":
                    component_name = name
                    content = (
                        'import React from "react";\n\n'
                        f"export const {component_name}: React.FC = () => {{\n"
                        "    return (\n        <div>\n"
                        f"            <h1>{component_name}</h1>\n"
                        "        </div>\n    );\n};\n"
                    )

            elif language == "go":
                if type == "struct":
                    struct_name = name
                    content = (
                        "package main\n\n"
                        f"type {struct_name} struct {{\n}}\n\n"
                        f"func New{struct_name}() *{struct_name} {{\n"
                        f"    return &{struct_name}{{}}\n}}\n"
                    )

            elif language == "rust":
                if type == "struct":
                    struct_name = name
                    content = (
                        f"pub struct {struct_name} {{\n}}\n\n"
                        f"impl {struct_name} {{\n"
                        f"    pub fn new() -> Self {{\n"
                        f"        Self {{}}\n    }}\n}}\n"
                    )

            if not content:
                return {"success": False, "error": f"Unknown language/type combination: {language}/{type}"}

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")

            return {
                "success": True,
                "output_path": str(output_path),
                "language": language,
                "type": type,
            }

        except Exception as e:
            logger.error(f"Boilerplate generation error: {e}")
            return {"success": False, "error": str(e)}

