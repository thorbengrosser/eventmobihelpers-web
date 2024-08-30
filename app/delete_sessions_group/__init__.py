from flask import Blueprint

delete_sessions_group = Blueprint('delete_sessions_group', __name__)

from . import routes
