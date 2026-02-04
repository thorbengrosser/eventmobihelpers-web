"""
Batch executor: given list of IDs + action (delete, update, resource-specific), loop over IDs, call client, collect results.
Optional rate limiting: small delay between requests to avoid hammering the API.
"""
import logging
import time
from typing import List, Dict, Any, Optional

from app.batch_editor.scope_resolver import RESOURCE_PEOPLE, RESOURCE_SESSIONS, RESOURCE_COMPANIES

logger = logging.getLogger(__name__)

# Optional delay between API calls (seconds) to avoid rate limits
BATCH_DELAY_SECONDS = 0.1

ACTION_DELETE = "delete"
ACTION_UPDATE = "update"
ACTION_ADD_TO_SESSION = "add_to_schedule"
ACTION_REMOVE_FROM_SESSION = "remove_from_schedule"
ACTION_ADD_TO_GROUP = "add_to_group"


def execute_batch(
    event_id: str,
    resource: str,
    action: str,
    scope_ids: List[str],
    action_payload: Optional[dict] = None,
    client: Any = None,
) -> List[Dict[str, Any]]:
    """
    Execute action on each ID in scope_ids. Returns list of { "id", "success", "error" }.
    """
    if not client or not scope_ids:
        return []

    action_payload = action_payload or {}
    results = []
    delay = BATCH_DELAY_SECONDS

    def maybe_delay():
        if delay and delay > 0:
            time.sleep(delay)

    if resource == RESOURCE_PEOPLE:
        if action == ACTION_DELETE:
            for pid in scope_ids:
                maybe_delay()
                try:
                    status_code, _ = client.delete_person(event_id, pid)
                    results.append({"id": pid, "success": status_code in (200, 202, 204), "error": None if status_code in (200, 202, 204) else f"Status {status_code}"})
                except Exception as e:
                    results.append({"id": pid, "success": False, "error": str(e)})
        elif action == ACTION_UPDATE:
            for pid in scope_ids:
                maybe_delay()
                try:
                    client.update_person(event_id, pid, action_payload)
                    results.append({"id": pid, "success": True, "error": None})
                except Exception as e:
                    results.append({"id": pid, "success": False, "error": str(e)})
        elif action == ACTION_ADD_TO_SESSION:
            session_id = action_payload.get("session_id")
            if not session_id:
                return [{"id": pid, "success": False, "error": "Missing session_id"} for pid in scope_ids]
            for pid in scope_ids:
                maybe_delay()
                ok, err = client.add_to_schedule(event_id, pid, session_id)
                results.append({"id": pid, "success": ok, "error": err})
        elif action == ACTION_REMOVE_FROM_SESSION:
            session_id = action_payload.get("session_id")
            if not session_id:
                return [{"id": pid, "success": False, "error": "Missing session_id"} for pid in scope_ids]
            for pid in scope_ids:
                maybe_delay()
                ok, err = client.remove_from_schedule(event_id, pid, session_id)
                results.append({"id": pid, "success": ok, "error": err})
        elif action == ACTION_ADD_TO_GROUP:
            for pid in scope_ids:
                maybe_delay()
                try:
                    person = client.get_person(event_id, pid)
                    current = person.get("groups") or []
                    current_ids = {g.get("id") for g in current if g.get("id")}
                    new_group_ids = action_payload.get("group_ids") or []
                    for gid in new_group_ids:
                        current_ids.add(gid)
                    group_objs = [{"id": gid} for gid in current_ids]
                    client.update_person(event_id, pid, {"groups": group_objs})
                    results.append({"id": pid, "success": True, "error": None})
                except Exception as e:
                    results.append({"id": pid, "success": False, "error": str(e)})
        else:
            results = [{"id": pid, "success": False, "error": f"Unknown action {action}"} for pid in scope_ids]

    elif resource == RESOURCE_SESSIONS:
        if action == ACTION_DELETE:
            for sid in scope_ids:
                maybe_delay()
                try:
                    status_code, _ = client.delete_session(event_id, sid)
                    results.append({"id": sid, "success": status_code in (200, 202, 204), "error": None if status_code in (200, 202, 204) else f"Status {status_code}"})
                except Exception as e:
                    results.append({"id": sid, "success": False, "error": str(e)})
        elif action == ACTION_UPDATE:
            for sid in scope_ids:
                maybe_delay()
                try:
                    client.update_session(event_id, sid, action_payload)
                    results.append({"id": sid, "success": True, "error": None})
                except Exception as e:
                    results.append({"id": sid, "success": False, "error": str(e)})
        else:
            results = [{"id": sid, "success": False, "error": f"Unknown action {action}"} for sid in scope_ids]

    elif resource == RESOURCE_COMPANIES:
        if action == ACTION_DELETE:
            for cid in scope_ids:
                maybe_delay()
                try:
                    status_code, _ = client.delete_company(event_id, cid)
                    results.append({"id": cid, "success": status_code in (200, 202, 204), "error": None if status_code in (200, 202, 204) else f"Status {status_code}"})
                except Exception as e:
                    results.append({"id": cid, "success": False, "error": str(e)})
        elif action == ACTION_UPDATE:
            for cid in scope_ids:
                maybe_delay()
                try:
                    client.update_company(event_id, cid, action_payload)
                    results.append({"id": cid, "success": True, "error": None})
                except Exception as e:
                    results.append({"id": cid, "success": False, "error": str(e)})
        else:
            results = [{"id": cid, "success": False, "error": f"Unknown action {action}"} for cid in scope_ids]

    else:
        results = [{"id": rid, "success": False, "error": f"Unknown resource {resource}"} for rid in scope_ids]

    return results
