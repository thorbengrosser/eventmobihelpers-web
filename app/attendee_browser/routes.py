from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_required
from urllib.parse import urlencode
from .forms import AttendeeFilterForm
from .services import list_attendees
from app.utils import get_api_client

attendee_browser = Blueprint('attendee_browser', __name__)


def build_pagination_url(page_num):
    """Build URL for pagination with all current filter parameters."""
    params = dict(request.args)
    params['page'] = page_num
    return url_for('attendee_browser.browse_attendees') + '?' + urlencode(params)


def parse_filters_from_request() -> dict:
    """Parse filters from request args."""
    filters = {}
    
    # eq[] filters
    eq_group_id = request.args.get('eq_group_id', '').strip()
    if eq_group_id:
        filters.setdefault('eq', {})['group_id'] = eq_group_id
    
    # in[] filters
    in_ticket_type = request.args.get('in_ticket_type', '').strip()
    if in_ticket_type:
        filters.setdefault('in', {})['ticket_type'] = in_ticket_type
    
    # date_between filters
    date_start = request.args.get('date_start', '').strip()
    date_end = request.args.get('date_end', '').strip()
    if date_start or date_end:
        date_range = {}
        if date_start:
            date_range['start'] = date_start
        if date_end:
            date_range['end'] = date_end
        filters.setdefault('date_between', {})['created_at'] = date_range
    
    return filters


@attendee_browser.route('/', methods=['GET', 'POST'])
@login_required
def browse_attendees():
    """Main attendee browser page with filters and pagination."""
    if not session.get('event_id'):
        return redirect(url_for('main.select_event'))
    
    event_id = session.get('event_id')
    
    # Get pagination params
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    
    per_page = 50
    
    # Parse filters
    filters = parse_filters_from_request()
    
    # Get sort parameters
    sort_column = request.args.get('sort_column')
    sort_direction = request.args.get('sort_direction', 'asc')
    
    # Populate form with current filter values
    form = AttendeeFilterForm()
    form.in_ticket_type.data = request.args.get('in_ticket_type', '')
    form.eq_group_id.data = request.args.get('eq_group_id', '')
    form.date_start.data = request.args.get('date_start', '')
    form.date_end.data = request.args.get('date_end', '')
    
    # Fetch attendees
    result = list_attendees(event_id, page, per_page, filters, sort_column, sort_direction)
    
    return render_template(
        'attendee_browser/browse.html',
        form=form,
        attendees=result.get('items', []),
        page=result.get('page', page),
        per_page=result.get('per_page', per_page),
        total=result.get('total', 0),
        total_pages=result.get('total_pages', 1),
        filters=filters,
        event_name=session.get('event_name'),
        error=result.get('error'),
        build_pagination_url=build_pagination_url
    )

