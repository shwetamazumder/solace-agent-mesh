import time
import threading

from .base_history_provider import BaseHistoryProvider
from .long_term_memory.long_term_memory import LongTermMemory
from .long_term_memory.store import get_store

from ....common.constants import HISTORY_MEMORY_ROLE


class LongTermMemoryHistoryProvider(BaseHistoryProvider):
    """
    A history provider that stores history in memory and manages long-term memory.
    """

    def __init__(self, config=None):
        super().__init__(config)

        llm_config = self.config.get("llm_config", {})
        if not llm_config.get("model") or not llm_config.get("api_key"):
            raise ValueError("Missing required configuration for Long-Term Memory provider, Missing 'model' or 'api_key' in 'llm_config'.")
        
        self.store_config = self.config.get("store_config", {})
        self.store = get_store(self.store_config)

        self.long_term_memory = LongTermMemory(llm_config)

    def store_history(self, session_id: str, role: str, content: str | dict):
        """
        Store a new entry in the history.

        :param session_id: The session identifier.
        :param role: The role of the entry to be stored in the history.
        :param content: The content of the entry to be stored in the history.
        """

        history = self.store.retrieve(session_id)
        if not history:
            history = {
                "history": [],
                "files": [],
                "last_active_time": time.time(),
                "num_characters": 0,
                "num_turns": 0,
                "memory": {
                    "facts": [],
                    "instructions": [],
                },
                "summary": {}
            }

        if (
            self.enforce_alternate_message_roles
            and history["num_turns"] > 0
            # Check if the last entry was by the same role
            and history["history"]
            and history["history"][-1]["role"] == role
        ):
            # Append to last entry
            history["history"][-1]["content"] += content
        else:
            # Add the new entry
            history["history"].append(
                {"role": role, "content": content}
            )
            # Update the number of turns
            history["num_turns"] += 1

        # Update the length
        history["num_characters"] += len(str(content))
        # Update the last active time
        history["last_active_time"] = time.time()


        self.store.store(session_id, history)

        if role == "user" and len(history["history"]) > 2:
            def background_task():
                history = self.store.retrieve(session_id)

                recent_messages = history["history"][-3:-1]

                memory = self.long_term_memory.extract_memory_from_chat(recent_messages)
                if memory and (memory.get("facts") or memory.get("instructions") or memory.get("update_notes")):
                    history = self.store.retrieve(session_id)
                    updated_memory = self.long_term_memory.update_user_memory(history["memory"], memory)
                    history["memory"] = updated_memory
                    self.store.store(session_id, history)

                # Check if active memory requires summarization
                if history["num_characters"] > self.max_characters or history["num_turns"] > self.max_turns:
                    cut_off_index = 0
                    if history["num_turns"] > self.max_turns:
                        cut_off_index = max(0, int(self.max_turns * 0.6)) # 60% of max_turns

                    if history["num_characters"] > self.max_characters:
                        index = 0
                        characters = 0
                        while characters < self.max_characters and index < len(history["history"]) - 1:
                            characters += len(str(history["history"][index]["content"]))
                            index += 1
                        cut_off_index = max(cut_off_index, index)

                    cut_off_index = cut_off_index if cut_off_index % 2 == 0 else cut_off_index + 1 # Ensure even number of turns
                    cut_off_index = min(cut_off_index, len(history["history"]) - 1) + 1 # Ensure cut_off_index is within bounds
                    summary = self.long_term_memory.summarize_chat(history[:cut_off_index])
                    updated_summary = self.long_term_memory.update_summary(history["summary"], summary)

                    history["summary"] = updated_summary

                    history["num_characters"] = sum(len(str(entry["content"])) for entry in history["history"])
                    history["num_turns"] = len(history["history"])
                    history["last_active_time"] = time.time()

                    self.store.store(session_id, history)

            threading.Thread(target=background_task).start()

    def get_history(self, session_id: str):
        """
        Retrieve the entire history for a session.

        :param session_id: The session identifier.
        :return: The complete history for the session.
        """
        history = self.store.retrieve(session_id)
        if not history:
            return []
        
        long_term_memory = self.long_term_memory.retrieve_user_memory(history)

        if long_term_memory:
            return [
                {
                    "role": HISTORY_MEMORY_ROLE,
                    "content": long_term_memory
                },
                *history["history"]
            ]
        return history["history"]

    def store_file(self, session_id: str, file: dict):
        """
        Store a file in the history.

        :param session_id: The session identifier.
        :param file: The file metadata to be stored in the history.
        """
        history = self.store.retrieve(session_id)
        if not history:
            history = {
                "history": [],
                "files": [],
                "last_active_time": time.time(),
                "num_characters": 0,
                "num_turns": 0,
                "memory": {
                    "facts": [],
                    "instructions": [],
                },
                "summary": {}
            }
        history["last_active_time"] = time.time()

        # Check duplicate
        for f in history["files"]:
            if f.get("url") and f.get("url") == file.get("url"):
                return

        history["files"].append(file)
        self.store.store(session_id, history)

    def get_files(self, session_id: str):
        """
        Retrieve the files for a session.

        :param session_id: The session identifier.
        :return: The files for the session.
        """
        history = self.store.retrieve(session_id)
        if not history:
            return []
        files = []
        current_time = time.time()
        all_files = history["files"].copy()
        for file in all_files:
            expiration_timestamp = file.get("expiration_timestamp")
            if expiration_timestamp and current_time > expiration_timestamp:
                history["files"].remove(file)
                continue
            files.append(file)
        self.store.store(session_id, history)
        return files

    def clear_history(self, session_id: str, keep_levels=0, clear_files=True):
        """
        Clear the history for a session, optionally keeping a specified number of recent entries.

        :param session_id: The session identifier.
        :param keep_levels: Number of most recent history entries to keep. Default is 0 (clear all).
        :param clear_files: Whether to clear associated files. Default is True.
        """
        history = self.store.retrieve(session_id)
        if not history:
            return
        
        if clear_files:
            history["files"] = []

        def background_task():
            history = self.store.retrieve(session_id)
            cut_off_index = max(0, len(history["history"]) - keep_levels)

            summary = self.long_term_memory.summarize_chat(history["history"][:cut_off_index])
            updated_summary = self.long_term_memory.update_summary(history["summary"], summary)

            history["summary"] = updated_summary
            history["history"] = history["history"][-keep_levels:]
            history["num_turns"] = keep_levels
            history["num_characters"] = sum(len(str(entry["content"])) for entry in history["history"])
            history["last_active_time"] = time.time()

            self.store.store(session_id, history)

        threading.Thread(target=background_task).start()

    def get_session_meta(self, session_id: str):
        """
        Retrieve the session metadata.

        :param session_id: The session identifier.
        :return: The session metadata.
        """
        history = self.store.retrieve(session_id)
        if not history:
            return None
        return {
            "num_characters": history["num_characters"],
            "num_turns": history["num_turns"],
            "last_active_time": history["last_active_time"],
        }

    def get_all_sessions(self) -> list[str]:
        return self.store.keys()
