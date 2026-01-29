"""Plaid client for accessing bank data via Plaid API."""

import os
import re
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.model.country_code import CountryCode
from plaid.model.products import Products

from flo.exceptions import (
    AuthenticationError,
    APIError,
    PlaidError,
    DataSourceNotFoundError,
)
from flo.plaid.models import Account, Transaction, Institution


class PlaidClient:
    """
    Client for accessing Plaid bank data.
    
    Credentials are automatically loaded from the global __data_sources__ dictionary
    that is injected by the Clyr backend into every agent execution.
    """
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        item_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        data_source_id: Optional[str] = None,
        client_id: Optional[str] = None,
        secret: Optional[str] = None,
        environment: Optional[str] = None,
    ):
        """
        Initialize Plaid client.
        
        If no parameters are provided, credentials are automatically loaded from
        the global __data_sources__ dictionary injected by the backend.
        
        Args:
            access_token: Plaid access token (optional, auto-loaded if not provided)
            item_id: Plaid item ID (optional, auto-loaded if not provided)
            tenant_id: Tenant ID (optional, auto-loaded if not provided)
            data_source_id: Data source ID (optional, auto-loaded if not provided)
            client_id: Plaid client ID (optional, defaults to env var)
            secret: Plaid secret (optional, defaults to env var)
            environment: Plaid environment (optional, defaults to env var or sandbox)
        """
        # Get credentials from parameters or global __data_sources__
        if access_token and item_id and tenant_id and data_source_id:
            self.access_token = access_token
            self.item_id = item_id
            self.tenant_id = tenant_id
            self.data_source_id = data_source_id
        else:
            # Try to load from global __data_sources__ (injected by backend)
            try:
                # Check if __data_sources__ is available (injected by backend)
                import builtins
                data_sources = getattr(builtins, "__data_sources__", {})
                
                # Fallback to globals() if not in builtins
                if not data_sources:
                    data_sources = globals().get("__data_sources__", {})
                
                # Look for Plaid data source
                plaid_source = None
                for key, source in data_sources.items():
                    platform = source.get("platform", "").lower()
                    parent_platform = source.get("parent_platform", "").lower()
                    if platform == "plaid" or parent_platform == "plaid":
                        plaid_source = source
                        break
                
                if not plaid_source:
                    raise DataSourceNotFoundError(
                        "Plaid data source not found in __data_sources__. "
                        "Make sure your team has connected Plaid."
                    )
                
                keys = plaid_source.get("keys", {})
                self.access_token = keys.get("access_token")
                self.item_id = keys.get("item_id")
                self.tenant_id = plaid_source.get("tenant_id")
                self.data_source_id = plaid_source.get("id")
                
                if not self.access_token:
                    raise AuthenticationError("No access token found in data source")
                if not self.item_id:
                    raise AuthenticationError("No item_id found in data source")
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
        self.client_id = client_id or os.getenv("PLAID_CLIENT_ID")
        self.secret = secret or os.getenv("PLAID_SECRET") or os.getenv("PLAID_CLIENT_SECRET")
        self.environment = environment or os.getenv("PLAID_ENV", "sandbox")
        
        # Debug: Check if env vars are available (helps diagnose Modal injection issues)
        env_client_id = os.getenv("PLAID_CLIENT_ID")
        env_secret = os.getenv("PLAID_SECRET") or os.getenv("PLAID_CLIENT_SECRET")
        
        if not self.client_id or not self.secret:
            error_msg = (
                f"PLAID_CLIENT_ID and PLAID_SECRET must be set. "
                f"Client ID from env: {bool(env_client_id)}, "
                f"Secret from env: {bool(env_secret)}, "
                f"Client ID provided: {bool(client_id)}, "
                f"Secret provided: {bool(secret)}"
            )
            raise AuthenticationError(error_msg)
        
        # Initialize Plaid API client
        # Plaid Python SDK expects credentials via api_key dictionary in Configuration constructor
        # According to: https://github.com/plaid/plaid-python
        # The api_key should use camelCase: 'clientId' and 'secret'
        configuration = Configuration(
            host=self._get_plaid_host(self.environment),
            api_key={
                'clientId': self.client_id,
                'secret': self.secret,
            }
        )
        
        # Create API client with configuration
        api_client = plaid_api.ApiClient(configuration)
        self.plaid_client = plaid_api.PlaidApi(api_client)
    
    def _get_plaid_host(self, environment: str) -> str:
        """Get Plaid host URL based on environment."""
        env_map = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com",
        }
        return env_map.get(environment.lower(), env_map["sandbox"])
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _handle_plaid_error(self, error: Exception) -> None:
        """Handle Plaid API errors and convert to appropriate exceptions."""
        error_msg = str(error)
        
        # Check for authentication errors
        if "invalid_access_token" in error_msg.lower() or "401" in error_msg:
            raise AuthenticationError(f"Plaid authentication failed: {error_msg}")
        
        # Check for API errors
        if "plaid" in error_msg.lower():
            raise PlaidError(f"Plaid API error: {error_msg}")
        
        # Generic API error
        raise APIError(f"Plaid request failed: {error_msg}")
    
    def get_accounts(self) -> List[Account]:
        """
        Get all accounts from Plaid.
        
        Returns:
            List of Account objects
        """
        try:
            from plaid.model.accounts_get_request import AccountsGetRequest
            
            request = AccountsGetRequest(access_token=self.access_token)
            response = self.plaid_client.accounts_get(request)
            
            # Handle response object (has attributes, not dict keys)
            accounts_data = response.accounts if hasattr(response, 'accounts') else []
            item = response.item if hasattr(response, 'item') else None
            institution_id = item.institution_id if item and hasattr(item, 'institution_id') else None
            
            # Try to fetch institution name if we have institution_id
            institution_name = None
            if institution_id:
                try:
                    institution = self.get_institution(institution_id)
                    institution_name = institution.name
                except Exception:
                    # If institution fetch fails, continue without name
                    pass
            
            # Convert account objects to dicts for from_plaid
            accounts_list = []
            for account in accounts_data:
                account_dict = {}
                if hasattr(account, '__dict__'):
                    account_dict = account.__dict__
                elif isinstance(account, dict):
                    account_dict = account
                else:
                    # Try to access as attributes
                    account_dict = {
                        'account_id': getattr(account, 'account_id', None),
                        'name': getattr(account, 'name', None),
                        'mask': getattr(account, 'mask', None),
                        'type': getattr(account, 'type', None),
                        'subtype': getattr(account, 'subtype', None),
                        'balances': getattr(account, 'balances', None),
                        'iso_currency_code': getattr(account, 'iso_currency_code', None),
                        'unofficial_currency_code': getattr(account, 'unofficial_currency_code', None),
                    }
                accounts_list.append(account_dict)
            
            return [
                Account.from_plaid(
                    account_data,
                    institution_id=institution_id,
                    institution_name=institution_name,
                )
                for account_data in accounts_list
            ]
        except Exception as e:
            self._handle_plaid_error(e)
            raise PlaidError(f"Failed to get accounts: {str(e)}") from e
    
    def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        account_ids: Optional[List[str]] = None,
    ) -> List[Transaction]:
        """
        Get transactions from Plaid.
        
        Args:
            start_date: Start date for transactions (defaults to 30 days ago)
            end_date: End date for transactions (defaults to today)
            account_ids: Optional list of account IDs to filter by
            
        Returns:
            List of Transaction objects
        """
        try:
            from plaid.model.transactions_get_request import TransactionsGetRequest
            from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
            
            # Default to last 30 days if not provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Convert datetime to date objects (Plaid SDK expects date objects, not strings or datetime)
            start_date_obj = start_date.date() if isinstance(start_date, datetime) else start_date
            end_date_obj = end_date.date() if isinstance(end_date, datetime) else end_date
            
            # Build request - only include options if account_ids is provided
            request_params = {
                'access_token': self.access_token,
                'start_date': start_date_obj,
                'end_date': end_date_obj,
            }
            
            if account_ids:
                options = TransactionsGetRequestOptions(account_ids=account_ids)
                request_params['options'] = options
            
            request = TransactionsGetRequest(**request_params)
            
            # Handle pagination
            all_transactions = []
            response = self.plaid_client.transactions_get(request)
            
            # Handle response object
            transactions = response.transactions if hasattr(response, 'transactions') else []
            total_transactions = getattr(response, 'total_transactions', len(transactions))
            
            # Helper function to convert camelCase to snake_case
            def _camel_to_snake(name):
                """Convert camelCase to snake_case."""
                s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
                return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
            
            # Convert transaction objects to dicts
            def _transaction_to_dict(txn):
                # Try to_dict() first (Plaid SDK objects often have this)
                if hasattr(txn, 'to_dict'):
                    txn_dict = txn.to_dict()
                    # Convert camelCase keys to snake_case for from_plaid
                    return {_camel_to_snake(k): v for k, v in txn_dict.items()}
                
                if isinstance(txn, dict):
                    # If already a dict, check if keys are camelCase and convert
                    if any(k and (k[0].isupper() or any(c.isupper() for c in k[1:])) for k in txn.keys()):
                        return {_camel_to_snake(k): v for k, v in txn.items()}
                    return txn
                    
                if hasattr(txn, '__dict__'):
                    return txn.__dict__
                
                # Try both snake_case and camelCase attributes as fallback
                return {
                    'transaction_id': getattr(txn, 'transaction_id', None) or getattr(txn, 'transactionId', None),
                    'account_id': getattr(txn, 'account_id', None) or getattr(txn, 'accountId', None),
                    'amount': getattr(txn, 'amount', None),
                    'date': getattr(txn, 'date', None),
                    'name': getattr(txn, 'name', None),
                    'merchant_name': getattr(txn, 'merchant_name', None) or getattr(txn, 'merchantName', None),
                    'category': getattr(txn, 'category', None),
                    'pending': getattr(txn, 'pending', None),
                    'iso_currency_code': getattr(txn, 'iso_currency_code', None) or getattr(txn, 'isoCurrencyCode', None),
                    'unofficial_currency_code': getattr(txn, 'unofficial_currency_code', None) or getattr(txn, 'unofficialCurrencyCode', None),
                    'authorized_date': getattr(txn, 'authorized_date', None) or getattr(txn, 'authorizedDate', None),
                    'location': getattr(txn, 'location', None),
                    'payment_meta': getattr(txn, 'payment_meta', None) or getattr(txn, 'paymentMeta', None),
                }
            
            all_transactions.extend([_transaction_to_dict(t) for t in transactions])
            
            # Paginate if necessary
            while len(all_transactions) < total_transactions:
                # Build pagination request with same date objects
                pagination_params = {
                    'access_token': self.access_token,
                    'start_date': start_date_obj,
                    'end_date': end_date_obj,
                }
                
                # Build options with offset
                pagination_options_params = {'offset': len(all_transactions)}
                if account_ids:
                    pagination_options_params['account_ids'] = account_ids
                
                pagination_options = TransactionsGetRequestOptions(**pagination_options_params)
                pagination_params['options'] = pagination_options
                
                request = TransactionsGetRequest(**pagination_params)
                response = self.plaid_client.transactions_get(request)
                page_transactions = response.transactions if hasattr(response, 'transactions') else []
                if not page_transactions:
                    break
                all_transactions.extend([_transaction_to_dict(t) for t in page_transactions])
            
            return [Transaction.from_plaid(t) for t in all_transactions]
        except Exception as e:
            self._handle_plaid_error(e)
            raise PlaidError(f"Failed to get transactions: {str(e)}") from e
    
    def get_balance(self, account_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get account balances from Plaid.
        
        Args:
            account_ids: Optional list of account IDs to filter by
            
        Returns:
            Dictionary with account balances
        """
        try:
            from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
            from plaid.model.accounts_balance_get_request_options import AccountsBalanceGetRequestOptions
            
            # Build request - only include options if account_ids is provided
            request_params = {
                'access_token': self.access_token,
            }
            
            if account_ids:
                options = AccountsBalanceGetRequestOptions(account_ids=account_ids)
                request_params['options'] = options
            
            request = AccountsBalanceGetRequest(**request_params)
            response = self.plaid_client.accounts_balance_get(request)
            
            accounts = response.accounts if hasattr(response, 'accounts') else []
            
            # Format balances by account - ensure all values are JSON-serializable primitives
            balances = {}
            for account in accounts:
                # Extract account_id
                account_id = None
                if isinstance(account, dict):
                    account_id = account.get('account_id')
                elif hasattr(account, 'account_id'):
                    account_id = account.account_id
                
                if not account_id:
                    continue
                
                # Extract balances object
                balances_obj = None
                if isinstance(account, dict):
                    balances_obj = account.get('balances')
                elif hasattr(account, 'balances'):
                    balances_obj = account.balances
                
                # Extract primitive values from balances
                available = None
                current = None
                limit = None
                iso_currency_code = None
                unofficial_currency_code = None
                
                if balances_obj:
                    # Try to_dict() first (Plaid SDK objects often have this)
                    if hasattr(balances_obj, 'to_dict'):
                        balances_dict = balances_obj.to_dict()
                        available = balances_dict.get('available')
                        current = balances_dict.get('current')
                        limit = balances_dict.get('limit')
                        iso_currency_code = balances_dict.get('iso_currency_code')
                        unofficial_currency_code = balances_dict.get('unofficial_currency_code')
                    elif isinstance(balances_obj, dict):
                        available = balances_obj.get('available')
                        current = balances_obj.get('current')
                        limit = balances_obj.get('limit')
                        iso_currency_code = balances_obj.get('iso_currency_code')
                        unofficial_currency_code = balances_obj.get('unofficial_currency_code')
                    else:
                        # Extract as attributes
                        available = getattr(balances_obj, 'available', None)
                        current = getattr(balances_obj, 'current', None)
                        limit = getattr(balances_obj, 'limit', None)
                        iso_currency_code = getattr(balances_obj, 'iso_currency_code', None)
                        unofficial_currency_code = getattr(balances_obj, 'unofficial_currency_code', None)
                
                # Ensure all values are JSON-serializable (convert to float/str/None)
                balances[account_id] = {
                    "available": float(available) if available is not None else None,
                    "current": float(current) if current is not None else None,
                    "limit": float(limit) if limit is not None else None,
                    "isoCurrencyCode": str(iso_currency_code) if iso_currency_code is not None else None,
                    "unofficialCurrencyCode": str(unofficial_currency_code) if unofficial_currency_code is not None else None,
                }
            
            return balances
        except Exception as e:
            self._handle_plaid_error(e)
            raise PlaidError(f"Failed to get balances: {str(e)}") from e
    
    def get_institution(self, institution_id: str) -> Institution:
        """
        Get institution details from Plaid.
        
        Args:
            institution_id: Plaid institution ID
            
        Returns:
            Institution object
        """
        try:
            from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
            
            request = InstitutionsGetByIdRequest(
                institution_id=institution_id,
                country_codes=[CountryCode("US")],
            )
            response = self.plaid_client.institutions_get_by_id(request)
            
            institution_obj = response.institution if hasattr(response, 'institution') else None
            if institution_obj:
                if hasattr(institution_obj, '__dict__'):
                    institution_data = institution_obj.__dict__
                elif isinstance(institution_obj, dict):
                    institution_data = institution_obj
                else:
                    institution_data = {
                        'institution_id': getattr(institution_obj, 'institution_id', None),
                        'name': getattr(institution_obj, 'name', None),
                        'logo': getattr(institution_obj, 'logo', None),
                        'url': getattr(institution_obj, 'url', None),
                        'primary_color': getattr(institution_obj, 'primary_color', None),
                        'country_codes': getattr(institution_obj, 'country_codes', None),
                        'products': getattr(institution_obj, 'products', None),
                    }
            else:
                institution_data = {}
            
            return Institution.from_plaid(institution_data)
        except Exception as e:
            self._handle_plaid_error(e)
            raise PlaidError(f"Failed to get institution: {str(e)}") from e
    
    def get_item(self) -> Dict[str, Any]:
        """
        Get item details from Plaid.
        
        Returns:
            Dictionary with item metadata
        """
        try:
            from plaid.model.item_get_request import ItemGetRequest
            
            request = ItemGetRequest(access_token=self.access_token)
            response = self.plaid_client.item_get(request)
            
            item = response.item if hasattr(response, 'item') else None
            if item:
                if isinstance(item, dict):
                    item_dict = item
                elif hasattr(item, '__dict__'):
                    item_dict = item.__dict__
                else:
                    item_dict = {
                        'item_id': getattr(item, 'item_id', None),
                        'institution_id': getattr(item, 'institution_id', None),
                        'webhook': getattr(item, 'webhook', None),
                        'error': getattr(item, 'error', None),
                        'available_products': getattr(item, 'available_products', None),
                        'billed_products': getattr(item, 'billed_products', None),
                        'consent_expiration_time': getattr(item, 'consent_expiration_time', None),
                        'update_type': getattr(item, 'update_type', None),
                    }
            else:
                item_dict = {}
            
            return {
                "itemId": item_dict.get("item_id") if isinstance(item_dict, dict) else getattr(item, 'item_id', None),
                "institutionId": item_dict.get("institution_id") if isinstance(item_dict, dict) else getattr(item, 'institution_id', None),
                "webhook": item_dict.get("webhook") if isinstance(item_dict, dict) else getattr(item, 'webhook', None),
                "error": item_dict.get("error") if isinstance(item_dict, dict) else getattr(item, 'error', None),
                "availableProducts": item_dict.get("available_products") if isinstance(item_dict, dict) else getattr(item, 'available_products', None),
                "billedProducts": item_dict.get("billed_products") if isinstance(item_dict, dict) else getattr(item, 'billed_products', None),
                "consentExpirationTime": item_dict.get("consent_expiration_time") if isinstance(item_dict, dict) else getattr(item, 'consent_expiration_time', None),
                "updateType": item_dict.get("update_type") if isinstance(item_dict, dict) else getattr(item, 'update_type', None),
            }
        except Exception as e:
            self._handle_plaid_error(e)
            raise PlaidError(f"Failed to get item: {str(e)}") from e

