"""Pydantic Models for Code Editor MCP - Type Safety and Validation."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FileInfo(BaseModel):
    """File information model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="File path")
    file_name: str = Field(..., description="File name")
    file_extension: str = Field(..., description="File extension")
    file_size: int = Field(ge=0, description="File size in bytes")
    language: str = Field(..., description="Programming language")
    encoding: str = Field(default="utf-8", description="File encoding")
    line_count: int = Field(ge=0, description="Number of lines")
    char_count: int = Field(ge=0, description="Number of characters")
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    last_analyzed: Optional[datetime] = Field(
        None, description="Last analysis timestamp"
    )


class ProjectInfo(BaseModel):
    """Project information model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_id: str = Field(..., description="Unique project identifier")
    project_name: str = Field(..., description="Project name")
    project_path: Path = Field(..., description="Project root path")
    project_type: str = Field(
        ..., description="Project type (python, javascript, etc.)"
    )
    total_files: int = Field(ge=0, description="Total number of files")
    total_lines: int = Field(ge=0, description="Total lines of code")
    total_size_mb: float = Field(ge=0, description="Total project size in MB")
    git_repo: Optional[str] = Field(None, description="Git repository URL")
    dependencies: List[str] = Field(
        default_factory=list, description="Project dependencies"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    last_analyzed: datetime = Field(default_factory=datetime.now)


class CodeAnalysis(BaseModel):
    """Code analysis result model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="Analyzed file path")
    functions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Function information"
    )
    classes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Class information"
    )
    imports: List[Dict[str, Any]] = Field(
        default_factory=list, description="Import information"
    )
    variables: List[Dict[str, Any]] = Field(
        default_factory=list, description="Variable information"
    )
    complexity: int = Field(ge=0, description="Cyclomatic complexity")
    line_count: int = Field(ge=0, description="Number of lines")
    char_count: int = Field(ge=0, description="Number of characters")
    analyzed_at: datetime = Field(default_factory=datetime.now)


class CodeMetrics(BaseModel):
    """Code quality metrics model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="File path")
    maintainability_index: float = Field(
        ge=0, le=100, description="Maintainability index"
    )
    cyclomatic_complexity: int = Field(ge=1, description="Cyclomatic complexity")
    cognitive_complexity: int = Field(ge=0, description="Cognitive complexity")
    lines_of_code: int = Field(ge=0, description="Lines of code")
    comment_density: float = Field(
        ge=0, le=100, description="Comment density percentage"
    )
    duplication_density: float = Field(
        ge=0, le=100, description="Code duplication percentage"
    )
    technical_debt: float = Field(ge=0, description="Technical debt in minutes")
    quality_score: float = Field(ge=0, le=100, description="Overall quality score")
    analyzed_at: datetime = Field(default_factory=datetime.now)


class CodeSmell(BaseModel):
    """Code smell detection model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    smell_id: str = Field(..., description="Unique smell identifier")
    file_path: Path = Field(..., description="File path")
    line_number: int = Field(ge=1, description="Line number")
    column_number: int = Field(ge=1, description="Column number")
    smell_type: str = Field(..., description="Type of code smell")
    severity: str = Field(
        ..., description="Severity level (low, medium, high, critical)"
    )
    message: str = Field(..., description="Smell description")
    suggestion: str = Field(..., description="Improvement suggestion")
    function_name: Optional[str] = Field(None, description="Affected function name")
    class_name: Optional[str] = Field(None, description="Affected class name")
    detected_at: datetime = Field(default_factory=datetime.now)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        valid_severities = ["low", "medium", "high", "critical"]
        if v not in valid_severities:
            raise ValueError(f"Severity must be one of {valid_severities}")
        return v


class CodeQuality(BaseModel):
    """Overall code quality assessment model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: Path = Field(..., description="File path")
    overall_score: float = Field(ge=0, le=100, description="Overall quality score")
    maintainability: float = Field(ge=0, le=100, description="Maintainability score")
    reliability: float = Field(ge=0, le=100, description="Reliability score")
    security: float = Field(ge=0, le=100, description="Security score")
    performance: float = Field(ge=0, le=100, description="Performance score")
    readability: float = Field(ge=0, le=100, description="Readability score")
    testability: float = Field(ge=0, le=100, description="Testability score")
    code_smells: List[CodeSmell] = Field(
        default_factory=list, description="Detected code smells"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )
    analyzed_at: datetime = Field(default_factory=datetime.now)


class TransformResult(BaseModel):
    """Code transformation result model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    transform_id: str = Field(..., description="Unique transform identifier")
    file_path: Path = Field(..., description="Transformed file path")
    transform_type: str = Field(..., description="Type of transformation")
    success: bool = Field(..., description="Transformation success status")
    changes_made: int = Field(ge=0, description="Number of changes made")
    lines_added: int = Field(ge=0, description="Lines added")
    lines_removed: int = Field(ge=0, description="Lines removed")
    lines_modified: int = Field(ge=0, description="Lines modified")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    warnings: List[str] = Field(
        default_factory=list, description="Transformation warnings"
    )
    before_snippet: Optional[str] = Field(
        None, description="Code before transformation"
    )
    after_snippet: Optional[str] = Field(None, description="Code after transformation")
    executed_at: datetime = Field(default_factory=datetime.now)
    duration_ms: float = Field(ge=0, description="Execution duration in milliseconds")


class WorkspaceStats(BaseModel):
    """Workspace statistics model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    workspace_path: Path = Field(..., description="Workspace directory path")
    total_files: int = Field(ge=0, description="Total files count")
    total_lines: int = Field(ge=0, description="Total lines of code")
    total_size_mb: float = Field(ge=0, description="Total size in MB")
    file_types: Dict[str, int] = Field(
        default_factory=dict, description="File type distribution"
    )
    language_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Language distribution"
    )
    complexity_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Complexity distribution"
    )
    quality_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Quality score distribution"
    )
    last_analyzed: datetime = Field(default_factory=datetime.now)


class RefactorOperation(BaseModel):
    """Code refactoring operation model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    operation_id: str = Field(..., description="Operation identifier")
    operation_type: str = Field(..., description="Type of refactoring")
    file_path: Path = Field(..., description="Target file path")
    element_name: str = Field(..., description="Element to refactor")
    element_type: str = Field(
        ..., description="Element type (function, class, variable)"
    )
    new_name: Optional[str] = Field(None, description="New name for rename operations")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Operation parameters"
    )
    success: bool = Field(default=False, description="Operation success status")
    changes_made: int = Field(ge=0, description="Number of changes made")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    executed_at: datetime = Field(default_factory=datetime.now)


class CodeGenerationRequest(BaseModel):
    """Code generation request model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    request_id: str = Field(..., description="Request identifier")
    template_type: str = Field(..., description="Code template type")
    parameters: Dict[str, Any] = Field(..., description="Generation parameters")
    target_file: Optional[Path] = Field(None, description="Target file path")
    language: str = Field(default="python", description="Target language")
    style: str = Field(default="standard", description="Code style")
    created_at: datetime = Field(default_factory=datetime.now)


# Utility functions
def create_transform_id(file_path: Path, transform_type: str) -> str:
    """Create unique transform ID."""
    import hashlib
    import time

    timestamp = str(int(time.time()))
    content = f"{file_path}_{transform_type}_{timestamp}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def validate_file_path(file_path: Union[str, Path]) -> bool:
    """Validate file path."""
    try:
        path = Path(file_path)
        return path.is_absolute() or not path.is_reserved()
    except Exception:
        return False


def validate_language(language: str) -> bool:
    """Validate programming language."""
    supported_languages = [
        "python",
        "javascript",
        "typescript",
        "java",
        "cpp",
        "c",
        "csharp",
        "go",
        "rust",
        "php",
        "ruby",
        "swift",
        "kotlin",
        "scala",
        "r",
    ]
    return language.lower() in supported_languages
