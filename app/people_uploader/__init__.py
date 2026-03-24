from flask import Blueprint

people_uploader = Blueprint("people_uploader", __name__)

from app.people_uploader import routes  # noqa: E402, F401
