"""
CLI（エントリーポイント）のテスト
TDD: Red phase - 失敗するテストから始める
"""
import unittest
from unittest.mock import Mock, patch
from main.interfaces.cli import main


class TestCLI(unittest.TestCase):
    @patch('main.interfaces.cli.AgentOrchestrator')
    @patch('sys.argv', ['cli.py', 'MODERATOR', '--mode', 'clean'])
    def test_main_should_create_orchestrator_with_correct_parameters(
        self, mock_orchestrator_class
    ):
        """
        CLIは適切なパラメータでAgentOrchestratorを作成し、
        startメソッドを呼び出す必要がある
        """
        # Arrange
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        # Act
        main()

        # Assert
        mock_orchestrator_class.assert_called_once_with('MODERATOR', 'clean')
        mock_orchestrator.start.assert_called_once()

    @patch('main.interfaces.cli.AgentOrchestrator')
    @patch('sys.argv', ['cli.py', 'DEBATER_A'])
    def test_main_should_default_to_clean_mode(self, mock_orchestrator_class):
        """
        CLIはモードが指定されない場合、デフォルトで'clean'モードを使用する
        """
        # Arrange
        mock_orchestrator = Mock()
        mock_orchestrator_class.return_value = mock_orchestrator

        # Act
        main()

        # Assert
        mock_orchestrator_class.assert_called_once_with('DEBATER_A', 'clean')


if __name__ == '__main__':
    unittest.main()
