from flask import render_template, redirect, url_for, flash, session
from . import add_people_to_group
from .forms import GroupForm, EmailForm
from .services import fetch_groups, fetch_person_by_email, update_person_groups
from app.utils import log_action, get_api_key
import logging
import re

logger = logging.getLogger(__name__)

def parse_emails(email_text):
    # Split by newlines, commas, semicolons, or spaces
    # Remove empty strings and strip whitespace
    emails = re.split(r'[,\s;]+', email_text)
    return [email.strip() for email in emails if email.strip()]

@add_people_to_group.route('/select_group', methods=['GET', 'POST'])
def select_group():
    api_key = get_api_key()
    event_id = session.get('event_id')
    if not api_key or not event_id:
        logger.warning("Missing api_key or event_id, redirecting to index")
        return redirect(url_for('main.index'))

    groups = fetch_groups(api_key, event_id)
    logger.debug(f"Fetched groups: {groups}")
    form = GroupForm()
    form.group.choices = [(group['id'], group['name']) for group in groups]

    if form.validate_on_submit():
        logger.debug(f"Selected group: {form.group.data}")
        session['group_id'] = form.group.data
        return redirect(url_for('add_people_to_group.add_people'))
    
    return render_template('add_people_to_group/select_group.html', form=form, event_name=session.get('event_name'))

@add_people_to_group.route('/add_people', methods=['GET', 'POST'])
def add_people():
    api_key = get_api_key()
    event_id = session.get('event_id')
    group_id = session.get('group_id')
    logger.debug(f"Current session state - event_id: {event_id}, group_id: {group_id}")
    
    if not api_key or not event_id or not group_id:
        logger.warning("Missing api_key, event_id, or group_id, redirecting to index")
        return redirect(url_for('main.index'))

    form = EmailForm()
    if form.validate_on_submit():
        email_text = form.email.data
        emails = parse_emails(email_text)
        logger.debug(f"Parsed emails: {emails}")
        
        success_count = 0
        error_count = 0
        not_found_count = 0
        
        for email in emails:
            logger.debug(f"Attempting to add person with email: {email}")
            person = fetch_person_by_email(api_key, event_id, email)
            if person:
                logger.debug(f"Found person: {person}")
                status_code, response = update_person_groups(api_key, event_id, person['id'], [group_id])
                logger.debug(f"Update response - status: {status_code}, body: {response}")
                if status_code == 200:
                    success_count += 1
                else:
                    logger.error(f"Failed to update groups. Status: {status_code}, Response: {response}")
                    error_count += 1
            else:
                logger.warning(f"No person found with email: {email}")
                not_found_count += 1
        
        # Show summary message
        message_parts = []
        if success_count > 0:
            message_parts.append(f"Successfully added {success_count} people to the group")
        if error_count > 0:
            message_parts.append(f"Failed to add {error_count} people")
        if not_found_count > 0:
            message_parts.append(f"Could not find {not_found_count} people")
        
        flash(" | ".join(message_parts), 'info' if error_count == 0 and not_found_count == 0 else 'warning')
        log_action('add_people_to_group', event_id)
        return redirect(url_for('add_people_to_group.add_people'))

    return render_template('add_people_to_group/add_people.html', form=form, event_name=session.get('event_name'))
