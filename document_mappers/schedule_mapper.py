"""
Schedule document mapper for converting Rootly schedules to Glean documents
"""

import logging
from typing import Dict, Optional, List
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
            self._add_schedule_content(doc_fields, attributes, schedule)
            
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
    
    def _add_schedule_content(self, doc_fields: Dict, attributes: Dict, schedule: Dict) -> None:
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
            content_parts.append(f"\nRotation Info:\n{rotation_info}")
        
        # Add enhanced on-call data
        self._add_oncall_data(content_parts, schedule)
        
        # Set body content
        doc_fields["body"] = self._build_content_field("\\n".join(content_parts))
    
    def _add_oncall_data(self, content_parts: List[str], schedule: Dict) -> None:
        """Add on-call shifts, users, and overrides to content"""
        
        # Get user lookup for resolving user names
        user_lookup = schedule.get('user_lookup', {})
        
        # Add schedule rotations
        if rotations := schedule.get('rotations'):
            content_parts.append("\n## Schedule Rotations")
            for rotation in rotations:
                if rotation_attrs := rotation.get('attributes'):
                    rotation_name = rotation_attrs.get('name', 'Unknown Rotation')
                    rotation_type = rotation_attrs.get('schedule_rotationable_type', 'Unknown Type')
                    active_days = ', '.join(rotation_attrs.get('active_days', []))
                    handoff_time = rotation_attrs.get('schedule_rotationable_attributes', {}).get('handoff_time', 'Unknown')
                    timezone = rotation_attrs.get('time_zone', 'Unknown')
                    
                    content_parts.append(f"### {rotation_name} ({rotation_type})")
                    content_parts.append(f"- Active Days: {active_days}")
                    content_parts.append(f"- Handoff Time: {handoff_time}")
                    content_parts.append(f"- Timezone: {timezone}")
        
        # Add upcoming shifts (from all_shifts)
        if all_shifts := schedule.get('all_shifts'):
            content_parts.append("\n## All Shifts")
            # Show first 10 shifts
            for shift in all_shifts[:10]:
                if shift_attrs := shift.get('attributes'):
                    start_time = shift_attrs.get('starts_at', 'Unknown')
                    end_time = shift_attrs.get('ends_at', 'Unknown')
                    user_display = "Unknown User"
                    
                    # Get user ID from relationships
                    if relationships := shift.get('relationships'):
                        if user_rel := relationships.get('user', {}).get('data'):
                            user_id = user_rel.get('id')
                            if user_id and user_id in user_lookup:
                                user_data = user_lookup[user_id]
                                user_attrs = user_data.get('attributes', {})
                                # Try different name fields (using official API fields only)
                                user_display = (
                                    user_attrs.get('name') or 
                                    user_attrs.get('full_name') or
                                    user_attrs.get('full_name_with_team') or
                                    f"{user_attrs.get('first_name', '')} {user_attrs.get('last_name', '')}".strip() or
                                    user_attrs.get('email', '').split('@')[0] or
                                    f"User {user_id}"
                                )
                            elif user_id:
                                user_display = f"User {user_id}"
                    
                    content_parts.append(f"- {start_time} to {end_time}: {user_display}")
        
        # Add schedule overrides
        if overrides := schedule.get('overrides'):
            content_parts.append("\n## Schedule Overrides")
            for override in overrides[:3]:  # Limit to next 3 overrides
                if override_attrs := override.get('attributes'):
                    start_time = override_attrs.get('start_time', 'Unknown')
                    end_time = override_attrs.get('end_time', 'Unknown')
                    user_display = "Unknown User"
                    
                    # Get user name from override attributes (different structure than shifts)
                    if attributes := override.get('attributes'):
                        if user_data := attributes.get('user', {}).get('data'):
                            user_id = user_data.get('id')
                            if user_id and user_id in user_lookup:
                                lookup_data = user_lookup[user_id]
                                user_attrs = lookup_data.get('attributes', {})
                                # Try different name fields (using official API fields only)
                                user_display = (
                                    user_attrs.get('name') or 
                                    user_attrs.get('full_name') or
                                    user_attrs.get('full_name_with_team') or
                                    f"{user_attrs.get('first_name', '')} {user_attrs.get('last_name', '')}".strip() or
                                    user_attrs.get('email', '').split('@')[0] or
                                    f"User {user_id}"
                                )
                            elif user_id:
                                # Try to use the user data directly from override if available
                                if user_attrs := user_data.get('attributes', {}):
                                    user_display = (
                                        user_attrs.get('name') or 
                                        user_attrs.get('full_name') or
                                        user_attrs.get('full_name_with_team') or
                                        f"{user_attrs.get('first_name', '')} {user_attrs.get('last_name', '')}".strip() or
                                        user_attrs.get('email', '').split('@')[0] or
                                        f"User {user_id}"
                                    )
                                else:
                                    user_display = f"User {user_id}"
                    
                    content_parts.append(f"- {start_time} to {end_time}: {user_display} (Override)")
        
