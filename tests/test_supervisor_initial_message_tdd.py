"""
TDD Phase 2: スーパーバイザーの初期メッセージ投函機能テスト

次のテストケース（Red -> Green -> Refactor）
Kent Beckの思想: 一度に一つの機能をテストし、段階的に構築する
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

# 新しい機能のテスト対象をインポート（まだ修正していないので失敗するはず）
try:
    from main.platform.supervisor import Supervisor
    SUPERVISOR_EXISTS = True
except ImportError:
    SUPERVISOR_EXISTS = False

from main.domain.models import Message


class TestSupervisorInitialMessageTDD:
    """スーパーバイザーの初期メッセージ投函機能のTDDテスト"""

    def test_supervisor_class_exists(self):
        """RED: Supervisorクラスが存在することを確認"""
        assert SUPERVISOR_EXISTS, "Supervisor class should exist"
        assert Supervisor is not None, "Supervisor should be importable"

    @pytest.mark.skipif(not SUPERVISOR_EXISTS,
                        reason="Supervisor not available")
    def test_supervisor_has_post_initial_message_method(self):
        """RED: post_initial_messageメソッドが存在することをテスト"""
        # テスト用プロジェクトファイルを作成
        supervisor = Supervisor("project.yml")

        # メソッドが存在することを確認
        assert hasattr(supervisor, 'post_initial_message'), \
            "Supervisor should have post_initial_message method"
        assert callable(getattr(supervisor, 'post_initial_message')), \
            "post_initial_message should be callable"

    @pytest.mark.skipif(not SUPERVISOR_EXISTS,
                        reason="Supervisor not available")
    def test_post_initial_message_creates_initiate_debate_message(self):
        """RED: 初期メッセージでINITIATE_DEBATEメッセージが作成されることをテスト"""
        # モックメッセージバスを設定
        mock_message_bus = MagicMock()

        supervisor = Supervisor("project.yml")
        supervisor.message_bus = mock_message_bus

        # テスト用トピック
        test_topic = "AI ethics in autonomous systems"

        # メソッドを呼び出し
        supervisor.post_initial_message(test_topic)

        # メッセージバスのpost_messageが呼ばれたことを確認
        mock_message_bus.post_message.assert_called_once()

        # 呼び出された引数を取得
        call_args = mock_message_bus.post_message.call_args[0]
        posted_message = call_args[0]

        # メッセージの内容を検証
        assert isinstance(posted_message, Message)
        assert posted_message.sender_id == "SYSTEM"
        assert posted_message.recipient_id == "MODERATOR"
        assert posted_message.message_type == "INITIATE_DEBATE"
        assert posted_message.payload["topic"] == test_topic
        assert "rules" in posted_message.payload
        assert posted_message.turn_id == 1

    @pytest.mark.skipif(not SUPERVISOR_EXISTS,
                        reason="Supervisor not available")
    def test_post_initial_message_raises_error_without_message_bus(self):
        """RED: メッセージバスが初期化されていない場合にエラーが発生することをテスト"""
        supervisor = Supervisor("project.yml")
        supervisor.message_bus = None

        with pytest.raises(ValueError) as excinfo:
            supervisor.post_initial_message("test topic")

        assert "Message bus must be initialized" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
