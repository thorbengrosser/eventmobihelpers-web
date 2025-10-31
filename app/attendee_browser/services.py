from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from app.utils import get_api_client
from flask import session
import requests
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# Simple in-memory cache (could be replaced with Redis/Memcached)
_attendee_cache = {}
_cache_key_prefix = 'attendees:'


def _get_cache_key(event_id: str, filters: Optional[Dict] = None) -> str:
    """Generate cache key for event + filters."""
    filter_str = json.dumps(filters, sort_keys=True) if filters else ''
    cache_data = f"{event_id}:{filter_str}"
    return _cache_key_prefix + hashlib.md5(cache_data.encode()).hexdigest()


def list_attendees(event_id: str, page: int = 1, per_page: int = 50, filters: Optional[Dict] = None, sort_column: Optional[str] = None, sort_direction: str = 'asc') -> Dict:
    """Fetch and filter attendees for an event with pagination using API-level pagination."""
    client = get_api_client()
    if not client:
        return {'items': [], 'page': page, 'per_page': per_page, 'total': 0, 'total_pages': 1}
    
    try:
        # Check cache first (cache doesn't include sort, we apply that later)
        cache_key = _get_cache_key(event_id, filters)
        
        # Try to get from cache
        if cache_key in _attendee_cache:
            all_items = _attendee_cache[cache_key]['items']
            cached_total = _attendee_cache[cache_key]['total']
        else:
            # Fetch all items from API (API seems to ignore pagination)
            # Build API params (without pagination - fetch all)
            api_params = {}
            
            # Try to pass filters to API when possible
            if filters:
                # Group ID filter - API supports this
                if filters.get('eq', {}).get('group_id'):
                    api_params['group_id'] = filters['eq']['group_id']
            
            # Make API request
            headers = dict(client.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            url = f"{client.BASE_URL}/events/{event_id}/people"
            
            # Fetch all data (API seems to return all regardless of pagination params)
            resp = requests.get(url, headers=headers, params=api_params, timeout=30)
            resp.raise_for_status()
            response_data = resp.json()
            
            # Extract data
            all_items = response_data.get('data', [])
            
            # Remove duplicates based on ID if present
            seen_ids = set()
            unique_items = []
            for item in all_items:
                item_id = item.get('id') or item.get('people_id')
                if item_id:
                    if item_id not in seen_ids:
                        seen_ids.add(item_id)
                        unique_items.append(item)
                else:
                    # No ID, include it
                    unique_items.append(item)
            all_items = unique_items
            
            # Try to get total from pagination metadata
            meta = response_data.get('meta', {})
            pagination = meta.get('pagination', {})
            total_items = pagination.get('total_items_count')
            
            if total_items is not None:
                cached_total = int(total_items)
            else:
                cached_total = len(all_items)
            
            # Cache the results
            _attendee_cache[cache_key] = {
                'items': all_items,
                'total': cached_total
            }
        
        # Apply client-side filters (all filters that weren't handled by API)
        client_side_filters = {}
        if filters:
            # Check which filters were handled by API
            if filters.get('eq', {}).get('group_id'):
                # Group ID filter was passed to API, don't apply client-side
                # Copy other eq filters
                eq_filters = {k: v for k, v in filters.get('eq', {}).items() if k != 'group_id'}
                if eq_filters:
                    client_side_filters['eq'] = eq_filters
            else:
                # All eq filters need client-side handling
                if filters.get('eq'):
                    client_side_filters['eq'] = filters['eq']
            
            if filters.get('in'):
                client_side_filters['in'] = filters['in']
            if filters.get('date_between'):
                client_side_filters['date_between'] = filters['date_between']
        
        # Apply client-side filters before pagination
        if client_side_filters:
            logger.info(f"Applying client-side filters: {client_side_filters}")
            initial_count = len(all_items)
            all_items = apply_client_filters(all_items, client_side_filters)
            filtered_count = len(all_items)
            logger.info(f"Filtered from {initial_count} to {filtered_count} items")
            cached_total = len(all_items)  # Recalculate total after filtering
            total = cached_total
        else:
            total = cached_total
        
        # Apply server-side sorting if requested
        if sort_column:
            try:
                # Get sort direction
                reverse = sort_direction == 'desc'
                
                # Define how to get the sort value for different columns
                def get_sort_value(item, column):
                    if column == 'name':
                        return item.get('name') or (item.get('first_name', '') + ' ' + item.get('last_name', '')).strip() or ''
                    elif column == 'email':
                        return item.get('email', '')
                    elif column == 'company':
                        return item.get('company') or item.get('company_name', '')
                    elif column == 'title':
                        return item.get('title') or item.get('job_title', '')
                    elif column == 'created_at':
                        return item.get('created_at', '')
                    elif column == 'updated_at':
                        return item.get('updated_at', '')
                    else:
                        return item.get(column, '')
                
                # Sort the items
                all_items = sorted(all_items, key=lambda x: get_sort_value(x, sort_column), reverse=reverse)
                logger.info(f"Sorted {len(all_items)} items by {sort_column} ({sort_direction})")
            except Exception as e:
                logger.warning(f"Failed to sort items: {e}")
        
        # Apply pagination (manual slicing)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        items = all_items[start_idx:end_idx]
        
        # Calculate total pages
        total_pages = max(1, (total + per_page - 1) // per_page) if total > 0 else 1
        
        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }
    except Exception as e:
        return {
            'items': [],
            'page': page,
            'per_page': per_page,
            'total': 0,
            'total_pages': 1,
            'error': str(e)
        }


def apply_client_filters(items: List[Dict], filters: Dict) -> List[Dict]:
    """Apply client-side filters to items (for fields not supported by API)."""
    if not filters:
        return items
    
    def normalize(value: Any) -> str:
        """Normalize value for comparison."""
        if value is None:
            return ''
        return str(value).lower().strip()
    
    filtered = []
    for item in items:
        matches = True
        
        # q[]: contains (case-insensitive) - only if not already filtered by API
        q_filters = filters.get('q', {})
        for field, needle in q_filters.items():
            if not needle:
                continue
            needle_norm = normalize(needle)
            hay = normalize(item.get(field, ''))
            if not hay or needle_norm not in hay:
                matches = False
                break
        
        if not matches:
            continue
        
        # eq[]: equals (case-insensitive)
        eq_filters = filters.get('eq', {})
        for field, value in eq_filters.items():
            if not value:
                continue
            expected = normalize(value)
            actual = normalize(item.get(field))
            if expected != actual:
                matches = False
                break
        
        if not matches:
            continue
        
        # in[]: membership (case-insensitive)
        in_filters = filters.get('in', {})
        for field, values in in_filters.items():
            if not values:
                continue
            # Handle comma-separated string or list
            if isinstance(values, str):
                options = [normalize(v) for v in values.split(',') if v.strip()]
            elif isinstance(values, list):
                options = [normalize(v) for v in values if v]
            else:
                continue
            
            if not options:
                continue
            
            actual = normalize(item.get(field))
            if not actual or actual not in options:
                matches = False
                break
        
        if not matches:
            continue
        
        # date_between[][start|end]
        date_filters = filters.get('date_between', {})
        for field, range_config in date_filters.items():
            if not isinstance(range_config, dict):
                continue
            value_raw = item.get(field)
            if not value_raw:
                matches = False
                break
            
            # Parse item date value
            try:
                value_str = str(value_raw)
                # Handle ISO format with timezone
                if value_str.endswith('Z'):
                    value_str = value_str.replace('Z', '+00:00')
                value_date = datetime.fromisoformat(value_str)
            except Exception:
                # Try parsing common date formats
                try:
                    # Try ISO format without timezone
                    value_date = datetime.fromisoformat(value_str[:19])
                except Exception:
                    matches = False
                    break
            
            start_raw = range_config.get('start')
            end_raw = range_config.get('end')
            
            if start_raw:
                try:
                    # datetime-local format is "YYYY-MM-DDTHH:mm" - normalize to ISO format
                    start_str = str(start_raw).strip()
                    if not start_str:
                        # Skip this filter if empty
                        pass
                    else:
                        # Normalize datetime-local format to ISO format with seconds
                        if 'T' in start_str:
                            # Check if it needs seconds (datetime-local is "YYYY-MM-DDTHH:mm")
                            if len(start_str) == 16:  # "2025-10-31T18:00"
                                start_str = start_str + ':00'  # Add seconds to get "2025-10-31T18:00:00"
                            # If still no seconds, check manually
                            elif start_str.count(':') == 1:  # Only HH:mm
                                start_str = start_str + ':00'
                        else:
                            # Date only, treat as start of day
                            start_str = start_str + 'T00:00:00'
                        
                        # Parse the normalized date string
                        start_date = datetime.fromisoformat(start_str)
                        
                        # Make naive datetimes timezone-aware if comparing with aware datetimes
                        if value_date.tzinfo is not None and start_date.tzinfo is None:
                            # Assume naive datetime is in UTC
                            start_date = start_date.replace(tzinfo=timezone.utc)
                        elif value_date.tzinfo is None and start_date.tzinfo is not None:
                            # Make value_date aware
                            value_date = value_date.replace(tzinfo=timezone.utc)
                        
                        # Compare dates (value_date must be >= start_date)
                        if value_date < start_date:
                            matches = False
                            break
                except Exception as e:
                    # If date parsing fails, log warning
                    logger.warning(f"Failed to parse start date '{start_raw}': {e}")
                    # Don't break - skip this filter if we can't parse it
                    pass
            
            if end_raw:
                end_str = str(end_raw).strip()
                if end_str:  # Only apply if end date is provided
                    try:
                        # datetime-local format is "YYYY-MM-DDTHH:mm" - normalize to ISO format
                        if 'T' in end_str:
                            # Check if it needs seconds (datetime-local is "YYYY-MM-DDTHH:mm")
                            if len(end_str) == 16:  # "2025-10-31T18:00"
                                end_str = end_str + ':00'  # Add seconds
                            # If still no seconds, check manually
                            elif end_str.count(':') == 1:  # Only HH:mm
                                end_str = end_str + ':00'
                        else:
                            # Date only, treat as end of day
                            end_str = end_str + 'T23:59:59'
                        
                        # Parse the normalized date string
                        end_date = datetime.fromisoformat(end_str)
                        
                        # Make naive datetimes timezone-aware if comparing with aware datetimes
                        if value_date.tzinfo is not None and end_date.tzinfo is None:
                            # Assume naive datetime is in UTC
                            end_date = end_date.replace(tzinfo=timezone.utc)
                        elif value_date.tzinfo is None and end_date.tzinfo is not None:
                            # Make value_date aware
                            value_date = value_date.replace(tzinfo=timezone.utc)
                        
                        # Compare dates (value_date must be <= end_date)
                        if value_date > end_date:
                            matches = False
                            break
                    except Exception as e:
                        # If date parsing fails, log warning
                        logger.warning(f"Failed to parse end date '{end_raw}': {e}")
                        # Don't break - skip this filter if we can't parse it
                        pass
        
        if matches:
            filtered.append(item)
    
    return filtered

