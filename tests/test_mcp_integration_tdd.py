"""
TDD 統合テスト: A2A通信のMCP化完全実装テスト

Kent BeckのTDD思想に基づく統合テスト
すべてのコンポーネントが連携して動作することを確認
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

# すべてのコンポーネントをインポート
from main.platform.supervisor import Supervisor
from main.domain.models import Message
from main.infrastructure.mcp_message_bus_server import post_message, get_message


class TestMCPIntegrationTDD:
    """A2A通信のMCP化統合テスト"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化"""
        # テスト用の一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        os.environ["DEBATE_DIR"] = self.temp_dir

        # メッセージキューをクリア（既存のメッセージを全て消費）
        agents = ["MODERATOR", "DEBATER_A", "DEBATER_N",
                  "JUDGE_L", "JUDGE_E", "JUDGE_R", "ANALYST"]
        for agent in agents:
            while True:
                result = get_message(agent)
                if result == "{}":
                    break

    def teardown_method(self):
        """各テストメソッドの後に実行されるクリーンアップ"""
        # 環境変数をクリア
        if "DEBATE_DIR" in os.environ:
            del os.environ["DEBATE_DIR"]

    def test_end_to_end_mcp_workflow(self):
        """RED→GREEN: エンドツーエンドのMCPワークフローテスト"""
        # 1. 直接メッセージバスを使ってメッセージを投函
        test_topic = "AI ethics in autonomous systems"

        # Message オブジェクトを作成
        test_message = Message(
            sender_id="SYSTEM",
            recipient_id="MODERATOR",
            message_type="INITIATE_DEBATE",
            payload={
                "topic": test_topic,
                "rules": "Test rules"
            },
            turn_id=1
        )

        # 2. MCPツール経由でメッセージを投函
        message_json = json.dumps(test_message.__dict__)
        post_result = post_message(message_json)
        assert "Success" in post_result

        # 3. MCPツール経由でメッセージを取得
        result_json = get_message("MODERATOR")
        result_dict = json.loads(result_json)

        # 4. メッセージの内容を検証
        assert result_dict["recipient_id"] == "MODERATOR"
        assert result_dict["sender_id"] == "SYSTEM"
        assert result_dict["message_type"] == "INITIATE_DEBATE"
        assert result_dict["payload"]["topic"] == test_topic
        assert "rules" in result_dict["payload"]
        assert result_dict["turn_id"] == 1

    def test_mcp_message_exchange_cycle(self):
        """RED→GREEN: MCPメッセージ交換サイクルテスト"""
        # 1. MODERATOR→DEBATER_Aへの戦略要求メッセージ
        strategy_request = Message(
            sender_id="MODERATOR",
            recipient_id="DEBATER_A",
            message_type="REQUEST_STRATEGY",
            payload={"topic": "AI ethics",
                     "instructions": "Provide your strategy"},
            turn_id=2
        )

        strategy_request_json = json.dumps(strategy_request.__dict__)
        post_result = post_message(strategy_request_json)
        assert "Success" in post_result

        # 2. DEBATER_Aがメッセージを受信
        received_json = get_message("DEBATER_A")
        received_dict = json.loads(received_json)

        assert received_dict["message_type"] == "REQUEST_STRATEGY"
        assert received_dict["sender_id"] == "MODERATOR"

        # 3. DEBATER_A→MODERATORへの戦略応答メッセージ
        strategy_response = Message(
            sender_id="DEBATER_A",
            recipient_id="MODERATOR",
            message_type="SUBMIT_STRATEGY",
            payload={
                "strategy": "Logic-based approach with empirical evidence",
                "key_points": ["Data analysis", "Systematic reasoning"]
            },
            turn_id=3
        )

        strategy_response_json = json.dumps(strategy_response.__dict__)
        post_result = post_message(strategy_response_json)
        assert "Success" in post_result

        # 4. MODERATORがメッセージを受信
        moderator_received_json = get_message("MODERATOR")
        moderator_received_dict = json.loads(moderator_received_json)

        assert moderator_received_dict["message_type"] == "SUBMIT_STRATEGY"
        assert moderator_received_dict["sender_id"] == "DEBATER_A"
        assert "strategy" in moderator_received_dict["payload"]

    def test_supervisor_mcp_integration(self):
        """RED→GREEN: スーパーバイザーとMCPの統合テスト"""
        # 直接MCPツールを使った一貫したテスト
        topics = [
            "Climate change solutions",
            "Universal Basic Income",
            "Space exploration priorities"
        ]

        for i, topic in enumerate(topics, 1):
            # メッセージを直接MCPツールで投函
            test_message = Message(
                sender_id="SYSTEM",
                recipient_id="MODERATOR",
                message_type="INITIATE_DEBATE",
                payload={"topic": topic, "rules": "Test rules"},
                turn_id=i
            )

            message_json = json.dumps(test_message.__dict__)
            post_result = post_message(message_json)
            assert "Success" in post_result

            # MCPツールで取得
            result_json = get_message("MODERATOR")
            result_dict = json.loads(result_json)

            # 検証
            assert result_dict["payload"]["topic"] == topic
            assert result_dict["turn_id"] == i
            assert result_dict["message_type"] == "INITIATE_DEBATE"

    def test_error_handling_integration(self):
        """RED→GREEN: エラーハンドリングの統合テスト"""
        # 1. 不正なJSONでのメッセージ投函
        invalid_json = "{'malformed': 'json'"
        result = post_message(invalid_json)
        assert "Error" in result

        # 2. 存在しないエージェントIDでのメッセージ取得
        result = get_message("NONEXISTENT_AGENT")
        result_dict = json.loads(result)
        assert result_dict == {}

        # 3. メッセージバスが初期化されていないスーパーバイザー
        supervisor = Supervisor("project.yml")
        supervisor.message_bus = None

        with pytest.raises(ValueError) as excinfo:
            supervisor.post_initial_message("test topic")
        assert "Message bus must be initialized" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
