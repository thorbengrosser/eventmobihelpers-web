from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    BooleanField,
    SubmitField,
    SelectField,
    RadioField,
    FieldList,
    FormField,
    HiddenField,
    IntegerField,
    DecimalField,
)
from wtforms.validators import DataRequired, Length, Optional, URL, ValidationError

try:  # WTForms 3.x
    from wtforms.fields import DateTimeLocalField
except ImportError:  # WTForms 2.x fallback
    from wtforms.fields.html5 import DateTimeLocalField  # type: ignore


class StringListEntryForm(FlaskForm):
    value = StringField('Value', validators=[Optional(), Length(max=256)])


class ExternalLinkForm(FlaskForm):
    id = StringField('ID', validators=[Optional(), Length(max=36)])
    name = StringField('Name', validators=[Optional(), Length(max=256)])
    link = StringField('URL', validators=[Optional(), Length(max=2048), URL()])
    order = IntegerField('Order', validators=[Optional()])
    remove = BooleanField('Remove Entry')


class TrackForm(FlaskForm):
    id = StringField('Track ID', validators=[Optional(), Length(max=36)])
    remove = BooleanField('Remove Entry')


class SubTrackForm(FlaskForm):
    id = StringField('Subtrack ID', validators=[Optional(), Length(max=36)])
    remove = BooleanField('Remove Entry')


class DocumentForm(FlaskForm):
    id = StringField('Document ID', validators=[Optional(), Length(max=36)])
    external_id = StringField('Document External ID', validators=[Optional(), Length(max=64)])
    remove = BooleanField('Remove Entry')


class RolePersonForm(FlaskForm):
    id = StringField('Person ID', validators=[Optional(), Length(max=36)])
    external_id = StringField('Person External ID', validators=[Optional(), Length(max=64)])
    remove = BooleanField('Remove Person')


class RoleForm(FlaskForm):
    identifier_type = SelectField(
        'Role Identifier Type',
        choices=[
            ('id', 'ID'),
            ('external_id', 'External ID'),
            ('type', 'Type'),
            ('name', 'Name'),
        ],
        default='id',
    )
    identifier_value = StringField('Role Identifier Value', validators=[Optional(), Length(max=256)])
    people = FieldList(FormField(RolePersonForm), label='People', min_entries=0)
    remove = BooleanField('Remove Role')


class MapLocationForm(FlaskForm):
    map_id = StringField('Map ID', validators=[Optional(), Length(max=36)])
    label = StringField('Map Label', validators=[Optional(), Length(max=128)])
    latitude = DecimalField('Latitude', validators=[Optional()])
    longitude = DecimalField('Longitude', validators=[Optional()])
    floor = StringField('Floor', validators=[Optional(), Length(max=64)])


class LocationForm(FlaskForm):
    label = StringField('Label', validators=[Optional(), Length(max=128)])
    map_location = FormField(MapLocationForm)


class AccessibilityForm(FlaskForm):
    entity_type = SelectField(
        'Entity Type',
        choices=[
            ('', 'Not Set'),
            ('people_groups', 'People Groups'),
            ('all_event_people', 'All Event People'),
        ],
        default='',
    )
    entity_ids = FieldList(FormField(StringListEntryForm), label='Entity IDs', min_entries=0)


class ChatForm(FlaskForm):
    enabled = BooleanField('Enabled')


class SettingsForm(FlaskForm):
    aaq_enabled = BooleanField('Ask A Question Enabled')
    prevent_schedule_overlap = BooleanField('Prevent Schedule Overlap')
    engagement_order = FieldList(FormField(StringListEntryForm), label='Engagement Order', min_entries=0)


class ContentExperienceForm(FlaskForm):
    type = SelectField(
        'Content Experience Type',
        choices=[
            ('', 'Not Set'),
            ('live_stream', 'Live Stream'),
            ('pre_recorded', 'Pre Recorded'),
            ('video_conference', 'Video Conference'),
            ('breakout_room', 'Breakout Room'),
            ('native_livestream', 'Native Livestream'),
            ('image', 'Image'),
        ],
        default='',
    )
    pre_content_offset = IntegerField('Pre Content Offset', validators=[Optional()])
    post_content_offset = IntegerField('Post Content Offset', validators=[Optional()])
    pre_content_json = TextAreaField('Pre Content (JSON)', validators=[Optional()])
    post_content_json = TextAreaField('Post Content (JSON)', validators=[Optional()])
    main_content_json = TextAreaField('Main Content (JSON)', validators=[Optional()])
    external_id = StringField('Content Experience External ID', validators=[Optional(), Length(max=64)])


class SessionCoreForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=256)])
    external_id = StringField('External ID', validators=[Optional(), Length(max=64)])
    description = TextAreaField('Description', validators=[Optional()])
    start_datetime = DateTimeLocalField('Start Time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    end_datetime = DateTimeLocalField('End Time', format='%Y-%m-%dT%H:%M', validators=[Optional()])

    def validate_end_datetime(self, field):
        if field.data and self.start_datetime.data and field.data <= self.start_datetime.data:
            raise ValidationError('End time must be after start time.')


class SessionForm(FlaskForm):
    session = SelectField('Session', validators=[DataRequired()])
    submit = SubmitField('Select Session')


class EditSessionForm(FlaskForm):
    mode = RadioField(
        'Editing Mode',
        choices=[('ui', 'Guided UI'), ('raw', 'Raw JSON')],
        default='ui',
    )

    initial_payload = HiddenField('Initial Payload')
    raw_payload = TextAreaField('Raw JSON Payload', validators=[Optional()])

    core = FormField(SessionCoreForm)
    accessibility = FormField(AccessibilityForm)
    location = FormField(LocationForm)
    chat = FormField(ChatForm)
    external_links = FieldList(FormField(ExternalLinkForm), label='External Links', min_entries=0)
    roles = FieldList(FormField(RoleForm), label='Roles', min_entries=0)
    tracks = FieldList(FormField(TrackForm), label='Tracks', min_entries=0)
    sub_tracks = FieldList(FormField(SubTrackForm), label='Subtracks', min_entries=0)
    settings = FormField(SettingsForm)
    documents = FieldList(FormField(DocumentForm), label='Documents', min_entries=0)
    content_experience = FormField(ContentExperienceForm)

    submit = SubmitField('Save Changes')