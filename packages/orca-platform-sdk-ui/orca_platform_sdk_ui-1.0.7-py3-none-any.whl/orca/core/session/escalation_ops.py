"""
Escalation Operations
=====================

Handles escalation operations for a session.
Ultra-focused: ONLY escalation to human review.
"""

import logging
import os
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class EscalationOperations:
    """
    Manages conversation escalation to human review.
    
    Ultra-focused on escalation only.
    Single Responsibility: Escalation handling.
    """
    
    def __init__(self, handler, data):
        """
        Initialize escalation operations.
        
        Args:
            handler: Parent handler (for accessing escalation service)
            data: Request data
        """
        self._handler = handler
        self._data = data
    
    def escalate(
        self,
        action: str = "human_handoff",
        # summary: Optional[str] = None,  # Deactivated for now
        reason: Optional[str] = None
    ) -> bool:
        """
        Escalate conversation for human review.
        
        This flags the conversation in the database so that human agents
        can see it needs attention.
        
        Args:
            action: Escalation action type (default: "human_handoff")
                    Common values: "human_handoff", "supervisor_review", 
                    "quality_check", "technical_issue"
            # summary: Optional AI-generated summary of the situation  # Deactivated for now
            reason: Optional categorization/reason code
            
        Returns:
            True if escalation succeeded, False otherwise
            
        Example:
            session.escalation.escalate(
                action="human_handoff",
                # summary="Customer requesting refund for damaged item",  # Deactivated for now
                reason="refund_request"
            )
        """
        try:
            # Get thread_id from data
            thread_id = getattr(self._data, 'thread_id', None)
            if not thread_id:
                logger.warning('⚠️ No thread_id available. Escalation skipped.')
                return False
            
            # Extract API base URL
            api_base_url = self._extract_api_base_url()
            
            # Get headers
            headers = getattr(self._data, 'headers', {})
            
            # Call escalation service
            return self._handler._escalation_service.escalate(
                thread_id=thread_id,
                api_base_url=api_base_url,
                action=action,
                headers=headers,
                # summary=summary,  # Deactivated for now
                reason=reason
            )
            
        except Exception as error:
            logger.error(f'❌ Escalation failed: {error}')
            return False
    
    def _extract_api_base_url(self) -> str:
        """
        Extract API base URL from request data.
        
        Returns:
            API base URL string
        """
        if hasattr(self._data, 'url') and self._data.url:
            parsed = urlparse(self._data.url)
            return f"{parsed.scheme}://{parsed.netloc}"
        
        return os.environ.get('ORCA_API_BASE_URL', 'http://localhost')
