from typing import List, Dict
from app.utils import get_api_client
from flask import session


def fetch_sessions() -> List[Dict]:
    client = get_api_client()
    event_id = session.get('event_id')
    if not client or not event_id:
        return []
    return client.get_sessions(event_id)


def fetch_session_detail(session_id: str) -> Dict:
    """Fetch a single session's details from the cached sessions list."""
    sessions = fetch_sessions()
    for s in sessions:
        if str(s.get('id')) == str(session_id):
            return s
    return {}


def fetch_session_attendees(session_id: str) -> List[Dict]:
    client = get_api_client()
    event_id = session.get('event_id')
    if not client or not event_id or not session_id:
        return []
    attendees = client.get_session_attendees(event_id, session_id)
    # Normalize attendee fields: id, name, company, email
    normalized = []
    for a in attendees:
        normalized.append({
            'id': a.get('id') or a.get('person_id'),
            'name': a.get('name') or a.get('full_name') or f"{a.get('first_name','')} {a.get('last_name','')}".strip(),
            'company': a.get('company') or a.get('company_name') or a.get('organization') or '',
            'email': a.get('email') or a.get('work_email') or a.get('personal_email') or ''
        })
    return normalized


