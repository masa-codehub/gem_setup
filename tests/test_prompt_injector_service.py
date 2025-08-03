"""
Prompt Injector Service のTDDテスト
プロンプト構築サービスのテスト
"""
import unittest
from unittest.mock import Mock, patch, mock_open
from main.infrastructure.prompt_injector_service import PromptInjectorService
from main.domain.models import Message


class TestPromptInjectorService(unittest.TestCase):
    """プロンプトインジェクターサービスのTDDテスト"""

    def test_should_build_prompt_with_persona_and_context(self):
        """Red: プロンプトインジェクターはペルソナと文脈からプロンプトを構築する必要がある"""
        # Arrange
        service = PromptInjectorService()

        test_message = Message(
            sender_id="SYSTEM",
            recipient_id="DEBATER_A",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": "AI benefits"},
            turn_id=1
        )

        context = {
            'message': test_message,
            'current_turn': 1
        }

        with patch('builtins.open', mock_open(read_data="You are a skilled debater.")):
            # Act
            prompt = service.build_prompt("DEBATER_A", context)

            # Assert
            self.assertIn("You are a skilled debater.", prompt)
            self.assertIn("AI benefits", prompt)
            self.assertIn("Current Context", prompt)

    def test_should_load_persona_from_config_file(self):
        """Red: ペルソナを設定ファイルから読み込める必要がある"""
        # Arrange
        service = PromptInjectorService()
        expected_persona = "You are a professional moderator."

        with patch('builtins.open', mock_open(read_data=expected_persona)):
            # Act
            persona = service.load_persona("MODERATOR")

            # Assert
            self.assertEqual(persona, expected_persona)

    @patch('builtins.open')
    def test_should_handle_missing_persona_file_gracefully(self, mock_file):
        """Red: ペルソナファイルが見つからない場合は適切に処理する必要がある"""
        # Arrange
        mock_file.side_effect = FileNotFoundError("File not found")
        service = PromptInjectorService()

        # Act
        persona = service.load_persona("UNKNOWN_AGENT")

        # Assert - デフォルトペルソナが返される
        self.assertIn("helpful AI assistant", persona)

    def test_should_load_system_rules(self):
        """Red: システムルールを読み込める必要がある"""
        # Arrange
        service = PromptInjectorService()
        expected_rules = "Follow debate protocol strictly."

        with patch('builtins.open', mock_open(read_data=expected_rules)):
            # Act
            rules = service.load_system_rules()

            # Assert
            self.assertEqual(rules, expected_rules)


if __name__ == '__main__':
    unittest.main()
