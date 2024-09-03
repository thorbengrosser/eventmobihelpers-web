from flask import render_template, redirect, url_for, flash, session
from . import manage_chat
from .forms import APIKeyForm, EventForm, GroupForm, ChatToggleForm
from .services import fetch_events, fetch_groups, fetch_people_in_group, update_chat_settings
from app.utils import log_action

@manage_chat.route('/api_key', methods=['GET', 'POST'])
def api_key():
    form = APIKeyForm()
    if form.validate_on_submit():
        session['api_key'] = form.api_key.data
        return redirect(url_for('manage_chat.select_event'))
    return render_template('manage_chat/api_key.html', form=form)

@manage_chat.route('/select_event', methods=['GET', 'POST'])
def select_event():
    api_key = session.get('api_key')
    if not api_key:
        return redirect(url_for('manage_chat.api_key'))

    events = fetch_events(api_key)
    if not events:
        flash('Failed to fetch events. Please check your API key.')
        return redirect(url_for('manage_chat.api_key'))

    form = EventForm()
    form.event.choices = [(event['id'], event['name']) for event in events]
    if form.validate_on_submit():
        session['event_id'] = form.event.data
        return redirect(url_for('manage_chat.select_group'))

    return render_template('manage_chat/select_event.html', form=form)

@manage_chat.route('/select_group', methods=['GET', 'POST'])
def select_group():
    api_key = session.get('api_key')
    event_id = session.get('event_id')
    if not api_key or not event_id:
        return redirect(url_for('manage_chat.api_key'))

    groups = fetch_groups(api_key, event_id)
    if not groups:
        flash('Failed to fetch groups.')
        return redirect(url_for('manage_chat.select_event'))

    form = GroupForm()
    form.group.choices = [(group['id'], group['name']) for group in groups]
    if form.validate_on_submit():
        session['group_id'] = form.group.data
        return redirect(url_for('manage_chat.toggle_chat'))

    return render_template('manage_chat/select_group.html', form=form)

@manage_chat.route('/toggle_chat', methods=['GET', 'POST'])
def toggle_chat():
    api_key = session.get('api_key')
    event_id = session.get('event_id')
    group_id = session.get('group_id')
    

    if not api_key or not event_id or not group_id:
        return redirect(url_for('manage_chat.api_key'))
    form = ChatToggleForm()
    if form.validate_on_submit():
        chat_enabled = form.chat_enabled.data
        people = fetch_people_in_group(api_key, event_id, group_id)
        if not people:
            flash('No people found in the selected group.', 'danger')
            return redirect(url_for('manage_chat.select_group'))

        success_count = 0
        failure_count = 0

        for person in people:
            person_id = person['id']
            status_code, response_data = update_chat_settings(api_key, event_id, person_id, chat_enabled)
            if status_code == 200:
                success_count += 1
            else:
                failure_count += 1

        if failure_count == 0:
            flash(f"Chat {'enabled' if chat_enabled else 'disabled'} for all members in the selected group.", 'success')
        else:
            flash(f"Chat settings updated for {success_count} out of {len(people)} people. Some updates failed.", 'warning')
        log_action('manage_chat', event_id)
        return redirect(url_for('manage_chat.api_key'))

    return render_template('manage_chat/toggle_chat.html', form=form)
