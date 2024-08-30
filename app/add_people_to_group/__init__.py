from flask import Blueprint

add_people_to_group = Blueprint('add_people_to_group', __name__)

from . import routes
