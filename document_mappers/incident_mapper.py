"""
Incident document mapper for converting Rootly incidents to Glean documents
"""

import json
import logging
from typing import Dict, Optional, List
from glean.api_client import models
from .base import BaseDocumentMapper

logger = logging.getLogger(__name__)


def incident_to_doc(incident: Dict) -> Optional[models.DocumentDefinition]:
    """
    Convert Rootly incident to Glean document
    
    Args:
        incident: Incident data from Rootly API
        
    Returns:
        DocumentDefinition object or None if conversion fails
    """
    mapper = IncidentDocumentMapper()
    return mapper.convert(incident)


class IncidentDocumentMapper(BaseDocumentMapper):
    """Maps Rootly incidents to Glean documents"""
    
    def convert(self, incident: Dict) -> Optional[models.DocumentDefinition]:
        """Convert incident to Glean document"""
        try:
            attributes = incident.get("attributes")
            if not attributes:
                logger.error(f"Incident ID {incident.get('id', 'Unknown')} missing attributes")
                return None
            
            # Create base document
            title = f"[INC-{attributes.get('sequential_id', 'N/A')}] {attributes.get('title', 'No Title')}"
            doc_fields = self._create_base_document(
                item_id=incident["id"],
                object_type="Incident",
                title=title,
                view_url=attributes.get("url")
            )
            
            # Add incident-specific fields
            self._add_status_and_tags(doc_fields, attributes)
            self._add_severity_data(doc_fields, attributes)
            self._add_kind_tag(doc_fields, attributes)
            self._add_content(doc_fields, attributes, incident)
            self._add_author(doc_fields, attributes)
            
            # Add timestamps
            doc_fields.update(self._extract_timestamps(attributes))
            
            logger.debug(f"Converted incident {incident['id']} to document")
            return models.DocumentDefinition(**doc_fields)
            
        except Exception as e:
            logger.error(f"Error converting incident {incident.get('id', 'Unknown')}: {e}", exc_info=True)
            return None
    
    def _add_status_and_tags(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add status and initialize tags"""
        if status := attributes.get('status'):
            doc_fields["status"] = status
            doc_fields.setdefault("tags", []).append(f"status:{status}")
    
    def _add_severity_data(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add severity information and tags"""
        if severity := attributes.get('severity'):
            if isinstance(severity, dict) and (severity_data := severity.get('data', {}).get('attributes', {})):
                severity_name = severity_data.get('name')
                if severity_name and severity_name != "Unknown":
                    doc_fields.setdefault("tags", []).append(f"severity:{severity_name}")
    
    def _add_kind_tag(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add incident kind tag"""
        if kind := attributes.get('kind'):
            doc_fields.setdefault("tags", []).append(f"kind:{kind}")
    
    def _add_content(self, doc_fields: Dict, attributes: Dict, incident: Dict) -> None:
        """Add body content and summary with enhanced data"""
        content_parts = []
        content_parts.append(f"Title: {attributes.get('title', 'No Title')}")
        
        if status := attributes.get('status'):
            content_parts.append(f"Status: {status}")
        
        # Add summary if exists
        if summary_text := attributes.get("summary"):
            content_parts.append(f"\\nSummary:\\n{summary_text}")
            doc_fields["summary"] = self._build_content_field(summary_text)
        
        # Add enhanced incident events data
        self._add_events_content(content_parts, incident)
        
        # Add enhanced action items
        self._add_enhanced_action_items(content_parts, incident)
        
        # Add enhanced severity information
        self._add_enhanced_severity_content(content_parts, incident)
        
        # Set body content
        doc_fields["body"] = self._build_content_field("\\n".join(content_parts))
    
    def _add_events_content(self, content_parts: List[str], incident: Dict) -> None:
        """Add incident events (timeline) information to content"""
        enhanced_data = incident.get("_enhanced_data", {})
        events = enhanced_data.get("events", [])
        
        if events:
            content_parts.append("\\n--- Incident Events Timeline ---")
            for event in events[:10]:  # Limit to first 10 events
                attributes = event.get("attributes", {})
                timestamp = attributes.get("occurred_at", attributes.get("created_at", ""))
                event_text = attributes.get("event", "")
                visibility = attributes.get("visibility", "")
                
                if event_text:
                    vis_indicator = " (internal)" if visibility == "internal" else ""
                    content_parts.append(f"[{timestamp[:16]}] {event_text}{vis_indicator}")
    
    def _add_enhanced_action_items(self, content_parts: List[str], incident: Dict) -> None:
        """Add detailed action items to content"""
        enhanced_data = incident.get("_enhanced_data", {})
        action_items = enhanced_data.get("action_items", [])
        
        if action_items:
            content_parts.append("\\n--- Action Items ---")
            for item in action_items:
                attributes = item.get("attributes", {})
                title = attributes.get("title", f"Action Item {item.get('id', 'Unknown')}")
                status = attributes.get("status", "Unknown")
                assignee = attributes.get("assignee", {}).get("name", "Unassigned")
                due_date = attributes.get("due_date", "")
                
                content_parts.append(f"• {title}")
                content_parts.append(f"  Status: {status} | Assignee: {assignee}")
                if due_date:
                    content_parts.append(f"  Due: {due_date}")
        else:
            # Fall back to basic action items if enhanced data not available
            if action_items := incident.get('relationships', {}).get('action_items', {}).get('data', []):
                content_parts.append("\\nAction Items:")
                for item in action_items:
                    content_parts.append(f"- {item.get('id', 'Unknown Action Item')}")
    
    def _add_enhanced_severity_content(self, content_parts: List[str], incident: Dict) -> None:
        """Add enhanced severity information to content"""
        enhanced_data = incident.get("_enhanced_data", {})
        severity_details = enhanced_data.get("severity_details", {})
        
        if severity_details:
            sev_attributes = severity_details.get("attributes", {})
            sev_name = sev_attributes.get("name", "")
            sev_description = sev_attributes.get("description", "")
            sev_level = sev_attributes.get("level", "")
            
            if sev_description and sev_description != sev_name:
                content_parts.append(f"\\nSeverity Details:")
                content_parts.append(f"Level: {sev_name} ({sev_level})")
                content_parts.append(f"Description: {sev_description}")
    
    def _add_author(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add author information"""
        if author := self._extract_author(attributes):
            doc_fields["author"] = author