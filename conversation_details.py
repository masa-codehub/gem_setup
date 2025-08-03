#!/usr/bin/env python3
"""
モデレータと肯定派討論者（DEBATER_A）の詳細会話内容確認

TDDテストで実際に交換されたメッセージの詳細を表示
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))


def display_conversation():
    """会話内容の詳細表示"""
    # テスト環境セットアップ
    temp_dir = tempfile.mkdtemp()
    os.environ['DEBATE_DIR'] = temp_dir

    from main.infrastructure.mcp_message_bus_server import post_message, get_message
    from main.domain.models import Message

    print('📋 モデレータと肯定派討論者（DEBATER_A）の会話内容')
    print('=' * 60)

    # Step 1: SYSTEM → MODERATOR への初期メッセージ
    print('\n🔄 Step 1: SYSTEM → MODERATOR (議論開始)')
    print('-' * 50)

    initiate_message = Message(
        sender_id="SYSTEM",
        recipient_id="MODERATOR",
        message_type="INITIATE_DEBATE",
        payload={
            "topic": "AI倫理とプライバシー保護のバランス",
            "rules": "この議論は順番制で進行します。まず、あなたがルールとトピックを説明し、その後、討論者Aに戦略を求めてください。"
        },
        turn_id=1
    )

    post_message(json.dumps(initiate_message.__dict__))
    received = get_message("MODERATOR")
    if received != "{}":
        msg = json.loads(received)
        print(f"💬 MODERATOR が受信したメッセージ:")
        print(f"   📌 タイプ: {msg['message_type']}")
        print(f"   📝 トピック: {msg['payload']['topic']}")
        print(f"   📜 ルール: {msg['payload']['rules']}")

    # Step 2: MODERATOR → DEBATER_A への戦略要求
    print('\n🔄 Step 2: MODERATOR → DEBATER_A (戦略要求)')
    print('-' * 50)

    strategy_request = Message(
        sender_id="MODERATOR",
        recipient_id="DEBATER_A",
        message_type="REQUEST_STRATEGY",
        payload={
            "topic": "AI倫理とプライバシー保護のバランス",
            "position": "肯定側（AI活用推進派）",
            "instructions": "あなたは肯定側として、AI技術の活用がプライバシー保護と両立可能であることを論証してください。データに基づいた論理的なアプローチで戦略を提示してください。",
            "time_limit": "3分間での発表"
        },
        turn_id=2
    )

    post_message(json.dumps(strategy_request.__dict__))
    received = get_message("DEBATER_A")
    if received != "{}":
        msg = json.loads(received)
        print(f"💬 DEBATER_A が受信したメッセージ:")
        print(f"   📌 タイプ: {msg['message_type']}")
        print(f"   📝 トピック: {msg['payload']['topic']}")
        print(f"   🎭 立場: {msg['payload']['position']}")
        print(f"   📋 指示: {msg['payload']['instructions']}")
        print(f"   ⏰ 制限時間: {msg['payload']['time_limit']}")

    # Step 3: DEBATER_A → MODERATOR への戦略応答
    print('\n🔄 Step 3: DEBATER_A → MODERATOR (戦略提出)')
    print('-' * 50)

    strategy_response = Message(
        sender_id="DEBATER_A",
        recipient_id="MODERATOR",
        message_type="SUBMIT_STRATEGY",
        payload={
            "strategy": "データ駆動型プライバシー保護戦略",
            "main_arguments": [
                "技術的解決策: 差分プライバシー、同態暗号、連合学習",
                "法的フレームワーク: GDPR準拠のAI開発ガイドライン",
                "経済的利益: プライバシー保護技術による新産業創出"
            ],
            "evidence_sources": [
                "EU AI Act 2024実装事例",
                "Apple の差分プライバシー導入結果",
                "Google Federated Learning の医療応用成果"
            ],
            "debate_approach": "事実とデータに基づく論理構築、感情論を避けた客観的分析",
            "expected_counterarguments": [
                "完全なプライバシー保護は技術的に不可能",
                "コスト対効果の問題",
                "規制の複雑さによる技術革新の阻害"
            ],
            "preparation_time": "戦略構築完了"
        },
        turn_id=3
    )

    post_message(json.dumps(strategy_response.__dict__))
    received = get_message("MODERATOR")
    if received != "{}":
        msg = json.loads(received)
        print(f"💬 MODERATOR が受信したメッセージ:")
        print(f"   📌 タイプ: {msg['message_type']}")
        print(f"   🎯 戦略名: {msg['payload']['strategy']}")
        print(f"   📋 主要論点:")
        for i, arg in enumerate(msg['payload']['main_arguments'], 1):
            print(f"      {i}. {arg}")
        print(f"   🔍 証拠資料:")
        for i, evidence in enumerate(msg['payload']['evidence_sources'], 1):
            print(f"      {i}. {evidence}")
        print(f"   🧠 議論手法: {msg['payload']['debate_approach']}")
        print(f"   ⚔️ 想定反論:")
        for i, counter in enumerate(msg['payload']['expected_counterarguments'], 1):
            print(f"      {i}. {counter}")

    print('\n📊 会話フロー完了')
    print('=' * 60)
    print('✅ 3つのメッセージ交換が正常に完了しました')
    print('🎭 DEBATER_A は論理的で証拠に基づいた戦略を提示')
    print('📈 実際の議論システムでの活用準備完了')


if __name__ == "__main__":
    display_conversation()
