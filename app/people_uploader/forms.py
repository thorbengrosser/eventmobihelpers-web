from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import RadioField, SubmitField
from wtforms.validators import DataRequired


EVENTMOBI_FIELDS = [
    ("", "-- Ignore this column --"),
    ("first_name", "First Name"),
    ("last_name", "Last Name"),
    ("email", "Email"),
    ("title", "Title / Job Title"),
    ("company_name", "Company Name"),
    ("pronouns", "Pronouns"),
    ("about", "About / Bio"),
    ("website", "Website"),
    ("checkin_code", "Check-in Code"),
    ("registration_status", "Registration Status"),
    ("external_id", "External ID"),
    ("social_twitter", "Social: Twitter"),
    ("social_facebook", "Social: Facebook"),
    ("social_linkedin", "Social: LinkedIn"),
    ("is_profile_visible", "Profile Visible (true/false)"),
    ("chat_enabled", "Chat Enabled (true/false)"),
]

MATCH_FIELD_CHOICES = [
    ("email", "Email (recommended)"),
    ("id", "EventMobi ID"),
    ("first_last_name", "First + Last Name (unreliable — may match wrong person)"),
]

MISSING_RECORD_CHOICES = [
    ("skip", "Skip — do not create a new person"),
    ("create", "Create new person"),
]


class UploadForm(FlaskForm):
    file = FileField(
        "Excel File (.xlsx)",
        validators=[
            FileRequired(),
            FileAllowed(["xlsx"], "Only .xlsx files are accepted."),
        ],
    )
    submit = SubmitField("Upload and Continue")


class MappingForm(FlaskForm):
    """Carries CSRF token and match_field radio. Column mapping dropdowns are
    rendered manually in the template and read from request.form in the route."""
    match_field = RadioField(
        "Match people in EventMobi by",
        choices=MATCH_FIELD_CHOICES,
        validators=[DataRequired()],
        default="email",
    )
    submit = SubmitField("Continue")


class MissingRecordForm(FlaskForm):
    missing_action = RadioField(
        "When a person is NOT found in EventMobi",
        choices=MISSING_RECORD_CHOICES,
        validators=[DataRequired()],
        default="skip",
    )
    submit = SubmitField("Preview")


class ReviewForm(FlaskForm):
    submit = SubmitField("Run Upload")
