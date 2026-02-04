from app.utils import get_api_client


def fetch_events(event_id):
    """Fetch events list (unused here but kept for compatibility)."""
    client = get_api_client()
    if not client:
        return []
    try:
        return client.get_events()
    except Exception:
        return []


def get_session_uuid(event_id, session_external_id):
    """
    Look up a session by external_id and return its id (uuid).
    session_external_id can be the session's external_id or the session's id.
    """
    client = get_api_client()
    if not client:
        return None
    try:
        sessions = client.list_sessions(event_id, external_id=session_external_id)
        if sessions:
            return sessions[0].get("id")
        # Try as direct id
        sessions = client.get_sessions(event_id)
        for s in sessions:
            if str(s.get("id")) == str(session_external_id) or str(s.get("external_id", "")) == str(session_external_id):
                return s.get("id")
        return None
    except Exception:
        return None


def delete_session(event_id, session_id):
    """
    Delete a session. Returns status_code (e.g. 204 on success) for compatibility with routes.
    """
    client = get_api_client()
    if not client:
        return 500
    try:
        status_code, _ = client.delete_session(event_id, session_id)
        return status_code
    except Exception:
        return 500
