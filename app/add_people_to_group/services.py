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

def fetch_person_by_email(api_key, event_id, email):
    url = f"https://uapi.eventmobi.com/events/{event_id}/people?include=groups&email={email}"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    return response.json().get('data', [])

def update_person_groups(api_key, event_id, person_id, groups):
    url = f"https://uapi.eventmobi.com/events/{event_id}/people/{person_id}"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    data = {"groups": groups}
    response = requests.patch(url, json=data, headers=headers)
    return response.status_code, response.json()
