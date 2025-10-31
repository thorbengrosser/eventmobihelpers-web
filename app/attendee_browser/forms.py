from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Optional


class AttendeeFilterForm(FlaskForm):
    """Form for filtering attendees."""
    # in[] filters (membership)
    in_ticket_type = StringField('Ticket Type (comma-separated)', validators=[Optional()])
    
    # eq[] filters (equals)
    eq_group_id = StringField('Group ID', validators=[Optional()])
    
    # date_between filters
    date_start = StringField('Created after (datetime)', validators=[Optional()])
    date_end = StringField('Created before (datetime)', validators=[Optional()])
    
    submit = SubmitField('Apply Filters')

