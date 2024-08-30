from flask import render_template, send_from_directory
from . import main

@main.route('/')
def index():
    return render_template('index.html')

# Custom route to serve styles.css manually
@main.route('/static/css/<path:filename>')
def custom_static(filename):
    return send_from_directory('static/css', filename)
