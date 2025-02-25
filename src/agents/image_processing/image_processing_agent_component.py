"""Responsible for processing the actions from the Image Processing Agent"""

import copy

from ..base_agent_component import (
    agent_info,
    BaseAgentComponent,
)

from .actions.create_image import ImageCreation
from .actions.describe_image import DescribeImage

info = copy.deepcopy(agent_info)
info["agent_name"] = "image_processing"
info["class_name"] = "ImageProcessingAgentComponent"
info["description"] = "Image Processing agent. This can generate images from text or describe images to text"


class ImageProcessingAgentComponent(
    BaseAgentComponent
):
    info = info
    actions = [ImageCreation, DescribeImage]
