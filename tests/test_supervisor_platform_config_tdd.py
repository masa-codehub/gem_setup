"""
TDD実装: Supervisor クラスのPlatformConfig対応テスト

Kent BeckのTDD思想に従い、SupervisorがPlatformConfigを使用するための
テストファーストでの実装
"""

import pytest
import tempfile
import os
import yaml

from main.frameworks_and_drivers.frameworks.platform_config import (
    PlatformConfig
)
from main.frameworks_and_drivers.drivers.supervisor import Supervisor


class TestSupervisorPlatformConfigTDD:
    """SupervisorクラスのPlatformConfig対応テスト"""

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
            'message_bus': {
                'type': 'sqlite',
                'db_path': 'test_messages.db'
            },
            'platform_config': {
                'data_storage_path': './test_runs',
                'message_db_path': 'test_messages.db',
                'agent_config_path': './test_config'
            }
        }

    def test_supervisor_can_accept_platform_config_object(self):
        """� GREEN: SupervisorがPlatformConfigオブジェクトを受け取れる"""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as f:
            yaml.dump(self.test_config, f)
            config_path = f.name

        try:
            platform_config = PlatformConfig(config_path)

            # Act
            supervisor = Supervisor(platform_config)

            # Assert
            assert supervisor is not None
            assert supervisor.platform_config == platform_config
            assert supervisor.project_def == platform_config.project_definition
        finally:
            os.unlink(config_path)

    def test_supervisor_uses_platform_config_for_message_bus_path(self):
        """� GREEN: SupervisorがPlatformConfigからメッセージバスのパスを取得する"""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as f:
            yaml.dump(self.test_config, f)
            config_path = f.name

        try:
            platform_config = PlatformConfig(config_path)

            # Act
            supervisor = Supervisor(platform_config)
            supervisor.initialize_message_bus()
            
            # Assert
            expected_db_path = platform_config.message_db_path
            assert supervisor.message_bus.db_path == expected_db_path
        finally:
            os.unlink(config_path)

    def test_supervisor_resolves_agent_config_paths_from_platform_config(self):
        """🔴 RED: Supervisorがエージェント設定のパスをPlatformConfigから解決する"""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as f:
            yaml.dump(self.test_config, f)
            config_path = f.name

        try:
            platform_config = PlatformConfig(config_path)  # noqa: F841

            # Act & Assert
            # 実装が完了すると、以下のようなテストが可能になる
            # supervisor = Supervisor(platform_config)
            # expected_config_path = platform_config.agent_config_path
            # assert supervisor.agent_config_path == expected_config_path
            
            pytest.skip("Agent config path resolution not implemented yet")
        finally:
            os.unlink(config_path)

    def test_supervisor_backward_compatibility_with_file_path(self):
        """🔴 RED: Supervisorは既存のファイルパス引数との後方互換性を保つ"""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as f:
            yaml.dump(self.test_config, f)
            config_path = f.name

        try:
            # Act
            # 既存のAPIは引き続き動作する必要がある
            supervisor = Supervisor(config_path)

            # Assert
            assert supervisor is not None
            assert supervisor.project_def == self.test_config
        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
