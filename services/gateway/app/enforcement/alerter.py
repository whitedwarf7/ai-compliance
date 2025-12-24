"""
Alert System

Sends alerts for policy violations via Slack and Email.
"""

import asyncio
import logging
import smtplib
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class Violation:
    """Represents a policy violation for alerting."""

    violation_type: str  # "pii_detected", "model_not_allowed", etc.
    violations: list[str]  # List of specific violations
    org_id: str | None = None
    app_id: str | None = None
    user_id: str | None = None
    model: str | None = None
    request_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    action_taken: str = "blocked"  # "blocked", "masked", "warned"
    severity: str = "high"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "violation_type": self.violation_type,
            "violations": self.violations,
            "org_id": self.org_id,
            "app_id": self.app_id,
            "user_id": self.user_id,
            "model": self.model,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "action_taken": self.action_taken,
            "severity": self.severity,
        }


class Alerter:
    """
    Sends alerts for policy violations via multiple channels.

    Supports:
    - Slack webhooks
    - Email via SMTP
    """

    def __init__(
        self,
        slack_webhook_url: str | None = None,
        email_enabled: bool = False,
        smtp_host: str | None = None,
        smtp_port: int = 587,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        email_from: str | None = None,
        email_to: list[str] | None = None,
    ):
        """
        Initialize the alerter.

        Args:
            slack_webhook_url: Slack webhook URL for notifications
            email_enabled: Whether email alerts are enabled
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username for authentication
            smtp_password: SMTP password for authentication
            email_from: Sender email address
            email_to: List of recipient email addresses
        """
        self.slack_webhook_url = slack_webhook_url
        self.email_enabled = email_enabled
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.email_from = email_from
        self.email_to = email_to or []

    async def send_alert(self, violation: Violation) -> None:
        """
        Send alert via all configured channels.

        Args:
            violation: The violation to alert on
        """
        tasks = []

        if self.slack_webhook_url:
            tasks.append(self.send_slack_alert(violation))

        if self.email_enabled and self.email_to:
            tasks.append(self.send_email_alert(violation))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_slack_alert(self, violation: Violation) -> bool:
        """
        Send alert to Slack webhook.

        Args:
            violation: The violation to alert on

        Returns:
            True if successful, False otherwise
        """
        if not self.slack_webhook_url:
            return False

        try:
            # Build Slack message
            color = self._get_severity_color(violation.severity)
            message = self._build_slack_message(violation, color)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=message,
                    timeout=10.0,
                )
                response.raise_for_status()

            logger.info(f"Slack alert sent for violation: {violation.violation_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    def _build_slack_message(self, violation: Violation, color: str) -> dict[str, Any]:
        """Build Slack webhook message payload."""
        violations_text = ", ".join(violation.violations)

        return {
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 AI Compliance Alert: {violation.violation_type.replace('_', ' ').title()}",
                    "fields": [
                        {
                            "title": "Violations",
                            "value": violations_text,
                            "short": False,
                        },
                        {
                            "title": "Action Taken",
                            "value": violation.action_taken.upper(),
                            "short": True,
                        },
                        {
                            "title": "Severity",
                            "value": violation.severity.upper(),
                            "short": True,
                        },
                        {
                            "title": "Organization",
                            "value": violation.org_id or "N/A",
                            "short": True,
                        },
                        {
                            "title": "Application",
                            "value": violation.app_id or "N/A",
                            "short": True,
                        },
                        {
                            "title": "Model",
                            "value": violation.model or "N/A",
                            "short": True,
                        },
                        {
                            "title": "Request ID",
                            "value": violation.request_id or "N/A",
                            "short": True,
                        },
                    ],
                    "footer": "AI Compliance Platform",
                    "ts": int(violation.timestamp.timestamp()),
                }
            ]
        }

    def _get_severity_color(self, severity: str) -> str:
        """Get Slack attachment color for severity level."""
        colors = {
            "low": "#36a64f",  # Green
            "medium": "#ff9800",  # Orange
            "high": "#f44336",  # Red
            "critical": "#9c27b0",  # Purple
        }
        return colors.get(severity.lower(), "#ff9800")

    async def send_email_alert(self, violation: Violation) -> bool:
        """
        Send alert via email.

        Args:
            violation: The violation to alert on

        Returns:
            True if successful, False otherwise
        """
        if not self.email_enabled or not self.email_to:
            return False

        try:
            # Build email
            subject = f"[AI Compliance Alert] {violation.violation_type.replace('_', ' ').title()}"
            body = self._build_email_body(violation)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_from or "compliance@localhost"
            msg["To"] = ", ".join(self.email_to)

            # Add HTML body
            msg.attach(MIMEText(body, "html"))

            # Send email (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_email_sync, msg)

            logger.info(f"Email alert sent for violation: {violation.violation_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    def _send_email_sync(self, msg: MIMEMultipart) -> None:
        """Synchronous email sending (for use in executor)."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)

    def _build_email_body(self, violation: Violation) -> str:
        """Build HTML email body."""
        violations_list = "".join(f"<li>{v}</li>" for v in violation.violations)

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #f44336;">🚨 AI Compliance Alert</h2>

            <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Violation Type</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{violation.violation_type}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Violations</td>
                    <td style="padding: 10px; border: 1px solid #ddd;"><ul>{violations_list}</ul></td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Action Taken</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{violation.action_taken.upper()}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Severity</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{violation.severity.upper()}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Organization</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{violation.org_id or 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Application</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{violation.app_id or 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Model</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{violation.model or 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Request ID</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{violation.request_id or 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Timestamp</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{violation.timestamp.isoformat()}</td>
                </tr>
            </table>

            <p style="color: #666; margin-top: 20px; font-size: 12px;">
                This alert was generated by the AI Compliance Platform.
            </p>
        </body>
        </html>
        """


