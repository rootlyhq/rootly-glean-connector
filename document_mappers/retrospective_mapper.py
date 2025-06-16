"""
Retrospective document mapper for converting Rootly retrospectives to Glean documents
"""

import logging
from typing import Dict, Optional
from glean.api_client import models
from .base import BaseDocumentMapper

logger = logging.getLogger(__name__)


def retrospective_to_doc(retrospective: Dict) -> Optional[models.DocumentDefinition]:
    """
    Convert Rootly retrospective to Glean document
    
    Args:
        retrospective: Retrospective data from Rootly API
        
    Returns:
        DocumentDefinition object or None if conversion fails
    """
    mapper = RetrospectiveDocumentMapper()
    return mapper.convert(retrospective)


class RetrospectiveDocumentMapper(BaseDocumentMapper):
    """Maps Rootly retrospectives to Glean documents"""
    
    def convert(self, retrospective: Dict) -> Optional[models.DocumentDefinition]:
        """Convert retrospective to Glean document"""
        try:
            attributes = retrospective.get("attributes")
            if not attributes:
                logger.error(f"Retrospective ID {retrospective.get('id', 'Unknown')} missing attributes")
                return None
            
            # Get incident info for title context
            incident_data = retrospective.get("relationships", {}).get("incident", {}).get("data", {})
            incident_id = incident_data.get("id", "Unknown")
            
            # Create base document
            title = f"Retrospective: {attributes.get('title', f'Incident {incident_id}')}"
            doc_fields = self._create_base_document(
                item_id=retrospective["id"],
                object_type="Retrospective",
                title=title,
                view_url=attributes.get("url")
            )
            
            # Add retrospective-specific fields
            self._add_status_and_tags(doc_fields, attributes)
            self._add_incident_context(doc_fields, retrospective)
            self._add_content(doc_fields, attributes)
            self._add_author(doc_fields, attributes)
            
            # Add timestamps
            doc_fields.update(self._extract_timestamps(attributes))
            
            logger.debug(f"Converted retrospective {retrospective['id']} to document")
            return models.DocumentDefinition(**doc_fields)
            
        except Exception as e:
            logger.error(f"Error converting retrospective {retrospective.get('id', 'Unknown')}: {e}", exc_info=True)
            return None
    
    def _add_status_and_tags(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add status and initialize tags"""
        if status := attributes.get('status'):
            doc_fields["status"] = status
            doc_fields.setdefault("tags", []).append(f"status:{status}")
        
        # Add retrospective-specific tags
        doc_fields.setdefault("tags", []).append("type:retrospective")
    
    def _add_incident_context(self, doc_fields: Dict, retrospective: Dict) -> None:
        """Add incident context tags"""
        incident_data = retrospective.get("relationships", {}).get("incident", {}).get("data", {})
        if incident_id := incident_data.get("id"):
            doc_fields.setdefault("tags", []).append(f"incident:{incident_id}")
    
    def _add_content(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add body content with retrospective details"""
        content_parts = []
        content_parts.append(f"Title: {attributes.get('title', 'No Title')}")
        
        if status := attributes.get('status'):
            content_parts.append(f"Status: {status}")
        
        # Add summary if exists
        if summary := attributes.get("summary"):
            content_parts.append(f"\\nSummary:\\n{summary}")
            doc_fields["summary"] = self._build_content_field(summary)
        
        # Add what went well section
        if what_went_well := attributes.get("what_went_well"):
            content_parts.append(f"\\n--- What Went Well ---\\n{what_went_well}")
        
        # Add what could be improved section
        if what_could_be_improved := attributes.get("what_could_be_improved"):
            content_parts.append(f"\\n--- What Could Be Improved ---\\n{what_could_be_improved}")
        
        # Add action items section
        if action_items := attributes.get("action_items"):
            content_parts.append(f"\\n--- Action Items ---\\n{action_items}")
        
        # Add lessons learned section
        if lessons_learned := attributes.get("lessons_learned"):
            content_parts.append(f"\\n--- Lessons Learned ---\\n{lessons_learned}")
        
        # Add additional notes if exists
        if notes := attributes.get("notes"):
            content_parts.append(f"\\n--- Additional Notes ---\\n{notes}")
        
        # Set body content
        doc_fields["body"] = self._build_content_field("\\n".join(content_parts))
    
    def _add_author(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add author information"""
        if author := self._extract_author(attributes):
            doc_fields["author"] = author