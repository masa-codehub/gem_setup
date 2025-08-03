"""
Platform Supervisor のTDDテスト
Kent BeckのTDD思想に従い、Red → Green → Refactor の順で実装
"""
import unittest
import tempfile
import os
import yaml
from unittest.mock import Mock, patch
from main.platform.supervisor import Supervisor


class TestPlatformSupervisor(unittest.TestCase):
    """スーパーバイザーのTDDテスト - まずはRed（失敗）から始める"""

    def setUp(self):
        """テストの前準備"""
        # テスト用のプロジェクト定義ファイルを作成
        self.test_project_def = {
            'project_name': 'test_debate',
            'agents': [
                {'id': 'MODERATOR', 'type': 'moderator'},
                {'id': 'DEBATER_A', 'type': 'debater'},
                {'id': 'DEBATER_N', 'type': 'debater'}
            ],
            'message_bus': {
                'type': 'sqlite',
                'db_path': 'test_messages.db'
            }
        }

        # 一時ファイルにプロジェクト定義を保存
        self.temp_project_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        )
        yaml.dump(self.test_project_def, self.temp_project_file)
        self.temp_project_file.close()

    def tearDown(self):
        """テストの後処理"""
        if os.path.exists(self.temp_project_file.name):
            os.unlink(self.temp_project_file.name)

    def test_supervisor_should_load_project_definition(self):
        """Red: スーパーバイザーはプロジェクト定義を読み込める必要がある"""
        # Arrange & Act - まだSupervisorクラスは存在しない（Red）
        supervisor = Supervisor(self.temp_project_file.name)

        # Assert
        self.assertEqual(supervisor.project_def['project_name'], 'test_debate')
        self.assertEqual(len(supervisor.project_def['agents']), 3)

    def test_supervisor_should_initialize_message_bus(self):
        """Red: スーパーバイザーはメッセージバスを初期化できる必要がある"""
        # Arrange
        supervisor = Supervisor(self.temp_project_file.name)

        # Act & Assert - メッセージバスが初期化される
        supervisor.initialize_message_bus()
        self.assertIsNotNone(supervisor.message_bus)

    @patch('subprocess.Popen')
    def test_supervisor_should_start_all_agents(self, mock_popen):
        """Red: スーパーバイザーは全エージェントを起動できる必要がある"""
        # Arrange
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        supervisor = Supervisor(self.temp_project_file.name)

        # Act
        supervisor.start()

        # Assert - 各エージェントに対してプロセスが起動される
        self.assertEqual(mock_popen.call_count, 3)  # 3つのエージェント
        self.assertEqual(len(supervisor.agent_processes), 3)

    @patch('subprocess.Popen')
    def test_supervisor_should_monitor_agent_processes(self, mock_popen):
        """Red: スーパーバイザーはエージェントプロセスを監視できる必要がある"""
        # Arrange
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # プロセスが実行中
        mock_popen.return_value = mock_process

        supervisor = Supervisor(self.temp_project_file.name)
        supervisor.start()

        # Act
        is_running = supervisor.are_agents_running()

        # Assert
        self.assertTrue(is_running)

    @patch('subprocess.Popen')
    def test_supervisor_should_shutdown_all_agents(self, mock_popen):
        """Red: スーパーバイザーは全エージェントを終了できる必要がある"""
        # Arrange
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # プロセスが実行中
        mock_popen.return_value = mock_process

        supervisor = Supervisor(self.temp_project_file.name)
        supervisor.start()

        # Act
        supervisor.shutdown()

        # Assert - 全プロセスにterminateが呼ばれる
        self.assertEqual(mock_process.terminate.call_count, 3)

    def test_supervisor_should_post_initial_message(self):
        """Red: スーパーバイザーは初期メッセージを投函できる必要がある"""
        # Arrange
        supervisor = Supervisor(self.temp_project_file.name)
        supervisor.initialize_message_bus()

        # Act
        supervisor.post_initial_message("Test topic")

        # Assert - MODERATORにメッセージが送信される
        message = supervisor.message_bus.get_message("MODERATOR")
        self.assertIsNotNone(message)
        self.assertEqual(message.message_type, "INITIATE_DEBATE")


if __name__ == '__main__':
    unittest.main()
