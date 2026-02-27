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

    def list_sessions(self, event_id, **filters):
        """List sessions with optional filters (track_id, external_id, search, sort, etc.)."""
        params = dict(filters) if filters else {}
        params.setdefault('sort', 'start_datetime')
        try:
            data = self._get_all_paginated(
                f'events/{event_id}/sessions',
                params=params,
                version_accept='application/vnd.eventmobi+json; version=4',
                limit=1000
            )
            return data if data else []
        except Exception as e:
            raise Exception(f"Failed to list sessions for event {event_id}: {str(e)}")

    def get_session(self, event_id, session_id, include=None):
        """Get a single session by ID. Optional include: location,chat,external_links,tracks,roles,settings,documents,content_experience,accessibility."""
        try:
            params = {}
            if include:
                params['include'] = include
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            url = f"{self.BASE_URL}/events/{event_id}/sessions/{session_id}"
            resp = requests.get(url, headers=headers, params=params or None, timeout=10)
            resp.raise_for_status()
            out = resp.json()
            return out.get('data') or out
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch session: {str(e)}")

    def create_session(self, event_id, body):
        """Create a new session."""
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            url = f"{self.BASE_URL}/events/{event_id}/sessions"
            resp = requests.post(url, headers=headers, json=body, timeout=10)
            resp.raise_for_status()
            out = resp.json()
            return out.get('data') or out
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create session: {str(e)}")

    def update_session(self, event_id, session_id, body):
        """Update a session (PATCH)."""
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            url = f"{self.BASE_URL}/events/{event_id}/sessions/{session_id}"
            resp = requests.patch(url, headers=headers, json=body, timeout=10)
            resp.raise_for_status()
            out = resp.json()
            return out.get('data') or out
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to update session: {str(e)}")

    def delete_session(self, event_id, session_id):
        """Delete a session. Returns (status_code, response_text) for callers that need to surface errors."""
        try:
            headers = dict(self.headers)
            url = f"{self.BASE_URL}/events/{event_id}/sessions/{session_id}"
            resp = requests.delete(url, headers=headers, timeout=10)
            return resp.status_code, resp.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to delete session: {str(e)}")

    def get_tracks(self, event_id):
        """Get all tracks for a specific event. Path: events/{event_id}/sessions/tracks (v4)."""
        try:
            response = self._make_request('GET', f'events/{event_id}/sessions/tracks')
            return response.get('data', [])
        except Exception as e:
            raise Exception(f"Failed to fetch tracks for event {event_id}: {str(e)}")

    def list_people_groups(self, event_id):
        """List people groups for an event. Path: events/{event_id}/people/groups (v4)."""
        try:
            response = self._make_request('GET', f'events/{event_id}/people/groups')
            return response.get('data', [])
        except Exception as e:
            raise Exception(f"Failed to fetch people groups for event {event_id}: {str(e)}")

    def get_groups(self, event_id):
        """Get all people groups for a specific event (alias for list_people_groups)."""
        return self.list_people_groups(event_id)
    
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

    def list_people(self, event_id, **filters):
        """List people with optional filters (email, emails, group_ids, registration_status, scheduled_session_id, search, sort, etc.)."""
        params = dict(filters) if filters else None
        try:
            data = self._get_all_paginated(
                f'events/{event_id}/people',
                params=params,
                version_accept='application/vnd.eventmobi+json; version=4',
                limit=1000
            )
            return data if data else []
        except Exception as e:
            raise Exception(f"Failed to list people for event {event_id}: {str(e)}")

    def create_person(self, event_id, body):
        """Create a new person. Body must include first_name, last_name (and optional email, etc.)."""
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            url = f"{self.BASE_URL}/events/{event_id}/people"
            resp = requests.post(url, headers=headers, json=body, timeout=10)
            resp.raise_for_status()
            out = resp.json()
            return out.get('data') or out
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create person: {str(e)}")

    def update_person(self, event_id, people_id, body):
        """Update a person (PATCH). Body can include first_name, last_name, groups, public_preferences, etc."""
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            headers['x-nested-list-partial-updates'] = '1'
            url = f"{self.BASE_URL}/events/{event_id}/people/{people_id}"
            resp = requests.patch(url, headers=headers, json=body, timeout=10)
            resp.raise_for_status()
            out = resp.json()
            return out.get('data') or out
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to update person: {str(e)}")

    def delete_person(self, event_id, people_id):
        """Delete a person. Returns (status_code, response_text) for callers that need to surface errors."""
        try:
            headers = dict(self.headers)
            url = f"{self.BASE_URL}/events/{event_id}/people/{people_id}"
            resp = requests.delete(url, headers=headers, timeout=10)
            return resp.status_code, resp.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to delete person: {str(e)}")

    def add_to_schedule(self, event_id, people_id, session_id):
        """
        Add a session to a person's personal schedule.

        Implementation detail: instead of using the dedicated Personal Schedule POST endpoint,
        this uses the People PATCH endpoint with `scheduled_sessions` and
        `x-nested-list-partial-updates=1`, which appends the session to the existing schedule.
        """
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            headers['Content-Type'] = 'application/json'
            headers['x-nested-list-partial-updates'] = '1'
            url = f"{self.BASE_URL}/events/{event_id}/people/{people_id}"
            body = {"scheduled_sessions": [{"id": session_id}]}
            resp = requests.patch(url, headers=headers, json=body, timeout=10)
            resp.raise_for_status()
            return True, None
        except requests.exceptions.RequestException as e:
            try:
                err_msg = e.response.json() if e.response else {}
                if isinstance(err_msg, dict) and err_msg.get('errors'):
                    msg = err_msg['errors'][0].get('message', str(err_msg['errors'][0]))
                elif isinstance(err_msg, dict) and err_msg.get('error'):
                    msg = err_msg['error'].get('message', str(err_msg['error']))
                else:
                    msg = e.response.text if e.response else str(e)
            except Exception:
                msg = e.response.text if e.response and hasattr(e, 'response') else str(e)
            return False, msg

    def remove_from_schedule(self, event_id, people_id, session_id):
        """Remove a session from a person's personal schedule (DELETE people/{id}/schedule/{session_id})."""
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            url = f"{self.BASE_URL}/events/{event_id}/people/{people_id}/schedule/{session_id}"
            resp = requests.delete(url, headers=headers, timeout=10)
            resp.raise_for_status()
            return True, None
        except requests.exceptions.RequestException as e:
            msg = e.response.text if e.response and hasattr(e, 'response') else str(e)
            return False, msg

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

    def list_people_custom_fields(self, event_id):
        """Get all people custom fields configured for the event. Returns list of field definitions with id, name, etc."""
        try:
            data = self._get_all_paginated(
                f'events/{event_id}/people/fields',
                version_accept='application/vnd.eventmobi+json; version=4',
                limit=500
            )
            return data if isinstance(data, list) else []
        except Exception as e:
            current_app.logger.warning("list_people_custom_fields failed: %s", e)
            return []

    def get_session_attendees(self, event_id, session_id, include=None):
        """Fetch attendees for a session using dedicated endpoints first, then fall back to filters.
        Optional include: e.g. 'custom_fields' to fetch custom field values (see People API include param)."""
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            params = {'limit': 500, 'page': 0}
            if include:
                params['include'] = include
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
        fallback_params = {'scheduled_session_id': session_id, 'sort': 'last_name'}
        if include:
            fallback_params['include'] = include
        people = self._get_all_paginated(
            f'events/{event_id}/people',
            params=fallback_params,
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

    def list_companies(self, event_id, **filters):
        """List companies for an event with optional filters."""
        params = dict(filters) if filters else None
        try:
            data = self._get_all_paginated(
                f'events/{event_id}/companies',
                params=params,
                version_accept='application/vnd.eventmobi+json; version=4',
                limit=1000
            )
            return data if data else []
        except Exception as e:
            raise Exception(f"Failed to list companies for event {event_id}: {str(e)}")

    def get_company(self, event_id, company_id):
        """Get a single company by ID."""
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            url = f"{self.BASE_URL}/events/{event_id}/companies/{company_id}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            out = resp.json()
            return out.get('data') or out
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch company: {str(e)}")

    def update_company(self, event_id, company_id, body):
        """Update a company (PATCH)."""
        try:
            headers = dict(self.headers)
            headers['Accept'] = 'application/vnd.eventmobi+json; version=4'
            url = f"{self.BASE_URL}/events/{event_id}/companies/{company_id}"
            resp = requests.patch(url, headers=headers, json=body, timeout=10)
            resp.raise_for_status()
            out = resp.json()
            return out.get('data') or out
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to update company: {str(e)}")

    def delete_company(self, event_id, company_id):
        """Delete a company. Returns (status_code, response_text)."""
        try:
            headers = dict(self.headers)
            url = f"{self.BASE_URL}/events/{event_id}/companies/{company_id}"
            resp = requests.delete(url, headers=headers, timeout=10)
            return resp.status_code, resp.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to delete company: {str(e)}")