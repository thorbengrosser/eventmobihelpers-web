from flask import render_template, redirect, url_for, flash, session
from . import add_people_to_group
from .forms import APIKeyForm, EventForm, GroupForm, EmailForm
from .services import fetch_events, fetch_groups, fetch_person_by_email, update_person_groups
from app.utils import log_action

@add_people_to_group.route('/api_key', methods=['GET', 'POST'])
def api_key():
    form = APIKeyForm()
    if form.validate_on_submit():
        session['api_key'] = form.api_key.data
        return redirect(url_for('add_people_to_group.select_event'))
    return render_template('add_people_to_group/api_key.html', form=form)

@add_people_to_group.route('/select_event', methods=['GET', 'POST'])
def select_event():
    api_key = session.get('api_key')
    if not api_key:
        return redirect(url_for('add_people_to_group.api_key'))

    events = fetch_events(api_key)
    if not events:
        flash('Failed to fetch events. Please check your API key.')
        return redirect(url_for('add_people_to_group.api_key'))

    form = EventForm()
    form.event.choices = [(event['id'], event['name']) for event in events]
    if form.validate_on_submit():
        session['event_id'] = form.event.data
        return redirect(url_for('add_people_to_group.select_group'))

    return render_template('add_people_to_group/select_event.html', form=form)

@add_people_to_group.route('/select_group', methods=['GET', 'POST'])
def select_group():
    api_key = session.get('api_key')
    event_id = session.get('event_id')
    if not api_key or not event_id:
        return redirect(url_for('add_people_to_group.api_key'))

    groups = fetch_groups(api_key, event_id)
    if not groups:
        flash('Failed to fetch groups.')
        return redirect(url_for('add_people_to_group.select_event'))

    form = GroupForm()
    form.group.choices = [(group['id'], group['name']) for group in groups]
    if form.validate_on_submit():
        session['group_id'] = form.group.data
        return redirect(url_for('add_people_to_group.enter_emails'))

    return render_template('add_people_to_group/select_group.html', form=form)

@add_people_to_group.route('/enter_emails', methods=['GET', 'POST'])
def enter_emails():
    api_key = session.get('api_key')
    event_id = session.get('event_id')
    group_id = session.get('group_id')

    if not api_key or not event_id or not group_id:
        return redirect(url_for('add_people_to_group.api_key'))

    form = EmailForm()
    if form.validate_on_submit():
        emails = form.emails.data.split(',')
        people_to_be_updated = []

        for email in emails:
            person_data = fetch_person_by_email(api_key, event_id, email.strip())
            if not person_data:
                flash(f"No person found with email {email}.")
                continue

            person = person_data[0]
            person_id = person['id']
            current_groups = person.get('groups', [])
            current_groups.append({"id": group_id})
            people_to_be_updated.append({"id": person_id, "groups": current_groups, "email": email})

        success_count = 0
        failure_count = 0
        failed_emails = []

        for person in people_to_be_updated:
            status_code, response_data = update_person_groups(api_key, event_id, person['id'], person['groups'])
            if status_code == 200:
                success_count += 1
            else:
                failure_count += 1
                failed_emails.append(person['email'])

        if failure_count == 0:
            flash("All people have been added to the specified group.", 'success')
        else:
            flash(f"Added {success_count} of {len(people_to_be_updated)} to the group. {failure_count} email addresses could not be added.", 'danger')
        log_action('add_people_to_group', event_id)
        return redirect(url_for('add_people_to_group.api_key'))

    return render_template('add_people_to_group/enter_emails.html', form=form)
