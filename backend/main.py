"""ATLAS AI FastAPI application."""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.agents.general_manager import GeneralManagerAgent
from backend.agents.report_writer import ReportWriterAgent
from backend.database import SessionLocal, engine, get_db
from backend.models import Agency, AuditLog, Base, Lead, Task
from backend.auth import router as auth_router, workspace_router
from backend.security import RequestContext, get_request_context, require_roles, validate_auth_config
from backend.schemas import (
    LeadCreate,
    LeadRead,
    TaskApprove,
    TaskCreate,
    TaskEdit,
    TaskRead,
    TaskReject,
    ReportGenerate,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_auth_config()
    Base.metadata.create_all(bind=engine)
    # Preserve the existing demo workspace after upgrading the database schema.
    with SessionLocal() as db:
        if db.get(Agency, "demo-agency") is None:
            db.add(
                Agency(
                    id="demo-agency",
                    name="ATLAS AI Demo Agency",
                    slug="demo-agency",
                    plan="prototype",
                    default_currency="EGP",
                    timezone="Africa/Cairo",
                )
            )
            db.commit()
    yield


app = FastAPI(
    title="ATLAS AI API",
    description="Cloud-first API for a travel-agency multi-agent platform.",
    version="0.5.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(workspace_router)

general_manager = GeneralManagerAgent()
report_writer = ReportWriterAgent()
STANDARD_RESULT_KEYS = {
    "result",
    "confidence",
    "assumptions",
    "risks",
    "next_action",
    "requires_owner_approval",
}


def _agency_id(context: RequestContext = Depends(get_request_context)) -> str:
    """Resolve the tenant from a verified membership, or a dev-only legacy selector."""
    return context.agency_id


def _get_lead(db: Session, lead_id: str, agency_id: str) -> Lead:
    lead = db.scalar(select(Lead).where(Lead.id == lead_id, Lead.agency_id == agency_id))
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return lead


def _get_task(db: Session, task_id: str, agency_id: str) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.agency_id == agency_id))
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


def _write_audit(
    db: Session,
    *,
    agency_id: str,
    action: str,
    entity_type: str,
    entity_id: str | None,
    details: dict[str, Any] | None = None,
    actor_id: str = "prototype-owner",
) -> None:
    """Store a minimal event attributed to the signed-in user when available."""
    db.add(
        AuditLog(
            agency_id=agency_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )
    )


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "app": "ATLAS AI",
        "status": "running",
        "api_docs": "/docs",
        "mode": "mock",
    }


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": "ATLAS AI",
        "mode": "mock",
    }


@app.post("/api/leads", response_model=LeadRead, status_code=status.HTTP_201_CREATED, tags=["leads"])
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    context: RequestContext = Depends(require_roles("owner", "admin", "manager", "agent")),
) -> Lead:
    if payload.travel_start and payload.travel_end and payload.travel_end < payload.travel_start:
        raise HTTPException(status_code=422, detail="travel_end must be on or after travel_start.")

    lead = Lead(agency_id=agency_id, **payload.model_dump())
    db.add(lead)
    db.flush()
    _write_audit(
        db,
        agency_id=agency_id,
        action="lead.created",
        entity_type="lead",
        entity_id=lead.id,
        details={"destination": lead.destination},
        actor_id=context.user_id,
    )
    db.commit()
    db.refresh(lead)
    return lead


@app.get("/api/leads", response_model=list[LeadRead], tags=["leads"])
def list_leads(
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Lead]:
    statement = (
        select(Lead)
        .where(Lead.agency_id == agency_id)
        .order_by(Lead.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@app.post("/api/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    context: RequestContext = Depends(require_roles("owner", "admin", "manager", "agent")),
) -> Task:
    lead = _get_lead(db, payload.lead_id, agency_id)
    started = perf_counter()
    try:
        assigned_agent_id, agent_response = general_manager.dispatch(
            payload.task_type,
            lead,
            payload.instructions,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    duration_ms = round((perf_counter() - started) * 1000)

    title_map = {
        "qualify_lead": f"تأهيل عميل: {lead.customer_name}",
        "build_offer": f"إعداد مسودة عرض: {lead.customer_name}",
        "prepare_cost_sheet": f"مراجعة تكاليف: {lead.customer_name}",
        "draft_invoice": f"مسودة فاتورة: {lead.customer_name}",
        "draft_marketing_content": f"محتوى تسويقي: {lead.customer_name}",
        "draft_customer_reply": f"مسودة رد للعميل: {lead.customer_name}",
        "classify_complaint": f"تصنيف شكوى: {lead.customer_name}",
    }
    task = Task(
        agency_id=agency_id,
        lead_id=lead.id,
        task_type=payload.task_type,
        title=title_map[payload.task_type],
        assigned_agent_id=assigned_agent_id,
        status="pending_approval",
        input_data={
            "instructions": payload.instructions,
            "mode": "mock",
            "routed_by": "general_manager",
        },
        result=agent_response,
        confidence=float(agent_response["confidence"]),
        requires_owner_approval=bool(agent_response["requires_owner_approval"]),
        duration_ms=duration_ms,
    )

    if payload.task_type == "qualify_lead":
        qualification = agent_response["result"]["qualification_status"]
        lead.status = qualification

    db.add(task)
    db.flush()
    _write_audit(
        db,
        agency_id=agency_id,
        action="task.created",
        entity_type="task",
        entity_id=task.id,
        details={"task_type": task.task_type, "assigned_agent_id": task.assigned_agent_id},
        actor_id=context.user_id,
    )
    db.commit()
    db.refresh(task)
    return task


@app.get("/api/tasks", response_model=list[TaskRead], tags=["tasks"])
def list_tasks(
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    task_status: str | None = Query(default=None, alias="status"),
    task_type: str | None = Query(default=None),
    lead_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Task]:
    statement = select(Task).where(Task.agency_id == agency_id)
    if task_status:
        statement = statement.where(Task.status == task_status)
    if lead_id:
        statement = statement.where(Task.lead_id == lead_id)
    if task_type:
        statement = statement.where(Task.task_type == task_type)
    statement = statement.order_by(Task.created_at.desc()).limit(limit)
    return list(db.scalars(statement).all())


@app.get("/api/tasks/{task_id}", response_model=TaskRead, tags=["tasks"])
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
) -> Task:
    return _get_task(db, task_id, agency_id)


@app.post("/api/tasks/{task_id}/approve", response_model=TaskRead, tags=["tasks"])
def approve_task(
    task_id: str,
    payload: TaskApprove,
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    context: RequestContext = Depends(require_roles("owner", "admin")),
) -> Task:
    task = _get_task(db, task_id, agency_id)
    if task.status != "pending_approval":
        raise HTTPException(status_code=409, detail="Only pending tasks can be approved.")
    task.status = "approved"
    task.owner_decision_notes = payload.notes
    _write_audit(db, agency_id=agency_id, action="task.approved", entity_type="task", entity_id=task.id, details={"task_type": task.task_type}, actor_id=context.user_id)
    db.commit()
    db.refresh(task)
    return task


@app.post("/api/tasks/{task_id}/reject", response_model=TaskRead, tags=["tasks"])
def reject_task(
    task_id: str,
    payload: TaskReject,
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    context: RequestContext = Depends(require_roles("owner", "admin")),
) -> Task:
    task = _get_task(db, task_id, agency_id)
    if task.status != "pending_approval":
        raise HTTPException(status_code=409, detail="Only pending tasks can be rejected.")
    task.status = "rejected"
    task.owner_decision_notes = payload.reason
    _write_audit(db, agency_id=agency_id, action="task.rejected", entity_type="task", entity_id=task.id, details={"task_type": task.task_type}, actor_id=context.user_id)
    db.commit()
    db.refresh(task)
    return task


@app.post("/api/tasks/{task_id}/edit", response_model=TaskRead, tags=["tasks"])
def edit_task(
    task_id: str,
    payload: TaskEdit,
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    context: RequestContext = Depends(require_roles("owner", "admin")),
) -> Task:
    task = _get_task(db, task_id, agency_id)
    if task.status != "pending_approval":
        raise HTTPException(status_code=409, detail="Only pending tasks can be edited.")
    missing = STANDARD_RESULT_KEYS.difference(payload.result)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Edited result is missing required fields: {', '.join(sorted(missing))}",
        )
    if payload.result.get("requires_owner_approval") is not True:
        raise HTTPException(status_code=422, detail="Owner approval cannot be removed by editing.")
    task.result = payload.result
    task.confidence = float(payload.result["confidence"])
    task.owner_decision_notes = payload.notes
    task.status = "pending_approval"
    _write_audit(db, agency_id=agency_id, action="task.edited", entity_type="task", entity_id=task.id, details={"task_type": task.task_type}, actor_id=context.user_id)
    db.commit()
    db.refresh(task)
    return task


@app.get("/api/workspace", tags=["workspace"])
def get_workspace(
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    context: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    agency = db.get(Agency, agency_id)
    if agency is None:
        raise HTTPException(status_code=404, detail="Agency workspace is not registered.")
    return {
        "agency_id": agency.id,
        "name": agency.name,
        "slug": agency.slug,
        "status": agency.status,
        "plan": agency.plan,
        "default_currency": agency.default_currency,
        "timezone": agency.timezone,
        "created_at": agency.created_at.isoformat(),
        "tenant_security": "signed_bearer_membership" if context.authenticated else "prototype_header_only",
        "authentication_enabled": context.authenticated,
        "current_role": context.role,
    }


@app.get("/api/audit", tags=["audit"])
def list_audit_events(
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    events = db.scalars(
        select(AuditLog)
        .where(AuditLog.agency_id == agency_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": event.id,
            "agency_id": event.agency_id,
            "actor_id": event.actor_id,
            "action": event.action,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "details": event.details,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]


@app.get("/api/agents", tags=["agents"])
def list_agents(
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
) -> list[dict[str, Any]]:
    definitions = [
        {"agent_id": "general_manager", "name": "General Manager", "role": "Routes requests and coordinates departments for owner review.", "manager_id": None, "department": "Management", "is_manager": True},
        {"agent_id": "sales_crew", "name": "Sales Manager", "role": "Coordinates lead qualification and draft offer preparation.", "manager_id": "general_manager", "department": "Sales", "is_manager": True},
        {"agent_id": "lead_qualifier", "name": "Lead Qualifier Agent", "role": "Checks lead completeness and identifies missing travel details.", "manager_id": "sales_crew", "department": "Sales"},
        {"agent_id": "offer_builder", "name": "Offer Builder Agent", "role": "Creates draft package structures without invented prices or availability.", "manager_id": "sales_crew", "department": "Sales"},
        {"agent_id": "finance_manager", "name": "Finance Manager", "role": "Coordinates cost review and invoice preparation; owner approval required.", "manager_id": "general_manager", "department": "Finance", "is_manager": True},
        {"agent_id": "costing_agent", "name": "Costing Agent", "role": "Prepares cost worksheets and flags missing supplier quotes; never invents prices.", "manager_id": "finance_manager", "department": "Finance"},
        {"agent_id": "invoice_agent", "name": "Invoice Agent", "role": "Prepares internal invoice drafts; cannot issue or collect payments.", "manager_id": "finance_manager", "department": "Finance"},
        {"agent_id": "marketing_manager", "name": "Marketing Manager", "role": "Coordinates reviewable campaign content and marketing work.", "manager_id": "general_manager", "department": "Marketing", "is_manager": True},
        {"agent_id": "marketing_content_agent", "name": "Content Agent", "role": "Drafts bilingual travel copy from recorded facts without unverified claims.", "manager_id": "marketing_manager", "department": "Marketing"},
        {"agent_id": "customer_success_manager", "name": "Customer Success Manager", "role": "Coordinates support and complaint handling; no automatic customer contact.", "manager_id": "general_manager", "department": "Customer Success", "is_manager": True},
        {"agent_id": "support_agent", "name": "Support Agent", "role": "Drafts customer replies for employee review; never sends messages.", "manager_id": "customer_success_manager", "department": "Customer Success"},
        {"agent_id": "complaint_handler", "name": "Complaint Handler", "role": "Classifies complaint notes and suggests human review steps.", "manager_id": "customer_success_manager", "department": "Customer Success"},
        {"agent_id": "reporting_manager", "name": "Reporting Manager", "role": "Oversees reports generated from agency records.", "manager_id": "general_manager", "department": "Reporting", "is_manager": True},
        {"agent_id": "report_writer", "name": "Report Writer", "role": "Summarizes recorded operational metrics; no external data is assumed.", "manager_id": "reporting_manager", "department": "Reporting"},
    ]
    response: list[dict[str, Any]] = []
    for definition in definitions:
        tasks = list(
            db.scalars(
                select(Task)
                .where(
                    Task.agency_id == agency_id,
                    Task.assigned_agent_id == definition["agent_id"],
                )
                .order_by(Task.created_at.desc())
                .limit(5)
            ).all()
        )
        response.append(
            {
                **definition,
                "status": "review_pending" if any(t.status == "pending_approval" for t in tasks) else "idle",
                "assigned_tasks_count": db.scalar(
                    select(func.count(Task.id)).where(
                        Task.agency_id == agency_id,
                        Task.assigned_agent_id == definition["agent_id"],
                    )
                ) or 0,
                "latest_confidence": tasks[0].confidence if tasks else None,
                "recent_outputs": [t.result for t in tasks[:3]],
                "risks": ["Prototype agent running in deterministic mock mode; no live supplier data."],
            }
        )
    return response


@app.get("/api/reports/weekly", tags=["reports"])
def weekly_report(
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
) -> dict[str, Any]:
    """Return a seven-day operational summary from this agency's stored records."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=7)

    lead_filter = (Lead.agency_id == agency_id, Lead.created_at >= since)
    task_filter = (Task.agency_id == agency_id, Task.created_at >= since)

    leads_created = db.scalar(
        select(func.count(Lead.id)).where(*lead_filter)
    ) or 0
    tasks_created = db.scalar(
        select(func.count(Task.id)).where(*task_filter)
    ) or 0

    lead_status_counts = {
        name: db.scalar(
            select(func.count(Lead.id)).where(*lead_filter, Lead.status == name)
        ) or 0
        for name in ("new", "needs_information", "qualified")
    }
    task_status_counts = {
        name: db.scalar(
            select(func.count(Task.id)).where(*task_filter, Task.status == name)
        ) or 0
        for name in ("pending_approval", "approved", "rejected")
    }

    task_types = (
        db.execute(
            select(Task.task_type, func.count(Task.id))
            .where(*task_filter)
            .group_by(Task.task_type)
        ).all()
    )
    task_type_counts = {task_type: count for task_type, count in task_types}

    department_for_task = {
        "qualify_lead": "Sales",
        "build_offer": "Sales",
        "prepare_cost_sheet": "Finance",
        "draft_invoice": "Finance",
        "draft_marketing_content": "Marketing",
        "draft_customer_reply": "Customer Success",
        "classify_complaint": "Customer Success",
        "generate_weekly_report": "Reporting",
    }
    department_task_counts = {
        name: 0 for name in ("Sales", "Finance", "Marketing", "Customer Success", "Reporting")
    }
    for task_type, count in task_types:
        department = department_for_task.get(task_type, "Other")
        if department in department_task_counts:
            department_task_counts[department] += count

    decision_count = task_status_counts["approved"] + task_status_counts["rejected"]
    approval_rate = (
        round(task_status_counts["approved"] / decision_count * 100, 1)
        if decision_count else None
    )
    average_duration_ms = db.scalar(
        select(func.avg(Task.duration_ms)).where(*task_filter)
    )
    average_duration_ms = round(float(average_duration_ms), 1) if average_duration_ms is not None else None

    return {
        "period_start": since.isoformat(),
        "period_end": now.isoformat(),
        "leads_created": leads_created,
        "tasks_created": tasks_created,
        "lead_status_counts": lead_status_counts,
        "task_status_counts": task_status_counts,
        "task_type_counts": task_type_counts,
        "department_task_counts": department_task_counts,
        "decided_tasks": decision_count,
        "approval_rate_percent": approval_rate,
        "average_task_duration_ms": average_duration_ms,
        "mode": "mock",
        "note": "Prototype metrics calculated only from recorded tasks and leads for the selected agency.",
    }


@app.post("/api/reports/weekly/generate", response_model=TaskRead, status_code=status.HTTP_201_CREATED, tags=["reports"])
def generate_weekly_report(
    payload: ReportGenerate,
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    context: RequestContext = Depends(require_roles("owner", "admin", "manager")),
) -> Task:
    """Create a reviewable narrative draft from recorded agency metrics only."""
    snapshot = weekly_report(db, agency_id)
    started = perf_counter()
    agent_response = report_writer.run(snapshot, payload.instructions)
    duration_ms = round((perf_counter() - started) * 1000)
    period_label = str(snapshot.get("period_end", ""))[:10]
    task = Task(
        agency_id=agency_id,
        lead_id=None,
        task_type="generate_weekly_report",
        title=f"التقرير التشغيلي الأسبوعي · {period_label}",
        assigned_agent_id=report_writer.agent_id,
        status="pending_approval",
        input_data={
            "mode": "rule_based_mock",
            "period_start": snapshot.get("period_start"),
            "period_end": snapshot.get("period_end"),
            "instructions": payload.instructions,
        },
        result=agent_response,
        confidence=0.0,
        requires_owner_approval=True,
        duration_ms=duration_ms,
    )
    db.add(task)
    db.flush()
    _write_audit(
        db,
        agency_id=agency_id,
        action="report.generated",
        entity_type="task",
        entity_id=task.id,
        details={"report_type": "weekly_operations", "period_end": period_label},
        actor_id=context.user_id,
    )
    db.commit()
    db.refresh(task)
    return task
