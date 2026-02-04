from flask import render_template, redirect, url_for, session, flash, request
from . import mass_delete_sessions
from .forms import SessionIDsForm
from .services import get_session_uuid, delete_session
from app.utils import log_action

@mass_delete_sessions.route('/delete_sessions', methods=['GET', 'POST'])
def delete_sessions():
    event_id = session.get('event_id')
    if not event_id:
        return redirect(url_for('main.index'))

    form = SessionIDsForm()
    if form.validate_on_submit():
        session_ids = form.session_ids.data.strip().split('\n')
        session_ids = [sid.strip() for sid in session_ids if sid.strip()]
        
        if not session_ids:
            flash('Please enter at least one session ID.', 'error')
            return redirect(url_for('mass_delete_sessions.delete_sessions'))

        # Process the session IDs (can be external_id or session id)
        for session_id in session_ids:
            try:
                uuid = get_session_uuid(event_id, session_id)
                if not uuid:
                    uuid = session_id  # Assume user pasted actual session id
                status_code = delete_session(event_id, uuid)
                if status_code in (200, 202, 204):
                    flash(f"Session {session_id} deleted successfully.", 'success')
                else:
                    flash(f"Failed to delete session {session_id}. Status code: {status_code}", 'danger')
            except Exception as e:
                flash(f"Error processing session {session_id}: {str(e)}", 'danger')

        log_action('mass_delete_sessions', event_id)
        return redirect(url_for('mass_delete_sessions.delete_sessions'))

    return render_template('mass_delete_sessions/delete_sessions.html', form=form, event_name=session.get('event_name'))
