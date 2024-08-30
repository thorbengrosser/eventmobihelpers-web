from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
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

class EmailForm(FlaskForm):
    emails = TextAreaField('Emails (comma-separated)', validators=[DataRequired()])
    submit = SubmitField('Submit')
