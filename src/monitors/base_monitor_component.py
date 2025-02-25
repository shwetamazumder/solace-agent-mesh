"""Base class for all monitor components in the Solace Agent Mesh.

Monitors are passive listeners that observe and track events in the mesh. They may
trigger agent actions but are not agents themselves.
"""

from typing import Any, Dict, Optional
from solace_ai_connector.components.component_base import ComponentBase
from solace_ai_connector.common.message import Message


class BaseMonitorComponent(ComponentBase):
    """Base class for monitor components.

    Provides common functionality for monitoring mesh events and interacting
    with agents when needed.
    """

    def __init__(self, module_info: Optional[Dict] = None, **kwargs: Any) -> None:
        """Initialize the monitor component.

        Args:
            module_info: Optional configuration dictionary for the module.
            **kwargs: Additional keyword arguments passed to parent class.
        """
        super().__init__(module_info or {}, **kwargs)
