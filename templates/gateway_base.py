"""Base class for all {{CAMEL_CASE_NAME}} gateways"""

from abc import ABC, abstractmethod
from solace_ai_connector.components.component_base import ComponentBase


# You can use a singleton pattern or a class variable to
# share a state between the input and output gateways

class {{CAMEL_CASE_NAME}}Base(ComponentBase, ABC):
    """Base class for all {{CAMEL_CASE_NAME}} gateways"""

    @abstractmethod
    def invoke(self, message, data):
        pass
