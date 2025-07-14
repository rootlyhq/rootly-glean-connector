"""
Schedule data fetcher for Rootly API
"""

import logging
from typing import List, Dict, Optional
from .base import RootlyDataFetcher

logger = logging.getLogger(__name__)


def fetch_schedules(
    updated_after: Optional[str] = None,
    max_items: Optional[int] = None,
    items_per_page: int = 10
) -> List[Dict]:
    """
    Fetch schedules from Rootly API with enhanced on-call data
    
    Args:
        updated_after: ISO 8601 timestamp to filter schedules
        max_items: Maximum number of schedules to fetch
        items_per_page: Number of items per page
        
    Returns:
        List of schedule dictionaries with enhanced on-call information
    """
    fetcher = RootlyDataFetcher()
    
    logger.info(f"Fetching schedules with enhanced on-call data, max_items: {max_items}")
    schedules = fetcher.fetch_paginated_data(
        endpoint="schedules",
        updated_after=updated_after,
        max_items=max_items,
        items_per_page=items_per_page
    )
    
    # Enhance each schedule with on-call data
    for schedule in schedules:
        _enhance_schedule_with_oncall_data(schedule, fetcher)
    
    return schedules


def _enhance_schedule_with_oncall_data(schedule: Dict, fetcher: RootlyDataFetcher) -> None:
    """
    Enhance schedule with shifts, users, and overrides data
    
    Args:
        schedule: Schedule dictionary to enhance
        fetcher: RootlyDataFetcher instance
    """
    schedule_id = schedule.get("id")
    if not schedule_id:
        return
        
    logger.debug(f"Enhancing schedule {schedule_id} with on-call data")
    
    try:
        # Fetch schedule rotations using correct endpoint path
        rotations_data = fetcher.fetch_single_endpoint(f"schedules/{schedule_id}/schedule_rotations")
        if rotations_data:
            schedule["rotations"] = rotations_data
            logger.debug(f"Added {len(rotations_data)} rotations to schedule {schedule_id}")
        
        # Fetch all shifts for this schedule (this endpoint exists)
        shifts_all_data = fetcher.fetch_single_endpoint("shifts", params={"schedule_id": schedule_id})
        if shifts_all_data:
            schedule["all_shifts"] = shifts_all_data
            logger.debug(f"Added {len(shifts_all_data)} all shifts to schedule {schedule_id}")
        
        # Fetch schedule override shifts using correct endpoint
        try:
            override_shifts_data = fetcher.fetch_single_endpoint(f"schedules/{schedule_id}/override_shifts")
            if override_shifts_data:
                schedule["overrides"] = override_shifts_data
                logger.debug(f"Added {len(override_shifts_data)} override shifts to schedule {schedule_id}")
            else:
                logger.debug(f"No schedule override shifts found for schedule {schedule_id}")
        except Exception as override_error:
            logger.debug(f"Failed to fetch schedule override shifts for {schedule_id}: {override_error}")
            # Don't add empty overrides key to avoid confusion
        
        # Fetch user details to resolve user names
        user_ids = set()
        
        # Collect all user IDs from shifts
        if shifts_all_data:
            for shift in shifts_all_data:
                if relationships := shift.get('relationships'):
                    if user_rel := relationships.get('user', {}).get('data'):
                        if user_id := user_rel.get('id'):
                            user_ids.add(user_id)
        
        # Collect user IDs from overrides (different structure than shifts)
        if override_shifts_data:
            for override in override_shifts_data:
                # Override shifts have user data in attributes.user.data, not relationships
                if attributes := override.get('attributes'):
                    if user_data := attributes.get('user', {}).get('data'):
                        if user_id := user_data.get('id'):
                            user_ids.add(user_id)
        
        # Fetch user details for all collected user IDs
        if user_ids:
            user_lookup = _fetch_users_lookup(fetcher, list(user_ids))
            schedule["user_lookup"] = user_lookup
            logger.debug(f"Added user lookup for {len(user_lookup)} users to schedule {schedule_id}")
        else:
            schedule["user_lookup"] = {}
            
    except Exception as e:
        logger.warning(f"Failed to enhance schedule {schedule_id} with on-call data: {e}")


def _fetch_users_lookup(fetcher: RootlyDataFetcher, user_ids: List[str]) -> Dict[str, Dict]:
    """
    Fetch user details for given user IDs to create a lookup dictionary
    
    Args:
        fetcher: RootlyDataFetcher instance
        user_ids: List of user IDs to fetch
        
    Returns:
        Dictionary mapping user_id -> user_data
    """
    user_lookup = {}
    
    # If no user IDs to fetch, return empty lookup
    if not user_ids:
        return user_lookup
    
    try:
        # Fetch users with adequate page size to get all users (there are ~65 total)
        logger.debug(f"Fetching user details for {len(user_ids)} users...")
        users_data = fetcher.fetch_single_endpoint("users", params={"page[size]": 100})
        
        if users_data:
            for user in users_data:
                user_id = user.get('id')
                if user_id in user_ids:
                    user_lookup[user_id] = user
                    
        logger.info(f"Built user lookup for {len(user_lookup)} out of {len(user_ids)} requested users")
        
        # If we didn't find all users, log the missing ones
        if len(user_lookup) < len(user_ids):
            missing_users = set(user_ids) - set(user_lookup.keys())
            logger.warning(f"Could not find user details for {len(missing_users)} users: {list(missing_users)[:5]}...")
        
    except Exception as e:
        logger.warning(f"Failed to fetch user details: {e}")
        
    return user_lookup

