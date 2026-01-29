"""Helper utilities for FARM."""

import hashlib
import uuid
from pathlib import Path


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def hash_content(content: str | bytes) -> str:
    """Generate SHA-256 hash of content."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, create if needed."""
    path.mkdir(parents=True, exist_ok=True)
    return path
