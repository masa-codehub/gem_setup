"""
AgentOrchestratorの統合テスト
TDD: agent_main.pyの機能をAgentOrchestratorに移植するためのテスト
"""
import unittest
from unittest.mock import Mock, patch
from main.interface_adapters.controllers.agent_orchestrator import AgentOrchestrator
from main.use_cases.interfaces import IMessageBroker, ILLMService
from main.use_cases.services.react_service import ReActService
from main.entities.models import Message


class TestAgentOrchestratorIntegration(unittest.TestCase):
    def setUp(self):
        """テストの前準備"""
        self.mock_message_broker = Mock(spec=IMessageBroker)
        self.mock_llm_service = Mock(spec=ILLMService)

    def test_orchestrator_should_integrate_clean_architecture_services(self):
        """
        Clean Architecture統合テスト - ファイル依存性なし
        - AgentOrchestratorがClean Architecture layersと正しく統合されることを検証
        """
        # Arrange
        from unittest.mock import MagicMock
        mock_message_broker = MagicMock()
        mock_gemini_service = MagicMock()
        mock_react_service = MagicMock()

        # Act
        orchestrator = AgentOrchestrator(
            agent_id="MODERATOR",
            mode="clean",
            message_broker=mock_message_broker,
            gemini_service=mock_gemini_service,
            react_service=mock_react_service
        )

        # Assert - AgentOrchestratorが適切に初期化されることを確認
        self.assertEqual(orchestrator.agent_id, "MODERATOR")
        self.assertEqual(orchestrator.mode, "clean")
        self.assertIsNotNone(orchestrator.message_broker)
        # 依存性注入されたサービスが正しく設定されていることを確認
        self.assertEqual(orchestrator.message_broker, mock_message_broker)

    def test_orchestrator_should_handle_message_processing_loop(self):
        """
        AgentOrchestratorはメッセージ処理のメインループを
        適切に管理する必要がある
        """
        # Arrange - mockを完全に実装
        orchestrator = AgentOrchestrator("MODERATOR", "clean")

        # Mock the _handle_message method directly
        with patch.object(orchestrator, '_handle_message') as mock_handle, \
                patch.object(orchestrator.message_broker, 'get_message') as \
                mock_get_message:

            # メッセージ処理シミュレーション：最初のメッセージでEXITを返す
            mock_get_message.side_effect = [
                Message(
                    sender_id="SYSTEM",
                    recipient_id="MODERATOR",
                    message_type="END_DEBATE",
                    payload={},
                    turn_id=1
                ),
                None  # 2回目の呼び出しではNone
            ]

            mock_handle.return_value = "EXIT"

            # Act - startメソッドを呼び出し
            orchestrator.start()

            # Assert
            mock_get_message.assert_called()
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
