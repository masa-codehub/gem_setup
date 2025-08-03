"""
TDD実装: MCPメッセージバスサーバーのテスト

Kent BeckのTDD思想に従い、最小限のテストから開始
1. Red: 失敗するテストを書く
2. Green: 最小限の実装でテストを通す
3. Refactor: コードを改善する
"""

import pytest
import json

# テスト対象をインポート（まだ存在しないのでテストは失敗するはず）
try:
    from main.infrastructure.mcp_message_bus_server import post_message, get_message
    MCP_SERVER_EXISTS = True
except ImportError:
    MCP_SERVER_EXISTS = False

from main.domain.models import Message


class TestMCPMessageBusServerTDD:
    """MCPサーバー機能のTDDテスト"""

    def test_post_message_tool_exists(self):
        """RED: post_messageツールが存在することをテスト"""
        # 現在は失敗するはず（まだ実装していない）
        assert MCP_SERVER_EXISTS, "MCP server module should exist"
        assert callable(post_message), "post_message should be callable"

    def test_get_message_tool_exists(self):
        """RED: get_messageツールが存在することをテスト"""
        # 現在は失敗するはず（まだ実装していない）
        assert MCP_SERVER_EXISTS, "MCP server module should exist"
        assert callable(get_message), "get_message should be callable"

    @pytest.mark.skipif(not MCP_SERVER_EXISTS, reason="MCP server not implemented yet")
    def test_post_message_success(self):
        """RED: メッセージ投函の成功ケースをテスト"""
        # テスト用メッセージを作成
        test_message = Message(
            sender_id="SYSTEM",
            recipient_id="MODERATOR",
            message_type="INITIATE_DEBATE",
            payload={"topic": "AI ethics", "rules": "Standard rules"},
            turn_id=1
        )

        message_json = json.dumps(test_message.__dict__)

        # MCPツールを呼び出し
        result = post_message(message_json)

        # 成功メッセージが返されることを確認
        assert "Success" in result
        assert "MODERATOR" in result

    @pytest.mark.skipif(not MCP_SERVER_EXISTS, reason="MCP server not implemented yet")
    def test_get_message_success(self):
        """RED: メッセージ取得の成功ケースをテスト"""
        # まずメッセージを投函
        test_message = Message(
            sender_id="SYSTEM",
            recipient_id="DEBATER_A",
            message_type="REQUEST_STRATEGY",
            payload={"topic": "AI ethics"},
            turn_id=1
        )

        message_json = json.dumps(test_message.__dict__)
        post_message(message_json)

        # メッセージを取得
        result = get_message("DEBATER_A")
        result_dict = json.loads(result)

        # 正しいメッセージが返されることを確認
        assert result_dict["recipient_id"] == "DEBATER_A"
        assert result_dict["message_type"] == "REQUEST_STRATEGY"
        assert result_dict["payload"]["topic"] == "AI ethics"

    @pytest.mark.skipif(not MCP_SERVER_EXISTS, reason="MCP server not implemented yet")
    def test_get_message_empty_queue(self):
        """RED: メッセージが存在しない場合のテスト"""
        result = get_message("NONEXISTENT_AGENT")
        result_dict = json.loads(result)

        # 空のオブジェクトが返されることを確認
        assert result_dict == {}

    @pytest.mark.skipif(not MCP_SERVER_EXISTS, reason="MCP server not implemented yet")
    def test_post_message_invalid_json(self):
        """RED: 不正なJSONの場合のエラーハンドリングをテスト"""
        invalid_json = "{'invalid': json}"

        result = post_message(invalid_json)

        # エラーメッセージが返されることを確認
        assert "Error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
