"""
Platform Supervisor - TDD Refactor Phase
Kent BeckのTDD思想に従い、Green Phaseの後にコードを改善
Clean Code原則を適用し、保守性と可読性を向上
"""
import yaml
import subprocess
import os
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from main.frameworks_and_drivers.frameworks.message_broker import (
    SqliteMessageBroker
)
from main.frameworks_and_drivers.frameworks.platform_config import (
    PlatformConfig
)
from main.entities.models import Message


class Supervisor:
    """
    プラットフォームスーパーバイザー - エージェントプロセスのライフサイクル管理

    run_debate.shと同等の機能を提供し、Kent BeckのTDD思想に基づいて
    テストファーストで開発されたClean Architectureの実装
    """

    def __init__(self, config: Union[str, PlatformConfig]):
        """
        プロジェクト定義またはPlatformConfigからスーパーバイザーを初期化

        Args:
            config: YAMLプロジェクト定義ファイルのパス、またはPlatformConfigオブジェクト
        """
        if isinstance(config, str):
            # 後方互換性: ファイルパスを受け取る場合
            self._load_project_definition(config)
            self.platform_config = None
            self.config = None  # TDD: テストが期待するプロパティを追加
        elif isinstance(config, PlatformConfig):
            # 新しい方式: PlatformConfigオブジェクトを受け取る場合
            self.project_def = config.project_definition
            self.platform_config = config
            self.config = config  # TDD: テストが期待するプロパティを追加
            # TDD Green Phase: エージェント設定パス解決機能を追加
            self.agent_config_path = config.agent_config_path
        else:
            raise TypeError(
                "config must be either a file path (str) or "
                "PlatformConfig object"
            )

        self._initialize_state()

    def _load_project_definition(self, project_file: str) -> None:
        """プロジェクト定義ファイルを読み込む"""
        with open(project_file, "r") as f:
            self.project_def = yaml.safe_load(f)

    def _initialize_state(self) -> None:
        """内部状態を初期化する"""
        self.agent_processes: List[subprocess.Popen] = []
        self.message_bus: Optional[SqliteMessageBroker] = None
        self.session_stats: Dict[str, Any] = {}
        self.config_validated: bool = False

    # ===== Core Message Bus Operations =====

    def initialize_message_bus(self) -> None:
        """A2Aメッセージバスを初期化する"""
        if self.platform_config:
            # PlatformConfigオブジェクトからパスを取得
            # message_db_pathがディレクトリなので、ファイルパスを構築
            db_path = self.platform_config.get_message_db_file_path()
        else:
            # 従来の方式（後方互換性）
            message_bus_config = self.project_def.get('message_bus', {})
            db_path = message_bus_config.get('db_path', 'messages.db')

        self.message_bus = SqliteMessageBroker(db_path)
        print(f"🔧 Database path: {db_path}")
        self.message_bus.initialize_db()
        print("🔧 Database initialized successfully")

    def _create_message(
        self, recipient_id: str, message_type: str,
        payload: Dict[str, Any], turn_id: int = 1
    ) -> Message:
        """メッセージオブジェクトを作成する（共通処理）"""
        return Message(
            sender_id="SYSTEM",
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            turn_id=turn_id
        )

    def _post_message(self, message: Message) -> None:
        """メッセージをバスに投函する（共通処理）"""
        if self.message_bus is None:
            raise ValueError("Message bus not initialized")
        self.message_bus.post_message(message)

    # ===== Agent Lifecycle Management =====

    def start(self) -> None:
        """プロジェクト定義に基づき、全エージェントを起動する"""
        # メッセージバスが初期化されていない場合は初期化
        if self.message_bus is None:
            self.initialize_message_bus()

        for agent_def in self.project_def['agents']:
            # 各エージェントを独立したプロセスとして起動
            cmd = [
                "python3", "-m", "main.agent_entrypoint",
                agent_def['id']
            ]

            # 環境変数の設定
            env = os.environ.copy()
            env['AGENT_ID'] = agent_def['id']

            proc = subprocess.Popen(cmd, env=env)
            self.agent_processes.append(proc)
            print(f"Launched agent: {agent_def['id']} (PID: {proc.pid})")

    def are_agents_running(self) -> bool:
        """エージェントプロセスが実行中かチェックする"""
        if not self.agent_processes:
            return False

        # 少なくとも1つのプロセスが実行中であればTrue
        for proc in self.agent_processes:
            if proc.poll() is None:  # プロセスが実行中
                return True
        return False

    def are_agents_ready(self) -> bool:
        """エージェントの準備状況を確認する"""
        return len(self.agent_processes) > 0

    def monitor(self) -> None:
        """エージェントプロセスを監視する（簡易実装）"""
        # 実際の監視ロジックは後で実装
        # 今はテストを通すための最小実装
        pass

    def shutdown(self) -> None:
        """全エージェントプロセスを終了させる"""
        for proc in self.agent_processes:
            if proc.poll() is None:  # まだ実行中の場合
                proc.terminate()
        print("All agents have been shut down.")

        # プロセスリストをクリア
        self.agent_processes.clear()

    # ===== Initial Message Posting Methods =====

    def post_initial_message(self, topic: str) -> None:
        """ディベート開始の初期メッセージを投函する"""
        if self.message_bus is None:
            raise ValueError("Message bus must be initialized.")

        # Moderatorにディベートのルールとトピックを説明させるためのメッセージ
        rules_text = ("This debate will proceed in turns. First, you will "
                      "explain the rules and topic. Then, you will ask "
                      "Debater A for their strategy.")

        initial_message = Message(
            sender_id="SYSTEM",
            recipient_id="MODERATOR",
            message_type="INITIATE_DEBATE",  # 新しいメッセージタイプ
            payload={
                "topic": topic,
                "rules": rules_text
            },
            turn_id=1
        )

        self.message_bus.post_message(initial_message)
        print("✅ Initial INITIATE_DEBATE message posted to MODERATOR.")

    def post_initial_message_with_metadata(self, topic: str) -> None:
        """メタデータを含む初期メッセージを投函する"""
        payload = {
            "topic": topic,
            "metadata": {"platform_version": "TDD-v1.0"},
            "session_id": f"session_{int(time.time())}",
            "timestamp": datetime.now().isoformat()
        }
        message = self._create_message(
            recipient_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload=payload
        )
        self._post_message(message)

    def post_initial_message_with_validation(self, topic: str) -> None:
        """エージェント準備確認付きの初期メッセージ投函"""
        if not self.are_agents_ready():
            raise RuntimeError("Agents not ready")
        self.post_initial_message(topic)

    def post_initial_messages_by_agent_type(self, topic: str) -> None:
        """エージェントタイプ別の初期メッセージ投函"""
        # MODERATORには司会開始メッセージ
        moderator_message = self._create_message(
            recipient_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": topic, "role": "moderator"}
        )
        self._post_message(moderator_message)

        # JUDGEには審査準備メッセージ
        for agent in self.project_def['agents']:
            if agent['type'] == 'judge':
                judge_message = self._create_message(
                    recipient_id=agent['id'],
                    message_type="PREPARE_FOR_JUDGMENT",
                    payload={"topic": topic, "role": "judge"}
                )
                self._post_message(judge_message)

    def post_initial_message_with_session(
        self, topic: str, session_config: Dict[str, Any]
    ) -> None:
        """セッション設定付きの初期メッセージ投函"""
        payload = {"topic": topic, "session_config": session_config}
        message = self._create_message(
            recipient_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload=payload
        )
        self._post_message(message)

    def post_initial_message_with_retry(
        self, topic: str, max_retries: int = 3
    ) -> None:
        """リトライ機能付きの初期メッセージ投函"""
        for attempt in range(max_retries):
            try:
                self.post_initial_message(topic)
                return
            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)  # 1秒待機してリトライ

    def post_initial_message_with_stats(self, topic: str) -> None:
        """統計機能付きの初期メッセージ投函"""
        start_time = datetime.now().isoformat()
        self.post_initial_message(topic)

        # 統計情報を記録
        self.session_stats = {
            'initial_messages_sent': 1,
            'session_start_time': start_time
        }

    def post_initial_message_with_config_validation(self, topic: str) -> None:
        """設定検証付きの初期メッセージ投函"""
        self._validate_project_config()
        self.config_validated = True
        self.post_initial_message(topic)

    # ===== Utility Methods =====

    def _validate_project_config(self) -> None:
        """プロジェクト設定の妥当性を検証する"""
        if len(self.project_def.get('agents', [])) == 0:
            raise ValueError("No agents defined")

    def get_initialization_stats(self) -> Dict[str, Any]:
        """初期化統計情報を取得"""
        return self.session_stats

    # ===== Scenario Management Methods (TDD Implementation) =====

    def kickoff_scenario(self) -> None:
        """
        シナリオを開始するために、最初のメッセージを投函する

        TDD Green Phase: テストを通す最小限の実装
        """
        if self.message_bus is None:
            raise ConnectionError("Message bus is not initialized.")

        # プロジェクト定義から初期タスクを取得
        initial_task = self.project_def.get('initial_task', {})
        topic = initial_task.get('topic', 'Default Topic')

        # Moderatorにディベートの開始を指示するメッセージ
        kickoff_message = Message(
            recipient_id="MODERATOR",
            sender_id="SYSTEM",
            message_type="INITIATE_DEBATE",
            payload={
                "topic": topic,
                "rules": "The debate will proceed according to the persona."
            },
            turn_id=1
        )
        self.message_bus.post_message(kickoff_message)
        print(
            f"🏁 Scenario kickoff message sent to MODERATOR with topic: '{topic}'")

    def monitor_for_shutdown(self, timeout_sec: int = 180) -> bool:
        """
        エージェントからのシャットダウン要求を監視する

        TDD Green Phase: テストを通す最小限の実装

        Args:
            timeout_sec: タイムアウト時間（秒）

        Returns:
            bool: シャットダウンメッセージを受信した場合True、タイムアウト時False
        """
        if self.message_bus is None:
            raise ConnectionError("Message bus is not initialized.")

        print("\n🗣️  Debate in progress. Monitoring for SHUTDOWN_SYSTEM message...")
        start_time = time.time()

        while time.time() - start_time < timeout_sec:
            # SUPERVISOR宛のメッセージを確認
            shutdown_msg = self.message_bus.get_message("SUPERVISOR")
            if shutdown_msg and shutdown_msg.message_type == "SHUTDOWN_SYSTEM":
                print(
                    f"✅ Received SHUTDOWN_SYSTEM from {shutdown_msg.sender_id}. Mission accomplished.")
                return True
            time.sleep(5)

        print("⏰ TIMEOUT: Shutdown message not received within the time limit.")
        return False

    def run_scenario(self, timeout_sec: int = 180) -> bool:
        """
        完全なシナリオを実行する

        1. エージェントを開始
        2. シナリオをキックオフ
        3. シャットダウンメッセージを監視
        4. エージェントを終了

        Args:
            timeout_sec: タイムアウト時間（秒）

        Returns:
            bool: シナリオが正常に完了した場合True
        """
        try:
            # 1. エージェントを開始
            print("🤖 Starting agent processes...")
            self.start()
            print("✅ All agents launched successfully")

            # エージェントが起動するまで少し待つ
            time.sleep(5)

            # 2. シナリオをキックオフ
            print("🏁 Starting scenario...")
            self.kickoff_scenario()

            # 3. シャットダウンメッセージを監視
            success = self.monitor_for_shutdown(timeout_sec)

            return success

        except Exception as e:
            print(f"❌ Error during scenario execution: {e}")
            return False
        finally:
            # 4. エージェントを終了
            print("🛑 Shutting down all agent processes.")
            self.shutdown()
