from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired

class APIKeyForm(FlaskForm):
    api_key = StringField('API Key', validators=[DataRequired()])
    submit = SubmitField('Next')

class EventForm(FlaskForm):
    event = SelectField('Select Event', validators=[DataRequired()], choices=[])
    submit = SubmitField('Next')

class SessionIDsForm(FlaskForm):
    session_ids = TextAreaField('Enter Session IDs (comma-separated)', validators=[DataRequired()])
    submit = SubmitField('Delete Sessions')
