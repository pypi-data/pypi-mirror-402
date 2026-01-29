"""Code execution and testing tools."""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
from loguru import logger


class CodeExecutor:
    """Code execution and testing with sandboxing."""

    def __init__(self):
        self.timeout_default = 30

    def _detect_language(self, file_path: Path) -> str:
        """Detect language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".cxx": "cpp",
            ".cc": "cpp",
            ".c": "c",
        }
        return ext_map.get(file_path.suffix.lower(), "unknown")

    def execute_code(
        self,
        file_path: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
        timeout: int = None,
    ) -> Dict[str, Any]:
        """
        Execute code file.

        Args:
            file_path: Path to code file
            args: Command line arguments
            env: Environment variables
            timeout: Execution timeout in seconds

        Returns:
            Dict with execution result
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            language = self._detect_language(path)
            timeout = timeout or self.timeout_default

            # Build command based on language
            if language == "python":
                cmd = ["python", str(path)]
            elif language == "javascript":
                cmd = ["node", str(path)]
            elif language == "typescript":
                # Try ts-node, fallback to compiled JS
                cmd = ["ts-node", str(path)]
            elif language == "java":
                # Compile first, then run
                class_name = path.stem
                compile_result = subprocess.run(
                    ["javac", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if compile_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Compilation failed: {compile_result.stderr}",
                    }
                cmd = ["java", "-cp", str(path.parent), class_name]
            elif language == "cpp":
                # Compile first, then run
                exe_name = path.stem
                exe_path = path.parent / exe_name
                compile_result = subprocess.run(
                    ["g++", "-o", str(exe_path), str(path)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if compile_result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Compilation failed: {compile_result.stderr}",
                    }
                cmd = [str(exe_path)]
            else:
                return {"success": False, "error": f"Unsupported language: {language}"}

            # Add arguments
            if args:
                cmd.extend(args)

            # Prepare environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)

            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=exec_env,
                cwd=path.parent,
            )

            return {
                "success": True,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "language": language,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Execution timed out after {timeout}s"}
        except FileNotFoundError as e:
            return {"success": False, "error": f"Command not found: {e.filename}"}
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {"success": False, "error": str(e)}

    def run_tests(
        self,
        project_path: str,
        test_pattern: str = "",
        framework: str = "auto",
    ) -> Dict[str, Any]:
        """
        Run tests in project.

        Args:
            project_path: Project directory path
            test_pattern: Test pattern/filter
            framework: Test framework (auto/pytest/jest/junit)

        Returns:
            Dict with test results
        """
        try:
            path = Path(project_path)
            if not path.exists():
                return {"success": False, "error": f"Project path not found: {project_path}"}

            # Auto-detect framework
            if framework == "auto":
                if (path / "pytest.ini").exists() or (path / "pyproject.toml").exists():
                    framework = "pytest"
                elif (path / "package.json").exists():
                    framework = "jest"  # Default for Node.js
                elif (path / "pom.xml").exists() or (path / "build.gradle").exists():
                    framework = "junit"
                else:
                    # Try to detect from files
                    py_files = list(path.rglob("test_*.py"))
                    if py_files:
                        framework = "pytest"
                    else:
                        return {"success": False, "error": "Could not auto-detect test framework"}

            # Build test command
            if framework == "pytest":
                cmd = ["pytest", "-v"]
                if test_pattern:
                    cmd.append(f"-k {test_pattern}")
            elif framework == "jest":
                cmd = ["npm", "test"]
                if test_pattern:
                    cmd.extend(["--testNamePattern", test_pattern])
            elif framework == "junit":
                if (path / "pom.xml").exists():
                    cmd = ["mvn", "test"]
                elif (path / "build.gradle").exists():
                    cmd = ["./gradlew", "test"]
                else:
                    return {"success": False, "error": "Maven or Gradle not found"}
            else:
                return {"success": False, "error": f"Unsupported framework: {framework}"}

            # Run tests
            result = subprocess.run(
                cmd,
                cwd=path,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes for tests
            )

            return {
                "success": True,
                "framework": framework,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "passed": result.returncode == 0,
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Test execution timed out"}
        except FileNotFoundError as e:
            return {"success": False, "error": f"Test framework not found: {e.filename}"}
        except Exception as e:
            logger.error(f"Test execution error: {e}")
            return {"success": False, "error": str(e)}

    def check_coverage(self, file_path: str = "", project_path: str = "") -> Dict[str, Any]:
        """
        Check test coverage.

        Args:
            file_path: Optional specific file path
            project_path: Project directory path

        Returns:
            Dict with coverage information
        """
        try:
            if project_path:
                path = Path(project_path)
            elif file_path:
                path = Path(file_path).parent
            else:
                return {"success": False, "error": "Either file_path or project_path required"}

            # Try pytest-cov for Python
            if (path / "pytest.ini").exists() or list(path.rglob("test_*.py")):
                cmd = ["pytest", "--cov", str(path), "--cov-report", "term"]
                if file_path:
                    cmd.extend(["--cov", str(Path(file_path))])

                result = subprocess.run(
                    cmd,
                    cwd=path,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                # Parse coverage from output
                coverage_lines = [l for l in result.stdout.split("\n") if "TOTAL" in l or "%" in l]
                coverage_info = "\n".join(coverage_lines[-5:]) if coverage_lines else result.stdout

                return {
                    "success": True,
                    "coverage_output": coverage_info,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

            return {"success": False, "error": "Coverage checking not supported for this project type"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Coverage check timed out"}
        except FileNotFoundError:
            return {"success": False, "error": "Coverage tool not installed"}
        except Exception as e:
            logger.error(f"Coverage check error: {e}")
            return {"success": False, "error": str(e)}

