from app.utils import get_api_client


def fetch_events():
    """Fetch all events using the shared API client."""
    client = get_api_client()
    if not client:
        return None
    try:
        return client.get_events()
    except Exception:
        return None


def fetch_groups(event_id):
    """Fetch people groups for an event using the shared API client."""
    client = get_api_client()
    if not client:
        return None
    try:
        return client.list_people_groups(event_id)
    except Exception:
        return None


def fetch_people_in_group(event_id, group_id):
    """Fetch people in a group using the shared API client."""
    client = get_api_client()
    if not client:
        return None
    try:
        return client.list_people(event_id, group_id=group_id)
    except Exception:
        return None


def update_attendee_settings(event_id, person_id, settings):
    """
    Update attendee settings (public_preferences, private_preferences) using the shared API client.
    Returns (status_code, response_body) for compatibility with existing routes.
    """
    client = get_api_client()
    if not client:
        return 0, None
    payload = {
        "public_preferences": {
            "chat_enabled": settings.get("enable_chat"),
            "is_profile_visible": settings.get("is_profile_visible"),
        },
        "private_preferences": {
            "receive_organizer_email": settings.get("receive_organizer_email"),
            "receive_attendee_email": settings.get("receive_attendee_email"),
            "attendee_push_notifications_enabled": settings.get("attendee_push_notifications"),
            "offline_notifications_enabled": settings.get("offline_notifications"),
        },
    }
    try:
        client.update_person(event_id, person_id, payload)
        return 200, {}
    except Exception as e:
        status = getattr(getattr(e, "response", None), "status_code", 500)
        try:
            body = getattr(getattr(e, "response", None), "json", lambda: {})() or {}
        except Exception:
            body = {"error": str(e)}
        return status, body
