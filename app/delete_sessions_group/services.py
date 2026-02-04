from app.utils import get_api_client


def fetch_events(event_id):
    """Fetch events using the shared API client."""
    client = get_api_client()
    if not client:
        return None
    try:
        return client.get_events()
    except Exception:
        return None


def fetch_tracks(event_id):
    """Fetch tracks for an event using the shared API client (events/{event_id}/sessions/tracks)."""
    client = get_api_client()
    if not client:
        return None
    try:
        return client.get_tracks(event_id)
    except Exception:
        return None


def fetch_sessions_by_track(event_id, track_id):
    """Fetch all sessions for an event and filter by track_id (client-side filter)."""
    client = get_api_client()
    if not client:
        return None
    try:
        sessions = client.list_sessions(event_id, include="tracks")
        if not sessions:
            return []
        return [s for s in sessions if any(t.get("id") == track_id for t in (s.get("tracks") or []))]
    except Exception:
        return None


def delete_session(event_id, session_id):
    """
    Delete a session using the shared API client.
    Returns (session_id, status_code) for compatibility with routes.
    """
    client = get_api_client()
    if not client:
        return session_id, 500
    try:
        status_code, _ = client.delete_session(event_id, session_id)
        return session_id, status_code
    except Exception:
        return session_id, 500
