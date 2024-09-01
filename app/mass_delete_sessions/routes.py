from flask import render_template, redirect, url_for, session, flash, request
from . import mass_delete_sessions
from .forms import APIKeyForm, EventForm, SessionIDsForm
from .services import fetch_events, get_session_uuid, delete_session
import asyncio
import aiohttp

@mass_delete_sessions.route('/api_key', methods=['GET', 'POST'])
def api_key():
    form = APIKeyForm()
    if form.validate_on_submit():
        session['api_key'] = form.api_key.data
        return redirect(url_for('mass_delete_sessions.select_event'))
    return render_template('mass_delete_sessions/api_key.html', form=form)

@mass_delete_sessions.route('/select_event', methods=['GET', 'POST'])
def select_event():
    api_key = session.get('api_key')
    if not api_key:
        return redirect(url_for('mass_delete_sessions.api_key'))

    # Fetch events using the API
    events = fetch_events(api_key)

    # Populate the form's SelectField with event choices
    form = EventForm()
    form.event.choices = [(event['id'], event['name']) for event in events]

    if form.validate_on_submit():
        session['event_id'] = form.event.data
        return redirect(url_for('mass_delete_sessions.delete_sessions'))
    
    return render_template('mass_delete_sessions/select_event.html', form=form)


@mass_delete_sessions.route('/delete_sessions', methods=['GET', 'POST'])
def delete_sessions():
    api_key = session.get('api_key')
    event_id = session.get('event_id')
    if not api_key or not event_id:
        return redirect(url_for('mass_delete_sessions.api_key'))

    form = SessionIDsForm()

    if form.validate_on_submit():
        session_ids = form.session_ids.data.split(',')
        session_ids = [sid.strip() for sid in session_ids if sid.strip()]

        errors = []  # List to collect errors for sessions that could not be deleted

        # Define the async function to delete all sessions
        async def delete_all_sessions():
            async with aiohttp.ClientSession() as session:
                for session_external_id in session_ids:
                    uuid = get_session_uuid(api_key, event_id, session_external_id)
                    if uuid:
                        response = await delete_session(session, event_id, uuid, api_key)
                        if response.get('errors'):
                            errors.append(f"{session_external_id}")
                    else:
                        errors.append(f"{session_external_id}")

        # Run the async function
        asyncio.run(delete_all_sessions())

        # Flash success or error messages based on the result
        if errors:
            flash(f"Completed. The following sessions could not be deleted: {', '.join(errors)}", 'danger')
        else:
            flash("All sessions deleted successfully.", 'success')

        return redirect(url_for('mass_delete_sessions.delete_complete'))

    return render_template('mass_delete_sessions/delete_sessions.html', form=form)

@mass_delete_sessions.route('/delete_complete')
def delete_complete():
    return render_template('mass_delete_sessions/delete_complete.html')
