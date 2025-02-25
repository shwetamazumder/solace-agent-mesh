"""Slack Post Message action."""

from typing import Dict, List, Union

from solace_ai_connector.common.log import log
from ....common.action import Action
from ....common.time import FIVE_MINUTES
from ....common.action_response import ActionResponse
from ....services.file_service import FileService, FS_PROTOCOL


class PostMessage(Action):
    """Action for posting messages to Slack channels."""

    def __init__(self, **kwargs):
        """Initialize the action with its configuration."""
        super().__init__(
            {
                "name": "post_message",
                "prompt_directive": "Post a message to a Slack channel",
                "params": [
                    {
                        "name": "channel",
                        "desc": "The Slack channel to post to (include # prefix)",
                        "type": "string",
                    },
                    {
                        "name": "thread_correlation_id",
                        "desc": "Optional correlation ID to group messages in a thread",
                        "type": "string",
                    },
                    {
                        "name": "text",
                        "desc": "Text message to post",
                        "type": "string",
                    },
                    {
                        "name": "blocks",
                        "desc": "Slack blocks for formatted message",
                        "type": "array",
                    },
                    {
                        "name": "files",
                        "desc": f"Array of file URLs ({FS_PROTOCOL}:// or inline files with <file><data/></file> tags)",
                        "type": "array",
                    },
                    {
                        "name": "last_post_to_thread",
                        "desc": "If True, clears the thread correlation cache after posting",
                        "type": "bool",
                    },
                ],
                "required_scopes": ["slack:post_message:create"],
            },
            **kwargs,
        )

    def _process_files(
        self, files: List[str], session_id: str
    ) -> List[Dict[str, Union[str, bytes]]]:
        """Process file URLs into uploadable content.

        Args:
            files: List of file URLs to process
            session_id: Current session ID for file service

        Returns:
            List of dicts containing file data and titles
        """
        if not files:
            return []

        file_service = FileService()
        processed_files = []

        for file_url in files:
            try:
                # Download file content
                content = file_service.download_to_buffer(file_url, session_id)

                # Extract filename from URL
                filename = file_url.split("/")[-1]
                processed_files.append(
                    {
                        "content": content,
                        "title": filename,
                    }
                )
            except Exception as e:
                log.error("Failed to process file %s: %s", file_url, str(e))

        return processed_files

    def invoke(self, params: Dict, meta: Dict = {}) -> ActionResponse:
        """Post message to Slack channel.

        Args:
            params: Action parameters including channel, message, etc.
            meta: Additional metadata including session_id

        Returns:
            ActionResponse with success/error message
        """
        try:
            # Get Slack client from agent
            slack_client = self.get_agent().slack_client

            channel = params.get("channel", "").strip()

            # Remove the # prefix if present
            if channel.startswith("#"):
                channel = channel[1:]

            # Get thread_ts from correlation id if provided
            thread_correlation_id = params.get("thread_correlation_id")
            thread_ts = None
            if thread_correlation_id:
                cache_key = f"slack_agent:thread_correlation:{thread_correlation_id}"
                thread_ts = self.get_agent().cache_service.get_data(cache_key)

            # Prepare message arguments
            msg_args = {
                "channel": channel,
                "text": params.get("text", ""),
                "blocks": params.get("blocks"),
                "thread_ts": thread_ts,
            }

            # Send message
            response = slack_client.chat_postMessage(**msg_args)

            # Handle thread correlation caching
            if thread_correlation_id:
                cache_key = f"slack_agent:thread_correlation:{thread_correlation_id}"

                # Clear cache if this is the last post
                if params.get("last_post_to_thread"):
                    self.get_agent().cache_service.remove_data(cache_key)
                # Store thread_ts if this is a new thread
                elif not thread_ts:
                    thread_cache_ttl = self.get_agent().get_config("thread_cache_ttl")
                    self.get_agent().cache_service.add_data(
                        cache_key,
                        response["ts"],
                        expiry=thread_cache_ttl,
                        component=self.get_agent(),
                    )
                    msg_args["thread_ts"] = response["ts"]

            # Process any files
            files = params.get("files", [])
            if files:
                processed_files = self._process_files(files, meta.get("session_id"))
                for file_data in processed_files:
                    slack_client.files_upload_v2(
                        channel=channel,
                        content=file_data["content"],
                        title=file_data["title"],
                        thread_ts=msg_args["thread_ts"],
                    )

            # Return thread_correlation_id in message for reference
            return ActionResponse(
                message=(
                    f"Successfully posted message to {channel}. "
                    f"Thread correlation ID: {thread_correlation_id or 'none'}"
                    + (
                        f" (thread_ts: {response['ts']})"
                        if not thread_ts
                        else f" (replied to existing thread)"
                    )
                )
            )

        except Exception as e:
            log.error("Failed to post Slack message: %s", str(e))
            return ActionResponse(message=f"Failed to post message to Slack: {str(e)}")
