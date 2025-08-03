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
    """SupervisorのPlatformConfig対応をテストするクラス"""

    def test_supervisor_can_accept_platform_config_object(self):
        """GREEN: SupervisorがPlatformConfigオブジェクトを受け入れる"""
        # Arrange
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.yml', delete=False
        ) as config_file:
            config_data = {
                "platform_config": {
                    "data_storage_path": "/tmp/test_data",
                    "message_db_path": "/tmp/test_db"
                },
                "agents": [
                    {"id": "MODERATOR", "persona_file": "moderator.md"}
                ]
            }
            yaml.dump(config_data, config_file)
            config_path = config_file.name

        try:
            platform_config = PlatformConfig(config_path)

            # Act
            supervisor = Supervisor(platform_config)

            # Assert
            assert supervisor.platform_config == platform_config
            assert supervisor.config == platform_config  # テスト用プロパティ

        finally:
            os.unlink(config_path)

    def test_supervisor_uses_platform_config_for_message_bus_path(self):
        """GREEN: SupervisorがPlatformConfigからメッセージバスパスを使用する"""
        # Arrange
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.yml', delete=False
        ) as config_file:
            config_data = {
                "platform_config": {
                    "data_storage_path": "/tmp/test_supervisor_data",
                    "message_db_path": "/tmp/test_supervisor_db"
                },
                "agents": [
                    {"id": "MODERATOR", "persona_file": "moderator.md"}
                ]
            }
            yaml.dump(config_data, config_file)
            config_path = config_file.name

        try:
            platform_config = PlatformConfig(config_path)

            # Act
            supervisor = Supervisor(platform_config)
            supervisor.initialize_message_bus()

            # Assert
            expected_db_path = platform_config.get_message_db_file_path()
            assert supervisor.message_bus.db_path == expected_db_path
        finally:
            os.unlink(config_path)

    def test_supervisor_resolves_agent_config_paths_from_platform_config(self):
        """GREEN: SupervisorがPlatformConfigからエージェント設定パスを解決する"""
        # Arrange
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.yml', delete=False
        ) as config_file:
            config_data = {
                "platform_config": {
                    "data_storage_path": "/tmp/test_data",
                    "message_db_path": "/tmp/test_db",
                    "agent_config_path": "./config/test_scenario"
                },
                "agents": [
                    {"id": "MODERATOR", "persona_file": "moderator.md"}
                ]
            }
            yaml.dump(config_data, config_file)
            config_path = config_file.name

        try:
            platform_config = PlatformConfig(config_path)

            # Act
            supervisor = Supervisor(platform_config)

            # Assert
            expected_config_path = platform_config.agent_config_path
            assert supervisor.agent_config_path == expected_config_path
        finally:
            os.unlink(config_path)

    def test_supervisor_backward_compatibility_with_file_path(self):
        """GREEN: Supervisorは既存のファイルパス引数との後方互換性を保つ"""
        # Arrange
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False
        ) as config_file:
            test_config = {
                "agents": [
                    {"id": "MODERATOR", "persona_file": "moderator.md"}
                ]
            }
            yaml.dump(test_config, config_file)
            config_path = config_file.name

        try:
            # Act
            supervisor = Supervisor(config_path)

            # Assert
            assert supervisor is not None
            assert supervisor.project_def == test_config
        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
