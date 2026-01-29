# Flo Integration Modules

Python integration modules for Flo workflows running in Modal containers. These modules provide easy access to QuickBooks, Plaid, Jobber, Buildium, Rent Manager, and Hostaway integrations from within your Python workflows, with credentials automatically injected by the backend.

## Overview

The Clyr backend automatically injects data source credentials into every workflow execution through a global `__data_sources__` dictionary. Workflow developers can use these modules without worrying about credential management.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Available Modules](#available-modules)
- [QuickBooks](#quickbooks-floquickbooks)
- [Plaid](#plaid-floplaid)
- [Jobber](#jobber-flojobber)
- [Buildium](#buildium-flobuildium)
- [Rent Manager](#rent-manager-florent_manager)
- [Hostaway](#hostaway-flohostaway)
- [Data Types](#data-types)
- [How Credentials Work](#how-credentials-work)
- [Error Handling](#error-handling)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [Architecture](#architecture)

## Installation

### For Local Development

```bash
cd python-modules/flo-sdk
pip install -e .
```

### In Modal Workflows

The module is pre-installed in the Modal base image. Simply import and use:

```python
from flo.quickbooks import QuickBooksClient
```

## Quick Start

```python
from flo.quickbooks import QuickBooksClient

# Automatically uses injected credentials (no parameters needed!)
qb = QuickBooksClient()

# Get vendors
vendors = qb.get_vendors()
print(f"Found {len(vendors)} vendors")

# Create a vendor
new_vendor = qb.create_vendor(
    name="New Supplier LLC",
    email="billing@newsupplier.com",
    phone="555-1234"
)
print(f"Created vendor: {new_vendor.name} ({new_vendor.foreign_id})")

# Access vendor data
for vendor in vendors:
    print(f"- {vendor.name}: {vendor.email}")
    # Convert to dict for JSON serialization
    vendor_dict = vendor.to_dict()
```

## Available Modules

### QuickBooks (`flo.quickbooks`)

Access QuickBooks data via Rutter API:

#### `QuickBooksClient()`

Initialize the client. Credentials are automatically loaded from injected data sources.

**Methods:**

- **`get_vendors(limit=500)`**: Get all vendors from QuickBooks
  - Returns: `List[Vendor]`
  - Automatically handles pagination
  
- **`create_vendor(name, email=None, phone=None, status='active', currency='USD', contact_name=None)`**: Create a new vendor
  - Returns: `Vendor`
  - Handles both sync and async Rutter responses

- **`get_customers(limit=500)`**: Get all customers from QuickBooks
  - Returns: `List[Customer]`
  - Automatically handles pagination

- **`get_accounts(limit=500)`**: Get all chart of accounts entries
  - Returns: `List[Account]`
  - Automatically handles pagination

- **`get_invoices(limit=500)`**: Get all invoices from QuickBooks
  - Returns: `List[Invoice]`
  - Automatically handles pagination

- **`get_classes(limit=500)`**: Get all classes from QuickBooks
  - Returns: `List[Dict[str, Any]]`

- **`get_items(limit=500)`**: Get all items from QuickBooks
  - Returns: `List[Dict[str, Any]]`

- **`get_tax_rates(limit=500)`**: Get all tax rates from QuickBooks
  - Returns: `List[Dict[str, Any]]`

### Plaid (`flo.plaid`)

Access bank account and transaction data via Plaid API:

#### `PlaidClient()`

Initialize the client. Credentials are automatically loaded from injected data sources.

**Methods:**

- **`get_accounts()`**: Get all bank accounts
  - Returns: `List[Account]`

- **`get_transactions(start_date, end_date, account_ids=None)`**: Get transactions for a date range
  - Returns: `List[Transaction]`
  - Args:
    - `start_date`: `datetime` or `date` object
    - `end_date`: `datetime` or `date` object
    - `account_ids`: Optional list of account IDs to filter by

- **`get_balance(account_ids=None)`**: Get account balances
  - Returns: `Dict[str, Any]` with balance information
  - Args: `account_ids` - Optional list of account IDs

- **`get_institution(institution_id)`**: Get institution details
  - Returns: `Institution`
  - Args: `institution_id` - Plaid institution ID

- **`get_item()`**: Get Plaid item information
  - Returns: `Dict[str, Any]` with item details

### Jobber (`flo.jobber`)

Access Jobber field service management data via GraphQL API:

#### `JobberClient()`

Initialize the client. Credentials are automatically loaded from injected data sources.

**Methods:**

- **`get_users()`**: Get all users from Jobber
  - Returns: `List[JobberUser]`
  - Automatically handles pagination

- **`get_clients(extra_ids=None)`**: Get all clients from Jobber
  - Returns: `List[JobberClient]`
  - Args: `extra_ids` - Optional list of additional client IDs to fetch
  - Automatically handles pagination

- **`get_jobs()`**: Get all jobs from Jobber
  - Returns: `List[JobberJob]`
  - Automatically handles pagination

- **`get_expenses()`**: Get all expenses from Jobber
  - Returns: `List[JobberExpense]`
  - Automatically handles pagination

- **`get_expense(expense_id)`**: Get a specific expense by ID
  - Returns: `Optional[JobberExpense]`
  - Args: `expense_id` - Jobber expense ID

### Buildium (`flo.buildium`)

Access Buildium property management data:

#### `BuildiumClient()`

Initialize the client. Credentials are automatically loaded from injected data sources.

**Methods:**

- **`get_users()`**: Get all users from Buildium
  - Returns: `List[BuildiumUser]`
  - Automatically handles pagination

- **`get_vendors()`**: Get all vendors from Buildium
  - Returns: `List[BuildiumVendor]`
  - Automatically handles pagination

- **`get_gl_accounts()`**: Get all GL accounts from Buildium
  - Returns: `List[BuildiumGlAccount]`
  - Automatically handles pagination

- **`get_bills(paid_status=None)`**: Get bills from Buildium
  - Returns: `List[BuildiumBill]`
  - Args: `paid_status` - Optional filter (e.g., "Unpaid", "Paid")
  - Automatically handles pagination

- **`get_rentals()`**: Get all rental properties from Buildium
  - Returns: `List[BuildiumRental]`

- **`get_rental_owners()`**: Get all rental owners from Buildium
  - Returns: `List[BuildiumRentalOwner]`

- **`get_rental_units()`**: Get all rental units from Buildium
  - Returns: `List[BuildiumRentalUnit]`

- **`get_associations()`**: Get all associations from Buildium
  - Returns: `List[BuildiumAssociation]`

- **`get_association_owners()`**: Get all association owners from Buildium
  - Returns: `List[BuildiumAssociationOwner]`

- **`get_association_units()`**: Get all association units from Buildium
  - Returns: `List[BuildiumAssociationUnit]`

- **`get_work_orders()`**: Get all work orders from Buildium
  - Returns: `List[BuildiumWorkOrder]`

### Rent Manager (`flo.rent_manager`)

Access Rent Manager property management data:

#### `RentManagerClient()`

Initialize the client. Credentials are automatically loaded from injected data sources.

**Methods:**

- **`get_users()`**: Get all users from Rent Manager
  - Returns: `List[RentManagerUser]`
  - Automatically handles pagination

- **`get_owners()`**: Get all owners from Rent Manager
  - Returns: `List[RentManagerOwner]`
  - Automatically handles pagination

- **`get_properties()`**: Get all properties from Rent Manager
  - Returns: `List[RentManagerProperty]`
  - Automatically handles pagination

- **`get_units()`**: Get all units from Rent Manager
  - Returns: `List[RentManagerUnit]`
  - Automatically handles pagination

- **`get_jobs()`**: Get all jobs from Rent Manager
  - Returns: `List[RentManagerJob]`
  - Automatically handles pagination

- **`get_credit_cards()`**: Get all credit cards from Rent Manager
  - Returns: `List[RentManagerCreditCard]`
  - Automatically handles pagination

- **`get_issues()`**: Get all issues from Rent Manager
  - Returns: `List[RentManagerIssue]`
  - Automatically handles pagination (PageSize=500)

- **`get_gl_accounts()`**: Get all GL accounts from Rent Manager
  - Returns: `List[RentManagerGlAccount]`
  - Automatically handles pagination

- **`get_vendors()`**: Get all vendors from Rent Manager
  - Returns: `List[RentManagerVendor]`
  - Automatically handles pagination (PageSize=100)

### Hostaway (`flo.hostaway`)

Access Hostaway vacation rental management data:

#### `HostawayClient()`

Initialize the client. Credentials are automatically loaded from injected data sources.

**Methods:**

- **`get_listings()`**: Get all listings from Hostaway
  - Returns: `List[HostawayListing]`
  - Automatically handles pagination

- **`get_owners()`**: Get all owners from Hostaway
  - Returns: `List[HostawayOwner]`
  - Automatically handles pagination

- **`get_users()`**: Get all users from Hostaway
  - Returns: `List[HostawayUser]`
  - Automatically handles pagination

- **`get_units()`**: Get all units from Hostaway
  - Returns: `List[HostawayUnit]`
  - Automatically handles pagination

### Merge File Storage (`flo.merge`)

Access files from Merge-connected cloud storage providers (Google Drive, SharePoint, OneDrive, Box, Dropbox):

#### `MergeFileStorageClient()`

Initialize the client. Credentials are automatically loaded from injected data sources.

**Methods:**

- **`list_drives(cursor=None)`**: List available drives (Google Shared Drives, SharePoint sites, etc.)
  - Returns: `List[MergeDrive]`
  - Args: `cursor` - Optional pagination cursor

- **`list_folders(drive_id=None, parent_folder_id=None, cursor=None)`**: List folders in a drive or parent folder
  - Returns: `List[MergeFolder]`
  - Args:
    - `drive_id` - Optional drive ID to filter by
    - `parent_folder_id` - Optional parent folder ID (None for root folders)
    - `cursor` - Optional pagination cursor

- **`list_files(drive_id=None, folder_id=None, cursor=None)`**: List files in a drive or folder
  - Returns: `List[MergeFile]`
  - Args:
    - `drive_id` - Optional drive ID to filter by
    - `folder_id` - Optional folder ID (None for root files)
    - `cursor` - Optional pagination cursor

- **`search_files(name)`**: Search for files by exact name
  - Returns: `List[MergeFile]`
  - Args: `name` - Exact file name to search for

- **`get_file(file_id)`**: Get file metadata
  - Returns: `MergeFile`
  - Args: `file_id` - Merge file ID

- **`download_file(file_id, local_path)`**: Download a file to local filesystem
  - Returns: `str` - Local path where file was saved
  - Args:
    - `file_id` - Merge file ID
    - `local_path` - Local path to save the file (e.g., "/mnt/inputs/report.pdf")

- **`download_file_to_inputs(file_id, filename=None)`**: Download a file to the standard inputs directory (`/mnt/inputs/`)
  - Returns: `str` - Local path where file was saved
  - Args:
    - `file_id` - Merge file ID
    - `filename` - Optional filename to use (defaults to original file name)

**Example:**

```python
from flo.merge import MergeFileStorageClient

# Initialize client (auto-loads credentials from __data_sources__)
merge = MergeFileStorageClient()

# Search for a file by name
files = merge.search_files("Monthly_Report.pdf")
if files:
    # Download to workflow inputs directory
    local_path = merge.download_file_to_inputs(files[0].id)
    
    # Process the downloaded file
    with open(local_path, "rb") as f:
        content = f.read()
        # ... process content ...

# Or browse storage structure
drives = merge.list_drives()
for drive in drives:
    print(f"Drive: {drive.name}")
    folders = merge.list_folders(drive_id=drive.id)
    files = merge.list_files(drive_id=drive.id)
    for file in files:
        print(f"  File: {file.name} ({file.size} bytes)")
```

## Data Types

All data types are available in their respective modules (e.g., `flo.quickbooks.models`, `flo.plaid.models`). Each model includes a `.to_dict()` method that returns camelCase dictionaries matching the backend's DTO format.

### QuickBooks Models

- `Vendor` - Vendor information
- `Customer` - Customer information
- `Account` - Chart of accounts entry
- `Invoice` - Invoice data
- `Expense` - Expense data

### Plaid Models

- `Account` - Bank account information
- `Transaction` - Transaction data
- `Institution` - Financial institution details

### Jobber Models

- `JobberUser` - User information
- `JobberClient` - Client information
- `JobberJob` - Job/work order data
- `JobberExpense` - Expense data

### Buildium Models

- `BuildiumUser`, `BuildiumVendor`, `BuildiumGlAccount`, `BuildiumBill`
- `BuildiumRental`, `BuildiumRentalOwner`, `BuildiumRentalUnit`
- `BuildiumAssociation`, `BuildiumAssociationOwner`, `BuildiumAssociationUnit`
- `BuildiumWorkOrder`

### Rent Manager Models

- `RentManagerUser`, `RentManagerOwner`, `RentManagerProperty`, `RentManagerUnit`
- `RentManagerJob`, `RentManagerCreditCard`, `RentManagerIssue`
- `RentManagerGlAccount`, `RentManagerVendor`

### Hostaway Models

- `HostawayListing` - Property listing information
- `HostawayOwner` - Owner information
- `HostawayUser` - User information
- `HostawayUnit` - Unit information

### Merge File Storage Models

- `MergeFile` - File metadata (id, name, mime_type, size, folder_id, download_url)
- `MergeFolder` - Folder metadata (id, name, parent_folder_id)
- `MergeDrive` - Drive/site metadata (id, name, drive_url)

## How Credentials Work

The Clyr backend automatically injects a `__data_sources__` global variable into every workflow execution:

```python
__data_sources__ = {
    "rutter": {
        "id": "ds_xxx",
        "platform": "quickbooks",
        "access_token": "rutter_token_xxx",
        "team_id": "team_yyy"
    },
    "plaid": {
        "id": "ds_zzz",
        "platform": "plaid",
        "access_token": "plaid_token_xxx",
        "item_id": "item_xxx",
        "team_id": "team_yyy"
    },
    "jobber": {
        "id": "ds_aaa",
        "platform": "jobber",
        "access_token": "jobber_token_xxx",
        "team_id": "team_yyy"
    },
    "google_drive": {
        "id": "ds_bbb",
        "platform": "google_drive",
        "integration_source": "merge",
        "tenant_id": "tenant_xxx",
        "keys": {
            "account_token": "merge_account_token_xxx",
            "integration": "google-drive",
            "linked_account_id": "la_xxx"
        }
    }
}
```

All clients automatically read from this dictionary, so you never need to handle credentials manually.

## Error Handling

```python
from flo.exceptions import (
    FloIntegrationError,
    QuickBooksError,
    PlaidError,
    JobberError,
    BuildiumError,
    RentManagerError,
    HostawayError,
    MergeError,
    AuthenticationError,
    APIError,
    DataSourceNotFoundError,
)

try:
    qb = QuickBooksClient()
    vendors = qb.get_vendors()
except DataSourceNotFoundError as e:
    print(f"Data source not found: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except QuickBooksError as e:
    print(f"QuickBooks error: {e}")
except MergeError as e:
    print(f"Merge file storage error: {e}")
except APIError as e:
    print(f"API error: {e}")
```

## Context Manager

Use with context manager for automatic cleanup:

```python
with QuickBooksClient() as qb:
    vendors = qb.get_vendors()
    # Session automatically closed
```

## Manual Initialization (Testing)

For testing purposes, you can manually provide credentials:

```python
qb = QuickBooksClient(
    access_token="your_token",
    team_id="team_id",
    data_source_id="ds_id"
)
```

## Local Development

### Setup

1. **Set up Jupyter kernel** (automatically done when deploying Modal image):

```bash
# From backend package directory
cd packages/backend
bun run deploy:modal
```

Or manually:
```bash
python3 packages/backend/scripts/setup-jupyter-kernel.py
```

This creates a virtual environment and Jupyter kernel matching the Modal container environment exactly.

2. **Configure backend API URL** (optional):

Create a `.env.local` file in `python-modules/flo-sdk/` if you need a custom backend URL:

```bash
API_BASE_URL=http://localhost:3000
```

If not set, defaults to `http://localhost:3000`.

**Prerequisites:**
- Backend server must be running
- Backend must have access to the database and configured with all required environment variables (PLAID_CLIENT_ID, PLAID_SECRET, RUTTER_CLIENT_ID, etc.)
- You need a valid `team_id` to fetch data sources

**Note:** Environment variables (like `PLAID_CLIENT_ID`, `PLAID_SECRET`, etc.) are automatically fetched from the backend and injected into your local Python environment, matching the Modal container behavior exactly. No need to configure them locally!

### Jupyter Notebook Development

1. Start Jupyter from the `python-modules/flo-sdk` directory:

```bash
cd python-modules/flo-sdk
jupyter notebook
```

2. When creating a new notebook, select the **"Python (Flo Workflows)"** kernel

3. In your notebook:

```python
# At the start of your notebook
from dev_utils.jupyter_helper import load_team_data_sources

# Load data sources for your team
load_team_data_sources("team_123...")

# Now use the clients normally - credentials are automatically injected
from flo.plaid import PlaidClient
plaid = PlaidClient()
accounts = plaid.get_accounts()

from flo.jobber import JobberClient
jobber = JobberClient()
clients = jobber.get_clients()
```

**Note**: The Jupyter kernel uses the same Python packages and versions as Modal containers, ensuring your local development matches production exactly.

### CLI Script Development

For running standalone Python scripts:

```bash
python dev_utils/cli_loader.py --team-id team_123... --script my_workflow.py
```

Or interactively:

```bash
python dev_utils/cli_loader.py --team-id team_123...
```

### Programmatic Usage

```python
from dev_utils.data_source_loader import inject_data_sources

# Load and inject data sources
inject_data_sources("team_123...")

# Your workflow code here
from flo.plaid import PlaidClient
plaid = PlaidClient()
```

### Example Workflows

See the `examples/` directory for complete workflow examples:

- `quickbooks/quickbooks_vendor_workflow.py` - List and create vendors
- `quickbooks/quickbooks_invoice_report.py` - Generate invoice summary report
- `plaid/plaid_transactions_workflow.py` - Fetch and analyze transactions
- `jobber/get_jobber_expenses.py` - Get Jobber expenses
- `buildium/get_buildium_vendors.py` - Get Buildium vendors
- `rent_manager/get_rent_manager_properties.py` - Get Rent Manager properties
- `hostaway/get_hostaway_listings.py` - Get Hostaway listings
- `merge/search_and_download_files.py` - Search and download files from Merge storage

## Datasets

The SDK provides access to Flo datasets for reading and writing structured data from workflows.

### Listing Available Datasets

You can list all datasets available to your workflow:

```python
from flo.datasets import FloDatasetClient

client = FloDatasetClient.from_env()

# List all datasets
result = client.list_datasets()
print(f"Found {result['total']} datasets")

# Search for specific datasets
invoices = client.list_datasets(search="invoice", page_size=10)
for dataset in invoices['datasets']:
    print(f"{dataset['name']}: {dataset['rowCount']} rows")

# Paginate through results
page = 1
while True:
    result = client.list_datasets(page=page, page_size=20)
    for dataset in result['datasets']:
        print(dataset['name'])
    
    if page >= result['totalPages']:
        break
    page += 1
```

The `list_datasets()` method returns a dictionary with:
- `datasets`: List of dataset objects with `id`, `name`, `description`, `rowCount`, `currentVersion`, etc.
- `total`: Total number of datasets
- `page`: Current page number
- `pageSize`: Number of datasets per page
- `totalPages`: Total number of pages

## Deployment

### Adding to Modal Image

The `flo-sdk` package is automatically included in the Modal runtime image. To deploy or update:

```bash
# From backend package directory
cd packages/backend
bun run deploy:modal
```

Or manually:
```bash
# From monorepo root
modal deploy packages/backend/scripts/build-modal-image.py
python3 packages/backend/scripts/setup-jupyter-kernel.py
```

This will:
1. Build the Modal image with all Python dependencies from `pyproject.toml`
2. Include the `flo-sdk` package from `python-modules/flo-sdk/`
3. Create/update a Jupyter kernel matching the Modal environment
4. Output an image ID (e.g., `im-xxx...`)

**Important**: 
- The Modal image uses dependencies from `python-modules/flo-sdk/pyproject.toml` (single source of truth)
- The Jupyter kernel matches the Modal environment exactly
- Note: The system now uses per-workflow-version images. Each workflow version builds its own image with the required dependencies.

## Architecture

This package mirrors the functionality of the TypeScript backend integration modules (`packages/backend/src/modules/integrations/`) to provide consistent data access patterns for Python workflows.

The `.to_dict()` methods on all data types return camelCase dictionaries that match the backend's DTO format, making it easy to pass data between Python workflows and the backend.

### Package Structure

```
python-modules/flo-sdk/
├── src/
│   └── flo/                    # Main package
│       ├── quickbooks/         # QuickBooks integration
│       ├── plaid/              # Plaid integration
│       ├── jobber/             # Jobber integration
│       ├── buildium/           # Buildium integration
│       ├── rent_manager/       # Rent Manager integration
│       ├── hostaway/           # Hostaway integration
│       ├── merge/              # Merge file storage integration
│       ├── datasets/           # Dataset client
│       ├── review/             # Human review client
│       └── exceptions.py       # Custom exceptions
├── dev_utils/                  # Development utilities
│   ├── data_source_loader.py   # Load data sources from backend
│   ├── jupyter_helper.py       # Jupyter notebook helpers
│   └── cli_loader.py           # CLI script runner
├── examples/                   # Example workflow scripts
└── pyproject.toml              # Package configuration
```

## License

MIT
