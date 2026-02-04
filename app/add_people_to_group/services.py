import logging
from app.utils import get_api_client

logger = logging.getLogger(__name__)


def fetch_events():
    """Fetch all events using the shared API client."""
    client = get_api_client()
    if not client:
        return None
    try:
        return client.get_events()
    except Exception as e:
        logger.error("Failed to fetch events: %s", e)
        return None


def fetch_groups(event_id):
    """Fetch people groups for an event using the shared API client."""
    client = get_api_client()
    if not client:
        return None
    try:
        return client.list_people_groups(event_id)
    except Exception as e:
        logger.error("Failed to fetch groups: %s", e)
        return None


def fetch_person_by_email(event_id, email):
    """Fetch a person by email using the shared API client."""
    client = get_api_client()
    if not client:
        return None
    try:
        people = client.list_people(event_id, email=email, include="groups")
        return people[0] if people else None
    except Exception as e:
        logger.error("Failed to fetch person by email: %s", e)
        return None


def update_person_groups(event_id, person_id, groups):
    """
    Update a person's groups (PATCH). groups is a list of group objects with id and optionally external_id.
    Returns (status_code, response_body) for compatibility with existing routes.
    """
    client = get_api_client()
    if not client:
        return 0, None
    try:
        client.update_person(event_id, person_id, {"groups": groups})
        return 200, {}
    except Exception as e:
        logger.error("Failed to update person groups: %s", e)
        status = getattr(getattr(e, "response", None), "status_code", 500)
        try:
            body = getattr(getattr(e, "response", None), "json", lambda: {})() or {}
        except Exception:
            body = {"error": str(e)}
        return status, body
