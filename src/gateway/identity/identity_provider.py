import importlib

from ...gateway.identity.passthru_identity import PassthruIdentity
from ...gateway.identity.bamboohr_identity import BambooHRIdentity
from ...gateway.identity.no_identity import NoIdentity
from ...gateway.identity.identity_base import IdentityBase
from ...common.constants import DEFAULT_IDENTITY_KEY_FIELD

IDENTITY_PROVIDERS = {
    "passthru": PassthruIdentity,
    "bamboohr": BambooHRIdentity,
    "none": NoIdentity,
}

DEFAULT_PROVIDER = "none"

class IdentityProvider:
    identity_provider: IdentityBase

    def __init__(self, config=None):
        self.config = config or {}
        self.provider_type = self.config.get("type", DEFAULT_PROVIDER)
        self.identity_field = self.config.get("key_field", DEFAULT_IDENTITY_KEY_FIELD)
        if self.provider_type not in IDENTITY_PROVIDERS and not self.config.get("module_path"):
            raise ValueError(
                f"Unsupported identity provider type: {self.provider_type}. No module_path provided."
            )

        provider_configuration = self.config.get("configuration", {})

        if self.provider_type in IDENTITY_PROVIDERS:
            # Load built-in identity provider
            self.identity_provider = IDENTITY_PROVIDERS[self.provider_type](provider_configuration)
        else:
            try:
                # Load the provider from the module path
                module_name = self.provider_type
                module_path = self.config.get("module_path")
                module = importlib.import_module(module_path, package=__package__)
                identity_class = getattr(module, module_name)
                if not issubclass(identity_class, IdentityBase):
                    raise ValueError(
                        f"Identity provider class {identity_class} does not inherit from IdentityBase"
                    )
                self.identity_provider = identity_class(provider_configuration)
            except Exception as e:
                raise ImportError("Unable to load component: " + str(e)) from e

    def get_identity_field(self) -> str:
        """Returns the configured field name to use for identity lookup"""
        return self.identity_field

    def get_user_info(self, identity: str) -> dict:
        """
        Get user information using the configured identity provider.

        :param identity: The user identity string (usually email)
        :return: Dictionary containing user information
        """
        return self.identity_provider.get_user_info(identity)