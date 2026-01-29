"""
Human Review Client for Flo Agents

Provides the ability for agents to request human review at checkpoints,
pause execution, and resume after receiving human input.

Example usage:

    from flo_integrations import request_human_review

    def process_invoices(inputs):
        # ... process invoices ...
        
        # Request human approval for high-value invoices
        result = request_human_review(
            checkpoint_id='approve_high_value_invoices',
            prompt='Please review and approve these high-value invoices',
            fields=[
                {
                    'type': 'multiselect',
                    'name': 'approved_invoice_ids',
                    'label': 'Select invoices to approve',
                    'required': True,
                    'options': [
                        {'label': 'Invoice #001 - $15,000', 'value': 'inv_001'},
                        {'label': 'Invoice #002 - $22,000', 'value': 'inv_002'},
                    ]
                },
                {
                    'type': 'textarea',
                    'name': 'notes',
                    'label': 'Approval notes (optional)',
                    'required': False,
                }
            ],
            context={'total_invoices': 10, 'high_value_count': 2},
            state={'all_invoices': invoices, 'progress': 'filtering_complete'}
        )
        
        # Agent resumes here after human approves
        approved_ids = result['response']['approved_invoice_ids']
        print(f"Human approved {len(approved_ids)} invoices")
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass


class ReviewFieldOption(TypedDict):
    """Option for select/multiselect/buttons fields."""
    label: str
    value: str


class ReviewField(TypedDict, total=False):
    """Field definition for review form.
    
    Supported types:
    - 'string': Single-line text input
    - 'number': Numeric input
    - 'boolean': Checkbox
    - 'select': Single select dropdown
    - 'date': Date picker
    - 'textarea': Multi-line text input
    - 'multiselect': Multi-select checkboxes
    - 'buttons': Button group selection
    """
    type: str  # 'string', 'number', 'boolean', 'select', 'textarea', 'multiselect', 'buttons'
    name: str
    label: str
    description: str
    required: bool
    options: List[ReviewFieldOption]
    defaultValue: Any


class ReviewResponse(TypedDict):
    """Response from human review."""
    decision: str  # 'approve', 'reject', or 'custom'
    response: Dict[str, Any]  # Field values entered by human
    notes: Optional[str]  # Optional reviewer notes
    checkpoint_state: Dict[str, Any]  # Restored checkpoint state


class HumanReviewPending(Exception):
    """Raised when agent is pausing for human review.
    
    This exception is raised internally and should not normally
    be caught by agent code. The agent will exit gracefully
    when a review is requested.
    """
    pass


@dataclass
class FloReviewClient:
    """Client for requesting human review during agent execution.
    
    This client handles the communication with the Flo backend API
    to create review requests and retrieve responses on resume.
    """
    
    base_url: str
    api_key: str
    run_id: str
    is_resume: bool
    current_checkpoint: Optional[str]

    @classmethod
    def from_env(cls) -> 'FloReviewClient':
        """Create client from environment variables.
        
        Required environment variables:
        - FLO_API_URL: Base URL of the Flo backend API
        - FLO_API_KEY: API key for authentication
        - FLO_RUN_ID: Current agent run ID
        
        Optional environment variables:
        - FLO_RESUME_MODE: Set to 'true' when resuming from checkpoint
        - FLO_CHECKPOINT_ID: ID of checkpoint being resumed from
        
        Raises:
            ValueError: If required environment variables are missing
        """
        base_url = os.getenv('FLO_API_URL')
        api_key = os.getenv('FLO_API_KEY')
        run_id = os.getenv('FLO_RUN_ID')
        is_resume = os.getenv('FLO_RESUME_MODE', '').lower() == 'true'
        current_checkpoint = os.getenv('FLO_CHECKPOINT_ID')

        if not all([base_url, api_key, run_id]):
            raise ValueError(
                "Missing required environment variables. "
                "Ensure FLO_API_URL, FLO_API_KEY, and FLO_RUN_ID are set."
            )

        return cls(
            base_url=base_url,  # type: ignore
            api_key=api_key,  # type: ignore
            run_id=run_id,  # type: ignore
            is_resume=is_resume,
            current_checkpoint=current_checkpoint,
        )

    def request_human_review(
        self,
        checkpoint_id: str,
        prompt: str,
        fields: List[ReviewField],
        context: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> ReviewResponse:
        """
        Request human review at a checkpoint.

        On first execution:
        - Creates review request in the Flo backend
        - Saves checkpoint state for later resume
        - Exits agent gracefully (sys.exit(0))

        On resume execution:
        - Returns the human's response immediately
        - Agent continues from checkpoint

        Args:
            checkpoint_id: Unique identifier for this checkpoint (e.g., "approve_invoices").
                          Must be unique within a single agent run.
            prompt: Question or instruction shown to the reviewer.
            fields: List of form fields for the reviewer to fill out.
                   Supported types: string, number, boolean, select, textarea,
                   multiselect, buttons.
            context: Additional data to display to the reviewer (read-only).
                    Useful for showing summary statistics or relevant info.
            state: Agent state to preserve for resume. Include any variables
                   or progress that needs to be restored when agent resumes.

        Returns:
            ReviewResponse with human's decision, field values, and saved state.
            Only returned when agent is resuming from this checkpoint.

        Note:
            On first execution, this function will NOT return. The agent
            will exit with code 0 (success) and resume later after
            the human submits their review.
        """
        # If we're resuming, check if this is the checkpoint we resumed from
        if self.is_resume:
            response = self._get_review_response(checkpoint_id)
            if response:
                print(f"[FLO] Loaded response for checkpoint: {checkpoint_id}")
                return response

        # First time hitting this checkpoint - create review request
        print(f"[FLO] Creating review request: {checkpoint_id}")
        self._create_review_request(
            checkpoint_id=checkpoint_id,
            prompt=prompt,
            fields=fields,
            context=context or {},
            state=state or {},
        )

        # Exit gracefully
        print(f"[FLO] Checkpoint saved: {checkpoint_id}")
        print(f"[FLO] Waiting for human review...")
        print(f"[FLO] Agent will resume automatically after review is submitted.")
        
        # Exit with code 0 (success) - the run status is updated by backend
        sys.exit(0)

    def _create_review_request(
        self,
        checkpoint_id: str,
        prompt: str,
        fields: List[ReviewField],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> None:
        """Create review request via internal API."""
        url = f"{self.base_url}/agent-api/runs/{self.run_id}/review"

        payload = {
            'checkpointId': checkpoint_id,
            'prompt': prompt,
            'fields': fields,
            'context': context,
            'state': state,
        }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            print(f"[FLO] Review request created: {result.get('reviewRequestId')}")
        except requests.RequestException as e:
            print(f"[FLO] Error creating review request: {e}")
            raise

    def _get_review_response(self, checkpoint_id: str) -> Optional[ReviewResponse]:
        """Get response for checkpoint from API."""
        url = f"{self.base_url}/agent-api/runs/{self.run_id}/checkpoints/{checkpoint_id}/response"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            return ReviewResponse(
                decision=data['decision'],
                response=data['response'],
                notes=data.get('notes'),
                checkpoint_state=data.get('checkpointState', {}),
            )
        except requests.RequestException as e:
            print(f"[FLO] Error getting review response: {e}")
            raise


# Global client instance (lazy-loaded)
_client: Optional[FloReviewClient] = None


def get_review_client() -> FloReviewClient:
    """Get or create the global review client.
    
    Creates a singleton FloReviewClient instance from environment variables.
    This is the recommended way to get a client for most use cases.
    
    Returns:
        FloReviewClient instance configured from environment.
        
    Raises:
        ValueError: If required environment variables are missing.
    """
    global _client
    if _client is None:
        _client = FloReviewClient.from_env()
    return _client


def request_human_review(
    checkpoint_id: str,
    prompt: str,
    fields: List[ReviewField],
    context: Optional[Dict[str, Any]] = None,
    state: Optional[Dict[str, Any]] = None,
) -> ReviewResponse:
    """
    Convenience function to request human review.
    
    This is the primary API for requesting human review in agent code.
    Uses a global client instance configured from environment variables.
    
    See FloReviewClient.request_human_review for full documentation.
    
    Example:
        from flo_integrations import request_human_review
        
        result = request_human_review(
            checkpoint_id='approve_payment',
            prompt='Approve this payment of $10,000?',
            fields=[
                {
                    'type': 'buttons',
                    'name': 'approved',
                    'label': 'Decision',
                    'required': True,
                    'options': [
                        {'label': 'Approve', 'value': 'yes'},
                        {'label': 'Reject', 'value': 'no'},
                    ]
                }
            ],
        )
        
        if result['response']['approved'] == 'yes':
            # Process the payment
            pass
    
    Args:
        checkpoint_id: Unique identifier for this checkpoint
        prompt: Question/instruction for the reviewer
        fields: Form fields for reviewer input
        context: Read-only context data to display
        state: Agent state to preserve for resume
        
    Returns:
        ReviewResponse with human's decision and field values
    """
    client = get_review_client()
    return client.request_human_review(
        checkpoint_id=checkpoint_id,
        prompt=prompt,
        fields=fields,
        context=context,
        state=state,
    )


# Export for package
__all__ = [
    'FloReviewClient',
    'ReviewField',
    'ReviewFieldOption',
    'ReviewResponse',
    'HumanReviewPending',
    'request_human_review',
    'get_review_client',
]

