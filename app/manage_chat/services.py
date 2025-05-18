import requests

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

def fetch_groups(api_key, event_id):
    url = f"https://uapi.eventmobi.com/events/{event_id}/people/groups"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    return response.json().get('data', [])

def fetch_people_in_group(api_key, event_id, group_id):
    url = f"https://uapi.eventmobi.com/events/{event_id}/people"
    querystring = {"group_id": group_id}
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        return None
    return response.json().get('data', [])

def update_attendee_settings(api_key, event_id, person_id, settings):
    url = f"https://uapi.eventmobi.com/events/{event_id}/people/{person_id}"
    
    # Prepare the payload with all settings
    payload = {
        "public_preferences": {
            "chat_enabled": settings.get('enable_chat'),
            "is_profile_visible": settings.get('is_profile_visible')
        },
        "private_preferences": {
            "receive_organizer_email": settings.get('receive_organizer_email'),
            "receive_attendee_email": settings.get('receive_attendee_email'),
            "attendee_push_notifications_enabled": settings.get('attendee_push_notifications'),
            "offline_notifications_enabled": settings.get('offline_notifications')
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    
    print(f"DEBUG: Updating settings for person {person_id} with payload: {payload}")
    response = requests.patch(url, json=payload, headers=headers)
    print(f"DEBUG: API Response status: {response.status_code}")
    print(f"DEBUG: API Response body: {response.text}")
    
    return response.status_code, response.json()
