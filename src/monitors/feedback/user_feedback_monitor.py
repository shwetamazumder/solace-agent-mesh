"""Monitor component that tracks user feedback for responses.

This component:
1. Listens to feedback events from the user
3. Creates .feedback file with the feedback contents
"""

from ..base_monitor_component import BaseMonitorComponent
from typing import Dict, Optional

from solace_ai_connector.common.log import log
from solace_ai_connector.common.message import Message
from ...services.file_service import FileService
from ...common.constants import SOLACE_AGENT_MESH_SYSTEM_SESSION_ID
from ...common.time import ONE_DAY

import json
import time

info = {
    "class_name": "UserFeedbackMonitor",
    "description": "Monitor that tracks user feedback and generates a feedback file",
    "config_parameters": [
    ],
}

DEFAULT_STIMULUS_TTL = 7 * ONE_DAY;
class UserFeedbackMonitor(BaseMonitorComponent):
    """Monitor that tracks user feedback and generates a feedback file"""

    def __init__(self, module_info: Optional[Dict] = None, **kwargs):
        module_info = module_info or {}
        module_info.update(info)
        super().__init__(module_info, **kwargs)
        self.feedback_ttl = self.get_config("feedback_ttl", DEFAULT_STIMULUS_TTL)

    def invoke(self, message: Message, data: Dict):

        """Create a feedback file with the feedback contents"""
        
        # Extract stimulus UUID and session ID from feedback data
        feedback_data = data.get("data", {})
        stimulus_uuid = feedback_data.get("stimulus_uuid", "unknown")

        # Create file content
        file_content = json.dumps(data, indent=2)

        # Upload file to the file service
        file_service = FileService()
        file_name = f"{stimulus_uuid}_feedback.json"
        file_service.upload_from_buffer(
            file_content.encode("utf-8"),
            file_name=file_name,
            session_id=SOLACE_AGENT_MESH_SYSTEM_SESSION_ID,
            data_source="User Feedback Monitor",
            expiration_timestamp=time.time() + self.feedback_ttl,
        )

        # File the related stimulus files and update the expiration date
        
        # First get all of the metadata
        metadata = file_service.list_all_metadata(
            session_id=SOLACE_AGENT_MESH_SYSTEM_SESSION_ID,
        )

        for meta in metadata:
            if meta["name"].endswith(f"{stimulus_uuid}.md") or meta["name"].endswith(f"{stimulus_uuid}.stim"):
                try:
                    file_service.update_file_expiration(
                        meta["url"],
                        expiration_timestamp=time.time() + self.feedback_ttl,
                    )
                except Exception as e:
                    log.error(f"Error updating expiration for file {meta['url']}: {str(e)}")
        return data
