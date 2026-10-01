"""Untrusted offline envelopes become validated drafts, never approvals or stock posts."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID


class OfflineValidationError(ValueError):
    http_status_code = 422
    pass


class OfflineConflict(OfflineValidationError):
    http_status_code = 409
    pass


MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 15 * 1024 * 1024
MAX_ATTACHMENTS = 5
MAX_PAYLOAD_CHARS = 32_768
OPERATIONS = {
    "progress": {"work_package", "baseline_version", "activity", "zone", "crew", "posting_date", "qty_reported", "notes", "kit_issue", "cable_reel"},
    "daily_report": {"posting_date", "site", "manpower", "equipment", "weather", "notes"},
    "kit_request": {"kit_template", "work_package", "qty_kits", "from_warehouse", "to_warehouse", "activity", "crew", "zone", "notes"},
    "kit_return": {"kit_issue", "to_warehouse", "returns", "notes"},
    "inspection": {"work_package", "zone", "inspection_type", "posting_date", "checks", "notes"},
}
REQUIRED = {
    "progress": {"work_package", "baseline_version", "activity", "zone", "crew", "posting_date", "qty_reported"},
    "daily_report": {"posting_date", "site"},
    "kit_request": {"kit_template", "work_package", "qty_kits", "from_warehouse", "to_warehouse", "activity", "crew"},
    "kit_return": {"kit_issue", "to_warehouse", "returns"},
    "inspection": {"work_package", "zone", "inspection_type", "posting_date", "checks"},
}


def _text(value: Any, label: str, limit: int = 140) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise OfflineValidationError(f"Invalid {label}")
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise OfflineValidationError(f"Invalid control character in {label}")
    return value


def _quantity(value: Any, label: str, positive: bool = False) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise OfflineValidationError(f"Invalid {label}")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise OfflineValidationError(f"Invalid {label}") from exc
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise OfflineValidationError(f"Invalid {label}")
    if result > Decimal("1000000000000") or result.as_tuple().exponent < -9:
        raise OfflineValidationError(f"{label} exceeds precision or quantity limits")
    return format(result, "f")


def _json_safe(value: Any, depth: int = 0) -> None:
    if depth > 8:
        raise OfflineValidationError("Payload nesting too deep")
    if value is None or isinstance(value, (bool, str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise OfflineValidationError("Nonfinite JSON number")
        return
    if isinstance(value, list):
        if len(value) > 200:
            raise OfflineValidationError("Too many payload rows")
        for item in value:
            _json_safe(item, depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise OfflineValidationError("JSON keys must be text")
            _json_safe(item, depth + 1)
        return
    raise OfflineValidationError("Unsupported payload value")


@dataclass(frozen=True)
class Attachment:
    filename: str
    mime_type: str
    sha256: str
    content: bytes


@dataclass(frozen=True)
class Envelope:
    uuid: str
    operation: str
    project: str
    payload: dict
    attachments: tuple[Attachment, ...]
    base_modified: str | None
    payload_hash: str


def validate_envelope(raw: dict) -> Envelope:
    if not isinstance(raw, dict):
        raise OfflineValidationError("Envelope must be an object")
    unexpected = set(raw) - {"uuid", "operation", "project", "payload", "attachments", "base_modified"}
    if unexpected:
        raise OfflineValidationError("Unexpected envelope fields: " + ", ".join(sorted(unexpected)))
    try:
        identity = UUID(str(raw.get("uuid", "")))
    except (ValueError, TypeError, AttributeError) as exc:
        raise OfflineValidationError("A canonical UUID v4 is required") from exc
    if identity.version != 4 or str(identity) != raw.get("uuid"):
        raise OfflineValidationError("A canonical UUID v4 is required")
    operation = raw.get("operation")
    if operation not in OPERATIONS:
        raise OfflineValidationError("Unsupported offline operation")
    project = _text(raw.get("project"), "project")
    payload = raw.get("payload")
    if not isinstance(payload, dict):
        raise OfflineValidationError("Payload must be an object")
    _json_safe(payload)
    if len(json.dumps(payload, ensure_ascii=False)) > MAX_PAYLOAD_CHARS:
        raise OfflineValidationError("Payload too large")
    if set(payload) - OPERATIONS[operation]:
        raise OfflineValidationError("Payload contains disallowed or trusted-only fields")
    if REQUIRED[operation] - set(payload):
        raise OfflineValidationError("Required draft fields are missing")
    payload = dict(payload)
    for key, value in payload.items():
        if key == "manpower":
            count = Decimal(_quantity(value, key))
            if count != count.to_integral_value():
                raise OfflineValidationError("Manpower must be a whole person count")
            payload[key] = int(count)
        elif key in {"qty_reported", "qty_kits"}:
            payload[key] = _quantity(value, key, positive=True)
        elif key in {"returns", "checks"}:
            if not isinstance(value, list) or not value:
                raise OfflineValidationError(f"{key} requires at least one row")
            result = []
            seen = set()
            for row in value:
                allowed = {"item_code", "qty", "uom"} if key == "returns" else {"check", "result", "notes"}
                required = {"item_code", "qty", "uom"} if key == "returns" else {"check", "result"}
                if not isinstance(row, dict) or set(row) - allowed or required - set(row):
                    raise OfflineValidationError(f"Invalid {key} row")
                row = dict(row)
                for field, item in row.items():
                    row[field] = _quantity(item, "return quantity", positive=True) if field == "qty" else _text(item, field, 1000)
                identifier = row.get("item_code", row.get("check"))
                if identifier in seen:
                    raise OfflineValidationError("Duplicate draft row")
                seen.add(identifier)
                if key == "checks" and row["result"] not in {"Pass", "Fail", "Not Applicable", "Not Checked"}:
                    raise OfflineValidationError("Invalid checklist result")
                result.append(row)
            payload[key] = result
        else:
            payload[key] = _text(value, key, 8000 if key in {"notes", "equipment", "manpower", "weather"} else 140)
            if key == "posting_date":
                try:
                    if date.fromisoformat(value).isoformat() != value:
                        raise ValueError
                except ValueError as exc:
                    raise OfflineValidationError("Invalid ISO posting date") from exc
    attachments = raw.get("attachments", [])
    if not isinstance(attachments, list) or len(attachments) > MAX_ATTACHMENTS:
        raise OfflineValidationError("Too many attachments")
    decoded = []
    total = 0
    for attachment in attachments:
        if not isinstance(attachment, dict) or set(attachment) != {"filename", "mime_type", "sha256", "content_base64"}:
            raise OfflineValidationError("Invalid attachment metadata")
        filename = _text(attachment["filename"], "attachment filename", 120)
        if re.search(r"[\\/:\x00]", filename) or filename in {".", ".."}:
            raise OfflineValidationError("Invalid attachment filename")
        encoded = attachment["content_base64"]
        if not isinstance(encoded, str) or len(encoded) > (MAX_ATTACHMENT_BYTES * 4 // 3 + 8):
            raise OfflineValidationError("Attachment too large")
        try:
            content = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise OfflineValidationError("Attachment encoding invalid") from exc
        mime = attachment["mime_type"]
        signatures = {"image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff"}
        if mime not in signatures or not content.startswith(signatures[mime]):
            raise OfflineValidationError("Only PNG/JPEG evidence is supported")
        digest = hashlib.sha256(content).hexdigest()
        if digest != attachment["sha256"]:
            raise OfflineValidationError("Attachment checksum mismatch")
        if digest in {item.sha256 for item in decoded}:
            raise OfflineValidationError("Duplicate attachment")
        total += len(content)
        if len(content) > MAX_ATTACHMENT_BYTES or total > MAX_TOTAL_BYTES:
            raise OfflineValidationError("Attachment size limit exceeded")
        decoded.append(Attachment(filename, mime, digest, content))
    modified = raw.get("base_modified")
    if modified is not None:
        modified = _text(modified, "base modification timestamp", 40)
    canonical = {"operation": operation, "project": project, "payload": payload, "base_modified": modified,
                 "attachments": [{"filename": item.filename, "mime_type": item.mime_type, "sha256": item.sha256} for item in decoded]}
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return Envelope(str(identity), operation, project, payload, tuple(decoded), modified, digest)


def receipt_identity(actor: str, uuid: str) -> str:
    _text(actor, "authenticated actor")
    return hashlib.sha256((actor + "\x00" + uuid).encode()).hexdigest()


def check_retry(existing: dict, actor: str, envelope: Envelope) -> dict:
    if existing.get("sync_user") != actor or existing.get("project") != envelope.project:
        raise OfflineConflict("Draft belongs to another user or project")
    if existing.get("payload_hash") != envelope.payload_hash:
        raise OfflineConflict("UUID was already used with different content; preserve the original draft")
    if existing.get("status") != "Accepted":
        raise OfflineConflict("Previous synchronization is not complete; retry later")
    return {"status": "synced", "uuid": envelope.uuid, "doctype": existing.get("reference_doctype"),
            "name": existing.get("reference_name"), "duplicate": True, "docstatus": 0}
