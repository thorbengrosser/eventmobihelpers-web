from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired

class GroupForm(FlaskForm):
    group = SelectField('Group', validators=[DataRequired()])
    submit = SubmitField('Select Group')

class AttendeeSettingsForm(FlaskForm):
    # Chat Settings
    enable_chat = BooleanField('Enable Chat')
    
    # Profile Visibility
    is_profile_visible = BooleanField('Make Profile Visible')
    
    # Notification Settings
    receive_organizer_email = BooleanField('Receive Organizer Emails')
    receive_attendee_email = BooleanField('Receive Attendee Emails')
    attendee_push_notifications = BooleanField('Enable Push Notifications')
    offline_notifications = BooleanField('Enable Offline Notifications')
    
    # Attendance Format
    attendance_format = SelectField('Attendance Format', choices=[
        ('in_person', 'In Person'),
        ('virtual', 'Virtual'),
        ('hybrid', 'Hybrid')
    ])
    
    submit = SubmitField('Update Settings')
