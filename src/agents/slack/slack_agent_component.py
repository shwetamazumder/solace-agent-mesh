"""Slack agent for posting messages to Slack channels."""

import copy
from slack_sdk import WebClient

from ..base_agent_component import agent_info, BaseAgentComponent
from .actions.post_message import PostMessage
from ...common.time import FIVE_MINUTES

info = copy.deepcopy(agent_info)
info.update(
    {
        "agent_name": "slack",
        "class_name": "SlackAgentComponent",
        "description": "Slack messaging agent for posting messages and files to channels",
        "config_parameters": [
            {
                "name": "slack_bot_token",
                "required": True,
                "description": "Slack bot user OAuth token",
                "type": "string",
            },
            {
                "name": "thread_cache_ttl",
                "required": False,
                "description": f"Time-to-live in seconds for thread correlation cache (default: {FIVE_MINUTES} seconds)",
                "type": "integer",
                "default": FIVE_MINUTES,
            },
        ],
    }
)


class SlackAgentComponent(BaseAgentComponent):
    """Component for handling Slack messaging operations."""

    info = info
    actions = [PostMessage]

    def __init__(self, module_info={}, **kwargs):
        """Initialize the Slack agent component.

        Args:
            module_info: Optional module configuration.
            **kwargs: Additional keyword arguments.

        Raises:
            ValueError: If required Slack configuration is missing.
        """
        super().__init__(module_info, **kwargs)

        # Get Slack configuration
        self.slack_bot_token = self.get_config("slack_bot_token")
        if not self.slack_bot_token:
            raise ValueError("Slack bot token is required")

        # Initialize Slack client
        self.slack_client = WebClient(token=self.slack_bot_token)
