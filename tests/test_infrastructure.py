#!/usr/bin/env python3
"""
インフラストラクチャ層のテスト
外部サービスとの具体的な実装をテスト
"""

from main.domain.models import Message
from main.infrastructure.file_repository import FileBasedPromptRepository
from main.infrastructure.gemini_service import GeminiService
from main.infrastructure.message_broker import SqliteMessageBroker
import sys
import os
import tempfile
import subprocess
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSqliteMessageBroker:
    """SQLiteメッセージブローカーのテスト"""

    def test_message_broker_initialization(self):
        """メッセージブローカーの初期化テスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        broker = SqliteMessageBroker(db_path)
        broker.initialize_db()

        # データベースファイルが作成されることを確認
        assert os.path.exists(db_path)

        # クリーンアップ
        os.unlink(db_path)

    def test_post_and_get_message(self):
        """メッセージの投稿と取得のテスト"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        broker = SqliteMessageBroker(db_path)
        broker.initialize_db()

        # メッセージ作成
        message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": "AI benefits"},
            turn_id=1
        )

        # メッセージ投稿
        broker.post_message(message)

        # メッセージ取得
        retrieved = broker.get_message("DEBATER_A")

        assert retrieved is not None
        assert retrieved.recipient_id == "DEBATER_A"
        assert retrieved.sender_id == "MODERATOR"
        assert retrieved.message_type == "PROMPT_FOR_STATEMENT"
        assert retrieved.payload["topic"] == "AI benefits"

        # 同じメッセージは二度取得されない
        retrieved_again = broker.get_message("DEBATER_A")
        assert retrieved_again is None

        # クリーンアップ
        os.unlink(db_path)


class TestGeminiService:
    """Geminiサービスのテスト"""

    def test_generate_response_success(self):
        """正常なレスポンス生成のテスト - 新アーキテクチャ対応"""
        service = GeminiService()

        # 既知のパターンでテスト
        prompt = "MODERATOR prompt with PROMPT_FOR_STATEMENT"
        response = service.generate_response(prompt)

        # 現在の実装では常にJSON形式で返される
        assert "```json" in response
        assert "recipient_id" in response
        assert "message_type" in response
        assert "payload" in response

    def test_generate_response_with_system_prompt(self):
        """システムプロンプト付きレスポンス生成のテスト - 新アーキテクチャ対応"""
        service = GeminiService()

        # DEBATER_Aのパターンでテスト
        response = service.generate_response(
            "DEBATER_A prompt with PROMPT_FOR_STATEMENT",
            system_prompt="System instruction"
        )

        # 現在の実装では常にJSON形式で返される
        assert "```json" in response
        assert "MODERATOR" in response  # DEBATER_Aは通常MODERATORに送信
        assert "SUBMIT_STATEMENT" in response

    def test_generate_response_error(self):
        """エラー時のテスト - 新アーキテクチャ対応"""
        service = GeminiService()

        # 現在の実装では例外を投げず、エラーメッセージをJSONで返す
        response = service.generate_response("Unknown pattern prompt")

        # エラー時でもJSON形式で返される
        assert "```json" in response
        assert "SYSTEM_ERROR" in response
        assert "No appropriate response pattern found" in response


class TestFileBasedPromptRepository:
    """ファイルベースプロンプトリポジトリのテスト"""

    def test_get_persona_success(self):
        """ペルソナ取得の成功テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # テスト用ペルソナファイル作成
            persona_file = os.path.join(temp_dir, "debater_a.md")
            with open(persona_file, 'w', encoding='utf-8') as f:
                f.write("You are a pro-AI debater with logical thinking.")

            repo = FileBasedPromptRepository(temp_dir)
            persona = repo.get_persona("DEBATER_A")

            assert persona == "You are a pro-AI debater with logical thinking."

    def test_get_persona_file_not_found(self):
        """ペルソナファイルが見つからない場合のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = FileBasedPromptRepository(temp_dir)
            persona = repo.get_persona("NONEXISTENT")

            assert persona == ""  # 空文字列を返す


class TestIntegrationWithExistingSystem:
    """既存システムとの統合テスト"""

    def test_existing_message_broker_compatibility(self):
        """既存のメッセージブローカーとの互換性テスト（新実装使用）"""
        # 新しいSqliteMessageBrokerで既存の機能をテスト
        import tempfile
        import os

        # 一時ファイルでテストデータベースを作成
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()

        try:
            broker = SqliteMessageBroker(temp_db.name)
            broker.initialize_db()

            # テスト用のメッセージデータ
            test_message = Message(
                sender_id="MODERATOR",
                recipient_id="DEBATER_A",
                message_type="PROMPT_FOR_STATEMENT",
                payload={"topic": "AI benefits"},
                turn_id=1
            )

            # 新実装での動作確認
            broker.post_message(test_message)
            retrieved = broker.get_message("DEBATER_A")

            assert retrieved is not None
            assert retrieved.message_type == "PROMPT_FOR_STATEMENT"
            assert retrieved.sender_id == "MODERATOR"
        finally:
            # クリーンアップ
            os.unlink(temp_db.name)
