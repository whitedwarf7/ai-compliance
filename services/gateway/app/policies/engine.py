"""
Policy Engine

Evaluates requests against compliance policies.
"""

import logging
from typing import Any

from ..detection.scanner import ScanResult
from .loader import PolicyLoader, load_policy_from_env
from .models import Policy, PolicyAction, PolicyResult, PolicyRules

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Evaluates requests against compliance policies.

    The engine checks:
    1. Whether the model is allowed
    2. Whether the application is allowed
    3. Whether detected PII should block, mask, or warn
    """

    def __init__(self, policy: Policy | None = None):
        """
        Initialize the policy engine.

        Args:
            policy: Policy to use (loads from env/default if not provided)
        """
        self.policy = policy or load_policy_from_env()
        logger.info(f"Policy engine initialized with policy: {self.policy.name}")

    def reload_policy(self, policy_file: str | None = None) -> None:
        """
        Reload the policy from file.

        Args:
            policy_file: Path to policy file (uses env if not provided)
        """
        loader = PolicyLoader()
        if policy_file:
            self.policy = loader.load_from_file(policy_file)
        else:
            self.policy = load_policy_from_env()
        logger.info(f"Policy reloaded: {self.policy.name}")

    def evaluate(
        self,
        model: str,
        app_id: str | None,
        org_id: str | None,
        scan_result: ScanResult,
    ) -> PolicyResult:
        """
        Evaluate a request against the policy.

        Args:
            model: The AI model being requested
            app_id: The application ID making the request
            org_id: The organization ID
            scan_result: Results from PII scanning

        Returns:
            PolicyResult indicating what action to take
        """
        # Get effective rules for this organization
        rules = self.policy.get_rules_for_org(org_id)

        # Check model allowlist/blocklist
        if not rules.is_model_allowed(model):
            return PolicyResult(
                action=PolicyAction.BLOCK,
                reason=f"Model '{model}' is not allowed by policy",
                violations=[f"MODEL_NOT_ALLOWED:{model}"],
            )

        # Check app allowlist/blocklist
        if app_id and not rules.is_app_allowed(app_id):
            return PolicyResult(
                action=PolicyAction.BLOCK,
                reason=f"Application '{app_id}' is not allowed by policy",
                violations=[f"APP_NOT_ALLOWED:{app_id}"],
            )

        # If no PII detected, allow
        if not scan_result.has_pii:
            return PolicyResult(
                action=PolicyAction.ALLOW,
                reason="No PII detected, request allowed",
            )

        # Check PII types against rules
        pii_types = scan_result.risk_flags

        # Check for blocking PII
        block_pii = rules.should_block_pii(pii_types)
        if block_pii:
            return PolicyResult(
                action=PolicyAction.BLOCK,
                reason=f"Request blocked: {', '.join(block_pii)} detected in prompt",
                violations=block_pii,
            )

        # Check for masking PII
        mask_pii = rules.should_mask_pii(pii_types)

        # Check for warning PII
        warn_pii = rules.should_warn_pii(pii_types)

        # Determine action
        if mask_pii:
            return PolicyResult(
                action=PolicyAction.MASK,
                reason=f"PII will be masked: {', '.join(mask_pii)}",
                pii_to_mask=mask_pii,
                warnings=warn_pii,
            )

        if warn_pii:
            return PolicyResult(
                action=PolicyAction.WARN,
                reason=f"Warning: {', '.join(warn_pii)} detected but allowed",
                warnings=warn_pii,
            )

        # PII detected but not in any rule list - allow with warning
        return PolicyResult(
            action=PolicyAction.ALLOW,
            reason="PII detected but not in policy rules",
            warnings=pii_types,
        )

    def get_policy_for_org(self, org_id: str | None) -> PolicyRules:
        """Get the effective policy rules for an organization."""
        return self.policy.get_rules_for_org(org_id)

    def get_policy_info(self) -> dict[str, Any]:
        """Get information about the current policy."""
        return {
            "name": self.policy.name,
            "version": self.policy.version,
            "description": self.policy.description,
            "rules": self.policy.to_dict()["rules"],
            "org_overrides": list(self.policy.org_overrides.keys()),
        }

