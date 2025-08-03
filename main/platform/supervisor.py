"""
Platform Supervisor - TDD Green Phase
Kent BeckのTDD思想に従い、テストを通すための最小限の実装
"""
import yaml
import subprocess
import os
from typing import List, Optional
from main.infrastructure.message_broker import SqliteMessageBroker
from main.domain.models import Message


class Supervisor:
    """プラットフォームスーパーバイザー - エージェントプロセスのライフサイクル管理"""

    def __init__(self, project_file: str):
        """
        プロジェクト定義ファイルからスーパーバイザーを初期化

        Args:
            project_file: YAMLプロジェクト定義ファイルのパス
        """
        with open(project_file, "r") as f:
            self.project_def = yaml.safe_load(f)

        self.agent_processes: List[subprocess.Popen] = []
        self.message_bus: Optional[SqliteMessageBroker] = None

    def initialize_message_bus(self) -> None:
        """A2Aメッセージバスを初期化する"""
        # プロジェクト定義からDB設定を取得
        message_bus_config = self.project_def.get('message_bus', {})
        db_path = message_bus_config.get('db_path', 'messages.db')

        self.message_bus = SqliteMessageBroker(db_path)
        self.message_bus.initialize_db()

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

    def post_initial_message(self, topic: str) -> None:
        """初期メッセージを投函する"""
        if self.message_bus is None:
            raise ValueError("Message bus not initialized")

        # MODERATORに討論開始メッセージを送信
        initial_message = Message(
            sender_id="SYSTEM",
            recipient_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": topic},
            turn_id=1
        )

        self.message_bus.post_message(initial_message)
