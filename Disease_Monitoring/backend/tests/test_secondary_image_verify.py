"""Tests for secondary image verification helpers."""

from ml.predict.secondary_image_verify import (
    _extract_json,
    _farmer_reject,
    _is_matching_crop,
)


def test_extract_json_plain():
    data = _extract_json('{"valid": true, "object_type": "tomato_leaf"}')
    assert data["valid"] is True
    assert data["object_type"] == "tomato_leaf"


def test_extract_json_fenced():
    data = _extract_json('Here:\n```json\n{"valid": false, "object_type": "other"}\n```')
    assert data["valid"] is False


def test_matching_crop_aliases():
    assert _is_matching_crop("LEAF", {"valid": True, "object_type": "tomato_leaf"})
    assert _is_matching_crop("LEAF", {"valid": False, "object_type": "tomato leaf"})
    assert _is_matching_crop("FRUIT", {"valid": True, "object_type": "tomato"})
    assert not _is_matching_crop("LEAF", {"valid": False, "object_type": "other"})
    assert not _is_matching_crop("FRUIT", {"valid": False, "object_type": "apple"})


def test_farmer_messages_have_no_provider_branding():
    for part in ("LEAF", "FRUIT"):
        msg = _farmer_reject(part).lower()
        assert "gemini" not in msg
        assert "google" not in msg
