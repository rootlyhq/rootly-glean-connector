"""
Alert data fetcher for Rootly API
"""

import logging
from typing import List, Dict, Optional
from .base import RootlyDataFetcher

logger = logging.getLogger(__name__)


def fetch_alerts(
    updated_after: Optional[str] = None,
    max_items: Optional[int] = None,
    items_per_page: int = 10
) -> List[Dict]:
    """
    Fetch alerts from Rootly API with enhanced monitoring rules data
    
    Args:
        updated_after: ISO 8601 timestamp to filter alerts
        max_items: Maximum number of alerts to fetch
        items_per_page: Number of items per page
        
    Returns:
        List of alert dictionaries with enhanced monitoring information
    """
    fetcher = RootlyDataFetcher()
    
    logger.info(f"Fetching alerts with enhanced monitoring data, max_items: {max_items}")
    alerts = fetcher.fetch_paginated_data(
        endpoint="alerts",
        updated_after=updated_after,
        max_items=max_items,
        items_per_page=items_per_page
    )
    
    # Enhance alerts with global monitoring configuration data
    _enhance_alerts_with_monitoring_data(alerts, fetcher)
    
    return alerts


def _enhance_alerts_with_monitoring_data(alerts: List[Dict], fetcher: RootlyDataFetcher) -> None:
    """
    Enhance alerts with monitoring rules, routing, and configuration data
    
    Args:
        alerts: List of alert dictionaries to enhance
        fetcher: RootlyDataFetcher instance
    """
    logger.debug("Enhancing alerts with monitoring configuration data")
    
    try:
        # These endpoints don't exist in Rootly API v1
        # Removing non-existent endpoint calls that cause 404 errors
        routing_rules = None
        urgencies = None
        alert_groups = None
        alert_events = None
        
        # Store global monitoring data (shared across all alerts)
        monitoring_context = {
            "routing_rules": routing_rules or [],
            "urgencies": urgencies or [],
            "alert_groups": alert_groups or [],
            "recent_events": alert_events[:10] if alert_events else []  # Last 10 events
        }
        
        # Add monitoring context to each alert
        for alert in alerts:
            alert["monitoring_context"] = monitoring_context
            
        logger.debug(f"Enhanced {len(alerts)} alerts with monitoring context: "
                    f"{len(monitoring_context['routing_rules'])} routing rules, "
                    f"{len(monitoring_context['urgencies'])} urgencies, "
                    f"{len(monitoring_context['alert_groups'])} groups")
            
    except Exception as e:
        logger.warning(f"Failed to enhance alerts with monitoring data: {e}")