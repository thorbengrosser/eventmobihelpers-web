from flask import Blueprint

mass_delete_sessions = Blueprint('mass_delete_sessions', __name__)

from . import routes
