from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, StringConstraints

from app.core.clock import iso

T = TypeVar("T")

# Public identifiers (validated before any DB access)
CustomerNumber = Annotated[str, StringConstraints(pattern=r"^C-\d{6}$")]
OrderNumber = Annotated[str, StringConstraints(pattern=r"^WA-\d{6}$")]
RmaNumber = Annotated[str, StringConstraints(pattern=r"^RMA-\d{6}$")]
TicketNumber = Annotated[str, StringConstraints(pattern=r"^TKT-\d{6}$")]
Sku = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9][A-Z0-9-]{2,39}$")]
StoreCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}-[A-Z]{2,5}$")]

UtcDateTime = Annotated[datetime, PlainSerializer(iso, return_type=str, when_used="json")]


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")


class Page(ApiModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    has_more: bool


class PageParams(ApiModel):
    page: int = Field(1, ge=1, le=10_000)
    page_size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class ErrorDetail(ApiModel):
    code: str
    message: str
    retryable: bool
    request_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(ApiModel):
    error: ErrorDetail


class PolicyReason(ApiModel):
    code: str
    message: str
    policy_ref: str | None = None


ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "Missing or invalid token"},
    403: {"model": ErrorResponse, "description": "Role not allowed"},
    404: {"model": ErrorResponse, "description": "Not found (or not yours)"},
    422: {"model": ErrorResponse, "description": "Validation or business-rule error"},
    429: {"model": ErrorResponse, "description": "Rate limited"},
}
