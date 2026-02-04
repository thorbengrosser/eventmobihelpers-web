"""
Resolve scope to a list of resource IDs.
- Single: resolve lookup (e.g. email, external_id) to one ID; return [id].
- Batch by IDs: parse and deduplicate list of IDs.
- Batch by criteria: call API list with filters and pagination; return list of ids.
"""
import logging
import re
from typing import List, Optional, Any

logger = logging.getLogger(__name__)

RESOURCE_PEOPLE = "people"
RESOURCE_SESSIONS = "sessions"
RESOURCE_COMPANIES = "companies"


# Simple heuristic: contains @ and has a dot after @ (e.g. user@domain.com)
_EMAIL_RE = re.compile(r".*@.+\..+")


def _looks_like_email(s: str) -> bool:
    if not s or not s.strip():
        return False
    s = s.strip()
    return bool(_EMAIL_RE.fullmatch(s))


def _parse_id_list(raw: str) -> List[str]:
    """Parse textarea/list of IDs or emails (newlines, commas, spaces). Deduplicate and strip."""
    if not raw or not raw.strip():
        return []
    parts = re.split(r"[,\s\n]+", raw.strip())
    seen = set()
    out = []
    for p in parts:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _resolve_people_batch_tokens(event_id: str, tokens: List[str], client: Any) -> List[str]:
    """Resolve a list of tokens (IDs or emails) to people IDs. Emails are looked up via API."""
    ids = []
    for token in tokens:
        if _looks_like_email(token):
            try:
                people = client.list_people(event_id, email=token)
                if people and people[0].get("id"):
                    ids.append(people[0]["id"])
                # else: email not found, skip (or could collect errors)
            except Exception as e:
                logger.debug("resolve email %s: %s", token, e)
        else:
            ids.append(token)
    return ids


def resolve_scope(
    resource: str,
    event_id: str,
    single_or_batch: str,
    by_ids: Optional[str] = None,
    criteria: Optional[dict] = None,
    client: Any = None,
) -> List[str]:
    """
    Resolve scope to a list of resource IDs.
    single_or_batch: "single" or "batch"
    by_ids: for batch, raw text of IDs (textarea). For single, the single ID or lookup value (e.g. email).
    criteria: for batch, dict of API filter params (e.g. group_ids, registration_status, track_id).
    Returns list of IDs (length 1 for single).
    """
    if not client:
        return []

    if single_or_batch == "single":
        if not by_ids or not str(by_ids).strip():
            return []
        lookup = str(by_ids).strip()
        if resource == RESOURCE_PEOPLE:
            # Lookup by email or use as people_id
            people = client.list_people(event_id, email=lookup)
            if people:
                return [people[0].get("id")]
            # Try as id
            try:
                p = client.get_person(event_id, lookup)
                if p and p.get("id"):
                    return [p["id"]]
            except Exception:
                pass
            return []
        if resource == RESOURCE_SESSIONS:
            sessions = client.list_sessions(event_id, external_id=lookup)
            if sessions:
                return [sessions[0].get("id")]
            try:
                s = client.get_session(event_id, lookup)
                if s and s.get("id"):
                    return [s["id"]]
            except Exception:
                pass
            return []
        if resource == RESOURCE_COMPANIES:
            try:
                c = client.get_company(event_id, lookup)
                if c and c.get("id"):
                    return [c["id"]]
            except Exception:
                pass
            companies = client.list_companies(event_id, external_id=lookup)
            if companies:
                return [companies[0].get("id")]
            return []

    if single_or_batch == "batch":
        if by_ids:
            tokens = _parse_id_list(by_ids)
            if resource == RESOURCE_PEOPLE and tokens:
                return _resolve_people_batch_tokens(event_id, tokens, client)
            return tokens
        if criteria:
            if resource == RESOURCE_PEOPLE:
                try:
                    items = client.list_people(event_id, **criteria)
                    return [item.get("id") for item in (items or []) if item.get("id")]
                except Exception as e:
                    logger.warning("resolve_scope people by criteria failed: %s", e)
                    return []
            if resource == RESOURCE_SESSIONS:
                try:
                    items = client.list_sessions(event_id, **criteria)
                    return [item.get("id") for item in (items or []) if item.get("id")]
                except Exception as e:
                    logger.warning("resolve_scope sessions by criteria failed: %s", e)
                    return []
            if resource == RESOURCE_COMPANIES:
                try:
                    items = client.list_companies(event_id, **criteria)
                    return [item.get("id") for item in (items or []) if item.get("id")]
                except Exception as e:
                    logger.warning("resolve_scope companies by criteria failed: %s", e)
                    return []
        return []

    return []
