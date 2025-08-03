"""
エージェントのメッセージ処理機能の統合テスト

実際のエージェントプロセスを起動し、メッセージの送受信ができることを確認する
"""
import unittest
import tempfile
import os
import time
import yaml
import subprocess
import signal
from pathlib import Path
from main.frameworks_and_drivers.drivers.supervisor import Supervisor
from main.frameworks_and_drivers.frameworks.message_broker import SqliteMessageBroker
from main.entities.models import Message


class TestAgentMessageProcessing(unittest.TestCase):
    """エージェントのメッセージ処理統合テスト"""

    def setUp(self):
        """テスト環境のセットアップ"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(
            self.temp_dir, "config", "scenario_test")
        os.makedirs(self.config_dir, exist_ok=True)

        # テスト用のプロジェクト定義ファイルを作成
        self.project_file = os.path.join(self.temp_dir, "scenario_test.yml")
        self._create_test_project_file()

        # エージェント設定ファイルを作成
        self._create_agent_config_files()

        # メッセージDBパス
        self.db_path = os.path.join(self.temp_dir, "messages.db")

        # エージェントプロセスのリスト
        self.agent_processes = []

    def tearDown(self):
        """テスト環境のクリーンアップ"""
        # エージェントプロセスを終了
        for process in self.agent_processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_project_file(self):
        """テスト用のプロジェクト定義ファイルを作成"""
        project_config = {
            'platform_config': {
                'data_storage_path': os.path.join(self.temp_dir, "runs", "scenario_test"),
                'message_db_path': "./",
                'agent_config_path': self.config_dir
            },
            'agents': [
                {'id': 'MODERATOR', 'persona_file': 'moderator.md'},
                {'id': 'DEBATER_A', 'persona_file': 'debater_a.md'}
            ],
            'initial_task': {
                'topic': 'Test Topic for Agent Processing'
            }
        }

        with open(self.project_file, 'w') as f:
            yaml.dump(project_config, f, allow_unicode=True)

    def _create_agent_config_files(self):
        """簡単なテスト用エージェント設定ファイルを作成"""
        # MODERATOR設定 - シンプルなエコーテスト
        moderator_config = """# TEST MODERATOR
Test moderator that simply acknowledges messages.

# CORE LOGIC
- **INITIATE_DEBATE**: Acknowledge receipt and send test response.
"""

        # DEBATER_A設定 - シンプルなエコーテスト
        debater_a_config = """# TEST DEBATER_A  
Test debater that simply acknowledges messages.

# CORE LOGIC
- **REQUEST_STATEMENT**: Acknowledge receipt and send test response.
"""

        with open(os.path.join(self.config_dir, "moderator.md"), 'w') as f:
            f.write(moderator_config)

        with open(os.path.join(self.config_dir, "debater_a.md"), 'w') as f:
            f.write(debater_a_config)

    def test_agent_startup_and_basic_communication(self):
        """
        テスト: エージェントが起動し、基本的な通信ができる
        """
        # Given: スーパーバイザーが初期化されている
        supervisor = Supervisor(self.project_file)
        supervisor.initialize_message_bus()

        # When: エージェントを起動
        supervisor.start()
        self.agent_processes = supervisor.agent_processes

        # エージェントが起動するまで待機
        time.sleep(3)

        # Then: エージェントプロセスが起動している
        for process in self.agent_processes:
            self.assertIsNone(
                process.poll(), "Agent process should be running")

        # メッセージを送信してみる
        test_message = Message(
            sender_id="SYSTEM",
            recipient_id="MODERATOR",
            message_type="TEST_MESSAGE",
            payload={"test": "Hello"},
            turn_id=1
        )
        supervisor.message_bus.post_message(test_message)

        # メッセージが投函されたことを確認
        moderator_msg = supervisor.message_bus.get_message("MODERATOR")
        self.assertEqual(moderator_msg.message_type, "TEST_MESSAGE")

        # クリーンアップ
        supervisor.shutdown()


if __name__ == '__main__':
    unittest.main()
