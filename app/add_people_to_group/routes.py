from flask import render_template, redirect, url_for, flash, session
from . import add_people_to_group
from .forms import GroupForm, EmailForm
from .services import fetch_groups, fetch_person_by_email, update_person_groups
from app.utils import log_action, get_api_key
import logging

logger = logging.getLogger(__name__)

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
        email = form.email.data
        logger.debug(f"Attempting to add person with email: {email}")
        person = fetch_person_by_email(api_key, event_id, email)
        if person:
            logger.debug(f"Found person: {person}")
            status_code, response = update_person_groups(api_key, event_id, person['id'], [group_id])
            logger.debug(f"Update response - status: {status_code}, body: {response}")
            if status_code == 200:
                flash(f"Successfully added {email} to the group!", 'success')
                log_action('add_people_to_group', event_id)
            else:
                logger.error(f"Failed to update groups. Status: {status_code}, Response: {response}")
                flash(f"Failed to add {email} to the group. Please try again.", 'error')
        else:
            logger.warning(f"No person found with email: {email}")
            flash(f"Could not find person with email {email}", 'error')
        return redirect(url_for('add_people_to_group.add_people'))

    return render_template('add_people_to_group/add_people.html', form=form, event_name=session.get('event_name'))
