from fastapi import APIRouter

api_v1_router = APIRouter(prefix="/api/v1", tags=["api"])


@api_v1_router.get("")
def api_root() -> dict[str, str]:
    return {"version": "v1"}
