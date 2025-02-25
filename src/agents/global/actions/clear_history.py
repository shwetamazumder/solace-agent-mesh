"""Clear history action"""

from solace_ai_connector.common.log import log
from ....common.action import Action
from ....common.action_response import ActionResponse


class ClearHistory(Action):
    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "clear_history",
                "prompt_directive": "Clear the chat history",
                "params": [
                    {
                        "name": "depth_to_keep",
                        "desc": "The number of messages to keep in the chat history. If 0, clear all history. ",
                        "type": "integer",
                    }
                ],
                "required_scopes": ["*:*:*"],
            },
            **kwargs,
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        log.debug("Clearing chat history")
        depth_to_keep = params.get("depth_to_keep", 0)
        return ActionResponse(
            clear_history=True,
            history_depth_to_keep=depth_to_keep,
        )
