from flask import render_template, redirect, url_for, session, flash, request
from . import expert_session_editor
from .forms import SessionForm, EditSessionForm
from .services import fetch_sessions, fetch_session_details, update_session
from datetime import datetime
from app.utils import log_action, get_api_key

@expert_session_editor.route('/select_session', methods=['GET', 'POST'])
def select_session():
    api_key = get_api_key()
    event_id = session.get('event_id')
    if not api_key or not event_id:
        return redirect(url_for('main.index'))

    sessions = fetch_sessions(api_key, event_id)
    form = SessionForm()
    form.session.choices = [(session['id'], session['name']) for session in sessions]

    if form.validate_on_submit():
        session['session_id'] = form.session.data
        return redirect(url_for('expert_session_editor.edit_session'))
    
    return render_template('expert_session_editor/select_session.html', form=form, event_name=session.get('event_name'))

@expert_session_editor.route('/edit_session', methods=['GET', 'POST'])
def edit_session():
    api_key = get_api_key()
    event_id = session.get('event_id')
    session_id = session.get('session_id')
    if not api_key or not event_id or not session_id:
        return redirect(url_for('main.index'))

    session_details = fetch_session_details(api_key, event_id, session_id)
    print('DEBUG: Loaded session_details from API:', session_details)

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
        print('DEBUG: Form data to be saved:', form.data)
        response = update_session(api_key, event_id, session_id, form.data)
        print('DEBUG: API response from update_session:', response)
        if response and 'errors' in response and response['errors']:
            for error in response['errors']:
                flash(error.get('message', 'Unknown error'), 'error')
            # Re-render the form with the user's input and error messages
            return render_template('expert_session_editor/edit_session.html', form=form, event_name=session.get('event_name'))
        flash('Session updated successfully!', 'success')
        log_action('expert_session_editor', event_id)
        return redirect(url_for('expert_session_editor.select_session'))

    return render_template('expert_session_editor/edit_session.html', form=form, event_name=session.get('event_name'))