from flask import render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import login_required
from wtforms import SelectField, SubmitField
from flask_wtf import FlaskForm
from . import attendee_list
from .services import fetch_sessions, fetch_session_attendees, fetch_session_detail
from datetime import datetime
from app.utils import get_api_client


class SessionSelectForm(FlaskForm):
    session_id = SelectField('Session', choices=[], validate_choice=False)
    submit = SubmitField('Show Attendees')


@attendee_list.route('/', methods=['GET', 'POST'])
@login_required
def select_session():
    if not session.get('event_id'):
        return redirect(url_for('main.select_event'))

    sessions = fetch_sessions()
    form = SessionSelectForm()
    def fmt_dt(value: str) -> str:
        if not value:
            return ''
        try:
            # Handle ISO strings with timezone
            # Replace Z with +00:00 for fromisoformat compatibility
            v = value.replace('Z', '+00:00')
            dt = datetime.fromisoformat(v)
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return value

    choices = []
    for s in sessions:
        title = s.get('title') or s.get('name') or f"Session {s.get('id')}"
        start_dt = s.get('start_datetime') or s.get('start_time') or ''
        label = f"{title} — {fmt_dt(start_dt)}" if start_dt else title
        choices.append((str(s['id']), label))
    form.session_id.choices = choices

    if request.method == 'POST':
        selected = request.form.get('session_id')
        if not selected:
            flash('Please select a session', 'error')
        else:
            return redirect(url_for('attendee_list.list_attendees', session_id=selected))

    return render_template('attendee_list/select_session.html', form=form, event_name=session.get('event_name'))


@attendee_list.route('/list')
@login_required
def list_attendees():
    if not session.get('event_id'):
        return redirect(url_for('main.select_event'))
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect(url_for('attendee_list.select_session'))
    attendees = fetch_session_attendees(session_id)
    return render_template('attendee_list/list.html', attendees=attendees, session_id=session_id, event_name=session.get('event_name'))


@attendee_list.route('/print')
@login_required
def print_attendees():
    if not session.get('event_id'):
        return redirect(url_for('main.select_event'))
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect(url_for('attendee_list.select_session'))
    attendees = fetch_session_attendees(session_id)
    sess = fetch_session_detail(session_id)
    # Map session fields
    session_name = sess.get('title') or sess.get('name') or f"Session {session_id}"
    room = sess.get('room') or sess.get('location') or sess.get('room_name') or ''
    start_dt = sess.get('start_datetime') or sess.get('start_time') or ''
    end_dt = sess.get('end_datetime') or sess.get('end_time') or ''
    return render_template(
        'attendee_list/print.html',
        attendees=attendees,
        event_name=session.get('event_name'),
        session_name=session_name,
        room=room,
        start_dt=start_dt,
        end_dt=end_dt
    )

@attendee_list.route('/debug')
@login_required
def debug_probe():
    if not session.get('event_id'):
        return redirect(url_for('main.select_event'))
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400
    client = get_api_client()
    if not client:
        return jsonify({'success': False, 'error': 'No API client'}), 400
    report = client.probe_session_attendance(session.get('event_id'), session_id)
    return jsonify({'success': True, 'report': report})

