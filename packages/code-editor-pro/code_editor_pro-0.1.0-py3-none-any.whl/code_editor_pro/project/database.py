"""Simplified SQLite database for projects."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict

from loguru import logger

from ..models import FileInfo, ProjectInfo, WorkspaceStats


class Database:
    """Lightweight SQLite database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._init_tables()

    def close(self):
        """Close database connection."""
        self.conn.close()

    def _init_tables(self):
        """Initialize database tables."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                project_path TEXT NOT NULL,
                project_type TEXT NOT NULL,
                total_files INTEGER DEFAULT 0,
                total_lines INTEGER DEFAULT 0,
                total_size_mb REAL DEFAULT 0,
                created_at TIMESTAMP,
                last_analyzed TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                file_path TEXT PRIMARY KEY,
                project_id TEXT,
                file_name TEXT NOT NULL,
                file_extension TEXT,
                file_size INTEGER,
                language TEXT,
                line_count INTEGER,
                char_count INTEGER,
                created_at TIMESTAMP,
                last_modified TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (project_id)
            )
        """
        )

        self.conn.commit()

    def save_project(self, project: ProjectInfo):
        """Save project to database."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO projects
            (project_id, project_name, project_path, project_type,
             total_files, total_lines, total_size_mb, created_at, last_analyzed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                project.project_id,
                project.project_name,
                str(project.project_path),
                project.project_type,
                project.total_files,
                project.total_lines,
                project.total_size_mb,
                project.created_at,
                project.last_analyzed,
            ),
        )
        self.conn.commit()

    def save_file(self, file_info: FileInfo, project_id: str):
        """Save file to database."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO files
            (file_path, project_id, file_name, file_extension, file_size,
             language, line_count, char_count, created_at, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(file_info.file_path),
                project_id,
                file_info.file_name,
                file_info.file_extension,
                file_info.file_size,
                file_info.language,
                file_info.line_count,
                file_info.char_count,
                file_info.created_at,
                file_info.last_modified,
            ),
        )
        self.conn.commit()

    def get_project_stats(self, project_id: str) -> WorkspaceStats:
        """Get project statistics."""
        cursor = self.conn.cursor()

        # Get project info
        cursor.execute(
            "SELECT project_path FROM projects WHERE project_id = ?", (project_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Project not found: {project_id}")

        # Get file stats
        cursor.execute(
            """
            SELECT language, COUNT(*), SUM(line_count), SUM(file_size)
            FROM files WHERE project_id = ?
            GROUP BY language
        """,
            (project_id,),
        )

        language_dist: Dict[str, int] = {}
        total_files = 0
        total_lines = 0
        total_size = 0.0

        for lang, count, lines, size in cursor.fetchall():
            if lang:
                language_dist[lang] = count
            if count:
                total_files += count
            if lines:
                total_lines += lines
            if size:
                total_size += size

        return WorkspaceStats(
            workspace_path=Path(row[0]),
            total_files=total_files,
            total_lines=total_lines,
            total_size_mb=total_size / (1024 * 1024),
            language_distribution=language_dist,
            last_analyzed=datetime.now(),
        )
