from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .forms import SelectSessionForm, EnterEmailsForm
from .services import fetch_person_by_email, add_session_to_personal_schedule
from app.attendee_list.services import fetch_sessions
from app.utils import get_api_key, log_action
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

add_attendee_to_session = Blueprint('add_attendee_to_session', __name__)

def parse_emails(email_text):
    """Parse emails from text, splitting by newlines, commas, semicolons, or spaces."""
    emails = re.split(r'[,\s;]+', email_text)
    return [email.strip() for email in emails if email.strip()]

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
    api_key = get_api_key()
    event_id = session.get('event_id')
    session_id = session.get('selected_session_id')
    
    if not api_key or not event_id:
        logger.warning("Missing api_key or event_id, redirecting to index")
        return redirect(url_for('main.index'))
    
    if not session_id:
        logger.warning("Missing selected_session_id, redirecting to select_session")
        flash('Please select a session first', 'error')
        return redirect(url_for('add_attendee_to_session.select_session'))
    
    form = EnterEmailsForm()
    if form.validate_on_submit():
        email_text = form.emails.data
        emails = parse_emails(email_text)
        logger.debug(f"Parsed {len(emails)} emails for session {session_id}")
        
        results = []
        success_count = 0
        error_count = 0
        not_found_count = 0
        
        for email in emails:
            logger.debug(f"Processing email: {email}")
            person = fetch_person_by_email(api_key, event_id, email)
            if person:
                person_id = person.get('id')
                logger.debug(f"Found person {person_id} for email {email}")
                success, error_msg = add_session_to_personal_schedule(api_key, event_id, person_id, session_id)
                if success:
                    results.append({
                        'email': email,
                        'success': True,
                        'error': None
                    })
                    success_count += 1
                else:
                    results.append({
                        'email': email,
                        'success': False,
                        'error': error_msg or 'Failed to add session'
                    })
                    error_count += 1
            else:
                logger.warning(f"No person found with email: {email}")
                results.append({
                    'email': email,
                    'success': False,
                    'error': 'Person not found'
                })
                not_found_count += 1
        
        logger.info(f"Processed {len(emails)} emails: {success_count} success, {error_count} errors, {not_found_count} not found")
        log_action('add_attendee_to_session', event_id)
        session['results'] = results
        return redirect(url_for('add_attendee_to_session.result'))
    
    return render_template('add_attendee_to_session/enter_emails.html', form=form, event_name=session.get('event_name'))

@add_attendee_to_session.route('/result', methods=['GET'])
def result():
    results = session.get('results', [])
    if not results:
        flash('No results to display', 'warning')
        return redirect(url_for('add_attendee_to_session.select_session'))
    
    # Calculate summary statistics
    total = len(results)
    success_count = sum(1 for r in results if r.get('success'))
    error_count = total - success_count
    
    # Clear results from session after displaying
    session.pop('results', None)
    
    return render_template('add_attendee_to_session/result.html', 
                         results=results, 
                         event_name=session.get('event_name'),
                         total=total,
                         success_count=success_count,
                         error_count=error_count) 