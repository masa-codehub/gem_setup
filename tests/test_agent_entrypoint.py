"""
Agent Entrypoint のTDDテスト
エージェントの標準化されたエントリーポイントテスト
"""
import unittest
import sys
from unittest.mock import Mock, patch
from main.agent_entrypoint import main as agent_main
from main.interfaces.agent_loop import AgentLoop


class TestAgentEntrypoint(unittest.TestCase):
    """エージェントエントリーポイントのTDDテスト"""

    @patch('main.agent_entrypoint.AgentLoop')
    @patch('sys.argv', ['agent_entrypoint.py', 'MODERATOR'])
    def test_entrypoint_should_create_agent_loop_with_correct_id(self, mock_agent_loop_class):
        """Red: エントリーポイントは正しいIDでAgentLoopを作成する必要がある"""
        # Arrange
        mock_agent_loop = Mock()
        mock_agent_loop_class.return_value = mock_agent_loop

        # Act
        agent_main()

        # Assert
        mock_agent_loop_class.assert_called_once_with('MODERATOR')
        mock_agent_loop.run.assert_called_once()

    @patch('main.agent_entrypoint.AgentLoop')
    @patch('sys.argv', ['agent_entrypoint.py', 'DEBATER_A'])
    def test_entrypoint_should_handle_different_agent_ids(self, mock_agent_loop_class):
        """Red: エントリーポイントは異なるエージェントIDを処理できる必要がある"""
        # Arrange
        mock_agent_loop = Mock()
        mock_agent_loop_class.return_value = mock_agent_loop

        # Act
        agent_main()

        # Assert
        mock_agent_loop_class.assert_called_once_with('DEBATER_A')

    @patch('sys.argv', ['agent_entrypoint.py'])
    def test_entrypoint_should_raise_error_when_no_agent_id(self):
        """Red: エージェントIDが指定されていない場合はエラーを起こす必要がある"""
        # Act & Assert
        with self.assertRaises(IndexError):
            agent_main()


if __name__ == '__main__':
    unittest.main()
