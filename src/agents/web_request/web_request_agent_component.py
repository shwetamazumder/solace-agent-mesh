"""Responsible for processing the actions from the Web Request Agent"""

import copy

from ..base_agent_component import (
    agent_info,
    BaseAgentComponent,
)

from .actions.do_web_request import DoWebRequest
from .actions.download_file import DownloadFile
from .actions.do_image_search import DoImageSearch
from .actions.do_news_search import DoNewsSearch
from .actions.do_suggestion_search import DoSuggestionSearch

info = copy.deepcopy(agent_info)
info["agent_name"] = "web_request"
info["class_name"] = "WebRequestAgentComponent"
info["description"] = (
    "Web request agent that is able to download and retrieve info from urls. ",
    "It can also search the web for news, images and suggestion results with the DuckDuckGo search engine.",
)


class WebRequestAgentComponent(BaseAgentComponent):
    info = info
    actions = [
        DoWebRequest,
        DownloadFile,
        DoImageSearch,
        DoNewsSearch,
        DoSuggestionSearch,
    ]
