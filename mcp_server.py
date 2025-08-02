import os
import logging
from filelock import FileLock
from mcp.server.fastmcp import FastMCP

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# サーバーを名前で初期化
mcp = FastMCP("DebateSystem")

# 堅牢なファイルロックのために、サードパーティライブラリを使用
# pip install filelock


@mcp.tool()
def write_to_transcript(message: str) -> str:
    """
    共有の討論トランスクリプトファイルに、ロックをかけて安全にメッセージを追記します。
    :param message: 追記するJSON形式のメッセージ文字列。
    :return: 書き込み成功の確認メッセージ。
    """
    logging.info("Received request for write_to_transcript.")
    try:
        debate_dir = os.environ.get("DEBATE_DIR")
        if not debate_dir:
            logging.error("DEBATE_DIR environment variable is not set.")
            return "Error: DEBATE_DIR environment variable is not set."

        transcript_file = os.path.join(debate_dir, "debate_transcript.json")
        lock_file = os.path.join(debate_dir, "transcript.lock")

        lock = FileLock(lock_file, timeout=10)
        with lock:
            with open(transcript_file, "a") as f:
                f.write(message + "\n")

        logging.info("Successfully wrote message to transcript.")
        return "Message successfully written to transcript."
    except Exception as e:
        logging.error(f"Error writing to transcript: {str(e)}")
        return f"Error writing to transcript: {str(e)}"


@mcp.tool()
def health_check() -> str:
    """
    サーバーが正常に起動しているかを確認するためのシンプルなツール。
    :return: サーバーが正常であることを示すメッセージ。
    """
    logging.info("Health check requested.")
    return "MCP Server is running correctly."


if __name__ == "__main__":
    logging.info("Starting MCP Server...")
    mcp.run(transport="stdio")
