"""Flo Python SDK - Datasets, integrations, and workflow utilities for Flo workflows."""

from flo.quickbooks import QuickBooksClient
from flo.jobber import JobberClient
from flo.plaid import PlaidClient
from flo.buildium import BuildiumClient
from flo.rent_manager import RentManagerClient
from flo.hostaway import HostawayClient
from flo.merge import (
    MergeFileStorageClient,
    MergeFile,
    MergeFolder,
    MergeDrive,
)
from flo.review import (
    FloReviewClient,
    request_human_review,
    get_review_client,
    ReviewField,
    ReviewFieldOption,
    ReviewResponse,
    HumanReviewPending,
)
from flo.exceptions import (
    FloIntegrationError,
    AuthenticationError,
    APIError,
    QuickBooksError,
    JobberError,
    PlaidError,
    BuildiumError,
    RentManagerError,
    HostawayError,
    MergeError,
    DataSourceNotFoundError,
)
from flo.datasets import (
    FloDatasetClient,
    DatasetClient,
    DatasetRow,
    DatasetNotFoundError,
    DatasetError,
)

__all__ = [
    "QuickBooksClient",
    "JobberClient",
    "PlaidClient",
    "BuildiumClient",
    "RentManagerClient",
    "HostawayClient",
    # Merge File Storage
    "MergeFileStorageClient",
    "MergeFile",
    "MergeFolder",
    "MergeDrive",
    # Human Review
    "FloReviewClient",
    "request_human_review",
    "get_review_client",
    "ReviewField",
    "ReviewFieldOption",
    "ReviewResponse",
    "HumanReviewPending",
    # Datasets
    "FloDatasetClient",
    "DatasetClient",
    "DatasetRow",
    "DatasetNotFoundError",
    "DatasetError",
    # Exceptions
    "FloIntegrationError",
    "AuthenticationError",
    "APIError",
    "QuickBooksError",
    "JobberError",
    "PlaidError",
    "BuildiumError",
    "RentManagerError",
    "HostawayError",
    "MergeError",
    "DataSourceNotFoundError",
]

__version__ = "0.9.4"

