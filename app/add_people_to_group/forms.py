from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired

class GroupForm(FlaskForm):
    group = SelectField('Group', validators=[DataRequired()])
    submit = SubmitField('Select Group')

class EmailForm(FlaskForm):
    email = TextAreaField('Email Addresses', validators=[DataRequired()], 
                         description='Enter email addresses (one per line, or separated by commas, spaces, or semicolons)')
    submit = SubmitField('Add People')
