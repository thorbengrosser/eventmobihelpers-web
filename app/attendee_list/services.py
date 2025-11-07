from typing import List, Dict
from app.utils import get_api_client
from flask import session


def fetch_sessions() -> List[Dict]:
    client = get_api_client()
    event_id = session.get('event_id')
    if not client or not event_id:
        return []
    sessions = client.get_sessions(event_id) or []

    # Deduplicate sessions by id because the API may return the same session multiple times
    unique_sessions = []
    seen_ids = set()
    for s in sessions:
        sid = str(s.get('id') or '')
        if sid and sid in seen_ids:
            continue
        if sid:
            seen_ids.add(sid)
        unique_sessions.append(s)
    return unique_sessions


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
    attendees = client.get_session_attendees(event_id, session_id) or []

    # Deduplicate attendees because the API may return the same page multiple times when pagination is ignored
    unique_attendees = []
    seen_keys = set()
    for a in attendees:
        key = str(
            a.get('id')
            or a.get('person_id')
            or a.get('email')
            or a.get('work_email')
            or a.get('personal_email')
            or repr(a)
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_attendees.append(a)

    # Normalize attendee fields: id, name, company, email
    normalized = []
    for a in unique_attendees:
        normalized.append({
            'id': a.get('id') or a.get('person_id'),
            'name': a.get('name') or a.get('full_name') or f"{a.get('first_name','')} {a.get('last_name','')}".strip(),
            'company': a.get('company') or a.get('company_name') or a.get('organization') or '',
            'email': a.get('email') or a.get('work_email') or a.get('personal_email') or ''
        })
    return normalized


