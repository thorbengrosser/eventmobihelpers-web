import requests
import logging

logger = logging.getLogger(__name__)

def fetch_events(api_key):
    url = "https://uapi.eventmobi.com/events"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    logger.debug(f"Fetching events from {url}")
    response = requests.get(url, headers=headers)
    logger.debug(f"Events API response status: {response.status_code}")
    if response.status_code != 200:
        logger.error(f"Failed to fetch events: {response.text}")
        return None
    return response.json().get('data', [])

def fetch_groups(api_key, event_id):
    url = f"https://uapi.eventmobi.com/events/{event_id}/people/groups"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    logger.debug(f"Fetching groups from {url}")
    response = requests.get(url, headers=headers)
    logger.debug(f"Groups API response status: {response.status_code}")
    if response.status_code != 200:
        logger.error(f"Failed to fetch groups: {response.text}")
        return None
    return response.json().get('data', [])

def fetch_person_by_email(api_key, event_id, email):
    url = f"https://uapi.eventmobi.com/events/{event_id}/people?include=groups&email={email}"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    logger.debug(f"Fetching person by email from {url}")
    response = requests.get(url, headers=headers)
    logger.debug(f"Person API response status: {response.status_code}")
    if response.status_code != 200:
        logger.error(f"Failed to fetch person: {response.text}")
        return None
    data = response.json().get('data', [])
    logger.debug(f"Found person data: {data}")
    return data[0] if data else None

def update_person_groups(api_key, event_id, person_id, groups):
    url = f"https://uapi.eventmobi.com/events/{event_id}/people/{person_id}"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=3",
        "Authorization": f"Bearer {api_key}"
    }
    # groups is now a list of group objects (with id and external_id)
    data = {"groups": groups}
    logger.debug(f"Updating person groups at {url} with data: {data}")
    response = requests.patch(url, json=data, headers=headers)
    logger.debug(f"Update groups API response status: {response.status_code}")
    logger.debug(f"Update groups API response: {response.text}")
    return response.status_code, response.json()
