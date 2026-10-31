"""Authentication, agency onboarding, and workspace membership routes."""
from __future__ import annotations
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Agency, AgencyMembership, AuditLog, User
from backend.schemas import AgencyRegistration, AuthLogin, MemberCreate, MemberUpdate, PasswordChange
from backend.security import RequestContext, get_request_context, hash_password, issue_access_token, require_roles, verify_password

router = APIRouter(prefix="/api/auth", tags=["authentication"])

def _token_response(user: User, agency: Agency, role: str) -> dict:
    token, expires = issue_access_token(user, agency.id, role)
    return {"access_token": token, "token_type": "bearer", "expires_in": expires,
            "user": {"id": user.id, "email": user.email, "full_name": user.full_name},
            "agency": {"id": agency.id, "name": agency.name, "slug": agency.slug}, "role": role}

@router.post("/register-agency", status_code=status.HTTP_201_CREATED)
def register_agency(payload: AgencyRegistration, db: Session = Depends(get_db)) -> dict:
    """Create a workspace and its first owner account atomically."""
    if db.scalar(select(Agency).where(Agency.slug == payload.agency_slug)):
        raise HTTPException(status_code=409, detail="This agency URL is already in use.")
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="This email is already registered.")
    agency = Agency(id=str(uuid4()), name=payload.agency_name.strip(), slug=payload.agency_slug,
                    plan="starter", default_currency=payload.default_currency, timezone=payload.timezone)
    user = User(id=str(uuid4()), email=payload.email, full_name=payload.full_name.strip(),
                password_hash=hash_password(payload.password))
    membership = AgencyMembership(agency_id=agency.id, user_id=user.id, role="owner")
    db.add_all([agency, user, membership])
    try:
        db.flush()
        db.add(AuditLog(agency_id=agency.id, actor_id=user.id, action="agency.registered",
                        entity_type="agency", entity_id=agency.id, details={"owner_user_id": user.id}))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Agency slug or email is already registered.") from exc
    return _token_response(user, agency, "owner")

@router.post("/login")
def login(payload: AuthLogin, db: Session = Depends(get_db)) -> dict:
    agency = db.scalar(select(Agency).where(Agency.slug == payload.agency_slug))
    user = db.scalar(select(User).where(User.email == payload.email))
    membership = None
    if agency is not None and user is not None:
        membership = db.scalar(select(AgencyMembership).where(
            AgencyMembership.agency_id == agency.id, AgencyMembership.user_id == user.id,
            AgencyMembership.is_active.is_(True)))
    if (agency is None or agency.status != "active" or user is None or not user.is_active
        or membership is None or not verify_password(payload.password, user.password_hash)):
        raise HTTPException(status_code=401, detail="Agency, email, or password is incorrect.")
    return _token_response(user, agency, membership.role)

@router.get("/me")
def current_user(context: RequestContext = Depends(get_request_context), db: Session = Depends(get_db)) -> dict:
    if not context.authenticated:
        raise HTTPException(status_code=401, detail="Sign in to view your account.")
    user, agency = db.get(User, context.user_id), db.get(Agency, context.agency_id)
    if user is None or agency is None: raise HTTPException(status_code=401, detail="Account not found.")
    return {"user": {"id": user.id, "email": user.email, "full_name": user.full_name},
            "agency": {"id": agency.id, "name": agency.name, "slug": agency.slug},
            "role": context.role, "authenticated": True}

@router.post("/change-password")
def change_password(payload: PasswordChange, context: RequestContext = Depends(get_request_context),
                    db: Session = Depends(get_db)) -> dict:
    if not context.authenticated: raise HTTPException(status_code=401, detail="Sign in to change your password.")
    user = db.get(User, context.user_id)
    if user is None or not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    db.add(AuditLog(agency_id=context.agency_id, actor_id=user.id, action="user.password_changed",
                    entity_type="user", entity_id=user.id, details={}))
    db.commit()
    return {"success": True, "message": "Password updated. Sign in again with the new password."}

workspace_router = APIRouter(prefix="/api/workspace", tags=["workspace"])

@workspace_router.get("/members")
def list_members(context: RequestContext = Depends(require_roles("owner", "admin")),
                 db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(AgencyMembership, User).join(User, User.id == AgencyMembership.user_id)
                      .where(AgencyMembership.agency_id == context.agency_id).order_by(User.full_name)).all()
    return [{"user_id": user.id, "email": user.email, "full_name": user.full_name,
             "role": membership.role, "is_active": membership.is_active and user.is_active,
             "joined_at": membership.created_at.isoformat()} for membership, user in rows]

@workspace_router.post("/members", status_code=status.HTTP_201_CREATED)
def create_member(payload: MemberCreate, context: RequestContext = Depends(require_roles("owner", "admin")),
                  db: Session = Depends(get_db)) -> dict:
    if context.role == "admin" and payload.role == "admin":
        raise HTTPException(status_code=403, detail="Only the agency owner can create administrators.")
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="This email is already registered.")
    user = User(id=str(uuid4()), email=payload.email, full_name=payload.full_name.strip(),
                password_hash=hash_password(payload.password))
    membership = AgencyMembership(agency_id=context.agency_id, user_id=user.id, role=payload.role)
    db.add_all([user, membership])
    db.flush()
    db.add(AuditLog(agency_id=context.agency_id, actor_id=context.user_id, action="workspace.member_created",
                    entity_type="user", entity_id=user.id, details={"role": payload.role}))
    db.commit()
    return {"user_id": user.id, "email": user.email, "full_name": user.full_name,
            "role": membership.role, "is_active": True,
            "message": "Member created. Share the initial password securely; it will not be shown again."}


@workspace_router.patch("/members/{member_user_id}")
def update_member(
    member_user_id: str,
    payload: MemberUpdate,
    context: RequestContext = Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    membership = db.scalar(select(AgencyMembership).where(
        AgencyMembership.agency_id == context.agency_id,
        AgencyMembership.user_id == member_user_id,
    ))
    user = db.get(User, member_user_id)
    if membership is None or user is None:
        raise HTTPException(status_code=404, detail="Workspace member not found.")
    if context.user_id == member_user_id and payload.is_active is False:
        raise HTTPException(status_code=409, detail="You cannot deactivate your own account.")
    if membership.role == "owner":
        raise HTTPException(status_code=409, detail="The agency owner role cannot be changed or deactivated.")
    if context.role == "admin" and membership.role == "admin":
        raise HTTPException(status_code=403, detail="Only the agency owner can manage administrators.")
    if payload.role == "admin" and context.role != "owner":
        raise HTTPException(status_code=403, detail="Only the agency owner can assign the administrator role.")
    if payload.role is None and payload.is_active is None:
        raise HTTPException(status_code=422, detail="Provide a role or active-status change.")
    if payload.role is not None:
        membership.role = payload.role
    if payload.is_active is not None:
        membership.is_active = payload.is_active
    db.add(AuditLog(
        agency_id=context.agency_id,
        actor_id=context.user_id,
        action="workspace.member_updated",
        entity_type="user",
        entity_id=user.id,
        details={"role": membership.role, "is_active": membership.is_active},
    ))
    db.commit()
    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": membership.role,
        "is_active": membership.is_active and user.is_active,
    }
