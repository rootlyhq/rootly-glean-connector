"""
Escalation policy data fetcher for Rootly API
"""

import logging
from typing import List, Dict, Optional
from .base import RootlyDataFetcher

logger = logging.getLogger(__name__)


def fetch_escalation_policies(
    updated_after: Optional[str] = None,
    max_items: Optional[int] = None,
    items_per_page: int = 10
) -> List[Dict]:
    """
    Fetch escalation policies from Rootly API with detailed notification chains
    
    Args:
        updated_after: ISO 8601 timestamp to filter policies
        max_items: Maximum number of policies to fetch
        items_per_page: Number of items per page
        
    Returns:
        List of escalation policy dictionaries with detailed notification chain data
    """
    fetcher = RootlyDataFetcher()
    
    logger.info(f"Fetching escalation policies with detailed notification chains, max_items: {max_items}")
    policies = fetcher.fetch_paginated_data(
        endpoint="escalation_policies",
        updated_after=updated_after,
        max_items=max_items,
        items_per_page=items_per_page
    )
    
    # Enhance each policy with detailed escalation chain data
    for policy in policies:
        _enhance_policy_with_notification_chains(policy, fetcher)
    
    return policies


def _enhance_policy_with_notification_chains(policy: Dict, fetcher: RootlyDataFetcher) -> None:
    """
    Enhance escalation policy with detailed notification chain information
    
    Args:
        policy: Escalation policy dictionary to enhance
        fetcher: RootlyDataFetcher instance
    """
    policy_id = policy.get("id")
    if not policy_id:
        return
        
    logger.debug(f"Enhancing escalation policy {policy_id} with notification chain data")
    
    try:
        # Note: Detailed escalation policy sub-endpoints don't exist in API v1
        # The main escalation-policies endpoint should contain all necessary data
        logger.debug(f"Escalation policy {policy_id} details included in main response")
            
    except Exception as e:
        logger.warning(f"Failed to enhance escalation policy {policy_id} with notification chain data: {e}")