import pytest

from yt_automation.validation import ScriptValidationError, parse_script_response


VALID_RESPONSE = """
{
  "pillar": "Compound Interest Stories",
  "core_idea": "A modeled investing head start grows over time.",
  "short": {
    "title": "Age 18 vs Age 28",
    "script": "(0-3s) Ten years can change the whole number."
  },
  "long_form": {
    "title": "Age 18 vs Age 28: Who Wins?",
    "script": "[Cold open 0:00-0:15] Ten years can change the whole number."
  },
  "key_numbers": ["$100/month"],
  "compliance_flags": []
}
"""


def test_parse_script_response_accepts_valid_payload():
    payload = parse_script_response(VALID_RESPONSE)

    assert payload["short"]["title"] == "Age 18 vs Age 28"


def test_parse_script_response_rejects_invalid_json():
    with pytest.raises(ScriptValidationError):
        parse_script_response("not json")


def test_parse_script_response_rejects_missing_schema_fields():
    with pytest.raises(ScriptValidationError):
        parse_script_response('{"pillar": "Money Mistakes"}')
