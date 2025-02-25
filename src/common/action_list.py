from .action import Action


class ActionList:

    def __init__(self, actions_classes, **kwargs):
        self.actions: Action = []
        self.actions_map = {}
        for action_class in actions_classes:
            action = action_class(**kwargs)
            self.actions.append(action)
            self.actions_map[action.name] = action

    def add_action(self, action):
        self.actions.append(action)
        self.actions_map[action.name] = action

    def set_agent(self, agent):
        for action in self.actions:
            action.set_agent(agent)

    def fix_scopes(self, search_value, replace_value):
        for action in self.actions:
            action.fix_scopes(search_value, replace_value)

    def set_config_fn(self, config_fn):
        for action in self.actions:
            action.set_config_fn(config_fn)

    def get_prompt_summary(self, prefix="") -> dict:
        summary = []
        for action in self.actions:
            summary.append(action.get_prompt_summary(prefix))
        return summary

    def get_action(self, name):
        return self.actions_map.get(name)
