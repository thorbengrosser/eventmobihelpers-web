from flask import session, render_template, redirect, url_for, flash
from . import delete_sessions_group
from .forms import APIKeyForm, EventForm, TrackForm
from .services import fetch_events, fetch_sessions_by_track, delete_session, fetch_tracks
import concurrent.futures
from app.utils import log_action

@delete_sessions_group.route('/api_key', methods=['GET', 'POST'])
def api_key():
    form = APIKeyForm()
    if form.validate_on_submit():
        session['api_key'] = form.api_key.data
        return redirect(url_for('delete_sessions_group.select_event'))
    return render_template('delete_sessions_group/api_key.html', form=form)

@delete_sessions_group.route('/select_event', methods=['GET', 'POST'])
def select_event():
    api_key = session.get('api_key')
    if not api_key:
        return redirect(url_for('delete_sessions_group.api_key'))

    events = fetch_events(api_key)
    if not events:
        flash('Failed to fetch events. Please check your API key.')
        return redirect(url_for('delete_sessions_group.api_key'))

    form = EventForm()
    form.event.choices = [(event['id'], event['name']) for event in events]
    if form.validate_on_submit():
        session['event_id'] = form.event.data
        return redirect(url_for('delete_sessions_group.select_track'))
    
    return render_template('delete_sessions_group/select_event.html', form=form)

@delete_sessions_group.route('/select_track', methods=['GET', 'POST'])
@delete_sessions_group.route('/select_track', methods=['GET', 'POST'])
def select_track():
    api_key = session.get('api_key')
    event_id = session.get('event_id')
    print("API Key in session:", api_key)
    print("Event ID in session:", event_id)

    if not api_key or not event_id:
        return redirect(url_for('delete_sessions_group.api_key'))

    # Fetch the tracks first
    tracks = fetch_tracks(api_key, event_id)
    if not tracks:
        flash('No tracks found for the selected event. Please select another event.', 'warning')
        return redirect(url_for('delete_sessions_group.select_event'))

    form = TrackForm()
    form.track.choices = [(track['id'], track['name']) for track in tracks]

    if form.validate_on_submit():
        track_id_to_delete = form.track.data
        sessions_to_delete = fetch_sessions_by_track(api_key, event_id, track_id_to_delete)
        if not sessions_to_delete:
            flash('No sessions found for the selected track.')
            return redirect(url_for('delete_sessions_group.select_event'))

        # Proceed to delete the sessions
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(delete_session, api_key, event_id, session_item['id']) for session_item in sessions_to_delete]
            for future in concurrent.futures.as_completed(futures):
                session_id, status_code = future.result()
                if status_code == 204:
                    flash(f"Session {session_id} deleted successfully.", 'success')
                else:
                    flash(f"Failed to delete session {session_id}. Status code: {status_code}", 'danger')
        log_action('delete_sessions_group', event_id)
        return redirect(url_for('delete_sessions_group.delete_complete'))

    return render_template('delete_sessions_group/select_track.html', form=form)


@delete_sessions_group.route('/delete_sessions_group/delete_complete')
def delete_complete():
    
    return render_template('delete_sessions_group/delete_complete.html')
