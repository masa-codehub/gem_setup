"""
Kent BeckのTDD思想に基づくシナリオ統合テスト

2エージェント（MODERATOR + DEBATER_A）によるシナリオテストを
TDDアプローチで実装する。

Red-Green-Refactorサイクル：
1. Red: 失敗するテストを書く
2. Green: テストが通る最小限の実装
3. Refactor: コードを改善
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


class TestScenarioIntegration(unittest.TestCase):
    """シナリオ統合テスト - 2エージェント構成"""

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
                'message_db_path': "./",
                'agent_config_path': self.config_dir
            },
            'agents': [
                {'id': 'MODERATOR', 'persona_file': 'moderator.md'},
                {'id': 'DEBATER_A', 'persona_file': 'debater_a.md'}
            ],
            'initial_task': {
                'topic': 'AIエージェントの自律的協調は、人間の創造性を拡張するか？'
            }
        }

        with open(self.project_file, 'w') as f:
            yaml.dump(project_config, f, allow_unicode=True)

    def _create_agent_config_files(self):
        """エージェント設定ファイルを作成"""
        # MODERATOR設定
        moderator_config = """# MISSION, VISION, VALUE
- **Mission**: 討論が公正、秩序、生産性を保つように進行させる。
- **Vision**: すべての参加者が最大限に能力を発揮できる、知的で安全な議論空間を創造する。
- **Value**: 公平性、明確性、時間厳守。

# PERSONA
あなたは厳格かつ公正な討論の司会者です。あなたの役割は、ルールを提示し、議論のフローを管理し、健全な対話を促進することです。

# CORE LOGIC
- **INITIATE_DEBATE**: このメッセージタイプを受け取ったら、ペイロードの`topic`と`rules`を基に、全参加者（このシナリオではDEBATER_A）に`DEBATE_BRIEFING`メッセージを送信し、次に`DEBATER_A`に`REQUEST_STATEMENT`メッセージを送信せよ。
- **SUBMIT_STATEMENT**: `DEBATER_A`からこのメッセージを受け取ったら、内容を確認し、次に**システムを終了させる**ために`recipient_id: "SUPERVISOR"`、`message_type: "SHUTDOWN_SYSTEM"`を持つメッセージを送信せよ。
"""

        # DEBATER_A設定
        debater_a_config = """# MISSION, VISION, VALUE
- **Mission**: 論理と証拠に基づき、与えられたテーマに対する説得力のある肯定的な主張を構築する。
- **Vision**: データと論理的推論が、複雑な問題に対するより良い理解と意思決定につながることを証明する。
- **Value**: 正確性、客観性、論理的一貫性。

# PERSONA
あなたは冷静で分析的な討論者です。あなたの強みは、感情に流されず、検証可能な事実とデータに基づいて議論を組み立てる能力です。

# CORE LOGIC
- **REQUEST_STATEMENT**: `MODERATOR`からこのメッセージを受け取ったら、あなたのペルソナに従い、討論のテーマに対する最初の主張を生成し、`SUBMIT_STATEMENT`メッセージとして`MODERATOR`に返信せよ。
"""

        with open(os.path.join(self.config_dir, "moderator.md"), 'w') as f:
            f.write(moderator_config)

        with open(os.path.join(self.config_dir, "debater_a.md"), 'w') as f:
            f.write(debater_a_config)

    def test_scenario_kickoff_functionality(self):
        """
        テスト: スーパーバイザーがシナリオをキックオフできる

        Red Phase: まず失敗するテストを書く
        このテストは最初は失敗する（kickoff_scenarioメソッドが存在しない）
        """
        # Given: スーパーバイザーが初期化されている
        supervisor = Supervisor(self.project_file)
        supervisor.initialize_message_bus()

        # When & Then: kickoff_scenarioメソッドが存在し、正常に実行できる
        # 現在は存在しないので、この行で失敗する
        supervisor.kickoff_scenario()

        # キックオフ後、メッセージが投函されているかを確認
        moderator_msg = supervisor.message_bus.get_message("MODERATOR")
        self.assertEqual(moderator_msg.message_type, "INITIATE_DEBATE")

    def test_supervisor_can_monitor_shutdown_messages(self):
        """
        テスト: スーパーバイザーがシャットダウンメッセージを監視できる

        Red Phase: まず失敗するテストを書く
        このテストは最初は失敗する（monitor_for_shutdownメソッドが存在しない）
        """
        # Given: スーパーバイザーが初期化されている
        supervisor = Supervisor(self.project_file)
        supervisor.initialize_message_bus()

        # When & Then: monitor_for_shutdownメソッドが存在し、正常に実行できる
        # 現在は存在しないので、この行で失敗する
        supervisor.monitor_for_shutdown(timeout_sec=1)

    def test_message_flow_scenario(self):
        """
        テスト: 完全なメッセージフローシナリオ

        このテストは以下の流れを検証する：
        1. SYSTEM -> MODERATOR (INITIATE_DEBATE)
        2. MODERATOR -> DEBATER_A (REQUEST_STATEMENT)  
        3. DEBATER_A -> MODERATOR (SUBMIT_STATEMENT)
        4. MODERATOR -> SUPERVISOR (SHUTDOWN_SYSTEM)
        """
        # Given: メッセージブローカーが初期化されている
        message_broker = SqliteMessageBroker(self.db_path)
        message_broker.initialize_db()

        # When: シナリオメッセージを順次投函する
        # 1. SYSTEM -> MODERATOR
        initiate_msg = Message(
            sender_id="SYSTEM",
            recipient_id="MODERATOR",
            message_type="INITIATE_DEBATE",
            payload={"topic": "Test Topic", "rules": "Test Rules"},
            turn_id=1
        )
        message_broker.post_message(initiate_msg)

        # 2. MODERATOR -> DEBATER_A
        request_msg = Message(
            sender_id="MODERATOR",
            recipient_id="DEBATER_A",
            message_type="REQUEST_STATEMENT",
            payload={"topic": "Test Topic"},
            turn_id=2
        )
        message_broker.post_message(request_msg)

        # 3. DEBATER_A -> MODERATOR
        submit_msg = Message(
            sender_id="DEBATER_A",
            recipient_id="MODERATOR",
            message_type="SUBMIT_STATEMENT",
            payload={"statement": "Test Statement"},
            turn_id=3
        )
        message_broker.post_message(submit_msg)

        # 4. MODERATOR -> SUPERVISOR
        shutdown_msg = Message(
            sender_id="MODERATOR",
            recipient_id="SUPERVISOR",
            message_type="SHUTDOWN_SYSTEM",
            payload={"reason": "Scenario Complete"},
            turn_id=4
        )
        message_broker.post_message(shutdown_msg)

        # Then: すべてのメッセージが正しく記録されている
        moderator_msg = message_broker.get_message("MODERATOR")
        self.assertEqual(moderator_msg.message_type, "INITIATE_DEBATE")

        debater_msg = message_broker.get_message("DEBATER_A")
        self.assertEqual(debater_msg.message_type, "REQUEST_STATEMENT")

        moderator_response = message_broker.get_message("MODERATOR")
        self.assertEqual(moderator_response.message_type, "SUBMIT_STATEMENT")

        supervisor_msg = message_broker.get_message("SUPERVISOR")
        self.assertEqual(supervisor_msg.message_type, "SHUTDOWN_SYSTEM")


if __name__ == '__main__':
    unittest.main()
