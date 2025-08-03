"""
Platform Integration Test
新しいプラットフォーム全体の統合テスト
"""
import unittest
import tempfile
import os
import yaml
from unittest.mock import Mock, patch
from main.platform.supervisor import Supervisor


class TestPlatformIntegration(unittest.TestCase):
    """プラットフォーム全体の統合テスト"""

    def setUp(self):
        """テストの前準備"""
        # 統合テスト用のプロジェクト定義を作成
        self.integration_project_def = {
            'project_name': 'agent_platform_integration',
            'agents': [
                {'id': 'MODERATOR', 'type': 'moderator'},
                {'id': 'DEBATER_A', 'type': 'debater'},
                {'id': 'DEBATER_N', 'type': 'debater'}
            ],
            'message_bus': {
                'type': 'sqlite',
                'db_path': 'integration_test_messages.db'
            },
            'initial_task': {
                'type': 'debate',
                'topic': 'The benefits of AI for humanity'
            }
        }

        # 一時ファイルを作成
        self.temp_project_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        )
        yaml.dump(self.integration_project_def, self.temp_project_file)
        self.temp_project_file.close()

    def tearDown(self):
        """テストの後処理"""
        if os.path.exists(self.temp_project_file.name):
            os.unlink(self.temp_project_file.name)

        # テスト用DBファイルも削除
        test_db = 'integration_test_messages.db'
        if os.path.exists(test_db):
            os.unlink(test_db)

    @patch('subprocess.Popen')
    def test_platform_supervisor_full_lifecycle(self, mock_popen):
        """統合テスト: プラットフォームのフルライフサイクル"""
        # Arrange
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # プロセス実行中
        mock_popen.return_value = mock_process

        supervisor = Supervisor(self.temp_project_file.name)

        # Act & Assert: 段階的にライフサイクルをテスト

        # 1. メッセージバス初期化
        supervisor.initialize_message_bus()
        self.assertIsNotNone(supervisor.message_bus)

        # 2. エージェント起動
        supervisor.start()
        self.assertEqual(len(supervisor.agent_processes), 3)
        self.assertEqual(mock_popen.call_count, 3)

        # 3. 初期メッセージ投函
        supervisor.post_initial_message("The benefits of AI for humanity")
        message = supervisor.message_bus.get_message("MODERATOR")
        self.assertIsNotNone(message)
        self.assertEqual(message.message_type, "PROMPT_FOR_STATEMENT")

        # 4. プロセス監視
        self.assertTrue(supervisor.are_agents_running())

        # 5. 終了処理
        supervisor.shutdown()
        self.assertEqual(mock_process.terminate.call_count, 3)

    def test_platform_project_definition_validation(self):
        """プロジェクト定義の妥当性検証テスト"""
        # Arrange
        supervisor = Supervisor(self.temp_project_file.name)

        # Assert: プロジェクト定義が正しく読み込まれている
        self.assertEqual(
            supervisor.project_def['project_name'],
            'agent_platform_integration'
        )
        self.assertEqual(len(supervisor.project_def['agents']), 3)
        self.assertIn('message_bus', supervisor.project_def)
        self.assertIn('initial_task', supervisor.project_def)

    def test_message_bus_initialization_with_custom_db_path(self):
        """カスタムDBパスでのメッセージバス初期化テスト"""
        # Arrange
        supervisor = Supervisor(self.temp_project_file.name)

        # Act
        supervisor.initialize_message_bus()

        # Assert
        expected_db_path = 'integration_test_messages.db'
        self.assertTrue(
            supervisor.message_bus.db_path.endswith(expected_db_path))


if __name__ == '__main__':
    unittest.main()
