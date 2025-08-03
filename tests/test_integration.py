#!/usr/bin/env python3
"""
統合テスト
クリーンアーキテクチャ全体の動作をテスト
"""

from main.entities.models import Message
from main.interface_adapters.controllers.agent_orchestrator import AgentOrchestrator
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAgentOrchestrator:
    """エージェントオーケストレーターの統合テスト"""

    @patch('subprocess.run')
    def test_debater_statement_flow(self, mock_run):
        """討論者の立論フローの統合テスト - 新アーキテクチャ対応"""
        # Mockの設定 - 適切なJSONレスポンスを返す
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''```json
{
    "recipient_id": "MODERATOR",
    "message_type": "SUBMIT_STATEMENT",
    "payload": {
        "statement": "AI brings significant benefits to society"
    }
}
```'''
        mock_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as temp_dir:
            # 環境変数設定
            os.environ["DEBATE_DIR"] = temp_dir

            # テスト用ペルソナファイル作成
            config_dir = os.path.join(temp_dir, "config")
            os.makedirs(config_dir, exist_ok=True)
            with open(os.path.join(config_dir, "debater_a.md"), 'w') as f:
                f.write("You are a pro-AI debater.")

            # オーケストレーター作成
            orchestrator = AgentOrchestrator("DEBATER_A")

            # 立論要求メッセージ作成
            message = Message(
                recipient_id="DEBATER_A",
                sender_id="MODERATOR",
                message_type="PROMPT_FOR_STATEMENT",
                payload={"topic": "AI benefits"},
                turn_id=1
            )

            # メッセージ処理
            result = orchestrator._handle_message(message)

            # 結果検証
            assert result is None  # 正常終了

            # 投稿されたメッセージを確認（新しいGeminiServiceは既知パターンで応答）
            posted_message = orchestrator.message_broker.get_message(
                "MODERATOR"
            )
            assert posted_message is not None
            assert posted_message.message_type == "SUBMIT_STATEMENT"
            assert posted_message.sender_id == "DEBATER_A"
            # 新しいGeminiServiceの実際の応答パターンに合わせる
            assert "statement" in posted_message.payload

    @patch('subprocess.run')
    def test_judge_judgement_flow(self, mock_run):
        """ジャッジの判定フローの統合テスト - 新アーキテクチャ対応"""
        # Mockの設定 - ジャッジメントレスポンス
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '''```json
{
    "recipient_id": "MODERATOR",
    "message_type": "SUBMIT_JUDGEMENT",
    "payload": {
        "judgement": "DEBATER_A: 42/50点",
        "reasoning": "Logical argument structure"
    }
}
```'''
        mock_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["DEBATE_DIR"] = temp_dir

            # テスト用ペルソナファイル作成
            config_dir = os.path.join(temp_dir, "config")
            os.makedirs(config_dir, exist_ok=True)
            with open(os.path.join(config_dir, "judge_l.md"), 'w') as f:
                f.write("You are a logical judge.")

            # 既存の議論履歴を作成
            orchestrator = AgentOrchestrator("JUDGE_L")

            # 事前に討論メッセージを挿入
            debate_msg_a = Message(
                recipient_id="MODERATOR",
                sender_id="DEBATER_A",
                message_type="SUBMIT_STATEMENT",
                payload={"content": "AI is beneficial"},
                turn_id=1
            )
            orchestrator.message_broker.post_message(debate_msg_a)

            debate_msg_n = Message(
                recipient_id="MODERATOR",
                sender_id="DEBATER_N",
                message_type="SUBMIT_STATEMENT",
                payload={"content": "AI is harmful"},
                turn_id=2
            )
            orchestrator.message_broker.post_message(debate_msg_n)

            # 履歴を既読にする（実際の履歴として扱う）
            _ = orchestrator.message_broker.get_message("MODERATOR")
            _ = orchestrator.message_broker.get_message("MODERATOR")

            # 判定要求メッセージ作成
            judgement_request = Message(
                recipient_id="JUDGE_L",
                sender_id="MODERATOR",
                message_type="REQUEST_JUDGEMENT",
                payload={},
                turn_id=5
            )

            # メッセージ処理
            result = orchestrator._handle_message(judgement_request)

            # 結果検証
            assert result is None

            # 投稿された判定を確認（新しいGeminiServiceの応答形式に合わせる）
            judgement_message = orchestrator.message_broker.get_message(
                "MODERATOR"
            )
            assert judgement_message is not None
            assert judgement_message.message_type == "SUBMIT_JUDGEMENT"
            assert judgement_message.sender_id == "JUDGE_L"

            # 判定内容の確認（新しい応答フォーマットに合わせる）
            assert "judgement" in judgement_message.payload
            assert ("DEBATER_A: 42/50点" in
                    judgement_message.payload["judgement"])

    @patch('subprocess.run')
    def test_error_handling(self, mock_run):
        """エラーハンドリングの統合テスト - 新アーキテクチャ対応"""
        # Mockの設定 - エラーレスポンス
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "API Error occurred"
        mock_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["DEBATE_DIR"] = temp_dir

            orchestrator = AgentOrchestrator("DEBATER_A")

            # 未知のメッセージタイプでエラーを発生させる
            error_message = Message(
                recipient_id="DEBATER_A",
                sender_id="MODERATOR",
                message_type="UNKNOWN_MESSAGE_TYPE",  # 未知のタイプ
                payload={},
                turn_id=1
            )

            # メッセージ処理（エラーが発生するはず）
            result = orchestrator._handle_message(error_message)

            # エラー時でも正常終了することを確認
            assert result is None

            # 現在のGeminiServiceはデフォルトでSYSTEM_ERRORを返す
            error_notification = orchestrator.message_broker.get_message(
                "MODERATOR"
            )
            assert error_notification is not None
            # 新しいアーキテクチャでは、AgentLoopがエラーをキャッチして
            # 適切にメッセージを送信する
            assert error_notification.sender_id == "DEBATER_A"

    def test_end_debate_signal(self):
        """討論終了シグナルのテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["DEBATE_DIR"] = temp_dir

            orchestrator = AgentOrchestrator("DEBATER_A")

            # 討論終了メッセージ
            end_message = Message(
                recipient_id="DEBATER_A",
                sender_id="MODERATOR",
                message_type="END_DEBATE",
                payload={},
                turn_id=10
            )

            # メッセージ処理
            result = orchestrator._handle_message(end_message)

            # EXIT を返すことを確認
            assert result == "EXIT"
