import requests
from app.session import get_api_key
from flask import current_app
import time

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
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 10
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def _get_all_paginated(self, endpoint, params=None, version_accept=None, limit=500, max_pages=50):
        results = []
        page = 0
        headers = dict(self.headers)
        if version_accept:
            headers['Accept'] = version_accept

        while page < max_pages:
            merged_params = dict(params or {})
            merged_params.update({'limit': limit, 'page': page})
            url = f"{self.BASE_URL}/{endpoint}"
            try:
                resp = requests.get(url, headers=headers, params=merged_params, timeout=10)
                resp.raise_for_status()
                body = resp.json()
                data = body.get('data') if isinstance(body, dict) else body
                if not isinstance(data, list) or not data:
                    break
                results.extend(data)

                meta = body.get('meta') if isinstance(body, dict) else None
                pagination = meta.get('pagination') if isinstance(meta, dict) else None

                page_items_count = len(data)
                total_items_count = None
                if pagination:
                    page_items_count = pagination.get('page_items_count', page_items_count)
                    total_items_count = pagination.get('total_items_count')

                if page_items_count < limit:
                    break
                if total_items_count is not None and len(results) >= total_items_count:
                    break

                page += 1
            except Exception:
                break
        return results
    
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
            params = {'sort': 'start_datetime'}
            data = self._get_all_paginated(
                f'events/{event_id}/sessions',
                params=params,
                version_accept='application/vnd.eventmobi+json; version=4',
                limit=1000
            )
            if data:
                return data
            response = self._make_request('GET', f'events/{event_id}/sessions', params=params)
            return response.get('data', []) if isinstance(response, dict) else response
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
            data = self._get_all_paginated(
                f'events/{event_id}/people',
                version_accept='application/vnd.eventmobi+json; version=4'
            )
            if not data:
                response = self._make_request('GET', f'events/{event_id}/people')
                return response.get('data', [])
            return data
        except Exception as e:
            raise Exception(f"Failed to fetch people for event {event_id}: {str(e)}") 

    def get_person(self, event_id, person_id):
        """Get a single person by ID."""
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            url = f"{self.BASE_URL}/events/{event_id}/people/{person_id}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json().get('data') or resp.json()
            return data
        except Exception:
            # Try v3
            response = self._make_request('GET', f'events/{event_id}/people/{person_id}')
            return response.get('data') or response

    def get_session_attendees(self, event_id, session_id):
        """Fetch attendees for a session using dedicated endpoints first, then fall back to filters."""
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            params = {'limit': 500, 'page': 0}
            url = f"{self.BASE_URL}/events/{event_id}/sessions/{session_id}/people"

            results = []
            while True:
                resp = requests.get(url, headers=headers, params=params, timeout=10)
                resp.raise_for_status()
                body = resp.json()
                page_items = body.get('data') if isinstance(body, dict) else body
                if not isinstance(page_items, list) or not page_items:
                    break
                results.extend(page_items)

                meta = body.get('meta') if isinstance(body, dict) else {}
                pagination = meta.get('pagination') if isinstance(meta, dict) else {}
                next_page = pagination.get('next_page_number')
                if next_page is None:
                    break
                params['page'] = next_page

            if results:
                return results
        except requests.RequestException as e:
            current_app.logger.warning(f"sessions/{session_id}/people endpoint failed: {e}")

        # Fallback: use people endpoint with scheduled_session_id filter (v4)
        people = self._get_all_paginated(
            f'events/{event_id}/people',
            params={'scheduled_session_id': session_id, 'sort': 'last_name'},
            version_accept='application/vnd.eventmobi+json; version=4',
            limit=500
        )
        if isinstance(people, list) and people:
            return people

        # Final fallback: single request without pagination helper
        response = self._make_request('GET', f'events/{event_id}/people', params={'scheduled_session_id': session_id})
        return response.get('data', []) if isinstance(response, dict) else []

    def probe_session_attendance(self, event_id, session_id):
        """Run real API requests against multiple endpoints/filters and report findings."""
        report = { 'event_id': event_id, 'session_id': session_id, 'checks': [] }
        v4 = 'application/vnd.eventmobi+json; version=4'
        headers_v4 = dict(self.headers)
        headers_v4['Accept'] = v4

        def do_get(url, headers=None, params=None):
            start = time.time()
            try:
                resp = requests.get(url, headers=headers or self.headers, params=params, timeout=10)
                took = round((time.time() - start) * 1000)
                data = None
                try:
                    j = resp.json()
                except Exception:
                    j = None
                if j is not None:
                    data = j.get('data') if isinstance(j, dict) else j
                count = len(data) if isinstance(data, list) else 0
                return {
                    'ok': resp.status_code < 400,
                    'status': resp.status_code,
                    'ms': took,
                    'count': count,
                    'sample': (data[:3] if isinstance(data, list) else None)
                }
            except Exception as e:
                took = round((time.time() - start) * 1000)
                return { 'ok': False, 'error': str(e), 'ms': took }

        # 1) sessions/{id}/attendees
        report['checks'].append({
            'name': 'sessions/{id}/attendees (v4)',
            'result': do_get(f"{self.BASE_URL}/events/{event_id}/sessions/{session_id}/attendees", headers=headers_v4, params={'page[size]': 200})
        })

        # 2) sessions/{id}/people
        report['checks'].append({
            'name': 'sessions/{id}/people (v4)',
            'result': do_get(f"{self.BASE_URL}/events/{event_id}/sessions/{session_id}/people", headers=headers_v4, params={'page[size]': 200})
        })

        # 3) personal_schedules with several filters
        personal_base = f"{self.BASE_URL}/events/{event_id}/personal_schedules"
        filters = [
            {'filter[session_id]': session_id},
            {'filter[session.id]': session_id},
            {'filter[session]': session_id},
            {'filter[session_uuid]': session_id},
            {'filter[session.uuid]': session_id},
        ]
        for f in filters:
            params = dict(f)
            params.update({'page[size]': 200})
            report['checks'].append({
                'name': f"personal_schedules (v4) {list(f.keys())[0]}",
                'result': do_get(personal_base, headers=headers_v4, params=params)
            })

        # 4) people filtered by possible session fields
        people_base = f"{self.BASE_URL}/events/{event_id}/people"
        people_filters = [
            {'filter[session_id]': session_id},
            {'filter[registered_session_id]': session_id},
            {'filter[registered_sessions.id]': session_id},
            {'filter[sessions.id]': session_id},
            {'filter[personal_schedules.session_id]': session_id},
        ]
        for f in people_filters:
            params = dict(f)
            params.update({'page[size]': 200})
            report['checks'].append({
                'name': f"people (v4) {list(f.keys())[0]}",
                'result': do_get(people_base, headers=headers_v4, params=params)
            })

        # 5) person sample quick check (if caller wants to verify a known person)
        report['hint'] = 'If you share this report, I can wire the correct endpoint/filter without guessing.'
        return report