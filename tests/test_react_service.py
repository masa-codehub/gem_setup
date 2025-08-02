"""
ReActServiceのテスト
TDD: まず失敗するテストを書く（Red phase）
"""
import unittest
from unittest.mock import Mock
from main.application.services.react_service import ReActService
from main.domain.models import Message


class TestReActService(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        self.mock_llm_service = Mock()
        self.react_service = ReActService(self.mock_llm_service)

    def test_think_and_act_should_generate_message_from_context(self):
        """
        ReActServiceは現在の文脈から次のアクションを思考し、
        適切なMessageを生成する必要がある
        """
        # Arrange
        agent_id = "MODERATOR"
        persona = "公正な司会者として議論を進める"
        history = [
            Message(
                sender_id="SYSTEM",
                recipient_id="MODERATOR",
                message_type="PROMPT_FOR_STATEMENT",
                payload={"topic": "AIの倫理について"},
                turn_id=1
            )
        ]

        # LLMの応答をモック
        self.mock_llm_service.generate_response.return_value = """
        私は司会者として、この議論を開始します。
        
        Action: post_message
        Input: {"recipient_id": "DEBATER_A", "message_type": "REQUEST_STATEMENT", "body": {"topic": "AIの倫理について"}}
        """

        # Act
        result = self.react_service.think_and_act(agent_id, persona, history)

        # Assert
        self.assertIsInstance(result, Message)
        self.assertEqual(result.sender_id, agent_id)
        self.mock_llm_service.generate_response.assert_called_once()


if __name__ == '__main__':
    unittest.main()
