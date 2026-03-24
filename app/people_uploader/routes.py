import csv
import io
import logging

from flask import (
    render_template, redirect, url_for,
    session as flask_session, request, flash, Response,
)
from flask_login import login_required

from app.people_uploader import people_uploader
from app.people_uploader.forms import (
    UploadForm, MappingForm, MissingRecordForm, ReviewForm, EVENTMOBI_FIELDS,
)
from app.people_uploader.services import (
    parse_excel,
    get_column_samples,
    save_rows_to_tempfile,
    load_rows_from_tempfile,
    delete_tempfile,
    build_preview,
    execute_upload,
)
from app.utils import get_api_client, log_action

logger = logging.getLogger(__name__)

# Session keys — all prefixed with "pu_" to avoid collisions
SK_HEADERS        = "pu_headers"
SK_ROWS_TOKEN     = "pu_rows_token"
SK_COLUMN_MAPPING = "pu_column_mapping"
SK_MATCH_FIELD    = "pu_match_field"
SK_MISSING_ACTION = "pu_missing_action"
SK_RESULTS_TOKEN  = "pu_results_token"
SK_CUSTOM_FIELDS  = "pu_custom_fields"   # [{id, name}, ...] fetched from API


def _require_event():
    """Return a redirect if no event or API client is configured, else None."""
    if not flask_session.get("event_id"):
        flash("Please select an event first.", "error")
        return redirect(url_for("main.index"))
    if not get_api_client():
        flash("Please configure your API key first.", "error")
        return redirect(url_for("main.change_api_key"))
    return None


def _clear_wizard():
    """Reset all wizard session keys and delete any temp files."""
    for token_key in (SK_ROWS_TOKEN, SK_RESULTS_TOKEN):
        token = flask_session.pop(token_key, None)
        if token:
            delete_tempfile(token)
    for key in (SK_HEADERS, SK_COLUMN_MAPPING, SK_MATCH_FIELD, SK_MISSING_ACTION, SK_CUSTOM_FIELDS):
        flask_session.pop(key, None)


# ---------------------------------------------------------------------------
# Step 1: Upload
# ---------------------------------------------------------------------------

@people_uploader.route("/", methods=["GET", "POST"])
@login_required
def step_upload():
    redir = _require_event()
    if redir:
        return redir

    form = UploadForm()
    if form.validate_on_submit():
        _clear_wizard()
        try:
            headers, rows = parse_excel(form.file.data)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("people_uploader.step_upload"))

        token = save_rows_to_tempfile(rows)
        flask_session[SK_HEADERS] = headers
        flask_session[SK_ROWS_TOKEN] = token
        return redirect(url_for("people_uploader.step_mapping"))

    return render_template(
        "people_uploader/step1_upload.html",
        form=form,
        event_name=flask_session.get("event_name"),
    )


# ---------------------------------------------------------------------------
# Step 2: Field Mapping
# ---------------------------------------------------------------------------

def _build_em_fields(custom_field_defs):
    """Build the full field list: standard fields + a separator + custom fields."""
    fields = list(EVENTMOBI_FIELDS)
    if custom_field_defs:
        fields.append(("__separator__", "── Custom Fields ──"))
        for cf in custom_field_defs:
            fid = cf.get("id") or cf.get("external_id")
            name = cf.get("name") or f"Custom Field ({fid})"
            if fid:
                fields.append((f"custom_field:{fid}", name))
    return fields


@people_uploader.route("/mapping", methods=["GET", "POST"])
@login_required
def step_mapping():
    redir = _require_event()
    if redir:
        return redir

    headers = flask_session.get(SK_HEADERS)
    if not headers:
        return redirect(url_for("people_uploader.step_upload"))

    form = MappingForm()

    # Fetch custom fields once on GET and cache in session; re-use on POST
    custom_field_defs = flask_session.get(SK_CUSTOM_FIELDS)
    if custom_field_defs is None:
        client = get_api_client()
        event_id = flask_session.get("event_id")
        try:
            custom_field_defs = client.list_people_custom_fields(event_id) or []
        except Exception:
            custom_field_defs = []
        flask_session[SK_CUSTOM_FIELDS] = custom_field_defs

    em_fields = _build_em_fields(custom_field_defs)

    if form.validate_on_submit():
        column_mapping = {}
        for i, col in enumerate(headers):
            mapped = request.form.get(f"col_map_{i}", "")
            # Discard the visual separator if somehow selected
            column_mapping[col] = "" if mapped == "__separator__" else mapped

        match_field = form.match_field.data

        # Validate: the match field column must be mapped
        if match_field == "first_last_name":
            fn = any(v == "first_name" for v in column_mapping.values())
            ln = any(v == "last_name" for v in column_mapping.values())
            match_ok = fn and ln
        else:
            match_ok = any(v == match_field for v in column_mapping.values())

        if not match_ok:
            field_label = dict([
                ("email", "Email"),
                ("id", "EventMobi ID"),
                ("first_last_name", "First Name and Last Name"),
            ]).get(match_field, match_field)
            flash(
                f"You selected '{field_label}' as the match field but did not map "
                "any column to it. Please map the correct column below.",
                "error",
            )
            return render_template(
                "people_uploader/step2_mapping.html",
                form=form,
                headers=headers,
                em_fields=em_fields,
                samples={},
                submitted_mapping=column_mapping,
                event_name=flask_session.get("event_name"),
            )

        flask_session[SK_COLUMN_MAPPING] = column_mapping
        flask_session[SK_MATCH_FIELD] = match_field
        return redirect(url_for("people_uploader.step_missing"))

    # On GET: load sample values to show in the mapping table
    samples = {}
    token = flask_session.get(SK_ROWS_TOKEN)
    if token:
        rows = load_rows_from_tempfile(token)
        if rows:
            samples = get_column_samples(rows, headers)

    # Build a {field_id: field_name} lookup for custom field name-based auto-detection
    cf_name_to_key = {
        cf.get("name", "").lower().strip(): f"custom_field:{cf.get('id') or cf.get('external_id')}"
        for cf in custom_field_defs
        if cf.get("id") or cf.get("external_id")
    }

    # Auto-detect plausible mappings by column name heuristics
    auto_mapping = {}
    for col in headers:
        col_lower = col.lower().strip()
        if col_lower in ("email", "e-mail", "emailaddress", "email address"):
            auto_mapping[col] = "email"
        elif col_lower in ("first_name", "firstname", "first name", "given name"):
            auto_mapping[col] = "first_name"
        elif col_lower in ("last_name", "lastname", "last name", "surname", "family name"):
            auto_mapping[col] = "last_name"
        elif col_lower in ("title", "job title", "jobtitle", "position"):
            auto_mapping[col] = "title"
        elif col_lower in ("company", "company_name", "companyname", "organisation", "organization"):
            auto_mapping[col] = "company_name"
        elif col_lower in ("pronouns",):
            auto_mapping[col] = "pronouns"
        elif col_lower in ("website", "url", "web"):
            auto_mapping[col] = "website"
        elif col_lower in ("about", "bio", "biography", "description"):
            auto_mapping[col] = "about"
        elif col_lower in ("checkin_code", "checkin code", "check-in code", "barcode"):
            auto_mapping[col] = "checkin_code"
        elif col_lower in ("id", "eventmobi id", "person_id", "people_id"):
            auto_mapping[col] = "id"
        elif col_lower in ("external_id", "external id"):
            auto_mapping[col] = "external_id"
        elif col_lower in cf_name_to_key:
            # Exact name match against a custom field
            auto_mapping[col] = cf_name_to_key[col_lower]
        else:
            auto_mapping[col] = ""

    return render_template(
        "people_uploader/step2_mapping.html",
        form=form,
        headers=headers,
        em_fields=em_fields,
        samples=samples,
        submitted_mapping=auto_mapping,
        event_name=flask_session.get("event_name"),
    )


# ---------------------------------------------------------------------------
# Step 3: Missing Record Handling
# ---------------------------------------------------------------------------

@people_uploader.route("/missing", methods=["GET", "POST"])
@login_required
def step_missing():
    redir = _require_event()
    if redir:
        return redir

    if not flask_session.get(SK_COLUMN_MAPPING):
        return redirect(url_for("people_uploader.step_mapping"))

    column_mapping = flask_session.get(SK_COLUMN_MAPPING, {})
    match_field = flask_session.get(SK_MATCH_FIELD, "email")
    fn_mapped = any(v == "first_name" for v in column_mapping.values())
    ln_mapped = any(v == "last_name" for v in column_mapping.values())
    can_create = fn_mapped and ln_mapped

    form = MissingRecordForm()

    if form.validate_on_submit():
        missing_action = form.missing_action.data
        if missing_action == "create" and not can_create:
            flash(
                "To create new people, you must map a column to 'First Name' "
                "and a column to 'Last Name' in the field mapping step.",
                "error",
            )
            return redirect(url_for("people_uploader.step_missing"))

        flask_session[SK_MISSING_ACTION] = missing_action
        return redirect(url_for("people_uploader.step_review"))

    match_field_label = dict([
        ("email", "Email"),
        ("id", "EventMobi ID"),
        ("first_last_name", "First + Last Name"),
    ]).get(match_field, match_field)

    return render_template(
        "people_uploader/step3_missing.html",
        form=form,
        match_field=match_field,
        match_field_label=match_field_label,
        can_create=can_create,
        event_name=flask_session.get("event_name"),
    )


# ---------------------------------------------------------------------------
# Step 4: Review (dry-run preview)
# ---------------------------------------------------------------------------

@people_uploader.route("/review", methods=["GET", "POST"])
@login_required
def step_review():
    redir = _require_event()
    if redir:
        return redir

    token = flask_session.get(SK_ROWS_TOKEN)
    column_mapping = flask_session.get(SK_COLUMN_MAPPING)
    match_field = flask_session.get(SK_MATCH_FIELD)
    missing_action = flask_session.get(SK_MISSING_ACTION)

    if not all([token, column_mapping, match_field, missing_action]):
        return redirect(url_for("people_uploader.step_upload"))

    rows = load_rows_from_tempfile(token)
    if rows is None:
        flash("Upload session expired. Please upload the file again.", "error")
        _clear_wizard()
        return redirect(url_for("people_uploader.step_upload"))

    form = ReviewForm()
    if form.validate_on_submit():
        return redirect(url_for("people_uploader.step_execute"))

    client = get_api_client()
    event_id = flask_session.get("event_id")

    preview_rows, counts = build_preview(
        rows=rows,
        column_mapping=column_mapping,
        match_field=match_field,
        missing_action=missing_action,
        client=client,
        event_id=event_id,
        max_preview=10,
    )

    match_field_label = dict([
        ("email", "Email"),
        ("id", "EventMobi ID"),
        ("first_last_name", "First + Last Name"),
    ]).get(match_field, match_field)

    return render_template(
        "people_uploader/step4_review.html",
        form=form,
        preview_rows=preview_rows,
        counts=counts,
        total_rows=len(rows),
        match_field_label=match_field_label,
        missing_action=missing_action,
        event_name=flask_session.get("event_name"),
    )


# ---------------------------------------------------------------------------
# Step 5: Execute
# ---------------------------------------------------------------------------

@people_uploader.route("/execute", methods=["POST"])
@login_required
def step_execute():
    redir = _require_event()
    if redir:
        return redir

    token = flask_session.get(SK_ROWS_TOKEN)
    column_mapping = flask_session.get(SK_COLUMN_MAPPING)
    match_field = flask_session.get(SK_MATCH_FIELD)
    missing_action = flask_session.get(SK_MISSING_ACTION)

    if not all([token, column_mapping, match_field, missing_action]):
        return redirect(url_for("people_uploader.step_upload"))

    rows = load_rows_from_tempfile(token)
    if rows is None:
        flash("Upload session expired. Please upload the file again.", "error")
        _clear_wizard()
        return redirect(url_for("people_uploader.step_upload"))

    client = get_api_client()
    event_id = flask_session.get("event_id")

    results = execute_upload(
        rows=rows,
        column_mapping=column_mapping,
        match_field=match_field,
        missing_action=missing_action,
        client=client,
        event_id=event_id,
    )

    # Store results in a temp file (may be large)
    results_token = save_rows_to_tempfile(results)
    delete_tempfile(token)
    flask_session.pop(SK_ROWS_TOKEN, None)
    flask_session[SK_RESULTS_TOKEN] = results_token

    log_action("people_uploader", event_id)
    return redirect(url_for("people_uploader.result"))


# ---------------------------------------------------------------------------
# Result view
# ---------------------------------------------------------------------------

@people_uploader.route("/result")
@login_required
def result():
    redir = _require_event()
    if redir:
        return redir

    results_token = flask_session.get(SK_RESULTS_TOKEN)
    if not results_token:
        return redirect(url_for("people_uploader.step_upload"))

    results = load_rows_from_tempfile(results_token)
    if results is None:
        flash("Results session expired.", "error")
        return redirect(url_for("people_uploader.step_upload"))

    updated = sum(1 for r in results if r.get("action") == "update" and r.get("success"))
    created = sum(1 for r in results if r.get("action") == "create" and r.get("success"))
    skipped = sum(1 for r in results if r.get("action") == "skip")
    errors  = sum(1 for r in results if not r.get("success") and r.get("action") != "skip")

    return render_template(
        "people_uploader/step5_result.html",
        results=results,
        updated=updated,
        created=created,
        skipped=skipped,
        errors=errors,
        total=len(results),
        event_name=flask_session.get("event_name"),
    )


@people_uploader.route("/result/export")
@login_required
def result_export():
    redir = _require_event()
    if redir:
        return redir

    results_token = flask_session.get(SK_RESULTS_TOKEN)
    if not results_token:
        return redirect(url_for("people_uploader.step_upload"))

    results = load_rows_from_tempfile(results_token)
    if results is None:
        flash("Results session expired.", "error")
        return redirect(url_for("people_uploader.step_upload"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["row_num", "match_value", "action", "person_id", "success", "status", "error"])
    for r in results:
        writer.writerow([
            r.get("row_num", ""),
            r.get("match_value", ""),
            r.get("action", ""),
            r.get("person_id", ""),
            r.get("success", False),
            r.get("status", ""),
            r.get("error") or "",
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=people_upload_result.csv"},
    )
