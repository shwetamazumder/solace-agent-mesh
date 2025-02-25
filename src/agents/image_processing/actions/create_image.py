"""Image Creation action"""

from solace_ai_connector.common.log import log
import random
import requests
import base64

from litellm import image_generation

from ....common.action import Action
from ....common.action_response import ActionResponse
from ....services.file_service import FileService


class ImageCreation(Action):

    def __init__(self, **kwargs):
        super().__init__(
            {
                "name": "create_image",
                "prompt_directive": "Create an image",
                "params": [
                    {
                        "name": "image_description",
                        "desc": "The prompt to use to create the image",
                        "type": "string",
                    }
                ],
                "required_scopes": ["image_processing:create_image:create"],
            },
            **kwargs,
        )

    def _get_image_content(self, image_data):
        """Helper function to extract image content from response data"""
        if 'url' in image_data and image_data['url'] is not None:
            return requests.get(image_data['url'], timeout=10).content
        elif 'b64_json' in image_data and image_data['b64_json'] is not None:
            return base64.b64decode(image_data['b64_json'])
        else:
            raise ValueError("No valid image data found in response")

    def invoke(self, params, meta={}) -> ActionResponse:
        prompt = params.get("image_description")
        if not prompt:
            return ActionResponse(message="Image description is required")
        try:
            response = image_generation(
                model=self.get_config("image_gen_model") or None,
                api_base=self.get_config("image_gen_endpoint") or None,
                api_key=self.get_config("image_gen_api_key") or None,
                prompt=prompt,
                n=1,
                **self.get_config("image_gen_litellm_config", {}),
            )
        except Exception as e:
            log.error(f"Error generating image:", e)
            return ActionResponse(message=f"Error generating image, {str(e)}")

        try:
            generated_image = self._get_image_content(response.get("data")[0])
        except Exception as e:
            log.error(f"Error retrieving image content:", e)
            return ActionResponse(message=f"Error retrieving image content: {str(e)}")

        file_service = FileService()
        image_name = "generated_image_" + str(random.randint(100000, 999999)) + ".png"
        image_meta = file_service.upload_from_buffer(
            generated_image,
            image_name,
            meta.get("session_id"),
            data_source="Image Processing Agent - Image Creation Action",
        )

        return ActionResponse(files=[image_meta])
