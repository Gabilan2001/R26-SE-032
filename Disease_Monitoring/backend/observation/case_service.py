"""Monitoring case helpers."""

from typing import Dict, Optional

from observation.observation_repository import create_case, get_case


def create_monitoring_case(crop_part: str, label: Optional[str] = None) -> Dict:
    return create_case(crop_part, label)


def fetch_case(case_id: str) -> Optional[Dict]:
    return get_case(case_id)
