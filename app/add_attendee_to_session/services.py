import requests
import logging

logger = logging.getLogger(__name__)

def fetch_person_by_email(api_key, event_id, email):
    """Fetch a person by their email address."""
    url = f"https://uapi.eventmobi.com/events/{event_id}/people?email={email}"
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

def add_session_to_personal_schedule(api_key, event_id, person_id, session_id):
    """Add a session to a person's personal schedule."""
    url = f"https://uapi.eventmobi.com/events/{event_id}/people/{person_id}/schedule"
    headers = {
        "Accept": "application/vnd.eventmobi+json; version=4",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "id": session_id
    }
    logger.debug(f"Adding session to personal schedule at {url} with data: {data}")
    response = requests.post(url, json=data, headers=headers)
    logger.debug(f"Add session API response status: {response.status_code}")
    logger.debug(f"Add session API response: {response.text}")
    if response.status_code in [200, 201]:
        return True, None
    else:
        try:
            error_data = response.json()
            # Handle different error response formats
            if isinstance(error_data, dict):
                if 'errors' in error_data and error_data['errors']:
                    error_msg = error_data['errors'][0].get('message', str(error_data['errors'][0]))
                elif 'error' in error_data:
                    error_msg = error_data['error'].get('message', str(error_data['error']))
                else:
                    error_msg = str(error_data)
            else:
                error_msg = str(error_data)
        except:
            error_msg = response.text
        return False, error_msg 