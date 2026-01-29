"""Rent Manager client for accessing Rent Manager data via REST API."""

import os
from typing import Optional, List, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from flo.exceptions import (
    AuthenticationError,
    APIError,
    RentManagerError,
    DataSourceNotFoundError,
)
from flo.rent_manager.models import (
    RentManagerUser,
    RentManagerOwner,
    RentManagerProperty,
    RentManagerUnit,
    RentManagerJob,
    RentManagerCreditCard,
    RentManagerIssue,
    RentManagerGlAccount,
    RentManagerVendor,
)


class RentManagerClient:
    """
    Client for accessing Rent Manager data via REST API.
    
    Credentials are automatically loaded from the global __data_sources__ dictionary
    that is injected by the Clyr backend into every agent execution.
    """
    
    # Entity paths matching RentManagerCrmEntities and RentManagerErpEntities
    USERS = "Users"
    OWNERS = "Owners"
    PROPERTIES = "Properties"
    UNITS = "Units"
    JOBS = "Jobs"
    CREDIT_CARDS = "CreditCards"
    ISSUES = "Issues"
    GL_ACCOUNTS = "GLAccounts"
    VENDORS = "Vendors"
    
    def __init__(
        self,
        sub_domain: Optional[str] = None,
        tenant_id: Optional[str] = None,
        data_source_id: Optional[str] = None,
        partner_token: Optional[str] = None,
    ):
        """
        Initialize Rent Manager client.
        
        If no parameters are provided, credentials are automatically loaded from
        the global __data_sources__ dictionary injected by the backend.
        
        Args:
            sub_domain: Rent Manager subdomain (optional, auto-loaded if not provided)
            tenant_id: Tenant ID (optional, auto-loaded if not provided)
            data_source_id: Data source ID (optional, auto-loaded if not provided)
            partner_token: Partner token (optional, auto-loaded from env if not provided)
        """
        # Get credentials from parameters or global __data_sources__
        if sub_domain and tenant_id and data_source_id:
            self.sub_domain = sub_domain
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
                
                # Look for Rent Manager data source
                rm_source = None
                for key, source in data_sources.items():
                    platform = source.get("platform", "").lower()
                    parent_platform = source.get("parent_platform", "").lower()
                    if platform == "rent_manager" or parent_platform == "rent_manager":
                        rm_source = source
                        break
                
                if not rm_source:
                    raise DataSourceNotFoundError(
                        "Rent Manager data source not found in __data_sources__. "
                        "Make sure your team has connected Rent Manager."
                    )
                
                keys = rm_source.get("keys", {})
                self.sub_domain = keys.get("subDomain")
                self.tenant_id = rm_source.get("tenant_id")
                self.data_source_id = rm_source.get("id")
                
                if not self.sub_domain:
                    raise AuthenticationError("No subDomain found in data source keys")
                if not self.tenant_id:
                    raise AuthenticationError("No tenant_id found in data source")
                if not self.data_source_id:
                    raise AuthenticationError("No data_source_id found in data source")
                    
            except NameError:
                raise DataSourceNotFoundError(
                    "__data_sources__ not found. This client must be used within "
                    "a Clyr agent execution context, or credentials must be provided manually."
                )
        
        # Get partner token from environment or parameter
        self.partner_token = partner_token or os.getenv("RM_PARTNER_TOKEN")
        if not self.partner_token:
            raise AuthenticationError(
                "RM_PARTNER_TOKEN must be set (injected by backend or provided as env var)"
            )
        
        # Create requests session
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "x-rm12api-partnertoken": self.partner_token,
            "X-RM12Api-CheckedPrivileges": "true",
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
    ) -> requests.Response:
        """
        Make a request to the Rent Manager API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (entity name)
            params: Query parameters
            data: Request body data
            headers: Optional additional headers
            
        Returns:
            Response object
            
        Raises:
            APIError: If the request fails
            AuthenticationError: If authentication fails
        """
        url = f"https://{self.sub_domain}.api.rentmanager.com/{endpoint}"
        
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
            
            return response
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    def _paginate(
        self,
        endpoint: str,
        page_size: int = 250,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Paginate through Rent Manager API results.
        
        Rent Manager uses PageSize/PageNumber pagination and returns total count
        in x-total-results header.
        
        Args:
            endpoint: API endpoint (entity name)
            page_size: Items per page (default: 250, varies by entity)
            params: Additional query parameters
            
        Returns:
            List of all items from all pages
        """
        if params is None:
            params = {}
        
        all_items = []
        page = 0
        
        while True:
            params.update({
                "PageSize": page_size,
                "PageNumber": page + 1,  # Rent Manager uses 1-based page numbers
            })
            
            response = self._request("GET", endpoint, params=params)
            items = response.json()
            
            # Rent Manager returns data directly as a list
            if not isinstance(items, list):
                items = []
            
            all_items.extend(items)
            
            # Check if we've fetched all items by comparing with total count header
            total_results = response.headers.get("x-total-results")
            if total_results:
                total_count = int(total_results)
                if len(all_items) >= total_count:
                    break
            
            # If no total count header, stop when we get fewer items than requested
            if len(items) < page_size:
                break
            
            page += 1
        
        return all_items
    
    # User methods
    
    def get_users(self) -> List[RentManagerUser]:
        """
        Get all users from Rent Manager.
        
        Returns:
            List of RentManagerUser objects
        """
        try:
            users_data = self._paginate(self.USERS, page_size=250)
            return [RentManagerUser.from_rent_manager(u) for u in users_data]
        except Exception as e:
            raise RentManagerError(f"Failed to get users: {str(e)}") from e
    
    # Owner methods
    
    def get_owners(self) -> List[RentManagerOwner]:
        """
        Get all owners from Rent Manager.
        
        Returns:
            List of RentManagerOwner objects
        """
        try:
            owners_data = self._paginate(self.OWNERS, page_size=250)
            return [RentManagerOwner.from_rent_manager(o) for o in owners_data]
        except Exception as e:
            raise RentManagerError(f"Failed to get owners: {str(e)}") from e
    
    # Property methods
    
    def get_properties(self) -> List[RentManagerProperty]:
        """
        Get all properties from Rent Manager.
        
        Returns:
            List of RentManagerProperty objects
        """
        try:
            properties_data = self._paginate(self.PROPERTIES, page_size=250)
            return [RentManagerProperty.from_rent_manager(p) for p in properties_data]
        except Exception as e:
            raise RentManagerError(f"Failed to get properties: {str(e)}") from e
    
    # Unit methods
    
    def get_units(self) -> List[RentManagerUnit]:
        """
        Get all units from Rent Manager.
        
        Returns:
            List of RentManagerUnit objects
        """
        try:
            units_data = self._paginate(self.UNITS, page_size=250)
            return [RentManagerUnit.from_rent_manager(u) for u in units_data]
        except Exception as e:
            raise RentManagerError(f"Failed to get units: {str(e)}") from e
    
    # Job methods
    
    def get_jobs(self) -> List[RentManagerJob]:
        """
        Get all jobs from Rent Manager.
        
        Returns:
            List of RentManagerJob objects
        """
        try:
            jobs_data = self._paginate(self.JOBS, page_size=250)
            return [RentManagerJob.from_rent_manager(j) for j in jobs_data]
        except Exception as e:
            raise RentManagerError(f"Failed to get jobs: {str(e)}") from e
    
    # Credit Card methods
    
    def get_credit_cards(self) -> List[RentManagerCreditCard]:
        """
        Get all credit cards from Rent Manager.
        
        Returns:
            List of RentManagerCreditCard objects
        """
        try:
            cards_data = self._paginate(self.CREDIT_CARDS, page_size=250)
            return [RentManagerCreditCard.from_rent_manager(c) for c in cards_data]
        except Exception as e:
            raise RentManagerError(f"Failed to get credit cards: {str(e)}") from e
    
    # Issue methods
    
    def get_issues(self) -> List[RentManagerIssue]:
        """
        Get all issues from Rent Manager.
        
        Returns:
            List of RentManagerIssue objects
        """
        try:
            # Issues use page size 500
            issues_data = self._paginate(self.ISSUES, page_size=500)
            return [RentManagerIssue.from_rent_manager(i) for i in issues_data]
        except Exception as e:
            raise RentManagerError(f"Failed to get issues: {str(e)}") from e
    
    # GL Account methods
    
    def get_gl_accounts(self) -> List[RentManagerGlAccount]:
        """
        Get all GL accounts from Rent Manager.
        
        Returns:
            List of RentManagerGlAccount objects
        """
        try:
            gl_accounts_data = self._paginate(self.GL_ACCOUNTS, page_size=250)
            return [RentManagerGlAccount.from_rent_manager(g) for g in gl_accounts_data]
        except Exception as e:
            raise RentManagerError(f"Failed to get GL accounts: {str(e)}") from e
    
    # Vendor methods
    
    def get_vendors(self) -> List[RentManagerVendor]:
        """
        Get all vendors from Rent Manager.
        
        Returns:
            List of RentManagerVendor objects
        """
        try:
            # Vendors use page size 100
            vendors_data = self._paginate(self.VENDORS, page_size=100)
            return [RentManagerVendor.from_rent_manager(v) for v in vendors_data]
        except Exception as e:
            raise RentManagerError(f"Failed to get vendors: {str(e)}") from e
