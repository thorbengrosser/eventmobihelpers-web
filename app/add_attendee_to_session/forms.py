from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired

class SelectSessionForm(FlaskForm):
    session = SelectField('Session', validators=[DataRequired()])
    submit = SubmitField('Next')

class EnterEmailsForm(FlaskForm):
    emails = TextAreaField('Attendee Email Addresses', validators=[DataRequired()])
    submit = SubmitField('Add to Session') 