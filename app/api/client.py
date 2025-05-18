import requests
from app.session import get_api_key

class EventMobiClient:
    BASE_URL = 'https://uapi.eventmobi.com'
    
    def __init__(self):
        self.api_key = get_api_key()
        if not self.api_key:
            raise ValueError("No API key found")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.eventmobi+json; version=3'
        }
    
    def _make_request(self, method, endpoint, **kwargs):
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def get_events(self):
        """Get all events accessible with the current API key."""
        try:
            response = self._make_request('GET', 'events')
            return response.get('data', [])
        except Exception as e:
            raise Exception(f"Failed to fetch events: {str(e)}")
    
    def get_event(self, event_id):
        """Get details for a specific event."""
        try:
            response = self._make_request('GET', f'events/{event_id}')
            return response.get('data', {})
        except Exception as e:
            raise Exception(f"Failed to fetch event {event_id}: {str(e)}")
    
    def get_sessions(self, event_id):
        """Get all sessions for a specific event."""
        try:
            response = self._make_request('GET', f'events/{event_id}/sessions')
            return response.get('data', [])
        except Exception as e:
            raise Exception(f"Failed to fetch sessions for event {event_id}: {str(e)}")
    
    def get_tracks(self, event_id):
        """Get all tracks for a specific event."""
        try:
            response = self._make_request('GET', f'events/{event_id}/tracks')
            return response.get('data', [])
        except Exception as e:
            raise Exception(f"Failed to fetch tracks for event {event_id}: {str(e)}")
    
    def get_groups(self, event_id):
        """Get all groups for a specific event."""
        try:
            response = self._make_request('GET', f'events/{event_id}/groups')
            return response.get('data', [])
        except Exception as e:
            raise Exception(f"Failed to fetch groups for event {event_id}: {str(e)}")
    
    def get_people(self, event_id):
        """Get all people for a specific event."""
        try:
            response = self._make_request('GET', f'events/{event_id}/people')
            return response.get('data', [])
        except Exception as e:
            raise Exception(f"Failed to fetch people for event {event_id}: {str(e)}") 