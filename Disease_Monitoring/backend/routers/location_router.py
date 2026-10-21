from fastapi import APIRouter

from utils.location_service import list_known_location_labels

router = APIRouter()


@router.get("/meta/locations")
def known_locations():
    """Curated place names for manual location selection (Sri Lanka)."""
    return {"locations": list_known_location_labels()}
