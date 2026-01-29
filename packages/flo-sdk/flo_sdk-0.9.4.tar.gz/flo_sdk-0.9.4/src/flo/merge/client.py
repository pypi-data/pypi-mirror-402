"""Merge file storage client for accessing files from Google Drive, SharePoint, etc."""

import os
from typing import Optional, List
import builtins

from merge.client import Merge
from tenacity import retry, stop_after_attempt, wait_exponential

from flo.exceptions import (
    AuthenticationError,
    APIError,
    DataSourceNotFoundError,
    MergeError,
)
from flo.merge.models import MergeFile, MergeFolder, MergeDrive


class MergeFileStorageClient:
    """
    Client for accessing files from Merge-connected storage providers
    (Google Drive, SharePoint, OneDrive, Box, Dropbox).

    Credentials are automatically loaded from the global __data_sources__ dictionary
    that is injected by the Flo backend into every workflow execution.

    Usage:
        # Automatically uses injected credentials
        client = MergeFileStorageClient()

        # List files
        files = client.list_files()

        # Search for a specific file
        files = client.search_files("Monthly_Report.pdf")

        # Download a file
        local_path = client.download_file(file_id, "/mnt/inputs/report.pdf")
    """

    def __init__(
        self,
        account_token: Optional[str] = None,
        api_key: Optional[str] = None,
        platform: Optional[str] = None,
        data_source_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize Merge File Storage client.

        If no parameters are provided, credentials are automatically loaded from
        the global __data_sources__ dictionary injected by the backend.

        Args:
            account_token: Merge account token (optional, auto-loaded if not provided)
            api_key: Merge API key (optional, defaults to env var MERGE_API_KEY)
            platform: Platform name e.g. "google_drive", "sharepoint" (optional, auto-detected)
            data_source_id: Data source ID (optional, auto-loaded if not provided)
            tenant_id: Tenant ID (optional, auto-loaded if not provided)
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("MERGE_API_KEY")
        if not self.api_key:
            raise AuthenticationError("MERGE_API_KEY must be set in environment")

        # Get credentials from parameters or global __data_sources__
        if account_token:
            self.account_token = account_token
            self.platform = platform
            self.data_source_id = data_source_id
            self.tenant_id = tenant_id
        else:
            self._load_from_data_sources()

        # Initialize Merge client
        self.client = Merge(
            api_key=self.api_key,
            account_token=self.account_token,
        )

    def _load_from_data_sources(self) -> None:
        """Load credentials from injected __data_sources__ global."""
        data_sources = getattr(builtins, "__data_sources__", {})

        if not data_sources:
            data_sources = globals().get("__data_sources__", {})

        # Find a Merge file storage data source
        merge_source = None
        for key, source in data_sources.items():
            integration_source = source.get("integration_source", "").lower()
            if integration_source == "merge":
                merge_source = source
                self.platform = key  # Platform is the dict key (e.g., "google_drive")
                break

        if not merge_source:
            raise DataSourceNotFoundError(
                "Merge file storage data source not found in __data_sources__. "
                "Make sure your team has connected a file storage provider (Google Drive, SharePoint, etc.)."
            )

        keys = merge_source.get("keys", {})
        self.account_token = keys.get("account_token")
        self.data_source_id = merge_source.get("id")
        self.tenant_id = merge_source.get("tenant_id")

        if not self.account_token:
            raise AuthenticationError("No account_token found in Merge data source")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass

    def _convert_response_to_dict(self, item) -> dict:
        """Convert Merge SDK response object to dictionary."""
        if isinstance(item, dict):
            return item
        elif hasattr(item, "__dict__"):
            return item.__dict__
        elif hasattr(item, "to_dict"):
            return item.to_dict()
        else:
            # Try to access common attributes
            result = {}
            for attr in ["id", "name", "mime_type", "size", "folder", "parent_folder", "created_at", "modified_at", "file_url", "drive_url"]:
                if hasattr(item, attr):
                    result[attr] = getattr(item, attr)
            return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def list_drives(self, cursor: Optional[str] = None) -> List[MergeDrive]:
        """
        List drives (Google Drive shared drives, SharePoint sites, etc.).

        Args:
            cursor: Pagination cursor for fetching next page

        Returns:
            List of MergeDrive objects
        """
        try:
            params = {}
            if cursor:
                params["cursor"] = cursor

            response = self.client.filestorage.drives.list(**params)

            drives = []
            for item in response.results or []:
                item_dict = self._convert_response_to_dict(item)
                drives.append(MergeDrive.from_merge(item_dict))

            return drives
        except Exception as e:
            raise MergeError(f"Failed to list drives: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def list_folders(
        self,
        drive_id: Optional[str] = None,
        parent_folder_id: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> List[MergeFolder]:
        """
        List folders in a drive or parent folder.

        Args:
            drive_id: Filter by drive ID
            parent_folder_id: Filter by parent folder ID (None for root folders)
            cursor: Pagination cursor

        Returns:
            List of MergeFolder objects
        """
        try:
            params = {}
            if drive_id:
                params["drive_id"] = drive_id
            if parent_folder_id is not None:
                params["parent_folder_id"] = parent_folder_id
            if cursor:
                params["cursor"] = cursor

            response = self.client.filestorage.folders.list(**params)

            folders = []
            for item in response.results or []:
                item_dict = self._convert_response_to_dict(item)
                folders.append(MergeFolder.from_merge(item_dict))

            return folders
        except Exception as e:
            raise MergeError(f"Failed to list folders: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def list_files(
        self,
        drive_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        cursor: Optional[str] = None,
    ) -> List[MergeFile]:
        """
        List files in a drive or folder.

        Args:
            drive_id: Filter by drive ID
            folder_id: Filter by folder ID (None for root files)
            cursor: Pagination cursor

        Returns:
            List of MergeFile objects
        """
        try:
            params = {}
            if drive_id:
                params["drive_id"] = drive_id
            if folder_id is not None:
                params["folder_id"] = folder_id
            if cursor:
                params["cursor"] = cursor

            response = self.client.filestorage.files.list(**params)

            files = []
            for item in response.results or []:
                item_dict = self._convert_response_to_dict(item)
                # Skip folders (identified by mime type)
                mime_type = item_dict.get("mime_type", "")
                if "folder" in mime_type.lower():
                    continue
                files.append(MergeFile.from_merge(item_dict))

            return files
        except Exception as e:
            raise MergeError(f"Failed to list files: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def search_files(self, name: str) -> List[MergeFile]:
        """
        Search for files by exact name.

        Args:
            name: Exact file name to search for

        Returns:
            List of matching MergeFile objects
        """
        try:
            response = self.client.filestorage.files.list(name=name)

            files = []
            for item in response.results or []:
                item_dict = self._convert_response_to_dict(item)
                mime_type = item_dict.get("mime_type", "")
                if "folder" not in mime_type.lower():
                    files.append(MergeFile.from_merge(item_dict))

            return files
        except Exception as e:
            raise MergeError(f"Failed to search files: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get_file(self, file_id: str) -> MergeFile:
        """
        Get file metadata.

        Args:
            file_id: Merge file ID

        Returns:
            MergeFile object
        """
        try:
            response = self.client.filestorage.files.retrieve(file_id)
            item_dict = self._convert_response_to_dict(response)
            return MergeFile.from_merge(item_dict)
        except Exception as e:
            raise MergeError(f"Failed to get file: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def download_file(self, file_id: str, local_path: str) -> str:
        """
        Download a file to local filesystem.

        Args:
            file_id: Merge file ID
            local_path: Local path to save the file (e.g., "/mnt/inputs/report.pdf")

        Returns:
            Local path where file was saved
        """
        try:
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Download file content
            response = self.client.filestorage.files.download(file_id)

            # Write to local file
            with open(local_path, "wb") as f:
                if hasattr(response, "read"):
                    # Stream response
                    f.write(response.read())
                elif isinstance(response, bytes):
                    f.write(response)
                else:
                    # Try to iterate
                    for chunk in response:
                        f.write(chunk)

            return local_path
        except Exception as e:
            raise MergeError(f"Failed to download file: {str(e)}") from e

    def download_file_to_inputs(self, file_id: str, filename: Optional[str] = None) -> str:
        """
        Download a file to the standard inputs directory (/mnt/inputs/).

        Args:
            file_id: Merge file ID
            filename: Optional filename to use (defaults to original file name)

        Returns:
            Local path where file was saved
        """
        if not filename:
            file_info = self.get_file(file_id)
            filename = file_info.name

        local_path = f"/mnt/inputs/{filename}"
        return self.download_file(file_id, local_path)
