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

def update_chat_settings(api_key, event_id, person_id, chat_enabled):
    url = f"https://uapi.eventmobi.com/events/{event_id}/people/{person_id}"
    payload = { "public_preferences": { "chat_enabled": chat_enabled } }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.patch(url, json=payload, headers=headers)
    return response.status_code, response.json()
