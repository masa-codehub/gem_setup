"""
SQLiteベースのメッセージブローカー実装
IMessageBrokerインターフェースの具体的な実装
"""

import sqlite3
import json
import os
from typing import Optional
from main.use_cases.interfaces import IMessageBroker
from main.entities.models import Message, AgentID


class SqliteMessageBroker(IMessageBroker):
    """SQLiteを使ったメッセージブローカー"""

    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: データベースファイルのパス。Noneの場合は環境変数から取得
        """
        if db_path is None:
            debate_dir = os.environ.get("DEBATE_DIR", ".")
            self.db_path = os.path.join(debate_dir, "messages.db")
        else:
            self.db_path = db_path
        self._connection = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def _get_connection(self):
        """Get or create database connection"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
        return self._connection

    def initialize_db(self):
        """データベースの初期化"""
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id TEXT NOT NULL,
                message_body TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    def post_message(self, message: Message) -> None:
        """メッセージを送信する"""
        # ドメインモデルを辞書に変換
        message_dict = {
            "turn_id": message.turn_id,
            "timestamp": message.timestamp,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "message_type": message.message_type,
            "payload": message.payload
        }

        message_body = json.dumps(message_dict)

        conn = self._get_connection()
        conn.execute(
            """INSERT INTO messages (recipient_id, message_body)
               VALUES (?, ?)""",
            (message.recipient_id, message_body)
        )
        conn.commit()

    def get_message(self, recipient_id: AgentID) -> Optional[Message]:
        """指定した受信者宛のメッセージを取得する"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 未読メッセージを取得
        cursor.execute("""
            SELECT id, message_body FROM messages
            WHERE recipient_id = ? AND is_read = 0
            ORDER BY created_at
            LIMIT 1
        """, (recipient_id,))

        row = cursor.fetchone()
        if not row:
            return None

        # メッセージを既読にマーク
        cursor.execute(
            "UPDATE messages SET is_read = 1 WHERE id = ?",
            (row['id'],)
        )
        conn.commit()

        # 辞書からドメインモデルに変換
        message_dict = json.loads(row['message_body'])
        return Message(
            recipient_id=message_dict['recipient_id'],
            sender_id=message_dict['sender_id'],
            message_type=message_dict['message_type'],
            payload=message_dict['payload'],
            turn_id=message_dict['turn_id'],
            timestamp=message_dict['timestamp']
        )

    def get_statistics(self) -> dict:
        """メッセージブローカーの統計情報を取得する"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 総メッセージ数
        cursor.execute("SELECT COUNT(*) as total FROM messages")
        total_messages = cursor.fetchone()[0]

        # 未読メッセージ数
        cursor.execute(
            "SELECT COUNT(*) as unread FROM messages WHERE is_read = 0"
        )
        unread_messages = cursor.fetchone()[0]

        return {
            'total_messages': total_messages,
            'unread_messages': unread_messages
        }

    def get_all_messages(self) -> list[Message]:
        """すべてのメッセージ履歴を取得する"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT message_body FROM messages
            ORDER BY created_at
        """)

        messages = []
        for row in cursor.fetchall():
            message_dict = json.loads(row['message_body'])
            messages.append(Message(
                recipient_id=message_dict['recipient_id'],
                sender_id=message_dict['sender_id'],
                message_type=message_dict['message_type'],
                payload=message_dict['payload'],
                turn_id=message_dict['turn_id'],
                timestamp=message_dict['timestamp']
            ))

        return messages
