from fastapi import APIRouter
from app.services.audit_log import list_logs
router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("")
async def logs():
    return list_logs()
