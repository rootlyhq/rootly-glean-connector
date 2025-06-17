"""
Sync coordinator for managing multi-data-type syncing between Rootly and Glean
"""

import logging
from typing import List, Dict, Any, Optional
from glean.api_client import models
from config import get_config
from data_fetchers import (
    fetch_incidents, 
    fetch_alerts, 
    fetch_schedules, 
    fetch_escalation_policies,
    fetch_retrospectives
)
from data_fetchers.enhanced_incidents import fetch_enhanced_incidents
from document_mappers import (
    incident_to_doc,
    alert_to_doc, 
    schedule_to_doc,
    escalation_policy_to_doc,
    retrospective_to_doc
)
from glean_schema import get_object_definitions

logger = logging.getLogger(__name__)


class SyncCoordinator:
    """Coordinates syncing of multiple data types from Rootly to Glean"""
    
    def __init__(self):
        self.config = get_config()
        self.data_type_configs = {
            'incidents': {
                'fetcher': self._fetch_incidents_with_enhancement,
                'mapper': incident_to_doc,
                'config': self.config.data_types.incidents
            },
            'alerts': {
                'fetcher': fetch_alerts,
                'mapper': alert_to_doc,
                'config': self.config.data_types.alerts
            },
            'schedules': {
                'fetcher': fetch_schedules,
                'mapper': schedule_to_doc,
                'config': self.config.data_types.schedules
            },
            'escalation_policies': {
                'fetcher': fetch_escalation_policies,
                'mapper': escalation_policy_to_doc,
                'config': self.config.data_types.escalation_policies
            },
            'retrospectives': {
                'fetcher': fetch_retrospectives,
                'mapper': retrospective_to_doc,
                'config': self.config.data_types.retrospectives
            }
        }
    
    def sync_all_data_types(self, updated_after: Optional[str] = None) -> Dict[str, Any]:
        """
        Sync all enabled data types from Rootly to Glean
        
        Args:
            updated_after: ISO 8601 timestamp to filter data
            
        Returns:
            Dictionary with sync results for each data type
        """
        results = {}
        all_documents = []
        
        for data_type, config_info in self.data_type_configs.items():
            if not config_info['config'].enabled:
                logger.info(f"Skipping {data_type} (disabled in configuration)")
                results[data_type] = {'status': 'skipped', 'reason': 'disabled'}
                continue
            
            try:
                logger.info(f"Starting sync for {data_type}...")
                documents = self._sync_data_type(data_type, config_info, updated_after)
                
                # Debug: Log document IDs being added
                if documents:
                    logger.info(f"Adding {len(documents)} {data_type} documents:")
                    for i, doc in enumerate(documents):
                        doc_dict = doc.model_dump() if hasattr(doc, 'model_dump') else doc.__dict__
                        logger.info(f"  {data_type}[{i}]: ID={doc_dict.get('id')}, Title={doc_dict.get('title', 'No title')}")
                
                all_documents.extend(documents)
                results[data_type] = {
                    'status': 'success',
                    'documents_created': len(documents)
                }
                logger.info(f"Successfully synced {len(documents)} {data_type}")
                
            except Exception as e:
                logger.error(f"Error syncing {data_type}: {e}", exc_info=True)
                results[data_type] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Deduplicate documents by ID before returning
        unique_documents = []
        seen_ids = set()
        duplicates_removed = 0
        
        for doc in all_documents:
            doc_dict = doc.model_dump() if hasattr(doc, 'model_dump') else doc.__dict__
            doc_id = doc_dict.get('id')
            
            if doc_id not in seen_ids:
                unique_documents.append(doc)
                seen_ids.add(doc_id)
            else:
                duplicates_removed += 1
                doc_title = doc_dict.get('title', 'No title')
                doc_type = doc_dict.get('object_type', 'Unknown')
                logger.warning(f"Removed duplicate document: ID={doc_id}, Type={doc_type}, Title={doc_title}")
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate documents. Final count: {len(unique_documents)}")
        
        # Return results with total document count
        results['summary'] = {
            'total_documents': len(unique_documents),
            'duplicates_removed': duplicates_removed,
            'sync_status': 'completed'
        }
        
        return results, unique_documents
    
    def _sync_data_type(
        self, 
        data_type: str, 
        config_info: Dict, 
        updated_after: Optional[str]
    ) -> List[models.DocumentDefinition]:
        """
        Sync a specific data type
        
        Args:
            data_type: Type of data to sync
            config_info: Configuration information for the data type
            updated_after: Timestamp filter
            
        Returns:
            List of converted documents
        """
        fetcher = config_info['fetcher']
        mapper = config_info['mapper']
        type_config = config_info['config']
        
        # Fetch data from Rootly
        logger.info(f"Fetching {data_type} from Rootly...")
        raw_data = fetcher(
            updated_after=updated_after,
            max_items=type_config.max_items,
            items_per_page=type_config.items_per_page
        )
        
        if not raw_data:
            logger.warning(f"No {data_type} data fetched from Rootly")
            return []
        
        # Convert to Glean documents
        logger.info(f"Converting {len(raw_data)} {data_type} to Glean documents...")
        documents = []
        
        for item in raw_data:
            try:
                doc = mapper(item)
                if doc:
                    documents.append(doc)
                else:
                    logger.warning(f"Failed to convert {data_type} item {item.get('id', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error converting {data_type} item {item.get('id', 'Unknown')}: {e}")
        
        logger.info(f"Successfully converted {len(documents)}/{len(raw_data)} {data_type} to documents")
        return documents
    
    def _fetch_incidents_with_enhancement(
        self, 
        updated_after: Optional[str] = None,
        max_items: Optional[int] = None,
        items_per_page: int = 10
    ) -> List[Dict]:
        """
        Wrapper to fetch incidents with enhancement based on configuration
        
        Args:
            updated_after: ISO 8601 timestamp to filter incidents
            max_items: Maximum number of incidents to fetch
            items_per_page: Number of items per page
            
        Returns:
            List of incident dictionaries (enhanced if configured)
        """
        incident_config = self.config.data_types.incidents
        enhanced_config = incident_config.enhanced_data
        
        # Check if any enhancement is enabled
        if (enhanced_config.include_events or 
            enhanced_config.include_action_items):
            
            logger.info("Using enhanced incident fetching with additional data")
            return fetch_enhanced_incidents(
                updated_after=updated_after,
                max_items=max_items,
                items_per_page=items_per_page,
                include_events=enhanced_config.include_events,
                include_action_items=enhanced_config.include_action_items
            )
        else:
            logger.info("Using basic incident fetching")
            return fetch_incidents(
                updated_after=updated_after,
                max_items=max_items,
                items_per_page=items_per_page
            )
    
    def get_enabled_data_types(self) -> List[str]:
        """Get list of enabled data types"""
        return [
            data_type for data_type, config_info in self.data_type_configs.items()
            if config_info['config'].enabled
        ]