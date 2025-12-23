"""
Policy Loader

Loads policies from YAML files.
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from .models import Policy

logger = logging.getLogger(__name__)


class PolicyLoader:
    """
    Loads and manages compliance policies from YAML files.
    """

    def __init__(self, policy_dir: str | Path | None = None):
        """
        Initialize the policy loader.

        Args:
            policy_dir: Directory containing policy files
        """
        self.policy_dir = Path(policy_dir) if policy_dir else None
        self._cached_policy: Policy | None = None
        self._cache_time: float = 0

    def load_from_file(self, file_path: str | Path) -> Policy:
        """
        Load a policy from a YAML file.

        Args:
            file_path: Path to the YAML policy file

        Returns:
            Loaded Policy object
        """
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"Policy file not found: {path}, using default policy")
            return self._default_policy()

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning(f"Empty policy file: {path}, using default policy")
                return self._default_policy()

            policy = Policy.from_dict(data)
            logger.info(f"Loaded policy '{policy.name}' from {path}")
            return policy

        except yaml.YAMLError as e:
            logger.error(f"Error parsing policy file {path}: {e}")
            return self._default_policy()
        except Exception as e:
            logger.error(f"Error loading policy file {path}: {e}")
            return self._default_policy()

    def load_from_string(self, yaml_content: str) -> Policy:
        """
        Load a policy from a YAML string.

        Args:
            yaml_content: YAML content as string

        Returns:
            Loaded Policy object
        """
        try:
            data = yaml.safe_load(yaml_content)
            if not data:
                return self._default_policy()
            return Policy.from_dict(data)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing policy YAML: {e}")
            return self._default_policy()

    def load_from_dict(self, data: dict[str, Any]) -> Policy:
        """
        Load a policy from a dictionary.

        Args:
            data: Policy data as dictionary

        Returns:
            Loaded Policy object
        """
        return Policy.from_dict(data)

    def _default_policy(self) -> Policy:
        """
        Return the default policy.

        The default policy:
        - Blocks critical PII (AADHAAR, PAN, CREDIT_CARD, SSN)
        - Masks medium PII (EMAIL, PHONE)
        - Allows all models and apps
        """
        return Policy.from_dict({
            "version": "1.0",
            "name": "Default Compliance Policy",
            "description": "Default policy that blocks critical PII and masks medium PII",
            "rules": {
                "block_if": ["AADHAAR", "PAN", "CREDIT_CARD", "SSN"],
                "mask_if": ["EMAIL", "PHONE"],
                "warn_if": ["IP_ADDRESS", "DATE_OF_BIRTH"],
                "allowed_models": [],  # Empty = all allowed
                "allowed_apps": ["*"],
            },
        })

    def get_default_policy(self) -> Policy:
        """Get the default policy."""
        return self._default_policy()


def load_policy_from_env() -> Policy:
    """
    Load policy from environment-configured file.

    Uses POLICY_FILE environment variable to locate the policy file.
    Falls back to default policy if not configured or file not found.
    """
    loader = PolicyLoader()
    policy_file = os.environ.get("POLICY_FILE")

    if policy_file:
        return loader.load_from_file(policy_file)

    return loader.get_default_policy()

