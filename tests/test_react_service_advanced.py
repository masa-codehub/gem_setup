"""
ReActServiceの詳細なテスト - 実際のReActロジックをテスト
TDD: より複雑な機能はテストから設計する
"""
import unittest
from unittest.mock import Mock
from main.application.services.react_service import ReActService
from main.application.interfaces import ILLMService, IMessageBroker
from main.domain.models import Message


class TestReActServiceAdvanced(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        self.mock_llm_service = Mock(spec=ILLMService)
        self.mock_message_broker = Mock(spec=IMessageBroker)
        self.react_service = ReActService(
            self.mock_llm_service,
            self.mock_message_broker
        )

    def test_observe_think_act_cycle_should_handle_incoming_message(self):
        """
        ReActサイクル：観察→思考→行動のフルサイクルをテスト
        """
        # Arrange - 受信メッセージの設定
        incoming_message = Message(
            sender_id="DEBATER_A",
            recipient_id="MODERATOR",
            message_type="SUBMIT_STATEMENT",
            payload={"text": "AIは人類に有益です", "topic": "AIの是非"},
            turn_id=1
        )
        self.mock_message_broker.get_message.return_value = incoming_message

        # Arrange - LLMの応答をモック
        self.mock_llm_service.generate_response.return_value = """
        Thought: DEBATER_Aから意見文が提出されました。次はDEBATER_Nからの意見文を要求する必要があります。

        Action: post_message
        Action Input: {
            "recipient_id": "DEBATER_N",
            "message_type": "PROMPT_FOR_STATEMENT",
            "payload": {
                "topic": "AIの是非",
                "opponent_statement": "AIは人類に有益です"
            }
        }
        """

        # Act
        result = self.react_service.observe_think_act("MODERATOR")

        # Assert - LLMが適切なプロンプトで呼び出されたか
        self.mock_llm_service.generate_response.assert_called_once()
        call_args = self.mock_llm_service.generate_response.call_args[0][0]
        self.assertIn("DEBATER_A", call_args)
        self.assertIn("SUBMIT_STATEMENT", call_args)

        # Assert - 結果メッセージが適切に生成されたか
        self.assertIsInstance(result, Message)
        self.assertEqual(result.sender_id, "MODERATOR")
        self.assertEqual(result.recipient_id, "DEBATER_N")
        self.assertEqual(result.message_type, "PROMPT_FOR_STATEMENT")

    def test_should_handle_no_incoming_messages(self):
        """
        新しいメッセージがない場合の処理
        """
        # Arrange
        self.mock_message_broker.get_message.return_value = None

        # Act
        result = self.react_service.observe_think_act("MODERATOR")

        # Assert
        self.assertIsNone(result)
        self.mock_llm_service.generate_response.assert_not_called()

    def test_should_parse_complex_llm_response_with_json(self):
        """
        LLMの複雑な応答（JSON含む）を正しくパースできるかテスト
        """
        # Arrange
        complex_response = '''
        私はモデレーターとして、この発言を分析しました。

        Thought: 両方の討論者から意見文を受け取りました。次は反駁フェーズに進む必要があります。

        Action: post_message
        Action Input: {
            "recipient_id": "DEBATER_A",
            "message_type": "PROMPT_FOR_REBUTTAL",
            "payload": {
                "opponent_statement": "AIは危険な技術です",
                "your_statement": "AIは有益な技術です",
                "phase": "rebuttal"
            }
        }

        このようにして議論を進行させます。
        '''

        # Act
        result = self.react_service._parse_action_from_response(
            complex_response)

        # Assert
        self.assertEqual(result["recipient_id"], "DEBATER_A")
        self.assertEqual(result["message_type"], "PROMPT_FOR_REBUTTAL")
        self.assertIn("opponent_statement", result["payload"])
        self.assertEqual(result["payload"]["phase"], "rebuttal")


if __name__ == '__main__':
    unittest.main()
