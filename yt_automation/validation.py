import json
from typing import Any


REQUIRED_TOP_LEVEL = {
    "pillar",
    "core_idea",
    "short",
    "long_form",
    "key_numbers",
    "compliance_flags",
}


class ScriptValidationError(ValueError):
    """Raised when Claude returns JSON that does not match the expected script schema."""


def parse_script_response(raw_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ScriptValidationError(f"Response was not valid JSON: {exc}") from exc

    validate_script_payload(payload)
    return payload


def validate_script_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ScriptValidationError("Response JSON must be an object.")

    missing = REQUIRED_TOP_LEVEL - set(payload)
    if missing:
        raise ScriptValidationError(f"Response JSON missing fields: {sorted(missing)}")

    for field in ("pillar", "core_idea"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ScriptValidationError(f"`{field}` must be a non-empty string.")

    _validate_script_section(payload["short"], "short")
    _validate_script_section(payload["long_form"], "long_form")

    for field in ("key_numbers", "compliance_flags"):
        if not isinstance(payload[field], list) or not all(isinstance(item, str) for item in payload[field]):
            raise ScriptValidationError(f"`{field}` must be an array of strings.")


def _validate_script_section(section: Any, name: str) -> None:
    if not isinstance(section, dict):
        raise ScriptValidationError(f"`{name}` must be an object.")

    for field in ("title", "script"):
        value = section.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ScriptValidationError(f"`{name}.{field}` must be a non-empty string.")
