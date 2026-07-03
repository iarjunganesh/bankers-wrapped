from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.config import Settings, get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    pipeline_version: str
    plaid_enabled: bool = False


@router.get("/health", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        pipeline_version=settings.pipeline_version,
        # Lets the frontend show "Connect a bank (sandbox)" only when usable
        plaid_enabled=settings.plaid_enabled,
    )
