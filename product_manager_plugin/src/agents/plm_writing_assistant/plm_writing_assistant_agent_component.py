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
    "This agent helps product managers generate blog posts from Confluence pages. "
    "It fetches content directly from Confluence and summarizes it into "
    "well-structured marketing content."
)
info["detailed_description"] = (
    "The PLM Writing Assistant can help you create professional blog posts "
    "by pulling information directly from Confluence pages. Simply provide "
    "a Confluence page URL, and it will fetch the content and generate a "
    "well-structured blog post tailored for product marketing purposes."
)

class PlmWritingAssistantAgentComponent(BaseAgentComponent):
    info = info
    """Agent component for the plm writing assistant"""
    actions = [PlmWritingAssistant]
