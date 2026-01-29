"""
Escalation Service
===================

Handles escalation of conversations for human review.
Follows Single Responsibility Principle (SRP).
"""

import logging
from typing import Dict, Optional
from ..domain.interfaces import IAPIClient

logger = logging.getLogger(__name__)


class EscalationService:
    """
    Escalates conversations for human review via Orca API.
    
    Responsibilities:
    - Validate escalation data
    - Format escalation payloads
    - Send escalation requests to API
    """
    
    def __init__(self, api_client: IAPIClient):
        """
        Initialize escalation service.
        
        Args:
            api_client: HTTP client for API communication
        """
        self._api_client = api_client
        logger.debug("EscalationService initialized")
    
    def escalate(
        self,
        thread_id: str,
        api_base_url: str,
        action: str,
        headers: Dict[str, str],
        # summary: Optional[str] = None,  # Deactivated for now
        reason: Optional[str] = None
    ) -> bool:
        """
        Escalate a conversation for human review.
        
        Args:
            thread_id: Conversation thread identifier
            api_base_url: API base URL
            action: Escalation action type (e.g., "human_handoff")
            headers: Request headers (tenant info, etc.)
            # summary: Optional AI-generated summary of the situation  # Deactivated for now
            reason: Optional categorization/reason for escalation
            
        Returns:
            True if escalation succeeded, False otherwise
        """
        # Validate required inputs
        if not thread_id:
            logger.warning('⚠️ No thread_id provided. Escalation skipped.')
            return False
        
        if not action:
            logger.warning('⚠️ No action provided. Escalation skipped.')
            return False
        
        # Build endpoint
        endpoint = f"{api_base_url}/api/internal/v1/conversations/{thread_id}/escalate"
        
        # Build payload
        payload = self._build_payload(action, reason)
        
        # Log escalation info
        self._log_escalation_info(endpoint, thread_id, action, reason)
        
        # Send to API
        try:
            response = self._api_client.post(endpoint, payload, headers=headers)
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info('🚨 Escalation sent successfully')
                logger.info(f'   Response Status: {response.status_code}')
                return True
            else:
                logger.error(f'❌ Escalation failed with status {response.status_code}')
                logger.error(f'   Response: {response.text}')
                return False
            
        except Exception as error:
            # Non-blocking - log but don't fail the request
            logger.error(f'❌ Escalation request failed: {error}')
            return False
    
    def _build_payload(
        self,
        action: str,
        # summary: Optional[str],  # Deactivated for now
        reason: Optional[str]
    ) -> Dict[str, str]:
        """
        Build escalation payload.
        
        Args:
            action: Escalation action type
            # summary: Optional summary  # Deactivated for now
            reason: Optional reason
            
        Returns:
            Payload dictionary
        """
        payload = {
            'action': str(action)
        }
        
        # Deactivated for now
        # if summary is not None:
        #     payload['summary'] = str(summary)
        
        if reason is not None:
            payload['reason'] = str(reason)
        
        return payload
    
    def _log_escalation_info(
        self,
        endpoint: str,
        thread_id: str,
        action: str,
        # summary: Optional[str],  # Deactivated for now
        reason: Optional[str]
    ) -> None:
        """
        Log escalation information.
        
        Args:
            endpoint: API endpoint
            thread_id: Thread identifier
            action: Escalation action
            # summary: Optional summary  # Deactivated for now
            reason: Optional reason
        """
        logger.info('🚨 Sending escalation to Orca API...')
        logger.info(f'   Endpoint: {endpoint}')
        logger.info(f'   Thread ID: {thread_id}')
        logger.info(f'   Action: {action}')
        
        if reason:
            logger.info(f'   Reason: {reason}')
        # Deactivated for now
        # if summary:
        #     logger.info(f'   Summary: {summary[:100]}...' if len(summary) > 100 else f'   Summary: {summary}')
