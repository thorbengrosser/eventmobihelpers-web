from flask import render_template, send_from_directory, redirect, url_for, session, flash, current_app, jsonify, request
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from app.utils import (
    store_api_key, get_api_key, validate_api_key, clear_session_data,
    get_api_client, store_event_data, get_event_data
)
from app.api.client import EventMobiClient
from app.extensions import db
from flask_login import current_user, login_required
from . import main

class APIKeyForm(FlaskForm):
    api_key = StringField('API Key', validators=[DataRequired()])
    submit = SubmitField('Next')

class EventForm(FlaskForm):
    event = SelectField('Event', validators=[DataRequired()])
    submit = SubmitField('Select Event')

@main.route('/')
@login_required
def index():
    # Check if we have both API key and event selected
    api_key = get_api_key()
    event_id, event_name = get_event_data()
    
    current_app.logger.debug(f"Session data: {dict(session)}")
    current_app.logger.debug(f"Event ID: {event_id}")
    current_app.logger.debug(f"Event Name: {event_name}")
    
    if not api_key:
        return redirect(url_for('main.setup_api_key'))
    if not event_id:
        return redirect(url_for('main.select_event'))
    
    return render_template('index.html', event_name=event_name)

@main.route('/setup', methods=['GET', 'POST'])
@login_required
def setup_api_key():
    # Check if we already have a valid API key
    existing_key = get_api_key()
    if existing_key:
        return redirect(url_for('main.select_event'))

    form = APIKeyForm()
    if form.validate_on_submit():
        api_key = form.api_key.data
        if validate_api_key(api_key):
            store_api_key(api_key)
            if request.form.get('remember_key'):
                current_user.save_api_key(api_key, current_app.secret_key)
                db.session.commit()
            return redirect(url_for('main.select_event'))
        else:
            flash('Invalid API key. Please try again.', 'error')
    return render_template('main/setup.html', form=form)

@main.route('/select_event', methods=['GET', 'POST'])
@login_required
def select_event():
    api_client = get_api_client()
    if not api_client:
        return redirect(url_for('main.setup_api_key'))

    try:
        events = api_client.get_events()
        if not events:
            flash('No events found. Please check your API key.', 'error')
            return redirect(url_for('main.setup_api_key'))

        form = EventForm()
        form.event.choices = [(event['id'], event['name']) for event in events]
        
        if form.validate_on_submit():
            event_id = form.event.data
            # Find the selected event
            selected_event = next(
                (event for event in events if str(event['id']) == str(event_id)),
                None
            )
            
            if selected_event:
                store_event_data(event_id, selected_event['name'])
                current_app.logger.debug(f"Selected event: {selected_event['name']}")
                return redirect(url_for('main.index'))
            else:
                current_app.logger.error(f"Could not find event with ID {event_id}")
                flash('Error: Could not find selected event', 'error')
                return redirect(url_for('main.select_event'))
        
        return render_template('main/select_event.html', form=form)
    except Exception as e:
        current_app.logger.error(f"Error fetching events: {str(e)}")
        flash('Error fetching events. Please try again.', 'error')
        return redirect(url_for('main.setup_api_key'))

@main.route('/change_event')
@login_required
def change_event():
    clear_session_data()
    return redirect(url_for('main.select_event'))

@main.route('/change_api_key')
@login_required
def change_api_key():
    clear_session_data()
    current_user.clear_api_key()
    db.session.commit()
    return redirect(url_for('main.setup_api_key'))

@main.route('/api/events')
@login_required
def get_events():
    client = get_api_client()
    if not client:
        return jsonify({
            'success': False,
            'error': 'No API key found'
        }), 401
    try:
        events = client.get_events()
        return jsonify({
            'success': True,
            'events': events
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/events/<event_id>')
@login_required
def get_event(event_id):
    client = get_api_client()
    if not client:
        return jsonify({
            'success': False,
            'error': 'No API key found'
        }), 401
    try:
        event = client.get_event(event_id)
        return jsonify({
            'success': True,
            'event': event
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/events/<event_id>/select', methods=['POST'])
@login_required
def select_event_api(event_id):
    """API endpoint to select an event."""
    try:
        client = get_api_client()
        if not client:
            return jsonify({
                'success': False,
                'error': 'No API key found'
            }), 401

        event = client.get_event(event_id)
        if not event:
            return jsonify({
                'success': False,
                'error': 'Event not found'
            }), 404

        store_event_data(event_id, event.get('name', 'Unknown Event'))
        current_app.logger.debug(f"Selected event: {event.get('name')}")
        return jsonify({
            'success': True,
            'event': event
        })
    except Exception as e:
        current_app.logger.error(f"Error selecting event: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main.route('/debug/routes')
def debug_routes():
    """List all registered routes (only when DEBUG). Use to verify batch_editor is loaded."""
    if not current_app.debug:
        return jsonify({'error': 'Not available'}), 404
    rules = []
    for rule in current_app.url_map.iter_rules():
        rules.append({'rule': rule.rule, 'endpoint': rule.endpoint, 'methods': list(rule.methods - {'HEAD', 'OPTIONS'})})
    rules.sort(key=lambda r: r['rule'])
    return jsonify({'routes': rules})
