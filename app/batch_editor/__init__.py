from flask import Blueprint

batch_editor = Blueprint("batch_editor", __name__)

from app.batch_editor import routes  # noqa: E402, F401
