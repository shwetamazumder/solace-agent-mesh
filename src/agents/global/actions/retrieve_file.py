"""Retrieve File content action"""

from solace_ai_connector.common.log import log
import re
import json

from ....common.action import Action
from ....common.action_response import ActionResponse, InlineFile
from ....services.file_service import FS_PROTOCOL, FS_URL_REGEX, FileService


class RetrieveFile(Action):
    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "retrieve_file",
                "prompt_directive": f"Retrieve the content of a text based file form a {FS_PROTOCOL} URL",
                "params": [
                    {
                        "name": "url",
                        "desc": f'The "{FS_PROTOCOL}://" url of the file (Optionally with query parameters - Without "resolve" parameter)',
                        "type": "string",
                    }
                ],
                "required_scopes": ["global:retrieve_file:read"],
            },
            **kwargs,
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        # Extract the URL from the text
        url = params.get("url")
        # validate the URL
        if not url or not re.match(FS_URL_REGEX, url):
            return ActionResponse(message=f"Invalid {FS_PROTOCOL} URL provided.")

        try:
            # Download the file
            file_service = FileService()
            file, _, file_meta = file_service.resolve_url(url, meta.get("session_id"), return_extra=True)
            file = file.decode("utf-8", errors="ignore") if type(file) == bytes else file
        except Exception as e:
            log.error("Failed to download file from the url %s: %s", url, str(e))
            return ActionResponse(message=f"Failed to download the file from the URL: {url}")

        max_allowed_size = self.get_config("max_allowed_file_retrieve_size", None)
        if max_allowed_size and len(file) > max_allowed_size:
            return ActionResponse(message=f"Error: File too large. File size exceeds the maximum allowed size of {max_allowed_size} bytes.")

        inline_file = InlineFile(content=file, name=file_meta.get("name", "unknown.txt"))
        return ActionResponse(message=f"Returning content of the file {url}.", inline_files=[inline_file])
