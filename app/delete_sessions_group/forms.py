from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

class APIKeyForm(FlaskForm):
    api_key = StringField('API Key', validators=[DataRequired()])
    submit = SubmitField('Next')

class EventForm(FlaskForm):
    event = SelectField('Event', choices=[], validators=[DataRequired()])
    submit = SubmitField('Next')

class TrackForm(FlaskForm):
    track = SelectField('Track', choices=[], validators=[DataRequired()])
    submit = SubmitField('Delete Sessions')
