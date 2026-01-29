"""Buildium client for accessing Buildium data via REST API."""

import os
from typing import Optional, List, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from flo.exceptions import (
    AuthenticationError,
    APIError,
    BuildiumError,
    DataSourceNotFoundError,
)
from flo.buildium.models import (
    BuildiumUser,
    BuildiumVendor,
    BuildiumGlAccount,
    BuildiumBill,
    BuildiumRental,
    BuildiumRentalOwner,
    BuildiumRentalUnit,
    BuildiumAssociation,
    BuildiumAssociationOwner,
    BuildiumAssociationUnit,
    BuildiumWorkOrder,
)


class BuildiumClient:
    """
    Client for accessing Buildium data via REST API.
    
    Credentials are automatically loaded from the global __data_sources__ dictionary
    that is injected by the Clyr backend into every agent execution.
    """
    
    # Entity paths matching BuildiumEntitiesPath enum
    USERS = "users"
    WORK_ORDERS = "workorders"
    ASSOCIATIONS = "associations"
    ASSOCIATIONS_OWNERS = "associations/owners"
    ASSOCIATIONS_UNITS = "associations/units"
    RENTALS = "rentals"
    RENTALS_OWNERS = "rentals/owners"
    RENTALS_UNITS = "rentals/units"
    ASSOCIATIONS_TENANTS = "associations/tenants"
    RENTALS_TENANTS = "leases/tenants"
    GL_ACCOUNTS = "glaccounts"
    VENDORS = "vendors"
    BILLS = "bills"
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        data_source_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Buildium client.
        
        If no parameters are provided, credentials are automatically loaded from
        the global __data_sources__ dictionary injected by the backend.
        
        Args:
            client_id: Buildium client ID (optional, auto-loaded if not provided)
            client_secret: Buildium client secret (optional, auto-loaded if not provided)
            tenant_id: Tenant ID (optional, auto-loaded if not provided)
            data_source_id: Data source ID (optional, auto-loaded if not provided)
            base_url: Buildium API base URL (optional, defaults to env var)
        """
        # Get credentials from parameters or global __data_sources__
        if client_id and client_secret and tenant_id and data_source_id:
            self.client_id = client_id
            self.client_secret = client_secret
            self.tenant_id = tenant_id
            self.data_source_id = data_source_id
        else:
            # Try to load from global __data_sources__ (injected by backend)
            try:
                import builtins
                data_sources = getattr(builtins, "__data_sources__", {})
                
                # Fallback to globals() if not in builtins
                if not data_sources:
                    data_sources = globals().get("__data_sources__", {})
                
                # Look for Buildium data source
                buildium_source = None
                for key, source in data_sources.items():
                    platform = source.get("platform", "").lower()
                    parent_platform = source.get("parent_platform", "").lower()
                    if platform == "buildium" or parent_platform == "buildium":
                        buildium_source = source
                        break
                
                if not buildium_source:
                    raise DataSourceNotFoundError(
                        "Buildium data source not found in __data_sources__. "
                        "Make sure your team has connected Buildium."
                    )
                
                keys = buildium_source.get("keys", {})
                self.client_id = keys.get("clientId")
                self.client_secret = keys.get("clientSecret")
                self.tenant_id = buildium_source.get("tenant_id")
                self.data_source_id = buildium_source.get("id")
                
                if not self.client_id:
                    raise AuthenticationError("No clientId found in data source keys")
                if not self.client_secret:
                    raise AuthenticationError("No clientSecret found in data source keys")
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
        self.base_url = base_url or os.getenv("BUILDIUM_URI", "https://api.buildium.com")
        
        # Create requests session
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "x-buildium-client-id": self.client_id,
            "x-buildium-client-secret": self.client_secret,
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
        Make a request to the Buildium API.
        
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
        url = f"{self.base_url}/v1/{endpoint}"
        
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
        limit: int = 1000,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Paginate through Buildium API results.
        
        Buildium uses offset/limit pagination and returns total count in x-total-count header.
        
        Args:
            endpoint: API endpoint
            limit: Items per page (default: 1000)
            params: Additional query parameters
            
        Returns:
            List of all items from all pages
        """
        if params is None:
            params = {}
        
        all_items = []
        offset = 0
        
        while True:
            pagination_params = {
                "limit": limit,
                "offset": offset,
                **params,
            }
            
            # Make request directly to get response headers
            url = f"{self.base_url}/v1/{endpoint}"
            response = self.session.get(
                url,
                params=pagination_params,
                timeout=30,
            )
            
            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError(f"Authentication failed: {response.text}")
            if not response.ok:
                raise APIError(
                    f"API request failed: {response.text}",
                    status_code=response.status_code,
                    response=response.json() if response.content else None,
                )
            
            # Parse response
            items = response.json()
            if not isinstance(items, list):
                items = []
            
            all_items.extend(items)
            
            # Check if we've fetched all items by comparing with total count header
            total_count = response.headers.get("x-total-count")
            if total_count:
                total_count_int = int(total_count)
                if len(all_items) >= total_count_int:
                    break
            
            # If no total count header, stop when we get fewer items than requested
            if len(items) < limit:
                break
            
            offset += limit
        
        return all_items
    
    # User methods
    
    def get_users(self) -> List[BuildiumUser]:
        """
        Get all users from Buildium.
        
        Returns:
            List of BuildiumUser objects
        """
        try:
            users_data = self._paginate(self.USERS)
            return [BuildiumUser.from_buildium(u) for u in users_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get users: {str(e)}") from e
    
    # Vendor methods
    
    def get_vendors(self) -> List[BuildiumVendor]:
        """
        Get all vendors from Buildium.
        
        Returns:
            List of BuildiumVendor objects
        """
        try:
            vendors_data = self._paginate(self.VENDORS)
            return [BuildiumVendor.from_buildium(v) for v in vendors_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get vendors: {str(e)}") from e
    
    # GL Account methods
    
    def get_gl_accounts(self) -> List[BuildiumGlAccount]:
        """
        Get all GL accounts from Buildium.
        
        Returns:
            List of BuildiumGlAccount objects
        """
        try:
            gl_accounts_data = self._paginate(self.GL_ACCOUNTS)
            return [BuildiumGlAccount.from_buildium(g) for g in gl_accounts_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get GL accounts: {str(e)}") from e
    
    # Bill methods
    
    def get_bills(self, paid_status: Optional[str] = None) -> List[BuildiumBill]:
        """
        Get bills from Buildium.
        
        Args:
            paid_status: Filter by paid status (e.g., "Unpaid", "Paid")
            
        Returns:
            List of BuildiumBill objects
        """
        try:
            params = {}
            if paid_status:
                params["paidstatus"] = paid_status
            
            bills_data = self._paginate(self.BILLS, params=params)
            return [BuildiumBill.from_buildium(b) for b in bills_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get bills: {str(e)}") from e
    
    # Rental methods
    
    def get_rentals(self) -> List[BuildiumRental]:
        """
        Get all rentals from Buildium.
        
        Returns:
            List of BuildiumRental objects
        """
        try:
            rentals_data = self._paginate(self.RENTALS)
            return [BuildiumRental.from_buildium(r) for r in rentals_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get rentals: {str(e)}") from e
    
    def get_rental_owners(self) -> List[BuildiumRentalOwner]:
        """
        Get all rental owners from Buildium.
        
        Returns:
            List of BuildiumRentalOwner objects
        """
        try:
            owners_data = self._paginate(self.RENTALS_OWNERS)
            return [BuildiumRentalOwner.from_buildium(o) for o in owners_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get rental owners: {str(e)}") from e
    
    def get_rental_units(self) -> List[BuildiumRentalUnit]:
        """
        Get all rental units from Buildium.
        
        Returns:
            List of BuildiumRentalUnit objects
        """
        try:
            units_data = self._paginate(self.RENTALS_UNITS)
            return [BuildiumRentalUnit.from_buildium(u) for u in units_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get rental units: {str(e)}") from e
    
    # Association methods
    
    def get_associations(self) -> List[BuildiumAssociation]:
        """
        Get all associations from Buildium.
        
        Returns:
            List of BuildiumAssociation objects
        """
        try:
            associations_data = self._paginate(self.ASSOCIATIONS)
            return [BuildiumAssociation.from_buildium(a) for a in associations_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get associations: {str(e)}") from e
    
    def get_association_owners(self) -> List[BuildiumAssociationOwner]:
        """
        Get all association owners from Buildium.
        
        Returns:
            List of BuildiumAssociationOwner objects
        """
        try:
            owners_data = self._paginate(self.ASSOCIATIONS_OWNERS)
            return [BuildiumAssociationOwner.from_buildium(o) for o in owners_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get association owners: {str(e)}") from e
    
    def get_association_units(self) -> List[BuildiumAssociationUnit]:
        """
        Get all association units from Buildium.
        
        Returns:
            List of BuildiumAssociationUnit objects
        """
        try:
            units_data = self._paginate(self.ASSOCIATIONS_UNITS)
            return [BuildiumAssociationUnit.from_buildium(u) for u in units_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get association units: {str(e)}") from e
    
    # Work Order methods
    
    def get_work_orders(self) -> List[BuildiumWorkOrder]:
        """
        Get all work orders from Buildium.
        
        Returns:
            List of BuildiumWorkOrder objects
        """
        try:
            work_orders_data = self._paginate(self.WORK_ORDERS)
            return [BuildiumWorkOrder.from_buildium(w) for w in work_orders_data]
        except Exception as e:
            raise BuildiumError(f"Failed to get work orders: {str(e)}") from e
