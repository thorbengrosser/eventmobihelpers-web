from flask import render_template, redirect, url_for, flash, session, request, jsonify
from . import add_people_to_group
from .forms import GroupForm, EmailForm
from .services import fetch_groups, fetch_person_by_email, update_person_groups
from app.utils import log_action
import logging
import re
import uuid
import time

logger = logging.getLogger(__name__)

# In-memory storage for email batches and results (to avoid cookie size limits)
# In production, consider using Redis or a database
_email_batches = {}
_results_cache = {}
_batch_cleanup_time = 3600  # Clean up batches after 1 hour

def parse_emails(email_text):
    # Split by newlines, commas, semicolons, or spaces
    # Remove empty strings and strip whitespace
    emails = re.split(r'[,\s;]+', email_text)
    return [email.strip() for email in emails if email.strip()]

@add_people_to_group.route('/select_group', methods=['GET', 'POST'])
def select_group():
    event_id = session.get('event_id')
    if not event_id:
        logger.warning("Missing event_id, redirecting to index")
        return redirect(url_for('main.index'))

    groups = fetch_groups(event_id)
    logger.debug(f"Fetched groups: {groups}")
    form = GroupForm()
    form.group.choices = [(group['id'], group['name']) for group in groups]

    if form.validate_on_submit():
        logger.debug(f"Selected group: {form.group.data}")
        session['group_id'] = form.group.data
        return redirect(url_for('add_people_to_group.add_people'))
    
    return render_template('add_people_to_group/select_group.html', form=form, event_name=session.get('event_name'))

def _cleanup_old_batches():
    """Remove batches and results older than the cleanup time."""
    current_time = time.time()
    # Clean up old batches
    to_remove = [bid for bid, data in _email_batches.items() 
                 if current_time - data['created_at'] > _batch_cleanup_time]
    for bid in to_remove:
        del _email_batches[bid]
        logger.debug(f"Cleaned up old batch {bid}")
    # Clean up old results
    to_remove_results = [rid for rid, data in _results_cache.items() 
                         if current_time - data['created_at'] > _batch_cleanup_time]
    for rid in to_remove_results:
        del _results_cache[rid]
        logger.debug(f"Cleaned up old results {rid}")

@add_people_to_group.route('/add_people', methods=['GET', 'POST'])
def add_people():
    event_id = session.get('event_id')
    group_id = session.get('group_id')
    logger.debug(f"Current session state - event_id: {event_id}, group_id: {group_id}")
    
    if not event_id or not group_id:
        logger.warning("Missing event_id or group_id, redirecting to index")
        return redirect(url_for('main.index'))

    form = EmailForm()
    if form.validate_on_submit():
        email_text = form.email.data
        emails = parse_emails(email_text)
        logger.debug(f"Parsed {len(emails)} emails")
        
        # Store emails in server-side cache instead of session (to avoid cookie size limits)
        batch_id = str(uuid.uuid4())
        _email_batches[batch_id] = {
            'emails': emails,
            'results': [],
            'created_at': time.time(),
            'group_id': group_id,
            'event_id': event_id
        }
        # Only store the batch ID in session (small)
        session['email_batch_id'] = batch_id
        session.modified = True
        logger.debug(f"Stored {len(emails)} emails in batch {batch_id} (not in session)")
        
        # Clean up old batches
        _cleanup_old_batches()
        
        # For small batches (< 50), process immediately
        if len(emails) < 50:
            # Fetch all groups for the event so we can look up external_id and other fields
            all_groups = fetch_groups(event_id) or []
            all_groups_dict = {g['id']: g for g in all_groups if 'id' in g}
            
            results = []
            success_count = 0
            error_count = 0
            not_found_count = 0

            for email in emails:
                logger.debug(f"Attempting to add person with email: {email}")
                person = fetch_person_by_email(event_id, email)
                if person:
                    logger.debug(f"Found person: {person}")
                    # Get current group objects
                    current_groups = person.get('groups', [])
                    current_group_ids = {g['id'] for g in current_groups if 'id' in g}
                    # Add the selected group if not already present
                    updated_group_ids = set(current_group_ids)
                    updated_group_ids.add(group_id)
                    # Build group objects with id and external_id (and optionally name/type)
                    updated_group_objs = []
                    for gid in updated_group_ids:
                        group_obj = all_groups_dict.get(gid)
                        if group_obj and group_obj.get('external_id') is not None:
                            updated_group_objs.append({
                                'id': group_obj['id'],
                                'external_id': group_obj['external_id']
                            })
                    status_code, response = update_person_groups(event_id, person['id'], updated_group_objs)
                    logger.debug(f"Update response - status: {status_code}, body: {response}")
                    if status_code == 200:
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
                            'error': f'Failed to update groups (status: {status_code})'
                        })
                        logger.error(f"Failed to update groups. Status: {status_code}, Response: {response}")
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
            log_action('add_people_to_group', event_id)
            
            # Store results in server-side cache instead of session (to avoid cookie size limits)
            results_id = str(uuid.uuid4())
            _results_cache[results_id] = {
                'results': results,
                'created_at': time.time()
            }
            session['results_id'] = results_id
            # Clean up the batch since we processed it immediately
            del _email_batches[batch_id]
            session.pop('email_batch_id', None)
            session.modified = True
            return redirect(url_for('add_people_to_group.result'))
        else:
            # For large batches, redirect to processing page
            return redirect(url_for('add_people_to_group.process_batch'))

    return render_template('add_people_to_group/add_people.html', form=form, event_name=session.get('event_name'))

@add_people_to_group.route('/process_batch', methods=['GET'])
def process_batch():
    """Show the batch processing page that will process emails via AJAX."""
    batch_id = session.get('email_batch_id')
    if not batch_id:
        flash('No batch to process', 'warning')
        return redirect(url_for('add_people_to_group.select_group'))
    
    batch_data = _email_batches.get(batch_id)
    if not batch_data:
        flash('Batch expired or not found', 'warning')
        return redirect(url_for('add_people_to_group.select_group'))
    
    emails = batch_data['emails']
    return render_template('add_people_to_group/process_batch.html', 
                         total_emails=len(emails),
                         event_name=session.get('event_name'))

@add_people_to_group.route('/process_emails_batch', methods=['POST'])
def process_emails_batch():
    """Process a batch of emails via AJAX to avoid timeout."""
    logger.info("process_emails_batch route called")
    
    try:
        request_data = request.get_json() if request.is_json else {}
        logger.info(f"Request JSON: {request_data}")
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")
        request_data = {}
    
    event_id = session.get('event_id')
    
    # Get batch from server-side storage instead of session
    batch_id = session.get('email_batch_id')
    if not batch_id:
        logger.error("No batch_id in session")
        return jsonify({'error': 'No batch ID found. Session may have expired.'}), 400
    
    batch_data = _email_batches.get(batch_id)
    if not batch_data:
        logger.error(f"Batch {batch_id} not found in storage")
        return jsonify({'error': 'Batch not found. It may have expired.'}), 400
    
    emails = batch_data['emails']
    group_id = batch_data['group_id']
    event_id = batch_data['event_id']
    
    logger.debug(f"Emails in batch: {len(emails) if emails else 0}")
    
    if not emails:
        logger.error("No emails found in batch")
        return jsonify({'error': 'No emails to process.'}), 400
    
    # Get batch parameters
    batch_size = request_data.get('batch_size', 10)
    start_index = request_data.get('start_index', 0)
    logger.info(f"Processing batch - start_index: {start_index}, batch_size: {batch_size}")
    
    # Fetch all groups for the event (only once, could be cached but keeping it simple)
    all_groups = fetch_groups(event_id) or []
    all_groups_dict = {g['id']: g for g in all_groups if 'id' in g}
    
    # Process this batch
    batch_emails = emails[start_index:start_index + batch_size]
    results = []
    
    for email in batch_emails:
        logger.debug(f"Processing email: {email}")
        person = fetch_person_by_email(event_id, email)
        if person:
            logger.debug(f"Found person: {person}")
            # Get current group objects
            current_groups = person.get('groups', [])
            current_group_ids = {g['id'] for g in current_groups if 'id' in g}
            # Add the selected group if not already present
            updated_group_ids = set(current_group_ids)
            updated_group_ids.add(group_id)
            # Build group objects with id and external_id
            updated_group_objs = []
            for gid in updated_group_ids:
                group_obj = all_groups_dict.get(gid)
                if group_obj and group_obj.get('external_id') is not None:
                    updated_group_objs.append({
                        'id': group_obj['id'],
                        'external_id': group_obj['external_id']
                    })
            status_code, response = update_person_groups(event_id, person['id'], updated_group_objs)
            logger.debug(f"Update response - status: {status_code}, body: {response}")
            if status_code == 200:
                results.append({
                    'email': email,
                    'success': True,
                    'error': None
                })
            else:
                results.append({
                    'email': email,
                    'success': False,
                    'error': f'Failed to update groups (status: {status_code})'
                })
        else:
            logger.warning(f"No person found with email: {email}")
            results.append({
                'email': email,
                'success': False,
                'error': 'Person not found'
            })
    
    # Update batch results in server-side storage
    batch_data['results'].extend(results)
    
    # Check if we're done
    next_index = start_index + len(batch_emails)
    is_complete = next_index >= len(emails)
    
    logger.debug(f"Batch processed: {len(batch_emails)} emails, next_index: {next_index}, complete: {is_complete}")
    
    if is_complete:
        log_action('add_people_to_group', event_id)
        # Store results in server-side cache instead of session (to avoid cookie size limits)
        results_id = str(uuid.uuid4())
        _results_cache[results_id] = {
            'results': batch_data['results'],
            'created_at': time.time()
        }
        # Only store the results ID in session (small)
        session['results_id'] = results_id
        # Clean up batch from server-side storage
        del _email_batches[batch_id]
        session.pop('email_batch_id', None)
        session.modified = True
        logger.debug(f"Completed batch {batch_id}, stored results in {results_id}")
    
    return jsonify({
        'results': results,
        'processed': next_index,
        'total': len(emails),
        'complete': is_complete,
        'next_index': next_index if not is_complete else None
    })

@add_people_to_group.route('/result', methods=['GET'])
def result():
    """Display results of adding people to group."""
    # Get results from server-side cache instead of session
    results_id = session.get('results_id')
    if not results_id:
        flash('No results to display', 'warning')
        return redirect(url_for('add_people_to_group.select_group'))
    
    results_data = _results_cache.get(results_id)
    if not results_data:
        flash('Results expired or not found', 'warning')
        session.pop('results_id', None)
        return redirect(url_for('add_people_to_group.select_group'))
    
    results = results_data['results']
    if not results:
        flash('No results to display', 'warning')
        session.pop('results_id', None)
        del _results_cache[results_id]
        return redirect(url_for('add_people_to_group.select_group'))
    
    # Calculate summary statistics
    total = len(results)
    success_count = sum(1 for r in results if r.get('success'))
    error_count = total - success_count
    
    # Clean up results from cache and session after displaying
    del _results_cache[results_id]
    session.pop('results_id', None)
    session.modified = True
    
    return render_template('add_people_to_group/result.html', 
                         results=results, 
                         event_name=session.get('event_name'),
                         total=total,
                         success_count=success_count,
                         error_count=error_count)
