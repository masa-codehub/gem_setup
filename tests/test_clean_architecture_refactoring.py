"""
Kent BeckのTDD思想に基づくクリーンアーキテクチャリファクタリング統合テスト

Red-Green-Refactorサイクルで新しいディレクトリ構造をテスト駆動で実装
"""

import pytest
from pathlib import Path


class TestCleanArchitectureStructure:
    """新しいクリーンアーキテクチャ構造のテスト（Red Phase）"""

    def test_entities_layer_exists(self):
        """🔴 RED: entities層が存在する"""
        entities_path = Path("/app/main/entities")
        assert entities_path.exists(), "entities directory should exist"
        init_file = entities_path / "__init__.py"
        assert init_file.exists(), "entities should be a Python package"

    def test_use_cases_layer_exists(self):
        """🔴 RED: use_cases層が存在する"""
        use_cases_path = Path("/app/main/use_cases")
        assert use_cases_path.exists(), "use_cases directory should exist"
        init_file = use_cases_path / "__init__.py"
        assert init_file.exists(), "use_cases should be a Python package"

    def test_interface_adapters_layer_exists(self):
        """🔴 RED: interface_adapters層が存在する"""
        adapters_path = Path("/app/main/interface_adapters")
        assert adapters_path.exists(), \
            "interface_adapters directory should exist"
        init_file = adapters_path / "__init__.py"
        assert init_file.exists(), \
            "interface_adapters should be a Python package"

    def test_frameworks_and_drivers_layer_exists(self):
        """🔴 RED: frameworks_and_drivers層が存在する"""
        frameworks_path = Path("/app/main/frameworks_and_drivers")
        assert frameworks_path.exists(), \
            "frameworks_and_drivers directory should exist"
        init_file = frameworks_path / "__init__.py"
        assert init_file.exists(), \
            "frameworks_and_drivers should be a Python package"

    def test_controllers_sublayer_exists(self):
        """🔴 RED: interface_adapters/controllers サブレイヤが存在する"""
        controllers_path = Path("/app/main/interface_adapters/controllers")
        assert controllers_path.exists(), "controllers directory should exist"
        init_file = controllers_path / "__init__.py"
        assert init_file.exists(), "controllers should be a Python package"

    def test_presenters_sublayer_exists(self):
        """🔴 RED: interface_adapters/presenters サブレイヤが存在する"""
        presenters_path = Path("/app/main/interface_adapters/presenters")
        assert presenters_path.exists(), "presenters directory should exist"
        init_file = presenters_path / "__init__.py"
        assert init_file.exists(), "presenters should be a Python package"

    def test_drivers_sublayer_exists(self):
        """🔴 RED: frameworks_and_drivers/drivers サブレイヤが存在する"""
        drivers_path = Path("/app/main/frameworks_and_drivers/drivers")
        assert drivers_path.exists(), "drivers directory should exist"
        init_file = drivers_path / "__init__.py"
        assert init_file.exists(), "drivers should be a Python package"

    def test_frameworks_sublayer_exists(self):
        """🔴 RED: frameworks_and_drivers/frameworks サブレイヤが存在する"""
        base_path = "/app/main/frameworks_and_drivers/frameworks"
        frameworks_path = Path(base_path)
        assert frameworks_path.exists(), "frameworks directory should exist"
        init_file = frameworks_path / "__init__.py"
        assert init_file.exists(), "frameworks should be a Python package"

    def test_external_interfaces_sublayer_exists(self):
        """🔴 RED: frameworks_and_drivers/external_interfaces サブレイヤが存在する"""
        base_path = "/app/main/frameworks_and_drivers/external_interfaces"
        external_path = Path(base_path)
        assert external_path.exists(), \
            "external_interfaces directory should exist"
        init_file = external_path / "__init__.py"
        assert init_file.exists(), \
            "external_interfaces should be a Python package"


class TestFilesMigration:
    """ファイルの正しい配置のテスト（Red Phase）"""

    def test_entities_models_file_exists(self):
        """🔴 RED: entities/models.py が存在する"""
        models_path = Path("/app/main/entities/models.py")
        assert models_path.exists(), "entities/models.py should exist"

    def test_use_cases_interfaces_exist(self):
        """🔴 RED: use_cases/interfaces/ が存在する"""
        interfaces_path = Path("/app/main/use_cases/interfaces")
        assert interfaces_path.exists(), \
            "use_cases/interfaces directory should exist"
        init_file = interfaces_path / "__init__.py"
        assert init_file.exists(), \
            "use_cases/interfaces should be a Python package"

    def test_use_cases_debate_use_cases_exists(self):
        """🔴 RED: use_cases/debate_use_cases.py が存在する"""
        debate_cases_path = Path("/app/main/use_cases/debate_use_cases.py")
        assert debate_cases_path.exists(), \
            "use_cases/debate_use_cases.py should exist"

    def test_agent_controller_exists(self):
        """🔴 RED: agent_controller.py (旧 agent_loop.py) が適切な場所に存在する"""
        base_path = "/app/main/interface_adapters/controllers"
        controller_path = Path(f"{base_path}/agent_controller.py")
        assert controller_path.exists(), \
            "agent_controller.py should exist in controllers"

    def test_cli_presenter_exists(self):
        """🔴 RED: cli_presenter.py が存在する"""
        base_path = "/app/main/interface_adapters/presenters"
        presenter_path = Path(f"{base_path}/cli_presenter.py")
        assert presenter_path.exists(), \
            "cli_presenter.py should exist in presenters"

    def test_supervisor_in_drivers(self):
        """🔴 RED: supervisor.py がドライバー層に存在する"""
        base_path = "/app/main/frameworks_and_drivers/drivers"
        supervisor_path = Path(f"{base_path}/supervisor.py")
        assert supervisor_path.exists(), \
            "supervisor.py should exist in drivers"

    def test_frameworks_in_correct_location(self):
        """🔴 RED: フレームワーク関連ファイルが正しい場所に存在する"""
        base_path = "/app/main/frameworks_and_drivers/frameworks"
        message_broker_path = Path(f"{base_path}/message_broker.py")
        gemini_service_path = Path(f"{base_path}/gemini_service.py")
        file_repository_path = Path(f"{base_path}/file_repository.py")

        assert message_broker_path.exists(), \
            "message_broker.py should exist in frameworks"
        assert gemini_service_path.exists(), \
            "gemini_service.py should exist in frameworks"
        assert file_repository_path.exists(), \
            "file_repository.py should exist in frameworks"

    def test_cli_in_external_interfaces(self):
        """🔴 RED: cli.py が外部インターフェース層に存在する"""
        base_path = "/app/main/frameworks_and_drivers/external_interfaces"
        cli_path = Path(f"{base_path}/cli.py")
        assert cli_path.exists(), \
            "cli.py should exist in external_interfaces"


class TestImportIntegrity:
    """新しい構造でのインポートが正しく動作することのテスト（Red Phase）"""

    def test_entities_can_be_imported(self):
        """🔴 RED: entities.models からドメインモデルをインポートできる"""
        try:
            from main.entities.models import Message, AgentID
            assert Message is not None
            assert AgentID is not None
        except ImportError as e:
            pytest.fail(f"Could not import from entities.models: {e}")

    def test_use_cases_interfaces_can_be_imported(self):
        """🔴 RED: use_cases.interfaces からインターフェースをインポートできる"""
        try:
            from main.use_cases.interfaces import IMessageBroker, ILLMService
            assert IMessageBroker is not None
            assert ILLMService is not None
        except ImportError as e:
            pytest.fail(f"Could not import from use_cases.interfaces: {e}")

    def test_use_cases_can_be_imported(self):
        """🔴 RED: use_cases.debate_use_cases からユースケースをインポートできる"""
        try:
            from main.use_cases.debate_use_cases import SubmitStatementUseCase
            assert SubmitStatementUseCase is not None
        except ImportError as e:
            msg = f"Could not import from use_cases.debate_use_cases: {e}"
            pytest.fail(msg)

    def test_controllers_can_be_imported(self):
        """🔴 RED: controllers からコントローラーをインポートできる"""
        try:
            from main.interface_adapters.controllers.agent_controller import AgentController  # noqa: E501
            assert AgentController is not None
        except ImportError as e:
            msg = f"Could not import from controllers.agent_controller: {e}"
            pytest.fail(msg)

    def test_frameworks_can_be_imported(self):
        """🔴 RED: frameworks からフレームワークコンポーネントをインポートできる"""
        try:
            from main.frameworks_and_drivers.frameworks.message_broker import SqliteMessageBroker  # noqa: E501
            from main.frameworks_and_drivers.frameworks.gemini_service import GeminiService  # noqa: E501
            assert SqliteMessageBroker is not None
            assert GeminiService is not None
        except ImportError as e:
            pytest.fail(f"Could not import from frameworks: {e}")

    def test_drivers_can_be_imported(self):
        """🔴 RED: drivers からドライバーをインポートできる"""
        try:
            from main.frameworks_and_drivers.drivers.supervisor import Supervisor  # noqa: E501
            assert Supervisor is not None
        except ImportError as e:
            pytest.fail(f"Could not import from drivers.supervisor: {e}")

    def test_external_interfaces_can_be_imported(self):
        """🔴 RED: external_interfaces から外部インターフェースをインポートできる"""
        try:
            from main.frameworks_and_drivers.external_interfaces.cli import CLI  # noqa: E501
            assert CLI is not None
        except ImportError as e:
            pytest.fail(f"Could not import from external_interfaces.cli: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
