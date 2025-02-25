"""Web Search action"""

from solace_ai_connector.common.log import log
import requests
from duckduckgo_search import DDGS


from ....common.action import Action
from ....common.action_response import ActionResponse
from ....services.file_service import FileService


class DoImageSearch(Action):
    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "do_image_search",
                "prompt_directive": "Search the web for images using a search engine.",
                "params": [
                    {
                        "name": "query",
                        "desc": "The search query to use",
                        "type": "string",
                    },
                    {
                        "name": "max_results",
                        "desc": "Maximum number of results to show, defaults to 3 if not present",
                        "type": "int",
                    },
                    {
                        "name": "size",
                        "desc": (
                            "Size of the image to search for. ",
                            "Can be one of: small, medium, large, wallpaper or None. Defaults to None if not present",
                        ),
                        "type": "string",
                    },
                ],
                "required_scopes": ["web_request:do_image_search:read"],
            },
            **kwargs,
        )

    def image_search(self, keyword, size, max_results) -> list:
        """
        Returns a list of dictionaries that represent image results
        """
        return DDGS().images(
            keywords=keyword,
            region="wt-wt",
            safesearch="off",
            size=str(size) or None,
            color=None,
            type_image=None,
            layout=None,
            license_image=None,
            max_results=int(max_results),
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        query = params.get("query")
        max_results = params.get("max_results", 3)
        size = params.get("size")
        results = []
        if not query:
            return ActionResponse(message="ERROR: Query not found!")
        results = self.image_search(query, size, max_results)  # append text results to results
        file_service = FileService()
        image_metas = []
        for result in results:
            try:
                received_image = requests.get(result.get("image"), timeout=10).content
                log.debug(f"Received image: {result.get('image')}")
                image_metas.append(
                    file_service.upload_from_buffer(
                        received_image,
                        result.get("title"),
                        meta.get("session_id"),
                        data_source="Web Request Agent - Image Search Action",
                    )
                )
            except Exception as e:
                log.error(f"Failed to download image: {result.get('image')} because {e}")
        return ActionResponse(files=image_metas)
