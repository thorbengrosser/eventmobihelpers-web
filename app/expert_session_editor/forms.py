from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeField, TextAreaField, BooleanField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired
from datetime import datetime

class SessionForm(FlaskForm):
    session = SelectField('Session', validators=[DataRequired()])
    submit = SubmitField('Select Session')

class EditSessionForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    start_datetime = DateTimeField('Start Time', format='%Y-%m-%d %H:%M:%S')
    end_datetime = DateTimeField('End Time', format='%Y-%m-%d %H:%M:%S')
    chat_enabled = RadioField('Chat Enabled', choices=[('true', 'Yes'), ('false', 'No')], default='false')
    aaq_enabled = RadioField('AAQ Enabled', choices=[('true', 'Yes'), ('false', 'No')], default='false')
    submit = SubmitField('Save Changes')