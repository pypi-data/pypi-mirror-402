"""Models for dataset operations."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class DatasetRow:
    """Represents a dataset row."""
    row_id: str
    data: Dict[str, Any]
    version: int

