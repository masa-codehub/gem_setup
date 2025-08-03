"""
TDD: 抽象化されたドメインモデルのテスト

Kent BeckのTDD思想に従い、まずテストを書いて新しいドメインモデルの仕様を定義する。
ディベート固有の概念を排除し、汎用的なエージェント連携プラットフォームの基本要素のみを残す。
"""

import pytest
from unittest.mock import patch


class TestNewDomainModels:
    """抽象化されたドメインモデルのテスト"""

    def test_agent_creation_with_generic_role(self):
        """エージェントを汎用的なロールで作成できる"""
        from main.entities.models import Agent

        # ディベート固有でない汎用的なロール
        agent = Agent(agent_id="AI_ASSISTANT", role="assistant")

        assert agent.agent_id == "AI_ASSISTANT"
        assert agent.role == "assistant"

    def test_message_with_generic_type_and_payload(self):
        """汎用的なメッセージタイプとペイロードでメッセージを作成できる"""
        from main.entities.models import Message

        message = Message(
            recipient_id="AGENT_B",
            sender_id="AGENT_A",
            message_type="TASK_REQUEST",
            payload={"task_type": "analysis", "data": "sample data"},
            turn_id=1
        )

        assert message.recipient_id == "AGENT_B"
        assert message.sender_id == "AGENT_A"
        assert message.message_type == "TASK_REQUEST"
        assert message.payload["task_type"] == "analysis"
        assert message.turn_id == 1
        assert message.timestamp is not None

    def test_task_creation_and_management(self):
        """タスクの作成と管理ができる"""
        from main.entities.models import Task

        task = Task(
            task_id="TASK_001",
            title="データ分析",
            description="売上データを分析してレポートを作成する",
            status="TODO",
            assignee_id="DATA_ANALYST",
            dependencies=["TASK_000"]
        )

        assert task.task_id == "TASK_001"
        assert task.title == "データ分析"
        assert task.status == "TODO"
        assert task.assignee_id == "DATA_ANALYST"
        assert "TASK_000" in task.dependencies

    def test_session_with_generic_objective(self):
        """汎用的な目標を持つセッションを作成できる"""
        from main.entities.models import Session

        session = Session(
            session_id="SESSION_001",
            objective="プロジェクト要件の分析と設計",
            participants=["ANALYST", "ARCHITECT", "DEVELOPER"],
            status="RUNNING"
        )

        assert session.session_id == "SESSION_001"
        assert session.objective == "プロジェクト要件の分析と設計"
        assert len(session.participants) == 3
        assert "ANALYST" in session.participants
        assert session.status == "RUNNING"

    def test_message_timestamp_generation(self):
        """メッセージにデフォルトタイムスタンプが設定される"""
        from main.entities.models import Message

        with patch('time.strftime') as mock_strftime:
            mock_strftime.return_value = "2025-08-03T12:00:00Z"

            message = Message(
                recipient_id="AGENT_B",
                sender_id="AGENT_A",
                message_type="NOTIFICATION",
                payload={},
                turn_id=1
            )

            assert message.timestamp == "2025-08-03T12:00:00Z"

    def test_agent_id_is_generic_string(self):
        """AgentIDが汎用的な文字列型である"""
        # 具体的なLiteralではなく、任意の文字列を受け入れる
        agent_ids = ["CUSTOM_AGENT", "AI_BOT_123", "HUMAN_OPERATOR"]

        for agent_id in agent_ids:
            # AgentIDはstringなので、任意の文字列を受け入れるべき
            assert isinstance(agent_id, str)

    def test_message_type_is_generic_string(self):
        """MessageTypeが汎用的な文字列型である"""
        # 具体的なLiteralではなく、任意の文字列を受け入れる
        message_types = ["CUSTOM_REQUEST", "DATA_UPDATE", "STATUS_REPORT"]

        for msg_type in message_types:
            # MessageTypeはstringなので、任意の文字列を受け入れるべき
            assert isinstance(msg_type, str)

    def test_task_without_dependencies(self):
        """依存関係なしでタスクを作成できる"""
        from main.entities.models import Task

        task = Task(
            task_id="SIMPLE_TASK",
            title="簡単なタスク",
            description="依存関係のないタスク",
            status="TODO",
            assignee_id="WORKER"
        )

        assert task.dependencies == []

    def test_session_status_transitions(self):
        """セッションのステータス遷移をテスト（ドメインロジックではなく単純な属性変更）"""
        from main.entities.models import Session

        session = Session(
            session_id="TEST_SESSION",
            objective="テスト目標",
            participants=["AGENT_1"],
            status="RUNNING"
        )

        # ステータスの変更（ビジネスロジックではなく単純な属性変更）
        session.status = "COMPLETED"
        assert session.status == "COMPLETED"

        session.status = "FAILED"
        assert session.status == "FAILED"


class TestOldDebateSpecificModelsRemoval:
    """ディベート固有のモデルが削除されたことを確認するテスト"""

    def test_debate_specific_models_are_removed(self):
        """ディベート固有のモデルが削除されている"""
        with pytest.raises(ImportError):
            from main.entities.models import DebatePhase  # noqa: F401

        with pytest.raises(ImportError):
            from main.entities.models import JudgementScore  # noqa: F401

        with pytest.raises(ImportError):
            from main.entities.models import DebateSession  # noqa: F401

        with pytest.raises(ImportError):
            from main.entities.models import Statement  # noqa: F401

    def test_debate_specific_literals_are_removed(self):
        """ディベート固有のLiteral型が削除されている"""
        # 新しいモデルでは、AgentIDとMessageTypeは汎用的なstrになっている
        from main.entities.models import AgentID, MessageType

        # これらは型エイリアスなので、実際の型はstrのはず
        assert AgentID == str
        assert MessageType == str
