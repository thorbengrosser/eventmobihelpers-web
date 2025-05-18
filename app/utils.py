import csv
from datetime import datetime
from flask import request, current_app
from app.api.client import EventMobiClient
from app.session import get_api_key, store_api_key, clear_session_data, store_event_data, get_event_data

def log_action(action: str, event_id: str) -> None:
    """Log an action to the log file."""
    log_file = current_app.config['LOG_FILE']
    ip_address = request.remote_addr
    log_entry = [datetime.now().isoformat(), action, ip_address, event_id]
    
    try:
        with open(log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(log_entry)
    except IOError:
        current_app.logger.error(f"Failed to write to log file: {log_file}")

def validate_api_key(api_key: str) -> bool:
    """Validate the API key by making a test request."""
    try:
        store_api_key(api_key)  # Temporarily store the key for testing
        client = EventMobiClient()
        events = client.get_events()
        current_app.logger.debug(f"API key validation successful. Found {len(events)} events.")
        return True
    except Exception as e:
        current_app.logger.error(f"API key validation failed: {str(e)}")
        clear_session_data()  # Clear the temporary key only if validation fails
        return False

def get_api_client() -> EventMobiClient:
    """Get an instance of the EventMobiClient."""
    api_key = get_api_key()
    if not api_key:
        return None
    try:
        return EventMobiClient()
    except Exception:
        return None