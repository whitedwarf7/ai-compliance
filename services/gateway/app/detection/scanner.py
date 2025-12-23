"""
Prompt Scanner

Scans conversation messages for PII using the PIIDetector.
"""

from dataclasses import dataclass, field
from typing import Any

from .detector import Detection, DetectionResult, PIIDetector
from .patterns import PIIType, Severity


@dataclass
class MessageScan:
    """Result of scanning a single message."""

    role: str
    index: int
    detection_result: DetectionResult

    @property
    def has_pii(self) -> bool:
        return self.detection_result.has_pii

    @property
    def detections(self) -> list[Detection]:
        return self.detection_result.detections


@dataclass
class ScanResult:
    """Result of scanning all messages in a conversation."""

    message_scans: list[MessageScan] = field(default_factory=list)
    total_detections: int = 0
    highest_severity: Severity = Severity.LOW
    pii_types_found: list[PIIType] = field(default_factory=list)

    @property
    def has_pii(self) -> bool:
        """Check if any PII was detected in any message."""
        return self.total_detections > 0

    @property
    def critical_found(self) -> bool:
        """Check if any critical severity PII was found."""
        return self.highest_severity == Severity.CRITICAL

    @property
    def risk_flags(self) -> list[str]:
        """Get list of PII types as risk flags for audit log."""
        return [t.value for t in self.pii_types_found]

    def get_detections_by_type(self, pii_type: PIIType) -> list[Detection]:
        """Get all detections of a specific type."""
        detections = []
        for scan in self.message_scans:
            detections.extend(
                d for d in scan.detections if d.pii_type == pii_type
            )
        return detections

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "has_pii": self.has_pii,
            "total_detections": self.total_detections,
            "highest_severity": self.highest_severity.value,
            "pii_types_found": [t.value for t in self.pii_types_found],
            "messages_with_pii": sum(1 for s in self.message_scans if s.has_pii),
            "total_messages_scanned": len(self.message_scans),
        }


class PromptScanner:
    """
    Scans conversation messages for PII.

    This scanner processes all messages in a conversation and aggregates
    the detection results into a single ScanResult.
    """

    def __init__(
        self,
        detector: PIIDetector | None = None,
        scan_roles: list[str] | None = None,
    ):
        """
        Initialize the prompt scanner.

        Args:
            detector: PIIDetector instance (creates default if not provided)
            scan_roles: Message roles to scan (defaults to all)
        """
        self.detector = detector or PIIDetector()
        self.scan_roles = scan_roles  # None means scan all roles

    def scan(self, messages: list[dict[str, str]]) -> ScanResult:
        """
        Scan all messages for PII.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            ScanResult with aggregated detection information
        """
        message_scans: list[MessageScan] = []
        all_pii_types: set[PIIType] = set()
        highest_severity = Severity.LOW
        total_detections = 0

        for index, message in enumerate(messages):
            role = message.get("role", "unknown")
            content = message.get("content", "")

            # Skip if role not in scan_roles
            if self.scan_roles and role not in self.scan_roles:
                continue

            # Detect PII in message content
            detection_result = self.detector.detect(content)

            message_scan = MessageScan(
                role=role,
                index=index,
                detection_result=detection_result,
            )
            message_scans.append(message_scan)

            # Aggregate results
            if detection_result.has_pii:
                total_detections += len(detection_result.detections)
                all_pii_types.update(detection_result.pii_types)

                # Update highest severity
                if self._severity_rank(detection_result.highest_severity) > self._severity_rank(highest_severity):
                    highest_severity = detection_result.highest_severity

        return ScanResult(
            message_scans=message_scans,
            total_detections=total_detections,
            highest_severity=highest_severity if total_detections > 0 else Severity.LOW,
            pii_types_found=list(all_pii_types),
        )

    def _severity_rank(self, severity: Severity) -> int:
        """Get numeric rank for severity level."""
        ranks = {
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        return ranks.get(severity, 0)

    def quick_check(self, messages: list[dict[str, str]]) -> bool:
        """
        Quickly check if any PII is present in messages.

        This is faster than full scan when you only need a boolean result.
        """
        for message in messages:
            content = message.get("content", "")
            if self.detector.detect_types(content):
                return True
        return False

