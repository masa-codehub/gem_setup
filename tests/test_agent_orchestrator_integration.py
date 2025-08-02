"""
AgentOrchestratorの統合テスト
TDD: agent_main.pyの機能をAgentOrchestratorに移植するためのテスト
"""
import unittest
from unittest.mock import Mock, patch
from main.interfaces.agent_orchestrator import AgentOrchestrator
from main.application.interfaces import IMessageBroker, ILLMService
from main.application.services.react_service import ReActService
from main.domain.models import Message


class TestAgentOrchestratorIntegration(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        self.mock_message_broker = Mock(spec=IMessageBroker)
        self.mock_llm_service = Mock(spec=ILLMService)

    @patch('main.interfaces.agent_orchestrator.SqliteMessageBroker')
    @patch('main.interfaces.agent_orchestrator.GeminiService')
    @patch('main.interfaces.agent_orchestrator.ReActService')
    def test_orchestrator_should_integrate_clean_architecture_services(
        self, mock_react_service, mock_gemini_service, mock_message_broker
    ):
        """
        AgentOrchestratorはクリーンアーキテクチャの各サービスを
        適切に統合して使用する必要がある
        """
        # Arrange
        orchestrator = AgentOrchestrator("MODERATOR", "clean")

        # 依存性が適切に注入されることを確認
        mock_message_broker.assert_called_once()
        mock_gemini_service.assert_called_once()
        mock_react_service.assert_called_once()

    def test_orchestrator_should_handle_message_processing_loop(self):
        """
        AgentOrchestratorはメッセージ処理のメインループを
        適切に管理する必要がある
        """
        # Arrange
        with patch('main.interfaces.agent_orchestrator.SqliteMessageBroker') as mock_broker_class, \
                patch('main.interfaces.agent_orchestrator.GeminiService') as mock_llm_class, \
                patch('main.interfaces.agent_orchestrator.ReActService') as mock_react_class, \
                patch('time.sleep') as mock_sleep:

            mock_broker = Mock()
            mock_broker_class.return_value = mock_broker

            # メッセージ処理シミュレーション：最初のメッセージでEXITを返す
            mock_broker.get_message.side_effect = [
                Message(
                    sender_id="SYSTEM",
                    recipient_id="MODERATOR",
                    message_type="END_DEBATE",
                    payload={},
                    turn_id=1
                ),
                None  # 2回目の呼び出しではNone
            ]

            orchestrator = AgentOrchestrator("MODERATOR", "clean")

            # Act - startメソッドを呼び出し（short loop for testing）
            with patch.object(orchestrator, '_handle_message') as mock_handle:
                mock_handle.return_value = "EXIT"
                orchestrator.start()

            # Assert
            mock_broker.get_message.assert_called()
            mock_handle.assert_called_once()

    def test_orchestrator_should_support_legacy_mode(self):
        """
        AgentOrchestratorはレガシーモードもサポートする必要がある
        """
        # Arrange & Act
        orchestrator = AgentOrchestrator("MODERATOR", "legacy")

        # Assert
        self.assertEqual(orchestrator.mode, "legacy")
        # レガシーモードでも正常に初期化されることを確認
        self.assertIsNotNone(orchestrator)


if __name__ == '__main__':
    unittest.main()
