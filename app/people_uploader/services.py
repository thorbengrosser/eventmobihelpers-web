import json
import os
import tempfile
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import openpyxl

BATCH_DELAY_SECONDS = 0.1
_TEMP_DIR = tempfile.gettempdir()
_TEMP_PREFIX = "em_uploader_"
_TEMP_TTL_SECONDS = 3600  # 1 hour

# EventMobi fields that map to nested social_links
_SOCIAL_FIELD_MAP = {
    "social_twitter": ("social_links", "twitter"),
    "social_facebook": ("social_links", "facebook"),
    "social_linkedin": ("social_links", "linkedin"),
}

# Fields that map to public_preferences
_PREF_FIELD_MAP = {
    "is_profile_visible": "is_profile_visible",
    "chat_enabled": "chat_enabled",
}


# ---------------------------------------------------------------------------
# Excel parsing
# ---------------------------------------------------------------------------

def parse_excel(file_storage) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Parse an uploaded FileStorage (.xlsx) into (headers, rows).

    Returns:
        headers: list of column names from row 1
        rows: list of dicts {header: cell_value} for data rows
    Raises ValueError on empty or unreadable files.
    """
    wb = openpyxl.load_workbook(file_storage, read_only=True, data_only=True)
    ws = wb.active
    all_rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not all_rows:
        raise ValueError("The uploaded file has no rows.")

    raw_headers = all_rows[0]
    headers = [
        str(h).strip() if h is not None else f"Column_{i + 1}"
        for i, h in enumerate(raw_headers)
    ]

    if not headers:
        raise ValueError("The uploaded file has no columns.")

    rows = []
    for raw_row in all_rows[1:]:
        row_dict = {}
        for i, header in enumerate(headers):
            cell = raw_row[i] if i < len(raw_row) else None
            row_dict[header] = str(cell).strip() if cell is not None else ""
        rows.append(row_dict)

    # Drop fully-empty rows
    rows = [r for r in rows if any(v for v in r.values())]
    return headers, rows


def get_column_samples(rows: List[Dict], headers: List[str], n: int = 3) -> Dict[str, List[str]]:
    """Return up to n non-empty sample values per column."""
    samples: Dict[str, List[str]] = {h: [] for h in headers}
    for row in rows:
        for h in headers:
            if len(samples[h]) < n:
                val = row.get(h, "")
                if val:
                    samples[h].append(val)
        if all(len(samples[h]) >= n for h in headers):
            break
    return samples


# ---------------------------------------------------------------------------
# Temp file storage (avoids Flask session size limits)
# ---------------------------------------------------------------------------

def save_rows_to_tempfile(rows: List[Dict]) -> str:
    """Serialize rows to a JSON temp file. Returns a UUID token."""
    token = str(uuid.uuid4())
    path = os.path.join(_TEMP_DIR, f"{_TEMP_PREFIX}{token}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    return token


def load_rows_from_tempfile(token: str) -> Optional[List[Dict]]:
    """Load rows from temp file by token. Returns None if not found or expired."""
    if not token:
        return None
    path = os.path.join(_TEMP_DIR, f"{_TEMP_PREFIX}{token}.json")
    if not os.path.exists(path):
        return None
    mtime = os.path.getmtime(path)
    if time.time() - mtime > _TEMP_TTL_SECONDS:
        try:
            os.remove(path)
        except OSError:
            pass
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_tempfile(token: str) -> None:
    """Delete a temp file by token (best-effort)."""
    if not token:
        return
    path = os.path.join(_TEMP_DIR, f"{_TEMP_PREFIX}{token}.json")
    try:
        os.remove(path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Field mapping helpers
# ---------------------------------------------------------------------------

def build_api_body(row: Dict, column_mapping: Dict[str, str]) -> Dict:
    """Convert one Excel row into an EventMobi API body dict.

    column_mapping: {excel_col_name: eventmobi_field_key or ""}
    Columns mapped to "" are ignored. Empty cell values are skipped.

    Custom fields (keys prefixed with "custom_field:") are collected into
    a "custom_fields" list: [{"id": "<field_id>", "value": "<value>"}, ...]
    """
    body: Dict[str, Any] = {}
    custom_fields: list = []

    for excel_col, em_field in column_mapping.items():
        if not em_field:
            continue
        value = row.get(excel_col, "")
        if value == "":
            continue

        if em_field.startswith("custom_field:"):
            field_id = em_field.split(":", 1)[1]
            custom_fields.append({"id": field_id, "value": value})
        elif em_field in _SOCIAL_FIELD_MAP:
            outer, inner = _SOCIAL_FIELD_MAP[em_field]
            body.setdefault(outer, {})[inner] = value
        elif em_field in _PREF_FIELD_MAP:
            pref_key = _PREF_FIELD_MAP[em_field]
            bool_val = value.lower() in ("true", "1", "yes")
            body.setdefault("public_preferences", {})[pref_key] = bool_val
        else:
            body[em_field] = value

    if custom_fields:
        body["custom_fields"] = custom_fields

    return body


def get_match_value_from_row(
    row: Dict,
    column_mapping: Dict[str, str],
    match_field: str,
) -> str:
    """Extract the match value from a row based on match_field strategy.

    For first_last_name: concatenates the values of the first_name and last_name
    mapped columns as "First Last".
    """
    if match_field == "first_last_name":
        first_col = next((col for col, f in column_mapping.items() if f == "first_name"), None)
        last_col = next((col for col, f in column_mapping.items() if f == "last_name"), None)
        first = row.get(first_col, "") if first_col else ""
        last = row.get(last_col, "") if last_col else ""
        return f"{first} {last}".strip()
    else:
        match_col = next((col for col, f in column_mapping.items() if f == match_field), None)
        return row.get(match_col, "") if match_col else ""


def lookup_person(
    client,
    event_id: str,
    match_field: str,
    match_value: str,
) -> Optional[Dict]:
    """Find a person in EventMobi. Returns person dict or None."""
    if not match_value:
        return None
    try:
        if match_field == "email":
            results = client.list_people(event_id, email=match_value)
            return results[0] if results else None
        elif match_field == "id":
            return client.get_person(event_id, match_value)
        elif match_field == "first_last_name":
            results = client.list_people(event_id, search=match_value)
            return results[0] if results else None
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Preview (dry-run, first N rows with real API lookups)
# ---------------------------------------------------------------------------

def build_preview(
    rows: List[Dict],
    column_mapping: Dict[str, str],
    match_field: str,
    missing_action: str,
    client,
    event_id: str,
    max_preview: int = 10,
) -> Tuple[List[Dict], Dict]:
    """Dry-run over the first max_preview rows.

    Returns:
        preview_rows: list of result dicts per row
        counts: {"n_update": N, "create": N, "skip": N, "error": N, "total": N, "preview_only": bool}
    Note: key is "n_update" (not "update") to avoid Jinja2's getattr-first lookup returning
    the built-in dict.update() method instead of the integer value.
    """
    preview_rows = []
    counts = {"n_update": 0, "create": 0, "skip": 0, "error": 0}

    for i, row in enumerate(rows[:max_preview]):
        match_value = get_match_value_from_row(row, column_mapping, match_field)
        api_body = build_api_body(row, column_mapping)
        warning = None

        if not match_value:
            action = "skip"
            person_id = None
            warning = "No match value found in this row."
        else:
            person = lookup_person(client, event_id, match_field, match_value)
            if person:
                action = "update"
                person_id = person.get("id")
            elif missing_action == "create":
                action = "create"
                person_id = None
                if not api_body.get("first_name") or not api_body.get("last_name"):
                    action = "error"
                    warning = "Create requires first_name and last_name to be mapped."
            else:
                action = "skip"
                person_id = None

        count_key = "n_update" if action == "update" else action
        counts[count_key] += 1
        preview_rows.append({
            "row_num": i + 2,
            "match_value": match_value,
            "action": action,
            "person_id": person_id,
            "fields": list(api_body.keys()),
            "warning": warning,
        })

        time.sleep(BATCH_DELAY_SECONDS)

    counts["total"] = len(rows)
    counts["preview_only"] = len(rows) > max_preview
    return preview_rows, counts


# ---------------------------------------------------------------------------
# Full execution
# ---------------------------------------------------------------------------

def execute_upload(
    rows: List[Dict],
    column_mapping: Dict[str, str],
    match_field: str,
    missing_action: str,
    client,
    event_id: str,
) -> List[Dict]:
    """Execute the full upload. Returns a list of result dicts."""
    results = []

    for i, row in enumerate(rows):
        match_value = get_match_value_from_row(row, column_mapping, match_field)
        api_body = build_api_body(row, column_mapping)
        row_num = i + 2

        if not match_value:
            results.append({
                "row_num": row_num,
                "match_value": "",
                "action": "skip",
                "person_id": None,
                "success": True,
                "error": None,
                "status": "skipped (no match value)",
            })
            continue

        time.sleep(BATCH_DELAY_SECONDS)
        person = lookup_person(client, event_id, match_field, match_value)

        if person:
            person_id = person.get("id")
            try:
                time.sleep(BATCH_DELAY_SECONDS)
                client.update_person(event_id, person_id, api_body)
                results.append({
                    "row_num": row_num,
                    "match_value": match_value,
                    "action": "update",
                    "person_id": person_id,
                    "success": True,
                    "error": None,
                    "status": "updated",
                })
            except Exception as e:
                results.append({
                    "row_num": row_num,
                    "match_value": match_value,
                    "action": "update",
                    "person_id": person_id,
                    "success": False,
                    "error": str(e),
                    "status": "error",
                })

        elif missing_action == "create":
            if not api_body.get("first_name") or not api_body.get("last_name"):
                results.append({
                    "row_num": row_num,
                    "match_value": match_value,
                    "action": "create",
                    "person_id": None,
                    "success": False,
                    "error": "first_name and last_name are required to create a person",
                    "status": "error",
                })
                continue
            try:
                time.sleep(BATCH_DELAY_SECONDS)
                new_person = client.create_person(event_id, api_body)
                results.append({
                    "row_num": row_num,
                    "match_value": match_value,
                    "action": "create",
                    "person_id": new_person.get("id") if new_person else None,
                    "success": True,
                    "error": None,
                    "status": "created",
                })
            except Exception as e:
                results.append({
                    "row_num": row_num,
                    "match_value": match_value,
                    "action": "create",
                    "person_id": None,
                    "success": False,
                    "error": str(e),
                    "status": "error",
                })
        else:
            results.append({
                "row_num": row_num,
                "match_value": match_value,
                "action": "skip",
                "person_id": None,
                "success": True,
                "error": None,
                "status": "skipped (not found)",
            })

    return results
