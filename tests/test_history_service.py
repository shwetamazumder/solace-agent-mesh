import unittest

from src.services.history_service import HistoryService



class TestHistoryService(unittest.TestCase):
    def setUp(self):
        self.history = HistoryService({"history_policy": {"max_turns": 10}})

    def test_store_history(self):
        # Dummy data
        session_id = "session123"
        role = "user"
        content = "Hello, world!"

        # Call the method
        self.history.store_history(session_id, role, content)

        # Retrieve the history
        history = self.history.get_history(session_id)

        # Assert the result
        self.assertIsNotNone(history)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["role"], role)
        self.assertEqual(history[0]["content"], content)

    def test_max_turns_limit(self):
        session_id = "session456"
        roles = [
            "user",
            "assistant",
        ] * 6  # 12 elements alternating between user and assistant

        # Add 12 elements to the history
        for i, role in enumerate(roles):
            content = f"Message {i+1}"
            self.history.store_history(session_id, role, content)

        # Retrieve the history
        history = self.history.get_history(session_id)

        # Assert that only 10 elements are present
        self.assertEqual(len(history), 10)

        # Assert that the first 10 messages are present (not the last 2)
        for i in range(10):
            self.assertEqual(history[i]["role"], roles[i + 2])
            self.assertEqual(history[i]["content"], f"Message {i+3}")

        # Assert that the first two messages (1 and 2) are not present
        self.assertNotIn("Message 1", [entry["content"] for entry in history])
        self.assertNotIn("Message 2", [entry["content"] for entry in history])


if __name__ == "__main__":
    unittest.main()
