from datetime import datetime, timezone
from decimal import Decimal

from app.utils import get_api_client


def _serialize_value(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.isoformat()
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(val) for key, val in value.items()}
    return value


def fetch_events():
    """Fetch all events using the shared API client."""
    client = get_api_client()
    if not client:
        return []
    try:
        return client.get_events()
    except Exception:
        return []


def fetch_sessions(event_id):
    """Fetch all sessions for an event using the shared API client."""
    client = get_api_client()
    if not client:
        return []
    try:
        return client.get_sessions(event_id)
    except Exception:
        return []


def fetch_session_details(event_id, session_id):
    """Fetch full session details with includes using the shared API client."""
    client = get_api_client()
    if not client:
        return {}
    try:
        return client.get_session(
            event_id,
            session_id,
            include="location,chat,external_links,tracks,roles,settings,documents,content_experience,accessibility",
        )
    except Exception:
        return {}


def update_session(event_id, session_id, data):
    """Update a session (PATCH) using the shared API client."""
    client = get_api_client()
    if not client:
        raise ValueError("No API client")
    update_data = _serialize_value(data)
    return client.update_session(event_id, session_id, update_data)
