"""
TDD Red Phase: post_initial_messageメソッドの新しいテスト
Kent BeckのTDD思想に準拠し、より詳細な機能をテストファーストで実装
"""
import pytest
import tempfile
import os
import yaml
from unittest.mock import MagicMock
from main.platform.supervisor import Supervisor
from main.domain.models import Message


class TestSupervisorInitialMessage:
    """Supervisorの初期メッセージ投函機能のテスト（TDD Red Phase）"""

    def setup_method(self):
        """各テストメソッド前のセットアップ"""
        # テンポラリディレクトリとプロジェクトファイルを作成
        self.temp_dir = tempfile.mkdtemp()
        self.project_file = os.path.join(self.temp_dir, "test_project.yml")

        # プロジェクト定義を作成
        project_def = {
            'project_name': 'test_debate',
            'agents': [
                {'id': 'MODERATOR', 'type': 'moderator'},
                {'id': 'DEBATER_A', 'type': 'debater'},
            ],
            'message_bus': {
                'type': 'sqlite',
                'db_path': 'test_messages.db'
            },
            'initial_task': {
                'type': 'debate',
                'topic': 'Test debate topic'
            }
        }

        with open(self.project_file, 'w') as f:
            yaml.dump(project_def, f)

    def teardown_method(self):
        """各テストメソッド後のクリーンアップ"""
        # テンポラリファイルを削除
        if os.path.exists(self.project_file):
            os.remove(self.project_file)

    def test_post_initial_message_sends_system_message_to_moderator(self):
        """
        🔴 FAILING TEST: post_initial_messageがSYSTEMからMODERATORへの
        PROMPT_FOR_STATEMENTメッセージを正しく送信することをテスト
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # テスト実行
        test_topic = "AI impact on society"
        supervisor.post_initial_message(test_topic)

        # 検証: post_messageが1回呼ばれることを確認
        mock_message_bus.post_message.assert_called_once()

        # 送信されたメッセージの内容を検証
        sent_message = mock_message_bus.post_message.call_args[0][0]
        assert isinstance(sent_message, Message)
        assert sent_message.sender_id == "SYSTEM"
        assert sent_message.recipient_id == "MODERATOR"
        assert sent_message.message_type == "PROMPT_FOR_STATEMENT"
        assert sent_message.payload["topic"] == test_topic
        assert sent_message.turn_id == 1

    def test_post_initial_message_fails_when_message_bus_not_initialized(self):
        """
        🔴 FAILING TEST: メッセージバスが初期化されていない場合に
        適切なエラーを発生させることをテスト
        """
        supervisor = Supervisor(self.project_file)
        # message_busを意図的にNoneのままにする

        # テスト実行と検証
        with pytest.raises(ValueError, match="Message bus not initialized"):
            supervisor.post_initial_message("Test topic")

    def test_post_initial_message_with_topic_from_project_definition(self):
        """
        🔴 FAILING TEST: プロジェクト定義からトピックを取得できることをテスト
        (将来の機能として、引数なしでも動作するように)
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # プロジェクト定義のトピックを使用
        expected_topic = supervisor.project_def['initial_task']['topic']
        supervisor.post_initial_message(expected_topic)

        # 検証
        sent_message = mock_message_bus.post_message.call_args[0][0]
        assert sent_message.payload["topic"] == expected_topic

    def test_post_initial_message_creates_valid_message_structure(self):
        """
        🔴 FAILING TEST: 作成されるメッセージが適切な構造を持つことをテスト
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        test_topic = "Complex debate topic with special characters: éñ中文"
        supervisor.post_initial_message(test_topic)

        # 送信されたメッセージの詳細検証
        sent_message = mock_message_bus.post_message.call_args[0][0]

        # 必須フィールドの存在確認
        assert hasattr(sent_message, 'sender_id')
        assert hasattr(sent_message, 'recipient_id')
        assert hasattr(sent_message, 'message_type')
        assert hasattr(sent_message, 'payload')
        assert hasattr(sent_message, 'turn_id')

        # ペイロードの構造確認
        assert isinstance(sent_message.payload, dict)
        assert 'topic' in sent_message.payload
        assert sent_message.payload['topic'] == test_topic

        # 特殊文字が正しく処理されることを確認
        assert isinstance(sent_message.payload['topic'], str)

    def test_post_initial_message_increments_turn_properly(self):
        """
        🔴 FAILING TEST: 複数の初期メッセージが送信される場合の
        ターン管理をテスト（将来の拡張機能）
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # 最初のメッセージ
        supervisor.post_initial_message("First topic")
        first_message = mock_message_bus.post_message.call_args_list[0][0][0]
        assert first_message.turn_id == 1

        # NOTE: 現在の実装では常にturn_id=1だが、
        # 将来的にターン管理が必要になる可能性を考慮してテストを作成

    def test_post_initial_message_handles_empty_topic(self):
        """
        🔴 FAILING TEST: 空のトピックが渡された場合の処理をテスト
        """
        supervisor = Supervisor(self.project_file)

        # メッセージバスをモック化
        mock_message_bus = MagicMock()
        supervisor.message_bus = mock_message_bus

        # 空文字列でテスト
        supervisor.post_initial_message("")

        sent_message = mock_message_bus.post_message.call_args[0][0]
        assert sent_message.payload["topic"] == ""

        # Noneでテスト（将来的にデフォルト値設定機能を追加する可能性）
        # NOTE: 現在の実装では文字列を期待するが、将来の拡張性を考慮
