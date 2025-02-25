"""Reponsible for doing some formatting of the conversation"""

from solace_ai_connector.components.component_base import ComponentBase

info = {
    "class_name": "ConversationFormatter",
    "description": "Reponsible for doing some formatting of the conversation",
    "config_parameters": [],
    "input_schema": {
        "type": "object",
        "properties": {
            "payload": {
                "type": "object",
            },
            "topic": {
                "type": "string",
            },
            "user_properties": {
                "type": "object",
            },
        },
        "required": ["payload", "topic", "user_properties"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
            },
        },
    },
}


class ConversationFormatter(ComponentBase):

    def __init__(self, **kwargs):
        super().__init__(info, **kwargs)

    def invoke(self, message, data):
        payload = data.get("payload")
        topic = data.get("topic")
        user_properties = data.get("user_properties")
        output_message = None
        if "/stimulus/gateway/" in topic:
            # If the message is a stimulus, format the message to include the user's name
            identity = user_properties.get("identity")
            stimulus = payload.get("text")

            if "/reinvoke" in topic:
                output_message = f"   Reinvoke the orchestrator with: \n{self.prefix_each_line(stimulus, '    ')}\n"
            else:
                output_message = f"\nNew request from {identity}:\n{self.prefix_each_line(stimulus, '    ')}\n"

        if "/response/gateway/" in topic or "/streamingResponse/gateway/" in topic:
            # If the payload contains last_chunk and it is not True, then skip this message
            if not isinstance(payload, dict):
                print("Payload is not a dictionary")
                return {"message": None}
            if payload.get("last_chunk") is not True:
                output_message = None
            else:
                # If the message is a response, format the message to include the response
                response = payload.get("text")
                output_message = (
                    f"  Response:\n{self.prefix_each_line(response, '      ')}\n"
                )

        if "/responseComplete/gateway/" in topic:
            # If the message is a response complete, format the message to include the completion message
            output_message = "  Response complete\n"

        if "/actionRequest/" in topic:
            # If the message is an action request, format the message to include the action name
            action_name = payload.get("action_name")
            action_params = payload.get("action_params", {})

            output_message = f"  Action request: {action_name}\n"
            # action params have the param name as the key and the value as the value
            for param_name, param_value in action_params.items():
                output_message += f"    {param_name}: {self.prefix_each_line(param_value, '      ')}\n"

        if "/actionResponse/" in topic:
            # Get the two topic levels after .../agent/ to determine the agent name
            after = topic.split("/agent/")[1]
            topic_levels = after.split("/")
            agent_name = topic_levels[0]
            action_name = topic_levels[1]

            output_message = f"  Action response: {agent_name}.{action_name}\n"

            for param, value in payload.items():
                output_message += (
                    f"    {param}: {self.prefix_each_line(value, '     ')}\n"
                )

        if output_message is None:
            return {"message": None}

        # Truncate the message if it is too long
        if len(output_message) > 2000:
            output_message = output_message[:2000] + "..."

        # output_message += "\n"

        return {"message": output_message}

    def prefix_each_line(self, text, prefix):
        if not isinstance(text, str):
            return text
        return "\n".join([f"{prefix}{line}" for line in text.split("\n")])
