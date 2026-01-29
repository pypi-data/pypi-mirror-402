"""Git operations client for version control integration."""

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

try:
    import git
    from git import Repo
    GITPYTHON_AVAILABLE = True
except ImportError:
    GITPYTHON_AVAILABLE = False
    logger.warning("GitPython not installed. Git operations will use subprocess.")


class GitClient:
    """Git operations client with safe error handling."""

    def __init__(self):
        self.use_gitpython = GITPYTHON_AVAILABLE

    def _get_repo(self, project_path: Path) -> Optional[Any]:
        """Get git repository object."""
        if not self.use_gitpython:
            return None
        
        try:
            repo_path = project_path if project_path.is_dir() else project_path.parent
            return Repo(repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            return None
        except Exception as e:
            logger.error(f"Error getting git repo: {e}")
            return None

    def status(self, project_path: str) -> Dict[str, Any]:
        """
        Get git status for project.

        Args:
            project_path: Path to project directory or file

        Returns:
            Dict with status information
        """
        try:
            path = Path(project_path)
            
            if self.use_gitpython:
                repo = self._get_repo(path)
                if repo:
                    return {
                        "success": True,
                        "is_repo": True,
                        "branch": repo.active_branch.name if not repo.head.is_detached else "detached",
                        "dirty": repo.is_dirty(),
                        "untracked_files": [f for f in repo.untracked_files],
                        "modified_files": [item.a_path for item in repo.index.diff(None)],
                        "staged_files": [item.a_path for item in repo.index.diff("HEAD")],
                    }

            # Fallback to subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path if path.is_dir() else path.parent,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return {"success": False, "error": "Not a git repository"}

            lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
            modified = [l[3:] for l in lines if l.startswith(" M")]
            untracked = [l[3:] for l in lines if l.startswith("??")]
            staged = [l[3:] for l in lines if l.startswith("M ")]

            # Get branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=path if path.is_dir() else path.parent,
                capture_output=True,
                text=True,
                timeout=5,
            )
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

            return {
                "success": True,
                "is_repo": True,
                "branch": branch,
                "dirty": len(lines) > 0,
                "untracked_files": untracked,
                "modified_files": modified,
                "staged_files": staged,
            }

        except FileNotFoundError:
            return {"success": False, "error": "Git not installed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git operation timed out"}
        except Exception as e:
            logger.error(f"Git status error: {e}")
            return {"success": False, "error": str(e)}

    def diff(self, file_path: Optional[str] = None, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get git diff for file or project.

        Args:
            file_path: Optional specific file path
            project_path: Project directory path

        Returns:
            Dict with diff information
        """
        try:
            if file_path:
                path = Path(file_path)
                work_dir = path.parent
                target = str(path)
            elif project_path:
                work_dir = Path(project_path)
                target = "."
            else:
                return {"success": False, "error": "Either file_path or project_path required"}

            if self.use_gitpython:
                repo = self._get_repo(Path(work_dir))
                if repo:
                    if file_path:
                        diff = repo.git.diff(target)
                    else:
                        diff = repo.git.diff()
                    
                    return {
                        "success": True,
                        "diff": diff,
                        "file": str(target) if file_path else "project",
                    }

            # Fallback to subprocess
            cmd = ["git", "diff", target] if file_path else ["git", "diff"]
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return {"success": False, "error": result.stderr or "Git diff failed"}

            return {
                "success": True,
                "diff": result.stdout,
                "file": str(target) if file_path else "project",
            }

        except FileNotFoundError:
            return {"success": False, "error": "Git not installed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git operation timed out"}
        except Exception as e:
            logger.error(f"Git diff error: {e}")
            return {"success": False, "error": str(e)}

    def commit(self, message: str, files: Optional[List[str]] = None, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Create git commit.

        Args:
            message: Commit message
            files: Optional list of files to commit (all if None)
            project_path: Project directory path

        Returns:
            Dict with commit result
        """
        try:
            if not project_path:
                return {"success": False, "error": "project_path required"}

            work_dir = Path(project_path)

            if self.use_gitpython:
                repo = self._get_repo(work_dir)
                if repo:
                    if files:
                        repo.index.add(files)
                    else:
                        repo.index.add(repo.untracked_files + [item.a_path for item in repo.index.diff(None)])
                    
                    commit = repo.index.commit(message)
                    return {
                        "success": True,
                        "commit_hash": commit.hexsha,
                        "message": message,
                        "files": files or "all",
                    }

            # Fallback to subprocess
            if files:
                subprocess.run(
                    ["git", "add"] + files,
                    cwd=work_dir,
                    check=True,
                    timeout=30,
                )
            else:
                subprocess.run(
                    ["git", "add", "."],
                    cwd=work_dir,
                    check=True,
                    timeout=30,
                )

            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return {"success": False, "error": result.stderr or "Commit failed"}

            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            commit_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else "unknown"

            return {
                "success": True,
                "commit_hash": commit_hash,
                "message": message,
                "files": files or "all",
            }

        except FileNotFoundError:
            return {"success": False, "error": "Git not installed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git operation timed out"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"Git command failed: {e.stderr}"}
        except Exception as e:
            logger.error(f"Git commit error: {e}")
            return {"success": False, "error": str(e)}

    def log(self, limit: int = 10, file_path: Optional[str] = None, project_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get git log.

        Args:
            limit: Number of commits to return
            file_path: Optional specific file path
            project_path: Project directory path

        Returns:
            Dict with log entries
        """
        try:
            if file_path:
                work_dir = Path(file_path).parent
                target = str(Path(file_path).name)
            elif project_path:
                work_dir = Path(project_path)
                target = None
            else:
                return {"success": False, "error": "Either file_path or project_path required"}

            if self.use_gitpython:
                repo = self._get_repo(work_dir)
                if repo:
                    commits = list(repo.iter_commits(max_count=limit, paths=target if target else None))
                    entries = []
                    for commit in commits:
                        entries.append({
                            "hash": commit.hexsha[:8],
                            "message": commit.message.split("\n")[0],
                            "author": commit.author.name,
                            "date": commit.committed_datetime.isoformat(),
                        })
                    
                    return {
                        "success": True,
                        "commits": entries,
                        "count": len(entries),
                    }

            # Fallback to subprocess
            cmd = ["git", "log", f"-{limit}", "--pretty=format:%h|%s|%an|%ai"]
            if target:
                cmd.append("--")
                cmd.append(target)

            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return {"success": False, "error": result.stderr or "Git log failed"}

            entries = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 3)
                if len(parts) >= 4:
                    entries.append({
                        "hash": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "date": parts[3],
                    })

            return {
                "success": True,
                "commits": entries,
                "count": len(entries),
            }

        except FileNotFoundError:
            return {"success": False, "error": "Git not installed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git operation timed out"}
        except Exception as e:
            logger.error(f"Git log error: {e}")
            return {"success": False, "error": str(e)}

    def branches(self, project_path: str) -> Dict[str, Any]:
        """
        List git branches.

        Args:
            project_path: Project directory path

        Returns:
            Dict with branch list
        """
        try:
            work_dir = Path(project_path)

            if self.use_gitpython:
                repo = self._get_repo(work_dir)
                if repo:
                    branches = [ref.name.split("/")[-1] for ref in repo.refs]
                    current = repo.active_branch.name if not repo.head.is_detached else "detached"
                    
                    return {
                        "success": True,
                        "branches": branches,
                        "current": current,
                    }

            # Fallback to subprocess
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return {"success": False, "error": result.stderr or "Git branch failed"}

            branches = []
            current = None
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                branch = line.strip().lstrip("*").strip().split("/")[-1]
                branches.append(branch)
                if line.strip().startswith("*"):
                    current = branch

            return {
                "success": True,
                "branches": branches,
                "current": current or "unknown",
            }

        except FileNotFoundError:
            return {"success": False, "error": "Git not installed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Git operation timed out"}
        except Exception as e:
            logger.error(f"Git branches error: {e}")
            return {"success": False, "error": str(e)}

