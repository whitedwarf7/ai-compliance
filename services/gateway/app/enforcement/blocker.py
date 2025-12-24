"""
Request Blocker

Handles blocking requests that violate compliance policies.
"""

from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse


@dataclass
class BlockResponse:
    """Response returned when a request is blocked."""

    error_type: str = "policy_violation"
    code: str = "pii_detected"
    message: str = "Request blocked due to policy violation"
    violations: list[str] = field(default_factory=list)
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "error": {
                "type": self.error_type,
                "code": self.code,
                "message": self.message,
                "violations": self.violations,
                "request_id": self.request_id,
            }
        }

    def to_json_response(self, status_code: int = 403) -> JSONResponse:
        """Convert to FastAPI JSONResponse."""
        return JSONResponse(
            status_code=status_code,
            content=self.to_dict(),
        )


class RequestBlocker:
    """
    Handles blocking requests that violate compliance policies.

    Creates appropriate error responses for blocked requests.
    """

    def block_pii_violation(
        self,
        violations: list[str],
        request_id: str | None = None,
    ) -> BlockResponse:
        """
        Create a block response for PII violations.

        Args:
            violations: List of PII types that caused the block
            request_id: Optional request ID for tracking

        Returns:
            BlockResponse with violation details
        """
        message = f"Request blocked: {', '.join(violations)} detected in prompt"
        return BlockResponse(
            error_type="policy_violation",
            code="pii_detected",
            message=message,
            violations=violations,
            request_id=request_id,
        )

    def block_model_not_allowed(
        self,
        model: str,
        request_id: str | None = None,
    ) -> BlockResponse:
        """
        Create a block response for disallowed model.

        Args:
            model: The model that was requested
            request_id: Optional request ID for tracking

        Returns:
            BlockResponse with violation details
        """
        return BlockResponse(
            error_type="policy_violation",
            code="model_not_allowed",
            message=f"Model '{model}' is not allowed by policy",
            violations=[f"MODEL_NOT_ALLOWED:{model}"],
            request_id=request_id,
        )

    def block_app_not_allowed(
        self,
        app_id: str,
        request_id: str | None = None,
    ) -> BlockResponse:
        """
        Create a block response for disallowed application.

        Args:
            app_id: The application ID that was blocked
            request_id: Optional request ID for tracking

        Returns:
            BlockResponse with violation details
        """
        return BlockResponse(
            error_type="policy_violation",
            code="app_not_allowed",
            message=f"Application '{app_id}' is not allowed by policy",
            violations=[f"APP_NOT_ALLOWED:{app_id}"],
            request_id=request_id,
        )

    def raise_block_exception(self, block_response: BlockResponse) -> None:
        """
        Raise an HTTPException for a blocked request.

        Args:
            block_response: The block response to raise

        Raises:
            HTTPException with 403 status code
        """
        raise HTTPException(
            status_code=403,
            detail=block_response.to_dict(),
        )


