"""This is a custom component that handles registrations from the distributed agents"""

# from solace_ai_connector.common.log import log
from solace_ai_connector.components.component_base import ComponentBase
from solace_ai_connector.common.message import Message
from ...orchestrator.orchestrator_main import OrchestratorState

info = {
    "class_name": "OrchestratorRegister",
    "description": ("This component handles registrations from the distributed agents"),
    "config_parameters": [
        {
            "name": "agent_ttl_ms",
            "required": False,
            "description": "The time-to-live for agent registrations in milliseconds. There must be a registration from an agent within this time period, otherwise the agent will be considered offline.",
            "default": 60000,
        },
    ],
    "input_schema": {
        "type": "object",
        "properties": {
            "agent_name": {
                "type": "string",
                "description": "The name of the agent.",
            },
            "description": {
                "type": "string",
                "description": "A description of the application.",
            },
            "actions": {
                "type": "array",
                "description": "A list of actions the application can perform.",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the action.",
                        },
                        "description": {
                            "type": "string",
                            "description": "A description of what the action does.",
                        },
                        "params": {
                            "type": "array",
                            "description": "A list of parameters for the action.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "The name of the parameter.",
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "A description of the parameter.",
                                    },
                                    "type": {
                                        "type": "string",
                                        "description": "The type of the parameter.",
                                    },
                                },
                                "required": ["name", "description", "type"],
                            },
                        },
                        "examples": {
                            "type": "array",
                            "description": "A list of examples for the action.",
                            "items": {
                                "type": "string",
                                "description": "An example for the action.",
                            },
                        },
                        "required_scopes": {
                            "type": "array",
                            "description": "A list of required scopes for the action.",
                            "items": {
                                "type": "string",
                                "description": "A required scope for the action.",
                            },
                        },
                    },
                    "required": ["name", "description", "params"],
                },
            },
        },
        "required": ["agent_name", "description", "actions"],
    },
}


class OrchestratorRegister(ComponentBase):
    def __init__(self, **kwargs):
        super().__init__(info, **kwargs)
        self.agent_ttl_ms = self.get_config("agent_ttl_ms")
        OrchestratorState.set_config({"agent_ttl_ms": self.agent_ttl_ms})
        with self.get_lock("orchestrator_state"):
            self.orchestrator_state = self.kv_store_get("orchestrator_state")
            if not self.orchestrator_state:
                self.orchestrator_state = OrchestratorState()
                self.kv_store_set("orchestrator_state", self.orchestrator_state)

    def invoke(self, message: Message, data):
        """Receive a registration from an agent and store it in the component's state."""
        # log.info("Received registration from agent")
        self.orchestrator_state.register_agent(data)
        return data
