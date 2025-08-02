"""
SqliteMessageBrokerの統計機能テスト
TDD: 新しい機能はテストから書く
"""
import unittest
import tempfile
import os
from main.infrastructure.message_broker import SqliteMessageBroker
from main.domain.models import Message


class TestSqliteMessageBrokerStatistics(unittest.TestCase):
    def setUp(self):
        """テスト用の一時データベースを作成"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.broker = SqliteMessageBroker(self.db_path)
        self.broker.initialize_db()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        os.unlink(self.db_path)

    def test_get_statistics_should_return_message_counts(self):
        """統計情報は送信・受信されたメッセージ数を返す必要がある"""
        # Arrange
        msg1 = Message(
            sender_id="DEBATER_A",
            recipient_id="MODERATOR",
            message_type="SUBMIT_STATEMENT",
            payload={"text": "テスト1"},
            turn_id=1
        )
        msg2 = Message(
            sender_id="DEBATER_N",
            recipient_id="MODERATOR",
            message_type="SUBMIT_STATEMENT",
            payload={"text": "テスト2"},
            turn_id=1
        )

        # Act - メッセージを投稿
        self.broker.post_message(msg1)
        self.broker.post_message(msg2)

        # Act - 統計を取得
        stats = self.broker.get_statistics()

        # Assert
        self.assertIsInstance(stats, dict)
        self.assertIn('total_messages', stats)
        self.assertEqual(stats['total_messages'], 2)
        self.assertIn('unread_messages', stats)

    def test_get_all_messages_should_return_full_history(self):
        """全メッセージ履歴を取得できる必要がある"""
        # Arrange
        msg = Message(
            sender_id="DEBATER_A",
            recipient_id="MODERATOR",
            message_type="SUBMIT_STATEMENT",
            payload={"text": "履歴テスト"},
            turn_id=1
        )

        # Act
        self.broker.post_message(msg)
        history = self.broker.get_all_messages()

        # Assert
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].sender_id, "DEBATER_A")


if __name__ == '__main__':
    unittest.main()
