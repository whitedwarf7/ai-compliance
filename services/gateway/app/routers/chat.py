import hashlib
import logging
import time
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel

from ..config import settings
from ..detection import PromptScanner, PIIDetector
from ..enforcement import RequestBlocker, PIIMasker, Alerter, Violation
from ..policies import PolicyEngine, PolicyAction
from ..providers import AzureOpenAIProvider, OpenAIProvider

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize components
pii_detector = PIIDetector()
prompt_scanner = PromptScanner(detector=pii_detector)
policy_engine = PolicyEngine()
request_blocker = RequestBlocker()
pii_masker = PIIMasker()
alerter = Alerter(
    slack_webhook_url=settings.alert_slack_webhook or None,
    email_enabled=settings.alert_email_enabled,
    smtp_host=settings.alert_email_smtp_host or None,
    smtp_port=settings.alert_email_smtp_port,
    smtp_user=settings.alert_email_smtp_user or None,
    smtp_password=settings.alert_email_smtp_password or None,
    email_from=settings.alert_email_from or None,
    email_to=settings.alert_email_recipients,
)


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[Message]
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop: list[str] | str | None = None
    stream: bool = False
    user: str | None = None

    class Config:
        extra = "allow"


def get_provider():
    """Get the configured AI provider."""
    if settings.ai_provider == "azure":
        return AzureOpenAIProvider(
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            deployment=settings.azure_openai_deployment,
            api_version=settings.azure_openai_api_version,
        )
    else:
        return OpenAIProvider(api_key=settings.openai_api_key)


def hash_prompt(messages: list[Message]) -> str:
    """Create a SHA-256 hash of the prompt messages."""
    content = "".join(f"{m.role}:{m.content}" for m in messages)
    return hashlib.sha256(content.encode()).hexdigest()


async def send_audit_log(log_data: dict[str, Any]):
    """Send audit log to the audit service asynchronously."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.audit_service_url}/api/v1/logs",
                json=log_data,
                timeout=5.0,
            )
    except Exception as e:
        logger.error(f"Failed to send audit log: {e}")


async def send_violation_alert(violation: Violation):
    """Send alert for a violation."""
    try:
        await alerter.send_alert(violation)
    except Exception as e:
        logger.error(f"Failed to send violation alert: {e}")


@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    x_app_key: str | None = Header(None, alias="X-App-Key"),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_org_id: str | None = Header(None, alias="X-Org-Id"),
):
    """
    OpenAI-compatible chat completions endpoint.

    This endpoint proxies requests to the configured AI provider while:
    - Scanning prompts for PII
    - Evaluating requests against compliance policies
    - Blocking, masking, or warning based on policy
    - Logging all requests to the audit service
    - Sending alerts for violations
    """
    request_id = str(uuid4())

    if body.stream:
        raise HTTPException(
            status_code=400,
            detail="Streaming is not supported in Phase 1",
        )

    # Use default model if not specified
    model = body.model or settings.default_model

    # Convert messages to dict format for scanning
    messages_dict = [{"role": m.role, "content": m.content} for m in body.messages]

    # Initialize risk flags and policy result
    risk_flags: list[str] = []
    policy_action = PolicyAction.ALLOW
    action_taken = "allowed"
    violations: list[str] = []

    # Phase 2: PII Detection and Policy Enforcement
    if settings.pii_detection_enabled:
        # Scan messages for PII
        scan_result = prompt_scanner.scan(messages_dict)

        if scan_result.has_pii:
            risk_flags = scan_result.risk_flags
            logger.info(
                f"Request {request_id}: PII detected - {risk_flags}",
                extra={"request_id": request_id, "pii_types": risk_flags},
            )

        # Evaluate against policy
        policy_result = policy_engine.evaluate(
            model=model,
            app_id=x_app_key,
            org_id=x_org_id,
            scan_result=scan_result,
        )

        policy_action = policy_result.action
        violations = policy_result.violations

        # Handle policy decision based on enforcement mode
        if settings.enforcement_mode == "enforce":
            if policy_result.should_block:
                # Create violation for alerting
                violation = Violation(
                    violation_type="pii_detected" if risk_flags else "policy_violation",
                    violations=violations,
                    org_id=x_org_id,
                    app_id=x_app_key,
                    user_id=x_user_id,
                    model=model,
                    request_id=request_id,
                    action_taken="blocked",
                    severity="critical" if scan_result.critical_found else "high",
                )

                # Send alert in background
                background_tasks.add_task(send_violation_alert, violation)

                # Log the blocked request
                audit_log = {
                    "id": request_id,
                    "org_id": x_org_id or "default",
                    "app_id": x_app_key or "unknown",
                    "user_id": x_user_id,
                    "model": model,
                    "provider": settings.ai_provider,
                    "prompt_hash": hash_prompt(body.messages),
                    "token_count_input": None,
                    "token_count_output": None,
                    "latency_ms": 0,
                    "risk_flags": risk_flags,
                    "metadata": {
                        "action": "blocked",
                        "violations": violations,
                        "reason": policy_result.reason,
                    },
                }
                background_tasks.add_task(send_audit_log, audit_log)

                # Block the request
                block_response = request_blocker.block_pii_violation(
                    violations=violations,
                    request_id=request_id,
                )
                return block_response.to_json_response()

            elif policy_result.should_mask:
                # Mask PII in messages before forwarding
                messages_dict = pii_masker.mask_from_scan_result(
                    messages=messages_dict,
                    scan_result=scan_result,
                    types_to_mask=policy_result.pii_to_mask,
                )
                action_taken = "masked"
                logger.info(
                    f"Request {request_id}: PII masked - {policy_result.pii_to_mask}",
                    extra={"request_id": request_id, "masked_types": policy_result.pii_to_mask},
                )

        elif settings.enforcement_mode == "warn":
            # Just log warnings, don't block or mask
            if policy_result.should_block or policy_result.warnings:
                action_taken = "warned"
                logger.warning(
                    f"Request {request_id}: Policy violation (warn mode) - {violations or policy_result.warnings}",
                    extra={"request_id": request_id, "violations": violations},
                )

        # If enforcement_mode is "log_only", we just continue

    # Update the payload with the (possibly masked) messages
    payload = body.model_dump(exclude_none=True)
    payload["model"] = model
    payload["messages"] = messages_dict

    # Get provider and make request
    provider = get_provider()
    start_time = time.time()

    try:
        response_data, status_code = await provider.chat_completion(payload)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to AI provider timed out")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Error connecting to AI provider: {str(e)}")
    finally:
        await provider.close()

    latency_ms = int((time.time() - start_time) * 1000)

    # Extract token usage from response
    usage = response_data.get("usage", {})
    token_count_input = usage.get("prompt_tokens")
    token_count_output = usage.get("completion_tokens")

    # Prepare audit log
    audit_log = {
        "id": request_id,
        "org_id": x_org_id or "default",
        "app_id": x_app_key or "unknown",
        "user_id": x_user_id,
        "model": model,
        "provider": provider.get_provider_name(),
        "prompt_hash": hash_prompt(body.messages),
        "token_count_input": token_count_input,
        "token_count_output": token_count_output,
        "latency_ms": latency_ms,
        "risk_flags": risk_flags,
        "metadata": {
            "client_ip": request.client.host if request.client else None,
            "request_id": response_data.get("id"),
            "action": action_taken,
            "violations": violations if violations else None,
        },
    }

    # Send audit log in background
    background_tasks.add_task(send_audit_log, audit_log)

    # Send alert for masked requests if configured
    if action_taken == "masked" and settings.alert_slack_webhook:
        violation = Violation(
            violation_type="pii_masked",
            violations=risk_flags,
            org_id=x_org_id,
            app_id=x_app_key,
            user_id=x_user_id,
            model=model,
            request_id=request_id,
            action_taken="masked",
            severity="medium",
        )
        background_tasks.add_task(send_violation_alert, violation)

    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=response_data)

    return response_data


@router.get("/policy")
async def get_current_policy():
    """Get the current policy configuration."""
    return policy_engine.get_policy_info()


@router.post("/policy/reload")
async def reload_policy():
    """Reload the policy from file."""
    policy_engine.reload_policy()
    return {
        "status": "success",
        "message": "Policy reloaded",
        "policy": policy_engine.get_policy_info(),
    }
