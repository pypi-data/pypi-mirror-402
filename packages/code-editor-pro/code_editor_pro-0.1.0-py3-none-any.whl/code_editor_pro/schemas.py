"""Database Schema Definitions for Code Editor MCP."""

from typing import Dict, List


class DatabaseSchemas:
    """SQLite schema definitions for code editor data management."""

    # Projects table schema
    PROJECTS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            project_name TEXT NOT NULL,
            project_path TEXT NOT NULL,
            project_type TEXT NOT NULL,
            total_files INTEGER DEFAULT 0,
            total_lines INTEGER DEFAULT 0,
            total_size_mb REAL DEFAULT 0,
            git_repo TEXT,
            dependencies TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """

    # Files table schema
    FILES_SCHEMA = """
        CREATE TABLE IF NOT EXISTS files (
            file_path TEXT PRIMARY KEY,
            project_id TEXT,
            file_name TEXT NOT NULL,
            file_extension TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            language TEXT NOT NULL,
            encoding TEXT DEFAULT 'utf-8',
            line_count INTEGER DEFAULT 0,
            char_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_analyzed TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (project_id)
        )
    """

    # Code analysis table schema
    CODE_ANALYSIS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS code_analysis (
            file_path TEXT PRIMARY KEY,
            functions TEXT,
            classes TEXT,
            imports TEXT,
            variables TEXT,
            complexity INTEGER DEFAULT 0,
            line_count INTEGER DEFAULT 0,
            char_count INTEGER DEFAULT 0,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_path) REFERENCES files (file_path)
        )
    """

    # Transform results table schema
    TRANSFORM_RESULTS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS transform_results (
            transform_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            transform_type TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            changes_made INTEGER DEFAULT 0,
            lines_added INTEGER DEFAULT 0,
            lines_removed INTEGER DEFAULT 0,
            lines_modified INTEGER DEFAULT 0,
            error_message TEXT,
            warnings TEXT,
            before_snippet TEXT,
            after_snippet TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duration_ms REAL DEFAULT 0,
            FOREIGN KEY (file_path) REFERENCES files (file_path)
        )
    """

    # Code smells table schema
    CODE_SMELLS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS code_smells (
            smell_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            line_number INTEGER NOT NULL,
            column_number INTEGER NOT NULL,
            smell_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            suggestion TEXT NOT NULL,
            function_name TEXT,
            class_name TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_path) REFERENCES files (file_path)
        )
    """

    # Code quality table schema
    CODE_QUALITY_SCHEMA = """
        CREATE TABLE IF NOT EXISTS code_quality (
            file_path TEXT PRIMARY KEY,
            overall_score REAL NOT NULL,
            maintainability REAL NOT NULL,
            reliability REAL NOT NULL,
            security REAL NOT NULL,
            performance REAL NOT NULL,
            readability REAL NOT NULL,
            testability REAL NOT NULL,
            recommendations TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_path) REFERENCES files (file_path)
        )
    """

    # Refactor operations table schema
    REFACTOR_OPERATIONS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS refactor_operations (
            operation_id TEXT PRIMARY KEY,
            operation_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            element_name TEXT NOT NULL,
            element_type TEXT NOT NULL,
            new_name TEXT,
            parameters TEXT,
            success BOOLEAN NOT NULL,
            changes_made INTEGER DEFAULT 0,
            error_message TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_path) REFERENCES files (file_path)
        )
    """

    # Workspace statistics table schema
    WORKSPACE_STATS_SCHEMA = """
        CREATE TABLE IF NOT EXISTS workspace_stats (
            workspace_id TEXT PRIMARY KEY,
            workspace_path TEXT NOT NULL,
            total_files INTEGER DEFAULT 0,
            total_lines INTEGER DEFAULT 0,
            total_size_mb REAL DEFAULT 0,
            file_types TEXT,
            language_distribution TEXT,
            complexity_distribution TEXT,
            quality_distribution TEXT,
            last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """

    # Code generation requests table schema
    CODE_GENERATION_SCHEMA = """
        CREATE TABLE IF NOT EXISTS code_generation (
            request_id TEXT PRIMARY KEY,
            template_type TEXT NOT NULL,
            parameters TEXT NOT NULL,
            target_file TEXT,
            language TEXT NOT NULL,
            style TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """

    # Indexes for better performance
    INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_files_project_id ON files (project_id)",
        "CREATE INDEX IF NOT EXISTS idx_files_language ON files (language)",
        "CREATE INDEX IF NOT EXISTS idx_transform_results_file ON transform_results (file_path)",
        "CREATE INDEX IF NOT EXISTS idx_transform_results_type ON transform_results (transform_type)",
        "CREATE INDEX IF NOT EXISTS idx_code_smells_file ON code_smells (file_path)",
        "CREATE INDEX IF NOT EXISTS idx_code_smells_severity ON code_smells (severity)",
        "CREATE INDEX IF NOT EXISTS idx_refactor_operations_file ON refactor_operations (file_path)",
        "CREATE INDEX IF NOT EXISTS idx_refactor_operations_type ON refactor_operations (operation_type)",
    ]

    # All schemas combined
    ALL_SCHEMAS = [
        PROJECTS_SCHEMA,
        FILES_SCHEMA,
        CODE_ANALYSIS_SCHEMA,
        TRANSFORM_RESULTS_SCHEMA,
        CODE_SMELLS_SCHEMA,
        CODE_QUALITY_SCHEMA,
        REFACTOR_OPERATIONS_SCHEMA,
        WORKSPACE_STATS_SCHEMA,
        CODE_GENERATION_SCHEMA,
    ] + INDEXES


class QueryPatterns:
    """Common query patterns for code editor operations."""

    # Project queries
    GET_PROJECT_BY_ID = "SELECT * FROM projects WHERE project_id = ?"
    GET_ALL_PROJECTS = "SELECT * FROM projects ORDER BY created_at DESC"
    GET_PROJECT_FILES = "SELECT * FROM files WHERE project_id = ? ORDER BY file_name"

    # File queries
    GET_FILE_BY_PATH = "SELECT * FROM files WHERE file_path = ?"
    GET_FILES_BY_LANGUAGE = "SELECT * FROM files WHERE language = ? ORDER BY file_name"
    GET_FILES_BY_EXTENSION = (
        "SELECT * FROM files WHERE file_extension = ? ORDER BY file_name"
    )

    # Analysis queries
    GET_ANALYSIS_BY_FILE = "SELECT * FROM code_analysis WHERE file_path = ?"
    GET_ANALYSIS_BY_PROJECT = """
        SELECT ca.* FROM code_analysis ca
        JOIN files f ON ca.file_path = f.file_path
        WHERE f.project_id = ?
    """

    # Transform queries
    GET_TRANSFORMS_BY_FILE = (
        "SELECT * FROM transform_results WHERE file_path = ? ORDER BY executed_at DESC"
    )
    GET_TRANSFORMS_BY_TYPE = "SELECT * FROM transform_results WHERE transform_type = ? ORDER BY executed_at DESC"
    GET_RECENT_TRANSFORMS = (
        "SELECT * FROM transform_results ORDER BY executed_at DESC LIMIT ?"
    )

    # Code smell queries
    GET_SMELLS_BY_FILE = (
        "SELECT * FROM code_smells WHERE file_path = ? ORDER BY line_number"
    )
    GET_SMELLS_BY_SEVERITY = (
        "SELECT * FROM code_smells WHERE severity = ? ORDER BY detected_at DESC"
    )
    GET_SMELLS_BY_TYPE = (
        "SELECT * FROM code_smells WHERE smell_type = ? ORDER BY detected_at DESC"
    )

    # Quality queries
    GET_QUALITY_BY_FILE = "SELECT * FROM code_quality WHERE file_path = ?"
    GET_QUALITY_BY_PROJECT = """
        SELECT cq.* FROM code_quality cq
        JOIN files f ON cq.file_path = f.file_path
        WHERE f.project_id = ?
    """

    # Statistics queries
    GET_PROJECT_STATS = """
        SELECT 
            COUNT(*) as total_files,
            SUM(line_count) as total_lines,
            SUM(file_size) as total_size,
            language,
            COUNT(*) as files_per_language
        FROM files 
        WHERE project_id = ?
        GROUP BY language
    """

    GET_WORKSPACE_STATS = """
        SELECT 
            COUNT(*) as total_files,
            SUM(line_count) as total_lines,
            SUM(file_size) as total_size,
            language,
            COUNT(*) as files_per_language
        FROM files 
        GROUP BY language
    """

    # Search queries
    SEARCH_FILES_BY_NAME = (
        "SELECT * FROM files WHERE file_name LIKE ? ORDER BY file_name"
    )
    SEARCH_FUNCTIONS_BY_NAME = """
        SELECT file_path, functions FROM code_analysis 
        WHERE functions LIKE ? 
        ORDER BY file_path
    """
    SEARCH_CLASSES_BY_NAME = """
        SELECT file_path, classes FROM code_analysis 
        WHERE classes LIKE ? 
        ORDER BY file_path
    """

    # Performance queries
    GET_MOST_COMPLEX_FILES = """
        SELECT file_path, complexity, line_count 
        FROM code_analysis 
        ORDER BY complexity DESC 
        LIMIT ?
    """

    GET_LARGEST_FILES = """
        SELECT file_path, line_count, char_count 
        FROM code_analysis 
        ORDER BY line_count DESC 
        LIMIT ?
    """

    GET_MOST_TRANSFORMED_FILES = """
        SELECT file_path, COUNT(*) as transform_count
        FROM transform_results 
        GROUP BY file_path 
        ORDER BY transform_count DESC 
        LIMIT ?
    """

    # Cleanup queries
    CLEANUP_OLD_TRANSFORMS = """
        DELETE FROM transform_results 
        WHERE executed_at < datetime('now', '-30 days')
    """

    CLEANUP_OLD_ANALYSIS = """
        DELETE FROM code_analysis 
        WHERE analyzed_at < datetime('now', '-7 days')
    """

    # Maintenance queries
    VACUUM_DATABASE = "VACUUM"
    ANALYZE_DATABASE = "ANALYZE"
    REINDEX_DATABASE = "REINDEX"
