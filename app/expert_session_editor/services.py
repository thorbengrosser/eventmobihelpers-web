import requests
from datetime import datetime

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
    
    # Create a copy of the data to modify
    update_data = data.copy()
    
    # Convert datetime objects to ISO format strings
    if 'start_datetime' in update_data and isinstance(update_data['start_datetime'], datetime):
        update_data['start_datetime'] = update_data['start_datetime'].isoformat()
    if 'end_datetime' in update_data and isinstance(update_data['end_datetime'], datetime):
        update_data['end_datetime'] = update_data['end_datetime'].isoformat()
    
    # Handle chat settings
    if 'chat_enabled' in update_data:
        chat_enabled = update_data.pop('chat_enabled') == 'true'
        update_data['chat'] = {'enabled': chat_enabled}
    
    # Handle AAQ settings
    if 'aaq_enabled' in update_data:
        aaq_enabled = update_data.pop('aaq_enabled') == 'true'
        if 'settings' not in update_data:
            update_data['settings'] = {}
        update_data['settings']['aaq_enabled'] = aaq_enabled
    
    response = requests.patch(url, headers=headers, json=update_data)
    return response.json()