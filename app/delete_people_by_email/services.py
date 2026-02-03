import logging
import re
from typing import List, Dict, Any, Optional, Tuple

import requests

from app.utils import get_api_key

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


def _build_headers(api_key: str) -> Dict[str, str]:
    return {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}",
    }


def fetch_person_by_email(api_key: str, event_id: str, email: str) -> Optional[Dict[str, Any]]:
    """
    Look up a single person by email address.

    Returns the first matching person dict or None if not found.
    """
    url = f"https://uapi.eventmobi.com/events/{event_id}/people"
    params = {"include": "groups", "email": email}
    headers = _build_headers(api_key)

    logger.debug("Fetching person by email from %s", url)
    response = requests.get(url, headers=headers, params=params)
    logger.debug("Person API response status: %s", response.status_code)

    if response.status_code != 200:
        logger.error("Failed to fetch person: %s", response.text)
        return None

    data = response.json().get("data", [])
    logger.debug("Found person data: %s", data)
    return data[0] if data else None


def delete_person(api_key: str, event_id: str, person_id: str) -> Tuple[int, str]:
    """
    Delete a person (attendee) from the event.

    Returns a tuple of (status_code, response_text) so callers can surface
    useful error information.
    """
    url = f"https://uapi.eventmobi.com/events/{event_id}/people/{person_id}"
    headers = _build_headers(api_key)

    logger.debug("Deleting person %s at %s", person_id, url)
    response = requests.delete(url, headers=headers)
    logger.debug("Delete person API response status: %s", response.status_code)
    logger.debug("Delete person API response: %s", response.text)

    return response.status_code, response.text

