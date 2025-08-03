"""
シンプルなモックエージェントを使ったシナリオテスト

実際のLLMサービスなし            'platform_config': {
                'data_storage_path': os.path.join(self.temp_dir, "runs", "scenario_test"),
                'message_db_path': "./", 
                'agent_config_path': self.config_dir
            },能な応答でシナリオフローをテストする
"""
import unittest
import tempfile
import os
import time
import yaml
from pathlib import Path
from main.frameworks_and_drivers.drivers.supervisor import Supervisor
from main.frameworks_and_drivers.frameworks.message_broker import SqliteMessageBroker
from main.entities.models import Message


class MockScenarioTest(unittest.TestCase):
    """モックエージェントを使ったシナリオテスト"""

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

        # メッセージDBパス
        self.db_path = os.path.join(self.temp_dir, "messages.db")

    def tearDown(self):
        """テスト環境のクリーンアップ"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_project_file(self):
        """テスト用のプロジェクト定義ファイルを作成"""
        project_config = {
            'platform_config': {
                'data_storage_path': os.path.join(self.temp_dir, "runs", "scenario_test"),
                'message_db_path': "messages.db",
                'agent_config_path': self.config_dir
            },
            'agents': [
                {'id': 'MODERATOR', 'persona_file': 'moderator.md'},
                {'id': 'DEBATER_A', 'persona_file': 'debater_a.md'}
            ],
            'initial_task': {
                'topic': 'Mock Scenario Test Topic'
            }
        }

        with open(self.project_file, 'w') as f:
            yaml.dump(project_config, f, allow_unicode=True)

    def test_mock_scenario_message_flow(self):
        """
        テスト: モックメッセージを使って完全なシナリオフローを模擬

        このテストでは実際のエージェントプロセスを起動せず、
        メッセージの流れを手動で模擬する
        """
        # Given: スーパーバイザーが初期化されている
        supervisor = Supervisor(self.project_file)
        supervisor.initialize_message_bus()

        # When: 1. シナリオをキックオフ
        supervisor.kickoff_scenario()

        # Then: 1. MODERATOR宛にINITIATE_DEBATEメッセージが送信される
        moderator_msg = supervisor.message_bus.get_message("MODERATOR")
        self.assertIsNotNone(moderator_msg)
        self.assertEqual(moderator_msg.message_type, "INITIATE_DEBATE")
        self.assertEqual(moderator_msg.sender_id, "SYSTEM")

        # Mock: 2. MODERATORがDEBATER_Aに REQUEST_STATEMENT を送信
        mock_request = Message(
            sender_id="MODERATOR",
            recipient_id="DEBATER_A",
            message_type="REQUEST_STATEMENT",
            payload={"topic": "Mock Scenario Test Topic"},
            turn_id=2
        )
        supervisor.message_bus.post_message(mock_request)

        # Mock: 3. DEBATER_AがMODERATORに SUBMIT_STATEMENT を送信
        mock_statement = Message(
            sender_id="DEBATER_A",
            recipient_id="MODERATOR",
            message_type="SUBMIT_STATEMENT",
            payload={"statement": "Mock statement from DEBATER_A"},
            turn_id=3
        )
        supervisor.message_bus.post_message(mock_statement)

        # Mock: 4. MODERATORがSUPERVISORに SHUTDOWN_SYSTEM を送信
        mock_shutdown = Message(
            sender_id="MODERATOR",
            recipient_id="SUPERVISOR",
            message_type="SHUTDOWN_SYSTEM",
            payload={"reason": "Mock scenario complete"},
            turn_id=4
        )
        supervisor.message_bus.post_message(mock_shutdown)

        # Then: 4. SUPERVISORがシャットダウンメッセージを受信できる
        shutdown_msg = supervisor.message_bus.get_message("SUPERVISOR")
        self.assertIsNotNone(shutdown_msg)
        self.assertEqual(shutdown_msg.message_type, "SHUTDOWN_SYSTEM")
        self.assertEqual(shutdown_msg.sender_id, "MODERATOR")

        # さらに確認: メッセージフローが正しい順序である
        # DEBATER_A宛のメッセージ
        debater_msg = supervisor.message_bus.get_message("DEBATER_A")
        self.assertEqual(debater_msg.message_type, "REQUEST_STATEMENT")

        # MODERATOR宛の追加メッセージ
        moderator_response = supervisor.message_bus.get_message("MODERATOR")
        self.assertEqual(moderator_response.message_type, "SUBMIT_STATEMENT")

    def test_monitor_for_shutdown_with_mock_message(self):
        """
        テスト: モックシャットダウンメッセージでmonitor_for_shutdownが正常に動作する
        """
        # Given: スーパーバイザーが初期化されている
        supervisor = Supervisor(self.project_file)
        supervisor.initialize_message_bus()

        # When: 事前にシャットダウンメッセージを投函
        shutdown_msg = Message(
            sender_id="MODERATOR",
            recipient_id="SUPERVISOR",
            message_type="SHUTDOWN_SYSTEM",
            payload={"reason": "Test shutdown"},
            turn_id=1
        )
        supervisor.message_bus.post_message(shutdown_msg)

        # Then: シャットダウンを監視する（短いタイムアウト）
        start_time = time.time()
        result = supervisor.monitor_for_shutdown(timeout_sec=10)
        end_time = time.time()

        # シャットダウンメッセージを受信して正常終了
        self.assertTrue(result)
        self.assertLess(end_time - start_time, 8)  # 8秒以内に終了


if __name__ == '__main__':
    unittest.main()
