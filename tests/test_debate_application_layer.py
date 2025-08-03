"""
TDD: ディベート固有モデルのアプリケーション層移行テスト

Kent BeckのTDD思想に従い、ディベート固有のビジネスロジックを
ドメイン層からアプリケーション層に移行するためのテストを定義する。
"""

import pytest
from unittest.mock import patch


class TestDebateSpecificApplicationModels:
    """ディベート固有のモデルがアプリケーション層に移行されたことをテスト"""

    def test_debate_session_is_in_application_layer(self):
        """ディベートセッションがアプリケーション層に移動している"""
        from main.use_cases.models import DebateSession
        from main.entities.models import Session, Message

        # ドメインレベルのSessionを使ってディベート専用のセッションを作成
        debate_session = DebateSession(
            base_session=Session(
                session_id="DEBATE_001",
                objective="AI Ethics Debate",
                participants=["DEBATER_A", "DEBATER_N", "MODERATOR"],
                status="RUNNING"
            ),
            topic="AI Ethics in Healthcare",
            current_phase="statement"
        )

        assert debate_session.base_session.session_id == "DEBATE_001"
        assert debate_session.topic == "AI Ethics in Healthcare"
        assert debate_session.current_phase == "statement"

    def test_debate_statement_is_in_application_layer(self):
        """ディベートの発言がアプリケーション層に移動している"""
        from main.use_cases.models import DebateStatement

        statement = DebateStatement(
            author_id="DEBATER_A",
            content="AI in healthcare should be regulated",
            statement_type="opening",
            turn_number=1
        )

        assert statement.author_id == "DEBATER_A"
        assert statement.content == "AI in healthcare should be regulated"
        assert statement.statement_type == "opening"
        assert statement.turn_number == 1
        assert statement.created_at is not None

    def test_judgement_score_is_in_application_layer(self):
        """判定スコアがアプリケーション層に移動している"""
        from main.use_cases.models import JudgementScore

        score = JudgementScore(
            debater_a_score=35,
            debater_n_score=25,
            judge_id="JUDGE_L",
            reasoning="DEBATER_A presented stronger arguments"
        )

        assert score.debater_a_score == 35
        assert score.debater_n_score == 25
        assert score.judge_id == "JUDGE_L"
        assert score.reasoning == "DEBATER_A presented stronger arguments"

    def test_debate_phase_is_in_application_layer(self):
        """ディベートフェーズがアプリケーション層に移動している"""
        from main.use_cases.models import DebatePhase

        phase = DebatePhase(
            phase="statement",
            participants=["DEBATER_A", "DEBATER_N"],
            completed_participants=[]
        )

        assert phase.phase == "statement"
        assert len(phase.participants) == 2
        assert phase.completed_participants == []

        # フェーズの進行ロジック
        phase.mark_participant_done("DEBATER_A")
        assert "DEBATER_A" in phase.completed_participants
        assert not phase.is_complete()

        phase.mark_participant_done("DEBATER_N")
        assert phase.is_complete()


class TestDebateServiceIntegration:
    """ディベートサービスがドメインモデルと正しく統合されているかテスト"""

    def test_debate_service_uses_generic_domain_models(self):
        """ディベートサービスが汎用ドメインモデルを使用している"""
        from main.use_cases.services.debate_service import DebateService
        from main.entities.models import Message, Session

        service = DebateService()

        # 汎用的なセッション開始メッセージ
        start_message = Message(
            recipient_id="MODERATOR",
            sender_id="SYSTEM",
            message_type="START_SESSION",
            payload={"session_type": "debate", "topic": "AI Ethics"},
            turn_id=0
        )

        # ディベートサービスが次のアクションを決定
        next_message = service.determine_next_action(start_message)

        assert next_message.message_type == "PROMPT_FOR_STATEMENT"
        assert next_message.recipient_id == "DEBATER_A"
        assert next_message.payload["topic"] == "AI Ethics"
        assert next_message.turn_id == 1

    def test_debate_service_handles_generic_message_flow(self):
        """ディベートサービスが汎用メッセージフローを処理できる"""
        from main.use_cases.services.debate_service import DebateService
        from main.entities.models import Message

        service = DebateService()

        # 発言提出メッセージ
        statement_message = Message(
            recipient_id="MODERATOR",
            sender_id="DEBATER_A",
            message_type="SUBMIT_RESPONSE",
            payload={
                "response_type": "statement",
                "content": "AI should be regulated in healthcare"
            },
            turn_id=1
        )

        next_message = service.determine_next_action(statement_message)

        assert next_message.message_type == "PROMPT_FOR_STATEMENT"
        assert next_message.recipient_id == "DEBATER_N"
        assert next_message.turn_id == 2
