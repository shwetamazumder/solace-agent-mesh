from abc import ABC, abstractmethod
from typing import List

from ....common.constants import DEFAULT_IDENTITY_KEY_FIELD

class BaseAuthorizationProvider(ABC):
    PERMISSIVE_SCOPES = ["*:*:*"]
    NO_SCOPES = []

    def __init__(self, config: dict):
        self.base_roles = config.get("base_roles", ["least_privileged_user"])
        self.role_to_scope_mappings = config.get(
            "role_to_scope_mappings",
            {"least_privileged_user": BaseAuthorizationProvider.NO_SCOPES},
        )
        self.configuration = config.get("configuration", {})
        self.authorization_field = config.get("key_field", DEFAULT_IDENTITY_KEY_FIELD)

    @abstractmethod
    def get_authorization_field(self) -> str:
        """Returns the configured field name to use for authorization lookup"""
        pass

    @abstractmethod
    def get_scopes(self, identity: str) -> List[str]:
        """Get scopes for a given identity."""
        pass

    @abstractmethod
    def get_roles(self, identity: str) -> List[str]:
        """Get roles for a given identity."""
        pass

    @staticmethod
    def is_authorized(originator_scopes: List[str], agent_scopes: List[str]) -> bool:
        """Check if the originator's scopes authorize access to the agent's scopes."""
        return any(
            BaseAuthorizationProvider._scope_matches(originator_scope, agent_scope)
            for originator_scope in originator_scopes
            for agent_scope in agent_scopes
        )

    @staticmethod
    def _scope_matches(originator_scope: str, agent_scope: str) -> bool:
        if not isinstance(originator_scope, str) or not isinstance(agent_scope, str):
            return False
        if not originator_scope or not agent_scope:
            return False
        originator_parts = originator_scope.split(":")
        agent_parts = agent_scope.split(":")
        if len(originator_parts) != 3 or len(agent_parts) != 3:
            return False
        return all(
            orig == agent or orig == "*" or agent == "*"
            for orig, agent in zip(originator_parts, agent_parts)
        )