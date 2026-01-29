"""Jobber client for accessing Jobber data via GraphQL API."""

import os
import time
from typing import Optional, List, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from flo.exceptions import (
    AuthenticationError,
    APIError,
    JobberError,
    DataSourceNotFoundError,
)
from flo.jobber.models import JobberUser, JobberClient, JobberJob, JobberExpense


# GraphQL Query Strings (converted from backend jobber.graphql.ts)
JOBBER_USERS_QUERY = """
query jobberUsers($after: String) {
    users(first: 200, after: $after) {
        nodes {
            id
            name {
                first
                last
            }
            email {
                raw
            }
            phone {
                raw
            }
            status
            isAccountAdmin
            isAccountOwner
        }
        pageInfo {
            hasNextPage
            endCursor
        }
    }
}
"""

JOBBER_CLIENTS_QUERY = """
query jobberClients($after: String, $filter: ClientFilterAttributes) {
    clients(first: 100, after: $after, filter: $filter) {
        nodes {
            id
            name
            emails {
                address
            }
            phones {
                number
            }
        }
        pageInfo {
            hasNextPage
            endCursor
        }
    }
}
"""

JOBBER_JOBS_QUERY = """
query jobberJobs($after: String, $filter: JobFilterAttributes) {
    jobs(first: 50, after: $after, filter: $filter) {
        nodes {
            id
            jobNumber
            title
            instructions
            jobStatus
            total
            createdAt
            startAt
            endAt
            client {
                id
            }
            visits(first: 3) {
                nodes {
                    assignedUsers(first: 10) {
                        nodes {
                            id
                        }
                    }
                }
            }
        }
        pageInfo {
            hasNextPage
            endCursor
        }
    }
}
"""

JOBBER_CLIENT_SUB_QUERY = """
query jobberClient($id: EncodedId!) {
    client(id: $id) {
        id
        name
        emails {
            address
        }
        phones {
            number
        }
    }
}
"""

JOBBER_EXPENSES_QUERY = """
query jobberTrx($after: String) {
    expenses(first: 200, after: $after) {
        nodes {
            id
            title
            total
            description
            date
            linkedJob {
                id
            }
        }
        pageInfo {
            hasNextPage
            endCursor
        }
    }
}
"""

JOBBER_EXPENSE_BY_ID_QUERY = """
query getExpense($id: EncodedId!) {
    expense(id: $id) {
        id
        linkedJob {
            id
        }
    }
}
"""

JOBBER_EXPENSE_CREATE_MUTATION = """
mutation PushJobberExpense($input: ExpenseCreateInput!) {
    expenseCreate(input: $input) {
        expense {
            id
        }
        userErrors {
            message
        }
    }
}
"""

JOBBER_EXPENSE_UPDATE_MUTATION = """
mutation UpdateJobberExpense($id: EncodedId!, $input: ExpenseEditInput!) {
    expenseEdit(expenseId: $id, input: $input) {
        expense {
            id
        }
        userErrors {
            message
        }
    }
}
"""

JOBBER_EXPENSE_DELETE_MUTATION = """
mutation DeleteJobberExpense($id: EncodedId!) {
    expenseDelete(expenseId: $id) {
        deletedExpense {
            id
        }
        userErrors {
            message
        }
    }
}
"""


class JobberClient:
    """
    Client for accessing Jobber data via GraphQL API.
    
    Credentials are automatically loaded from the global __data_sources__ dictionary
    that is injected by the Clyr backend into every agent execution.
    """
    
    BASE_URL = "https://api.getjobber.com/api/graphql"
    GRAPHQL_VERSION = "2025-01-20"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        tenant_id: Optional[str] = None,
        data_source_id: Optional[str] = None,
    ):
        """
        Initialize Jobber client.
        
        If no parameters are provided, credentials are automatically loaded from
        the global __data_sources__ dictionary injected by the backend.
        
        Args:
            access_token: Jobber access token (optional, auto-loaded if not provided)
            tenant_id: Tenant ID (optional, auto-loaded if not provided)
            data_source_id: Data source ID (optional, auto-loaded if not provided)
        """
        # Get credentials from parameters or global __data_sources__
        if access_token and tenant_id and data_source_id:
            self.access_token = access_token
            self.refresh_token = None  # Manual init doesn't provide refresh_token
            self.tenant_id = tenant_id
            self.data_source_id = data_source_id
        else:
            # Try to load from global __data_sources__ (injected by backend)
            try:
                # Check if __data_sources__ is available (injected by backend)
                # The backend injects this as a global variable in the agent execution context
                # Use the same pattern as QuickBooksClient
                import builtins
                data_sources = getattr(builtins, "__data_sources__", {})
                
                # Fallback to globals() if not in builtins
                if not data_sources:
                    data_sources = globals().get("__data_sources__", {})
                
                if not data_sources:
                    raise DataSourceNotFoundError(
                        "__data_sources__ is empty. This means the backend did not inject "
                        "any data sources. Check backend logs for 'Loaded data sources for team' "
                        "or verify that your team has connected data sources."
                    )
                
                # Look for Jobber data source
                # Backend uses platform name as the key in __data_sources__
                # The key is: ds.platform || ds.parentPlatform (both are "jobber" for Jobber)
                jobber_source = None
                
                # First try direct key lookup (backend uses platform name as key)
                if "jobber" in data_sources:
                    jobber_source = data_sources["jobber"]
                else:
                    # Fallback: search by platform/parent_platform values
                    # Also check if any key matches "jobber" (case-insensitive)
                    for key, source in data_sources.items():
                        key_lower = key.lower()
                        platform = source.get("platform", "").lower()
                        parent_platform = source.get("parent_platform", "").lower()
                        if (key_lower == "jobber" or 
                            platform == "jobber" or 
                            parent_platform == "jobber"):
                            jobber_source = source
                            break
                
                if not jobber_source:
                    # Provide helpful error message with available data sources
                    available_keys = list(data_sources.keys())
                    available_platforms = [
                        f"{k}: platform={v.get('platform')}, parent_platform={v.get('parent_platform')}"
                        for k, v in data_sources.items()
                    ]
                    raise DataSourceNotFoundError(
                        f"Jobber data source not found in __data_sources__. "
                        f"Available keys: {available_keys}. "
                        f"Available platforms: {available_platforms}. "
                        "Make sure your team has connected Jobber."
                    )
                
                keys = jobber_source.get("keys", {})
                self.access_token = keys.get("access_token")
                self.refresh_token = keys.get("refresh_token")  # Load refresh_token for token refresh
                self.tenant_id = jobber_source.get("tenant_id")
                self.data_source_id = jobber_source.get("id")
                
                # Debug: log what we found (remove in production if needed)
                if not self.access_token:
                    raise AuthenticationError(
                        f"No access token found in Jobber data source. "
                        f"Available keys in source: {list(jobber_source.keys())}"
                    )
                if not self.tenant_id:
                    raise AuthenticationError("No tenant_id found in data source")
                if not self.data_source_id:
                    raise AuthenticationError("No data_source_id found in data source")
                    
            except NameError:
                raise DataSourceNotFoundError(
                    "__data_sources__ not found. This client must be used within "
                    "a Clyr agent execution context, or credentials must be provided manually."
                )
        
        # Create requests session
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "X-JOBBER-GRAPHQL-VERSION": self.GRAPHQL_VERSION,
        })
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.session.close()
    
    def _refresh_token(self) -> str:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            New access token
            
        Raises:
            AuthenticationError: If refresh fails
        """
        if not self.refresh_token:
            raise AuthenticationError("No refresh token available to refresh access token")
        
        import os
        client_id = os.getenv("JOBBER_CLIENT_ID")
        client_secret = os.getenv("JOBBER_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise AuthenticationError(
                "JOBBER_CLIENT_ID and JOBBER_CLIENT_SECRET must be set for token refresh"
            )
        
        try:
            response = requests.post(
                "https://api.getjobber.com/api/oauth/token",
                params={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                },
                timeout=30,
            )
            
            if not response.ok:
                raise AuthenticationError(
                    f"Failed to refresh token: {response.text}"
                )
            
            data = response.json()
            new_access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token")
            
            if not new_access_token:
                raise AuthenticationError("No access token in refresh response")
            
            # Update tokens
            self.access_token = new_access_token
            if new_refresh_token:
                self.refresh_token = new_refresh_token
            
            # Update session headers
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}",
            })
            
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            raise AuthenticationError(f"Token refresh request failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _graphql_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a GraphQL request to Jobber API.
        
        Args:
            query: GraphQL query/mutation string
            variables: GraphQL variables dict
            
        Returns:
            Response JSON as dict
            
        Raises:
            APIError: If the request fails
            AuthenticationError: If authentication fails
        """
        if variables is None:
            variables = {}
        
        payload = {
            "query": query,
            "variables": variables,
        }
        
        try:
            response = self.session.post(
                self.BASE_URL,
                json=payload,
                timeout=30,
            )
            
            # Handle authentication errors
            if response.status_code == 401:
                # Try to refresh token and retry once
                try:
                    self._refresh_token()
                    # Retry the request with new token
                    response = self.session.post(
                        self.BASE_URL,
                        json=payload,
                        timeout=30,
                    )
                    
                    if response.status_code == 401:
                        raise AuthenticationError(
                            f"Authentication failed after token refresh: {response.text}. "
                            "Token may have expired. Please reconnect Jobber."
                        )
                except AuthenticationError:
                    # Re-raise if refresh failed
                    raise
                except Exception as e:
                    raise AuthenticationError(
                        f"Authentication failed and token refresh error: {str(e)}"
                    )
            
            # Handle other errors
            if not response.ok:
                raise APIError(
                    f"API request failed: {response.text}",
                    status_code=response.status_code,
                    response=response.json() if response.content else None,
                )
            
            result = response.json()
            
            # Check for GraphQL errors
            if "errors" in result:
                error_messages = [e.get("message", "Unknown error") for e in result["errors"]]
                raise APIError(f"GraphQL errors: {', '.join(error_messages)}")
            
            return result.get("data", {})
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    def _paginate_graphql(
        self,
        key: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        rate_limit_ms: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Paginate through GraphQL results using cursor-based pagination.
        
        Matches backend pageJobber pattern exactly.
        
        Args:
            key: Key in response containing the paginated data (e.g., "users", "clients")
            query: GraphQL query string
            variables: Initial GraphQL variables (will have "after" added)
            rate_limit_ms: Milliseconds to wait between pages (0 = no rate limit)
            
        Returns:
            List of all items from all pages
        """
        if variables is None:
            variables = {}
        
        accumulator = []
        after = None
        
        while True:
            # Add cursor to variables
            page_variables = {**variables, "after": after}
            
            # Make request
            result = self._graphql_request(query, page_variables)
            
            # Extract items from this page
            page_data = result.get(key, {})
            items = page_data.get("nodes", [])
            accumulator.extend(items)
            
            # Check if there are more pages
            page_info = page_data.get("pageInfo", {})
            has_next_page = page_info.get("hasNextPage", False)
            
            if not has_next_page:
                break
            
            # Get cursor for next page
            after = page_info.get("endCursor")
            
            # Rate limiting
            if rate_limit_ms > 0:
                time.sleep(rate_limit_ms / 1000.0)
        
        return accumulator
    
    # User methods
    
    def get_users(self) -> List[JobberUser]:
        """
        Get all users from Jobber.
        
        Returns:
            List of JobberUser objects
        """
        try:
            users_data = self._paginate_graphql(
                "users",
                JOBBER_USERS_QUERY,
            )
            return [JobberUser.from_jobber(u) for u in users_data]
        except Exception as e:
            raise JobberError(f"Failed to get users: {str(e)}") from e
    
    # Client methods
    
    def get_clients(self, extra_ids: Optional[List[str]] = None) -> List[JobberClient]:
        """
        Get clients from Jobber.
        
        Fetches clients created in the last 3 months, plus any additional
        clients specified by ID.
        
        Args:
            extra_ids: Optional list of client IDs to fetch even if not in recent filter
            
        Returns:
            List of JobberClient objects
        """
        if extra_ids is None:
            extra_ids = []
        
        try:
            # Calculate 3 months ago date
            from datetime import datetime, timedelta
            three_months_ago = datetime.now() - timedelta(days=90)
            filter_date = three_months_ago.strftime("%Y-%m-%d")
            
            # Fetch recent clients
            clients_data = self._paginate_graphql(
                "clients",
                JOBBER_CLIENTS_QUERY,
                variables={"filter": {"createdAt": {"after": filter_date}}},
            )
            
            # Fetch any missing clients by ID
            missing_ids = [
                client_id for client_id in extra_ids
                if not any(c.get("id") == client_id for c in clients_data)
            ]
            
            for client_id in missing_ids:
                try:
                    result = self._graphql_request(
                        JOBBER_CLIENT_SUB_QUERY,
                        {"id": client_id},
                    )
                    client_data = result.get("client")
                    if client_data:
                        clients_data.append(client_data)
                except Exception:
                    # Log warning but continue (matching backend pattern)
                    pass
            
            return [JobberClient.from_jobber(c) for c in clients_data]
        except Exception as e:
            raise JobberError(f"Failed to get clients: {str(e)}") from e
    
    # Job methods
    
    def get_jobs(self) -> List[JobberJob]:
        """
        Get jobs from Jobber.
        
        Fetches jobs and filters to those with startAt within the last 3 months.
        Uses 1000ms rate limit between pages.
        
        Returns:
            List of JobberJob objects
        """
        try:
            # Fetch all jobs with rate limiting
            jobs_data = self._paginate_graphql(
                "jobs",
                JOBBER_JOBS_QUERY,
                rate_limit_ms=1000,
            )
            
            # Filter jobs by date (3 months)
            from datetime import datetime, timedelta
            three_months_ago = datetime.now() - timedelta(days=90)
            
            filtered_jobs = []
            for job in jobs_data:
                start_at = job.get("startAt")
                if not start_at:
                    # Include jobs without startAt
                    filtered_jobs.append(job)
                else:
                    try:
                        start_date = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                        if start_date > three_months_ago:
                            filtered_jobs.append(job)
                    except Exception:
                        # If date parsing fails, include the job
                        filtered_jobs.append(job)
            
            return [JobberJob.from_jobber(j) for j in filtered_jobs]
        except Exception as e:
            raise JobberError(f"Failed to get jobs: {str(e)}") from e
    
    # Expense methods
    
    def get_expenses(self) -> List[JobberExpense]:
        """
        Get all expenses from Jobber.
        
        Returns:
            List of JobberExpense objects
        """
        try:
            expenses_data = self._paginate_graphql(
                "expenses",
                JOBBER_EXPENSES_QUERY,
            )
            # Temporary debug: print first expense to see what fields are returned
            if expenses_data:
                print(f"DEBUG: First expense raw data: {expenses_data[0]}")
            return [JobberExpense.from_jobber(e) for e in expenses_data]
        except Exception as e:
            raise JobberError(f"Failed to get expenses: {str(e)}") from e
    
    def get_expense(self, expense_id: str) -> Optional[JobberExpense]:
        """
        Get a single expense by ID.
        
        Args:
            expense_id: Expense ID
            
        Returns:
            JobberExpense object or None if not found
        """
        try:
            result = self._graphql_request(
                JOBBER_EXPENSE_BY_ID_QUERY,
                {"id": expense_id},
            )
            expense_data = result.get("expense")
            if not expense_data or not expense_data.get("id"):
                return None
            return JobberExpense.from_jobber(expense_data)
        except Exception as e:
            raise JobberError(f"Failed to get expense: {str(e)}") from e
    
    def create_expense(
        self,
        title: str,
        total: float,
        date: str,
        description: Optional[str] = None,
        linked_job_id: Optional[str] = None,
        receipt_url: Optional[str] = None,
        reimbursable_to_id: Optional[str] = None,
        accounting_code_id: Optional[str] = None,
    ) -> str:
        """
        Create a new expense in Jobber.
        
        Args:
            title: Expense title
            total: Expense total amount
            date: Expense date (ISO format string)
            description: Optional description
            linked_job_id: Optional linked job ID
            receipt_url: Optional receipt URL
            reimbursable_to_id: Optional reimbursable to user ID
            accounting_code_id: Optional accounting code ID
            
        Returns:
            Created expense ID
            
        Raises:
            JobberError: If creation fails or userErrors are returned
        """
        try:
            input_data = {
                "title": title,
                "total": total,
                "date": date,
            }
            
            if description:
                input_data["description"] = description
            if linked_job_id:
                input_data["linkedJobId"] = linked_job_id
            if receipt_url:
                input_data["receiptUrl"] = receipt_url
            if reimbursable_to_id:
                input_data["reimbursableToId"] = reimbursable_to_id
            if accounting_code_id:
                input_data["accountingCodeId"] = accounting_code_id
            
            result = self._graphql_request(
                JOBBER_EXPENSE_CREATE_MUTATION,
                {"input": input_data},
            )
            
            expense_create = result.get("expenseCreate", {})
            
            # Check for userErrors
            user_errors = expense_create.get("userErrors", [])
            if user_errors:
                error_messages = [e.get("message", "Unknown error") for e in user_errors]
                raise JobberError(f"Failed to create expense: {', '.join(error_messages)}")
            
            expense = expense_create.get("expense", {})
            expense_id = expense.get("id")
            if not expense_id:
                raise JobberError("Expense creation succeeded but no ID returned")
            
            return expense_id
            
        except JobberError:
            raise
        except Exception as e:
            raise JobberError(f"Failed to create expense: {str(e)}") from e
    
    def update_expense(
        self,
        expense_id: str,
        title: Optional[str] = None,
        total: Optional[float] = None,
        date: Optional[str] = None,
        description: Optional[str] = None,
        linked_job_id: Optional[str] = None,
        receipt_url: Optional[str] = None,
        reimbursable_to_id: Optional[str] = None,
        accounting_code_id: Optional[str] = None,
    ) -> str:
        """
        Update an existing expense in Jobber.
        
        Args:
            expense_id: Expense ID to update
            title: Optional expense title
            total: Optional expense total amount
            date: Optional expense date (ISO format string)
            description: Optional description
            linked_job_id: Optional linked job ID
            receipt_url: Optional receipt URL
            reimbursable_to_id: Optional reimbursable to user ID
            accounting_code_id: Optional accounting code ID
            
        Returns:
            Updated expense ID
            
        Raises:
            JobberError: If update fails or userErrors are returned
        """
        try:
            input_data = {}
            
            if title is not None:
                input_data["title"] = title
            if total is not None:
                input_data["total"] = total
            if date is not None:
                input_data["date"] = date
            if description is not None:
                input_data["description"] = description
            if linked_job_id is not None:
                input_data["linkedJobId"] = linked_job_id
            if receipt_url is not None:
                input_data["receiptUrl"] = receipt_url
            if reimbursable_to_id is not None:
                input_data["reimbursableToId"] = reimbursable_to_id
            if accounting_code_id is not None:
                input_data["accountingCodeId"] = accounting_code_id
            
            result = self._graphql_request(
                JOBBER_EXPENSE_UPDATE_MUTATION,
                {"id": expense_id, "input": input_data},
            )
            
            expense_edit = result.get("expenseEdit", {})
            
            # Check for userErrors
            user_errors = expense_edit.get("userErrors", [])
            if user_errors:
                error_messages = [e.get("message", "Unknown error") for e in user_errors]
                raise JobberError(f"Failed to update expense: {', '.join(error_messages)}")
            
            expense = expense_edit.get("expense", {})
            return expense.get("id", expense_id)
            
        except JobberError:
            raise
        except Exception as e:
            raise JobberError(f"Failed to update expense: {str(e)}") from e
    
    def delete_expense(self, expense_id: str) -> None:
        """
        Delete an expense in Jobber.
        
        Gracefully handles "Expense does not exist" error (matching backend pattern).
        
        Args:
            expense_id: Expense ID to delete
            
        Raises:
            JobberError: If deletion fails (except for "Expense does not exist")
        """
        try:
            result = self._graphql_request(
                JOBBER_EXPENSE_DELETE_MUTATION,
                {"id": expense_id},
            )
            
            expense_delete = result.get("expenseDelete", {})
            
            # Check for userErrors
            user_errors = expense_delete.get("userErrors", [])
            if user_errors:
                # Check if error is "Expense does not exist" - handle gracefully
                error_messages = [e.get("message", "") for e in user_errors]
                if any("does not exist" in msg.lower() or "not exist" in msg.lower() for msg in error_messages):
                    # Expense already deleted - this is fine (matching backend pattern)
                    return
                
                # Other errors should be raised
                raise JobberError(f"Failed to delete expense: {', '.join(error_messages)}")
            
        except JobberError:
            raise
        except Exception as e:
            # Check if error message indicates expense doesn't exist
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "not exist" in error_msg:
                # Expense already deleted - this is fine
                return
            raise JobberError(f"Failed to delete expense: {str(e)}") from e

