from typing import Dict, Any

from solace_ai_connector.components.component_base import ComponentBase
from solace_ai_connector.common.message import Message


from ...services.file_service import FileService, FS_PROTOCOL
from ...services.file_service.file_utils import recursive_file_resolver

info = {
    "class_name": "FileResolverComponent",
    "description": (
        f"This component resolves all the {FS_PROTOCOL} URLs in the input data. "
        "And returns the object with resolved URLs if `resolve_files` is set to True in user properties."
    ),
    "config_parameters": [
        {
            "name": "force_resolve",
            "required": False,
            "description": "Resolve all the urls regardless of the 'resolve' query parameter",
            "default": True,
            "type": "boolean",
        },
    ],
    "input_schema": {
        "type": "object",  # Any Object or string
        "required": [],
    },
    "output_schema": {
        "type": "object",  # Returns the object with resolved URLS
        "required": [],
    },
}


class FileResolverComponent(ComponentBase):
    def __init__(self, **kwargs):
        super().__init__(info, **kwargs)
        self.file_service = FileService()
        self.force_resolve = self.get_config("force_resolve", True)

    def invoke(self, message: Message, data: Dict[str, Any]) -> Dict[str, Any]:
        should_resolve_files = (message.get_user_properties() or {}).get("resolve_files", False)
        if not should_resolve_files:
            return data
        copied_data = data.copy()
        session_id = (message.get_user_properties() or {}).get("session_id")
        if not session_id:
            return copied_data

        copied_data = recursive_file_resolver(
            copied_data,
            resolver=self.file_service.resolve_all_resolvable_urls,
            session_id=session_id,
            force_resolve=self.force_resolve,
        )

        return copied_data
