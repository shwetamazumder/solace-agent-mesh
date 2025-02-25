"""This is the base class that provides LLM and Embedding service access"""

from abc import ABC , abstractmethod
from solace_ai_connector.components.component_base import ComponentBase
from solace_ai_connector.common.message import Message
from solace_ai_connector.common.utils import ensure_slash_on_end



agent_info = {
    "class_name": "LLMServiceComponentBase",
    "description": "This is the base class that provides LLM and Embedding service access",
    "config_parameters": [
        {
            "name": "llm_service_topic",
            "required": False,
            "description": "The topic to use for the LLM service",
        },
        {
            "name": "embedding_service_topic",
            "required": False,
            "description": "The topic to use for the Embedding service",
        },
    ]
}


class LLMServiceComponentBase(ComponentBase, ABC):

    def __init__(self, module_info={}, **kwargs):
        super().__init__(module_info, **kwargs)
        self.current_message = None
        self.current_request_data = None

        self.llm_service_topic = self.get_config("llm_service_topic")
        if self.llm_service_topic:
            self.llm_service_topic = ensure_slash_on_end(self.llm_service_topic)
            # Check that the component's broker request/response is enabled
            if not self.is_broker_request_response_enabled():
                raise ValueError(
                    "LLM service topic is set, but the component does not "
                    f"have its broker request/response enabled, {self.__class__.__name__}"
                )

        self.embedding_service_topic = self.get_config("embedding_service_topic")
        if self.embedding_service_topic:
            self.embedding_service_topic = ensure_slash_on_end(
                self.embedding_service_topic
            )
            # Check that the component's broker request/response is enabled
            if not self.is_broker_request_response_enabled():
                raise ValueError(
                    "Embedding service topic is set, but the component does not "
                    f"have its broker request/response enabled, {self.__class__.__name__}"
                )
            
    def process_pre_invoke(self, message):
        self.current_request_data = super().process_pre_invoke(message)
        return self.current_request_data

    def process_post_invoke(self, result, message):
        super().process_post_invoke(result, message)
        self.current_request_data = None

    @abstractmethod
    def invoke(self, message, data):
        pass

    def do_llm_service_request_stream(self, message):
        for response_message, last_message in self.do_broker_request_response(
            message,
            stream=True,
            streaming_complete_expression="input.payload:last_chunk",
        ):
            yield response_message.get_payload(), last_message
        return

    def do_llm_service_request(self, messages, stream=False, resolve_files=False):
        """Send a message to the LLM service"""
        if not self.llm_service_topic:
            raise ValueError(f"LLM service topic not set on {self.__class__.__name__}")

        user_properties = self.current_message.get_user_properties().copy()

        # Add the topic suffix
        stimulus_uuid = user_properties.get("stimulus_uuid", "x")
        session_id = user_properties.get("session_id", "x")
        originator_id = user_properties.get("originator_id", "x")

        topic = f"{self.llm_service_topic}{stimulus_uuid}/{session_id}/{originator_id}"
        user_properties["resolve_files"] = resolve_files

        if self.current_request_data:
            action_list_id = self.current_request_data.get("action_list_id")
            action_idx = self.current_request_data.get("action_idx")
            action_name = self.current_request_data.get("action_name")

            source_info = {
                "type": "agent",
                "agent_name": self.info.get("agent_name"),
                "action_list_id": action_list_id,
                "action_idx": action_idx,
                "action_name": action_name,
            }
        else:
            source_info = {
                "type": "agent",
                "agent_name": self.info.get("agent_name"),
            }

        user_properties["llm_request_source_info"] = source_info

        message = Message(
            topic=topic,
            payload={"messages": messages, "stream": stream},
            user_properties=user_properties,
        )

        if stream:
            return self.do_llm_service_request_stream(message)
        else:
            return self.do_broker_request_response(message).get_payload()

    def do_embedding_service_request(self, items, resolve_files=False):
        """Send a message to the Embedding service"""
        if not self.embedding_service_topic:
            raise ValueError(
                f"Embedding service topic not set on {self.__class__.__name__}"
            )

        user_properties = self.current_message.get_user_properties().copy()

        # Add the topic suffix
        stimulus_uuid = user_properties.get("stimulus_uuid", "x")
        session_id = user_properties.get("session_id", "x")
        originator_id = user_properties.get("originator_id", "x")

        topic = f"{self.embedding_service_topic}{stimulus_uuid}/{session_id}/{originator_id}"
        user_properties["resolve_files"] = resolve_files

        message = Message(
            topic=topic,
            payload={
                "items": items,
            },
            user_properties=user_properties,
        )

        return (
            self.do_broker_request_response(message).get_payload().get("embeddings", [])
        )

