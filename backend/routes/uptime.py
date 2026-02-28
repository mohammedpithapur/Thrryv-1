from fastapi import APIRouter

router = APIRouter()

@router.get("/uptime-ping")
async def uptime_ping():
    return {"status": "ok"}
