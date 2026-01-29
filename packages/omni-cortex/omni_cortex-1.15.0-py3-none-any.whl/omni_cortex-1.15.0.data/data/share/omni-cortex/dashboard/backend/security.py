"""Security utilities for Omni-Cortex Dashboard."""

import os
import re
from pathlib import Path
from typing import Optional


class PathValidator:
    """Validate and sanitize file paths to prevent traversal attacks."""

    # Pattern for valid omni-cortex database paths
    VALID_DB_PATTERN = re.compile(r'^.*[/\\]\.omni-cortex[/\\]cortex\.db$')
    GLOBAL_DB_PATTERN = re.compile(r'^.*[/\\]\.omni-cortex[/\\]global\.db$')

    @staticmethod
    def is_valid_project_db(path: str) -> bool:
        """Check if path is a valid omni-cortex project database."""
        try:
            resolved = Path(path).resolve()
            path_str = str(resolved)

            # Must match expected patterns
            if PathValidator.VALID_DB_PATTERN.match(path_str):
                return resolved.exists() and resolved.is_file()
            if PathValidator.GLOBAL_DB_PATTERN.match(path_str):
                return resolved.exists() and resolved.is_file()

            return False
        except (ValueError, OSError):
            return False

    @staticmethod
    def validate_project_path(path: str) -> Path:
        """Validate and return resolved path, or raise ValueError."""
        if not PathValidator.is_valid_project_db(path):
            raise ValueError(f"Invalid project database path: {path}")
        return Path(path).resolve()

    @staticmethod
    def is_safe_static_path(base_dir: Path, requested_path: str) -> Optional[Path]:
        """Validate static file path is within base directory.

        Returns resolved path if safe, None if traversal detected.
        """
        try:
            # Resolve both paths to absolute
            base_resolved = base_dir.resolve()
            requested = (base_dir / requested_path).resolve()

            # Check if requested path is under base directory
            if base_resolved in requested.parents or requested == base_resolved:
                if requested.exists() and requested.is_file():
                    return requested

            return None
        except (ValueError, OSError):
            return None


def sanitize_log_input(value: str, max_length: int = 200) -> str:
    """Sanitize user input for safe logging.

    Prevents log injection by:
    - Escaping newlines
    - Limiting length
    - Removing control characters
    """
    if not isinstance(value, str):
        value = str(value)

    # Remove control characters except spaces
    sanitized = ''.join(c if c.isprintable() or c == ' ' else '?' for c in value)

    # Escape potential log injection patterns
    sanitized = sanitized.replace('\n', '\\n').replace('\r', '\\r')

    # Truncate
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + '...'

    return sanitized


# Environment-based configuration
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"


def get_cors_config():
    """Get CORS configuration based on environment."""
    if IS_PRODUCTION:
        origins = os.getenv("CORS_ORIGINS", "").split(",")
        origins = [o.strip() for o in origins if o.strip()]
        return {
            "allow_origins": origins,
            "allow_methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
        }
    else:
        return {
            "allow_origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
