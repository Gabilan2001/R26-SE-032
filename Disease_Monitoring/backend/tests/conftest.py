import pytest


@pytest.fixture(autouse=True)
def _skip_live_secondary_severity(monkeypatch):
    """Keep integration tests off the live vision API; unit tests patch the util directly."""

    def _stub(image_bytes, crop_part, primary_severity):
        cls = str(primary_severity).upper()
        return {
            "verification_status": "SECONDARY_UNAVAILABLE",
            "final_severity": cls,
            "secondary_severity": None,
            "secondary_confidence": None,
            "secondary_estimated_area_percentage": None,
            "secondary_reasoning": None,
        }

    monkeypatch.setattr(
        "observation.observation_service.verify_secondary_severity",
        _stub,
    )
