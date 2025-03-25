from solace_ai_connector.components.component_base import ComponentBase
from solace_ai_connector.common.log import log
from ...services.history_service import HistoryService
from ..identity.identity_provider import IdentityProvider
from ...common.constants import DEFAULT_IDENTITY_KEY_FIELD


class GatewayBase(ComponentBase):
    def __init__(self, info, **kwargs):
        super().__init__(info, **kwargs)
        self.gateway_id = self.get_config("gateway_id", "default-change-me")
        self.history_instance = self._initialize_history()

    def _initialize_history(self):
        self.use_history = self.get_config("retain_history", True)

        if not self.use_history:
            return None

        history_config = self.get_config("history_config", {})

        try:
            return HistoryService(
                history_config, identifier=self.gateway_id + "_history"
            )
        except (ImportError, AttributeError, ValueError) as e:
            log.error("Failed to load history class: %s", e)
            raise

    def _initialize_identity_component(self):
        identity_config = self.get_config("identity", {})
        identity_key_field = self.get_config("identity_key_field", DEFAULT_IDENTITY_KEY_FIELD)
        
        if "key_field" not in identity_config:
            identity_config["key_field"] = identity_key_field

        try:
            return IdentityProvider(identity_config)
        except (ImportError, AttributeError, ValueError) as e:
            log.error("Failed to load identity class: %s", e)
            raise
