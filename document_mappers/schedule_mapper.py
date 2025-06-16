"""
Schedule document mapper for converting Rootly schedules to Glean documents
"""

import logging
from typing import Dict, Optional
from glean.api_client import models
from .base import BaseDocumentMapper

logger = logging.getLogger(__name__)


def schedule_to_doc(schedule: Dict) -> Optional[models.DocumentDefinition]:
    """
    Convert Rootly schedule to Glean document
    
    Args:
        schedule: Schedule data from Rootly API
        
    Returns:
        DocumentDefinition object or None if conversion fails
    """
    mapper = ScheduleDocumentMapper()
    return mapper.convert(schedule)


class ScheduleDocumentMapper(BaseDocumentMapper):
    """Maps Rootly schedules to Glean documents"""
    
    def convert(self, schedule: Dict) -> Optional[models.DocumentDefinition]:
        """Convert schedule to Glean document"""
        try:
            attributes = schedule.get("attributes")
            if not attributes:
                logger.error(f"Schedule ID {schedule.get('id', 'Unknown')} missing attributes")
                return None
            
            # Create base document
            title = f"[SCHEDULE] {attributes.get('name', 'No Name')}"
            doc_fields = self._create_base_document(
                item_id=schedule["id"],
                object_type="Schedule",
                title=title,
                view_url=attributes.get("url")
            )
            
            # Add schedule-specific fields
            self._add_schedule_type(doc_fields, attributes)
            self._add_schedule_status(doc_fields, attributes)
            self._add_team_info(doc_fields, attributes)
            self._add_schedule_content(doc_fields, attributes)
            
            # Add timestamps
            doc_fields.update(self._extract_timestamps(attributes))
            
            logger.debug(f"Converted schedule {schedule['id']} to document")
            return models.DocumentDefinition(**doc_fields)
            
        except Exception as e:
            logger.error(f"Error converting schedule {schedule.get('id', 'Unknown')}: {e}", exc_info=True)
            return None
    
    def _add_schedule_type(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add schedule type information"""
        if schedule_type := attributes.get('schedule_type', attributes.get('type')):
            doc_fields.setdefault("tags", []).append(f"schedule_type:{schedule_type}")
    
    def _add_schedule_status(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add schedule status"""
        if status := attributes.get('status'):
            doc_fields["status"] = status
            doc_fields.setdefault("tags", []).append(f"status:{status}")
    
    def _add_team_info(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add team/owner information"""
        if team := attributes.get('team'):
            doc_fields.setdefault("tags", []).append(f"team:{team}")
        
        if owner := attributes.get('owner'):
            doc_fields.setdefault("tags", []).append(f"owner:{owner}")
    
    def _add_schedule_content(self, doc_fields: Dict, attributes: Dict) -> None:
        """Add schedule body content"""
        content_parts = []
        content_parts.append(f"Name: {attributes.get('name', 'No Name')}")
        
        if description := attributes.get("description"):
            content_parts.append(f"Description: {description}")
            doc_fields["summary"] = self._build_content_field(description)
        
        if schedule_type := attributes.get('schedule_type'):
            content_parts.append(f"Type: {schedule_type}")
        
        if timezone := attributes.get('timezone'):
            content_parts.append(f"Timezone: {timezone}")
        
        # Add rotation info if available
        if rotation_info := attributes.get('rotation_info'):
            content_parts.append(f"\\nRotation Info:\\n{rotation_info}")
        
        # Set body content
        doc_fields["body"] = self._build_content_field("\\n".join(content_parts))