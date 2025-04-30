"""The agent component for the PLM slide deck builder that creates slides from Confluence pages"""

import os
import copy
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from solace_agent_mesh.agents.base_agent_component import (
    agent_info,
    BaseAgentComponent,
)

# Slide deck builder action import
from plm_slide_deck_builder.actions.plm_slide_deck_builder import PLMSlideDeckBuilder

info = copy.deepcopy(agent_info)
info["agent_name"] = "plm_slide_deck_builder"
info["class_name"] = "PlmSlideDeckBuilderAgentComponent"
info["description"] = (
    "Creates PowerPoint slides from Confluence pages. "
    "Provide a Confluence URL to generate a complete slide deck."
)
info["detailed_description"] = (
    "The PLM Slide Deck Builder helps product managers create professional "
    "PowerPoint presentations directly from Confluence pages. It uses AI to "
    "analyze the page content and design an appropriate slide structure, "
    "then builds a fully formatted PPTX file ready for use. Simply provide "
    "a Confluence page URL to get started."
)

class PlmSlideDeckBuilderAgentComponent(BaseAgentComponent):
    info = info
    # slide deck builder action
    actions = [PLMSlideDeckBuilder]
