"""The agent component for the plm slide deck builder"""

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
    "This agent handles creation of presentation slide decks from Confluence pages. It should be used "
    "when a user explicitly requests to create or generate a presentation from Confluence content."
)

class PlmSlideDeckBuilderAgentComponent(BaseAgentComponent):
    info = info
    # slide deck builder action
    actions = [PLMSlideDeckBuilder]
