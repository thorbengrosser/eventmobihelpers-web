from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

class TrackForm(FlaskForm):
    track = SelectField('Track', validators=[DataRequired()])
    submit = SubmitField('Delete Sessions')
