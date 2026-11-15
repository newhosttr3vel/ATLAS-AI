"""HTTP API for personal software-engineering workspaces."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import AuditLog
from backend.security import RequestContext, get_request_context, require_roles
from backend.engineering.models import EngineeringRun
from backend.engineering.schemas import EngineeringRunCreate, EngineeringRunRead
from backend.engineering.orchestrator import EngineeringOrchestrator

router = APIRouter(prefix="/api/engineering", tags=["software-engineering"])
orchestrator = EngineeringOrchestrator()

@router.post("/runs", response_model=EngineeringRunRead, status_code=201)
def create_engineering_run(
    payload: EngineeringRunCreate,
    db: Session = Depends(get_db),
    context: RequestContext = Depends(require_roles("owner", "admin", "manager")),
) -> EngineeringRun:
    result = orchestrator.run(context.agency_id, payload.workspace, payload.prompt, payload.max_steps)
    record = EngineeringRun(
        agency_id=context.agency_id, workspace=payload.workspace, prompt=payload.prompt,
        status=result["status"], mode=result["mode"], summary=result["summary"],
        logs=result["logs"], changed_files=result["changed_files"],
    )
    db.add(record)
    db.flush()
    db.add(AuditLog(
        agency_id=context.agency_id, actor_id=context.user_id, action="engineering.run_created",
        entity_type="engineering_run", entity_id=record.id,
        details={"workspace":payload.workspace,"status":result["status"],"mode":result["mode"]},
    ))
    db.commit()
    db.refresh(record)
    return record

@router.get("/runs", response_model=list[EngineeringRunRead])
def list_engineering_runs(
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
    limit: int = Query(default=30, ge=1, le=100),
) -> list[EngineeringRun]:
    statement = select(EngineeringRun).where(EngineeringRun.agency_id == context.agency_id)
    statement = statement.order_by(EngineeringRun.created_at.desc()).limit(limit)
    return list(db.scalars(statement).all())
