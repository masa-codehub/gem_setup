"""
MCP Message Bus Server - Green Phase Implementation
"""
import json
from main.entities.models import Message, AgentID
from main.frameworks_and_drivers.frameworks.message_broker import SqliteMessageBroker


def post_message(message_data: str) -> str:
    """メッセージを投稿"""
    try:
        # JSON文字列をパース
        if isinstance(message_data, str):
            message_dict = json.loads(message_data)
        else:
            message_dict = message_data

        # SqliteMessageBrokerを使用してメッセージを保存
        broker = SqliteMessageBroker()
        broker.initialize_db()

        # Messageオブジェクトを作成
        message = Message(**message_dict)
        broker.post_message(message)

        return f"Message posted successfully for {message.recipient_id}"
    except Exception as e:
        return f"Error posting message: {e}"


def get_message(agent_id: AgentID) -> str:
    """メッセージを取得"""
    try:
        broker = SqliteMessageBroker()
        broker.initialize_db()

        message = broker.get_message(agent_id)
        if message:
            # Messageオブジェクトを辞書に変換してJSONで返す
            return json.dumps(message.__dict__)
        else:
            return "{}"  # Empty JSON for no messages
    except Exception as e:
        return f'{{"error": "Error getting message: {e}"}}'
