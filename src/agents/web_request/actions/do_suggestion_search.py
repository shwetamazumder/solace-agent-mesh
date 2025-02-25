"""Web Request action"""

from duckduckgo_search import DDGS

from ....common.action import Action
from ....common.action_response import ActionResponse


class DoSuggestionSearch(Action):

    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "do_suggestion_search",
                "prompt_directive": "Browse the web and get suggestions for the search query especially on new or unfamiliar topics.",
                "params": [
                    {
                        "name": "query",
                        "desc": "The search query to use",
                        "type": "string",
                    }
                ],
                "required_scopes": ["web_request:do_suggestion_search:read"],
            },
            **kwargs,
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        query = params.get("query")
        if not query:
            return ActionResponse(message="ERROR: Query not found!")
        content = DDGS().suggestions(query)

        return ActionResponse(message=content)
