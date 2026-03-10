from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """Return 204 so browsers stop logging 404 for favicon requests."""
    return Response(status_code=204)


@router.get(
    "/health",
    summary="Health check",
    description="Returns the health status of the API.",
)
async def health_check() -> dict[str, str]:
    """Check if the API is running."""
    return {"status": "healthy"}
