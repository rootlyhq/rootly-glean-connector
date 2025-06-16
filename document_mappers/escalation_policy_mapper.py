"""
Escalation policy document mapper for converting Rootly escalation policies to Glean documents
"""

import logging
from typing import Dict, Optional
from glean.api_client import models
from .base import BaseDocumentMapper

logger = logging.getLogger(__name__)


def escalation_policy_to_doc(policy: Dict) -> Optional[models.DocumentDefinition]:
    """
    Convert Rootly escalation policy to Glean document
    
    Args:
        policy: Escalation policy data from Rootly API
        
    Returns:
        DocumentDefinition object or None if conversion fails
    """
    mapper = EscalationPolicyDocumentMapper()
    return mapper.convert(policy)


class EscalationPolicyDocumentMapper(BaseDocumentMapper):
    """Maps Rootly escalation policies to Glean documents"""
    
    def convert(self, policy: Dict) -> Optional[models.DocumentDefinition]:
        """Convert escalation policy to Glean document"""
        try:
            attributes = policy.get("attributes")
            if not attributes:
                logger.error(f"Escalation policy ID {policy.get('id', 'Unknown')} missing attributes")
                return None
            
            # Create base document
            title = f"[ESCALATION] {attributes.get('name', 'No Name')}"
            doc_fields = self._create_base_document(
                item_id=policy["id"],
                object_type="EscalationPolicy",
                title=title,
                view_url=attributes.get("url")
            )
            
            # Add escalation policy-specific fields
            self._add_policy_status(doc_fields, attributes)
            self._add_team_info(doc_fields, attributes)
            self._add_escalation_steps(doc_fields, attributes, policy)
            self._add_policy_content(doc_fields, attributes)
            
            # Add timestamps
            doc_fields.update(self._extract_timestamps(attributes))
            
            logger.debug(f"Converted escalation policy {policy['id']} to document")
            return models.DocumentDefinition(**doc_fields)
            
        except Exception as e:
            logger.error(f"Error converting escalation policy {policy.get('id', 'Unknown')}: {e}", exc_info=True)
            return None
    
    def _add_policy_status(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add policy status"""
        if status := attributes.get('status'):
            doc_fields["status"] = status
            doc_fields.setdefault("tags", []).append(f"status:{status}")
    
    def _add_team_info(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add team information"""
        if team := attributes.get('team'):
            doc_fields.setdefault("tags", []).append(f"team:{team}")
    
    def _add_escalation_steps(self, doc_fields: Dict, attributes: Dict, policy: Dict) -> None:
        """Add escalation steps information"""
        # Try to get escalation steps from relationships or attributes
        steps = []
        
        if relationships := policy.get('relationships', {}).get('escalation_steps', {}).get('data', []):
            for step in relationships:
                if step_id := step.get('id'):
                    steps.append(f"Step {step_id}")
        
        if steps:
            doc_fields.setdefault("tags", []).append(f"escalation_steps:{len(steps)}")
    
    def _add_policy_content(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add escalation policy body content"""
        content_parts = []
        content_parts.append(f"Name: {attributes.get('name', 'No Name')}")
        
        if description := attributes.get("description"):
            content_parts.append(f"Description: {description}")
            doc_fields["summary"] = self._build_content_field(description)
        
        if repeat_count := attributes.get('repeat_count'):
            content_parts.append(f"Repeat Count: {repeat_count}")
        
        if escalation_timeout := attributes.get('escalation_timeout'):
            content_parts.append(f"Escalation Timeout: {escalation_timeout} minutes")
        
        # Add escalation rules if available
        if rules := attributes.get('escalation_rules'):
            content_parts.append(f"\\nEscalation Rules:\\n{rules}")
        
        # Set body content
        doc_fields["body"] = self._build_content_field("\\n".join(content_parts))