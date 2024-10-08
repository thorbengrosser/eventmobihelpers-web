from flask import Flask
from .main import main as main_blueprint
from .delete_sessions_group import delete_sessions_group
from .add_people_to_group import add_people_to_group
from .manage_chat import manage_chat
from .mass_delete_sessions import mass_delete_sessions
from .expert_session_editor import expert_session_editor



import logging


def create_app():
    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG)
    app.config['SECRET_KEY'] = 'your_secret_key'

    print("Template folder:", app.template_folder)  # Debug print

    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(delete_sessions_group, url_prefix='/delete_sessions_group')
    app.register_blueprint(add_people_to_group, url_prefix='/add_people_to_group')
    app.register_blueprint(manage_chat, url_prefix='/manage_chat')
    app.register_blueprint(mass_delete_sessions, url_prefix='/mass_delete_sessions')
    app.register_blueprint(expert_session_editor, url_prefix='/expert_session_editor')


    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)