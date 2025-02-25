"""Monitor component that tracks stimulus events and errors.

This component:
1. Listens to all Solace Agent Mesh events
2. Tracks events and errors for each stimulus
3. Creates .stim and .md files when stimuli complete
4. Triggers notifications to agents when errors occur
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import yaml
import json
import base64
from solace_ai_connector.common.log import log
from solace_ai_connector.common.message import Message

from ..base_monitor_component import BaseMonitorComponent
from ...common.stimulus_utils import describe_stimulus
from ...common.constants import SOLACE_AGENT_MESH_SYSTEM_SESSION_ID
from ...services.file_service import FileService
from ...common.time import FIVE_MINUTES


info = {
    "class_name": "StimAndErrorMonitor",
    "description": "Monitor that tracks stimulus events/errors and generates summary files",
    "config_parameters": [
        {
            "name": "stimulus_ttl",
            "required": False,
            "description": "Time-to-live for stimulus state in seconds (default: 3600)",
            "type": "integer",
            "default": 20,
        },
        {
            "name": "notification_flow_name",
            "required": True,
            "description": "Flow to send notifications to. This flow must be defined within the same instance as this monitor",
            "type": "string",
        },
        {
            "name": "error_format",
            "required": False,
            "description": "Format for error messages (default: text)",
            "type": "string",
            "default": "markdown",
        },
        {
            "name": "notification_mode",
            "required": False,
            "description": "Mode for sending notifications. One of 'errors', 'all', 'none (default: errors)",
            "type": "string",
            "default": "errors",
        },
    ],
}


DEFAULT_STIMULUS_TTL = FIVE_MINUTES


class StimAndErrorMonitor(BaseMonitorComponent):
    """Monitor that tracks stimulus events/errors and generates summary files."""

    SLACK_POST_MESSAGE_SCOPE = "slack:post_message:create"

    def __init__(self, module_info: Optional[Dict] = None, **kwargs):
        """Initialize the monitor.

        Args:
            module_info: Optional configuration dictionary.
            **kwargs: Additional keyword arguments.
        """
        module_info = module_info or {}
        module_info.update(info)
        super().__init__(module_info, **kwargs)
        self.stimulus_ttl = self.get_config("stimulus_ttl", DEFAULT_STIMULUS_TTL)
        self.notification_flow_name = self.get_config(
            "notification_flow_name",
        )
        self.error_format = self.get_config("error_format", "markdown")
        self.notification_mode = self.get_config("notification_mode", "errors")

    def _get_stimulus_cache_key(self, stimulus_uuid: str) -> str:
        """Generate cache key for a stimulus.

        Args:
            stimulus_uuid: The UUID of the stimulus.

        Returns:
            The cache key string.
        """
        return f"monitor:stimulus_state:{stimulus_uuid}"

    def _get_stimulus_state(self, stimulus_uuid: str) -> Dict:
        """Get current state for a stimulus from cache.

        Args:
            stimulus_uuid: The UUID of the stimulus.

        Returns:
            Dictionary containing stimulus state with events, errors and metadata.
        """
        cache_key = self._get_stimulus_cache_key(stimulus_uuid)
        state = self.cache_service.get_data(cache_key) or {
            "events": [],
            "errors": [],
            "metadata": {},
        }
        return state

    def _save_stimulus_state(self, stimulus_uuid: str, state: Dict) -> None:
        """Save stimulus state to cache.

        Args:
            stimulus_uuid: The UUID of the stimulus.
            state: Dictionary containing the state to save.
        """
        cache_key = self._get_stimulus_cache_key(stimulus_uuid)
        self.cache_service.add_data(
            cache_key, state, expiry=self.stimulus_ttl, component=self
        )

    def add_system_event(self, message: Message) -> None:
        """Add a system event to stimulus state.

        Args:
            message: The Message object containing the system event.
        """
        user_props = message.get_user_properties() or {}
        topic = message.get_topic()
        stimulus_uuid = user_props.get("stimulus_uuid")

        if not stimulus_uuid:
            return

        if "/stimulus/error/" in topic:
            error_info = message.get_payload() or {}

            if "error_message" in error_info:
                # Solace Agent Mesh error format
                error_message = error_info.get("error_message", "Unknown error")
                error_source = error_info.get("source", "Unknown source")
            if "error" in error_info:
                # solace-ai-connector error format
                error = error_info.get("error", {})
                error_text = error.get("text", "Unknown error")
                location = error_info.get("location")
                location_str = "Unknown"
                error_original_message = error_info.get("message", None)
                if location:
                    location_str = (
                        f"{location.get('instance', '')}"
                        f".{location.get('flow', '')}"
                        f".{location.get('component', '')}"
                        f"[{location.get('component_idx', '0')}]"
                    )

                error_message = (
                    f"\n  Error in component {location_str}"
                    f"\n  Exception name: {error.get('exception', 'Unknown')}"
                    f"\n  Exception info: {error_text}"
                    f"\n  Stack trace: {error.get('traceback', '--none--')}\n"
                )

                error_source = (
                    f"\n  Instance: {location.get('instance', 'Unknown')}"
                    f"\n  Flow: {location.get('flow', 'Unknown')}"
                    f"\n  Component: {location.get('component', 'Unknown')}"
                    f"\n  Component Index: {location.get('component_idx', '0')}\n"
                )

            self.add_error(
                stimulus_uuid,
                error_message=error_message,
                error_source=error_source,
                user_properties=user_props,
            )

        state = self._get_stimulus_state(stimulus_uuid)

        # Add the event
        state["events"].append(
            {
                "topic": topic,
                "payload": message.get_payload(),
                "user_properties": user_props,
                "timestamp": time.time(),
            }
        )

        self._save_stimulus_state(stimulus_uuid, state)

        # If the event's topic contains "responseComplete", mark the stimulus as complete
        if "/responseComplete/" in topic:
            self.handle_stimulus_complete(stimulus_uuid, state, session_id=SOLACE_AGENT_MESH_SYSTEM_SESSION_ID)

    def add_error(
        self,
        stimulus_uuid: str,
        error_message: str,
        error_source: str,
        user_properties: Optional[Dict] = None,
    ) -> None:
        """Add an error to stimulus state and notify.

        Args:
            stimulus_uuid: The UUID of the stimulus.
            error_message: The error message.
            error_source: The source of the error.
            user_properties: Optional user properties.
        """
        state = self._get_stimulus_state(stimulus_uuid)

        # Add the error
        error = {
            "message": error_message,
            "source": error_source,
            "timestamp": time.time(),
            "user_properties": user_properties or {},
        }
        state["errors"].append(error)

        self._save_stimulus_state(stimulus_uuid, state)

        error_text = None
        error_blocks = None
        if self.error_format == "slack":
            error_blocks = self._format_error_message_slack(
                stimulus_uuid, error_message, error_source
            )
        elif self.error_format == "markdown":
            error_text = (
                f"__Error detected for stimulus **{stimulus_uuid}**__\n\n"
                "*Error Message*\n"
                f"{error_message}\n\n"
                "*Source*\n"
                f"{error_source}"
            )
        else:
            error_text = f"Error detected in stimulus {stimulus_uuid} from {error_source}: {error_message}"

        # Send notification about the error
        self.send_to_flow(
            self.notification_flow_name,
            Message(
                payload={
                    "is_last": False,
                    "correlation_id": stimulus_uuid,
                    "text": error_text,
                    "blocks": error_blocks,
                },
                user_properties={
                    "originator_scopes": [self.SLACK_POST_MESSAGE_SCOPE],
                    "session_id": user_properties.get("session_id"),
                },
            ),
        )

    def _format_error_message_markdown(
        self, stimulus_uuid: str, error_message: str, error_source: str
    ) -> str:
        """Format an error message as a markdown string.

        Args:
            stimulus_uuid: The UUID of the stimulus.
            error_message: The error message.
            error_source: The source of the error.

        Returns:
            The formatted error message.
        """

        return (
            f"__Error detected for stimulus **{stimulus_uuid}**__\n\n"
            "*Error Message*\n"
            f"{error_message}\n\n"
            "*Source*\n"
            f"{error_source}"
        )

    def _stimulus_has_error(self, state: Dict, is_timeout: bool) -> bool:
        """Check if a stimulus state contains an error.

        Args:
            state: The state of the stimulus.
            is_timeout: Whether this was a timeout completion.

        Returns:
            True if the stimulus state contains an error, False otherwise.
        """
        if is_timeout:
            return True

        return bool(state.get("errors"))

    def _format_error_message_slack(
        self, stimulus_uuid: str, error_message: str, error_source: str
    ) -> List[Dict]:
        """Format an error message as a Slack message.

        Args:
            stimulus_uuid: The UUID of the stimulus.
            error_message: The error message.
            error_source: The source of the error.

        Returns:
            The formatted error message in Slack blocks.

        """

        return [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":grimacing: Error detected for stimulus *{stimulus_uuid}*",
                    }
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Error Message*"},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": error_message}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Source*"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": error_source}},
        ]

    def _create_stimulus_files(
        self,
        stimulus_uuid: str,
        state: Dict,
        is_timeout: bool = False,
        session_id: str = None,
    ) -> Tuple[str, str]:
        """Create .stim and .md files for a completed stimulus.

        Args:
            stimulus_uuid: The UUID of the stimulus.
            state: The current state of the stimulus.
            is_timeout: Whether this was a timeout completion.
            session_id: Session ID for file service operations.

        Returns:
            Tuple of (stim_file_url, md_file_url).

        Raises:
            ValueError: If required file creation fails.
        """
        try:
            # Get user email from the first event's user properties
            identity = None
            if state["events"]:
                identity = (
                    state["events"][0]
                    .get("user_properties", {})
                    .get("user_info", {})
                    .get("email", "unknown")
                )
            # If no user email is found, use the identity
            if not identity:
                identity = state["events"][0].get("user_properties", {}).get("identity", "unknown")

            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Base filename
            base_filename = f"{identity}_{timestamp}_{stimulus_uuid}"

            # Add completion status to state
            state["completion_status"] = "timeout" if is_timeout else "complete"

            # Get the last event and get the available files from the user properties
            available_files = (
                state["events"][-1]
                .get("user_properties", {})
                .get("available_files", None)
            )
            try:
                available_files = json.loads(available_files)
            except Exception as e:
                log.error("Failed to parse available files: %s", str(e))
                available_files = []

            # If there are available files, go to the file service and get the file content
            if available_files:
                file_service = FileService()
                for file in available_files:
                    if "url" not in file:
                        if "data" in file:
                            file["content"] = file["data"]
                        file["id"] = file.get("name", "no file name")
                    else:
                        try:
                            file["content"] = file_service.download_to_buffer(
                                file["url"], session_id
                            )
                            file["id"] = file["url"]
                        except Exception as e:
                            # This can happen if the file has timed out
                            log.debug(
                                "Failed to download file from %s: %s",
                                file["url"],
                                str(e),
                            )
                            file["content"] = b"File no longer exists"
                            file["mime_type"] = "text/plain"
                    mime_type = file.get("mime_type", "")
                    if (
                        file.get("content")
                        and not mime_type.startswith("application")
                        and not mime_type.startswith("text")
                    ):
                        # base64 encode binary files
                        file["content"] = base64.b64encode(file["content"]).decode(
                            "utf-8"
                        )
                    elif type(file["content"]) == bytes:
                        file["content"] = file["content"].decode("utf-8")

            # Create .stim file
            stim_data = state.copy()
            stim_data["files"] = available_files
            stim_content = yaml.dump(stim_data, sort_keys=False)
            file_service = FileService()
            stim_meta = file_service.upload_from_buffer(
                stim_content.encode("utf-8"),
                f"{base_filename}.stim",
                session_id=session_id,
                data_source="Monitor - Stimulus and Error - Stimulus File",
            )

            # Create .md file using stimulus_utils
            md_content = describe_stimulus(stimulus_uuid, state, is_timeout=is_timeout)
            md_meta = file_service.upload_from_buffer(
                md_content.encode("utf-8"),
                f"{base_filename}.md",
                session_id=session_id,
                data_source="Monitor - Stimulus and Error - Description File",
            )

            return stim_meta["url"], md_meta["url"]

        except Exception as e:
            log.error("Failed to create stimulus files: %s", str(e))
            raise ValueError(f"Failed to create stimulus files: {str(e)}")

    def handle_stimulus_complete(
        self,
        stimulus_uuid: str,
        stimulus_state: Dict = None,
        is_timeout: bool = False,
        session_id: Optional[str] = None,
    ) -> None:
        """Handle stimulus completion or timeout.

        Args:
            stimulus_uuid: The UUID of the completed stimulus.
            stimulus_state: Optional pre-fetched state.
            is_timeout: Whether this was a timeout completion.
            session_id: Optional session ID for file operations.
        """
        try:
            # Get current state
            state = stimulus_state or self._get_stimulus_state(stimulus_uuid)

            # Create .stim and .md files
            stim_url, md_url = self._create_stimulus_files(
                stimulus_uuid, state, is_timeout, session_id=session_id
            )

            if self.notification_mode == "none":
                return

            if self.notification_mode == "errors" and not self._stimulus_has_error(
                state, is_timeout
            ):
                return

            user_properties = (
                state["events"][0].get("user_properties") if state["events"] else {}
            )

            # Send notification about completion
            self.send_to_flow(
                self.notification_flow_name,
                Message(
                    payload={
                        "is_last": False,
                        "correlation_id": stimulus_uuid,
                        "text": f"Stimulus {stimulus_uuid} {'timed out' if is_timeout else 'completed'}",
                    },
                    user_properties={
                        "originator_scopes": ["slack:post_message:create"],
                        "session_id": session_id,
                    },
                ),
            )
            self.send_to_flow(
                self.notification_flow_name,
                Message(
                    payload={
                        "is_last": True,
                        "correlation_id": stimulus_uuid,
                        "text": "Stimulus Files:",
                        "files": [md_url, stim_url],
                    },
                    user_properties={
                        "originator_scopes": ["slack:post_message:create"],
                        "session_id": SOLACE_AGENT_MESH_SYSTEM_SESSION_ID,
                    },
                ),
            )

        except Exception as e:
            log.error(
                "Error handling stimulus completion for %s: %s", stimulus_uuid, str(e)
            )
        finally:
            # Remove stimulus from cache after successful completion
            cache_key = self._get_stimulus_cache_key(stimulus_uuid)
            self.cache_service.remove_data(cache_key)

    def handle_cache_expiry_event(self, event: Dict) -> None:
        """Handle cache expiry events for stimulus state.

        Args:
            event: Dictionary containing cache expiry event details.
        """
        # Extract stimulus UUID from cache key
        cache_key = event.get("key", "")
        if not cache_key.startswith("monitor:stimulus_state:"):
            return

        stimulus_uuid = cache_key.split(":")[-1]

        state = event.get("expired_data", {})

        # Mark stimulus as complete with timeout
        self.handle_stimulus_complete(
            stimulus_uuid=stimulus_uuid,
            stimulus_state=state,
            is_timeout=True,
            session_id=SOLACE_AGENT_MESH_SYSTEM_SESSION_ID,
        )

    def invoke(self, message: Message, data: Dict) -> None:
        """Process incoming messages.

        Args:
            message: The incoming Solace message.
            data: Additional message data/context.
        """
        self.add_system_event(message)
        return data
