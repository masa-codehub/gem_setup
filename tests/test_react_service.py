"""
ReActServiceのテスト
TDD: まず失敗するテストを書く（Red phase）
"""
import unittest
from unittest.mock import Mock
from main.use_cases.services.react_service import ReActService
from main.entities.models import Message


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

        # LLMの応答をモック - 新しいアーキテクチャでMessageオブジェクトを返す
        mock_response = Message(
            sender_id=agent_id,
            recipient_id="DEBATER_A",
            message_type="REQUEST_STATEMENT",
            payload={"topic": "AIの倫理について"},
            turn_id=2
        )
        self.mock_llm_service.generate_response.return_value = mock_response

        # Act
        result = self.react_service.think_and_act(agent_id, persona, history)

        # Assert
        self.assertIsInstance(result, Message)
        self.assertEqual(result.sender_id, agent_id)
        # 新しいインターフェースでは(agent_id, context_message)で呼び出される
        self.mock_llm_service.generate_response.assert_called_once_with(
            agent_id, history[-1])


if __name__ == '__main__':
    unittest.main()
