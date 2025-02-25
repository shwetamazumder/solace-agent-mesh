import os
import sys
import queue
import threading

from solace_ai_connector.common.log import log
from solace_ai_connector.common.message import Message

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from {{SNAKE_CASE_NAME}}.{{SNAKE_CASE_NAME}}_base import {{CAMEL_CASE_NAME}}Base


info = {
    "class_name": "{{CAMEL_CASE_NAME}}Input",
    "description": (
        "Description of your gateway input."
    ),
    "config_parameters": [],
    "output_schema": {
        "type": "object",
        "properties": {
            "event": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                    },
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                },
                                "content": {
                                    "type": "string",
                                },
                                "size": {
                                    "type": "number",
                                },
                            },
                        },
                    },
                },
            },
        },
        "required": ["event"],
    },
}


class {{CAMEL_CASE_NAME}}Input({{CAMEL_CASE_NAME}}Base):
    def __init__(self, **kwargs):
        super().__init__(info, **kwargs)
        log.debug("{{CAMEL_CASE_NAME}}Input initialized")

        self.message_queue = queue.Queue()

        self.{{SNAKE_CASE_NAME}}_thread = threading.Thread(target=self.start_{{SNAKE_CASE_NAME}}, args=(self.message_queue))
        self.{{SNAKE_CASE_NAME}}_thread.daemon = True
        self.{{SNAKE_CASE_NAME}}_thread.start()

    def stop_component(self):
        log.debug("Stopping {{CAMEL_CASE_NAME}}Input component")
        if self.{{SNAKE_CASE_NAME}}_thread:
            self.{{SNAKE_CASE_NAME}}_thread.join()
    
    def start_{{SNAKE_CASE_NAME}}(self, message_queue):
        # This is a placeholder for the actual implementation
        payload = {
            "text": "Hello, World!",
            "files": [
                {
                    "name": "file.txt",
                    "content": "base64 encoded content",
                    "size": 10,
                }
            ]
        }
        user_properties = {
            "session_id": "session_id",
            "identity": "test@email.com"
        }
        message = Message(payload=payload, user_properties=user_properties)
        message.set_previous(payload)
        message_queue.put(message)

    def get_next_message(self):
        """Get the next message from the queue.
        """
        return self.message_queue.get()

    def invoke(self, message:Message, data:dict):
        log.debug("{{CAMEL_CASE_NAME}}Output invoked, %s", data)
        return data
