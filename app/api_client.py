import requests
from flask import current_app
from typing import Optional, Dict, Any, List

class EventMobiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = current_app.config['EVENTMOBI_API_BASE_URL']
        self.api_version = current_app.config['EVENTMOBI_API_VERSION']
        self.headers = {
            "Accept": f"application/vnd.eventmobi+json; version={self.api_version}",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the EventMobi API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all events."""
        return self._make_request('GET', 'events')

    def get_event(self, event_id: str) -> Dict[str, Any]:
        """Get a specific event."""
        return self._make_request('GET', f'events/{event_id}')

    def get_sessions(self, event_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for an event."""
        return self._make_request('GET', f'events/{event_id}/sessions')

    def delete_session(self, event_id: str, session_id: str) -> Dict[str, Any]:
        """Delete a session."""
        return self._make_request('DELETE', f'events/{event_id}/sessions/{session_id}')

    def get_groups(self, event_id: str) -> List[Dict[str, Any]]:
        """Get all groups for an event."""
        return self._make_request('GET', f'events/{event_id}/groups')

    def add_people_to_group(self, event_id: str, group_id: str, people_ids: List[str]) -> Dict[str, Any]:
        """Add people to a group."""
        return self._make_request('POST', f'events/{event_id}/groups/{group_id}/people', 
                                json={'people_ids': people_ids})

    def validate_api_key(self) -> bool:
        """Validate the API key by making a test request."""
        try:
            self._make_request('GET', 'events')
            return True
        except requests.exceptions.RequestException:
            return False 