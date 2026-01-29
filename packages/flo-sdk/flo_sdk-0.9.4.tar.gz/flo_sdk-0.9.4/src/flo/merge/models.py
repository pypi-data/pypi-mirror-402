"""Data models for Merge file storage."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MergeFile:
    """Represents a file from Merge-connected storage."""

    id: str
    name: str
    mime_type: Optional[str] = None
    size: Optional[int] = None
    folder_id: Optional[str] = None
    folder_name: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    download_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary (camelCase for backend compatibility)."""
        return {
            "id": self.id,
            "name": self.name,
            "mimeType": self.mime_type,
            "size": self.size,
            "folderId": self.folder_id,
            "folderName": self.folder_name,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "modifiedAt": self.modified_at.isoformat() if self.modified_at else None,
            "downloadUrl": self.download_url,
        }

    @classmethod
    def from_merge(cls, data: dict) -> "MergeFile":
        """Create from Merge API response."""
        # Handle folder field - can be string ID or object
        folder_id = None
        if data.get("folder"):
            folder = data["folder"]
            if isinstance(folder, str):
                folder_id = folder
            elif isinstance(folder, dict) and "id" in folder:
                folder_id = folder["id"]

        # Parse dates
        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )
            elif isinstance(data["created_at"], datetime):
                created_at = data["created_at"]

        modified_at = None
        if data.get("modified_at"):
            if isinstance(data["modified_at"], str):
                modified_at = datetime.fromisoformat(
                    data["modified_at"].replace("Z", "+00:00")
                )
            elif isinstance(data["modified_at"], datetime):
                modified_at = data["modified_at"]

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Untitled"),
            mime_type=data.get("mime_type"),
            size=data.get("size"),
            folder_id=folder_id,
            created_at=created_at,
            modified_at=modified_at,
            download_url=data.get("file_url"),
        )


@dataclass
class MergeFolder:
    """Represents a folder from Merge-connected storage."""

    id: str
    name: str
    parent_folder_id: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary (camelCase for backend compatibility)."""
        return {
            "id": self.id,
            "name": self.name,
            "parentFolderId": self.parent_folder_id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "modifiedAt": self.modified_at.isoformat() if self.modified_at else None,
        }

    @classmethod
    def from_merge(cls, data: dict) -> "MergeFolder":
        """Create from Merge API response."""
        # Handle parent_folder field - can be string ID or object
        parent_id = None
        if data.get("parent_folder"):
            parent = data["parent_folder"]
            if isinstance(parent, str):
                parent_id = parent
            elif isinstance(parent, dict) and "id" in parent:
                parent_id = parent["id"]

        # Parse dates
        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )
            elif isinstance(data["created_at"], datetime):
                created_at = data["created_at"]

        modified_at = None
        if data.get("modified_at"):
            if isinstance(data["modified_at"], str):
                modified_at = datetime.fromisoformat(
                    data["modified_at"].replace("Z", "+00:00")
                )
            elif isinstance(data["modified_at"], datetime):
                modified_at = data["modified_at"]

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Untitled"),
            parent_folder_id=parent_id,
            created_at=created_at,
            modified_at=modified_at,
        )


@dataclass
class MergeDrive:
    """Represents a drive from Merge-connected storage (Google Drive, SharePoint site, etc.)."""

    id: str
    name: str
    drive_url: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary (camelCase for backend compatibility)."""
        return {
            "id": self.id,
            "name": self.name,
            "driveUrl": self.drive_url,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "modifiedAt": self.modified_at.isoformat() if self.modified_at else None,
        }

    @classmethod
    def from_merge(cls, data: dict) -> "MergeDrive":
        """Create from Merge API response."""
        # Parse dates
        created_at = None
        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(
                    data["created_at"].replace("Z", "+00:00")
                )
            elif isinstance(data["created_at"], datetime):
                created_at = data["created_at"]

        modified_at = None
        if data.get("modified_at"):
            if isinstance(data["modified_at"], str):
                modified_at = datetime.fromisoformat(
                    data["modified_at"].replace("Z", "+00:00")
                )
            elif isinstance(data["modified_at"], datetime):
                modified_at = data["modified_at"]

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Untitled"),
            drive_url=data.get("drive_url"),
            created_at=created_at,
            modified_at=modified_at,
        )
