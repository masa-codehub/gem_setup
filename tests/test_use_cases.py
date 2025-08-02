#!/usr/bin/env python3
"""
ユースケースのテスト
TDD: ビジネスロジックをテストファーストで作成
"""

from tests.test_application_interfaces import MockMessageBroker, MockLLMService
from main.domain.models import Message
from main.application.use_cases import (
    SubmitStatementUseCase,
    SubmitRebuttalUseCase,
    SubmitJudgementUseCase
)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockPromptRepository:
    """テスト用のモックプロンプトリポジトリ"""

    def __init__(self, persona: str = "Test persona"):
        self.persona = persona

    def get_persona(self, agent_id: str) -> str:
        return self.persona


class MockDebateHistoryService:
    """テスト用のモック討論履歴サービス"""

    def __init__(self, history: list = None):
        self.history = history or []

    def get_debate_history(self) -> list:
        return self.history


class TestSubmitStatementUseCase:
    """立論提出ユースケースのテスト"""

    def test_execute_statement_submission(self):
        """立論提出が正しく実行されることをテスト"""
        # Arrange
        broker = MockMessageBroker()
        llm = MockLLMService("Generated statement content")
        prompt_repo = MockPromptRepository("Pro-AI debater persona")

        use_case = SubmitStatementUseCase(
            llm_service=llm,
            message_broker=broker,
            prompt_repository=prompt_repo
        )

        # Act
        use_case.execute(
            topic="AI is beneficial",
            sender_id="DEBATER_A",
            turn_id=1
        )

        # Assert
        assert len(broker.posted_messages) == 1
        posted_msg = broker.posted_messages[0]
        assert posted_msg.message_type == "SUBMIT_STATEMENT"
        assert posted_msg.sender_id == "DEBATER_A"
        assert posted_msg.recipient_id == "MODERATOR"
        assert posted_msg.payload["content"] == "Generated statement content"
        assert posted_msg.turn_id == 2  # turn_id + 1

        # LLMに正しいプロンプトが送られたかチェック
        assert "Pro-AI debater persona" in llm.last_prompt
        assert "AI is beneficial" in llm.last_prompt

    def test_execute_with_different_agents(self):
        """異なるエージェントでの立論提出をテスト"""
        broker = MockMessageBroker()
        llm = MockLLMService("Anti-AI statement")
        prompt_repo = MockPromptRepository("Anti-AI debater persona")

        use_case = SubmitStatementUseCase(
            llm_service=llm,
            message_broker=broker,
            prompt_repository=prompt_repo
        )

        use_case.execute(
            topic="AI dangers",
            sender_id="DEBATER_N",
            turn_id=3
        )

        posted_msg = broker.posted_messages[0]
        assert posted_msg.sender_id == "DEBATER_N"
        assert posted_msg.turn_id == 4


class TestSubmitRebuttalUseCase:
    """反駁提出ユースケースのテスト"""

    def test_execute_rebuttal_submission(self):
        """反駁提出が正しく実行されることをテスト"""
        # Arrange
        broker = MockMessageBroker()
        llm = MockLLMService("Generated rebuttal content")
        prompt_repo = MockPromptRepository("Logical debater")
        history_service = MockDebateHistoryService([
            {"sender": "DEBATER_A", "content": "AI is beneficial"}
        ])

        use_case = SubmitRebuttalUseCase(
            llm_service=llm,
            message_broker=broker,
            prompt_repository=prompt_repo,
            history_service=history_service
        )

        # Act
        use_case.execute(
            topic="AI debate",
            sender_id="DEBATER_N",
            turn_id=2
        )

        # Assert
        assert len(broker.posted_messages) == 1
        posted_msg = broker.posted_messages[0]
        assert posted_msg.message_type == "SUBMIT_REBUTTAL"
        assert posted_msg.sender_id == "DEBATER_N"

        # 履歴がプロンプトに含まれているかチェック
        assert "AI is beneficial" in llm.last_prompt


class TestSubmitJudgementUseCase:
    """判定提出ユースケースのテスト"""

    def test_execute_judgement_submission(self):
        """判定提出が正しく実行されることをテスト"""
        # Arrange
        broker = MockMessageBroker()
        llm = MockLLMService("""
DEBATER_A 採点:
- 論理性と一貫性: 8/10点
- 証拠と根拠: 7/10点
- 反駁の効果性: 9/10点
- 最終弁論: 8/10点
- 総合評価: 8/10点
- 合計: 40/50点

DEBATER_N 採点:
- 論理性と一貫性: 7/10点
- 証拠と根拠: 6/10点
- 反駁の効果性: 8/10点
- 最終弁論: 7/10点
- 総合評価: 7/10点
- 合計: 35/50点
        """)
        prompt_repo = MockPromptRepository("Fair judge")
        history_service = MockDebateHistoryService([
            {"sender": "DEBATER_A", "content": "Statement A"},
            {"sender": "DEBATER_N", "content": "Statement N"}
        ])

        use_case = SubmitJudgementUseCase(
            llm_service=llm,
            message_broker=broker,
            prompt_repository=prompt_repo,
            history_service=history_service
        )

        # Act
        use_case.execute(
            topic="AI debate",
            sender_id="JUDGE_L",
            turn_id=5
        )

        # Assert
        assert len(broker.posted_messages) == 1
        posted_msg = broker.posted_messages[0]
        assert posted_msg.message_type == "SUBMIT_JUDGEMENT"
        assert posted_msg.sender_id == "JUDGE_L"

        # スコア抽出のチェック
        scores = posted_msg.payload["scores"]
        assert scores["debater_a"] == 40
        assert scores["debater_n"] == 35
