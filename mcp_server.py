import os
from filelock import FileLock
from mcp.server.fastmcp import FastMCP

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
    try:
        debate_dir = os.environ.get("DEBATE_DIR")
        if not debate_dir:
            return "Error: DEBATE_DIR environment variable is not set."

        transcript_file = os.path.join(debate_dir, "debate_transcript.json")
        lock_file = os.path.join(debate_dir, "transcript.lock")

        lock = FileLock(lock_file, timeout=10)
        with lock:
            with open(transcript_file, "a") as f:
                f.write(message + "\n")

        return "Message successfully written to transcript."
    except Exception as e:
        return f"Error writing to transcript: {str(e)}"


if __name__ == "__main__":
    # stdioトランスポートを使用してサーバーを実行
    mcp.run(transport="stdio")
