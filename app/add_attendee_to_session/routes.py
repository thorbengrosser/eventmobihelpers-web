from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .forms import SelectSessionForm, EnterEmailsForm
from app.attendee_list.services import fetch_sessions
from datetime import datetime

add_attendee_to_session = Blueprint('add_attendee_to_session', __name__)

@add_attendee_to_session.route('/', methods=['GET', 'POST'])
def select_session():
    if not session.get('event_id'):
        return redirect(url_for('main.select_event'))
    form = SelectSessionForm()
    sessions = fetch_sessions()
    def fmt_dt(value: str) -> str:
        if not value:
            return ''
        try:
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
    form.session.choices = choices
    if request.method == 'POST':
        selected = request.form.get('session')
        if not selected:
            flash('Please select a session', 'error')
        else:
            session['selected_session_id'] = selected
            return redirect(url_for('add_attendee_to_session.enter_emails'))
    return render_template('add_attendee_to_session/select_session.html', form=form, event_name=session.get('event_name'))

@add_attendee_to_session.route('/enter_emails', methods=['POST', 'GET'])
def enter_emails():
    if not session.get('event_id'):
        return redirect(url_for('main.select_event'))
    form = EnterEmailsForm()
    return render_template('add_attendee_to_session/enter_emails.html', form=form, event_name=session.get('event_name'))

@add_attendee_to_session.route('/result', methods=['POST'])
def result():
    # TODO: Implement result display logic
    return render_template('add_attendee_to_session/result.html') 