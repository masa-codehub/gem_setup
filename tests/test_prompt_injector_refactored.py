"""
TDD: プロンプトインジェクターサービスのリファクタリングテスト

Kent BeckのTDD思想に従い、プロンプト生成の責務を
インフラストラクチャ層で明確に分離するためのテストを定義する。
"""

import pytest
from unittest.mock import Mock


class TestPromptInjectorService:
    """プロンプトインジェクターサービスのテスト"""

    def test_prompt_injector_builds_generic_prompt(self):
        """プロンプトインジェクターが汎用的なメッセージからプロンプトを構築する"""
        from main.frameworks_and_drivers.frameworks.prompt_injector_service import PromptInjectorService
        from main.entities.models import Message
        from main.use_cases.interfaces import IPromptRepository

        # モックリポジトリを作成
        mock_repo = Mock(spec=IPromptRepository)
        mock_repo.get_persona.return_value = "You are a helpful AI assistant."

        injector = PromptInjectorService(mock_repo)

        context_message = Message(
            recipient_id="AI_ASSISTANT",
            sender_id="USER",
            message_type="TASK_REQUEST",
            payload={"task": "analyze data", "context": "sales report"},
            turn_id=1
        )

        prompt = injector.build_prompt("AI_ASSISTANT", context_message)

        assert "You are a helpful AI assistant." in prompt
        assert "analyze data" in prompt
        assert "sales report" in prompt

    def test_prompt_injector_handles_debate_specific_context(self):
        """プロンプトインジェクターがディベート固有のコンテキストを処理できる"""
        from main.frameworks_and_drivers.frameworks.prompt_injector_service import PromptInjectorService
        from main.entities.models import Message
        from main.use_cases.interfaces import IPromptRepository

        mock_repo = Mock(spec=IPromptRepository)
        mock_repo.get_persona.return_value = "You are DEBATER_A in a formal debate."

        injector = PromptInjectorService(mock_repo)

        debate_message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={
                "topic": "AI Ethics",
                "phase": "opening_statement",
                "time_limit": "3 minutes"
            },
            turn_id=1
        )

        prompt = injector.build_prompt("DEBATER_A", debate_message)

        assert "You are DEBATER_A in a formal debate." in prompt
        assert "AI Ethics" in prompt
        assert "opening_statement" in prompt
        assert "3 minutes" in prompt

    def test_prompt_injector_formats_message_history(self):
        """プロンプトインジェクターがメッセージ履歴を適切にフォーマットする"""
        from main.frameworks_and_drivers.frameworks.prompt_injector_service import PromptInjectorService
        from main.entities.models import Message
        from main.use_cases.interfaces import IPromptRepository

        mock_repo = Mock(spec=IPromptRepository)
        mock_repo.get_persona.return_value = "You are an analyst."

        injector = PromptInjectorService(mock_repo)

        current_message = Message(
            recipient_id="ANALYST",
            sender_id="SYSTEM",
            message_type="REQUEST_ANALYSIS",
            payload={"data": "quarterly_report.csv"},
            turn_id=3
        )

        history = [
            Message("ANALYST", "USER", "GREETING", {"message": "Hello"}, 1),
            Message("USER", "ANALYST", "RESPONSE", {"message": "Hi there"}, 2)
        ]

        prompt = injector.build_prompt("ANALYST", current_message, history)

        assert "You are an analyst." in prompt
        assert "Hello" in prompt
        assert "Hi there" in prompt
        assert "quarterly_report.csv" in prompt


class TestGeminiServiceIntegration:
    """GeminiServiceとPromptInjectorServiceの統合テスト"""

    def test_gemini_service_uses_prompt_injector(self):
        """GeminiServiceがPromptInjectorServiceを使用している"""
        from main.frameworks_and_drivers.frameworks.gemini_service import GeminiService
        from main.frameworks_and_drivers.frameworks.prompt_injector_service import PromptInjectorService
        from main.entities.models import Message
        from unittest.mock import Mock, patch

        # モックプロンプトインジェクター
        mock_injector = Mock(spec=PromptInjectorService)
        mock_injector.build_prompt.return_value = (
            "You are DEBATER_A. Topic: AI Ethics. Provide your opening statement."
        )

        service = GeminiService(mock_injector)

        message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": "AI Ethics"},
            turn_id=1
        )

        # gemini-cliの呼び出しをモック
        with patch.object(service, '_call_gemini_cli', return_value="AI should be regulated..."):
            with patch.object(service, '_parse_response') as mock_parse:
                mock_parse.return_value = Message(
                    recipient_id="MODERATOR",
                    sender_id="DEBATER_A",
                    message_type="SUBMIT_STATEMENT",
                    payload={"content": "AI should be regulated..."},
                    turn_id=2
                )

                result = service.generate_response("DEBATER_A", message)

                # プロンプトインジェクターが呼ばれたことを確認
                mock_injector.build_prompt.assert_called_once_with(
                    "DEBATER_A", message)
                assert result.message_type == "SUBMIT_STATEMENT"
