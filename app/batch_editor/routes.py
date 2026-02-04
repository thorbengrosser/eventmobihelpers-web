import csv
import io
import logging
from flask import render_template, redirect, url_for, session as flask_session, request, flash, Response

from app.batch_editor import batch_editor
from app.batch_editor.forms import ResourceForm, ScopeForm, ActionForm, ReviewForm, UpdatePeopleForm, UpdateSessionForm, UpdateCompanyForm
from app.batch_editor.scope_resolver import resolve_scope, RESOURCE_PEOPLE, RESOURCE_SESSIONS
from app.batch_editor.executor import (
    execute_batch,
    ACTION_DELETE,
    ACTION_UPDATE,
    ACTION_ADD_TO_SESSION,
    ACTION_REMOVE_FROM_SESSION,
    ACTION_ADD_TO_GROUP,
)
from app.utils import get_api_client, log_action

logger = logging.getLogger(__name__)

SESSION_KEY_RESOURCE = "batch_editor_resource"
SESSION_KEY_SCOPE_IDS = "batch_editor_scope_ids"
SESSION_KEY_ACTION = "batch_editor_action"
SESSION_KEY_ACTION_PAYLOAD = "batch_editor_action_payload"
SESSION_KEY_RESULTS = "batch_editor_results"


def _require_event():
    if not flask_session.get("event_id"):
        return redirect(url_for("main.select_event"))
    if not get_api_client():
        return redirect(url_for("main.setup_api_key"))
    return None


def _action_choices_for_resource(resource):
    if resource == RESOURCE_PEOPLE:
        return [
            (ACTION_DELETE, "Delete"),
            (ACTION_UPDATE, "Update (fields)"),
            (ACTION_ADD_TO_SESSION, "Add to session"),
            (ACTION_REMOVE_FROM_SESSION, "Remove from session"),
            (ACTION_ADD_TO_GROUP, "Add to group"),
        ]
    if resource == RESOURCE_SESSIONS:
        return [
            (ACTION_DELETE, "Delete"),
            (ACTION_UPDATE, "Update (fields)"),
        ]
    if resource == "companies":
        return [
            (ACTION_DELETE, "Delete"),
            (ACTION_UPDATE, "Update (fields)"),
        ]
    return []


@batch_editor.route("/shortcut/<name>", methods=["GET"])
def shortcut(name):
    """Shortcut: set resource and action in session and redirect to scope step."""
    redir = _require_event()
    if redir:
        return redir
    shortcuts_map = {
        "delete_people": (RESOURCE_PEOPLE, ACTION_DELETE),
        "add_people_to_group": (RESOURCE_PEOPLE, ACTION_ADD_TO_GROUP),
        "edit_attendee_settings": (RESOURCE_PEOPLE, ACTION_UPDATE),
        "add_attendee_to_session": (RESOURCE_PEOPLE, ACTION_ADD_TO_SESSION),
        "mass_delete_sessions": (RESOURCE_SESSIONS, ACTION_DELETE),
        "delete_sessions_by_track": (RESOURCE_SESSIONS, ACTION_DELETE),
        "expert_session_editor": (RESOURCE_SESSIONS, ACTION_UPDATE),
    }
    if name not in shortcuts_map:
        flash(f"Unknown shortcut: {name}", "warning")
        return redirect(url_for("batch_editor.step_resource"))
    resource, action = shortcuts_map[name]
    flask_session[SESSION_KEY_RESOURCE] = resource
    flask_session.pop(SESSION_KEY_SCOPE_IDS, None)
    flask_session[SESSION_KEY_ACTION] = action
    flask_session.pop(SESSION_KEY_ACTION_PAYLOAD, None)
    flask_session.pop(SESSION_KEY_RESULTS, None)
    return redirect(url_for("batch_editor.step_scope"))


@batch_editor.route("/", methods=["GET", "POST"])
def step_resource():
    redir = _require_event()
    if redir:
        return redir

    form = ResourceForm()
    if form.validate_on_submit():
        flask_session[SESSION_KEY_RESOURCE] = form.resource.data
        flask_session.pop(SESSION_KEY_SCOPE_IDS, None)
        flask_session.pop(SESSION_KEY_ACTION, None)
        flask_session.pop(SESSION_KEY_ACTION_PAYLOAD, None)
        flask_session.pop(SESSION_KEY_RESULTS, None)
        return redirect(url_for("batch_editor.step_scope"))

    return render_template(
        "batch_editor/resource.html",
        form=form,
        event_name=flask_session.get("event_name"),
    )


@batch_editor.route("/scope", methods=["GET", "POST"])
def step_scope():
    redir = _require_event()
    if redir:
        return redir
    if not flask_session.get(SESSION_KEY_RESOURCE):
        return redirect(url_for("batch_editor.step_resource"))

    form = ScopeForm()
    resource = flask_session[SESSION_KEY_RESOURCE]
    event_id = flask_session.get("event_id")

    if form.validate_on_submit():
        client = get_api_client()
        if not client:
            flash("API client not available.", "error")
            return redirect(url_for("main.index"))

        single_or_batch = form.scope_mode.data
        by_ids = None
        criteria = None

        if single_or_batch == "single":
            by_ids = (form.scope_value.data or "").strip()
            if not by_ids:
                flash("Enter an ID or lookup value for single scope.", "error")
                return redirect(url_for("batch_editor.step_scope"))
        else:
            by_ids = (form.scope_ids.data or "").strip() or None
            if resource == RESOURCE_PEOPLE:
                if form.criteria_group_id.data:
                    criteria = criteria or {}
                    criteria["group_id"] = form.criteria_group_id.data.strip()
                if form.criteria_registration_status.data:
                    criteria = criteria or {}
                    criteria["registration_status"] = form.criteria_registration_status.data
            if resource == RESOURCE_SESSIONS and form.criteria_track_id.data:
                criteria = criteria or {}
                criteria["track_id"] = form.criteria_track_id.data.strip()
            if resource == "companies" and form.criteria_company_group_id.data:
                criteria = criteria or {}
                criteria["group_id"] = form.criteria_company_group_id.data.strip()

        scope_ids = resolve_scope(
            resource=resource,
            event_id=event_id,
            single_or_batch=single_or_batch,
            by_ids=by_ids,
            criteria=criteria,
            client=client,
        )
        if not scope_ids:
            flash("No matching IDs found. Check your criteria or IDs.", "error")
            return redirect(url_for("batch_editor.step_scope"))
        flask_session[SESSION_KEY_SCOPE_IDS] = scope_ids
        flask_session.pop(SESSION_KEY_ACTION, None)
        flask_session.pop(SESSION_KEY_ACTION_PAYLOAD, None)
        return redirect(url_for("batch_editor.step_action"))

    return render_template(
        "batch_editor/scope.html",
        form=form,
        resource=resource,
        event_name=flask_session.get("event_name"),
    )


def _fetch_sessions_and_groups(event_id):
    """Fetch sessions and people groups for dropdowns. Returns (sessions, groups) or ([], []) on error."""
    client = get_api_client()
    if not client:
        return [], []
    sessions, groups = [], []
    try:
        sessions = client.get_sessions(event_id) or []
    except Exception:
        pass
    try:
        groups = client.get_groups(event_id) or []
    except Exception:
        pass
    return sessions, groups


@batch_editor.route("/action", methods=["GET", "POST"])
def step_action():
    redir = _require_event()
    if redir:
        return redir
    if not flask_session.get(SESSION_KEY_RESOURCE) or not flask_session.get(SESSION_KEY_SCOPE_IDS):
        return redirect(url_for("batch_editor.step_resource"))

    resource = flask_session[SESSION_KEY_RESOURCE]
    scope_ids = flask_session[SESSION_KEY_SCOPE_IDS]
    event_id = flask_session.get("event_id")
    form = ActionForm()
    form.action.choices = _action_choices_for_resource(resource)

    sessions, groups = [], []
    if resource == RESOURCE_PEOPLE:
        sessions, groups = _fetch_sessions_and_groups(event_id)

    if form.validate_on_submit():
        action = form.action.data
        flask_session[SESSION_KEY_ACTION] = action
        payload = {}
        if action in (ACTION_ADD_TO_SESSION, ACTION_REMOVE_FROM_SESSION):
            session_id = request.form.get("session_id")
            if session_id:
                payload["session_id"] = session_id.strip()
        if action == ACTION_ADD_TO_GROUP:
            group_id = request.form.get("group_id")
            if group_id:
                payload["group_ids"] = [group_id.strip()]
        flask_session[SESSION_KEY_ACTION_PAYLOAD] = payload
        if action == ACTION_UPDATE and resource in (RESOURCE_PEOPLE, RESOURCE_SESSIONS, "companies"):
            return redirect(url_for("batch_editor.step_action_update"))
        return redirect(url_for("batch_editor.step_review"))

    return render_template(
        "batch_editor/action.html",
        form=form,
        resource=resource,
        scope_count=len(scope_ids),
        event_name=flask_session.get("event_name"),
        sessions=sessions,
        groups=groups,
    )


@batch_editor.route("/action-update", methods=["GET", "POST"])
def step_action_update():
    redir = _require_event()
    if redir:
        return redir
    resource = flask_session.get(SESSION_KEY_RESOURCE)
    action = flask_session.get(SESSION_KEY_ACTION)
    if action != ACTION_UPDATE or resource not in (RESOURCE_PEOPLE, RESOURCE_SESSIONS, "companies"):
        return redirect(url_for("batch_editor.step_action"))

    form = UpdatePeopleForm() if resource == RESOURCE_PEOPLE else UpdateSessionForm() if resource == RESOURCE_SESSIONS else UpdateCompanyForm() if resource == "companies" else None
    if form and form.validate_on_submit():
        payload = {}
        if resource == RESOURCE_PEOPLE:
            if form.first_name.data:
                payload["first_name"] = form.first_name.data.strip()
            if form.last_name.data:
                payload["last_name"] = form.last_name.data.strip()
            if form.email.data:
                payload["email"] = form.email.data.strip()
            if form.title.data:
                payload["title"] = form.title.data.strip()
            if form.company_name.data:
                payload["company_name"] = form.company_name.data.strip()
            if form.chat_enabled.data:
                payload.setdefault("public_preferences", {})["chat_enabled"] = form.chat_enabled.data == "true"
            if form.is_profile_visible.data:
                payload.setdefault("public_preferences", {})["is_profile_visible"] = form.is_profile_visible.data == "true"
        elif resource == RESOURCE_SESSIONS:
            if form.name.data:
                payload["name"] = form.name.data.strip()
            if form.description.data is not None:
                payload["description"] = form.description.data.strip()
        elif resource == "companies":
            if form.name.data:
                payload["name"] = form.name.data.strip()
        flask_session[SESSION_KEY_ACTION_PAYLOAD] = payload
        return redirect(url_for("batch_editor.step_review"))

    return render_template(
        "batch_editor/action_update.html",
        form=form,
        resource=resource,
        event_name=flask_session.get("event_name"),
    )


@batch_editor.route("/review", methods=["GET", "POST"])
def step_review():
    redir = _require_event()
    if redir:
        return redir
    resource = flask_session.get(SESSION_KEY_RESOURCE)
    scope_ids = flask_session.get(SESSION_KEY_SCOPE_IDS)
    action = flask_session.get(SESSION_KEY_ACTION)
    action_payload = flask_session.get(SESSION_KEY_ACTION_PAYLOAD) or {}
    if not resource or not scope_ids or not action:
        return redirect(url_for("batch_editor.step_resource"))

    if request.method == "POST" and request.form.get("confirm"):
        client = get_api_client()
        if not client:
            flash("API client not available.", "error")
            return redirect(url_for("main.index"))
        event_id = flask_session.get("event_id")
        results = execute_batch(
            event_id=event_id,
            resource=resource,
            action=action,
            scope_ids=scope_ids,
            action_payload=action_payload,
            client=client,
        )
        flask_session[SESSION_KEY_RESULTS] = results
        log_action("batch_editor", event_id)
        return redirect(url_for("batch_editor.result"))

    return render_template(
        "batch_editor/review.html",
        resource=resource,
        scope_count=len(scope_ids),
        action=action,
        action_payload=action_payload,
        event_name=flask_session.get("event_name"),
    )


@batch_editor.route("/result")
def result():
    redir = _require_event()
    if redir:
        return redir
    results = flask_session.get(SESSION_KEY_RESULTS)
    if results is None:
        return redirect(url_for("batch_editor.step_resource"))

    success_count = sum(1 for r in results if r.get("success"))
    error_count = len(results) - success_count
    resource = flask_session.get(SESSION_KEY_RESOURCE)
    action = flask_session.get(SESSION_KEY_ACTION)

    return render_template(
        "batch_editor/result.html",
        results=results,
        success_count=success_count,
        error_count=error_count,
        total=len(results),
        resource=resource,
        action=action,
        event_name=flask_session.get("event_name"),
    )


@batch_editor.route("/result/export")
def result_export():
    """Export batch result as CSV (all rows or failures only via ?failures=1)."""
    redir = _require_event()
    if redir:
        return redir
    results = flask_session.get(SESSION_KEY_RESULTS)
    if results is None:
        return redirect(url_for("batch_editor.step_resource"))
    failures_only = request.args.get("failures", "").lower() in ("1", "true", "yes")
    rows = [r for r in results if not r.get("success")] if failures_only else results
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "success", "error"])
    for r in rows:
        writer.writerow([r.get("id", ""), r.get("success", False), r.get("error") or ""])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=batch_result.csv"},
    )
