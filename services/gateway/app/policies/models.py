"""
Policy Models

Data models for compliance policies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PolicyAction(str, Enum):
    """Actions that can be taken based on policy evaluation."""

    ALLOW = "ALLOW"  # Request is allowed to proceed
    BLOCK = "BLOCK"  # Request is blocked
    MASK = "MASK"  # PII is masked before forwarding
    WARN = "WARN"  # Request proceeds but warning is logged


@dataclass
class PolicyRules:
    """Rules within a policy."""

    # PII types that should block the request
    block_if: list[str] = field(default_factory=list)

    # PII types that should be masked before forwarding
    mask_if: list[str] = field(default_factory=list)

    # PII types that should generate a warning but allow the request
    warn_if: list[str] = field(default_factory=list)

    # Allowed AI models (empty = all allowed)
    allowed_models: list[str] = field(default_factory=list)

    # Blocked AI models
    blocked_models: list[str] = field(default_factory=list)

    # Allowed applications (empty or ["*"] = all allowed)
    allowed_apps: list[str] = field(default_factory=lambda: ["*"])

    # Blocked applications
    blocked_apps: list[str] = field(default_factory=list)

    def is_model_allowed(self, model: str) -> bool:
        """Check if a model is allowed by this policy."""
        if model in self.blocked_models:
            return False
        if not self.allowed_models:
            return True
        return model in self.allowed_models

    def is_app_allowed(self, app_id: str) -> bool:
        """Check if an application is allowed by this policy."""
        if app_id in self.blocked_apps:
            return False
        if not self.allowed_apps or "*" in self.allowed_apps:
            return True
        return app_id in self.allowed_apps

    def should_block_pii(self, pii_types: list[str]) -> list[str]:
        """Get PII types that should cause blocking."""
        return [t for t in pii_types if t in self.block_if]

    def should_mask_pii(self, pii_types: list[str]) -> list[str]:
        """Get PII types that should be masked."""
        return [t for t in pii_types if t in self.mask_if]

    def should_warn_pii(self, pii_types: list[str]) -> list[str]:
        """Get PII types that should cause warning."""
        return [t for t in pii_types if t in self.warn_if]


@dataclass
class Policy:
    """A compliance policy definition."""

    version: str = "1.0"
    name: str = "Default Policy"
    description: str = ""
    rules: PolicyRules = field(default_factory=PolicyRules)
    org_overrides: dict[str, PolicyRules] = field(default_factory=dict)

    def get_rules_for_org(self, org_id: str | None) -> PolicyRules:
        """Get the effective rules for an organization."""
        if org_id and org_id in self.org_overrides:
            return self.org_overrides[org_id]
        return self.rules

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Policy":
        """Create a Policy from a dictionary."""
        rules_data = data.get("rules", {})
        rules = PolicyRules(
            block_if=rules_data.get("block_if", []),
            mask_if=rules_data.get("mask_if", []),
            warn_if=rules_data.get("warn_if", []),
            allowed_models=rules_data.get("allowed_models", []),
            blocked_models=rules_data.get("blocked_models", []),
            allowed_apps=rules_data.get("allowed_apps", ["*"]),
            blocked_apps=rules_data.get("blocked_apps", []),
        )

        # Parse org overrides
        org_overrides = {}
        for org_id, override_data in data.get("org_overrides", {}).items():
            org_overrides[org_id] = PolicyRules(
                block_if=override_data.get("block_if", rules.block_if),
                mask_if=override_data.get("mask_if", rules.mask_if),
                warn_if=override_data.get("warn_if", rules.warn_if),
                allowed_models=override_data.get("allowed_models", rules.allowed_models),
                blocked_models=override_data.get("blocked_models", rules.blocked_models),
                allowed_apps=override_data.get("allowed_apps", rules.allowed_apps),
                blocked_apps=override_data.get("blocked_apps", rules.blocked_apps),
            )

        return cls(
            version=data.get("version", "1.0"),
            name=data.get("name", "Default Policy"),
            description=data.get("description", ""),
            rules=rules,
            org_overrides=org_overrides,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert policy to dictionary."""
        return {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "rules": {
                "block_if": self.rules.block_if,
                "mask_if": self.rules.mask_if,
                "warn_if": self.rules.warn_if,
                "allowed_models": self.rules.allowed_models,
                "blocked_models": self.rules.blocked_models,
                "allowed_apps": self.rules.allowed_apps,
                "blocked_apps": self.rules.blocked_apps,
            },
        }


@dataclass
class PolicyResult:
    """Result of policy evaluation."""

    action: PolicyAction
    reason: str
    violations: list[str] = field(default_factory=list)
    pii_to_mask: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def should_block(self) -> bool:
        """Check if the request should be blocked."""
        return self.action == PolicyAction.BLOCK

    @property
    def should_mask(self) -> bool:
        """Check if PII should be masked."""
        return self.action == PolicyAction.MASK or bool(self.pii_to_mask)

    @property
    def should_alert(self) -> bool:
        """Check if an alert should be sent."""
        return self.action in (PolicyAction.BLOCK, PolicyAction.WARN)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "action": self.action.value,
            "reason": self.reason,
            "violations": self.violations,
            "pii_to_mask": self.pii_to_mask,
            "warnings": self.warnings,
        }


