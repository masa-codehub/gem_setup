"""
TDD Refactor Phase - Legacy Test Modernization
既存テストを新しいアーキテクチャに適応させる
"""
import unittest
from unittest.mock import Mock, patch
from main.infrastructure.gemini_service import GeminiService
from main.infrastructure.prompt_injector_service import PromptInjectorService
from main.infrastructure.file_repository import FileBasedPromptRepository
from main.domain.models import Message


class TestGeminiServiceModernized(unittest.TestCase):
    """GeminiServiceの現代化されたテスト"""

    def setUp(self):
        """テスト前の準備 - 新しいアーキテクチャ対応"""
        # モックプロンプトリポジトリを作成
        self.mock_repo = Mock(spec=FileBasedPromptRepository)
        self.mock_repo.get_persona.return_value = "You are a test agent."

        # プロンプトインジェクターとGeminiServiceを初期化
        self.prompt_injector = PromptInjectorService(self.mock_repo)
        self.service = GeminiService(self.prompt_injector)

    @patch('subprocess.run')
    def test_generate_response_with_new_architecture(self, mock_run):
        """新アーキテクチャに適応したレスポンス生成テスト"""
        # サブプロセスのモック設定
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ('```json\n'
                              '{"recipient_id": "DEBATER_A", '
                              '"message_type": "PROMPT_FOR_STATEMENT", '
                              '"payload": {"topic": "test"}}\n```')
        mock_run.return_value = mock_result

        # テスト用メッセージ
        test_message = Message(
            recipient_id="MODERATOR",
            sender_id="SYSTEM",
            message_type="START_SESSION",
            payload={"session_type": "debate", "topic": "AI Ethics"},
            turn_id=0
        )

        # 新しいインターフェースでテスト
        response = self.service.generate_response("MODERATOR", test_message)

        assert response.recipient_id == "DEBATER_A"
        assert response.message_type == "PROMPT_FOR_STATEMENT"
        assert response.payload["topic"] == "test"

    @patch('subprocess.run')
    def test_generate_response_error_handling_modernized(self, mock_run):
        """現代化されたエラーハンドリングテスト"""
        # Arrange - エラー状況のモック
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "API Error occurred"
        mock_run.return_value = mock_result

        # テスト用メッセージ
        test_message = Message(
            recipient_id="DEBATER_A",
            sender_id="MODERATOR",
            message_type="PROMPT_FOR_STATEMENT",
            payload={"topic": "test"},
            turn_id=1
        )

        # Act - 新しいインターフェースでテスト
        response = self.service.generate_response("DEBATER_A", test_message)

        # Assert - エラー時は適切なフォールバックレスポンスが返る
        assert response.recipient_id == "MODERATOR"
        assert response.sender_id == "DEBATER_A"
        assert response.message_type == "RESPONSE"
        # エラー内容は_call_gemini_cliが実際に呼ばれた結果に依存


if __name__ == '__main__':
    unittest.main()
