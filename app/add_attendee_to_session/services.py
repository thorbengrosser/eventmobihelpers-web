import logging
from app.utils import get_api_client

logger = logging.getLogger(__name__)


def fetch_person_by_email(event_id, email):
    """Fetch a person by their email address using the shared API client."""
    client = get_api_client()
    if not client:
        return None
    try:
        people = client.list_people(event_id, email=email)
        return people[0] if people else None
    except Exception as e:
        logger.error("Failed to fetch person by email: %s", e)
        return None


def add_session_to_personal_schedule(event_id, person_id, session_id):
    """Add a session to a person's personal schedule using the shared API client. Returns (success, error_msg)."""
    client = get_api_client()
    if not client:
        return False, "No API client"
    success, error_msg = client.add_to_schedule(event_id, person_id, session_id)
    return success, error_msg
