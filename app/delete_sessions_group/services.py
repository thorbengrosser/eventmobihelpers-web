import requests
from app.api.client import EventMobiClient

def fetch_events(api_key):
    url = "https://uapi.eventmobi.com/events"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    return response.json().get('data', [])

def fetch_tracks(api_key, event_id):
    client = EventMobiClient()
    try:
        response = client._make_request('GET', f'events/{event_id}/sessions/tracks')
        return response.get('data', [])
    except Exception as e:
        print(f"Failed to fetch tracks: {str(e)}")
        return None

def fetch_sessions_by_track(api_key, event_id, track_id):
    url = f"https://uapi.eventmobi.com/events/{event_id}/sessions"
    querystring = {"include": "tracks"}
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code != 200:
        return None

    try:
        sessions_data = response.json()
    except json.JSONDecodeError:
        return None

    # Filter sessions by track
    sessions_by_track = [
        session for session in sessions_data.get('data', [])
        if any(track['id'] == track_id for track in session.get('tracks', []))
    ]
    
    return sessions_by_track

def delete_session(api_key, event_id, session_id):
    url = f"https://uapi.eventmobi.com/events/{event_id}/sessions/{session_id}"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.delete(url, headers=headers)
    return session_id, response.status_code
