from flask import session, render_template, redirect, url_for, flash
from . import delete_sessions_group
from .forms import TrackForm
from .services import fetch_sessions_by_track, delete_session, fetch_tracks
import concurrent.futures
from app.utils import log_action, get_api_key

@delete_sessions_group.route('/select_track', methods=['GET', 'POST'])
def select_track():
    api_key = get_api_key()
    event_id = session.get('event_id')
    if not api_key or not event_id:
        return redirect(url_for('main.index'))

    tracks = fetch_tracks(api_key, event_id)
    if not tracks:
        flash('No tracks found for the selected event. Please select another event.', 'warning')
        return redirect(url_for('main.index'))

    form = TrackForm()
    form.track.choices = [(track['id'], track['name']) for track in tracks]

    if form.validate_on_submit():
        track_id_to_delete = form.track.data
        sessions_to_delete = fetch_sessions_by_track(api_key, event_id, track_id_to_delete)
        if not sessions_to_delete:
            flash('No sessions found for the selected track.')
            return redirect(url_for('main.index'))

        # Proceed to delete the sessions
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(delete_session, api_key, event_id, session_item['id']) for session_item in sessions_to_delete]
            for future in concurrent.futures.as_completed(futures):
                session_id, status_code = future.result()
                if status_code in [200, 204]:
                    flash(f"Session {session_id} deleted successfully.", 'success')
                else:
                    flash(f"Failed to delete session {session_id}. Status code: {status_code}", 'danger')
        log_action('delete_sessions_group', event_id)
        return redirect(url_for('main.index'))

    return render_template('delete_sessions_group/select_track.html', form=form, event_name=session.get('event_name'))

@delete_sessions_group.route('/logout')
def logout():
    clear_api_key()
    return redirect(url_for('delete_sessions_group.api_key'))

@delete_sessions_group.route('/delete_sessions_group/delete_complete')
def delete_complete():
    
    return render_template('delete_sessions_group/delete_complete.html', event_name=session.get('event_name'))
