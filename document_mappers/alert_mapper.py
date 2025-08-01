"""
Alert document mapper for converting Rootly alerts to Glean documents
"""

import logging
from typing import Dict, Optional
from glean.api_client import models
from .base import BaseDocumentMapper

logger = logging.getLogger(__name__)


def alert_to_doc(alert: Dict) -> Optional[models.DocumentDefinition]:
    """
    Convert Rootly alert to Glean document
    
    Args:
        alert: Alert data from Rootly API
        
    Returns:
        DocumentDefinition object or None if conversion fails
    """
    mapper = AlertDocumentMapper()
    return mapper.convert(alert)


class AlertDocumentMapper(BaseDocumentMapper):
    """Maps Rootly alerts to Glean documents"""
    
    def convert(self, alert: Dict) -> Optional[models.DocumentDefinition]:
        """Convert alert to Glean document"""
        try:
            # Debug: Log the structure of the first alert to see what fields are available
            if not hasattr(self, '_logged_structure'):
                logger.info(f"Sample alert structure: {alert}")
                self._logged_structure = True
                
            attributes = alert.get("attributes")
            if not attributes:
                logger.error(f"Alert ID {alert.get('id', 'Unknown')} missing attributes")
                return None
                
            # Debug: Log attributes for first alert
            if not hasattr(self, '_logged_attributes'):
                logger.info(f"Sample alert attributes: {attributes}")
                self._logged_attributes = True
            
            # Create base document - try multiple possible title fields
            alert_title = (
                attributes.get('summary') or 
                attributes.get('title') or 
                attributes.get('name') or 
                (attributes.get('data', {}).get('title') if isinstance(attributes.get('data'), dict) else None) or
                (attributes.get('data', {}).get('summary') if isinstance(attributes.get('data'), dict) else None) or
                (attributes.get('description', '').strip()[:50] + '...' if attributes.get('description', '').strip() else None) or
                f"Alert {alert.get('id', 'Unknown')}"
            )
            title = f"[ALERT] {alert_title}"
            doc_fields = self._create_base_document(
                item_id=alert["id"],
                object_type="Alert",
                title=title,
                view_url=attributes.get("url")
            )
            
            # Add alert-specific fields
            self._add_alert_status(doc_fields, attributes)
            self._add_alert_priority(doc_fields, attributes)
            self._add_alert_source(doc_fields, attributes)
            self._add_alert_content(doc_fields, attributes, alert)
            self._add_author(doc_fields, attributes)
            
            # Add timestamps
            doc_fields.update(self._extract_timestamps(attributes))
            
            logger.debug(f"Converted alert {alert['id']} to document")
            return models.DocumentDefinition(**doc_fields)
            
        except Exception as e:
            logger.error(f"Error converting alert {alert.get('id', 'Unknown')}: {e}", exc_info=True)
            return None
    
    def _add_alert_status(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add alert status and tags"""
        if status := attributes.get('status'):
            doc_fields["status"] = status
            doc_fields.setdefault("tags", []).append(f"alert_status:{status}")
    
    def _add_alert_priority(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add alert priority information"""
        if priority := attributes.get('priority', attributes.get('severity')):
            doc_fields.setdefault("tags", []).append(f"priority:{priority}")
    
    def _add_alert_source(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add alert source information"""
        if source := attributes.get('source', attributes.get('source_type')):
            doc_fields.setdefault("tags", []).append(f"source:{source}")
    
    def _add_alert_content(self, doc_fields: Dict, attributes: Dict, alert: Dict) -> None:
        """Add alert body content with enhanced monitoring rules"""
        content_parts = []
        # Use multiple possible title fields for content
        alert_title = (
            attributes.get('summary') or 
            attributes.get('title') or 
            attributes.get('name') or 
            (attributes.get('data', {}).get('title') if isinstance(attributes.get('data'), dict) else None) or
            (attributes.get('data', {}).get('summary') if isinstance(attributes.get('data'), dict) else None) or
            (attributes.get('description', '').strip()[:50] + '...' if attributes.get('description', '').strip() else None) or
            f"Alert {alert.get('id', 'Unknown')}"
        )
        content_parts.append(f"Title: {alert_title}")
        
        if status := attributes.get('status'):
            content_parts.append(f"Status: {status}")
        
        if priority := attributes.get('priority'):
            content_parts.append(f"Priority: {priority}")
        
        if source := attributes.get('source'):
            content_parts.append(f"Source: {source}")
        
        # Add description/message if exists
        if description := attributes.get("description", attributes.get("message")):
            content_parts.append(f"\nDescription:\n{description}")
            doc_fields["summary"] = self._build_content_field(description)
        
        # Add details if they exist
        if details := attributes.get("details"):
            content_parts.append(f"\nDetails:\n{details}")
        
        # Add enhanced monitoring configuration data
        self._add_monitoring_rules_content(content_parts, alert)
        
        # Set body content
        doc_fields["body"] = self._build_content_field("\n".join(content_parts))
    
    def _add_monitoring_rules_content(self, content_parts: list, alert: Dict) -> None:
        """Add monitoring rules and configuration content"""
        monitoring_context = alert.get("monitoring_context", {})
        
        # Add alert routing rules
        if routing_rules := monitoring_context.get("routing_rules"):
            content_parts.append("\n## Alert Routing Rules")
            for rule in routing_rules[:3]:  # Limit to 3 rules for readability
                if rule_attrs := rule.get("attributes"):
                    rule_name = rule_attrs.get("name", "Unnamed Rule")
                    match_mode = rule_attrs.get("match_mode", "Unknown")
                    content_parts.append(f"- **{rule_name}** (Match: {match_mode})")
                    
                    # Add rule conditions if available
                    if conditions := rule_attrs.get("conditions"):
                        content_parts.append(f"  Conditions: {conditions}")
        
        # Add alert urgencies/priorities
        if urgencies := monitoring_context.get("urgencies"):
            content_parts.append("\n## Alert Urgency Levels")
            for urgency in urgencies:
                if urgency_attrs := urgency.get("attributes"):
                    urgency_name = urgency_attrs.get("name", "Unknown")
                    urgency_level = urgency_attrs.get("level", "Unknown")
                    content_parts.append(f"- **{urgency_name}**: Level {urgency_level}")
        
        # Add alert groups
        if alert_groups := monitoring_context.get("alert_groups"):
            content_parts.append("\n## Alert Groups")
            for group in alert_groups[:3]:  # Limit to 3 groups
                if group_attrs := group.get("attributes"):
                    group_name = group_attrs.get("name", "Unnamed Group")
                    group_desc = group_attrs.get("description", "No description")
                    content_parts.append(f"- **{group_name}**: {group_desc}")
        
        # Add recent alert events context
        if recent_events := monitoring_context.get("recent_events"):
            content_parts.append("\n## Recent Alert Activity")
            for event in recent_events[:3]:  # Limit to 3 recent events
                if event_attrs := event.get("attributes"):
                    event_type = event_attrs.get("event_type", "Unknown")
                    event_time = event_attrs.get("created_at", "Unknown time")
                    content_parts.append(f"- {event_type} at {event_time}")
    
    def _add_author(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add author information"""
        if author := self._extract_author(attributes):
            doc_fields["author"] = author