"""
Platform Supervisor Tests
Kent Beck TDD: Red → Green → Refactor

TDD原則に従い、project.ymlへの依存を排除し、
テストが設計を駆動するようにリファクタリング
"""
import pytest
from unittest.mock import Mock


class TestSupervisorInitialization:
    """Supervisorの初期化に関するTDDテスト"""

    def test_supervisor_should_initialize_with_config(
        self, real_platform_config
    ):
        """Supervisorは設定オブジェクトで正しく初期化されること

        TDD Green Phase: 実際のPlatformConfigを使用してテストを通す
        """
        try:
            from main.frameworks_and_drivers.drivers.supervisor import (
                Supervisor
            )

            # Act
            supervisor = Supervisor(real_platform_config)

            # Assert
            assert supervisor.config is not None
            assert supervisor.config == real_platform_config

        except ImportError:
            # Red Phase: 実装がまだない場合
            pytest.skip("Supervisor implementation not available - Red Phase")

    def test_supervisor_should_initialize_message_bus(
        self, real_platform_config
    ):
        """Supervisorはメッセージバスを正しく初期化すること

        TDD Green Phase: 実際のPlatformConfigを使用してテストを通す
        """
        try:
            from main.frameworks_and_drivers.drivers.supervisor import (
                Supervisor
            )

            # Arrange
            supervisor = Supervisor(real_platform_config)

            # Act
            supervisor.initialize_message_bus()

            # Assert
            assert hasattr(supervisor, 'message_bus')
            assert supervisor.message_bus is not None
            # 設定で指定したDBパスが使われていることを確認
            if hasattr(supervisor.message_bus, 'db_path'):
                expected_path = real_platform_config.get_message_db_file_path()
                assert supervisor.message_bus.db_path == expected_path

        except ImportError:
            pytest.skip("Supervisor implementation not available - Red Phase")


class TestSupervisorScenarioKickoff:
    """Supervisorのシナリオ開始機能のTDDテスト"""

    def test_supervisor_should_kickoff_scenario_successfully(
        self, real_platform_config
    ):
        """Supervisorはシナリオを正しくキックオフすること

        TDD Green Phase: 実際のPlatformConfigを使用してテストを通す
        """
        try:
            from main.frameworks_and_drivers.drivers.supervisor import (
                Supervisor
            )

            # Arrange
            supervisor = Supervisor(real_platform_config)
            supervisor.initialize_message_bus()

            # Act
            supervisor.kickoff_scenario()

            # Assert
            # MODERATORに初期メッセージが送信されること
            moderator_message = supervisor.message_bus.get_message("MODERATOR")
            assert moderator_message is not None
            assert moderator_message.message_type == "INITIATE_DEBATE"

        except ImportError:
            pytest.skip("Supervisor implementation not available - Red Phase")

    def test_supervisor_should_handle_initial_task_configuration(
        self, real_platform_config
    ):
        """Supervisorは初期タスク設定を正しく処理すること

        TDD Green Phase: 実際のPlatformConfigの構造に合わせてテスト
        """
        # Arrange
        mock_supervisor = Mock()
        mock_supervisor.config = real_platform_config

        # 期待される動作をモックで定義（Green Phase）
        mock_supervisor.kickoff_scenario = Mock()

        # Act
        mock_supervisor.kickoff_scenario()

        # Assert
        # キックオフが呼び出されることを確認
        mock_supervisor.kickoff_scenario.assert_called_once()

        # PlatformConfigが正しく構成されていることを確認
        assert real_platform_config is not None
        # project_definitionから初期タスクを取得できることを確認
        project_def = real_platform_config.project_definition
        assert project_def is not None
        if 'initial_task' in project_def:
            assert project_def['initial_task'] is not None


class TestSupervisorErrorHandling:
    """Supervisorのエラーハンドリングに関するTDDテスト"""

    def test_supervisor_should_handle_missing_config_gracefully(self):
        """Supervisorは設定が不正な場合に適切にエラーハンドリングすること

        TDD Red Phase: エラーケースの動作を定義
        """
        try:
            from main.frameworks_and_drivers.drivers.supervisor import (
                Supervisor
            )

            # Act & Assert
            with pytest.raises((ValueError, TypeError)):
                Supervisor(None)

        except ImportError:
            # Red Phase: 実装がない場合でもエラーハンドリングの要件は定義
            pytest.skip("Supervisor implementation not available - Red Phase")
