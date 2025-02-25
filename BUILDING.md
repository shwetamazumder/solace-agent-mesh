# Solace Agent Mesh Repository Building Instructions

Solace Agent Mesh repository is accessible as both a CLI and a Python Module.

The cli, `solace_agent_mesh`, allows for adding new components and building the repository.
This repository cannot be executed without instantiation and building.

To access the solace-agent-mesh components in a new application, import the components using the relative file path to `src`, but instead of `src` use `solace_agent_mesh`. For example: 

```python
from solace_agent_mesh.agents.base_agent_component import (
    BaseAgentComponent
)
```

In the packaged artifacts, the following directories are included
- cli
- config
- templates
- web-visualizer/dist/* (added under /assets/web-visualizer)
- src/* (Spread, sub-directories are accessible through root )

> **NOTE:** If a directory inside the `src` directory has the same name as one of the other included directories, the contents will get merged.

The inclusion settings can be found in the section `[tool.hatch.build.targets.wheel.force-include]` at the [`pyproject.toml`](./pyproject.toml) file.

Anything outside the mentioned directories, will be ignored in the produced artifact.

> **NOTE:** The JavaScript web-based visualizer is included in the artifact, and it is built before the python packaging process. If using the Makefile commands, this process automatically happens before the packaging.


# CLI Build Command Instructions

To build the CLI, run the following command:

```bash
solace_agent_mesh build
```

During the build, a new build directory is created with the 2 following subdirectories:
- `configs`: Includes all the configuration files required to run solace-ai-connector (This contains both the user defined components and solace agent mesh components)
- `modules`: Includes all the python modules required for the user defined components

All the config files in `solace_agent_mesh` must use public module path for all python references:
For example instead of `src.agents` use `solace_agent_mesh.agents`

During the build phase, any literal placeholders in the configuration files will be replaced with the actual values. (Values that are inside the `{{` and `}}`)

List of the **built-in agents** to be included in the configuration is first filtered by the solace agent mesh config file, then the user defined config file. (With precedence to the user defined config file)

The default configuration can be found under `solace_agent_mesh.built_in.agents` in [solace-agent-mesh-default.yaml](./templates/solace-agent-mesh-default.yaml)

> **NOTE:** Any built-in agent that is not included in the list of agents in the configuration file will be ignored.

User defined **gateways** only include some parts of the shared config, the rest of the configuration is handled by the template at [templates/gateway-wrapper.yaml](./templates/gateway-wrapper.yaml). During the build phase, the template is populated with the user defined gateway configuration for each user defined gateway.

**Other config file**: solace agent mesh has a lot of other important configuration file such as the orchestrator. All the config file inside the [configs](./configs/) directory will be included in the build **unless** the file is prefixed with one of the following:
- "_"
- "agent" (agents are handled separately through the built-in agents logic)
- "gateway"

This list can be updated inside the function `build_solace_agent_mesh` at [cli/commands/build.py](./cli/commands/build.py)
During this process, all the relative `src.*` paths will get converted to `solace-agent-mesh.*` path.


