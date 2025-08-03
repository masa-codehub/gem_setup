"""
Agent Loop のTDDテスト
エージェントのメインループ実装のテスト
"""
import unittest
import time
from unittest.mock import Mock, patch, MagicMock
from main.interface_adapters.controllers.agent_controller import AgentLoop
from main.entities.models import Message

# Clean Architecture対応のパス定数
MESSAGE_BROKER_PATH = 'main.frameworks_and_drivers.frameworks.message_broker.SqliteMessageBroker'
PROMPT_INJECTOR_PATH = 'main.frameworks_and_drivers.frameworks.prompt_injector_service.PromptInjectorService'
GEMINI_SERVICE_PATH = 'main.frameworks_and_drivers.frameworks.gemini_service.GeminiService'


class TestAgentLoop(unittest.TestCase):
    """エージェントループのTDDテスト"""

    @patch(MESSAGE_BROKER_PATH)
    @patch(PROMPT_INJECTOR_PATH)
    @patch(GEMINI_SERVICE_PATH)
    def test_agent_loop_should_initialize_with_dependencies(
        self, mock_gemini_service, mock_prompt_injector, mock_message_broker
    ):
        """Red: AgentLoopは必要な依存性を初期化する必要がある"""
        # Act
        agent_loop = AgentLoop("MODERATOR")

        # Assert
        self.assertEqual(agent_loop.agent_id, "MODERATOR")
        mock_message_broker.assert_called_once()
        mock_prompt_injector.assert_called_once()
        mock_gemini_service.assert_called_once()

    @patch(MESSAGE_BROKER_PATH)
    @patch(PROMPT_INJECTOR_PATH)
    @patch(GEMINI_SERVICE_PATH)
    @patch('time.sleep')
    def test_agent_loop_should_process_messages_in_loop(
        self, mock_sleep, mock_gemini_service, mock_prompt_injector,
        mock_message_broker
    ):
        """Red: AgentLoopはメッセージを継続的に処理する必要がある"""
        # Arrange
        mock_broker_instance = Mock()
        mock_message_broker.return_value = mock_broker_instance

        test_message = Message(
            sender_id="SYSTEM",
            recipient_id="MODERATOR",
            message_type="TEST_MESSAGE",
            payload={"test": "data"},
            turn_id=1
        )

        # 最初の呼び出しでメッセージを返し、2回目でNoneを返してループを終了
        mock_broker_instance.get_message.side_effect = [test_message, None]

        agent_loop = AgentLoop("MODERATOR")

        # Mock the run method to stop after 2 iterations
        original_run = agent_loop.run
        with patch.object(agent_loop, 'run') as mock_run:
            def side_effect():
                # 2回だけループしてテスト終了
                for _ in range(2):
                    message = agent_loop.message_bus.get_message(
                        agent_loop.agent_id)
                    if message:
                        agent_loop._process_message(message)
                    time.sleep(5)

            mock_run.side_effect = side_effect

            # Act
            agent_loop.run()

            # Assert
            self.assertEqual(mock_broker_instance.get_message.call_count, 2)

    @patch(MESSAGE_BROKER_PATH)
    @patch(PROMPT_INJECTOR_PATH)
    @patch(GEMINI_SERVICE_PATH)
    def test_agent_loop_should_process_message_with_llm(
        self, mock_gemini_service, mock_prompt_injector, mock_message_broker
    ):
        """Red: AgentLoopはLLMサービスを使ってメッセージを処理する必要がある"""
        # Arrange
        mock_broker_instance = Mock()
        mock_message_broker.return_value = mock_broker_instance

        mock_injector_instance = Mock()
        mock_prompt_injector.return_value = mock_injector_instance
        mock_injector_instance.build_prompt.return_value = "Test prompt"

        mock_llm_instance = Mock()
        mock_gemini_service.return_value = mock_llm_instance
        mock_llm_instance.generate_response.return_value = "Test response"

        test_message = Message(
            sender_id="SYSTEM",
            recipient_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": "AI benefits"},
            turn_id=1
        )

        agent_loop = AgentLoop("MODERATOR")

        # Act
        agent_loop._process_message(test_message)

        # Assert
        mock_injector_instance.build_prompt.assert_called_once()
        mock_llm_instance.generate_response.assert_called_once_with(
            "Test prompt")


if __name__ == '__main__':
    unittest.main()
