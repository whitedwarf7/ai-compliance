import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog

router = APIRouter()


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""

    id: str | None = None
    org_id: str
    app_id: str
    user_id: str | None = None
    model: str
    provider: str
    prompt_hash: str
    token_count_input: int | None = None
    token_count_output: int | None = None
    latency_ms: int | None = None
    risk_flags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""

    id: str
    org_id: str
    app_id: str
    user_id: str | None
    model: str
    provider: str
    prompt_hash: str
    token_count_input: int | None
    token_count_output: int | None
    latency_ms: int | None
    risk_flags: list[str]
    metadata: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """Schema for paginated response."""

    items: list[AuditLogResponse]
    total: int
    page: int
    limit: int
    pages: int


class StatsResponse(BaseModel):
    """Schema for audit log statistics."""

    total_requests: int
    total_tokens_input: int
    total_tokens_output: int
    unique_models: int
    unique_apps: int
    requests_with_risk_flags: int


@router.post("", response_model=AuditLogResponse, status_code=201)
async def create_audit_log(
    log: AuditLogCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new audit log entry.

    This endpoint is called by the gateway service to log AI requests.
    Audit logs are immutable - once created, they cannot be modified or deleted.
    """
    log_id = uuid.UUID(log.id) if log.id else uuid.uuid4()

    db_log = AuditLog(
        id=log_id,
        org_id=log.org_id,
        app_id=log.app_id,
        user_id=log.user_id,
        model=log.model,
        provider=log.provider,
        prompt_hash=log.prompt_hash,
        token_count_input=log.token_count_input,
        token_count_output=log.token_count_output,
        latency_ms=log.latency_ms,
        risk_flags=log.risk_flags,
        metadata=log.metadata,
    )

    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    return AuditLogResponse(
        id=str(db_log.id),
        org_id=db_log.org_id,
        app_id=db_log.app_id,
        user_id=db_log.user_id,
        model=db_log.model,
        provider=db_log.provider,
        prompt_hash=db_log.prompt_hash,
        token_count_input=db_log.token_count_input,
        token_count_output=db_log.token_count_output,
        latency_ms=db_log.latency_ms,
        risk_flags=db_log.risk_flags or [],
        metadata=db_log.metadata or {},
        created_at=db_log.created_at,
    )


@router.get("", response_model=PaginatedResponse)
async def list_audit_logs(
    org_id: str | None = Query(None, description="Filter by organization ID"),
    app_id: str | None = Query(None, description="Filter by application ID"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    model: str | None = Query(None, description="Filter by AI model"),
    provider: str | None = Query(None, description="Filter by provider (openai/azure)"),
    start_date: datetime | None = Query(None, description="Filter logs from this date"),
    end_date: datetime | None = Query(None, description="Filter logs until this date"),
    has_risk_flags: bool | None = Query(None, description="Filter logs with/without risk flags"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List and filter audit logs with pagination.

    Supports filtering by organization, application, user, model, provider,
    date range, and presence of risk flags.
    """
    query = db.query(AuditLog)

    # Apply filters
    if org_id:
        query = query.filter(AuditLog.org_id == org_id)
    if app_id:
        query = query.filter(AuditLog.app_id == app_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if model:
        query = query.filter(AuditLog.model == model)
    if provider:
        query = query.filter(AuditLog.provider == provider)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    if has_risk_flags is not None:
        if has_risk_flags:
            query = query.filter(func.jsonb_array_length(AuditLog.risk_flags) > 0)
        else:
            query = query.filter(func.jsonb_array_length(AuditLog.risk_flags) == 0)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * limit
    logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    # Calculate total pages
    pages = (total + limit - 1) // limit

    return PaginatedResponse(
        items=[
            AuditLogResponse(
                id=str(log.id),
                org_id=log.org_id,
                app_id=log.app_id,
                user_id=log.user_id,
                model=log.model,
                provider=log.provider,
                prompt_hash=log.prompt_hash,
                token_count_input=log.token_count_input,
                token_count_output=log.token_count_output,
                latency_ms=log.latency_ms,
                risk_flags=log.risk_flags or [],
                metadata=log.metadata or {},
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_audit_stats(
    org_id: str | None = Query(None, description="Filter by organization ID"),
    start_date: datetime | None = Query(None, description="Filter logs from this date"),
    end_date: datetime | None = Query(None, description="Filter logs until this date"),
    db: Session = Depends(get_db),
):
    """
    Get aggregate statistics for audit logs.

    Returns total requests, token usage, unique models/apps, and risk flag counts.
    """
    query = db.query(AuditLog)

    if org_id:
        query = query.filter(AuditLog.org_id == org_id)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    total_requests = query.count()

    # Token counts
    tokens = db.query(
        func.coalesce(func.sum(AuditLog.token_count_input), 0).label("input"),
        func.coalesce(func.sum(AuditLog.token_count_output), 0).label("output"),
    ).filter(
        AuditLog.org_id == org_id if org_id else True,
        AuditLog.created_at >= start_date if start_date else True,
        AuditLog.created_at <= end_date if end_date else True,
    ).first()

    # Unique counts
    unique_models = query.distinct(AuditLog.model).count()
    unique_apps = query.distinct(AuditLog.app_id).count()

    # Risk flag count
    risk_query = query.filter(func.jsonb_array_length(AuditLog.risk_flags) > 0)
    requests_with_risk_flags = risk_query.count()

    return StatsResponse(
        total_requests=total_requests,
        total_tokens_input=int(tokens.input) if tokens else 0,
        total_tokens_output=int(tokens.output) if tokens else 0,
        unique_models=unique_models,
        unique_apps=unique_apps,
        requests_with_risk_flags=requests_with_risk_flags,
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
):
    """Get a single audit log entry by ID."""
    try:
        log_uuid = uuid.UUID(log_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid log ID format")

    log = db.query(AuditLog).filter(AuditLog.id == log_uuid).first()

    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return AuditLogResponse(
        id=str(log.id),
        org_id=log.org_id,
        app_id=log.app_id,
        user_id=log.user_id,
        model=log.model,
        provider=log.provider,
        prompt_hash=log.prompt_hash,
        token_count_input=log.token_count_input,
        token_count_output=log.token_count_output,
        latency_ms=log.latency_ms,
        risk_flags=log.risk_flags or [],
        metadata=log.metadata or {},
        created_at=log.created_at,
    )

