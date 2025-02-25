"""Action to handle errors from the system"""

from solace_ai_connector.common.log import log

from ....common.action import Action
from ....common.action_response import (
    ActionResponse,
    ErrorInfo,
    WithContextQuery,
)


class ErrorAction(Action):
    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "error_action",
                "prompt_directive": "Raise an error message",
                "params": [
                    {
                        "name": "error_message",
                        "desc": "The error to send to the user",
                        "type": "string",
                    }
                ],
                "required_scopes": ["*:*:*"],
            },
            **kwargs,
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        error_message = params.get("error_message")
        if error_message:
            log.error("Raising error: %s", error_message)
            # If the error_message contains "Failed to parse response",
            # then return a response requesting a redo from the LLM
            if "Failed to parse response" in error_message:
                return ActionResponse(
                    context_query=WithContextQuery(
                        context_type="statement",
                        context="Your response was not correctly formated and parsing failed. Please try again but don't comment on the parsing problem in your response.",
                        query="",
                    )
                )
            return ActionResponse(error_info=ErrorInfo(error_message=error_message))
