"""Web Search action"""

from duckduckgo_search import DDGS


from ....common.action import Action
from ....common.action_response import ActionResponse


class DoNewsSearch(Action):
    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "do_news_search",
                "prompt_directive": "Search the web for news and current events using a search engine.",
                "params": [
                    {
                        "name": "query",
                        "desc": "The search query to use",
                        "type": "string",
                    },
                    {
                        "name": "max_results",
                        "desc": "Maximum number of results to show, defaults to 5 if not present",
                        "type": "int",
                    },
                ],
                "required_scopes": ["web_request:do_news_search:read"],
            },
            **kwargs,
        )

    def news_search(self, keyword, max_results) -> list:
        """
        Returns a list of dictionaries that represent news results
        """
        return DDGS().news(keywords=keyword, region="wt-wt", max_results=int(max_results))

    def invoke(self, params, meta={}) -> ActionResponse:
        query = params.get("query")
        max_results = params.get("max_results", 5)
        results = []
        if not query:
            return ActionResponse(message="ERROR: Query not found!")
        results = self.news_search(query, max_results)  # append text results to results

        return ActionResponse(message=results)
