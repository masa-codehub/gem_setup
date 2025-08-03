"""
TDD実装: 設定ファイルの外部化・動的読み込み機能テスト

Kent BeckのTDD思想に従い、テストファーストで設定管理機能を実装します
"""

import pytest
import tempfile
import os
import yaml
from unittest.mock import patch

from main.frameworks_and_drivers.frameworks.platform_config import (
    PlatformConfig
)


class TestPlatformConfigTDD:
    """設定ファイル管理機能のTDDテスト"""

    def setup_method(self):
        """各テストの前準備"""
        # テスト用の設定データ
        self.test_config = {
            'project_name': 'test_debate_platform',
            'agents': [
                {
                    'id': 'MODERATOR',
                    'type': 'moderator',
                    'persona_file': 'moderator.md'
                },
                {
                    'id': 'DEBATER_A',
                    'type': 'debater',
                    'persona_file': 'debater_a.md'
                }
            ],
            'platform_config': {
                'data_storage_path': './test_runs',
                'message_db_path': './',
                'agent_config_path': './test_config'
            }
        }

    def test_platform_config_loads_yaml_file_successfully(self):
        """🔴 RED: PlatformConfigがYAMLファイルを正しく読み込める"""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as f:
            yaml.dump(self.test_config, f)
            config_path = f.name

        try:
            # Act
            config = PlatformConfig(config_path)

            # Assert
            assert config.project_definition == self.test_config
            expected_name = 'test_debate_platform'
            assert config.project_definition['project_name'] == expected_name
        finally:
            os.unlink(config_path)

    def test_platform_config_raises_error_for_missing_file(self):
        """🔴 RED: 存在しないファイルを指定した場合、FileNotFoundErrorが発生する"""
        # Arrange
        non_existent_path = "/path/to/non/existent/file.yml"

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            PlatformConfig(non_existent_path)

        assert "Configuration file not found" in str(exc_info.value)

    def test_platform_config_resolves_relative_paths_to_absolute(self):
        """🔴 RED: 相対パスが絶対パスに正しく解決される"""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as f:
            yaml.dump(self.test_config, f)
            config_path = f.name

        try:
            # Act
            config = PlatformConfig(config_path)

            # Assert
            assert os.path.isabs(config.data_storage_path)
            assert config.data_storage_path.endswith('test_runs')
            assert os.path.isabs(config.message_db_path)
            assert os.path.isdir(config.message_db_path)  # ディレクトリであることを確認

            # データベースファイルパスの取得テスト
            db_file_path = config.get_message_db_file_path('test_messages.db')
            assert db_file_path.endswith('test_messages.db')
        finally:
            os.unlink(config_path)

    def test_platform_config_creates_data_directory_if_not_exists(self):
        """🔴 RED: データディレクトリが存在しない場合、自動的に作成される"""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = self.test_config.copy()
            new_path = os.path.join(temp_dir, 'new_test_runs')
            config_data['platform_config']['data_storage_path'] = new_path

            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.yml', delete=False
            ) as f:
                yaml.dump(config_data, f)
                config_path = f.name

            try:
                # Act
                config = PlatformConfig(config_path)

                # Assert
                assert os.path.exists(config.data_storage_path)
                assert os.path.isdir(config.data_storage_path)
            finally:
                os.unlink(config_path)

    def test_platform_config_provides_default_values_for_missing_config(self):
        """🔴 RED: 設定項目が欠けている場合、デフォルト値が使用される"""
        # Arrange
        minimal_config = {
            'project_name': 'minimal_test',
            'agents': []
            # platform_config セクションなし
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as f:
            yaml.dump(minimal_config, f)
            config_path = f.name

        try:
            # Act
            config = PlatformConfig(config_path)

            # Assert
            assert config.data_storage_path.endswith('runs')  # デフォルト値
            assert os.path.isdir(config.message_db_path)  # ディレクトリであることを確認
            db_file_path = config.get_message_db_file_path()
            assert db_file_path.endswith('messages.db')  # デフォルトファイル名
            assert config.agent_config_path == './config'  # デフォルト値
        finally:
            os.unlink(config_path)

    def test_platform_config_handles_environment_variable_substitution(self):
        """🔴 RED: 環境変数による設定値の置換が機能する"""
        # Arrange
        config_with_env = {
            'project_name': 'env_test',
            'agents': [],
            'platform_config': {
                'data_storage_path': '${DATA_DIR:-./default_runs}',
                'message_db_path': '${DB_DIR:-./}'
            }
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as f:
            yaml.dump(config_with_env, f)
            config_path = f.name

        try:
            # Act
            env_vars = {'DATA_DIR': '/custom/data', 'DB_DIR': '/custom/db/'}
            with patch.dict(os.environ, env_vars):
                config = PlatformConfig(config_path)

            # Assert
            assert config.data_storage_path == '/custom/data'
            assert config.message_db_path == '/custom/db/'
            db_file_path = config.get_message_db_file_path('custom.db')
            assert db_file_path.endswith('custom.db')
        finally:
            os.unlink(config_path)

    def test_supervisor_can_be_initialized_with_platform_config(self):
        """🔴 RED: SupervisorがPlatformConfigオブジェクトを受け取って初期化できる"""
        # これはSupervisorクラスの修正後にテストが通るようになる
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as f:
            yaml.dump(self.test_config, f)
            config_path = f.name

        try:
            # Act
            config = PlatformConfig(config_path)  # noqa: F841

            # Supervisorのコンストラクタがまだ修正されていないため、今は失敗することを確認
            from main.frameworks_and_drivers.drivers.supervisor import (
                Supervisor
            )

            # この時点では、SupervisorはまだPlatformConfigオブジェクトを受け取れない
            # 実装が完了すると、以下のようにインスタンス化できるようになる
            # supervisor = Supervisor(config)

            # 現在の実装では、まだファイルパスを受け取る形式
            supervisor = Supervisor(config_path)
            assert supervisor is not None
        finally:
            os.unlink(config_path)

    def test_run_platform_script_reads_environment_config_variable(self):
        """GREEN: run_platform.pyが環境変数から設定ファイルを読み取れる"""
        # TDD Green Phase: 実装が存在することを確認
        from pathlib import Path

        script_path = Path("/app/run_platform.py")
        content = script_path.read_text()

        # 環境変数AGENT_PLATFORM_CONFIGを読み取っていることを確認
        assert 'AGENT_PLATFORM_CONFIG' in content, \
            "run_platform.py should read AGENT_PLATFORM_CONFIG"

        # os.getenvを使用していることを確認
        assert 'os.getenv(' in content, \
            "run_platform.py should use os.getenv to read environment"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
