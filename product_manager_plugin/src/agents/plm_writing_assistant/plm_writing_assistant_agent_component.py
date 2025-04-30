"""The agent component for the plm writing assistant"""

import os
import copy
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from solace_agent_mesh.agents.base_agent_component import (
    agent_info,
    BaseAgentComponent,
)

# plm_writing_assistant imports
from product_manager_plugin.src.agents.plm_writing_assistant.actions.plm_writing_assistant import PlmWritingAssistant


info = copy.deepcopy(agent_info)
info["agent_name"] = "plm_writing_assistant"
info["class_name"] = "PlmWritingAssistantAgentComponent"
info["description"] = (
    "This agent helps product managers generate content from Confluence pages. "
    "It fetches content directly from Confluence and transforms it into "
    "well-structured marketing content or presentation slides."
)
info["detailed_description"] = (
    "The PLM Writing Assistant can help you create professional content "
    "by pulling information directly from Confluence pages. Simply provide "
    "a Confluence page URL, and it will fetch the content and generate either:\n\n"
    "1. A well-structured blog post tailored for product marketing purposes\n"
    "2. Presentation slide content ready for use in PowerPoint or other presentation tools\n\n"
    "Specify the 'output_type' parameter as either 'blog_post' or 'slide_content' to choose the format."
)

class PlmWritingAssistantAgentComponent(BaseAgentComponent):
    info = info
    """Agent component for the plm writing assistant"""
    actions = [PlmWritingAssistant]
