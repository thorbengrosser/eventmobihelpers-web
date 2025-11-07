from datetime import datetime, timezone
from decimal import Decimal

import requests

def fetch_events(api_key):
    url = "https://uapi.eventmobi.com/events"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    return response.json().get('data', [])

def fetch_sessions(api_key, event_id):
    url = f"https://uapi.eventmobi.com/events/{event_id}/sessions"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
    return response.json().get('data', [])

def fetch_session_details(api_key, event_id, session_id):
    url = (
        f"https://uapi.eventmobi.com/events/{event_id}/sessions/{session_id}"
        "?include=location,chat,external_links,tracks,roles,settings,documents,content_experience,accessibility"
    )
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {}
    return response.json().get('data', {})

def _serialize_value(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.isoformat()
        return value.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(val) for key, val in value.items()}
    return value


def update_session(api_key, event_id, session_id, data):
    url = f"https://uapi.eventmobi.com/events/{event_id}/sessions/{session_id}"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    update_data = _serialize_value(data)

    response = requests.patch(url, headers=headers, json=update_data)
    return response.json()