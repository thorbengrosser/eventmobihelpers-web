import logging
import re
from typing import List, Dict, Any, Optional, Tuple

from app.utils import get_api_client

logger = logging.getLogger(__name__)


def parse_emails(raw_text: str) -> List[str]:
    """
    Parse a blob of text into a list of email addresses.

    Splits on newlines, commas, semicolons, and whitespace, then strips
    and de-duplicates addresses while preserving order.
    """
    if not raw_text:
        return []

    # Split on common separators
    parts = re.split(r"[,\s;]+", raw_text)
    seen = set()
    emails: List[str] = []

    for part in parts:
        email = part.strip()
        if not email:
            continue
        if email.lower() in seen:
            continue
        seen.add(email.lower())
        emails.append(email)

    return emails


def fetch_person_by_email(event_id: str, email: str) -> Optional[Dict[str, Any]]:
    """
    Look up a single person by email address using the shared API client.

    Returns the first matching person dict or None if not found.
    """
    client = get_api_client()
    if not client:
        return None
    try:
        people = client.list_people(event_id, email=email)
        return people[0] if people else None
    except Exception as e:
        logger.error("Failed to fetch person by email: %s", e)
        return None


def delete_person(event_id: str, person_id: str) -> Tuple[int, str]:
    """
    Delete a person (attendee) from the event using the shared API client.

    Returns a tuple of (status_code, response_text) so callers can surface
    useful error information.
    """
    client = get_api_client()
    if not client:
        return 0, "No API client"
    try:
        return client.delete_person(event_id, person_id)
    except Exception as e:
        logger.error("Failed to delete person %s: %s", person_id, e)
        return 500, str(e)
