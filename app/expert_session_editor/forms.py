from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, TextAreaField, BooleanField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired
from datetime import datetime


class APIKeyForm(FlaskForm):
    api_key = StringField('API Key', validators=[DataRequired()])
    submit = SubmitField('Submit')

class EventForm(FlaskForm):
    event = SelectField('Select Event', validators=[DataRequired()])
    submit = SubmitField('Next')

class SessionForm(FlaskForm):
    session = SelectField('Select Session', validators=[DataRequired()])
    submit = SubmitField('Next')

class EditSessionForm(FlaskForm):
    name = StringField('Session Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    start_datetime = DateTimeField('Start Time', format='%Y-%m-%dT%H:%M:%S', validators=[DataRequired()])
    end_datetime = DateTimeField('End Time', format='%Y-%m-%dT%H:%M:%S', validators=[DataRequired()])
    chat_enabled = RadioField('Chat Enabled', choices=[('true', 'Enabled'), ('false', 'Disabled')], default='false')
    aaq_enabled = RadioField('AAQ Enabled', choices=[('true', 'Enabled'), ('false', 'Disabled')], default='false')
    submit = SubmitField('Save Changes')