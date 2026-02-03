from flask import Flask, jsonify
from flask_wtf.csrf import CSRFProtect
from .main import main as main_bp
from .delete_sessions_group import delete_sessions_group as delete_sessions_bp
from .add_people_to_group import add_people_to_group as add_people_bp
from .delete_people_by_email import delete_people_by_email as delete_people_by_email_bp
from .manage_chat import manage_attendee_settings
from .mass_delete_sessions import mass_delete_sessions
from .expert_session_editor import expert_session_editor
from .auth import bp as auth_bp
from .add_attendee_to_session import add_attendee_to_session
from .attendee_list import attendee_list
from .attendee_browser import attendee_browser
import logging
import os
from config import config
from .extensions import db, login
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

def create_app(config_name='default'):
    app = Flask(__name__, 
                static_folder='static',
                static_url_path='/static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    login.init_app(app)
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Setup logging
    app.logger.setLevel(logging.DEBUG)
    if not app.debug:
        # In production, log to a file
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler('logs/eventmobihelpers.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('EventMobi Helpers startup')

    # Register user loader
    @login.user_loader
    def load_user(id):
        from app.models import User
        return User.query.get(int(id))

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(delete_sessions_bp, url_prefix='/delete_sessions_group')
    app.register_blueprint(add_people_bp, url_prefix='/add_people_to_group')
    app.register_blueprint(delete_people_by_email_bp, url_prefix='/delete_people_by_email')
    app.register_blueprint(manage_attendee_settings, url_prefix='/manage_attendee_settings')
    app.register_blueprint(mass_delete_sessions, url_prefix='/mass_delete_sessions')
    app.register_blueprint(expert_session_editor, url_prefix='/expert_session_editor')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(add_attendee_to_session, url_prefix='/add_attendee_to_session')
    app.register_blueprint(attendee_list, url_prefix='/attendee_list')
    app.register_blueprint(attendee_browser, url_prefix='/attendee_browser')

    # Create database tables and initial admin user
    with app.app_context():
        # Import models here to avoid circular imports
        from app.models import User
        
        # Create all database tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if admin is None:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            app.logger.info('Created initial admin user')

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        app.logger.error(f'Unhandled Exception: {e}')
        return jsonify({'error': 'Internal server error'}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)