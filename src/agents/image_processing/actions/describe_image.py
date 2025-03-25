"""Image Description action"""

from solace_ai_connector.common.log import log
import re
import random
import requests
from io import BytesIO


from ....common.action import Action
from ....common.action_response import ActionResponse
from ....services.file_service import FS_PROTOCOL, FileService
from ....services.file_service.file_utils import starts_with_fs_url


class DescribeImage(Action):

    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "describe_image",
                "prompt_directive": "Describe an image",
                "params": [
                    {
                        "name": "image_url",
                        "desc": f'The "{FS_PROTOCOL}://" or "https://" url of the image to describe',
                        "type": "string",
                    }
                ],
                "required_scopes": ["image_processing:describe_image:create"],
            },
            **kwargs,
        )

    def extract_url_from_text(self, text: str) -> str:
        """
        Extracts the first URL from a given text.
        """
        url = None
        # URL Regex pattern
        # Starts with https:// or http:// or FS_PROTOCOL://
        # ends with space or newline or end of string
        url_pattern = r"(https?|{}):\/\/\S+".format(FS_PROTOCOL)
        match = re.search(url_pattern, text)
        if match:
            url = match.group()
        return url

    def download_image(self, image_url: str, session_id: str) -> str:
        """
        Download the image using the provided image URL.
        """
        url = image_url
        if not starts_with_fs_url(url):
            # Download the image and upload to the file service
            file_service = FileService()
            byte_buffer = BytesIO(requests.get(image_url).content)
            metadata = file_service.upload_from_buffer(
                byte_buffer.read(),
                str(random.randint(100000, 999999)) + "_image.png",
                session_id,
                data_source="Image Processing Agent - Describe Image Action",
            )
            url = metadata.get("url")

        base64_image_url = f"{url}?encoding=datauri&resolve=true"
        return base64_image_url

    def get_image_description(self, base64_image_url: str) -> str:
        """
        Get the description of the image using the provided image URL.
        """
        agent = self.get_agent()
        content = agent.do_llm_service_request(
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "describe the content of this image in detail",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": base64_image_url},
                        },
                    ],
                }
            ],
            resolve_files=True,
        ).get("content")

        return content

    def invoke(self, params, meta={}) -> ActionResponse:
        log.debug("Describing image: %s", params.get("image_url"))
        # Extract the URL from the text
        url = self.extract_url_from_text(params.get("image_url", ""))
        if not url:
            return ActionResponse(message="No image URL found in the query.")

        try:
            # Download the image
            image_url = self.download_image(url, meta.get("session_id"))
        except Exception as e:
            log.error("Failed to download image from the url %s: %s", url, str(e))
            return ActionResponse(message=f"Failed to download the image from the URL: {url}")

        try:
            # Get the image description
            description = self.get_image_description(image_url)
            return ActionResponse(message=description)
        except Exception as e:
            log.error("Failed to describe image in %s: %s", url, str(e))
            return ActionResponse(message=f"Failed to describe the image in {url}.")
