"""
Human Review Client for Flo Agents

Provides the ability for agents to request human review at checkpoints,
pause execution, and resume after receiving human input.
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
    """Field definition for human review forms."""
    type: str  # 'string', 'number', 'boolean', 'select', 'textarea', 'multiselect', 'buttons'
    name: str
    label: str
    description: str
    required: bool
    options: List[ReviewFieldOption]
    defaultValue: Any


class ReviewResponse(TypedDict):
    """Response from human review."""
    decision: str
    response: Dict[str, Any]
    notes: Optional[str]
    checkpoint_state: Dict[str, Any]


class HumanReviewPending(Exception):
    """Raised when agent is pausing for human review."""
    pass


@dataclass
class FloReviewClient:
    """Client for requesting human review during agent execution."""
    
    base_url: str
    api_key: str
    run_id: str
    is_resume: bool
    current_checkpoint: Optional[str]

    @classmethod
    def from_env(cls) -> 'FloReviewClient':
        """Create client from environment variables."""
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
            base_url=base_url,
            api_key=api_key,
            run_id=run_id,
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
        - Creates review request
        - Saves checkpoint state
        - Exits agent gracefully (calls sys.exit(0))

        On resume execution:
        - Returns the human's response immediately

        Args:
            checkpoint_id: Unique identifier for this checkpoint (e.g., "approve_invoices")
            prompt: Question or instruction shown to the reviewer
            fields: List of form fields for the reviewer to fill out
            context: Additional data to display to the reviewer
            state: Agent state to preserve for resume (variables, progress, etc.)

        Returns:
            ReviewResponse with human's decision, field values, and saved state
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
    """Get or create the global review client."""
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
    
    See FloReviewClient.request_human_review for full documentation.
    
    Example:
        ```python
        from flo.review import request_human_review
        
        result = request_human_review(
            checkpoint_id='approve_invoices',
            prompt='Please review and approve these invoices',
            fields=[
                {
                    'type': 'multiselect',
                    'name': 'approved_ids',
                    'label': 'Select invoices to approve',
                    'required': True,
                    'options': [
                        {'label': 'Invoice #1 - $100', 'value': 'inv_1'},
                        {'label': 'Invoice #2 - $200', 'value': 'inv_2'},
                    ]
                },
                {
                    'type': 'textarea',
                    'name': 'notes',
                    'label': 'Notes (optional)',
                    'required': False,
                }
            ],
            context={'total_amount': 300},
            state={'pending_invoices': ['inv_1', 'inv_2']},
        )
        
        # Agent resumes here after human submits review
        approved_ids = result['response']['approved_ids']
        ```
    """
    client = get_review_client()
    return client.request_human_review(
        checkpoint_id=checkpoint_id,
        prompt=prompt,
        fields=fields,
        context=context,
        state=state,
    )

