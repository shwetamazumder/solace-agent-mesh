"""The agent component for the {{SPACED_NAME}}"""

import os
import copy
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from solace_agent_mesh.agents.base_agent_component import (
    agent_info,
    BaseAgentComponent,
)

# Sample action import
from {{SNAKE_CASE_NAME}}.actions.sample_action import SampleAction

info = copy.deepcopy(agent_info)
info["agent_name"] = "{{SNAKE_CASE_NAME}}"
info["class_name"] = "{{CAMEL_CASE_NAME}}AgentComponent"
info["description"] = (
    "This agent handles ... It should be used "
    "when an user explicitly requests information ... "
)

class {{CAMEL_CASE_NAME}}AgentComponent(BaseAgentComponent):
    info = info
    # sample action
    actions = [SampleAction]
