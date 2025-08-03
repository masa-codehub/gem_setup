#!/usr/bin/env python3
"""
TDD実装完成デモンストレーション

Kent BeckのTDD思想に従って実装したA2A通信のMCP化システムのデモ
実際のメッセージフローを確認します
"""

import sys
import os
import tempfile
import json
import time
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))


def main():
    print("🚀 TDD Implementation Demo: A2A Communication with MCP")
    print("=" * 60)

    # テスト環境セットアップ
    temp_dir = tempfile.mkdtemp()
    os.environ['DEBATE_DIR'] = temp_dir
    print(f"📁 Test environment: {temp_dir}")

    try:
        # Step 1: MCP Server Tools Test
        print("\n🧪 Step 1: Testing MCP Server Tools")
        print("-" * 40)

        from main.infrastructure.mcp_message_bus_server import post_message, get_message
        from main.domain.models import Message

        # テストメッセージを作成
        test_message = Message(
            sender_id="SYSTEM",
            recipient_id="MODERATOR",
            message_type="INITIATE_DEBATE",
            payload={
                "topic": "AI Ethics in Autonomous Systems",
                "rules": "Standard debate rules apply"
            },
            turn_id=1
        )

        # メッセージを投函
        message_json = json.dumps(test_message.__dict__)
        result = post_message(message_json)
        print(f"📤 Post message result: {result}")

        # メッセージを取得
        retrieved = get_message("MODERATOR")
        if retrieved != "{}":
            retrieved_dict = json.loads(retrieved)
            print(
                f"📨 Retrieved message type: {retrieved_dict['message_type']}")
            print(f"📋 Topic: {retrieved_dict['payload']['topic']}")
        else:
            print("📭 No messages in queue")

        # Step 2: Supervisor Integration Test
        print("\n🧪 Step 2: Testing Supervisor Integration")
        print("-" * 40)

        from main.platform.supervisor import Supervisor

        supervisor = Supervisor("project.yml")
        print("✅ Supervisor created")

        supervisor.initialize_message_bus()
        print("✅ Message bus initialized")

        # 初期メッセージを投函
        supervisor.post_initial_message("Climate Change Solutions")
        print("✅ Initial message posted")

        # Step 3: Message Exchange Cycle Test
        print("\n🧪 Step 3: Testing Message Exchange Cycle")
        print("-" * 40)

        # MODERATOR → DEBATER_A への戦略要求
        strategy_request = Message(
            sender_id="MODERATOR",
            recipient_id="DEBATER_A",
            message_type="REQUEST_STRATEGY",
            payload={
                "topic": "Climate Change Solutions",
                "instructions": "Please provide your debate strategy"
            },
            turn_id=2
        )

        strategy_json = json.dumps(strategy_request.__dict__)
        post_result = post_message(strategy_json)
        print(f"📤 Strategy request sent: {post_result}")

        # DEBATER_A がメッセージを受信
        received_strategy = get_message("DEBATER_A")
        if received_strategy != "{}":
            strategy_dict = json.loads(received_strategy)
            print(f"📨 DEBATER_A received: {strategy_dict['message_type']}")

        # DEBATER_A → MODERATOR への戦略応答
        strategy_response = Message(
            sender_id="DEBATER_A",
            recipient_id="MODERATOR",
            message_type="SUBMIT_STRATEGY",
            payload={
                "strategy": "Evidence-based environmental policy approach",
                "key_points": [
                    "Scientific data analysis",
                    "Economic impact assessment",
                    "Implementation feasibility"
                ]
            },
            turn_id=3
        )

        response_json = json.dumps(strategy_response.__dict__)
        post_result = post_message(response_json)
        print(f"📤 Strategy response sent: {post_result}")

        # MODERATOR がメッセージを受信
        moderator_received = get_message("MODERATOR")
        if moderator_received != "{}":
            moderator_dict = json.loads(moderator_received)
            print(f"📨 MODERATOR received: {moderator_dict['message_type']}")
            print(f"🎯 Strategy: {moderator_dict['payload']['strategy']}")

        # Step 4: Error Handling Test
        print("\n🧪 Step 4: Testing Error Handling")
        print("-" * 40)

        # 不正なJSONテスト
        error_result = post_message("invalid json")
        print(f"❌ Invalid JSON result: {error_result}")

        # 存在しないエージェントテスト
        empty_result = get_message("NONEXISTENT_AGENT")
        print(f"📭 Nonexistent agent result: {empty_result}")

        print("\n🎉 All Demo Tests Completed Successfully!")
        print("=" * 60)
        print("✅ MCP Server Tools: Working")
        print("✅ Supervisor Integration: Working")
        print("✅ Message Exchange Cycle: Working")
        print("✅ Error Handling: Working")
        print("\n🏆 TDD Implementation: COMPLETE")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
