from flask import render_template, redirect, url_for, flash, session
from . import manage_attendee_settings
from .forms import GroupForm, AttendeeSettingsForm
from .services import fetch_groups, fetch_people_in_group, update_attendee_settings
from app.utils import log_action, get_api_key

@manage_attendee_settings.route('/select_group', methods=['GET', 'POST'])
def select_group():
    api_key = get_api_key()
    event_id = session.get('event_id')
    if not api_key or not event_id:
        return redirect(url_for('main.index'))

    groups = fetch_groups(api_key, event_id)
    form = GroupForm()
    form.group.choices = [(group['id'], group['name']) for group in groups]

    if form.validate_on_submit():
        session['group_id'] = form.group.data
        return redirect(url_for('manage_attendee_settings.manage_settings'))
    
    return render_template('manage_attendee_settings/select_group.html', form=form, event_name=session.get('event_name'))

@manage_attendee_settings.route('/manage_settings', methods=['GET', 'POST'])
def manage_settings():
    api_key = get_api_key()
    event_id = session.get('event_id')
    group_id = session.get('group_id')
    if not api_key or not event_id or not group_id:
        return redirect(url_for('main.index'))

    people = fetch_people_in_group(api_key, event_id, group_id)
    form = AttendeeSettingsForm()

    if form.validate_on_submit():
        # Get all settings from the form
        settings = {
            'enable_chat': form.enable_chat.data,
            'is_profile_visible': form.is_profile_visible.data,
            'attendance_format': form.attendance_format.data,
            'receive_organizer_email': form.receive_organizer_email.data,
            'receive_attendee_email': form.receive_attendee_email.data,
            'attendee_push_notifications': form.attendee_push_notifications.data,
            'offline_notifications': form.offline_notifications.data
        }
        
        print(f"DEBUG: Form data submitted: {settings}")
        print(f"DEBUG: Number of people in group: {len(people) if people else 0}")
        
        # Update settings for each person in the group
        success_count = 0
        for person in people:
            print(f"DEBUG: Processing person: {person.get('id')} - {person.get('name')}")
            status_code, response = update_attendee_settings(api_key, event_id, person['id'], settings)
            if status_code in [200, 204]:
                success_count += 1
            else:
                print(f"DEBUG: Failed to update person {person.get('id')}. Status: {status_code}, Response: {response}")
        
        if success_count > 0:
            flash(f'Successfully updated settings for {success_count} attendees!', 'success')
        else:
            flash('Failed to update settings for any attendees.', 'error')
            
        log_action('manage_attendee_settings', event_id)
        return redirect(url_for('manage_attendee_settings.select_group'))

    return render_template('manage_attendee_settings/manage_settings.html', form=form, people=people, event_name=session.get('event_name'))
