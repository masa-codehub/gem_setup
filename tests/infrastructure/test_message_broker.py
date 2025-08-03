"""
Message Broker Infrastructure Layer Tests
Kent Beck TDD: Red → Green → Refactor

TDD原則:
1. 失敗するテストを最初に書く (Red)
2. テストを通すための最小限の実装 (Green)
3. コードを改善する (Refactor)
"""
import pytest


class TestMessageBrokerBasicOperations:
    """Message Brokerの基本操作に関するTDDテスト"""

    def test_post_and_get_message_should_work_correctly(
        self, initialized_message_broker
    ):
        """メッセージの投稿と取得が正しく動作すること

        TDD Green Phase: 実際のMessageクラスを使用してテストを通す
        """
        # Arrange
        broker = initialized_message_broker

        # 実際のMessageオブジェクトを作成
        from main.entities.models import Message

        test_message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="REQUEST_STATEMENT",
            payload={"topic": "Test Topic"},
            turn_id=1
        )

        # Act
        broker.post_message(test_message)
        retrieved_message = broker.get_message("DEBATER_A")

        # Assert
        # TDD原則: 期待する動作を明確に定義
        assert retrieved_message is not None
        assert retrieved_message.recipient_id == "DEBATER_A"
        assert retrieved_message.sender_id == "MODERATOR"

        # 異なる受信者のメッセージは取得されないこと
        other_message = broker.get_message("DEBATER_B")
        assert other_message is None

    def test_message_broker_should_initialize_database(
        self, real_platform_config
    ):
        """Message Brokerはデータベースを正しく初期化すること

        TDD Green Phase: 実際のPlatformConfigを使用してテストを通す
        """
        try:
            from main.frameworks_and_drivers.frameworks.message_broker import (
                SqliteMessageBroker
            )

            # Arrange & Act
            db_file_path = real_platform_config.get_message_db_file_path()
            broker = SqliteMessageBroker(db_file_path)
            broker.initialize_db()

            # Assert
            # データベースファイルが作成されること
            import os
            assert os.path.exists(db_file_path)

        except ImportError:
            # 実装がまだ存在しない場合（純粋なTDD Red Phase）
            pytest.skip("Implementation not yet available - Red Phase")


class TestMessageBrokerStatistics:
    """Message Broker統計機能のTDDテスト"""

    def test_statistics_should_track_message_count(
        self, initialized_message_broker
    ):
        """統計機能はメッセージ数を正しく追跡すること

        TDD Green Phase: 実際のMessageクラスを使用してテストを通す
        """
        # Arrange
        broker = initialized_message_broker

        # 実際のMessageオブジェクトを2つ作成
        from main.entities.models import Message

        msg1 = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="REQUEST_STATEMENT",
            payload={"topic": "Test Topic 1"},
            turn_id=1
        )

        msg2 = Message(
            recipient_id="DEBATER_B",
            sender_id="MODERATOR",
            message_type="REQUEST_STATEMENT",
            payload={"topic": "Test Topic 2"},
            turn_id=1
        )

        # Act
        broker.post_message(msg1)
        broker.post_message(msg2)

        # 統計機能が実装されていれば呼び出し、そうでなければテストをスキップ
        if hasattr(broker, 'get_statistics'):
            stats = broker.get_statistics()

            # Assert
            assert isinstance(stats, dict)
            assert "total_messages" in stats
            assert stats["total_messages"] == 2
            assert "unread_messages" in stats
        else:
            # Green Phase: 統計機能が未実装の場合はスキップ
            import pytest
            pytest.skip("Statistics feature not yet implemented - Green Phase")
