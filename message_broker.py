import sqlite3
import json
import os

DB_FILE = os.path.join(os.environ.get("DEBATE_DIR", "."), "messages.db")


def initialize_db():
    """データベースとテーブルを初期化する"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id TEXT NOT NULL,
                message_body TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


def post_message(recipient_id: str, message_body: dict):
    """指定された受信者宛にメッセージを投稿する"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO messages (recipient_id, message_body) VALUES (?, ?)",
            (recipient_id, json.dumps(message_body))
        )
        conn.commit()
    msg_type = message_body.get('message_type', 'UNKNOWN')
    import sys
    print(f"📮 Posted for {recipient_id} (type: {msg_type})", file=sys.stderr)


def get_message(recipient_id: str) -> dict | None:
    """指定された受信者宛の未読メッセージを1件取得し、既読にする"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM messages WHERE recipient_id = ? AND is_read = 0 "
            "ORDER BY created_at LIMIT 1",
            (recipient_id,)
        )
        row = c.fetchone()
        if row:
            c.execute(
                "UPDATE messages SET is_read = 1 WHERE id = ?",
                (row['id'],)
            )
            conn.commit()
            message = json.loads(row['message_body'])
            # Use stderr for log messages to avoid interfering with JSON output
            import sys
            msg_type = message.get('message_type', 'UNKNOWN')
            print(f"📬 Retrieved for {recipient_id} (type: {msg_type})",
                  file=sys.stderr)
            return message
    return None


def get_message_count(recipient_id: str = None):
    """メッセージ数を取得する（全体またはエージェント別）"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        if recipient_id:
            c.execute(
                "SELECT COUNT(*) FROM messages WHERE recipient_id = ?",
                (recipient_id,)
            )
        else:
            c.execute("SELECT COUNT(*) FROM messages")
        return c.fetchone()[0]


def get_statistics():
    """メッセージブローカーの統計情報を取得する"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # エージェント別メッセージ数
        c.execute("""
            SELECT recipient_id,
                   COUNT(*) as total_messages,
                   SUM(is_read) as read_messages,
                   COUNT(*) - SUM(is_read) as unread_messages
            FROM messages
            GROUP BY recipient_id
        """)
        agent_stats = c.fetchall()

        # 全体統計
        c.execute("SELECT COUNT(*) FROM messages")
        total_messages = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM messages WHERE is_read = 1")
        read_messages = c.fetchone()[0]

        return {
            'total_messages': total_messages,
            'read_messages': read_messages,
            'unread_messages': total_messages - read_messages,
            'agent_stats': [dict(row) for row in agent_stats]
        }


if __name__ == '__main__':
    # このスクリプトが直接呼び出された場合、コマンドライン引数に応じて動作
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 message_broker.py <command> [args...]")
        print("Commands:")
        print("  init                    - Initialize database")
        print("  post <recipient> <msg>  - Post message to recipient")
        print("  get <recipient>         - Get message for recipient")
        print("  count [recipient]       - Count messages")
        print("  stats                   - Show statistics")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        initialize_db()
        print("✅ Database initialized")
    elif command == "post":
        if len(sys.argv) < 4:
            print("Usage: post <recipient> <message_json>")
            sys.exit(1)
        try:
            recipient = sys.argv[2]
            message = json.loads(sys.argv[3])
            post_message(recipient, message)
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error posting message: {e}")
            sys.exit(1)
    elif command == "get":
        if len(sys.argv) < 3:
            print("Usage: get <recipient>")
            sys.exit(1)
        recipient = sys.argv[2]
        message = get_message(recipient)
        if message:
            print(json.dumps(message))
    elif command == "count":
        recipient = sys.argv[2] if len(sys.argv) > 2 else None
        count = get_message_count(recipient)
        if recipient:
            print(f"Messages for {recipient}: {count}")
        else:
            print(f"Total messages: {count}")
    elif command == "stats":
        stats = get_statistics()
        print("📊 Message Broker Statistics:")
        print(f"   Total messages: {stats['total_messages']}")
        print(f"   Read messages: {stats['read_messages']}")
        print(f"   Unread messages: {stats['unread_messages']}")
        print("📋 Agent Statistics:")
        for agent_stat in stats['agent_stats']:
            agent = agent_stat['recipient_id']
            total = agent_stat['total_messages']
            read = agent_stat['read_messages']
            unread = agent_stat['unread_messages']
            print(f"   {agent}: {total} total, {read} read, {unread} unread")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
