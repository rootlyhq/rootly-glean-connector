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
            attributes = alert.get("attributes")
            if not attributes:
                logger.error(f"Alert ID {alert.get('id', 'Unknown')} missing attributes")
                return None
            
            # Create base document
            title = f"[ALERT] {attributes.get('title', attributes.get('name', 'No Title'))}"
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
            self._add_alert_content(doc_fields, attributes)
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
    
    def _add_alert_content(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add alert body content"""
        content_parts = []
        content_parts.append(f"Title: {attributes.get('title', attributes.get('name', 'No Title'))}")
        
        if status := attributes.get('status'):
            content_parts.append(f"Status: {status}")
        
        if priority := attributes.get('priority'):
            content_parts.append(f"Priority: {priority}")
        
        if source := attributes.get('source'):
            content_parts.append(f"Source: {source}")
        
        # Add description/message if exists
        if description := attributes.get("description", attributes.get("message")):
            content_parts.append(f"\\nDescription:\\n{description}")
            doc_fields["summary"] = self._build_content_field(description)
        
        # Add details if they exist
        if details := attributes.get("details"):
            content_parts.append(f"\\nDetails:\\n{details}")
        
        # Set body content
        doc_fields["body"] = self._build_content_field("\\n".join(content_parts))
    
    def _add_author(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add author information"""
        if author := self._extract_author(attributes):
            doc_fields["author"] = author