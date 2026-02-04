from flask_wtf import FlaskForm
from wtforms import SelectField, RadioField, StringField, TextAreaField, SubmitField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Optional


class ResourceForm(FlaskForm):
    """Step 1: Choose resource (People, Sessions)."""
    resource = SelectField(
        "Resource",
        choices=[
            ("people", "People (attendees)"),
            ("sessions", "Sessions"),
            ("companies", "Companies"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Next")


class ScopeForm(FlaskForm):
    """Step 2: Choose scope – single or batch; by IDs or by criteria."""
    scope_mode = RadioField(
        "Scope",
        choices=[
            ("single", "Single (one ID or lookup)"),
            ("batch", "Batch (many)"),
        ],
        validators=[DataRequired()],
        default="single",
    )
    # For single: one value (email, id, or external_id). For batch: textarea of IDs or criteria.
    scope_value = StringField("ID or lookup value (e.g. email for people, external_id for sessions)", validators=[Optional()])
    scope_ids = TextAreaField(
        "List of IDs (one per line or comma-separated)",
        validators=[Optional()],
        description="For batch: paste IDs or leave empty and use criteria below.",
    )
    # Criteria (resource-dependent). People: group_id, registration_status. Sessions: track_id.
    criteria_group_id = StringField("Group ID (people only)", validators=[Optional()])
    criteria_registration_status = SelectField(
        "Registration status (people only)",
        choices=[
            ("", "Any"),
            ("registered", "Registered"),
            ("invited", "Invited"),
            ("declined", "Declined"),
            ("registration_pending", "Registration pending"),
            ("not_started", "Not started"),
            ("expired", "Expired"),
        ],
        validators=[Optional()],
    )
    criteria_track_id = StringField("Track ID (sessions only)", validators=[Optional()])
    criteria_company_group_id = StringField("Company group ID (companies only)", validators=[Optional()])
    submit = SubmitField("Resolve scope")


class ActionForm(FlaskForm):
    """Step 3: Choose action (Delete, Update, or resource-specific)."""
    action = SelectField("Action", choices=[], validators=[DataRequired()])
    submit = SubmitField("Next")


class ReviewForm(FlaskForm):
    """Step 4: Confirm and run."""
    confirm = SubmitField("Run batch")


class ActionPayloadSessionForm(FlaskForm):
    """Extra form for action that needs session_id (e.g. Add to session)."""
    session_id = StringField("Session ID", validators=[DataRequired()])
    submit = SubmitField("Next")


class ActionPayloadGroupForm(FlaskForm):
    """Extra form for Add to group – need group_id(s)."""
    group_id = StringField("Group ID", validators=[DataRequired()])
    submit = SubmitField("Next")


class UpdatePeopleForm(FlaskForm):
    """Form for Update People action – fields to set on each person."""
    first_name = StringField("First name", validators=[Optional()])
    last_name = StringField("Last name", validators=[Optional()])
    email = StringField("Email", validators=[Optional()])
    title = StringField("Title", validators=[Optional()])
    company_name = StringField("Company name", validators=[Optional()])
    chat_enabled = SelectField("Chat enabled", choices=[("", "No change"), ("true", "Yes"), ("false", "No")], validators=[Optional()])
    is_profile_visible = SelectField("Profile visible", choices=[("", "No change"), ("true", "Yes"), ("false", "No")], validators=[Optional()])
    submit = SubmitField("Apply to batch")


class UpdateSessionForm(FlaskForm):
    """Minimal form for Update Session action."""
    name = StringField("Session name", validators=[Optional()])
    description = StringField("Description", validators=[Optional()])
    submit = SubmitField("Apply to batch")


class UpdateCompanyForm(FlaskForm):
    """Minimal form for Update Company action."""
    name = StringField("Company name", validators=[Optional()])
    submit = SubmitField("Apply to batch")
