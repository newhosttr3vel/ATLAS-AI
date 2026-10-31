"""ATLAS AI FastAPI application."""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.agents.general_manager import GeneralManagerAgent
from backend.database import engine, get_db
from backend.models import Base, Lead, Task
from backend.schemas import (
    LeadCreate,
    LeadRead,
    TaskApprove,
    TaskCreate,
    TaskEdit,
    TaskRead,
    TaskReject,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ATLAS AI API",
    description="Cloud-first API for a travel-agency multi-agent platform.",
    version="0.2.0",
    lifespan=lifespan,
)

general_manager = GeneralManagerAgent()
STANDARD_RESULT_KEYS = {
    "result",
    "confidence",
    "assumptions",
    "risks",
    "next_action",
    "requires_owner_approval",
}


def _agency_id(x_agency_id: str = Header(default="demo-agency", alias="X-Agency-ID")) -> str:
    """Prototype tenant selector; this is not authentication or authorization."""
    cleaned = x_agency_id.strip()
    if not cleaned or len(cleaned) > 80:
        raise HTTPException(status_code=400, detail="Invalid X-Agency-ID header.")
    return cleaned


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
) -> Lead:
    if payload.travel_start and payload.travel_end and payload.travel_end < payload.travel_start:
        raise HTTPException(status_code=422, detail="travel_end must be on or after travel_start.")

    lead = Lead(agency_id=agency_id, **payload.model_dump())
    db.add(lead)
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
    db.commit()
    db.refresh(task)
    return task


@app.get("/api/tasks", response_model=list[TaskRead], tags=["tasks"])
def list_tasks(
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
    task_status: str | None = Query(default=None, alias="status"),
    lead_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Task]:
    statement = select(Task).where(Task.agency_id == agency_id)
    if task_status:
        statement = statement.where(Task.status == task_status)
    if lead_id:
        statement = statement.where(Task.lead_id == lead_id)
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
) -> Task:
    task = _get_task(db, task_id, agency_id)
    if task.status != "pending_approval":
        raise HTTPException(status_code=409, detail="Only pending tasks can be approved.")
    task.status = "approved"
    task.owner_decision_notes = payload.notes
    db.commit()
    db.refresh(task)
    return task


@app.post("/api/tasks/{task_id}/reject", response_model=TaskRead, tags=["tasks"])
def reject_task(
    task_id: str,
    payload: TaskReject,
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
) -> Task:
    task = _get_task(db, task_id, agency_id)
    if task.status != "pending_approval":
        raise HTTPException(status_code=409, detail="Only pending tasks can be rejected.")
    task.status = "rejected"
    task.owner_decision_notes = payload.reason
    db.commit()
    db.refresh(task)
    return task


@app.post("/api/tasks/{task_id}/edit", response_model=TaskRead, tags=["tasks"])
def edit_task(
    task_id: str,
    payload: TaskEdit,
    db: Session = Depends(get_db),
    agency_id: str = Depends(_agency_id),
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
    db.commit()
    db.refresh(task)
    return task


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
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=7)
    leads_created = db.scalar(
        select(func.count(Lead.id)).where(
            Lead.agency_id == agency_id,
            Lead.created_at >= since,
        )
    ) or 0
    tasks_created = db.scalar(
        select(func.count(Task.id)).where(
            Task.agency_id == agency_id,
            Task.created_at >= since,
        )
    ) or 0
    status_counts = {
        name: db.scalar(
            select(func.count(Task.id)).where(
                Task.agency_id == agency_id,
                Task.created_at >= since,
                Task.status == name,
            )
        ) or 0
        for name in ("pending_approval", "approved", "rejected")
    }
    return {
        "period_start": since.isoformat(),
        "period_end": now.isoformat(),
        "leads_created": leads_created,
        "tasks_created": tasks_created,
        "task_status_counts": status_counts,
        "mode": "mock",
        "note": "Prototype metrics for the selected agency only.",
    }
