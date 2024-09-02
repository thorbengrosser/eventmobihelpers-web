from flask import render_template, redirect, url_for, session, flash, request
from . import expert_session_editor
from .forms import APIKeyForm, EventForm, SessionForm, EditSessionForm
from .services import fetch_events, fetch_sessions, fetch_session_details, update_session
from datetime import datetime


@expert_session_editor.route('/api_key', methods=['GET', 'POST'])
def api_key():
    form = APIKeyForm()
    if form.validate_on_submit():
        session['api_key'] = form.api_key.data
        return redirect(url_for('expert_session_editor.select_event'))
    return render_template('expert_session_editor/api_key.html', form=form)

@expert_session_editor.route('/select_event', methods=['GET', 'POST'])
def select_event():
    api_key = session.get('api_key')
    if not api_key:
        return redirect(url_for('expert_session_editor.api_key'))

    events = fetch_events(api_key)
    form = EventForm()
    form.event.choices = [(event['id'], event['name']) for event in events]

    if form.validate_on_submit():
        session['event_id'] = form.event.data
        return redirect(url_for('expert_session_editor.select_session'))
    
    return render_template('expert_session_editor/select_event.html', form=form)

@expert_session_editor.route('/select_session', methods=['GET', 'POST'])
def select_session():
    api_key = session.get('api_key')
    event_id = session.get('event_id')
    if not api_key or not event_id:
        return redirect(url_for('expert_session_editor.api_key'))

    sessions = fetch_sessions(api_key, event_id)
    form = SessionForm()
    form.session.choices = [(session['id'], session['name']) for session in sessions]

    if form.validate_on_submit():
        session['session_id'] = form.session.data
        return redirect(url_for('expert_session_editor.edit_session'))
    
    return render_template('expert_session_editor/select_session.html', form=form)

@expert_session_editor.route('/edit_session', methods=['GET', 'POST'])
def edit_session():
    api_key = session.get('api_key')
    event_id = session.get('event_id')
    session_id = session.get('session_id')
    if not api_key or not event_id or not session_id:
        return redirect(url_for('expert_session_editor.api_key'))

    session_details = fetch_session_details(api_key, event_id, session_id)

    # Convert string datetime fields to datetime objects
    if 'start_datetime' in session_details:
        session_details['start_datetime'] = datetime.fromisoformat(session_details['start_datetime'].replace('Z', '+00:00'))
    if 'end_datetime' in session_details:
        session_details['end_datetime'] = datetime.fromisoformat(session_details['end_datetime'].replace('Z', '+00:00'))

    # Check for 'chat' key and set chat_enabled
    if session_details.get('chat') is None:
        session_details['chat_enabled'] = 'false'
    else:
        session_details['chat_enabled'] = 'true' if session_details['chat'].get('enabled', False) else 'false'

    # Check for 'settings' and set aaq_enabled
    if session_details.get('settings') is None:
        session_details['aaq_enabled'] = 'false'
    else:
        session_details['aaq_enabled'] = 'true' if session_details['settings'].get('aaq_enabled', False) else 'false'

    form = EditSessionForm(data=session_details)
    if form.validate_on_submit():
        updated_data = {
            'name': form.name.data,
            'description': form.description.data,
            'start_datetime': form.start_datetime.data.isoformat(),
            'end_datetime': form.end_datetime.data.isoformat(),
            'chat': {
                'enabled': form.chat_enabled.data == 'true'
            },
            'settings': {
                'aaq_enabled': form.aaq_enabled.data == 'true'
            }
        }
        response = update_session(api_key, event_id, session_id, updated_data)
        flash(f"Session updated. Response: {response}", 'success')
        return redirect(url_for('expert_session_editor.edit_session'))

    return render_template('expert_session_editor/edit_session.html', form=form, session_details=session_details)