"""The agent component for the global actions"""

import copy

from ..base_agent_component import (
    agent_info,
    BaseAgentComponent,
)

from .actions.agent_state_change import AgentStateChangeAction
from .actions.clear_history import ClearHistory
from .actions.error_action import ErrorAction
from .actions.plantuml_diagram import PlantUmlDiagram
from .actions.plotly_graph import PlotlyGraph
from .actions.retrieve_file import RetrieveFile
from .actions.create_file import CreateFile
from .actions.convert_file_to_markdown import ConvertFileToMarkdown


info = copy.deepcopy(agent_info)
info["agent_name"] = "global"
info["class_name"] = "GlobalAgentComponent"
info["description"] = "Global agent."
info["always_open"] = True


class GlobalAgentComponent(BaseAgentComponent):
    info = info
    actions = [
        AgentStateChangeAction,
        ClearHistory,
        ErrorAction,
        PlantUmlDiagram,
        PlotlyGraph,
        RetrieveFile,
        CreateFile,
        ConvertFileToMarkdown
    ]
