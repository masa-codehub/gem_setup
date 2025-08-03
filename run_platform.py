#!/usr/bin/env python3
"""
プラットフォーム統合起動スクリプト

Kent BeckのTDD思想に従って実装された設定ファイル外部化対応の
新しいプラットフォーム起動スクリプト

環境変数 AGENT_PLATFORM_CONFIG を読み取り、適切な設定で
Supervisorを起動する。
"""

from main.entities.models import Message
from main.frameworks_and_drivers.drivers.supervisor import Supervisor
from main.frameworks_and_drivers.frameworks.platform_config import (
    PlatformConfig
)
import os
import sys
import signal
from pathlib import Path

# プロジェクトルートを最初に追加
sys.path.insert(0, str(Path(__file__).parent))

# プロジェクトルート追加後にインポート

# デフォルトの設定ファイルパス
DEFAULT_CONFIG_FILE = "project.yml"

# グローバル変数でSupervisorインスタンスを保持（シグナルハンドラー用）
supervisor_instance = None


def signal_handler(signum, frame):
    """シグナルハンドラー - 適切にプラットフォームを終了"""
    global supervisor_instance
    print("\n🛑 Shutdown signal received...")

    if supervisor_instance:
        print("🧹 Shutting down supervisor...")
        try:
            supervisor_instance.shutdown()
        except Exception as e:
            print(f"⚠️  Error during shutdown: {e}")

    print("✨ Platform shutdown complete.")
    sys.exit(0)


def post_initial_message(supervisor: Supervisor, config: PlatformConfig):
    """初期メッセージを投函する"""
    initial_task = config.get_initial_task_config()

    if not initial_task:
        print("⚠️  No initial task configured. Skipping initial message.")
        return

    topic = initial_task.get('topic', 'Default debate topic')

    print(f"📬 Posting initial message with topic: '{topic}'")

    # 初期メッセージを作成して投函
    message = Message(
        sender_id='SYSTEM',
        recipient_id='MODERATOR',
        message_type='PROMPT_FOR_STATEMENT',
        payload={
            'topic': topic,
            'metadata': {
                'platform_version': 'TDD-v2.0',
                'config_source': config.config_path
            }
        },
        turn_id=1
    )

    supervisor.message_bus.post_message(message)
    print("✅ Initial message posted successfully")


def main():
    """
    プラットフォームのメインエントリーポイント。
    環境変数 `AGENT_PLATFORM_CONFIG` を読み取り、
    適切な設定でSupervisorを起動する。
    """
    global supervisor_instance

    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 1. 環境変数から設定ファイルパスを取得
    config_file_path = os.getenv("AGENT_PLATFORM_CONFIG", DEFAULT_CONFIG_FILE)
    print("🏛️ Agent Collaboration Platform Starting...")
    print(f"🔌 Loading configuration from: {config_file_path}")

    try:
        # 2. 設定を読み込み、オブジェクトを生成
        config = PlatformConfig(config_file_path)
        print("✅ Configuration loaded successfully")

        # 3. Supervisorを初期化
        print("🚀 Initializing Supervisor...")
        supervisor = Supervisor(config)
        supervisor_instance = supervisor  # グローバル変数に保存

        # 4. メッセージバスを初期化
        print("📬 Initializing A2A Message Bus...")
        supervisor.initialize_message_bus()
        print("✅ Message Bus initialized successfully")

        # 5. エージェントプロセスを起動
        print("🤖 Starting agent processes...")
        supervisor.start()
        print("✅ All agents launched successfully")

        # 6. 初期メッセージを投函（設定されている場合）
        post_initial_message(supervisor, config)

        # 7. 監視ループを開始
        print("👁️  Starting monitoring loop...")
        print("Press Ctrl+C to stop the platform")
        print("-" * 50)

        supervisor.monitor()

    except FileNotFoundError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        print("💡 Make sure the configuration file exists", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"💥 An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if supervisor_instance:
            print("🛑 Final cleanup...")
            try:
                supervisor_instance.shutdown()
            except Exception as e:
                print(f"⚠️  Error during final cleanup: {e}")


if __name__ == "__main__":
    main()
