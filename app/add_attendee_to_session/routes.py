from flask import Blueprint, render_template, request, redirect, url_for, flash

add_attendee_to_session = Blueprint('add_attendee_to_session', __name__)

@add_attendee_to_session.route('/', methods=['GET'])
def select_session():
    # TODO: Implement session selection logic
    return render_template('add_attendee_to_session/select_session.html')

@add_attendee_to_session.route('/enter_emails', methods=['POST', 'GET'])
def enter_emails():
    # TODO: Implement email entry logic
    return render_template('add_attendee_to_session/enter_emails.html')

@add_attendee_to_session.route('/result', methods=['POST'])
def result():
    # TODO: Implement result display logic
    return render_template('add_attendee_to_session/result.html') 