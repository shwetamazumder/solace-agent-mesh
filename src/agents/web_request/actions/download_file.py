"""File Request action"""

from solace_ai_connector.common.log import log
import requests
from io import BytesIO


from ....common.action import Action
from ....common.action_response import ActionResponse
from ....services.file_service import FileService, FS_PROTOCOL


class DownloadFile(Action):

    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "download_external_file",
                "prompt_directive": f"Given a http/https external URL of a file (image, video, etc.), fetch the content from the URL and add the file to the {FS_PROTOCOL} file service so it can be used in the system.",
                "params": [
                    {
                        "name": "url",
                        "desc": "URL of file",
                        "type": "string",
                    },
                    {
                        "name": "local_file_name",
                        "desc": "Local file name to use for the file - make sure it has the correct extension",
                        "type": "string",
                    },
                ],
                "required_scopes": ["web_request:download_file:write"],
            },
            **kwargs,
        )

    def invoke(self, params, meta={}) -> ActionResponse:
        url = params.get("url")
        local_file_name = params.get("local_file_name")

        if not url:
            return ActionResponse(message="URL is required")

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"}

        # Fetch the file from the URL and write it in chunks
        files = []
        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as file_response:
                file_response.raise_for_status()
                byte_io = BytesIO()
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive new chunks
                        byte_io.write(chunk)
                byte_io.seek(0)
                file_service = FileService()
                meta = file_service.upload_from_buffer(
                    byte_io.read(),
                    local_file_name,
                    meta.get("session_id"),
                    data_source="Web Request Agent - Download File Action",
                )
                files.append(meta)
        except requests.exceptions.HTTPError as e:
            return ActionResponse(message=f"Failed to fetch file from URL: {e}")
        except Exception as e:
            return ActionResponse(message=f"An error occurred: {e}")

        return ActionResponse(files=files)
