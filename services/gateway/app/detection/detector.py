"""
PII Detector

Main detection class that scans text for PII using regex patterns.
"""

from dataclasses import dataclass, field
from typing import Any

from .patterns import PII_PATTERNS, PIIPattern, PIIType, Severity, get_severity_for_type


@dataclass
class Detection:
    """Represents a single PII detection in text."""

    pii_type: PIIType
    value: str
    start: int
    end: int
    severity: Severity
    masked_value: str = ""

    def __post_init__(self):
        """Generate masked value if not provided."""
        if not self.masked_value:
            self.masked_value = f"[{self.pii_type.value}_REDACTED]"

    def to_dict(self) -> dict[str, Any]:
        """Convert detection to dictionary."""
        return {
            "pii_type": self.pii_type.value,
            "start": self.start,
            "end": self.end,
            "severity": self.severity.value,
            "masked_value": self.masked_value,
        }


@dataclass
class DetectionResult:
    """Result of PII detection on a piece of text."""

    text: str
    detections: list[Detection] = field(default_factory=list)
    highest_severity: Severity = Severity.LOW

    @property
    def has_pii(self) -> bool:
        """Check if any PII was detected."""
        return len(self.detections) > 0

    @property
    def pii_types(self) -> list[PIIType]:
        """Get unique list of detected PII types."""
        return list(set(d.pii_type for d in self.detections))

    @property
    def critical_detections(self) -> list[Detection]:
        """Get only critical severity detections."""
        return [d for d in self.detections if d.severity == Severity.CRITICAL]

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "has_pii": self.has_pii,
            "detection_count": len(self.detections),
            "pii_types": [t.value for t in self.pii_types],
            "highest_severity": self.highest_severity.value,
            "detections": [d.to_dict() for d in self.detections],
        }


class PIIDetector:
    """
    Detects PII in text using regex patterns.

    The detector scans text for various types of PII including emails,
    phone numbers, credit cards, SSNs, Aadhaar, PAN, and more.
    """

    def __init__(
        self,
        patterns: list[PIIPattern] | None = None,
        enabled_types: list[PIIType] | None = None,
        disabled_types: list[PIIType] | None = None,
    ):
        """
        Initialize the PII detector.

        Args:
            patterns: Custom patterns to use (defaults to PII_PATTERNS)
            enabled_types: If set, only detect these PII types
            disabled_types: If set, skip these PII types
        """
        self.patterns = patterns or PII_PATTERNS
        self.enabled_types = enabled_types
        self.disabled_types = disabled_types or []

    def _should_check_pattern(self, pattern: PIIPattern) -> bool:
        """Check if a pattern should be used for detection."""
        if self.enabled_types and pattern.pii_type not in self.enabled_types:
            return False
        if pattern.pii_type in self.disabled_types:
            return False
        return True

    def detect(self, text: str) -> DetectionResult:
        """
        Scan text for PII.

        Args:
            text: The text to scan

        Returns:
            DetectionResult containing all detections
        """
        if not text:
            return DetectionResult(text=text)

        detections: list[Detection] = []
        highest_severity = Severity.LOW

        for pattern in self.patterns:
            if not self._should_check_pattern(pattern):
                continue

            matches = pattern.pattern.finditer(text)
            for match in matches:
                detection = Detection(
                    pii_type=pattern.pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    severity=pattern.severity,
                )
                detections.append(detection)

                # Track highest severity
                if self._severity_rank(pattern.severity) > self._severity_rank(highest_severity):
                    highest_severity = pattern.severity

        # Sort detections by position
        detections.sort(key=lambda d: d.start)

        # Remove overlapping detections (keep higher severity)
        detections = self._remove_overlaps(detections)

        return DetectionResult(
            text=text,
            detections=detections,
            highest_severity=highest_severity if detections else Severity.LOW,
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

    def _remove_overlaps(self, detections: list[Detection]) -> list[Detection]:
        """
        Remove overlapping detections, keeping higher severity ones.

        For example, a phone number might also match as a partial credit card.
        We keep the detection with higher severity.
        """
        if not detections:
            return detections

        result: list[Detection] = []
        for detection in detections:
            # Check if this detection overlaps with any in result
            overlaps = False
            for i, existing in enumerate(result):
                if self._ranges_overlap(
                    (detection.start, detection.end),
                    (existing.start, existing.end),
                ):
                    overlaps = True
                    # Keep the one with higher severity
                    if self._severity_rank(detection.severity) > self._severity_rank(existing.severity):
                        result[i] = detection
                    break

            if not overlaps:
                result.append(detection)

        return result

    def _ranges_overlap(self, r1: tuple[int, int], r2: tuple[int, int]) -> bool:
        """Check if two ranges overlap."""
        return r1[0] < r2[1] and r2[0] < r1[1]

    def get_severity(self, pii_type: PIIType) -> Severity:
        """Get severity level for a PII type."""
        return get_severity_for_type(pii_type)

    def detect_types(self, text: str) -> list[PIIType]:
        """
        Quickly detect which PII types are present in text.

        Returns only the types, not the full detection details.
        """
        result = self.detect(text)
        return result.pii_types


