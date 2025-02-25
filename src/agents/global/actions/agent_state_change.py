"""Agent state change action"""

from solace_ai_connector.common.log import log
from ....common.action import Action
from ....common.action_response import (
    ActionResponse,
    AgentStateChange,
    ErrorInfo,
)


class AgentStateChangeAction(Action):

    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "change_agent_status",
                "prompt_directive": "Handle agent state change",
                "params": [
                    {
                        "name": "agent_name",
                        "desc": "Name of the agent",
                        "type": "string",
                    },
                    {
                        "name": "new_state",
                        "desc": "New state of the agent: open or closed",
                        "type": "string",
                    },
                ],
                "required_scopes": ["*:*:*"],
            },
            **kwargs,
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        agent_name = params["agent_name"]
        new_state = params["new_state"]
        log.debug("Handling agent state change: %s -> %s", agent_name, new_state)

        if new_state == "open":
            return ActionResponse(
                message=f"_Opening agent {agent_name}..._",
                agent_state_change=AgentStateChange(agent_name, "open"),
            )
        elif new_state == "closed":
            return ActionResponse(
                agent_state_change=AgentStateChange(agent_name, "closed"),
            )
        else:
            log.error("Invalid agent state: %s", new_state)
            return ActionResponse(
                error_info=ErrorInfo(error_message=f"Invalid agent state for {agent_name}: {new_state}"),
            )
