from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

class SessionIDsForm(FlaskForm):
    session_ids = TextAreaField('Session IDs (one per line)', validators=[DataRequired()])
    submit = SubmitField('Delete Sessions')
