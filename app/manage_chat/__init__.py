from flask import Blueprint

manage_chat = Blueprint('manage_chat', __name__)

from . import routes
