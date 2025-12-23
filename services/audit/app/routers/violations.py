"""Violations API endpoints for compliance reporting."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, func, case, literal
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog

router = APIRouter()


class ViolationSummary(BaseModel):
    """Summary of policy violations."""

    total_violations: int
    total_blocked: int
    total_masked: int
    total_warned: int
    by_type: dict[str, int]
    by_action: dict[str, int]
    by_severity: dict[str, int]
    top_violating_apps: list[dict[str, Any]]
    top_violating_orgs: list[dict[str, Any]]
    recent_violations: list[dict[str, Any]]


class ViolationTrend(BaseModel):
    """Violation trend over time."""

    date: str
    total: int
    blocked: int
    masked: int
    warned: int


class ViolationResponse(BaseModel):
    """Individual violation record."""

    id: str
    org_id: str
    app_id: str
    user_id: str | None
    model: str
    risk_flags: list[str]
    action: str
    created_at: datetime


@router.get("/summary", response_model=ViolationSummary)
async def get_violations_summary(
    org_id: str | None = Query(None, description="Filter by organization ID"),
    app_id: str | None = Query(None, description="Filter by application ID"),
    start_date: datetime | None = Query(None, description="Filter from this date"),
    end_date: datetime | None = Query(None, description="Filter until this date"),
    db: Session = Depends(get_db),
):
    """
    Get a summary of policy violations.

    Returns aggregate statistics including:
    - Total violations by type and action
    - Top violating applications and organizations
    - Recent violations
    """
    # Base query for logs with risk flags
    query = db.query(AuditLog).filter(
        func.jsonb_array_length(AuditLog.risk_flags) > 0
    )

    if org_id:
        query = query.filter(AuditLog.org_id == org_id)
    if app_id:
        query = query.filter(AuditLog.app_id == app_id)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    # Get total count
    total_violations = query.count()

    # Count by action (from metadata)
    all_logs = query.all()

    action_counts = {"blocked": 0, "masked": 0, "warned": 0, "allowed": 0}
    type_counts: dict[str, int] = {}
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for log in all_logs:
        # Count by action
        action = (log.metadata or {}).get("action", "allowed")
        if action in action_counts:
            action_counts[action] += 1

        # Count by PII type
        for pii_type in (log.risk_flags or []):
            type_counts[pii_type] = type_counts.get(pii_type, 0) + 1

            # Estimate severity from type
            if pii_type in ["AADHAAR", "PAN", "CREDIT_CARD", "SSN"]:
                severity_counts["critical"] += 1
            elif pii_type in ["PASSPORT"]:
                severity_counts["high"] += 1
            elif pii_type in ["EMAIL", "PHONE", "DATE_OF_BIRTH"]:
                severity_counts["medium"] += 1
            else:
                severity_counts["low"] += 1

    # Top violating apps
    app_violations = (
        db.query(
            AuditLog.app_id,
            func.count(AuditLog.id).label("count"),
        )
        .filter(func.jsonb_array_length(AuditLog.risk_flags) > 0)
        .group_by(AuditLog.app_id)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )

    top_apps = [{"app_id": app_id, "violation_count": count} for app_id, count in app_violations]

    # Top violating orgs
    org_violations = (
        db.query(
            AuditLog.org_id,
            func.count(AuditLog.id).label("count"),
        )
        .filter(func.jsonb_array_length(AuditLog.risk_flags) > 0)
        .group_by(AuditLog.org_id)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )

    top_orgs = [{"org_id": org_id, "violation_count": count} for org_id, count in org_violations]

    # Recent violations
    recent = (
        query
        .order_by(desc(AuditLog.created_at))
        .limit(10)
        .all()
    )

    recent_violations = [
        {
            "id": str(log.id),
            "org_id": log.org_id,
            "app_id": log.app_id,
            "model": log.model,
            "risk_flags": log.risk_flags or [],
            "action": (log.metadata or {}).get("action", "unknown"),
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in recent
    ]

    return ViolationSummary(
        total_violations=total_violations,
        total_blocked=action_counts["blocked"],
        total_masked=action_counts["masked"],
        total_warned=action_counts["warned"],
        by_type=type_counts,
        by_action=action_counts,
        by_severity=severity_counts,
        top_violating_apps=top_apps,
        top_violating_orgs=top_orgs,
        recent_violations=recent_violations,
    )


@router.get("", response_model=list[ViolationResponse])
async def list_violations(
    org_id: str | None = Query(None, description="Filter by organization ID"),
    app_id: str | None = Query(None, description="Filter by application ID"),
    pii_type: str | None = Query(None, description="Filter by PII type"),
    action: str | None = Query(None, description="Filter by action (blocked/masked/warned)"),
    start_date: datetime | None = Query(None, description="Filter from this date"),
    end_date: datetime | None = Query(None, description="Filter until this date"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List individual violation records with filtering.
    """
    query = db.query(AuditLog).filter(
        func.jsonb_array_length(AuditLog.risk_flags) > 0
    )

    if org_id:
        query = query.filter(AuditLog.org_id == org_id)
    if app_id:
        query = query.filter(AuditLog.app_id == app_id)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    if pii_type:
        # Filter by specific PII type in risk_flags array
        query = query.filter(AuditLog.risk_flags.contains([pii_type]))

    # Apply pagination
    offset = (page - 1) * limit
    logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    # Filter by action if specified (post-query since it's in JSONB)
    if action:
        logs = [
            log for log in logs
            if (log.metadata or {}).get("action") == action
        ]

    return [
        ViolationResponse(
            id=str(log.id),
            org_id=log.org_id,
            app_id=log.app_id,
            user_id=log.user_id,
            model=log.model,
            risk_flags=log.risk_flags or [],
            action=(log.metadata or {}).get("action", "unknown"),
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/trends")
async def get_violation_trends(
    org_id: str | None = Query(None, description="Filter by organization ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db),
):
    """
    Get violation trends over time.

    Returns daily violation counts for the specified period.
    """
    from datetime import timedelta

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(AuditLog).filter(
        func.jsonb_array_length(AuditLog.risk_flags) > 0,
        AuditLog.created_at >= start_date,
        AuditLog.created_at <= end_date,
    )

    if org_id:
        query = query.filter(AuditLog.org_id == org_id)

    logs = query.all()

    # Group by date
    daily_counts: dict[str, dict[str, int]] = {}

    for log in logs:
        if not log.created_at:
            continue

        date_str = log.created_at.strftime("%Y-%m-%d")
        if date_str not in daily_counts:
            daily_counts[date_str] = {"total": 0, "blocked": 0, "masked": 0, "warned": 0}

        daily_counts[date_str]["total"] += 1

        action = (log.metadata or {}).get("action", "allowed")
        if action in daily_counts[date_str]:
            daily_counts[date_str][action] += 1

    # Convert to list sorted by date
    trends = [
        ViolationTrend(
            date=date,
            total=counts["total"],
            blocked=counts["blocked"],
            masked=counts["masked"],
            warned=counts["warned"],
        )
        for date, counts in sorted(daily_counts.items())
    ]

    return {"trends": trends, "period_days": days, "start_date": start_date.isoformat(), "end_date": end_date.isoformat()}


@router.get("/by-type")
async def get_violations_by_type(
    org_id: str | None = Query(None, description="Filter by organization ID"),
    start_date: datetime | None = Query(None, description="Filter from this date"),
    end_date: datetime | None = Query(None, description="Filter until this date"),
    db: Session = Depends(get_db),
):
    """
    Get violation breakdown by PII type.
    """
    query = db.query(AuditLog).filter(
        func.jsonb_array_length(AuditLog.risk_flags) > 0
    )

    if org_id:
        query = query.filter(AuditLog.org_id == org_id)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    logs = query.all()

    # Count by type
    type_counts: dict[str, dict[str, int]] = {}

    for log in logs:
        action = (log.metadata or {}).get("action", "allowed")

        for pii_type in (log.risk_flags or []):
            if pii_type not in type_counts:
                type_counts[pii_type] = {"total": 0, "blocked": 0, "masked": 0, "warned": 0}

            type_counts[pii_type]["total"] += 1
            if action in type_counts[pii_type]:
                type_counts[pii_type][action] += 1

    return {
        "by_type": [
            {
                "pii_type": pii_type,
                **counts,
            }
            for pii_type, counts in sorted(type_counts.items(), key=lambda x: x[1]["total"], reverse=True)
        ]
    }

