from abc import ABC, abstractmethod

from .action_response import ActionResponse


class Action(ABC):

    def __init__(self, attributes, agent=None, config_fn=None, **kwargs):
        self.validate_attributes(attributes)
        self.long_description = attributes.get(
            "long_description", attributes.get("prompt_directive", "<unspecified>")
        )
        self._prompt_directive = attributes.get("prompt_directive")
        self._name = attributes.get("name")
        self._params = attributes.get("params")
        self._disabled = attributes.get("disabled", False)
        self._examples = attributes.get("examples", [])
        self._required_scopes = attributes.get("required_scopes", [])
        self._config_fn = config_fn
        self.agent = agent
        self.kwargs = kwargs

    @property
    def name(self):
        return self._name

    @property
    def disabled(self):
        return self._disabled

    @property
    def examples(self):
        return self._examples

    @property
    def required_scopes(self):
        return self._required_scopes

    def set_agent(self, agent):
        self.agent = agent

    def fix_scopes(self, search_value, replace_value):
        self._required_scopes = [
            scope.replace(search_value, replace_value)
            for scope in self._required_scopes
        ]

    def get_agent(self):
        return self.agent

    def set_config_fn(self, config_fn):
        self._config_fn = config_fn

    def get_config(self, key=None, default=None):
        if self._config_fn:
            return self._config_fn(key, default)
        return default

    def get_prompt_summary(self, prefix="") -> dict:
        if self.disabled:
            return None
        summary = {}
        action_name = self._name
        summary[action_name] = {
            "desc": self._prompt_directive,
            "params": [f"{param['name']} ({param['desc']})" for param in self._params],
            "examples": self._examples,
            "required_scopes": self._required_scopes,
        }
        return summary

    def validate_attributes(self, attributes):
        if not attributes.get("name"):
            raise ValueError("Actions must have a name")
        if not attributes.get("prompt_directive"):
            raise ValueError("Actions must have a prompt_directive")
        if attributes.get("params"):
            params = attributes.get("params")
            for param in params:
                if not param.get("name"):
                    raise ValueError(
                        "Action attributes params must have a descriptive name"
                    )
                if not param.get("desc"):
                    raise ValueError("Action attributes params must have a description")
                if not param.get("type"):
                    raise ValueError("Action attributes params must have a type")

    @abstractmethod
    def invoke(self, params, meta={}) -> ActionResponse:
        raise NotImplementedError("Invoke method must be implemented in subclass")
