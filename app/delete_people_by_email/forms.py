from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired


class DeletePeopleEmailForm(FlaskForm):
    """
    Form for entering one or more email addresses to delete people.
    """

    emails = TextAreaField(
        'Email Addresses',
        validators=[DataRequired()],
        description='Enter email addresses (one per line, or separated by commas, spaces, or semicolons)',
    )
    submit = SubmitField('Delete People')

