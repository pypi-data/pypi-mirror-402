"""Hostaway client for accessing Hostaway data via REST API."""

import os
from typing import Optional, List, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from flo.exceptions import (
    AuthenticationError,
    APIError,
    HostawayError,
    DataSourceNotFoundError,
)
from flo.hostaway.models import (
    HostawayListing,
    HostawayOwner,
    HostawayUser,
    HostawayUnit,
)


class HostawayClient:
    """
    Client for accessing Hostaway data via REST API.
    
    Credentials are automatically loaded from the global __data_sources__ dictionary
    that is injected by the Clyr backend into every agent execution.
    """
    
    # Entity paths matching HostawayEntities type
    LISTINGS = "listings"
    OWNERS = "owners"
    USERS = "users"
    UNITS = "units"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        data_source_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Hostaway client.
        
        If no parameters are provided, credentials are automatically loaded from
        the global __data_sources__ dictionary injected by the backend.
        
        Args:
            access_token: Hostaway access token (optional, auto-loaded if not provided)
            client_id: Hostaway client ID (optional, auto-loaded if not provided)
            client_secret: Hostaway client secret (optional, auto-loaded if not provided)
            tenant_id: Tenant ID (optional, auto-loaded if not provided)
            data_source_id: Data source ID (optional, auto-loaded if not provided)
            base_url: Hostaway API base URL (optional, defaults to env var)
        """
        # Get credentials from parameters or global __data_sources__
        if access_token and client_id and client_secret and tenant_id and data_source_id:
            self.access_token = access_token
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
                
                # Look for Hostaway data source
                hostaway_source = None
                for key, source in data_sources.items():
                    platform = source.get("platform", "").lower()
                    parent_platform = source.get("parent_platform", "").lower()
                    if platform == "hostaway" or parent_platform == "hostaway":
                        hostaway_source = source
                        break
                
                if not hostaway_source:
                    raise DataSourceNotFoundError(
                        "Hostaway data source not found in __data_sources__. "
                        "Make sure your team has connected Hostaway."
                    )
                
                keys = hostaway_source.get("keys", {})
                self.access_token = keys.get("accessToken")
                self.client_id = keys.get("clientId")
                self.client_secret = keys.get("clientSecret")
                self.tenant_id = hostaway_source.get("tenant_id")
                self.data_source_id = hostaway_source.get("id")
                
                if not self.access_token:
                    raise AuthenticationError("No accessToken found in data source keys")
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
        self.base_url = base_url or os.getenv("HOSTAWAY_URI", "https://api.hostaway.com/v1")
        
        # Create requests session
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
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
        Make a request to the Hostaway API.
        
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
        url = f"{self.base_url}/{endpoint}"
        
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
        Paginate through Hostaway API results.
        
        Hostaway uses offset/limit pagination.
        
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
            url = f"{self.base_url}/{endpoint}"
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
            
            # Parse response - Hostaway API may return results in different formats
            response_data = response.json()
            
            # Handle different response formats
            if isinstance(response_data, dict):
                # Check if results are in a 'result' key
                if "result" in response_data:
                    items = response_data["result"]
                # Check if results are in a 'data' key
                elif "data" in response_data:
                    items = response_data["data"]
                # Check if results are in a list format
                elif isinstance(response_data.get("items"), list):
                    items = response_data["items"]
                else:
                    # If the dict itself contains the items (e.g., listings directly)
                    items = [response_data] if response_data else []
            elif isinstance(response_data, list):
                items = response_data
            else:
                items = []
            
            if not isinstance(items, list):
                items = []
            
            all_items.extend(items)
            
            # Check if we've fetched all items
            # If we got fewer items than requested, we're done
            if len(items) < limit:
                break
            
            # Check if there's pagination info in response
            if isinstance(response_data, dict):
                # Check for common pagination indicators
                has_more = response_data.get("hasMore", False)
                if not has_more:
                    break
                
                # Check total count if available
                total_count = response_data.get("totalCount") or response_data.get("total")
                if total_count and len(all_items) >= total_count:
                    break
            
            offset += limit
        
        return all_items
    
    # Listing methods
    
    def get_listings(self) -> List[HostawayListing]:
        """
        Get all listings from Hostaway.
        
        Returns:
            List of HostawayListing objects
        """
        try:
            listings_data = self._paginate(self.LISTINGS)
            return [HostawayListing.from_hostaway(l) for l in listings_data]
        except Exception as e:
            raise HostawayError(f"Failed to get listings: {str(e)}") from e
    
    # Owner methods
    
    def get_owners(self) -> List[HostawayOwner]:
        """
        Get all owners from Hostaway.
        
        Returns:
            List of HostawayOwner objects
        """
        try:
            owners_data = self._paginate(self.OWNERS)
            return [HostawayOwner.from_hostaway(o) for o in owners_data]
        except Exception as e:
            raise HostawayError(f"Failed to get owners: {str(e)}") from e
    
    # User methods
    
    def get_users(self) -> List[HostawayUser]:
        """
        Get all users from Hostaway.
        
        Returns:
            List of HostawayUser objects
        """
        try:
            users_data = self._paginate(self.USERS)
            return [HostawayUser.from_hostaway(u) for u in users_data]
        except Exception as e:
            raise HostawayError(f"Failed to get users: {str(e)}") from e
    
    # Unit methods
    
    def get_units(self) -> List[HostawayUnit]:
        """
        Get all units from Hostaway.
        
        Returns:
            List of HostawayUnit objects
        """
        try:
            units_data = self._paginate(self.UNITS)
            return [HostawayUnit.from_hostaway(u) for u in units_data]
        except Exception as e:
            raise HostawayError(f"Failed to get units: {str(e)}") from e
