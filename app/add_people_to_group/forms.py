from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired

class GroupForm(FlaskForm):
    group = SelectField('Group', validators=[DataRequired()])
    submit = SubmitField('Select Group')

class EmailForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Add Person')
