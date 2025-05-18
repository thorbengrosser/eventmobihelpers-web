from flask import session

def store_api_key(api_key: str) -> None:
    """Store the API key in the session."""
    session['api_key'] = api_key

def get_api_key() -> str:
    """Get the API key from the session."""
    return session.get('api_key')

def clear_session_data() -> None:
    """Clear all session data."""
    session.clear()

def store_event_data(event_id: str, event_name: str) -> None:
    """Store event data in the session."""
    session['event_id'] = event_id
    session['event_name'] = event_name

def get_event_data() -> tuple:
    """Get event data from the session."""
    return session.get('event_id'), session.get('event_name') 