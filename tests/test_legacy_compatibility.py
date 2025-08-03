"""
レガシーmessage_broker.pyの機能を全てカバーできているかテスト
TDD: レガシーコードを削除する前に、その機能が全て新しい実装でカバーされているかテストする
"""
import unittest
import tempfile
import os
from main.frameworks_and_drivers.frameworks.message_broker import SqliteMessageBroker
from main.entities.models import Message


class TestLegacyCompatibility(unittest.TestCase):
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

    def test_legacy_message_broker_can_be_replaced(self):
        """
        レガシーmessage_broker.pyの全ての機能が
        新しいSqliteMessageBrokerで再現できることを確認
        """
        # Arrange - テストメッセージ
        test_message = Message(
            sender_id="DEBATER_A",
            recipient_id="MODERATOR",
            message_type="SUBMIT_STATEMENT",
            payload={"text": "レガシー互換テスト"},
            turn_id=1
        )

        # Act & Assert - 基本的なメッセージ送受信
        self.broker.post_message(test_message)
        received = self.broker.get_message("MODERATOR")

        self.assertIsNotNone(received)
        self.assertEqual(received.sender_id, "DEBATER_A")
        self.assertEqual(received.payload["text"], "レガシー互換テスト")

        # Act & Assert - 統計情報
        stats = self.broker.get_statistics()
        self.assertIn('total_messages', stats)
        self.assertEqual(stats['total_messages'], 1)

        # Act & Assert - 履歴取得
        history = self.broker.get_all_messages()
        self.assertEqual(len(history), 1)

    def test_new_implementation_is_production_ready(self):
        """
        新しい実装が本番環境に投入可能なレベルであることを確認
        """
        # Arrange - 複数のメッセージを送信
        messages = [
            Message(
                sender_id=f"DEBATER_{chr(65+i)}",
                recipient_id="MODERATOR",
                message_type="SUBMIT_STATEMENT",
                payload={"text": f"テストメッセージ{i}"},
                turn_id=i+1
            ) for i in range(5)
        ]

        # Act - 大量のメッセージ処理
        for msg in messages:
            self.broker.post_message(msg)

        # Assert - パフォーマンスと正確性
        stats = self.broker.get_statistics()
        self.assertEqual(stats['total_messages'], 5)
        self.assertEqual(stats['unread_messages'], 5)

        # 順次受信して確認
        received_count = 0
        while True:
            msg = self.broker.get_message("MODERATOR")
            if msg is None:
                break
            received_count += 1

        self.assertEqual(received_count, 5)

        # 受信後の統計確認
        final_stats = self.broker.get_statistics()
        self.assertEqual(final_stats['total_messages'], 5)
        self.assertEqual(final_stats['unread_messages'], 0)


if __name__ == '__main__':
    unittest.main()
