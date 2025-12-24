import csv
import io
from datetime import datetime
from typing import Generator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog

router = APIRouter()


def generate_csv(logs: list[AuditLog]) -> Generator[str, None, None]:
    """Generate CSV content from audit logs."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    header = [
        "id",
        "org_id",
        "app_id",
        "user_id",
        "model",
        "provider",
        "prompt_hash",
        "token_count_input",
        "token_count_output",
        "latency_ms",
        "risk_flags",
        "created_at",
    ]
    writer.writerow(header)
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)

    # Write data rows
    for log in logs:
        row = [
            str(log.id),
            log.org_id,
            log.app_id,
            log.user_id or "",
            log.model,
            log.provider,
            log.prompt_hash,
            log.token_count_input or "",
            log.token_count_output or "",
            log.latency_ms or "",
            ",".join(log.risk_flags) if log.risk_flags else "",
            log.created_at.isoformat() if log.created_at else "",
        ]
        writer.writerow(row)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)


@router.get("/csv")
async def export_logs_csv(
    org_id: str | None = Query(None, description="Filter by organization ID"),
    app_id: str | None = Query(None, description="Filter by application ID"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    model: str | None = Query(None, description="Filter by AI model"),
    provider: str | None = Query(None, description="Filter by provider"),
    start_date: datetime | None = Query(None, description="Filter logs from this date"),
    end_date: datetime | None = Query(None, description="Filter logs until this date"),
    has_risk_flags: bool | None = Query(None, description="Filter logs with/without risk flags"),
    db: Session = Depends(get_db),
):
    """
    Export audit logs as CSV file.

    Returns a streaming CSV response with all matching audit logs.
    Supports the same filters as the list endpoint.
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

    # Order by created_at descending
    logs = query.order_by(desc(AuditLog.created_at)).all()

    # Generate filename with timestamp
    filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        generate_csv(logs),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )


