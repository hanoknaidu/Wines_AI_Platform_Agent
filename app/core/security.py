"""Authentication primitives: JWT issue/verify and the Principal model.

Roles
  customer  a logged-in shopper; may only touch their own data
  agent     the AI agent acting *on behalf of one customer* (delegated token
            minted per chat run, short TTL, bound to session + run)
  staff     support / finance staff; may read any customer, approve refunds

In production, customer and staff tokens come from the identity provider
(swap HS256 for RS256 + JWKS by changing JWT_ALGORITHM and the key source);
agent tokens are always minted by this service."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Literal

import jwt

from app.core.clock import Clock
from app.core.config import Settings
from app.core.errors import AuthenticationError

Role = Literal["customer", "agent", "staff"]

AGENT_SCOPES = (
    "customers:read",
    "orders:read",
    "orders:write",
    "refunds:read",
    "refunds:write",
    "returns:read",
    "returns:write",
    "catalog:read",
    "support:read",
    "support:write",
)


@dataclass(frozen=True)
class Principal:
    subject: str  # customer_number for customer/agent, employee code for staff
    role: Role
    customer_number: str | None = None
    session_id: str | None = None
    run_id: str | None = None
    scopes: tuple[str, ...] = field(default_factory=tuple)
    token_id: str | None = None

    @property
    def actor_type(self) -> str:
        """Value for audit_logs.actor_type / *_by_type columns."""
        return {"customer": "customer", "agent": "ai_agent", "staff": "staff"}[self.role]

    @property
    def is_staff(self) -> bool:
        return self.role == "staff"

    @property
    def rate_limit_key(self) -> str:
        return f"{self.role}:{self.subject}"

    def can_access_customer(self, customer_number: str) -> bool:
        return self.is_staff or self.customer_number == customer_number


class TokenService:
    def __init__(self, settings: Settings, clock: Clock) -> None:
        self._s = settings
        self._clock = clock

    def _encode(self, claims: dict, ttl_s: int) -> str:
        now = self._clock.now()
        payload = {
            **claims,
            "iss": self._s.jwt_issuer,
            "aud": self._s.jwt_audience,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=ttl_s)).timestamp()),
            "jti": uuid.uuid4().hex,
        }
        return jwt.encode(payload, self._s.jwt_secret.get_secret_value(), algorithm=self._s.jwt_algorithm)

    def issue_customer_token(self, customer_number: str) -> str:
        return self._encode({"sub": customer_number, "role": "customer"}, self._s.access_token_ttl_s)

    def issue_staff_token(self, employee_code: str) -> str:
        return self._encode({"sub": employee_code, "role": "staff"}, self._s.access_token_ttl_s)

    def issue_agent_token(self, customer_number: str, session_id: str, run_id: str) -> str:
        return self._encode(
            {
                "sub": customer_number,
                "role": "agent",
                "sid": session_id,
                "run": run_id,
                "scope": " ".join(AGENT_SCOPES),
            },
            self._s.agent_token_ttl_s,
        )

    def verify(self, token: str) -> Principal:
        try:
            claims = jwt.decode(
                token,
                self._s.jwt_secret.get_secret_value(),
                algorithms=[self._s.jwt_algorithm],
                audience=self._s.jwt_audience,
                issuer=self._s.jwt_issuer,
                # The frozen demo clock may be in the past; validate exp against it.
                options={"verify_exp": False, "verify_iat": False, "verify_nbf": False},
                leeway=30,
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid or expired token", code="INVALID_TOKEN") from exc
        now = int(self._clock.now().timestamp())
        if claims.get("exp", 0) + 30 < now or claims.get("nbf", 0) - 30 > now:
            raise AuthenticationError("Invalid or expired token", code="TOKEN_EXPIRED")
        role = claims.get("role")
        if role not in ("customer", "agent", "staff"):
            raise AuthenticationError("Invalid or expired token", code="INVALID_TOKEN")
        sub = str(claims.get("sub", ""))
        return Principal(
            subject=sub,
            role=role,
            customer_number=sub if role in ("customer", "agent") else None,
            session_id=claims.get("sid"),
            run_id=claims.get("run"),
            scopes=tuple(str(claims.get("scope", "")).split()),
            token_id=claims.get("jti"),
        )
