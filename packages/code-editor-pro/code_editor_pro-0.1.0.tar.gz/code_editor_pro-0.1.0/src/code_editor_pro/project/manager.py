"""Project management (refactored from data_manager.py)."""

from datetime import datetime
from pathlib import Path
from typing import Union

from loguru import logger

from ..models import FileInfo, ProjectInfo, WorkspaceStats
from .database import Database


class ProjectManager:
    """Simplified project manager."""

    def __init__(self, workspace_dir: str = "./code_workspace"):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.db = Database(self.workspace / "projects.db")

    def create_project(
        self, name: str, path: Union[str, Path], language: str = "python"
    ) -> ProjectInfo:
        """Create new project."""
        project_id = f"proj_{int(datetime.now().timestamp())}"
        project_path = Path(path)
        project_path.mkdir(parents=True, exist_ok=True)

        project = ProjectInfo(
            project_id=project_id,
            project_name=name,
            project_path=project_path,
            project_type=language,
            total_files=0,
            total_lines=0,
            total_size_mb=0.0,
            created_at=datetime.now(),
            last_analyzed=datetime.now(),
        )

        self.db.save_project(project)
        logger.info(f"Created project: {name} ({project_id})")
        return project

    def add_file(self, file_path: Union[str, Path], project_id: str) -> FileInfo:
        """Add file to project."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = file_path.stat()
        content = file_path.read_text(encoding="utf-8")

        file_info = FileInfo(
            file_path=file_path,
            file_name=file_path.name,
            file_extension=file_path.suffix,
            file_size=stat.st_size,
            language=self._detect_language(file_path.suffix),
            line_count=len(content.splitlines()),
            char_count=len(content),
            created_at=datetime.fromtimestamp(stat.st_ctime),
            last_modified=datetime.fromtimestamp(stat.st_mtime),
        )

        self.db.save_file(file_info, project_id)
        logger.info(f"Added file: {file_info.file_name} to project {project_id}")
        return file_info

    def get_project_stats(self, project_id: str) -> WorkspaceStats:
        """Get project statistics."""
        return self.db.get_project_stats(project_id)

    def _detect_language(self, extension: str) -> str:
        """Detect language from extension."""
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
        }
        return lang_map.get(extension.lower(), "unknown")
