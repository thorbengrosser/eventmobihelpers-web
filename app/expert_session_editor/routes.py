import json
from datetime import datetime, timezone

from flask import render_template, redirect, url_for, session, flash, request

from . import expert_session_editor
from .forms import SessionForm, EditSessionForm
from .services import fetch_sessions, fetch_session_details, update_session
from app.utils import log_action


def _parse_iso_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None


def _normalize_iso(value):
    dt = _parse_iso_datetime(value)
    if not dt:
        return None
    return _to_iso_string(dt)


def _to_iso_string(dt):
    if dt is None:
        return None
    if isinstance(dt, str):
        return _normalize_iso(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    iso = dt.isoformat(timespec='seconds')
    return iso.replace('+00:00', 'Z')


def _to_form_datetime(value):
    dt = _parse_iso_datetime(value)
    if not dt:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _json_default(value):
    if isinstance(value, datetime):
        return _to_iso_string(value)
    try:
        from decimal import Decimal

        if isinstance(value, Decimal):
            return float(value)
    except ImportError:
        pass
    raise TypeError(f'Object of type {type(value).__name__} is not JSON serializable')


def _ensure_min_entries(field, minimum=1, extra=0, add_extra=True):
    existing = len(field.entries)
    target = max(existing, minimum) + (extra if add_extra else 0)
    while len(field.entries) < target:
        field.append_entry()


def _prepare_dynamic_lists(form, add_extra=True):
    _ensure_min_entries(form.accessibility.entity_ids, minimum=1, extra=2, add_extra=add_extra)
    _ensure_min_entries(form.settings.engagement_order, minimum=1, extra=2, add_extra=add_extra)
    _ensure_min_entries(form.external_links, minimum=1, extra=2, add_extra=add_extra)
    _ensure_min_entries(form.roles, minimum=1, extra=1, add_extra=add_extra)
    for role_entry in form.roles:
        _ensure_min_entries(role_entry.form.people, minimum=1, extra=1, add_extra=add_extra)
    _ensure_min_entries(form.tracks, minimum=1, extra=2, add_extra=add_extra)
    _ensure_min_entries(form.sub_tracks, minimum=1, extra=2, add_extra=add_extra)
    _ensure_min_entries(form.documents, minimum=1, extra=2, add_extra=add_extra)


def _ff(field):
    """Resolve a FormField to its enclosed form when present."""
    return getattr(field, 'form', field)


def _build_canonical_payload(details):
    payload = {}

    payload['external_id'] = details.get('external_id')
    payload['name'] = details.get('name')
    payload['description'] = details.get('description')
    payload['start_datetime'] = _normalize_iso(details.get('start_datetime'))
    payload['end_datetime'] = _normalize_iso(details.get('end_datetime'))

    accessibility = details.get('accessibility') or {}
    entity_type = accessibility.get('entity_type')
    entity_ids = accessibility.get('entity_ids') or []
    if entity_type or entity_ids:
        payload['accessibility'] = {
            'entity_type': entity_type,
            'entity_ids': entity_ids,
        }
    else:
        payload['accessibility'] = None

    location = details.get('location') or {}
    location_payload = {}
    if location.get('label') is not None:
        location_payload['label'] = location.get('label')
    map_location = location.get('map_location') or {}
    map_payload = {}
    for key in ('map_id', 'label', 'latitude', 'longitude', 'floor'):
        if map_location.get(key) is not None:
            map_payload[key] = map_location.get(key)
    if map_payload:
        location_payload['map_location'] = map_payload
    payload['location'] = location_payload if location_payload else None

    chat = details.get('chat')
    if chat is None:
        payload['chat'] = {'enabled': False}
    else:
        payload['chat'] = {'enabled': bool(chat.get('enabled', False))}

    settings = details.get('settings') or {}
    payload['settings'] = {
        'aaq_enabled': bool(settings.get('aaq_enabled', False)),
        'prevent_schedule_overlap': bool(settings.get('prevent_schedule_overlap', False)),
        'engagement_order': settings.get('engagement_order') or [],
    }

    payload['external_links'] = []
    for link in details.get('external_links') or []:
        link_payload = {}
        for key in ('id', 'name', 'link', 'order'):
            if link.get(key) not in (None, ''):
                link_payload[key] = link.get(key)
        if link_payload:
            payload['external_links'].append(link_payload)

    payload['roles'] = []
    for role in details.get('roles') or []:
        role_payload = {}
        for key in ('id', 'external_id', 'type', 'name'):
            if role.get(key):
                role_payload[key] = role.get(key)
        people_payload = []
        for person in role.get('people', []):
            person_payload = {}
            if person.get('id'):
                person_payload['id'] = person.get('id')
            if person.get('external_id'):
                person_payload['external_id'] = person.get('external_id')
            if person_payload:
                people_payload.append(person_payload)
        role_payload['people'] = people_payload
        if role_payload:
            payload['roles'].append(role_payload)

    payload['tracks'] = []
    for track in details.get('tracks') or []:
        if track.get('id'):
            payload['tracks'].append({'id': track.get('id')})

    payload['sub_tracks'] = []
    for sub_track in details.get('sub_tracks') or []:
        if sub_track.get('id'):
            payload['sub_tracks'].append({'id': sub_track.get('id')})

    payload['documents'] = []
    for document in details.get('documents') or []:
        document_payload = {}
        if document.get('id'):
            document_payload['id'] = document.get('id')
        if document.get('external_id'):
            document_payload['external_id'] = document.get('external_id')
        if document_payload:
            payload['documents'].append(document_payload)

    content = details.get('content_experience')
    if content:
        payload['content_experience'] = {
            'type': content.get('type'),
            'pre_content_offset': content.get('pre_content_offset'),
            'post_content_offset': content.get('post_content_offset'),
            'pre_content': content.get('pre_content'),
            'post_content': content.get('post_content'),
            'main_content': content.get('main_content'),
            'external_id': content.get('external_id'),
        }
    else:
        payload['content_experience'] = None

    return payload


def _build_form_initial_data(payload):
    data = {
        'mode': 'ui',
        'core': {
            'name': payload.get('name'),
            'external_id': payload.get('external_id'),
            'description': payload.get('description'),
            'start_datetime': _to_form_datetime(payload.get('start_datetime')),
            'end_datetime': _to_form_datetime(payload.get('end_datetime')),
        },
        'accessibility': {
            'entity_type': '',
            'entity_ids': [],
        },
        'location': {
            'label': None,
            'map_location': {},
        },
        'chat': {
            'enabled': False,
        },
        'settings': {
            'aaq_enabled': False,
            'prevent_schedule_overlap': False,
            'engagement_order': [],
        },
        'external_links': [],
        'roles': [],
        'tracks': [],
        'sub_tracks': [],
        'documents': [],
        'content_experience': {
            'type': '',
            'pre_content_offset': payload.get('content_experience', {}).get('pre_content_offset') if payload.get('content_experience') else None,
            'post_content_offset': payload.get('content_experience', {}).get('post_content_offset') if payload.get('content_experience') else None,
            'pre_content_json': '',
            'post_content_json': '',
            'main_content_json': '',
            'external_id': payload.get('content_experience', {}).get('external_id') if payload.get('content_experience') else None,
        },
    }

    accessibility = payload.get('accessibility') or {}
    data['accessibility']['entity_type'] = accessibility.get('entity_type') or ''
    data['accessibility']['entity_ids'] = [
        {'value': value} for value in accessibility.get('entity_ids', [])
    ]

    location = payload.get('location') or {}
    data['location']['label'] = location.get('label')
    map_location = location.get('map_location') or {}
    data['location']['map_location'] = {
        'map_id': map_location.get('map_id'),
        'label': map_location.get('label'),
        'latitude': map_location.get('latitude'),
        'longitude': map_location.get('longitude'),
        'floor': map_location.get('floor'),
    }

    chat = payload.get('chat') or {}
    data['chat']['enabled'] = bool(chat.get('enabled', False))

    settings = payload.get('settings') or {}
    data['settings']['aaq_enabled'] = bool(settings.get('aaq_enabled', False))
    data['settings']['prevent_schedule_overlap'] = bool(settings.get('prevent_schedule_overlap', False))
    data['settings']['engagement_order'] = [
        {'value': value} for value in settings.get('engagement_order', [])
    ]

    data['external_links'] = payload.get('external_links') or []

    for role in payload.get('roles') or []:
        identifier_type = next((key for key in ('id', 'external_id', 'type', 'name') if key in role), 'id')
        data['roles'].append(
            {
                'identifier_type': identifier_type,
                'identifier_value': role.get(identifier_type),
                'people': [
                    {'id': person.get('id'), 'external_id': person.get('external_id')}
                    for person in role.get('people', [])
                ],
            }
        )

    data['tracks'] = payload.get('tracks') or []
    data['sub_tracks'] = payload.get('sub_tracks') or []
    data['documents'] = payload.get('documents') or []

    content = payload.get('content_experience') or {}
    if content.get('type'):
        data['content_experience']['type'] = content.get('type')
    if content.get('pre_content') is not None:
        data['content_experience']['pre_content_json'] = json.dumps(content.get('pre_content'), indent=2, sort_keys=True)
    if content.get('post_content') is not None:
        data['content_experience']['post_content_json'] = json.dumps(content.get('post_content'), indent=2, sort_keys=True)
    if content.get('main_content') is not None:
        data['content_experience']['main_content_json'] = json.dumps(content.get('main_content'), indent=2, sort_keys=True)

    return data


def _collect_string_list(field):
    values = []
    for entry in field:
        entry_form = _ff(entry)
        value_field = getattr(entry_form, 'value', None)
        if value_field is not None and value_field.data:
            values.append(value_field.data)
    return values


def _build_payload_from_form(form):
    payload = {}
    errors = False

    core = _ff(form.core)
    payload['name'] = core.name.data
    payload['external_id'] = core.external_id.data or None
    payload['description'] = core.description.data or None
    payload['start_datetime'] = _to_iso_string(core.start_datetime.data)
    payload['end_datetime'] = _to_iso_string(core.end_datetime.data)

    accessibility = _ff(form.accessibility)
    entity_type = getattr(accessibility, 'entity_type').data or None
    entity_ids = _collect_string_list(accessibility.entity_ids)
    if entity_type or entity_ids:
        payload['accessibility'] = {
            'entity_type': entity_type,
            'entity_ids': entity_ids,
        }
    else:
        payload['accessibility'] = None

    location = _ff(form.location)
    map_location = _ff(location.map_location)
    location_payload = {}
    if location.label.data:
        location_payload['label'] = location.label.data
    map_payload = {}
    if map_location.map_id.data:
        map_payload['map_id'] = map_location.map_id.data
    if map_location.label.data:
        map_payload['label'] = map_location.label.data
    if map_location.latitude.data is not None:
        map_payload['latitude'] = float(map_location.latitude.data)
    if map_location.longitude.data is not None:
        map_payload['longitude'] = float(map_location.longitude.data)
    if map_location.floor.data:
        map_payload['floor'] = map_location.floor.data
    if map_payload:
        location_payload['map_location'] = map_payload
    payload['location'] = location_payload if location_payload else None

    chat = _ff(form.chat)
    payload['chat'] = None
    if chat.enabled.data is not None:
        payload['chat'] = {'enabled': bool(chat.enabled.data)}

    settings = _ff(form.settings)
    payload['settings'] = {
        'aaq_enabled': bool(settings.aaq_enabled.data),
        'prevent_schedule_overlap': bool(settings.prevent_schedule_overlap.data),
        'engagement_order': _collect_string_list(settings.engagement_order),
    }

    links = []
    for entry in form.external_links:
        entry_form = _ff(entry)
        if entry_form.remove.data:
            continue
        link_data = {}
        if entry_form.id.data:
            link_data['id'] = entry_form.id.data
        if entry_form.name.data:
            link_data['name'] = entry_form.name.data
        if entry_form.link.data:
            link_data['link'] = entry_form.link.data
        if entry_form.order.data is not None:
            link_data['order'] = entry_form.order.data
        if link_data:
            links.append(link_data)
    payload['external_links'] = links

    roles = []
    for entry in form.roles:
        role_form = _ff(entry)
        if role_form.remove.data:
            continue
        identifier_value = role_form.identifier_value.data
        if not identifier_value:
            continue
        role_data = {role_form.identifier_type.data: identifier_value}
        people = []
        for person_entry in role_form.people:
            person_form = _ff(person_entry)
            if person_form.remove.data:
                continue
            person_data = {}
            if person_form.id.data:
                person_data['id'] = person_form.id.data
            if person_form.external_id.data:
                person_data['external_id'] = person_form.external_id.data
            if person_data:
                people.append(person_data)
        role_data['people'] = people
        roles.append(role_data)
    payload['roles'] = roles

    tracks = []
    for entry in form.tracks:
        t_form = _ff(entry)
        if t_form.remove.data:
            continue
        if t_form.id.data:
            tracks.append({'id': t_form.id.data})
    payload['tracks'] = tracks

    sub_tracks = []
    for entry in form.sub_tracks:
        st_form = _ff(entry)
        if st_form.remove.data:
            continue
        if st_form.id.data:
            sub_tracks.append({'id': st_form.id.data})
    payload['sub_tracks'] = sub_tracks

    documents = []
    for entry in form.documents:
        d_form = _ff(entry)
        if d_form.remove.data:
            continue
        document_data = {}
        if d_form.id.data:
            document_data['id'] = d_form.id.data
        if d_form.external_id.data:
            document_data['external_id'] = d_form.external_id.data
        if document_data:
            documents.append(document_data)
    payload['documents'] = documents

    content_payload = None
    content_form = _ff(form.content_experience)
    if (
        content_form.type.data
        or content_form.pre_content_offset.data is not None
        or content_form.post_content_offset.data is not None
        or content_form.pre_content_json.data
        or content_form.post_content_json.data
        or content_form.main_content_json.data
        or content_form.external_id.data
    ):
        content_payload = {
            'type': content_form.type.data or None,
            'pre_content_offset': content_form.pre_content_offset.data,
            'post_content_offset': content_form.post_content_offset.data,
            'external_id': content_form.external_id.data or None,
        }

        for field_name, field in (
            ('pre_content', content_form.pre_content_json),
            ('post_content', content_form.post_content_json),
            ('main_content', content_form.main_content_json),
        ):
            raw_value = field.data.strip() if field.data else ''
            if raw_value:
                try:
                    content_payload[field_name] = json.loads(raw_value)
                except json.JSONDecodeError as exc:
                    field.errors.append(f'Invalid JSON: {exc}')
                    errors = True
            else:
                content_payload[field_name] = None

    payload['content_experience'] = content_payload

    return payload, errors


def _diff_payload(initial, current):
    if initial is None and current is None:
        return None

    if isinstance(current, dict):
        initial = initial or {}
        result = {}
        for key, value in current.items():
            diff_value = _diff_payload(initial.get(key), value)
            if diff_value is not None:
                result[key] = diff_value
        for key in set(initial.keys()) - set(current.keys()):
            result[key] = None
        return result or None

    if isinstance(current, list):
        initial = initial or []
        if current != initial:
            return current
        return None

    if current != initial:
        return current

    return None

@expert_session_editor.route('/select_session', methods=['GET', 'POST'])
def select_session():
    event_id = session.get('event_id')
    if not event_id:
        return redirect(url_for('main.index'))

    sessions = fetch_sessions(event_id)
    form = SessionForm()
    form.session.choices = [(session['id'], session['name']) for session in sessions]

    if form.validate_on_submit():
        session['session_id'] = form.session.data
        return redirect(url_for('expert_session_editor.edit_session'))
    
    return render_template('expert_session_editor/select_session.html', form=form, event_name=session.get('event_name'))

@expert_session_editor.route('/edit_session', methods=['GET', 'POST'])
def edit_session():
    event_id = session.get('event_id')
    session_id = session.get('session_id')
    if not event_id or not session_id:
        return redirect(url_for('main.index'))

    session_details = fetch_session_details(event_id, session_id)
    if not session_details:
        flash('Unable to load session details. Please try again.', 'error')
        return redirect(url_for('expert_session_editor.select_session'))

    canonical_payload = _build_canonical_payload(session_details)
    initial_payload_json = json.dumps(canonical_payload, sort_keys=True, default=_json_default)

    if request.method == 'POST':
        form = EditSessionForm()
        _prepare_dynamic_lists(form, add_extra=False)
        if form.validate_on_submit():
            try:
                initial_payload = json.loads(form.initial_payload.data or '{}')
            except json.JSONDecodeError:
                initial_payload = {}

            mode = form.mode.data or 'ui'
            if mode == 'raw':
                raw_value = form.raw_payload.data or ''
                if not raw_value.strip():
                    form.raw_payload.errors.append('Provide JSON to update when using Raw mode.')
                    return render_template('expert_session_editor/edit_session.html', form=form, event_name=session.get('event_name'))
                try:
                    current_payload = json.loads(raw_value)
                except json.JSONDecodeError as exc:
                    form.raw_payload.errors.append(f'Invalid JSON: {exc}')
                    return render_template('expert_session_editor/edit_session.html', form=form, event_name=session.get('event_name'))
            else:
                current_payload, payload_errors = _build_payload_from_form(form)
                if payload_errors:
                    return render_template('expert_session_editor/edit_session.html', form=form, event_name=session.get('event_name'))

            diff_payload = _diff_payload(initial_payload, current_payload)
            if not diff_payload:
                flash('No changes detected.', 'info')
                return redirect(url_for('expert_session_editor.edit_session'))

            response = update_session(event_id, session_id, diff_payload)
            if response and response.get('errors'):
                for error in response['errors']:
                    flash(error.get('message', 'Unknown error'), 'error')
                return render_template('expert_session_editor/edit_session.html', form=form, event_name=session.get('event_name'))

            flash('Session updated successfully!', 'success')
            log_action('expert_session_editor', event_id)
            return redirect(url_for('expert_session_editor.select_session'))
    else:
        form_data = _build_form_initial_data(canonical_payload)
        form = EditSessionForm(data=form_data)
        form.initial_payload.data = initial_payload_json
        form.raw_payload.data = json.dumps(canonical_payload, indent=2, sort_keys=True, default=_json_default)
        _prepare_dynamic_lists(form, add_extra=True)

    return render_template('expert_session_editor/edit_session.html', form=form, event_name=session.get('event_name'))