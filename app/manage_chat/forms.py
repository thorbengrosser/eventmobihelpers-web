from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired

class APIKeyForm(FlaskForm):
    api_key = StringField('API Key', validators=[DataRequired()])
    submit = SubmitField('Submit')

class EventForm(FlaskForm):
    event = SelectField('Select Event', validators=[DataRequired()])
    submit = SubmitField('Submit')

class GroupForm(FlaskForm):
    group = SelectField('Select Group', validators=[DataRequired()])
    submit = SubmitField('Submit')

class ChatToggleForm(FlaskForm):
    chat_enabled = BooleanField('Enable Chat for Selected Group')
    submit = SubmitField('Submit')
