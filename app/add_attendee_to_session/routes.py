from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
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
    
    # Handle POST request first - if valid, redirect immediately without fetching sessions
    if request.method == 'POST':
        selected = request.form.get('session')
        if not selected:
            flash('Please select a session', 'error')
            # Fall through to render form with error (will fetch sessions below)
        else:
            session['selected_session_id'] = selected
            return redirect(url_for('add_attendee_to_session.enter_emails'))
    
    # Only fetch sessions when we need to render the form (GET or POST with error)
    sessions = fetch_sessions()
    
    # Deduplicate sessions by ID
    # Duplicates can occur because:
    # 1. Sessions may appear in multiple tracks, causing the API to return them multiple times
    # 2. Pagination might have edge cases where the same session appears on multiple pages
    # 3. The EventMobi API may return sessions multiple times if they have multiple relationships
    seen_ids = set()
    unique_sessions = []
    for s in sessions:
        session_id = s.get('id')
        if session_id and session_id not in seen_ids:
            seen_ids.add(session_id)
            unique_sessions.append(s)
        elif not session_id:
            # Include sessions without ID (shouldn't happen, but be safe)
            unique_sessions.append(s)
    
    # Sort sessions by start time, then by title for consistent ordering
    def get_sort_key(s):
        start_dt = s.get('start_datetime') or s.get('start_time') or ''
        title = s.get('title') or s.get('name') or ''
        try:
            if start_dt:
                v = start_dt.replace('Z', '+00:00')
                dt = datetime.fromisoformat(v)
                return (dt, title)
        except:
            pass
        return (datetime.min, title)
    
    unique_sessions.sort(key=get_sort_key)
    
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
    # Use a set to track choice IDs to prevent duplicates in the choices list itself
    seen_choice_ids = set()
    for s in unique_sessions:
        session_id = str(s.get('id', ''))
        if session_id and session_id not in seen_choice_ids:
            seen_choice_ids.add(session_id)
            title = s.get('title') or s.get('name') or f"Session {session_id}"
            start_dt = s.get('start_datetime') or s.get('start_time') or ''
            label = f"{title} — {fmt_dt(start_dt)}" if start_dt else title
            choices.append((session_id, label))
    form.session.choices = choices
    
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
        
        # Store emails in session for batch processing
        session['emails_to_process'] = emails
        session['processing_results'] = []
        session['processing_index'] = 0
        session.modified = True  # Ensure Flask saves the session
        logger.debug(f"Stored {len(emails)} emails in session for batch processing")
        
        # For small batches (< 50), process immediately
        if len(emails) < 50:
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
        else:
            # For large batches, redirect to processing page
            return redirect(url_for('add_attendee_to_session.process_batch'))
    
    return render_template('add_attendee_to_session/enter_emails.html', form=form, event_name=session.get('event_name'))

@add_attendee_to_session.route('/process_batch', methods=['GET'])
def process_batch():
    """Show the batch processing page that will process emails via AJAX."""
    emails = session.get('emails_to_process', [])
    if not emails:
        flash('No emails to process', 'warning')
        return redirect(url_for('add_attendee_to_session.select_session'))
    return render_template('add_attendee_to_session/process_batch.html', 
                         total_emails=len(emails),
                         event_name=session.get('event_name'))

@add_attendee_to_session.route('/process_emails_batch', methods=['POST'])
def process_emails_batch():
    """Process a batch of emails via AJAX to avoid timeout."""
    api_key = get_api_key()
    event_id = session.get('event_id')
    session_id = session.get('selected_session_id')
    
    logger.debug(f"Processing batch - event_id: {event_id}, session_id: {session_id}")
    logger.debug(f"Session keys: {list(session.keys())}")
    
    if not api_key or not event_id or not session_id:
        logger.error(f"Missing parameters - api_key: {bool(api_key)}, event_id: {event_id}, session_id: {session_id}")
        return jsonify({'error': 'Missing required parameters'}), 400
    
    emails = session.get('emails_to_process', [])
    logger.debug(f"Emails in session: {len(emails) if emails else 0}")
    
    if not emails:
        logger.error("No emails found in session")
        return jsonify({'error': 'No emails to process. Session may have expired.'}), 400
    
    # Get batch parameters
    batch_size = request.json.get('batch_size', 10)
    start_index = request.json.get('start_index', 0)
    
    # Process this batch
    batch_emails = emails[start_index:start_index + batch_size]
    results = []
    
    for email in batch_emails:
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
            else:
                results.append({
                    'email': email,
                    'success': False,
                    'error': error_msg or 'Failed to add session'
                })
        else:
            logger.warning(f"No person found with email: {email}")
            results.append({
                'email': email,
                'success': False,
                'error': 'Person not found'
            })
    
    # Update session with results
    if 'processing_results' not in session:
        session['processing_results'] = []
    session['processing_results'].extend(results)
    
    # Check if we're done
    next_index = start_index + len(batch_emails)
    is_complete = next_index >= len(emails)
    
    logger.debug(f"Batch processed: {len(batch_emails)} emails, next_index: {next_index}, complete: {is_complete}")
    
    if is_complete:
        log_action('add_attendee_to_session', event_id)
        session['results'] = session['processing_results']
        # Clean up processing data
        session.pop('emails_to_process', None)
        session.pop('processing_results', None)
        session.pop('processing_index', None)
    
    # Explicitly mark session as modified (Flask sessions need this)
    session.modified = True
    
    return jsonify({
        'results': results,
        'processed': next_index,
        'total': len(emails),
        'complete': is_complete,
        'next_index': next_index if not is_complete else None
    })

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