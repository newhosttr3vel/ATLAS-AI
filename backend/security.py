"""Password hashing and tenant-bound signed bearer sessions (stdlib only)."""
from __future__ import annotations
import base64, hashlib, hmac, json, os, secrets, time
from dataclasses import dataclass
from typing import Any
from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Agency, AgencyMembership, User

PASSWORD_ITERATIONS = 310_000
TOKEN_TTL_SECONDS = 8 * 60 * 60
TOKEN_ISSUER = "atlas-ai"

@dataclass(frozen=True)
class RequestContext:
    agency_id: str
    user_id: str
    role: str
    authenticated: bool

def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

def _secret() -> bytes:
    configured = os.getenv("ATLAS_AUTH_SECRET", "").strip()
    if os.getenv("APP_ENV", "development").lower() == "production":
        if len(configured) < 32:
            raise RuntimeError("ATLAS_AUTH_SECRET must contain at least 32 characters in production.")
        return configured.encode("utf-8")
    return (configured or "atlas-ai-development-only-secret-change-before-deploy").encode("utf-8")

def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256\u0024{PASSWORD_ITERATIONS}\u0024{_b64encode(salt)}\u0024{_b64encode(digest)}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256": return False
        rounds_value = int(rounds)
        if rounds_value < 100_000 or rounds_value > 2_000_000: return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _b64decode(salt_text), rounds_value)
        return hmac.compare_digest(actual, _b64decode(digest_text))
    except (ValueError, TypeError):
        return False

def issue_access_token(user: User, agency_id: str, role: str) -> tuple[str, int]:
    now = int(time.time())
    claims = {"iss": TOKEN_ISSUER, "sub": user.id, "aid": agency_id, "role": role,
              "ver": user.token_version, "iat": now, "exp": now + TOKEN_TTL_SECONDS}
    header = {"alg": "HS256", "typ": "JWT"}
    unsigned = f"{_b64encode(json.dumps(header, separators=(',', ':')).encode())}.{_b64encode(json.dumps(claims, separators=(',', ':')).encode())}"
    signature = hmac.new(_secret(), unsigned.encode("ascii"), hashlib.sha256).digest()
    return f"{unsigned}.{_b64encode(signature)}", TOKEN_TTL_SECONDS

def _read_token(token: str) -> dict[str, Any]:
    try:
        head, body, signature = token.split(".")
        unsigned = f"{head}.{body}"
        expected = hmac.new(_secret(), unsigned.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64decode(signature)): raise ValueError("Invalid signature")
        header, claims = json.loads(_b64decode(head)), json.loads(_b64decode(body))
        now = int(time.time())
        if header != {"alg": "HS256", "typ": "JWT"}: raise ValueError("Invalid token header")
        if claims.get("iss") != TOKEN_ISSUER or int(claims.get("exp", 0)) <= now: raise ValueError("Expired token")
        if int(claims.get("iat", 0)) > now + 60: raise ValueError("Invalid token time")
        if not all(claims.get(key) for key in ("sub", "aid", "role")): raise ValueError("Missing claims")
        return claims
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.") from exc

def authenticate_bearer(authorization: str | None, db: Session) -> RequestContext:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="A valid bearer access token is required.")
    claims = _read_token(token.strip())
    user = db.get(User, str(claims["sub"]))
    membership = db.scalar(select(AgencyMembership).where(
        AgencyMembership.user_id == str(claims["sub"]),
        AgencyMembership.agency_id == str(claims["aid"]),
        AgencyMembership.is_active.is_(True)))
    agency = db.get(Agency, str(claims["aid"]))
    if (user is None or not user.is_active or membership is None or agency is None
        or agency.status != "active" or int(claims.get("ver", -1)) != user.token_version
        or claims.get("role") != membership.role):
        raise HTTPException(status_code=401, detail="This account or agency membership is no longer active.")
    return RequestContext(agency_id=agency.id, user_id=user.id, role=membership.role, authenticated=True)

def get_request_context(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_agency_id: str | None = Header(default=None, alias="X-Agency-ID"),
    db: Session = Depends(get_db),
) -> RequestContext:
    if authorization:
        context = authenticate_bearer(authorization, db)
        if x_agency_id and x_agency_id.strip() != context.agency_id:
            raise HTTPException(status_code=403, detail="The requested agency does not match this signed session.")
        return context
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise HTTPException(status_code=401, detail="Sign in is required.")
    agency_id = (x_agency_id or "demo-agency").strip()
    if not agency_id or len(agency_id) > 80:
        raise HTTPException(status_code=400, detail="Invalid X-Agency-ID header.")
    # Compatibility only: the legacy header works in development, never in production.
    return RequestContext(agency_id=agency_id, user_id="prototype-owner", role="owner", authenticated=False)

def require_roles(*allowed_roles: str):
    def dependency(context: RequestContext = Depends(get_request_context)) -> RequestContext:
        if context.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Your role does not have permission to perform this action.")
        return context
    return dependency


def validate_auth_config() -> None:
    """Fail fast on unsafe or incomplete production token configuration."""
    if os.getenv("APP_ENV", "development").lower() == "production":
        _secret()
