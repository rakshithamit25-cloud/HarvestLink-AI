from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import AgentLog
from app.schemas import AgentLogResponse

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("/agent", response_model=List[AgentLogResponse])
def get_agent_logs(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns real agent execution logs for the Agent Activity Panel:
    Agent name, task, mode (llm/rule-based), input/output summary,
    decision status, execution time in ms, timestamp.
    """
    return db.query(AgentLog).order_by(AgentLog.id.desc()).limit(limit).all()
