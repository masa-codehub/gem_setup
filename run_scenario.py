#!/usr/bin/env python3
"""
シナリオ実行スクリプト

Kent BeckのTDD思想に従って実装された2エージェント構成のシナリオテスト実行スクリプト

使用方法:
    python run_scenario.py --project_file project.yml
"""

from main.frameworks_and_drivers.drivers.supervisor import Supervisor
from main.frameworks_and_drivers.frameworks.platform_config import PlatformConfig
import argparse
import sys
import os
from pathlib import Path

# プロジェクトルートを最初に追加
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description="シナリオテスト実行スクリプト"
    )
    parser.add_argument(
        "--project_file",
        default="project.yml",
        help="プロジェクト定義ファイルのパス (デフォルト: project.yml)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="シナリオのタイムアウト時間（秒）(デフォルト: 180)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🎯 シナリオテスト実行開始")
    print("=" * 60)
    print(f"📋 プロジェクトファイル: {args.project_file}")
    print(f"⏰ タイムアウト: {args.timeout}秒")
    print()

    try:
        # 1. プラットフォーム設定を読み込み（ベースディレクトリ取得のため）
        print("📋 Loading project configuration...")
        temp_platform_config = PlatformConfig(args.project_file)
        print("✅ Configuration loaded successfully")

        # シナリオ実行用のタイムスタンプ付きディレクトリを作成
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        # 設定ファイルからベースディレクトリを取得
        scenario_config = temp_platform_config.project_definition.get(
            'scenario_config', {}
        )
        runs_base_dir = scenario_config.get('runs_base_dir', 'scenario_runs')
        scenario_dir = f"{runs_base_dir}/{timestamp}"

        os.makedirs(scenario_dir, exist_ok=True)

        # 環境変数を設定
        os.environ["DEBATE_DIR"] = scenario_dir

        print(f"📁 シナリオ実行ディレクトリ: {scenario_dir}")
        print(f"📋 ベースディレクトリ設定: {runs_base_dir}")

        # 2. 環境変数設定後にPlatformConfigを再初期化
        print("🔄 Reloading configuration with environment variables...")
        platform_config = PlatformConfig(args.project_file)

        # 3. メッセージDBの完全パスを環境変数として設定
        message_db_path = platform_config.get_message_db_file_path()
        os.environ["MESSAGE_DB_PATH"] = message_db_path
        print(f"🔧 Message DB Path: {message_db_path}")

        # 2. スーパーバイザーを初期化（PlatformConfigオブジェクトを渡す）
        print("🚀 Initializing Supervisor...")
        supervisor = Supervisor(platform_config)

        # 3. メッセージバスを初期化
        print("📬 Initializing A2A Message Bus...")
        supervisor.initialize_message_bus()
        print("✅ Message Bus initialized successfully")

        # 4. シナリオを実行
        print("\n" + "=" * 60)
        print("🎬 シナリオ実行開始")
        print("=" * 60)

        success = supervisor.run_scenario(timeout_sec=args.timeout)

        print("\n" + "=" * 60)
        if success:
            print("✅ シナリオが正常に完了しました！")
            print("🎉 Mission Accomplished!")
        else:
            print("❌ シナリオがタイムアウトまたはエラーで終了しました")
            return 1
        print("=" * 60)

        return 0

    except FileNotFoundError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        print("💡 プロジェクトファイルが存在することを確認してください", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"💥 予期しないエラーが発生しました: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
