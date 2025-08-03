"""
TDD Green Phase: MCPメッセージバスサーバーの最小実装
Kent BeckのTDD思想: テストを通すための最小限のコードを書く
"""

import os
import json
import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP
from main.infrastructure.message_broker import SqliteMessageBroker
from main.domain.models import Message

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MCP - %(levelname)s - %(message)s'
)

# MCPサーバーとブローカーの初期化
mcp = FastMCP("A2A_Message_Bus")
broker: Optional[SqliteMessageBroker] = None


def initialize_broker():
    """ブローカーの初期化"""
    global broker
    if broker is None:
        db_path = os.environ.get("DEBATE_DIR", ".")
        broker = SqliteMessageBroker(
            os.path.join(db_path, "messages.db")
        )
        broker.initialize_db()
        logging.info("Message broker initialized")


@mcp.tool()
def post_message(message_json: str) -> str:
    """
    シリアライズされたMessageオブジェクトをA2Aメッセージバスに投函する。

    Args:
        message_json: MessageオブジェクトのJSON文字列

    Returns:
        成功または失敗のメッセージ
    """
    try:
        initialize_broker()
        msg_dict = json.loads(message_json)
        message = Message(**msg_dict)
        broker.post_message(message)
        logging.info(f"Message posted for {message.recipient_id}")
        return f"Success: Message posted for {message.recipient_id}."
    except Exception as e:
        logging.error(f"Failed to post message: {e}")
        return f"Error: {e}"


@mcp.tool()
def get_message(recipient_id: str) -> str:
    """
    指定されたエージェント宛の未読メッセージを1件取得する。

    Args:
        recipient_id: メッセージを取得するエージェントのID

    Returns:
        MessageオブジェクトのJSON文字列。
        メッセージがない場合は空のJSONオブジェクトを返す。
    """
    try:
        initialize_broker()
        message = broker.get_message(recipient_id)
        if message:
            logging.info(f"Message retrieved for {recipient_id}")
            return json.dumps(message.__dict__)
        return "{}"
    except Exception as e:
        logging.error(f"Failed to get message for {recipient_id}: {e}")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    initialize_broker()
    logging.info("MCP Message Bus Server starting...")
    mcp.run(transport="stdio")
