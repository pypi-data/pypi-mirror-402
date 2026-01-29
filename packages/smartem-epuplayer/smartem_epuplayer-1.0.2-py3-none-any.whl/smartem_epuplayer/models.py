from dataclasses import dataclass
from typing import Any


@dataclass
class EPUEvent:
    timestamp: float
    event_type: str  # created, modified, deleted, moved, appended, truncated, patched
    src_path: str
    dest_path: str | None = None
    is_directory: bool = False
    content: str | None = None  # For small text files
    size: int | None = None
    # New fields for diff-based recording
    content_hash: str | None = None  # SHA256 hash for integrity
    binary_chunk_id: str | None = None  # Reference to binary chunk in tar
    operation_data: dict[str, Any] | None = None  # append_data, patch_info, etc.
    file_position: int | None = None  # For append/patch operations
    is_placeholder: bool = False  # True if this is a placeholder file
