#!/usr/bin/env python3
"""
Platform Supervisor Main Script
エージェント連携プラットフォームのメインエントリーポイント
Kent BeckのTDD思想で開発された、汎用的なプラットフォーム
"""
import argparse
import signal
import sys
import time
from main.platform.supervisor import Supervisor


def signal_handler(signum, frame):
    """シグナルハンドラー - 適切にプラットフォームを終了"""
    print("\n🛑 Received termination signal. Shutting down platform...")
    sys.exit(0)


def main():
    """メインエントリーポイント"""
    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # コマンドライン引数解析
    parser = argparse.ArgumentParser(
        description="Agent Collaboration Platform Supervisor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python platform_supervisor.py project.yml
  python platform_supervisor.py --timeout 600 debate_project.yml
  python platform_supervisor.py --topic "AI Ethics" project.yml
        """
    )
    parser.add_argument(
        'project_file',
        help='YAML project definition file path'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Platform timeout in seconds (default: 300)'
    )
    parser.add_argument(
        '--topic',
        type=str,
        help='Override initial topic from command line'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    args = parser.parse_args()

    try:
        print("🏛️ Agent Collaboration Platform Starting...")
        print(f"📋 Project File: {args.project_file}")
        print(f"⏱️  Timeout: {args.timeout} seconds")
        if args.topic:
            print(f"📝 Topic Override: {args.topic}")
        print()

        # スーパーバイザー初期化
        supervisor = Supervisor(args.project_file)

        # メッセージバス初期化
        print("📬 Initializing A2A Message Bus...")
        supervisor.initialize_message_bus()
        print("✅ Message Bus initialized successfully")

        # エージェント起動
        print("🤖 Starting agent processes...")
        supervisor.start()
        print("✅ All agents launched successfully")

        # 初期メッセージ投函
        topic = args.topic or supervisor.project_def.get(
            'initial_task', {}).get('topic', 'Default Topic')
        print(f"📮 Posting initial message with topic: {topic}")
        supervisor.post_initial_message(topic)
        print("✅ Initial message posted")

        print()
        print("🎯 Platform is running. Monitoring agents...")
        print("   Press Ctrl+C to gracefully shutdown")
        print()

        # 監視ループ
        start_time = time.time()
        while time.time() - start_time < args.timeout:
            if not supervisor.are_agents_running():
                print("⚠️  All agents have terminated. Shutting down platform.")
                break

            if args.debug:
                elapsed = int(time.time() - start_time)
                print(
                    f"🔍 Debug: Platform running for {elapsed}s, {args.timeout - elapsed}s remaining")

            time.sleep(10)

        print("⏰ Platform timeout reached or agents completed. Shutting down...")

    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal. Shutting down platform...")
    except Exception as e:
        print(f"❌ Platform error: {e}")
        sys.exit(1)
    finally:
        # 清掃処理
        if 'supervisor' in locals():
            print("🧹 Cleaning up agent processes...")
            supervisor.shutdown()
        print("✅ Platform shutdown complete.")


if __name__ == "__main__":
    main()
