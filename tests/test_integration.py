#!/usr/bin/env python3
"""
統合テスト - ファイル依存性完全排除版
TDD思想: 外部依存を排除して高速で予測可能なテストを実現
"""

from unittest.mock import MagicMock
from main.entities.models import Message
from main.interface_adapters.controllers.agent_orchestrator import (
    AgentOrchestrator
)


class TestAgentOrchestratorTDD:
    """エージェントオーケストレーターのTDD統合テスト"""

    def test_debater_statement_flow_without_file_dependencies(
        self, mock_gemini_service, initialized_message_broker
    ):
        """討論者の立論フロー - ファイル依存なし版"""
        # Given: モックベースのオーケストレーター
        orchestrator = AgentOrchestrator("DEBATER_A")

        # 依存性注入でファイル依存を排除
        orchestrator.message_broker = initialized_message_broker
        orchestrator.gemini_service = mock_gemini_service

        # ReActサービスもモック化
        mock_react_service = MagicMock()
        mock_react_service._test_mode = True  # テストモードフラグを設定
        mock_response = Message(
            sender_id="DEBATER_A",
            recipient_id="MODERATOR",
            message_type="SUBMIT_STATEMENT",
            payload={"statement": "AI brings significant benefits to society"},
            turn_id=2
        )
        mock_react_service.think_and_act.return_value = mock_response
        orchestrator.react_service = mock_react_service

        # 立論要求メッセージ作成
        message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": "AI benefits"},
            turn_id=1
        )

        # When: メッセージ処理
        result = orchestrator._handle_message(message)

        # Then: 正常終了と応答メッセージの確認
        assert result is None  # 正常終了

        # ReActサービスが適切に呼び出されたことを確認
        mock_react_service.think_and_act.assert_called_once()

        # メッセージがポストされたことを確認
        posted_message = initialized_message_broker.get_message("MODERATOR")
        assert posted_message is not None
        assert posted_message.message_type == "SUBMIT_STATEMENT"
        assert posted_message.sender_id == "DEBATER_A"
        assert "statement" in posted_message.payload

    def test_judge_judgement_flow_without_file_dependencies(
        self, mock_gemini_service, initialized_message_broker
    ):
        """ジャッジの判定フロー - ファイル依存なし版"""
        # Given: モックベースのジャッジオーケストレーター
        orchestrator = AgentOrchestrator("JUDGE_L")
        orchestrator.message_broker = initialized_message_broker
        orchestrator.gemini_service = mock_gemini_service

        # ReActサービスもモック化
        mock_react_service = MagicMock()
        mock_react_service._test_mode = True  # テストモードフラグを設定
        mock_judgement = Message(
            sender_id="JUDGE_L",
            recipient_id="MODERATOR",
            message_type="SUBMIT_JUDGEMENT",
            payload={
                "judgement": "DEBATER_A: 42/50点",
                "reasoning": "Logical argument structure"
            },
            turn_id=3
        )
        mock_react_service.think_and_act.return_value = mock_judgement
        orchestrator.react_service = mock_react_service

        # 判定要求メッセージ作成
        judgement_request = Message(
            recipient_id="JUDGE_L",
            sender_id="MODERATOR",
            message_type="REQUEST_JUDGEMENT",
            payload={"debate_summary": "AI discussion completed"},
            turn_id=2
        )

        # When: メッセージ処理
        result = orchestrator._handle_message(judgement_request)

        # Then: 正常終了と判定メッセージの確認
        assert result is None

        judgement_message = initialized_message_broker.get_message("MODERATOR")
        assert judgement_message is not None
        assert judgement_message.message_type == "SUBMIT_JUDGEMENT"
        assert judgement_message.sender_id == "JUDGE_L"
        assert "judgement" in judgement_message.payload

    def test_error_handling_without_file_dependencies(
        self, initialized_message_broker
    ):
        """エラーハンドリング - ファイル依存なし版"""
        # Given: サービスなしのオーケストレーター
        orchestrator = AgentOrchestrator("DEBATER_A")
        orchestrator.message_broker = initialized_message_broker
        orchestrator.gemini_service = None  # 意図的にサービスをNoneに設定

        # ReActサービスも意図的にNoneに設定
        orchestrator.react_service = None

        invalid_message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="INVALID_MESSAGE_TYPE",
            payload={"invalid": "data"},
            turn_id=1
        )

        # When: 無効なメッセージを処理
        result = orchestrator._handle_message(invalid_message)

        # Then: エラーが適切に処理される
        assert result is None  # 例外なく終了することを確認

    def test_end_debate_signal_without_file_dependencies(
        self, initialized_message_broker
    ):
        """討論終了信号処理 - ファイル依存なし版"""
        # Given
        orchestrator = AgentOrchestrator("MODERATOR")
        orchestrator.message_broker = initialized_message_broker

        end_message = Message(
            recipient_id="MODERATOR",
            sender_id="SYSTEM",
            message_type="END_DEBATE",
            payload={"results": "Debate completed successfully"},
            turn_id=10
        )

        # When
        result = orchestrator._handle_message(end_message)

        # Then: END_DEBATEメッセージは"EXIT"を返す
        assert result == "EXIT"
