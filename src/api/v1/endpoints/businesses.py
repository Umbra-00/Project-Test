from fastapi import APIRouter

router = APIRouter()

@router.get("/businesses")
def get_businesses():
    # Placeholder for business logic to fetch businesses
    return [{"id": 1, "name": "Example Business"}]

