"""
PII Detection Patterns

Regex patterns for detecting various types of Personally Identifiable Information (PII).
Each pattern includes the regex, a description, and severity level.
"""

import re
from enum import Enum
from dataclasses import dataclass


class PIIType(str, Enum):
    """Types of PII that can be detected."""

    EMAIL = "EMAIL"
    PHONE = "PHONE"
    PAN = "PAN"  # India PAN card
    AADHAAR = "AADHAAR"  # India Aadhaar
    CREDIT_CARD = "CREDIT_CARD"
    SSN = "SSN"  # US Social Security Number
    IP_ADDRESS = "IP_ADDRESS"
    PASSPORT = "PASSPORT"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    BANK_ACCOUNT = "BANK_ACCOUNT"


class Severity(str, Enum):
    """Severity levels for PII detections."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class PIIPattern:
    """Definition of a PII detection pattern."""

    pii_type: PIIType
    pattern: re.Pattern
    description: str
    severity: Severity
    examples: list[str]


# Email pattern - RFC 5322 simplified
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    re.IGNORECASE,
)

# Phone number patterns - International format
# Matches: +1-555-123-4567, +91 98765 43210, (555) 123-4567, 555-123-4567
PHONE_PATTERN = re.compile(
    r"(?:\+?1[-.\s]?)?"  # Optional country code for US
    r"(?:\+?91[-.\s]?)?"  # Optional country code for India
    r"(?:\(\d{3}\)|\d{3})[-.\s]?"  # Area code
    r"\d{3}[-.\s]?"  # First 3 digits
    r"\d{4}"  # Last 4 digits
    r"|\b\d{5}[-.\s]?\d{5}\b",  # Indian mobile format: 98765 43210
    re.IGNORECASE,
)

# India PAN Card - Format: ABCDE1234F (5 letters, 4 digits, 1 letter)
PAN_PATTERN = re.compile(
    r"\b[A-Z]{3}[ABCFGHLJPTK][A-Z]\d{4}[A-Z]\b",
    re.IGNORECASE,
)

# India Aadhaar - 12 digits, often formatted as XXXX XXXX XXXX
AADHAAR_PATTERN = re.compile(
    r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b",
)

# Credit Card Numbers - Major card formats with optional separators
# Visa: 4xxx, Mastercard: 5xxx, Amex: 34xx/37xx, Discover: 6xxx
CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:"
    r"4\d{3}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}"  # Visa
    r"|5[1-5]\d{2}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}"  # Mastercard
    r"|3[47]\d{2}[-.\s]?\d{6}[-.\s]?\d{5}"  # Amex
    r"|6(?:011|5\d{2})[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}"  # Discover
    r")\b",
)

# US Social Security Number - Format: XXX-XX-XXXX
SSN_PATTERN = re.compile(
    r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
)

# IPv4 Address
IP_ADDRESS_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
)

# Passport Number - Generic format (alphanumeric, 6-9 characters)
PASSPORT_PATTERN = re.compile(
    r"\b[A-Z]{1,2}\d{6,8}\b",
    re.IGNORECASE,
)

# Date of Birth - Common formats
DATE_OF_BIRTH_PATTERN = re.compile(
    r"\b(?:"
    r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"  # DD/MM/YYYY or MM/DD/YYYY
    r"|\d{4}[-/]\d{1,2}[-/]\d{1,2}"  # YYYY-MM-DD
    r")\b",
)

# Bank Account Numbers - Generic format (8-18 digits)
BANK_ACCOUNT_PATTERN = re.compile(
    r"\b\d{8,18}\b",
)


# All PII patterns with metadata
PII_PATTERNS: list[PIIPattern] = [
    PIIPattern(
        pii_type=PIIType.EMAIL,
        pattern=EMAIL_PATTERN,
        description="Email address",
        severity=Severity.MEDIUM,
        examples=["user@example.com", "john.doe@company.co.uk"],
    ),
    PIIPattern(
        pii_type=PIIType.PHONE,
        pattern=PHONE_PATTERN,
        description="Phone number (US/India formats)",
        severity=Severity.MEDIUM,
        examples=["+1-555-123-4567", "+91 98765 43210", "(555) 123-4567"],
    ),
    PIIPattern(
        pii_type=PIIType.PAN,
        pattern=PAN_PATTERN,
        description="India PAN Card number",
        severity=Severity.CRITICAL,
        examples=["ABCPD1234E", "BNZPM2501F"],
    ),
    PIIPattern(
        pii_type=PIIType.AADHAAR,
        pattern=AADHAAR_PATTERN,
        description="India Aadhaar number (12 digits)",
        severity=Severity.CRITICAL,
        examples=["1234 5678 9012", "123456789012"],
    ),
    PIIPattern(
        pii_type=PIIType.CREDIT_CARD,
        pattern=CREDIT_CARD_PATTERN,
        description="Credit card number (Visa, Mastercard, Amex, Discover)",
        severity=Severity.CRITICAL,
        examples=["4111-1111-1111-1111", "5500 0000 0000 0004"],
    ),
    PIIPattern(
        pii_type=PIIType.SSN,
        pattern=SSN_PATTERN,
        description="US Social Security Number",
        severity=Severity.CRITICAL,
        examples=["123-45-6789", "123 45 6789"],
    ),
    PIIPattern(
        pii_type=PIIType.IP_ADDRESS,
        pattern=IP_ADDRESS_PATTERN,
        description="IPv4 address",
        severity=Severity.LOW,
        examples=["192.168.1.1", "10.0.0.1"],
    ),
    PIIPattern(
        pii_type=PIIType.PASSPORT,
        pattern=PASSPORT_PATTERN,
        description="Passport number",
        severity=Severity.HIGH,
        examples=["A12345678", "AB1234567"],
    ),
    PIIPattern(
        pii_type=PIIType.DATE_OF_BIRTH,
        pattern=DATE_OF_BIRTH_PATTERN,
        description="Date of birth",
        severity=Severity.MEDIUM,
        examples=["15/03/1990", "1990-03-15"],
    ),
]


def get_pattern_by_type(pii_type: PIIType) -> PIIPattern | None:
    """Get a PII pattern by its type."""
    for pattern in PII_PATTERNS:
        if pattern.pii_type == pii_type:
            return pattern
    return None


def get_severity_for_type(pii_type: PIIType) -> Severity:
    """Get the severity level for a PII type."""
    pattern = get_pattern_by_type(pii_type)
    if pattern:
        return pattern.severity
    return Severity.MEDIUM

