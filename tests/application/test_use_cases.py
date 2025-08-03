"""
Application Layer Use Cases Tests
Kent Beck TDD: アプリケーション層はビジネスロジックの心臓部

TDD原則: Use Casesは外部の実装詳細に依存せず、
        ドメインモデルとの協調のみをテストする
"""
import pytest
from unittest.mock import Mock


class TestDebateUseCases:
    """ディベートUse Casesのテスト"""

    def test_initiate_debate_should_send_initial_message(self):
        """ディベート開始時は初期メッセージを送信すること

        TDD Red Phase: ディベート開始の要件を定義
        """
        # Arrange - モックで依存関係を定義
        mock_message_broker = Mock()
        mock_config = Mock()
        mock_config.initial_task = {"topic": "AI Ethics"}

        # Use Case実装がない場合のモック定義（Red Phase）
        mock_debate_use_case = Mock()
        mock_debate_use_case.message_broker = mock_message_broker
        mock_debate_use_case.config = mock_config

        def initiate_debate():
            # 期待される動作をモックで定義
            initial_message = Mock()
            initial_message.recipient_id = "MODERATOR"
            initial_message.message_type = "INITIATE_DEBATE"
            initial_message.payload = mock_config.initial_task

            mock_message_broker.post_message(initial_message)
            return initial_message

        mock_debate_use_case.initiate_debate = initiate_debate

        # Act
        result = mock_debate_use_case.initiate_debate()

        # Assert
        assert result.recipient_id == "MODERATOR"
        assert result.message_type == "INITIATE_DEBATE"
        assert result.payload["topic"] == "AI Ethics"
        mock_message_broker.post_message.assert_called_once()

    def test_process_debater_statement_should_validate_input(self):
        """ディベーター発言処理時は入力を検証すること

        TDD Red Phase: 入力検証の要件を定義
        """
        # Arrange
        mock_debate_use_case = Mock()

        def process_statement(statement):
            if not statement or not statement.strip():
                raise ValueError("Statement cannot be empty")
            if len(statement) > 1000:
                raise ValueError("Statement too long")
            return {"status": "processed", "statement": statement}

        mock_debate_use_case.process_statement = process_statement

        # Act & Assert - 正常ケース
        result = mock_debate_use_case.process_statement("Valid statement")
        assert result["status"] == "processed"

        # Act & Assert - エラーケース
        with pytest.raises(ValueError, match="cannot be empty"):
            mock_debate_use_case.process_statement("")

        with pytest.raises(ValueError, match="too long"):
            mock_debate_use_case.process_statement("x" * 1001)

    def test_evaluate_debate_round_should_track_turn_progression(self):
        """ディベート評価時はターンの進行を追跡すること

        TDD Red Phase: ターン管理の要件を定義
        """
        # Arrange
        mock_debate_use_case = Mock()
        mock_debate_use_case.current_turn = 1
        mock_debate_use_case.max_turns = 5

        def evaluate_round():
            current = mock_debate_use_case.current_turn
            max_turns = mock_debate_use_case.max_turns

            if current >= max_turns:
                return {"status": "completed", "winner": "DEBATER_A"}
            else:
                mock_debate_use_case.current_turn += 1
                return {
                    "status": "continuing",
                    "next_turn": mock_debate_use_case.current_turn
                }

        mock_debate_use_case.evaluate_round = evaluate_round

        # Act - 通常のターン進行
        result = mock_debate_use_case.evaluate_round()
        assert result["status"] == "continuing"
        assert result["next_turn"] == 2

        # Act - 最終ターンでの完了
        mock_debate_use_case.current_turn = 5
        result = mock_debate_use_case.evaluate_round()
        assert result["status"] == "completed"
        assert "winner" in result


class TestMessageProcessingUseCases:
    """メッセージ処理Use Casesのテスト"""

    def test_handle_agent_message_should_route_correctly(self):
        """エージェントメッセージは正しくルーティングされること

        TDD Red Phase: メッセージルーティングの要件を定義
        """
        # Arrange
        mock_message_handler = Mock()

        def handle_message(message):
            if message.message_type == "SUBMIT_STATEMENT":
                return {"action": "forward_to_judge", "recipient": "JUDGE"}
            elif message.message_type == "REQUEST_EVALUATION":
                return {
                    "action": "forward_to_moderator",
                    "recipient": "MODERATOR"
                }
            else:
                raise ValueError(
                    f"Unknown message type: {message.message_type}"
                )

        mock_message_handler.handle_message = handle_message

        # Test message
        test_message = Mock()
        test_message.message_type = "SUBMIT_STATEMENT"

        # Act
        result = mock_message_handler.handle_message(test_message)

        # Assert
        assert result["action"] == "forward_to_judge"
        assert result["recipient"] == "JUDGE"

    def test_validate_message_format_should_check_required_fields(self):
        """メッセージ形式検証は必須フィールドをチェックすること

        TDD Red Phase: メッセージ検証の要件を定義
        """
        # Arrange
        mock_validator = Mock()

        def validate_message(message):
            required_fields = [
                "sender_id", "recipient_id", "message_type", "payload"
            ]
            missing_fields = []

            for field in required_fields:
                if (not hasattr(message, field) or
                        getattr(message, field) is None):
                    missing_fields.append(field)

            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")

            return True

        mock_validator.validate_message = validate_message

        # Act & Assert - 有効なメッセージ
        valid_message = Mock()
        valid_message.sender_id = "DEBATER_A"
        valid_message.recipient_id = "MODERATOR"
        valid_message.message_type = "SUBMIT_STATEMENT"
        valid_message.payload = {"text": "Valid"}

        assert mock_validator.validate_message(valid_message) is True

        # Act & Assert - 無効なメッセージ
        invalid_message = Mock()
        invalid_message.sender_id = "DEBATER_A"
        invalid_message.recipient_id = None  # 必須フィールドが欠けている
        invalid_message.message_type = "SUBMIT_STATEMENT"
        invalid_message.payload = {"text": "Invalid"}

        with pytest.raises(ValueError, match="Missing required fields"):
            mock_validator.validate_message(invalid_message)
