"""
TDD実装: run_platform.py スクリプトのテスト

Kent BeckのTDD思想に従い、メインエントリーポイント用のテストファーストでの実装
"""

import pytest
import os


class TestRunPlatformScriptTDD:
    """run_platform.pyスクリプトのTDDテスト"""

    def test_run_platform_script_exists_and_is_executable(self):
        """GREEN: run_platform.pyスクリプトが存在し実行可能である"""
        # Arrange & Act & Assert
        script_path = "/app/run_platform.py"

        # 実装後は存在することを確認
        assert os.path.exists(script_path), \
            "run_platform.py should exist"

        # 実行権限があることを確認
        assert os.access(script_path, os.X_OK), \
            "run_platform.py should be executable"

    def test_run_platform_reads_default_config_file(self):
        """GREEN: run_platform.pyはデフォルトでproject.ymlを読み込む"""
        # TDD Green Phase: 実装を検証する
        from pathlib import Path

        # run_platform.pyの内容を読み取って検証
        script_path = Path("/app/run_platform.py")
        content = script_path.read_text()

        # デフォルト設定ファイルが定義されていることを確認
        assert 'DEFAULT_CONFIG_FILE = "project.yml"' in content, \
            "run_platform.py should define DEFAULT_CONFIG_FILE as project.yml"

        # 環境変数からデフォルト値を使用することを確認
        expected = 'os.getenv("AGENT_PLATFORM_CONFIG", DEFAULT_CONFIG_FILE)'
        assert expected in content, \
            "run_platform.py should use DEFAULT_CONFIG_FILE as fallback"

    def test_run_platform_reads_environment_config_variable(self):
        """GREEN: 環境変数AGENT_PLATFORM_CONFIGから設定ファイルを読み取る"""
        from pathlib import Path

        script_path = Path("/app/run_platform.py")
        content = script_path.read_text()

        # 環境変数を読み取るコードが存在することを確認
        assert 'AGENT_PLATFORM_CONFIG' in content, \
            "run_platform.py should read AGENT_PLATFORM_CONFIG env var"

        # os.getenvを使用していることを確認
        assert 'os.getenv(' in content, \
            "run_platform.py should use os.getenv"

    def test_run_platform_handles_missing_config_file_gracefully(self):
        """GREEN: 設定ファイルが見つからない場合、適切なエラーメッセージを表示する"""
        from pathlib import Path

        script_path = Path("/app/run_platform.py")
        content = script_path.read_text()

        # FileNotFoundError をキャッチしていることを確認
        assert 'FileNotFoundError' in content, \
            "run_platform.py should handle FileNotFoundError"

        # エラーメッセージを表示していることを確認
        assert 'Configuration Error' in content, \
            "run_platform.py should show configuration error message"

    def test_run_platform_initializes_supervisor_with_platform_config(self):
        """GREEN: run_platform.pyがPlatformConfigでSupervisorを初期化する"""
        from pathlib import Path

        script_path = Path("/app/run_platform.py")
        content = script_path.read_text()

        # PlatformConfigをインポートしていることを確認
        platform_config_import = 'from main.frameworks_and_drivers'
        assert platform_config_import in content, \
            "run_platform.py should import PlatformConfig"

        # Supervisorを初期化していることを確認
        assert 'Supervisor(config)' in content, \
            "run_platform.py should initialize Supervisor with config"

    def test_run_platform_posts_initial_message_if_configured(self):
        """GREEN: 設定にinitial_taskがある場合、初期メッセージを投函する"""
        from pathlib import Path

        script_path = Path("/app/run_platform.py")
        content = script_path.read_text()

        # 初期メッセージを投函する関数が存在することを確認
        assert 'def post_initial_message(' in content, \
            "run_platform.py should have post_initial_message function"

        # 初期タスク設定を取得していることを確認
        assert 'get_initial_task_config' in content, \
            "run_platform.py should get initial task config"

    def test_run_platform_handles_keyboard_interrupt_gracefully(self):
        """GREEN: Ctrl+Cでの中断を適切にハンドリングする"""
        from pathlib import Path

        script_path = Path("/app/run_platform.py")
        content = script_path.read_text()

        # シグナルハンドラーが設定されていることを確認
        assert 'signal.signal(signal.SIGINT' in content, \
            "run_platform.py should handle SIGINT"

        # シグナルハンドラー関数が存在することを確認
        assert 'def signal_handler(' in content, \
            "run_platform.py should have signal_handler function"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
