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
    url = f"https://uapi.eventmobi.com/events/{event_id}/sessions/{session_id}?include=location,chat,external_links,tracks,roles,settings,documents"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {}
    return response.json().get('data', {})

def update_session(api_key, event_id, session_id, data):
    url = f"https://uapi.eventmobi.com/events/{event_id}/sessions/{session_id}"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.patch(url, headers=headers, json=data)
    return response.json()