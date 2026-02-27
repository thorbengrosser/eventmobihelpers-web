from typing import List, Dict, Any, Tuple
from app.utils import get_api_client
from flask import session

# Standard columns available on People (per EventMobi API swagger)
STANDARD_COLUMNS: List[Tuple[str, str]] = [
    ('name', 'Name'),
    ('first_name', 'First Name'),
    ('last_name', 'Last Name'),
    ('email', 'Email'),
    ('company', 'Company'),
    ('title', 'Title'),
    ('pronouns', 'Pronouns'),
    ('about', 'About'),
    ('website', 'Website'),
    ('checkin_code', 'Check-in Code'),
    ('created_at', 'Created'),
    ('updated_at', 'Updated'),
]


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


def fetch_people_custom_fields() -> List[Dict]:
    """Fetch people custom field definitions for the current event."""
    client = get_api_client()
    event_id = session.get('event_id')
    if not client or not event_id:
        return []
    return client.list_people_custom_fields(event_id) or []


def get_available_columns() -> List[Tuple[str, str]]:
    """Return (key, label) for all available columns: standard fields + custom fields."""
    columns = list(STANDARD_COLUMNS)
    for cf in fetch_people_custom_fields():
        fid = cf.get('id') or cf.get('external_id')
        name = cf.get('name') or f"Custom ({fid})"
        if fid:
            columns.append((f'custom_field:{fid}', name))
    return columns


def _format_datetime(val: Any) -> str:
    """Format ISO datetime for display."""
    if not val:
        return ''
    s = str(val)
    if 'T' in s and len(s) >= 19:
        return s[:19].replace('T', ' ')
    return s


def get_cell_value(attendee: Dict, column_key: str) -> Any:
    """Get the display value for a column from an attendee."""
    if column_key == 'name':
        return (
            attendee.get('name')
            or attendee.get('full_name')
            or f"{attendee.get('first_name', '')} {attendee.get('last_name', '')}".strip()
        )
    if column_key == 'company':
        return attendee.get('company') or attendee.get('company_name') or attendee.get('organization') or ''
    if column_key == 'email':
        return attendee.get('email') or attendee.get('work_email') or attendee.get('personal_email') or ''
    if column_key == 'title':
        return attendee.get('title') or attendee.get('job_title') or ''
    if column_key.startswith('custom_field:'):
        field_id = column_key.split(':', 1)[1]
        for cf in attendee.get('custom_fields') or []:
            if str(cf.get('id')) == str(field_id) or str(cf.get('external_id')) == str(field_id):
                val = cf.get('value')
                if val is not None:
                    return val
                if cf.get('file') and isinstance(cf['file'], dict):
                    return cf['file'].get('url') or cf['file'].get('filename') or '—'
                if cf.get('options_selected_values'):
                    return ', '.join(str(v) for v in cf['options_selected_values']) if cf['options_selected_values'] else ''
                return ''
        return ''
    val = attendee.get(column_key, '')
    if column_key in ('created_at', 'updated_at') and val:
        return _format_datetime(val)
    return val


def fetch_session_attendees(session_id: str, include_custom_fields: bool = True) -> List[Dict]:
    client = get_api_client()
    event_id = session.get('event_id')
    if not client or not event_id or not session_id:
        return []
    include = 'custom_fields' if include_custom_fields else None
    attendees = client.get_session_attendees(event_id, session_id, include=include) or []

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

    # Add normalized name, company, email for backward compatibility; keep full raw data
    for a in unique_attendees:
        a['name'] = (
            a.get('name')
            or a.get('full_name')
            or f"{a.get('first_name', '')} {a.get('last_name', '')}".strip()
        )
        a['company'] = a.get('company') or a.get('company_name') or a.get('organization') or ''
        a['email'] = a.get('email') or a.get('work_email') or a.get('personal_email') or ''
    return unique_attendees


