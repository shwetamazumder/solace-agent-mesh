from abc import ABC, abstractmethod

class IdentityBase(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def get_user_info(self, identity: str) -> dict:
        """Get user information for a given identity."""
        pass