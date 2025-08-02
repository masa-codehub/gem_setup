"""
JSON パース機能の単体テスト
TDD: まず基本的な機能から確実に動作するようにテストする
"""
import unittest
from main.application.services.react_service import ReActService
from unittest.mock import Mock


class TestReActServiceJsonParsing(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        self.react_service = ReActService(Mock())

    def test_parse_simple_json_action(self):
        """シンプルなJSON形式のアクションをパースできるかテスト"""
        # Arrange
        simple_response = '''
Action Input: {"recipient_id": "DEBATER_A", "message_type": "PROMPT_FOR_STATEMENT", "payload": {"topic": "test"}}
        '''

        # Act
        result = self.react_service._parse_action_from_response(
            simple_response)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["recipient_id"], "DEBATER_A")
        self.assertEqual(result["message_type"], "PROMPT_FOR_STATEMENT")

    def test_parse_multiline_json_action(self):
        """複数行にわたるJSONをパースできるかテスト"""
        # Arrange
        multiline_response = '''
Action Input: {
    "recipient_id": "DEBATER_N",
    "message_type": "PROMPT_FOR_REBUTTAL",
    "payload": {
        "topic": "AI Ethics"
    }
}
        '''

        # Act
        result = self.react_service._parse_action_from_response(
            multiline_response)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["recipient_id"], "DEBATER_N")
        self.assertEqual(result["message_type"], "PROMPT_FOR_REBUTTAL")


if __name__ == '__main__':
    unittest.main()
