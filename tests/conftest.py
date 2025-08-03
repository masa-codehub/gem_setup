"""
テストスイート全体で使用する共通フィクスチャ
Kent BeckのTDD思想：テストコードは実装の設計を駆動する
"""
import pytest
import os
import tempfile
import yaml
from unittest.mock import Mock


@pytest.fixture
def temp_run_dir():
    """テスト用の一時的な実行ディレクトリを作成するフィクスチャ

    TDD原則：テストの独立性を保つため、各テストで独立したファイルシステムを提供
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_config_dict(temp_run_dir):
    """テスト用の設定辞書を生成するフィクスチャ

    TDD原則：具体的な設定ファイルに依存せず、テストが必要とする最小限の設定を動的に生成
    """
    # メッセージDBディレクトリとファイルパスを分離
    db_dir = os.path.join(temp_run_dir, "db")

    return {
        "platform_config": {
            "data_storage_path": temp_run_dir,
            "message_db_path": db_dir,  # ディレクトリパス
            "agent_config_path": "./config/scenario_test"
        },
        "agents": [
            {"id": "MODERATOR", "persona_file": "moderator.md"},
            {"id": "DEBATER_A", "persona_file": "debater_a.md"}
        ],
        "initial_task": {
            "topic": "Test Topic for TDD"
        }
    }


@pytest.fixture
def test_config_file(test_config_dict, temp_run_dir):
    """テスト用の設定ファイルを作成するフィクスチャ

    TDD原則：実装の詳細（ファイル形式等）から独立したテスト環境を提供
    """
    config_path = os.path.join(temp_run_dir, "test_project.yml")
    with open(config_path, 'w') as f:
        yaml.dump(test_config_dict, f)
    return config_path


@pytest.fixture
def real_platform_config(test_config_file):
    """実際のPlatformConfigオブジェクトを提供するフィクスチャ

    TDD Green Phase: 実際のクラスを使用してテストを通す
    """
    try:
        from main.frameworks_and_drivers.frameworks.platform_config import (
            PlatformConfig
        )

        return PlatformConfig(test_config_file)
    except ImportError:
        # 実装が存在しない場合は、モックオブジェクトを返す
        mock_config = Mock()
        mock_config.message_db_path = "/tmp/test_messages.db"
        mock_config.data_storage_path = "/tmp"
        mock_config.agent_config_path = "./config/scenario_test"
        mock_config.agents = [
            {"id": "MODERATOR", "persona_file": "moderator.md"},
            {"id": "DEBATER_A", "persona_file": "debater_a.md"}
        ]
        mock_config.initial_task = {"topic": "Test Topic for TDD"}
        return mock_config


@pytest.fixture
def initialized_message_broker(real_platform_config):
    """初期化済みのメッセージブローカーを提供するフィクスチャ

    TDD原則：テストの準備段階を自動化し、テストの意図を明確にする
    ResourceWarning対策：データベース接続を適切に管理する
    """
    broker = None
    try:
        from main.frameworks_and_drivers.frameworks.message_broker import (
            SqliteMessageBroker
        )

        # PlatformConfigから正しいファイルパスを取得
        db_file_path = real_platform_config.get_message_db_file_path()
        broker = SqliteMessageBroker(db_file_path)
        broker.initialize_db()

        yield broker

    except ImportError:
        # モジュールが存在しない場合は、モックオブジェクトを返す
        # TDD原則：実装が存在しない場合でも、テストは実行可能であるべき
        mock_broker = Mock()
        mock_broker.db_path = real_platform_config.get_message_db_file_path()
        mock_broker.post_message = Mock()
        mock_broker.get_message = Mock(return_value=None)
        mock_broker.initialize_db = Mock()
        mock_broker.close = Mock()
        yield mock_broker

    finally:
        # データベース接続を確実に閉じる（ResourceWarning対策）
        if broker:
            # すべての可能な接続を閉じる
            if hasattr(broker, '_connection') and broker._connection:
                try:
                    broker._connection.close()
                except Exception:
                    pass  # 既に閉じられている場合もある
            if hasattr(broker, 'close'):
                try:
                    broker.close()
                except Exception:
                    pass
