from flask import Blueprint

attendee_list = Blueprint('attendee_list', __name__)

from . import routes  # noqa: E402,F401


