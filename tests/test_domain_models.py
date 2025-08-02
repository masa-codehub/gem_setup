#!/usr/bin/env python3
"""
ドメインモデルのテスト
TDD: まずテストから書き始める
"""

from main.domain.models import Message, Statement, Agent, DebatePhase
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMessage:
    """Messageドメインモデルのテスト"""

    def test_message_creation(self):
        """メッセージを正しく作成できることをテスト"""
        message = Message(
            recipient_id="MODERATOR",
            sender_id="DEBATER_A",
            message_type="SUBMIT_STATEMENT",
            payload={"content": "Test content"},
            turn_id=1
        )

        assert message.recipient_id == "MODERATOR"
        assert message.sender_id == "DEBATER_A"
        assert message.message_type == "SUBMIT_STATEMENT"
        assert message.payload["content"] == "Test content"
        assert message.turn_id == 1

    def test_message_with_timestamp(self):
        """タイムスタンプが自動で設定されることをテスト"""
        message = Message(
            recipient_id="MODERATOR",
            sender_id="DEBATER_A",
            message_type="SUBMIT_STATEMENT",
            payload={"content": "Test content"},
            turn_id=1
        )

        assert message.timestamp is not None
        assert isinstance(message.timestamp, str)


class TestStatement:
    """Statementドメインモデルのテスト"""

    def test_statement_creation(self):
        """声明を正しく作成できることをテスト"""
        statement = Statement(
            author_id="DEBATER_A",
            content="AI is beneficial for humanity"
        )

        assert statement.author_id == "DEBATER_A"
        assert statement.content == "AI is beneficial for humanity"


class TestAgent:
    """Agentドメインモデルのテスト"""

    def test_agent_creation(self):
        """エージェントを正しく作成できることをテスト"""
        agent = Agent(
            agent_id="DEBATER_A",
            role="debater",
            persona="You are a pro-AI debater"
        )

        assert agent.agent_id == "DEBATER_A"
        assert agent.role == "debater"
        assert agent.persona == "You are a pro-AI debater"

    def test_judge_agent_creation(self):
        """ジャッジエージェントを正しく作成できることをテスト"""
        judge = Agent(
            agent_id="JUDGE_L",
            role="judge",
            persona="You are a logical judge"
        )

        assert judge.agent_id == "JUDGE_L"
        assert judge.role == "judge"


class TestDebatePhase:
    """DebatePhaseドメインモデルのテスト"""

    def test_debate_phase_creation(self):
        """討論フェーズを正しく作成できることをテスト"""
        phase = DebatePhase(
            phase="statement",
            participants=["DEBATER_A", "DEBATER_N"]
        )

        assert phase.phase == "statement"
        assert "DEBATER_A" in phase.participants
        assert "DEBATER_N" in phase.participants

    def test_phase_completion(self):
        """フェーズ完了状態をテスト"""
        phase = DebatePhase(
            phase="rebuttal",
            participants=["DEBATER_A", "DEBATER_N"]
        )

        assert not phase.is_complete()

        phase.mark_participant_done("DEBATER_A")
        assert not phase.is_complete()

        phase.mark_participant_done("DEBATER_N")
        assert phase.is_complete()
