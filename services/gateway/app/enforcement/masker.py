"""
PII Masker

Masks detected PII in text before forwarding to AI providers.
"""

from ..detection.detector import Detection
from ..detection.patterns import PIIType


class PIIMasker:
    """
    Masks PII in text by replacing detected values with redaction placeholders.

    Example:
        "Contact john@email.com" -> "Contact [EMAIL_REDACTED]"
    """

    def __init__(self, mask_format: str = "[{type}_REDACTED]"):
        """
        Initialize the masker.

        Args:
            mask_format: Format string for masked values. Use {type} for PII type.
        """
        self.mask_format = mask_format

    def get_mask_value(self, pii_type: PIIType) -> str:
        """Get the mask value for a PII type."""
        return self.mask_format.format(type=pii_type.value)

    def mask_text(
        self,
        text: str,
        detections: list[Detection],
        types_to_mask: list[str] | None = None,
    ) -> str:
        """
        Mask detected PII in text.

        Args:
            text: The original text
            detections: List of PII detections from the detector
            types_to_mask: Optional list of PII types to mask (masks all if None)

        Returns:
            Text with PII replaced by mask values
        """
        if not detections:
            return text

        # Filter detections if types_to_mask is specified
        if types_to_mask:
            detections = [
                d for d in detections
                if d.pii_type.value in types_to_mask
            ]

        if not detections:
            return text

        # Sort detections by position (reverse order to preserve positions)
        sorted_detections = sorted(detections, key=lambda d: d.start, reverse=True)

        # Replace each detection with its mask
        result = text
        for detection in sorted_detections:
            mask = self.get_mask_value(detection.pii_type)
            result = result[:detection.start] + mask + result[detection.end:]

        return result

    def mask_messages(
        self,
        messages: list[dict[str, str]],
        message_detections: dict[int, list[Detection]],
        types_to_mask: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """
        Mask PII in a list of messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            message_detections: Dict mapping message index to detections
            types_to_mask: Optional list of PII types to mask

        Returns:
            New list of messages with PII masked
        """
        masked_messages = []

        for i, message in enumerate(messages):
            if i in message_detections and message_detections[i]:
                masked_content = self.mask_text(
                    message.get("content", ""),
                    message_detections[i],
                    types_to_mask,
                )
                masked_messages.append({
                    **message,
                    "content": masked_content,
                })
            else:
                masked_messages.append(message.copy())

        return masked_messages

    def mask_from_scan_result(
        self,
        messages: list[dict[str, str]],
        scan_result,  # ScanResult type
        types_to_mask: list[str] | None = None,
    ) -> list[dict[str, str]]:
        """
        Mask PII in messages using a ScanResult.

        Args:
            messages: List of message dicts
            scan_result: ScanResult from PromptScanner
            types_to_mask: Optional list of PII types to mask

        Returns:
            New list of messages with PII masked
        """
        # Build detection map from scan result
        message_detections: dict[int, list[Detection]] = {}

        for message_scan in scan_result.message_scans:
            if message_scan.has_pii:
                message_detections[message_scan.index] = message_scan.detections

        return self.mask_messages(messages, message_detections, types_to_mask)


