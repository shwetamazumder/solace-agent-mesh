import os
import sys

from solace_ai_connector.common.log import log
from solace_ai_connector.common.message import Message

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from {{SNAKE_CASE_NAME}}.{{SNAKE_CASE_NAME}}_base import {{CAMEL_CASE_NAME}}Base

info = {
    "class_name": "{{CAMEL_CASE_NAME}}Output",
    "description": (
        "Description of your gateway output."
    ),
    "config_parameters": [],
    "input_schema": {
        "type": "object",
        "properties": {
            "message_info": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                    },
                },
                "required": ["session_id"],
            },
            "content": {
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
                                "mime_type": {
                                    "type": "string",
                                },
                            },
                        },
                    },
                },
            },
        },
        "required": ["message_info", "content"],
    },
}


class {{CAMEL_CASE_NAME}}Output({{CAMEL_CASE_NAME}}Base):
    def __init__(self, **kwargs):
        super().__init__(info, **kwargs)
        log.debug("{{CAMEL_CASE_NAME}}Output initialized")

    def stop_component(self):
        log.debug("Stopping {{CAMEL_CASE_NAME}}Output Component")

    def invoke(self, message:Message, data:dict):
        log.debug("{{CAMEL_CASE_NAME}}Output invoked, %s", data)

