"""
Base document mapper with common functionality
"""

import logging
from typing import Dict, Any, Optional, List
from dateutil import parser as dtparse
from glean.api_client import models
from config import get_config

logger = logging.getLogger(__name__)


class BaseDocumentMapper:
    """Base class for mapping Rootly data to Glean documents"""
    
    def __init__(self):
        self.config = get_config()
    
    def _extract_author(self, data: Dict[str, Any], user_path: str = "user") -> Optional[Dict[str, str]]:
        """
        Extract author information from Rootly data
        
        Args:
            data: Raw data dictionary
            user_path: Path to user data in the dictionary
            
        Returns:
            Author dictionary or None
        """
        try:
            user_data = data.get(user_path, {})
            if isinstance(user_data, dict) and user_data.get('data', {}).get('attributes', {}):
                user_attrs = user_data['data']['attributes']
                author_details = {}
                
                if full_name := user_attrs.get('full_name'):
                    author_details["name"] = full_name
                if email := user_attrs.get('email'):
                    author_details["email"] = email
                    
                return author_details if author_details else None
        except Exception as e:
            logger.warning(f"Could not extract author information: {e}")
        
        return None
    
    def _extract_timestamps(self, attributes: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract and convert timestamps from Rootly data
        
        Args:
            attributes: Attributes dictionary from Rootly API
            
        Returns:
            Dictionary with converted timestamps
        """
        timestamps = {}
        
        for field_name, api_field in [("created_at", "created_at"), ("updated_at", "updated_at")]:
            if ts_value := attributes.get(api_field):
                try:
                    timestamps[field_name] = int(dtparse.isoparse(ts_value).timestamp())
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse {api_field}: {ts_value}, error: {e}")
        
        return timestamps
    
    def _build_content_field(self, text: str, mime_type: str = "text/plain") -> Dict[str, str]:
        """
        Build content field for Glean document
        
        Args:
            text: Text content
            mime_type: MIME type of content
            
        Returns:
            Content field dictionary
        """
        return {
            "mime_type": mime_type,
            "text_content": text
        }
    
    def _create_base_document(
        self,
        item_id: str,
        object_type: str,
        title: str,
        view_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create base document structure
        
        Args:
            item_id: Unique ID of the item
            object_type: Type of object (Incident, Alert, etc.)
            title: Document title
            view_url: URL to view the item
            
        Returns:
            Base document dictionary
        """
        # Use the item_id directly without prefix to avoid duplicates
        doc_fields = {
            "id": item_id,
            "datasource": self.config.glean.datasource_name,
            "title": title,
            "object_type": object_type,
            "permissions": {
                "allow_anonymous_access": True
            }
        }
        
        # Always provide a view_url - either the actual URL or a default one
        if view_url and view_url.strip():
            doc_fields["view_url"] = view_url
        else:
            # Generate a default URL based on object type and ID
            type_mapping = {
                "Incident": "incidents",
                "Alert": "alerts", 
                "Schedule": "schedules",
                "EscalationPolicy": "escalation_policies"
            }
            object_type_url = type_mapping.get(object_type, object_type.lower() + "s")
            doc_fields["view_url"] = f"https://rootly.com/account/{object_type_url}/{item_id}"
            
        logger.debug(f"Created base document for {item_id}: {doc_fields}")
        return doc_fields