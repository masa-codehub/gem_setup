#!/usr/bin/env python3
"""
インフラストラクチャ層のテスト
外部サービスとの具体的な実装をテスト
"""

from main.entities.models import Message
from main.frameworks_and_drivers.frameworks.file_repository import FileBasedPromptRepository
from main.frameworks_and_drivers.frameworks.gemini_service import GeminiService
from main.frameworks_and_drivers.frameworks.message_broker import SqliteMessageBroker
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
    """Geminiサービスのテスト - 新アーキテクチャ対応"""

    def test_generate_response_success(self):
        """正常なレスポンス生成のテスト - 新アーキテクチャ対応"""
        from main.frameworks_and_drivers.frameworks.file_repository import (
            FileBasedPromptRepository
        )
        from main.frameworks_and_drivers.frameworks.prompt_injector_service import (
            PromptInjectorService
        )
        from main.entities.models import Message
        from unittest.mock import Mock, patch

        # モックプロンプトリポジトリを作成
        mock_repo = Mock(spec=FileBasedPromptRepository)
        mock_repo.get_persona.return_value = "You are a test agent."

        # プロンプトインジェクターとGeminiServiceを初期化
        prompt_injector = PromptInjectorService(mock_repo)
        service = GeminiService(prompt_injector)

        # テスト用のメッセージを作成
        test_message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": "AI benefits"},
            turn_id=1
        )

        # 新しいインターフェースでテスト
        with patch.object(service, '_call_gemini_cli',
                          return_value='{"content": "test response"}'):
            response = service.generate_response("DEBATER_A", test_message)

            assert response.recipient_id == "MODERATOR"  # fallback response
            assert response.sender_id == "DEBATER_A"
            assert response.message_type == "RESPONSE"
            assert "test response" in response.payload["content"]

    def test_generate_response_with_system_prompt(self):
        """システムプロンプト付きレスポンス生成のテスト - 新アーキテクチャ対応"""
        from main.frameworks_and_drivers.frameworks.file_repository import (
            FileBasedPromptRepository
        )
        from main.frameworks_and_drivers.frameworks.prompt_injector_service import (
            PromptInjectorService
        )
        from main.entities.models import Message
        from unittest.mock import Mock, patch

        # モックプロンプトリポジトリを作成
        mock_repo = Mock(spec=FileBasedPromptRepository)
        mock_repo.get_persona.return_value = (
            "You are a test agent with system rules."
        )

        prompt_injector = PromptInjectorService(mock_repo)
        service = GeminiService(prompt_injector)

        test_message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": "AI benefits", "instructions": "Be precise"},
            turn_id=1
        )

        json_response = ('```json\n'
                         '{"recipient_id": "MODERATOR", '
                         '"message_type": "SUBMIT_STATEMENT", '
                         '"payload": {"statement": "test"}}\n```')

        with patch.object(service, '_call_gemini_cli',
                          return_value=json_response):
            response = service.generate_response("DEBATER_A", test_message)

            assert response.recipient_id == "MODERATOR"
            assert response.message_type == "SUBMIT_STATEMENT"
            assert response.payload["statement"] == "test"

    def test_generate_response_error(self):
        """エラー時のテスト - 新アーキテクチャ対応"""
        from main.frameworks_and_drivers.frameworks.file_repository import (
            FileBasedPromptRepository
        )
        from main.frameworks_and_drivers.frameworks.prompt_injector_service import (
            PromptInjectorService
        )
        from main.entities.models import Message
        from unittest.mock import Mock, patch

        # モックプロンプトリポジトリを作成
        mock_repo = Mock(spec=FileBasedPromptRepository)
        mock_repo.get_persona.return_value = "You are a test agent."

        prompt_injector = PromptInjectorService(mock_repo)
        service = GeminiService(prompt_injector)

        test_message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="INVALID_TYPE",
            payload={},
            turn_id=1
        )

        # エラーをシミュレート
        with patch.object(service, '_call_gemini_cli',
                          return_value="Error: API failure"):
            response = service.generate_response("DEBATER_A", test_message)

            # フォールバック応答が返される
            assert response.recipient_id == "MODERATOR"
            assert response.sender_id == "DEBATER_A"
            assert response.message_type == "RESPONSE"
            assert "Error: API failure" in response.payload["content"]


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
