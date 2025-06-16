"""
Enhanced incident data fetcher with timeline, RCA, and detailed data
"""

import logging
from typing import List, Dict, Optional, Any
from .base import RootlyDataFetcher

logger = logging.getLogger(__name__)


class EnhancedIncidentFetcher(RootlyDataFetcher):
    """Enhanced incident fetcher with timeline and RCA data"""
    
    def fetch_incident_events(self, incident_id: str) -> List[Dict[str, Any]]:
        """
        Fetch incident events (timeline) for a specific incident
        
        Args:
            incident_id: The incident ID
            
        Returns:
            List of incident event dictionaries
        """
        try:
            logger.debug(f"Fetching events for incident {incident_id}")
            payload = self._make_request(f"incidents/{incident_id}/events")
            events = payload.get("data", [])
            logger.debug(f"Found {len(events)} events for incident {incident_id}")
            return events
        except Exception as e:
            logger.warning(f"Could not fetch events for incident {incident_id}: {e}")
            return []
    
    def fetch_incident_action_items(self, incident_id: str) -> List[Dict[str, Any]]:
        """
        Fetch detailed action items for a specific incident
        
        Args:
            incident_id: The incident ID
            
        Returns:
            List of action item dictionaries
        """
        try:
            logger.debug(f"Fetching action items for incident {incident_id}")
            payload = self._make_request(f"incidents/{incident_id}/action_items")
            action_items = payload.get("data", [])
            logger.debug(f"Found {len(action_items)} action items for incident {incident_id}")
            return action_items
        except Exception as e:
            logger.warning(f"Could not fetch action items for incident {incident_id}: {e}")
            return []
    
    def fetch_severity_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch all severity definitions for enhanced severity data
        
        Returns:
            Dictionary mapping severity IDs to severity data
        """
        try:
            logger.debug("Fetching severity definitions")
            payload = self._make_request("severities")
            severities = payload.get("data", [])
            
            # Create lookup dictionary
            severity_lookup = {}
            for severity in severities:
                severity_id = severity.get("id")
                if severity_id:
                    severity_lookup[severity_id] = severity
            
            logger.debug(f"Loaded {len(severity_lookup)} severity definitions")
            return severity_lookup
        except Exception as e:
            logger.warning(f"Could not fetch severity definitions: {e}")
            return {}
    
    def enrich_incidents_with_details(
        self, 
        incidents: List[Dict[str, Any]],
        include_events: bool = True,
        include_action_items: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Enrich incidents with additional detailed data
        
        Args:
            incidents: List of basic incident data
            include_events: Whether to fetch incident events (timeline)
            include_action_items: Whether to fetch detailed action items
            
        Returns:
            List of enriched incident dictionaries
        """
        if not incidents:
            return incidents
        
        logger.info(f"Enriching {len(incidents)} incidents with additional data...")
        
        # Fetch severity definitions once for all incidents
        severity_lookup = self.fetch_severity_definitions()
        
        enriched_incidents = []
        for incident in incidents:
            incident_id = incident.get("id")
            if not incident_id:
                logger.warning("Incident missing ID, skipping enrichment")
                enriched_incidents.append(incident)
                continue
            
            enriched_incident = incident.copy()
            enriched_incident["_enhanced_data"] = {}
            
            # Add incident events (timeline)
            if include_events:
                events = self.fetch_incident_events(incident_id)
                enriched_incident["_enhanced_data"]["events"] = events
            
            # Add detailed action items
            if include_action_items:
                action_items = self.fetch_incident_action_items(incident_id)
                enriched_incident["_enhanced_data"]["action_items"] = action_items
            
            # Enhance severity data
            if severity_lookup:
                severity_data = incident.get("attributes", {}).get("severity", {})
                if isinstance(severity_data, dict) and severity_data.get("data", {}).get("id"):
                    severity_id = severity_data["data"]["id"]
                    if severity_id in severity_lookup:
                        enriched_incident["_enhanced_data"]["severity_details"] = severity_lookup[severity_id]
            
            enriched_incidents.append(enriched_incident)
        
        logger.info(f"Successfully enriched {len(enriched_incidents)} incidents")
        return enriched_incidents


def fetch_enhanced_incidents(
    updated_after: Optional[str] = None,
    max_items: Optional[int] = None,
    items_per_page: int = 10,
    include_events: bool = True,
    include_action_items: bool = True
) -> List[Dict]:
    """
    Fetch incidents with enhanced data including events and action items
    
    Args:
        updated_after: ISO 8601 timestamp to filter incidents
        max_items: Maximum number of incidents to fetch
        items_per_page: Number of items per page
        include_events: Whether to fetch incident events (timeline)
        include_action_items: Whether to fetch detailed action items
        
    Returns:
        List of enhanced incident dictionaries
    """
    fetcher = EnhancedIncidentFetcher()
    
    # First fetch basic incidents
    logger.info(f"Fetching basic incidents, max_items: {max_items}")
    basic_incidents = fetcher.fetch_paginated_data(
        endpoint="incidents",
        updated_after=updated_after,
        max_items=max_items,
        items_per_page=items_per_page
    )
    
    if not basic_incidents:
        logger.info("No basic incidents found")
        return []
    
    # Then enrich with additional data
    enhanced_incidents = fetcher.enrich_incidents_with_details(
        basic_incidents,
        include_events=include_events,
        include_action_items=include_action_items
    )
    
    return enhanced_incidents