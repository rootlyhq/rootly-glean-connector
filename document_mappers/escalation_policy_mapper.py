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
            self._add_policy_content(doc_fields, attributes, policy)
            
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
    
    def _add_policy_content(self, doc_fields: Dict, attributes: Dict, policy: Dict) -> None:
        """Add escalation policy body content with detailed notification chains"""
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
            content_parts.append(f"\nEscalation Rules:\n{rules}")
        
        # Add detailed notification chain information
        self._add_notification_chain_content(content_parts, policy)
        
        # Set body content
        doc_fields["body"] = self._build_content_field("\n".join(content_parts))
    
    def _add_notification_chain_content(self, content_parts: list, policy: Dict) -> None:
        """Add detailed notification chain and escalation level content"""
        
        # Add escalation levels (detailed steps)
        if escalation_levels := policy.get("escalation_levels"):
            content_parts.append("\n## Escalation Levels")
            for i, level in enumerate(escalation_levels, 1):
                if level_attrs := level.get("attributes"):
                    level_name = level_attrs.get("name", f"Level {i}")
                    notification_type = level_attrs.get("notification_type", "Unknown")
                    timeout = level_attrs.get("timeout", "Unknown")
                    
                    content_parts.append(f"\n### {level_name}")
                    content_parts.append(f"- **Notification Type**: {notification_type}")
                    content_parts.append(f"- **Timeout**: {timeout} minutes")
                    
                    # Add level-specific details
                    if repeat_count := level_attrs.get("repeat_count"):
                        content_parts.append(f"- **Repeat Count**: {repeat_count}")
                    
                    if position := level_attrs.get("position"):
                        content_parts.append(f"- **Position**: {position}")
        
        # Add escalation paths (notification routing)
        if escalation_paths := policy.get("escalation_paths"):
            content_parts.append("\n## Escalation Paths")
            for path in escalation_paths:
                if path_attrs := path.get("attributes"):
                    path_name = path_attrs.get("name", "Unnamed Path")
                    path_type = path_attrs.get("path_type", "Unknown")
                    content_parts.append(f"- **{path_name}** ({path_type})")
                    
                    # Add path conditions if available
                    if conditions := path_attrs.get("conditions"):
                        content_parts.append(f"  Conditions: {conditions}")
                    
                    # Add path targets from relationships
                    if relationships := path.get("relationships"):
                        if targets := relationships.get("targets", {}).get("data", []):
                            target_names = [target.get("id", "Unknown") for target in targets]
                            content_parts.append(f"  Targets: {', '.join(target_names)}")
        
        # Add user notification rules
        if user_notification_rules := policy.get("user_notification_rules"):
            content_parts.append("\n## User Notification Rules")
            for rule in user_notification_rules[:5]:  # Limit to 5 rules
                if rule_attrs := rule.get("attributes"):
                    rule_name = rule_attrs.get("name", "Unnamed Rule")
                    notification_method = rule_attrs.get("notification_method", "Unknown")
                    content_parts.append(f"- **{rule_name}**: {notification_method}")
                    
                    # Add rule timing if available
                    if delay := rule_attrs.get("delay_minutes"):
                        content_parts.append(f"  Delay: {delay} minutes")
                    
                    # Add rule conditions
                    if conditions := rule_attrs.get("conditions"):
                        content_parts.append(f"  Conditions: {conditions}")