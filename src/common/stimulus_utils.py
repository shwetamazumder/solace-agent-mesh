"""Utilities for describing stimulus state and events.

This module provides functions for generating human-readable descriptions
of stimulus state, including events, errors and completion status.
"""

from typing import Dict, List
import time
import json

from solace_ai_connector.common.log import log
from ..services.file_service import FileService


def _format_timestamp(timestamp: float) -> str:
    """Formats a Unix timestamp into a human readable string.

    Args:
        timestamp: Unix timestamp to format

    Returns:
        Formatted timestamp string in YYYY-MM-DD HH:MM:SS format
    """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def _format_event(event: Dict) -> str:
    """Formats a single stimulus event into markdown.

    Args:
        event: Dictionary containing event details including topic, payload,
            user properties and timestamp

    Returns:
        Markdown formatted string describing the event
    """
    timestamp = _format_timestamp(event.get("timestamp", 0))
    topic = event.get("topic", "")
    payload = event.get("payload", {})
    user_props = event.get("user_properties", {})

    # Format based on topic pattern, similar to ConversationFormatter
    if "/stimulus/" in topic:
        stimulus_text = payload.get("text", "")
        identity = user_props.get("identity", "unknown")
        if "/reinvoke" in topic:
            return f"### {timestamp} - Reinvoke Request\nFrom: {identity}\n```\n{stimulus_text}\n```\n"
        return f"### {timestamp} - Initial Request\nFrom: {identity}\n```\n{stimulus_text}\n```\n"

    if "/response/" in topic or "/streamingResponse/" in topic:
        if isinstance(payload, dict) and payload.get("last_chunk") is True:
            response_text = payload.get("text", "")
            return f"### {timestamp} - Response:\n{response_text}\n\n"
        return ""

    if "/responseComplete/" in topic:
        return f"### {timestamp} - Response Complete\n"

    if "/actionRequest/" in topic:
        action_name = payload.get("action_name", "")
        action_params = payload.get("action_params", {})
        params_text = "\n".join(f"- {k}: {v}" for k, v in action_params.items())
        return f"### {timestamp} - Action Request: {action_name}\n{params_text}\n"

    if "/actionResponse/" in topic:
        topic_parts = topic.split("/agent/")[1].split("/")
        agent_name = topic_parts[0]
        action_name = topic_parts[1]
        response_text = "\n".join(f"- {k}: {v}" for k, v in payload.items())
        return f"### {timestamp} - Action Response: {agent_name}.{action_name}\n{response_text}\n"

    return f"### {timestamp} - Other Event\nTopic: {topic}\n"


def _format_error(error: Dict) -> str:
    """Formats a single stimulus error into markdown.

    Args:
        error: Dictionary containing error details including message,
            timestamp and user properties

    Returns:
        Markdown formatted string describing the error
    """
    timestamp = _format_timestamp(error.get("timestamp", 0))
    message = error.get("message", "Unknown error")
    source = error.get("source", "Unknown source")
    return f"### {timestamp} - Error\nSource: {source}\nDetails: {message}\n"


def describe_stimulus(stimulus_uuid: str, state: Dict, is_timeout: bool = False) -> str:
    """Generates a markdown description of a stimulus's complete state.

    Takes a stimulus state dictionary and generates a human-readable markdown
    description including all events, errors and completion status.

    Args:
        stimulus_uuid: UUID of the stimulus
        state: Dictionary containing complete stimulus state including events,
            errors and metadata
        is_timeout: Whether this stimulus timed out

    Returns:
        Markdown formatted string describing the complete stimulus journey
    """
    events: List[Dict] = state.get("events", [])
    errors: List[Dict] = state.get("errors", [])
    completion_status = state.get("completion_status", "unknown")

    # Start with header
    description = f"# Stimulus {stimulus_uuid}\n\n"

    # Add completion status with timeout indicator if applicable
    status_str = completion_status.upper()
    if is_timeout:
        status_str += " (TIMED OUT)"
    description += f"**Status:** {status_str}\n\n"

    # Add events section
    if events:
        description += "## Events\n\n"
        for event in events:
            description += _format_event(event)

    # Add errors section
    if errors:
        description += "\n## Errors\n\n"
        for error in errors:
            description += _format_error(error)

    # Add any available files
    available_files_json = (
        events[-1].get("user_properties", {}).get("available_files", None)
    )
    available_files = []
    if available_files_json:
        try:
            available_files_user_prop = json.loads(available_files_json)
            if available_files_user_prop:
                file_service = FileService()
                available_files = [
                    file_service.get_file_block_by_metadata(file)
                    for file in available_files_user_prop
                ]
        except Exception as e:
            log.error("Failed to get available files: %s", str(e))

        if available_files:
            description += "\n## Available Files\n\n"
            description += "\n\n".join(available_files)

    return description
