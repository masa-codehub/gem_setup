"""
メッセージブローカーの動作を確認するデバッグテスト
"""
import unittest
import tempfile
import os
from main.frameworks_and_drivers.frameworks.message_broker import SqliteMessageBroker
from main.entities.models import Message


class TestMessageBrokerDebug(unittest.TestCase):
    """メッセージブローカーのデバッグテスト"""

    def setUp(self):
        """テスト環境のセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "debug.db")

    def tearDown(self):
        """テスト環境のクリーンアップ"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_message_broker_basic_operations(self):
        """メッセージブローカーの基本動作テスト"""
        # Given: メッセージブローカーが初期化されている
        broker = SqliteMessageBroker(self.db_path)
        broker.initialize_db()

        # When: メッセージを投函
        test_message = Message(
            sender_id="SENDER",
            recipient_id="RECIPIENT",
            message_type="TEST_MESSAGE",
            payload={"test": "data"},
            turn_id=1
        )
        broker.post_message(test_message)

        # Then: メッセージが取得できる
        received_message = broker.get_message("RECIPIENT")
        self.assertIsNotNone(received_message)
        self.assertEqual(received_message.message_type, "TEST_MESSAGE")
        self.assertEqual(received_message.sender_id, "SENDER")

        # 2回目の取得では None が返される（既読のため）
        second_attempt = broker.get_message("RECIPIENT")
        self.assertIsNone(second_attempt)

    def test_supervisor_specific_message_flow(self):
        """SUPERVISORへのメッセージフロー専用テスト"""
        # Given: メッセージブローカーが初期化されている
        broker = SqliteMessageBroker(self.db_path)
        broker.initialize_db()

        # When: SUPERVISORにシャットダウンメッセージを送信
        shutdown_message = Message(
            sender_id="MODERATOR",
            recipient_id="SUPERVISOR",
            message_type="SHUTDOWN_SYSTEM",
            payload={"reason": "Test shutdown"},
            turn_id=1
        )
        broker.post_message(shutdown_message)

        # Then: SUPERVISORがメッセージを受信できる
        received = broker.get_message("SUPERVISOR")
        self.assertIsNotNone(received)
        self.assertEqual(received.message_type, "SHUTDOWN_SYSTEM")
        self.assertEqual(received.sender_id, "MODERATOR")

        # Debug: データベースの内容を確認
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages")
        rows = cursor.fetchall()
        print(f"Debug: Messages in DB: {rows}")
        conn.close()

    def test_multiple_recipients(self):
        """複数の受信者へのメッセージ配信テスト"""
        # Given: メッセージブローカーが初期化されている
        broker = SqliteMessageBroker(self.db_path)
        broker.initialize_db()

        # When: 異なる受信者にメッセージを送信
        msg1 = Message(
            sender_id="SYSTEM", recipient_id="MODERATOR",
            message_type="INITIATE_DEBATE", payload={}, turn_id=1
        )
        msg2 = Message(
            sender_id="MODERATOR", recipient_id="DEBATER_A",
            message_type="REQUEST_STATEMENT", payload={}, turn_id=2
        )
        msg3 = Message(
            sender_id="MODERATOR", recipient_id="SUPERVISOR",
            message_type="SHUTDOWN_SYSTEM", payload={}, turn_id=3
        )

        broker.post_message(msg1)
        broker.post_message(msg2)
        broker.post_message(msg3)

        # Then: 各受信者が自分宛のメッセージだけを受信
        moderator_msg = broker.get_message("MODERATOR")
        self.assertEqual(moderator_msg.message_type, "INITIATE_DEBATE")

        debater_msg = broker.get_message("DEBATER_A")
        self.assertEqual(debater_msg.message_type, "REQUEST_STATEMENT")

        supervisor_msg = broker.get_message("SUPERVISOR")
        self.assertEqual(supervisor_msg.message_type, "SHUTDOWN_SYSTEM")


if __name__ == '__main__':
    unittest.main()
