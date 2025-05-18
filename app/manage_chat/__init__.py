from flask import Blueprint

manage_attendee_settings = Blueprint('manage_attendee_settings', __name__)

from . import routes
