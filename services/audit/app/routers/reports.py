"""PDF Report generation endpoints."""

import io
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

from ..database import get_db
from ..models import AuditLog

router = APIRouter()


def create_header(title: str, subtitle: str = "") -> list:
    """Create report header elements."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=6,
        textColor=colors.HexColor('#0ea5e9'),
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
    )
    
    elements = [
        Paragraph(title, title_style),
    ]
    if subtitle:
        elements.append(Paragraph(subtitle, subtitle_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    return elements


def create_summary_table(data: dict[str, Any]) -> Table:
    """Create a summary statistics table."""
    table_data = [
        ['Metric', 'Value'],
        ['Total AI Requests', f"{data.get('total_requests', 0):,}"],
        ['Total Violations', f"{data.get('total_violations', 0):,}"],
        ['Requests Blocked', f"{data.get('blocked', 0):,}"],
        ['Requests Masked', f"{data.get('masked', 0):,}"],
        ['Unique Applications', f"{data.get('unique_apps', 0):,}"],
        ['Unique Models', f"{data.get('unique_models', 0):,}"],
    ]
    
    table = Table(table_data, colWidths=[3 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    return table


def create_violations_table(violations: list[dict]) -> Table:
    """Create a violations breakdown table."""
    table_data = [['PII Type', 'Count', 'Blocked', 'Masked']]
    
    for v in violations[:10]:  # Top 10
        table_data.append([
            v.get('type', 'Unknown'),
            str(v.get('count', 0)),
            str(v.get('blocked', 0)),
            str(v.get('masked', 0)),
        ])
    
    table = Table(table_data, colWidths=[2.5 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fef2f2')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fecaca')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    return table


def create_top_apps_table(apps: list[dict]) -> Table:
    """Create a top violating apps table."""
    table_data = [['Rank', 'Application', 'Violations']]
    
    for i, app in enumerate(apps[:10], 1):
        table_data.append([
            str(i),
            app.get('app_id', 'Unknown'),
            str(app.get('count', 0)),
        ])
    
    table = Table(table_data, colWidths=[0.8 * inch, 3.5 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fffbeb')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#fde68a')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    return table


@router.get("/audit")
async def generate_audit_report(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    org_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Generate a PDF audit report.

    Returns a downloadable PDF with:
    - Executive summary
    - Violation statistics
    - Top risks by application
    - Recommendations
    """
    # Default to last 30 days
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Query data
    query = db.query(AuditLog)
    if org_id:
        query = query.filter(AuditLog.org_id == org_id)
    query = query.filter(
        AuditLog.created_at >= start_date,
        AuditLog.created_at <= end_date,
    )

    all_logs = query.all()
    total_requests = len(all_logs)

    # Calculate statistics
    violations_query = query.filter(func.jsonb_array_length(AuditLog.risk_flags) > 0)
    violation_logs = violations_query.all()
    total_violations = len(violation_logs)

    # Count by action and type
    blocked = 0
    masked = 0
    type_counts: dict[str, dict[str, int]] = {}

    for log in violation_logs:
        action = (log.request_metadata or {}).get("action", "allowed")
        if action == "blocked":
            blocked += 1
        elif action == "masked":
            masked += 1

        for pii_type in (log.risk_flags or []):
            if pii_type not in type_counts:
                type_counts[pii_type] = {"count": 0, "blocked": 0, "masked": 0}
            type_counts[pii_type]["count"] += 1
            if action == "blocked":
                type_counts[pii_type]["blocked"] += 1
            elif action == "masked":
                type_counts[pii_type]["masked"] += 1

    # Top violating apps
    app_counts: dict[str, int] = {}
    for log in violation_logs:
        app_id = log.app_id
        app_counts[app_id] = app_counts.get(app_id, 0) + 1

    top_apps = sorted(
        [{"app_id": k, "count": v} for k, v in app_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    # Unique counts
    unique_apps = len(set(log.app_id for log in all_logs))
    unique_models = len(set(log.model for log in all_logs))

    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#1e293b'),
    )
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=10,
        textColor=colors.HexColor('#475569'),
    )

    elements = []

    # Header
    elements.extend(create_header(
        "AI Compliance Audit Report",
        f"Period: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}",
    ))

    # Executive Summary
    elements.append(Paragraph("Executive Summary", section_style))
    summary_text = f"""
    During the reporting period, the AI Compliance Platform processed <b>{total_requests:,}</b> AI requests
    across <b>{unique_apps}</b> applications using <b>{unique_models}</b> different AI models.
    The system detected <b>{total_violations:,}</b> policy violations, with <b>{blocked:,}</b> requests blocked
    and <b>{masked:,}</b> requests having PII masked before forwarding to AI providers.
    """
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Summary Statistics
    elements.append(Paragraph("Summary Statistics", section_style))
    summary_data = {
        "total_requests": total_requests,
        "total_violations": total_violations,
        "blocked": blocked,
        "masked": masked,
        "unique_apps": unique_apps,
        "unique_models": unique_models,
    }
    elements.append(create_summary_table(summary_data))
    elements.append(Spacer(1, 0.3 * inch))

    # Violations by Type
    if type_counts:
        elements.append(Paragraph("Violations by PII Type", section_style))
        violations_data = sorted(
            [{"type": k, **v} for k, v in type_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
        elements.append(create_violations_table(violations_data))
        elements.append(Spacer(1, 0.3 * inch))

    # Top Violating Applications
    if top_apps:
        elements.append(Paragraph("Top Violating Applications", section_style))
        elements.append(create_top_apps_table(top_apps))
        elements.append(Spacer(1, 0.3 * inch))

    # Recommendations
    elements.append(Paragraph("Recommendations", section_style))
    recommendations = []
    if blocked > 0:
        recommendations.append(
            "• Review blocked requests to identify training needs for teams sending sensitive data to AI."
        )
    if total_violations > total_requests * 0.1:
        recommendations.append(
            "• High violation rate detected. Consider expanding PII awareness training."
        )
    if top_apps:
        recommendations.append(
            f"• Focus remediation efforts on '{top_apps[0]['app_id']}' which has the highest violation count."
        )
    recommendations.append(
        "• Regularly review and update compliance policies to address emerging risks."
    )

    for rec in recommendations:
        elements.append(Paragraph(rec, body_style))

    # Footer
    elements.append(Spacer(1, 0.5 * inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
    )
    elements.append(Paragraph(
        f"Generated by AI Compliance Platform on {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}",
        footer_style,
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    filename = f"audit_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )


