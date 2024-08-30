from flask import Flask
from .main.routes import main  # Import the main blueprint (you'll create this next)
# Import other blueprints as you add them

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object('config.Config')  # Assumes you'll create a config.py file

    # Register blueprints
    app.register_blueprint(main)
    # Register other blueprints here

    return app
