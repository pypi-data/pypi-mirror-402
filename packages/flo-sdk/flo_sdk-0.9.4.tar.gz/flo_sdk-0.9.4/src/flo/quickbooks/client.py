"""QuickBooks client for accessing QuickBooks data via Rutter API."""

import os
import json
from typing import Optional, List, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from flo.exceptions import (
    AuthenticationError,
    APIError,
    QuickBooksError,
    DataSourceNotFoundError,
)
from flo.quickbooks.models import Vendor, Customer, Account, Invoice, Expense


class QuickBooksClient:
    """
    Client for accessing QuickBooks data via Rutter API.
    
    Credentials are automatically loaded from the global __data_sources__ dictionary
    that is injected by the Clyr backend into every agent execution.
    """
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        tenant_id: Optional[str] = None,
        data_source_id: Optional[str] = None,
        base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize QuickBooks client.
        
        If no parameters are provided, credentials are automatically loaded from
        the global __data_sources__ dictionary injected by the backend.
        
        Args:
            access_token: Rutter access token (optional, auto-loaded if not provided)
            tenant_id: Tenant ID (optional, auto-loaded if not provided)
            data_source_id: Data source ID (optional, auto-loaded if not provided)
            base_url: Rutter API base URL (optional, defaults to env var or sandbox)
            client_id: Rutter client ID (optional, defaults to env var)
            client_secret: Rutter client secret (optional, defaults to env var)
        """
        # Get credentials from parameters or global __data_sources__
        if access_token and tenant_id and data_source_id:
            self.access_token = access_token
            self.tenant_id = tenant_id
            self.data_source_id = data_source_id
        else:
            # Try to load from global __data_sources__ (injected by backend)
            try:
                # Check if __data_sources__ is available (injected by backend)
                # The backend injects this as a global variable in the agent execution context
                import builtins
                data_sources = getattr(builtins, "__data_sources__", {})
                
                # Fallback to globals() if not in builtins
                if not data_sources:
                    data_sources = globals().get("__data_sources__", {})
                
                # Look for QuickBooks/Rutter data source
                qb_source = None
                for key, source in data_sources.items():
                    platform = source.get("platform", "").lower()
                    parent_platform = source.get("parent_platform", "").lower()
                    if platform in ["quickbooks", "quickbooks_online", "quickbooks_desktop"] or \
                       parent_platform == "rutter":
                        qb_source = source
                        break
                
                if not qb_source:
                    raise DataSourceNotFoundError(
                        "QuickBooks data source not found in __data_sources__. "
                        "Make sure your team has connected QuickBooks."
                    )
                
                keys = qb_source.get("keys", {})
                self.access_token = keys.get("access_token")
                self.tenant_id = qb_source.get("tenant_id")
                self.data_source_id = qb_source.get("id")
                
                if not self.access_token:
                    raise AuthenticationError("No access token found in data source")
                if not self.tenant_id:
                    raise AuthenticationError("No tenant_id found in data source")
                if not self.data_source_id:
                    raise AuthenticationError("No data_source_id found in data source")
                    
            except NameError:
                raise DataSourceNotFoundError(
                    "__data_sources__ not found. This client must be used within "
                    "a Clyr agent execution context, or credentials must be provided manually."
                )
        
        # Get API configuration from environment or parameters
        self.base_url = base_url or os.getenv("RUTTER_API_URI", "https://sandbox.rutter.com")
        self.client_id = client_id or os.getenv("RUTTER_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("RUTTER_CLIENT_SECRET")
        
        if not self.client_id or not self.client_secret:
            raise AuthenticationError(
                "RUTTER_CLIENT_ID and RUTTER_CLIENT_SECRET must be set "
                "(injected by backend or provided as env vars)"
            )
        
        # Create requests session with basic auth
        self.session = requests.Session()
        self.session.auth = (self.client_id, self.client_secret)
        self.session.headers.update({
            "Content-Type": "application/json",
        })
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to the Rutter API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            headers: Optional additional headers
            
        Returns:
            Response JSON as dict
            
        Raises:
            APIError: If the request fails
            AuthenticationError: If authentication fails
        """
        url = f"{self.base_url}{endpoint}"
        
        # Add access_token to params
        if params is None:
            params = {}
        params["access_token"] = self.access_token
        
        # Prepare headers
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers if request_headers else None,
                timeout=30,
            )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError(
                    f"Authentication failed: {response.text}"
                )
            
            # Handle other errors
            if not response.ok:
                raise APIError(
                    f"API request failed: {response.text}",
                    status_code=response.status_code,
                    response=response.json() if response.content else None,
                )
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    def _paginate(
        self,
        endpoint: str,
        entity: str,
        limit: int = 500,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Paginate through Rutter API results.
        
        Args:
            endpoint: API endpoint
            entity: Entity name (e.g., "vendors", "customers")
            limit: Items per page
            params: Additional query parameters
            
        Returns:
            List of all entities from all pages
        """
        if params is None:
            params = {}
        
        params.update({
            "limit": limit,
            "expand": "platform_data",
            "force_fetch": "true",
        })
        
        all_items = []
        cursor = None
        
        while True:
            if cursor:
                params["cursor"] = cursor
            
            response = self._request("GET", endpoint, params=params)
            data = response.get("data", {})
            
            items = data.get(entity, [])
            all_items.extend(items)
            
            cursor = data.get("next_cursor")
            if not cursor:
                break
        
        return all_items
    
    # Vendor methods
    
    def get_vendors(self, limit: int = 500) -> List[Vendor]:
        """
        Get all vendors from QuickBooks.
        
        Args:
            limit: Maximum items per page (default: 500)
            
        Returns:
            List of Vendor objects
        """
        try:
            vendors_data = self._paginate(
                "/accounting/vendors",
                "vendors",
                limit=limit,
            )
            return [Vendor.from_rutter(v) for v in vendors_data]
        except Exception as e:
            raise QuickBooksError(f"Failed to get vendors: {str(e)}") from e
    
    def create_vendor(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        status: str = "active",
        currency: str = "USD",
        contact_name: Optional[str] = None,
    ) -> Vendor:
        """
        Create a new vendor in QuickBooks.
        
        Args:
            name: Vendor name (required)
            email: Vendor email
            phone: Vendor phone
            status: Vendor status (default: "active")
            currency: Default currency (default: "USD")
            contact_name: Contact name
            
        Returns:
            Created Vendor object
            
        Note:
            This may return an async job response. The client handles both
            sync and async responses automatically.
        """
        try:
            payload = {
                "vendor_name": name,
                "status": status,
                "currency_code": currency,
            }
            
            if email:
                payload["email"] = email
            if phone:
                payload["phone"] = phone
            if contact_name:
                payload["contact_name"] = contact_name
            
            response = self._request(
                "POST",
                "/accounting/vendors",
                data=payload,
            )
            
            # Handle async job response
            if response.get("data", {}).get("job_id"):
                # For async jobs, we would need to poll for completion
                # For now, raise an error indicating async response
                raise QuickBooksError(
                    "Vendor creation initiated asynchronously. "
                    "Poll the job_id to check completion status."
                )
            
            # Handle sync response
            vendor_data = response.get("data", {})
            return Vendor.from_rutter(vendor_data)
            
        except Exception as e:
            raise QuickBooksError(f"Failed to create vendor: {str(e)}") from e
    
    # Customer methods
    
    def get_customers(self, limit: int = 500) -> List[Customer]:
        """
        Get all customers from QuickBooks.
        
        Args:
            limit: Maximum items per page (default: 500)
            
        Returns:
            List of Customer objects
        """
        try:
            customers_data = self._paginate(
                "/accounting/customers",
                "customers",
                limit=limit,
            )
            return [Customer.from_rutter(c) for c in customers_data]
        except Exception as e:
            raise QuickBooksError(f"Failed to get customers: {str(e)}") from e
    
    # Account methods
    
    def get_accounts(self, limit: int = 500) -> List[Account]:
        """
        Get all chart of accounts entries from QuickBooks.
        
        Args:
            limit: Maximum items per page (default: 500)
            
        Returns:
            List of Account objects
        """
        try:
            accounts_data = self._paginate(
                "/accounting/accounts",
                "accounts",
                limit=limit,
            )
            return [Account.from_rutter(a) for a in accounts_data]
        except Exception as e:
            raise QuickBooksError(f"Failed to get accounts: {str(e)}") from e
    
    # Invoice methods
    
    def get_invoices(self, limit: int = 500) -> List[Invoice]:
        """
        Get all invoices from QuickBooks.
        
        Args:
            limit: Maximum items per page (default: 500)
            
        Returns:
            List of Invoice objects
        """
        try:
            invoices_data = self._paginate(
                "/accounting/invoices",
                "invoices",
                limit=limit,
            )
            return [Invoice.from_rutter(i) for i in invoices_data]
        except Exception as e:
            raise QuickBooksError(f"Failed to get invoices: {str(e)}") from e
    
    # Additional entity methods (classes, items, tax_rates)
    
    def get_classes(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Get all classes from QuickBooks.
        
        Args:
            limit: Maximum items per page (default: 500)
            
        Returns:
            List of class dictionaries
        """
        try:
            return self._paginate(
                "/accounting/classes",
                "classes",
                limit=limit,
            )
        except Exception as e:
            raise QuickBooksError(f"Failed to get classes: {str(e)}") from e
    
    def get_items(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Get all items from QuickBooks.
        
        Args:
            limit: Maximum items per page (default: 500)
            
        Returns:
            List of item dictionaries
        """
        try:
            return self._paginate(
                "/accounting/items",
                "items",
                limit=limit,
            )
        except Exception as e:
            raise QuickBooksError(f"Failed to get items: {str(e)}") from e
    
    def get_tax_rates(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Get all tax rates from QuickBooks.
        
        Args:
            limit: Maximum items per page (default: 500)
            
        Returns:
            List of tax rate dictionaries
        """
        try:
            return self._paginate(
                "/accounting/tax_rates",
                "tax_rates",
                limit=limit,
            )
        except Exception as e:
            raise QuickBooksError(f"Failed to get tax rates: {str(e)}") from e
    
    # Expense methods
    
    def create_expense(
        self,
        account_id: str,
        currency_code: str,
        transaction_date: str,
        memo: str,
        line_items: List[Dict[str, Any]],
        vendor_id: Optional[str] = None,
        expense_type: str = "expense",
        tax_inclusive: Optional[bool] = None,
        auto_exchange_rate: bool = True,
    ) -> Expense:
        """
        Create a new expense in QuickBooks via Rutter API.
        
        Args:
            account_id: Account ID for the expense (required)
            currency_code: Currency code (e.g., "USD") (required)
            transaction_date: Transaction date in ISO format (required)
            memo: Memo/description for the expense (required)
            line_items: List of line item dictionaries. Each line item should have:
                - amount: float (required)
                - total_amount: float (required)
                - description: str (required)
                - account_id: str (optional)
                - class_id: str (optional)
                - customer_id: str (optional)
                - tax_rate_id: str (optional)
                - department_id: str (optional)
                - additional_fields: dict (optional) with billable bool and item dict
            vendor_id: Optional vendor ID
            expense_type: Expense type (default: "expense")
            tax_inclusive: Whether tax is inclusive (optional)
            auto_exchange_rate: Whether to use auto exchange rate (default: True)
            
        Returns:
            Created Expense object
            
        Raises:
            QuickBooksError: If creation fails or async response is returned
            
        Note:
            This may return an async job response. The client handles both
            sync and async responses automatically.
        """
        try:
            # Build additional_fields
            additional_fields: Dict[str, Any] = {}
            if auto_exchange_rate:
                additional_fields["auto_exchange_rate"] = True
            if tax_inclusive is not None:
                additional_fields["tax_inclusive"] = tax_inclusive
            
            # Build expense payload
            expense_payload: Dict[str, Any] = {
                "account_id": account_id,
                "currency_code": currency_code,
                "transaction_date": transaction_date,
                "memo": memo,
                "expense_type": expense_type,
                "line_items": line_items,
            }
            
            if vendor_id:
                expense_payload["vendor_id"] = vendor_id
            if additional_fields:
                expense_payload["additional_fields"] = additional_fields
            
            # Build request body
            request_body = {
                "response_mode": "prefer_sync",
                "expense": expense_payload,
            }
            
            # Make request with version header
            response = self._request(
                "POST",
                "/versioned/accounting/expenses",
                data=request_body,
                headers={"x-rutter-version": "2024-08-31"},
            )
            
            # Handle async job response
            if response.get("async_response"):
                async_response = response.get("async_response", {})
                raise QuickBooksError(
                    f"Expense creation initiated asynchronously. "
                    f"Job ID: {async_response.get('id')}. "
                    f"Status: {async_response.get('status')}. "
                    f"Poll the job_id to check completion status."
                )
            
            # Handle sync response
            expense_data = response.get("expense")
            if not expense_data:
                raise QuickBooksError("No expense data in response")
            
            return Expense.from_rutter(expense_data)
            
        except QuickBooksError:
            raise
        except Exception as e:
            raise QuickBooksError(f"Failed to create expense: {str(e)}") from e

