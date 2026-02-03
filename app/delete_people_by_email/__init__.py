from flask import Blueprint

delete_people_by_email = Blueprint('delete_people_by_email', __name__)

from . import routes

