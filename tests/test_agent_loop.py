"""
Agent Controller のTDDテスト - Kent Beck TDD思想準拠
テストが設計を駆動し、外部依存を完全に排除した実装
"""
import pytest
from main.interface_adapters.controllers.agent_controller import (
    AgentController
)
from main.entities.models import Message


class TestAgentControllerTDD:
    """
    TDD原則に基づくAgentControllerのテスト
    Red -> Green -> Refactor のサイクルを重視
    """

    def test_should_process_message_without_file_dependencies(
        self, mock_gemini_service, initialized_message_broker
    ):
        """
        Red: AgentControllerは外部ファイルに依存せずにメッセージを処理できる

        TDD原則：
        - テストが要求を明確に示す
        - 外部依存を完全に排除
        - 高速で予測可能
        """
        # Given: 依存関係を注入してテスト対象を初期化
        agent_id = "MODERATOR"
        controller = AgentController(agent_id)

        # 外部の依存関係をモックに差し替える（依存性注入）
        controller.message_bus = initialized_message_broker
        controller.gemini_service = mock_gemini_service

        # テスト用の入力メッセージを準備
        incoming_message = Message(
            recipient_id=agent_id,
            sender_id="SYSTEM",
            message_type="INITIATE_DEBATE",
            payload={"topic": "TDD Test Topic"},
            turn_id=1
        )

        # When: メッセージを処理する
        controller._process_message(incoming_message)

        # Then: 期待される動作が実行されたことを検証
        # a) GeminiServiceが正しい引数で呼び出されたか
        mock_gemini_service.generate_structured_response.\
            assert_called_once_with(
                agent_id=agent_id,
                context=incoming_message
            )

        # b) メッセージバスに応答が投函されたか
        # モックが返すダミーレスポンスのrecipient_idに送信される
        response_msg = controller.message_bus.get_message("TEST_RECIPIENT")
        assert response_msg is not None
        assert response_msg.message_type == "MOCK_RESPONSE"
        assert "mock LLM response" in response_msg.payload["content"]

    def test_should_initialize_with_dependency_injection(self):
        """
        Red: AgentControllerは依存性注入により初期化できる

        TDD原則：設計の意図を明確に表現する
        """
        # Given & When: エージェントIDで初期化
        agent_id = "TEST_AGENT"
        controller = AgentController(agent_id)

        # Then: 基本的な属性が設定されている
        assert controller.agent_id == agent_id
        # 実際の依存関係は後から注入される（テスト時はモック）

    def test_should_handle_no_llm_service_gracefully(
        self, initialized_message_broker
    ):
        """
        Green: LLMサービスがない場合でも適切に処理する

        TDD原則：エッジケースも明確にテストする
        """
        # Given: LLMサービスなしのコントローラー
        controller = AgentController("TEST_AGENT")
        controller.message_bus = initialized_message_broker
        controller.gemini_service = None  # LLMサービスを意図的にNoneに設定

        test_message = Message(
            recipient_id="TEST_AGENT",
            sender_id="SYSTEM",
            message_type="TEST_MESSAGE",
            payload={"test": "data"},
            turn_id=1
        )

        # When: メッセージを処理（例外が発生しないことを確認）
        try:
            controller._process_message(test_message)
            # Then: 例外なく完了すればOK
            assert True
        except Exception as e:
            pytest.fail(f"Should handle missing LLM service gracefully: {e}")

    def test_should_create_response_message_correctly(
        self, mock_gemini_service, initialized_message_broker
    ):
        """
        Refactor: レスポンスメッセージの作成ロジックが正しく動作する

        TDD原則：内部実装の詳細もテストで検証
        """
        # Given
        controller = AgentController("MODERATOR")
        controller.message_bus = initialized_message_broker
        controller.gemini_service = mock_gemini_service

        original_message = Message(
            recipient_id="MODERATOR",
            sender_id="SYSTEM",
            message_type="INITIATE_DEBATE",
            payload={"topic": "Test"},
            turn_id=5
        )

        # When
        controller._process_message(original_message)

        # Then: ターンIDが適切にインクリメントされている
        response = controller.message_bus.get_message("TEST_RECIPIENT")
        assert response.turn_id == 6  # original_turn_id + 1


if __name__ == '__main__':
    pytest.main([__file__])
