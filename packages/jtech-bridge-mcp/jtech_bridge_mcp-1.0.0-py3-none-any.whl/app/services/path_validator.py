"""
Path Validation Service

Provides security checks for file access, ensuring operations are restricted
to allowed project directories.
"""

from pathlib import Path

from app.logging_config import get_logger
from app.repositories.project_repository import get_project_repository

logger = get_logger(__name__)


class PathValidator:
    """Validator for file paths."""

    def __init__(self) -> None:
        self._project_repository = get_project_repository()

    async def validate_path(self, path_str: str) -> Path:
        """
        Validate if a path is safe to access (within a registered project).

        Args:
            path_str: The absolute path to validate.

        Returns:
            Path: The resolved Path object if valid.

        Raises:
            ValueError: If path is not absolute or invalid format.
            PermissionError: If path is not within any registered project.
            FileNotFoundError: If the file does not exist.
        """
        try:
            path = Path(path_str).resolve()
        except Exception as e:
            raise ValueError(f"Invalid path format: {e}") from e

        if not path.is_absolute():
            raise ValueError("Path must be absolute")

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Get allowed roots from projects
        projects = await self._project_repository.get_all()
        allowed_roots = [Path(p.path).resolve() for p in projects]

        is_allowed = False
        for root in allowed_roots:
            if path.is_relative_to(root):
                is_allowed = True
                break

        if not is_allowed:
            logger.warning(f"Access denied for path: {path}")
            raise PermissionError(f"Access denied: {path} is not within any registered project.")

        return path


_validator: PathValidator | None = None


def get_path_validator() -> PathValidator:
    """Get the singleton PathValidator instance."""
    global _validator
    if _validator is None:
        _validator = PathValidator()
    return _validator
